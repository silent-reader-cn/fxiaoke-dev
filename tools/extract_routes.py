# -*- coding: utf-8 -*-
"""
从 VuePress 站点的 app.js 里提取全站路由清单 + 中文分类层级。

站点是 VuePress 2 + Plume 主题的 SSG 产物，两份权威数据都编译进了 app.js：
  1) sidebar 配置对象 —— 带 prefix 层级与中文 text，给出「模块 / 对象」中文名
  2) 路由表 ["<path>.html",{loader:...,meta:{title:"<标题>"}}] —— 给出每个页面的标题

产出 _source/_toc.json（路由清单 + 中文层级映射）与 _source/_sidebar.json。

用法：
    python tools/extract_routes.py                     # 自动下载 app.js 并提取
    python tools/extract_routes.py --app-js js/app-XXXX.js
    python tools/extract_routes.py --out _source/_toc.json
"""
import argparse
import gzip
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# 站点路径前缀（文档站挂在 /openapi_v2 下）
SITE_PREFIX = "/openapi_v2"
ORIGIN = "https://developer.fxiaoke.com"
LANDING = ORIGIN + SITE_PREFIX + "/"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# 分块定义：路由一级目录 -> (块目录名, 中文块名)
BLOCKS = [
    ("/start/", "01_start", "快速开始与接入"),
    ("/object/", "02_object", "对象接口"),
    ("/common/", "03_common", "通用接口"),
    ("/FAQ/", "04_faq", "常见问题"),
]
# 英文镜像与博客不纳入
SKIP_PREFIXES = ("/en/", "/blog")


def match_obj(text, start):
    """start 指向 '{'，返回配对 '}' 之后的下标；找不到返回 -1。"""
    depth = 0
    in_str = False
    esc = False
    k = start
    while k < len(text):
        ch = text[k]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return k + 1
        k += 1
    return -1


def parse_sidebar(src):
    """抠出 sidebar 配置对象并转成 dict。"""
    anchor = src.find('"/start/":{items:[')
    if anchor < 0:
        raise RuntimeError("未找到 sidebar 配置入口 '\"/start/\":{items:['")
    start = src.rfind("{", 0, anchor)
    end = match_obj(src, start)
    if end < 0:
        raise RuntimeError("sidebar 对象括号不配对")
    frag = src[start:end]
    # JS 对象字面量 -> JSON：给裸键名补引号，替换布尔字面量
    js = re.sub(r"([{,])([A-Za-z_$][A-Za-z0-9_$]*):", r'\1"\2":', frag)
    js = js.replace("!1", "false").replace("!0", "true")
    return json.loads(js)


def walk_sidebar(items, base, ancestors, out):
    """
    递归 sidebar，产出 {路径前缀: [中文层级]}。
    items 可能是 'auto'、list[str] 或 list[dict]。
    """
    if items == "auto" or items is None:
        return
    if isinstance(items, list):
        for it in items:
            if isinstance(it, str):
                # 裸字符串项（如 FAQ 下的 slug）
                out[base + it + "/"] = ancestors + [it]
                continue
            text = it.get("text", "")
            prefix = it.get("prefix", "")
            if prefix.startswith("/"):
                newbase = prefix if prefix.endswith("/") else prefix + "/"
            else:
                newbase = base + prefix + "/"
            sub = it.get("items")
            if sub == "auto":
                out[newbase] = ancestors + [text]
            else:
                # 中间节点：也登记一份，便于最长前缀匹配兜底
                out.setdefault(newbase, ancestors + [text])
                walk_sidebar(sub, newbase, ancestors + [text], out)


def extract_route_titles(src):
    """从路由表提取 {path(无.html): title}。"""
    pat = re.compile(
        r'\["(/[^"]*?\.html)",\s*\{loader:\(\)=>.*?meta:\{title:"((?:[^"\\]|\\.)*)"\}\}\]'
    )
    titles = {}
    for path, title in pat.findall(src):
        titles[path[:-5] if path.endswith(".html") else path] = title
    return titles


def http_get(url, timeout=40):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept-Encoding": "gzip",
        "Accept-Language": "zh-CN,zh;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return raw.decode("utf-8", "replace")


def resolve_app_js(app_js):
    """
    返回 app.js 的本地路径。

    给定路径存在就直接用；否则从文档站首页找出 `assets/app-*.js` 的引用并下载到
    js/ 下（文件名带内容哈希，站点改版后会变，所以必须每次现找）。
    """
    if app_js and os.path.exists(app_js):
        return app_js
    print("本地未找到 app.js，正在从文档站定位并下载 …")
    landing = http_get(LANDING)
    m = re.search(r'["\'](/openapi_v2/assets/app-[A-Za-z0-9_-]+\.js)["\']', landing)
    if not m:
        raise RuntimeError("文档站首页里没找到 app-*.js 引用，站点结构可能已变")
    url = ORIGIN + m.group(1)
    out = os.path.join(ROOT, "js", os.path.basename(m.group(1)))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    src = http_get(url)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    print(f"  已下载 {url} -> {os.path.relpath(out, ROOT)}（{len(src)} 字节）")
    return out


def build_toc(app_js_path):
    src = open(app_js_path, encoding="utf-8").read()

    sidebar = parse_sidebar(src)
    # 存档 sidebar 配置，供人工核对中文分类
    json.dump(sidebar, open(os.path.join(ROOT, "_source", "_sidebar.json"), "w",
                            encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)

    prefix_map = {}
    for key, node in sidebar.items():
        base = node.get("prefix", key)
        if not base.endswith("/"):
            base += "/"
        walk_sidebar(node.get("items"), base, [], prefix_map)

    titles = extract_route_titles(src)

    # 反向：由路由反查中文层级
    prefixes_sorted = sorted(prefix_map.keys(), key=len, reverse=True)

    # 模块 / 对象 的中英文对照（对象页强制两级目录时要用）
    module_cn = {}
    object_cn = {}
    for pfx, names in prefix_map.items():
        parts = pfx.strip("/").split("/")
        if parts[0] == "object" and len(parts) == 2:
            module_cn[parts[1]] = names[-1]
        elif parts[0] == "object" and len(parts) == 3:
            object_cn[f"{parts[1]}/{parts[2]}"] = names[-1]

    pages = []
    for path in sorted(titles):
        if path.startswith(SKIP_PREFIXES):
            continue
        block_dir = block_cn = None
        for bp, bd, bc in BLOCKS:
            if path.startswith(bp.rstrip("/")):
                block_dir, block_cn = bd, bc
                break
        if block_dir is None:
            continue

        # 最长前缀匹配拿中文层级
        cat = None
        probe = path.rstrip("/") + "/"
        for pfx in prefixes_sorted:
            if probe.startswith(pfx):
                cat = prefix_map[pfx]
                break
        if not cat:
            cat = [block_cn]

        pages.append(
            {
                "path": path,
                "url": ORIGIN + SITE_PREFIX + path + ".html",
                "title": titles[path],
                "block": block_dir,
                "blockCn": block_cn,
                "category": cat,  # 中文层级列表，如 ["商品与产品","商品"]
                "categoryCn": " / ".join(cat),
            }
        )

    toc = {
        "source": ORIGIN + SITE_PREFIX,
        "appJs": os.path.basename(app_js_path),
        "blocks": [{"dir": bd, "name": bc, "prefix": bp} for bp, bd, bc in BLOCKS],
        "totalPages": len(pages),
        # 路径前缀 -> 中文层级（来自 sidebar，权威且比页面面包屑完整）
        "prefixCn": {k: v for k, v in sorted(prefix_map.items())},
        "moduleCn": module_cn,
        "objectCn": object_cn,
        "pages": pages,
    }
    return toc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--app-js", default=None,
                    help="本地 app-*.js 路径；不给则自动从文档站下载")
    ap.add_argument("--out", default=os.path.join(ROOT, "_source", "_toc.json"))
    args = ap.parse_args()

    app_js = resolve_app_js(args.app_js)
    toc = build_toc(app_js)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(toc, open(args.out, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)

    # 概览
    from collections import Counter

    by_block = Counter(p["block"] for p in toc["pages"])
    print("已写出", args.out)
    print("总页面数:", toc["totalPages"])
    for _, bd, bc in BLOCKS:
        print(f"  {bd}  {bc}: {by_block[bd]}")
    no_cat = [p for p in toc["pages"] if len(p["category"]) <= 1]
    print("分类层级不足（<=1 级）的页面:", len(no_cat))
    for p in no_cat[:10]:
        print("   ", p["path"], "->", p["categoryCn"])
    # 重名检查
    dup = Counter(p["path"] for p in toc["pages"])
    print("重复路径:", [k for k, v in dup.items() if v > 1][:5])


if __name__ == "__main__":
    sys.exit(main())

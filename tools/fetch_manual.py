# -*- coding: utf-8 -*-
"""
批量抓取纷享销客开发者手册并转换成 Markdown。

依赖：仅 Python 3 标准库（urllib / gzip / html.parser）。

流程：
    _source/_toc.json  --(逐页 GET)-->  整页 HTML
                       --(html2md)-->   Markdown
                       --(写盘)-->      references/<块>/<分类>/<标题>.md

设计要点：
  * 增量：页面已记录在 _source/_files.json 就跳过联网；--force 强制重抓
  * 两阶段：先并发抓取（只拿元数据与正文），再串行定路径写盘
    —— 因为输出路径依赖面包屑，且需要全局撞名保护，必须串行决定
  * 对象页强制两级目录「模块 / 对象」：有 6 个对象没登记在 sidebar，
    面包屑缺对象级，只用标题会互相覆盖
  * 页面 600KB 里 97% 是内联侧边栏，抓下来只留正文，磁盘占用极小

用法：
    python tools/fetch_manual.py                 # 增量抓取全站
    python tools/fetch_manual.py --only /object/CommoditiesAndProducts
    python tools/fetch_manual.py --force --jobs 8
    python tools/fetch_manual.py --limit 20      # 试跑
    python tools/fetch_manual.py --prune         # 列出已下线页面
"""
import argparse
import gzip
import json
import os
import re
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import html2md  # noqa: E402

TOC = os.path.join(ROOT, "_source", "_toc.json")
FILES = os.path.join(ROOT, "_source", "_files.json")
REFS = os.path.join(ROOT, "references")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

_lock = threading.Lock()
_stats = {"ok": 0, "skip": 0, "fail": 0, "bytes": 0}
_failures = []


def sanitize(name, fallback="untitled"):
    name = re.sub(r'[\\/:*?"<>|\r\n\t]', "_", name or "")
    name = re.sub(r"\s+", " ", name).strip().strip(". ")
    return name or fallback


def fetch(url, retries=3, timeout=40):
    """GET 一个页面，返回 (HTML 文本, 字节数)。"""
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Encoding": "gzip",
                "Accept-Language": "zh-CN,zh;q=0.9",
            })
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                enc = "utf-8"
                m = re.search(r"charset=([\w-]+)", r.headers.get("Content-Type", ""))
                if m:
                    enc = m.group(1)
                return raw.decode(enc, errors="replace"), len(raw)
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(0.6 * (attempt + 1))
    raise last


def compute_path(page, meta, toc):
    """
    决定 (输出绝对路径, 分类目录, 标题)。

    分类以 _toc.json 的 prefixCn（来自 sidebar）为准 —— 页面面包屑对
    「未登记在 sidebar 的对象页」只有两级，不可靠。
    """
    segs = page["path"].strip("/").split("/")
    crumbs = [c for c in meta.get("breadcrumb", []) if c and c != "首页"]
    title = crumbs[-1] if crumbs else (page.get("title") or segs[-1])

    prefix_cn = toc.get("prefixCn", {})

    if page["block"] == "02_object" and len(segs) >= 4:
        # 对象页恒定两级「模块 / 对象」：sidebar 未登记的对象用英文名兜底，
        # 否则 6 个对象会挤进模块目录并靠 -action 后缀区分，很难看
        mod = toc.get("moduleCn", {}).get(segs[1], segs[1])
        obj = toc.get("objectCn", {}).get(f"{segs[1]}/{segs[2]}", segs[2])
        cats = [mod, obj]
    else:
        cats = None
        probe = page["path"].rstrip("/") + "/"
        for pfx in sorted(prefix_cn, key=len, reverse=True):
            if probe.startswith(pfx):
                cats = list(prefix_cn[pfx])
                break
        if cats is None:
            cats = crumbs[:-1] if crumbs else []

    cats = [sanitize(c) for c in cats if c]
    parts = [REFS, page["block"]] + cats + [sanitize(title)]
    return os.path.join(*parts) + ".md", cats, title


def build_frontmatter(page, meta, cats, title):
    crumbs = [c for c in meta.get("breadcrumb", []) if c and c != "首页"]
    fm = [
        "---",
        f'title: "{title}"',
        f'path: "{page["path"]}"',
        f'url: "{page["url"]}"',
        f'block: "{page["blockCn"]}"',
    ]
    if crumbs:
        fm.append(f'module: "{crumbs[0]}"')
    if len(crumbs) >= 2:
        fm.append(f'object: "{crumbs[1]}"')
    fm.append(f'category: "{" / ".join(cats)}"')
    fm.append(f'updatedAt: "{meta.get("updatedAt", "")}"')
    fm.append(f'fetchedAt: "{time.strftime("%Y-%m-%d %H:%M:%S")}"')
    fm.append("---")
    return "\n".join(fm)


def assign_unique(target, page_path, used, action):
    """撞名保护：同目录同标题时补上 URL 末段区分。"""
    if target not in used:
        return target
    root, ext = os.path.splitext(target)
    cand = f"{root}-{action}{ext}"
    n = 2
    while cand in used:
        cand = f"{root}-{action}-{n}{ext}"
        n += 1
    return cand


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--toc", default=TOC)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="")
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--delay", type=float, default=0.1)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--prune", action="store_true")
    args = ap.parse_args()

    toc = json.load(open(args.toc, encoding="utf-8"))
    pages = toc["pages"]
    if args.only:
        pages = [p for p in pages if p["path"].startswith(args.only)]
    if args.limit:
        pages = pages[: args.limit]

    manifest = {}
    if os.path.exists(FILES):
        for r in json.load(open(FILES, encoding="utf-8")):
            manifest[r["path"]] = r

    if args.prune:
        keep = {os.path.normpath(os.path.join(ROOT, r["file"])) for r in manifest.values()}
        stale = []
        for dp, _d, fs in os.walk(REFS):
            for fn in fs:
                if fn.endswith(".md") and fn != "_INDEX.md":
                    p = os.path.normpath(os.path.join(dp, fn))
                    if p not in keep:
                        stale.append(p)
        print(f"磁盘上共 {len(keep)} 个受管文件，发现 {len(stale)} 个不在清单中：")
        for p in stale[:30]:
            print("   ", os.path.relpath(p, ROOT))
        if len(stale) > 30:
            print(f"    … 其余 {len(stale) - 30} 个")
        return 0

    todo = [p for p in pages if args.force or p["path"] not in manifest]
    print(f"清单 {len(pages)} 页；已抓 {len(pages) - len(todo)}；本轮待抓 {len(todo)}（线程 {args.jobs}）")
    if not todo:
        print("全部已是最新。")
        return 0

    t0 = time.time()
    results = []

    def worker(p):
        time.sleep(args.delay)
        try:
            html, nbytes = fetch(p["url"])
        except Exception as e:  # noqa: BLE001
            with _lock:
                _stats["fail"] += 1
                _failures.append({"path": p["path"], "error": f"{type(e).__name__}: {e}"})
            return None
        meta = html2md.extract_page(html)
        body = html2md.html_to_markdown(meta.pop("contentHtml"))
        if not body.strip():
            with _lock:
                _stats["fail"] += 1
                _failures.append({"path": p["path"], "error": "正文为空"})
            return None
        with _lock:
            _stats["bytes"] += nbytes
        return (p, meta, body)

    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = [ex.submit(worker, p) for p in todo]
        done = 0
        for fu in as_completed(futs):
            done += 1
            r = fu.result()
            if r:
                results.append(r)
            if done % 100 == 0 or done == len(todo):
                print(f"  抓取 {done}/{len(todo)}  失败 {_stats['fail']}  "
                      f"{_stats['bytes'] / 1e6:.0f}MB  {time.time() - t0:.0f}s")

    # 串行定路径 + 写盘
    used = {os.path.normpath(os.path.join(ROOT, r["file"])) for r in manifest.values()}
    results.sort(key=lambda x: x[0]["path"])
    for p, meta, body in results:
        target, cats, title = compute_path(p, meta, toc)
        target = os.path.normpath(target)
        action = p["path"].rsplit("/", 1)[-1]
        target = assign_unique(target, p["path"], used, action)
        used.add(target)
        rec = {"path": p["path"], "file": os.path.relpath(target, ROOT),
               "title": title, "category": "/".join(cats)}
        if args.dry_run:
            manifest[p["path"]] = rec
            continue
        os.makedirs(os.path.dirname(target), exist_ok=True)
        fm = build_frontmatter(p, meta, cats, title)
        with open(target, "w", encoding="utf-8", newline="\n") as f:
            f.write(f"{fm}\n\n# {title}\n\n{body}")
        manifest[p["path"]] = rec
        _stats["ok"] += 1

    if not args.dry_run:
        json.dump(sorted(manifest.values(), key=lambda x: x["path"]),
                  open(FILES, "w", encoding="utf-8", newline="\n"),
                  ensure_ascii=False, indent=1)

    print(f"\n完成：写入 {_stats['ok']}，失败 {_stats['fail']}，"
          f"下载 {_stats['bytes'] / 1e6:.1f}MB，用时 {time.time() - t0:.0f}s")
    if _failures:
        print(f"失败清单（共 {len(_failures)}，前 20）：")
        for f in _failures[:20]:
            print("   ", f["path"], "->", f["error"])
        json.dump(_failures, open(os.path.join(ROOT, "_source", "_failures.json"), "w",
                                  encoding="utf-8", newline="\n"),
                  ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())

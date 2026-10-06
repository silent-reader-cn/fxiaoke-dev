# -*- coding: utf-8 -*-
"""
纷享销客开发者手册 —— 统一全文检索。

直接读 references/ 下的 Markdown（不依赖预生成索引，所以不存在
「改了文档忘了重建索引就搜不到」的漂移问题），返回命中条目的正文。

依赖：仅 Python 3 标准库。

用法：
    python scripts/search.py 商品                                     # 全库检索
    python scripts/search.py 创建产品对象 --full                       # 完整正文
    python scripts/search.py 审批 --scope common --brief               # 精简一行
    python scripts/search.py 库存 查询 --all --scope object            # 多词全命中
    python scripts/search.py --path /object/CommoditiesAndProducts/ProductObj/add
    python scripts/search.py --list --scope start                      # 列出条目
选项：
    --scope S     start|object|common|faq，逗号可组合，默认 all
    --category C  限定分类（中文，子串匹配，如 "库存与仓储"）
    --brief       每条只输出一行摘要
    --full / -d   输出完整正文（不截断）
    --all         多个关键词必须全部命中
    --limit N     最多返回多少条（默认 20）
    --max N       非 --full 时每条正文上限（默认 1500 字符）
    --list        只列条目，不输出正文
    --path P      按 path 或标题精确取一篇（默认输出完整正文）
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REFS = os.path.join(ROOT, "references")

SCOPE_DIRS = {
    "start": "01_start",
    "object": "02_object",
    "common": "03_common",
    "faq": "04_faq",
}
DIR_SCOPES = {v: k for k, v in SCOPE_DIRS.items()}

FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)


def parse_md(text):
    """拆出 frontmatter 与正文。"""
    meta = {}
    body = text
    m = FM_RE.match(text)
    if m:
        for line in m.group(1).split("\n"):
            mm = re.match(r'^(\w+):\s*"(.*)"\s*$', line)
            if mm:
                meta[mm.group(1)] = mm.group(2)
        body = text[m.end():]
    return meta, body


def iter_docs(scopes=None, category=None):
    """遍历语料，产出 (scope, meta, body, relpath)。"""
    for dirpath, _dirs, files in os.walk(REFS):
        rel = os.path.relpath(dirpath, REFS).replace("\\", "/")
        top = rel.split("/")[0]
        scope = DIR_SCOPES.get(top)
        if scope is None or (scopes and scope not in scopes):
            continue
        for fn in sorted(files):
            if not fn.endswith(".md") or fn == "_INDEX.md":
                continue
            full = os.path.join(dirpath, fn)
            try:
                text = open(full, encoding="utf-8").read()
            except Exception:  # noqa: BLE001
                continue
            meta, body = parse_md(text)
            if category and category not in meta.get("category", ""):
                continue
            yield scope, meta, body, os.path.relpath(full, ROOT).replace("\\", "/")


def score(meta, body, kws, require_all):
    """
    分层加权打分。返回 (分数, 命中词数, 各词命中次数)。

    注意 path 必须参与：对象页最自然的查法是直接敲对象 apiName
    （如 `ProductObj`），而 apiName 只出现在 path 里 ——
    有些占位页正文里的 `dataObjectApiName` 甚至填错了对象名。
    """
    title = meta.get("title", "")
    cat = meta.get("category", "")
    path = meta.get("path", "")
    segs = set(path.strip("/").split("/"))

    counts = []
    for kw in kws:
        c = body.count(kw) + title.count(kw) * 3
        if kw in path:
            c += 1
        counts.append(c)
    if require_all and any(c == 0 for c in counts):
        return None
    hit = sum(1 for c in counts if c > 0)
    if hit == 0:
        return None

    s = 0
    for kw in kws:
        if title == kw:
            s += 20000
        elif title.startswith(kw):
            s += 5000
        elif kw in title:
            s += 2000
        if kw in cat:
            s += 800
        if kw in segs:
            s += 6000  # 正好命中一个 URL 段（模块 / 对象 / 动作）—— 强信号
        elif kw in path:
            s += 1200
    s += sum(counts) * 10
    return s, hit, counts


def make_snippet(body, kws, width):
    """围绕首次命中位置截断，绝不静默丢内容。"""
    pos = -1
    for kw in kws:
        p = body.find(kw)
        if p >= 0 and (pos < 0 or p < pos):
            pos = p
    if pos < 0:
        return body[:width] + ("\n…(后略)" if len(body) > width else "")
    start = max(0, pos - width // 3)
    end = min(len(body), start + width)
    start = max(0, end - width)
    out = body[start:end]
    prefix = "…(前略) " if start > 0 else ""
    suffix = "\n…(后略，完整正文请加 --full)" if end < len(body) else ""
    return prefix + out + suffix


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("keywords", nargs="*")
    ap.add_argument("--scope", default="all")
    ap.add_argument("--category", default="")
    ap.add_argument("--brief", action="store_true")
    ap.add_argument("--full", "-d", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--max", type=int, default=1500)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--path", default="")
    args = ap.parse_args()

    scopes = None
    if args.scope and args.scope != "all":
        scopes = {s.strip() for s in args.scope.split(",") if s.strip()}
        bad = scopes - set(SCOPE_DIRS)
        if bad:
            print(f"未知 scope：{', '.join(sorted(bad))}；可选 {', '.join(SCOPE_DIRS)}")
            return 2

    # 精确取一篇
    if args.path:
        want = args.path.strip()
        for scope, meta, body, rel in iter_docs(scopes, args.category):
            if meta.get("path") == want or meta.get("title") == want:
                print(f"# {meta.get('title')}")
                print(f"path: {meta.get('path')}")
                print(f"分类: {meta.get('category')}   块: {meta.get('block')}")
                print(f"更新: {meta.get('updatedAt')}   原文: {meta.get('url')}")
                print(f"文件: {rel}\n")
                print(body.strip())
                return 0
        print(f"未找到：{want}")
        return 1

    kws = [k for k in args.keywords if k]
    if not kws and not args.list:
        ap.print_help()
        return 2

    results = []
    total_hits = 0
    for scope, meta, body, rel in iter_docs(scopes, args.category):
        if not kws:
            results.append((0, 0, [], scope, meta, body, rel))
            total_hits += 1
            continue
        # 文件级预筛：整篇不含任何关键词的直接跳过（path 也要算，
        # 否则按对象 apiName 查会一条都搜不到）
        hay = (body + meta.get("title", "") + meta.get("category", "")
               + meta.get("path", ""))
        if not any(k in hay for k in kws):
            continue
        sc = score(meta, body, kws, args.all)
        if sc is None:
            continue
        s, hit, counts = sc
        results.append((s, hit, counts, scope, meta, body, rel))
        total_hits += 1

    if kws:
        results.sort(key=lambda r: (-r[0], r[4].get("title", "")))
    else:
        results.sort(key=lambda r: (r[4].get("category", ""), r[4].get("title", "")))

    shown = results[: args.limit]
    print(f"命中 {total_hits} 条，显示前 {len(shown)} 条"
          f"{'（--list）' if args.list else ''}\n")

    for i, (s, hit, counts, scope, meta, body, rel) in enumerate(shown, 1):
        title = meta.get("title", "")
        cat = meta.get("category", "")
        if args.brief or args.list:
            print(f"{i:>3}. [{scope}] {title}   | {cat} | {meta.get('path')}")
            continue
        print("=" * 78)
        print(f"{i}. 【{title}】  ({scope} / {cat})")
        print(f"   path: {meta.get('path')}")
        print(f"   原文: {meta.get('url')}")
        if args.full:
            print()
            print(body.strip())
        else:
            print()
            print(make_snippet(body, kws, args.max))
        print()
    if total_hits > len(shown):
        print(f"…还有 {total_hits - len(shown)} 条未显示，用 --limit 调整")
    return 0


if __name__ == "__main__":
    sys.exit(main())

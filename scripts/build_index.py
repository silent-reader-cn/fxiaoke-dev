# -*- coding: utf-8 -*-
"""
从 Markdown 派生各级 _INDEX.md（总索引 / 块索引 / 分类索引）。

只做一件事：扫 references/ 下的 .md，按目录层级生成索引。
解析逻辑 import search，避免两套解析器漂移。

用法：
    python scripts/build_index.py
"""
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import search  # noqa: E402

REFS = os.path.join(ROOT, "references")
BANNER = "<!-- 由 scripts/build_index.py 从 Markdown 自动生成，请勿手工编辑 -->"

BLOCK_TITLES = {
    "01_start": "快速开始与接入",
    "02_object": "对象接口",
    "03_common": "通用接口",
    "04_faq": "常见问题",
}
SCOPE_BY_DIR = {v: k for k, v in search.SCOPE_DIRS.items()}


def rel_link(from_dir, target_abs):
    """从 from_dir（链接所在的目录）到 target_abs 的相对链接。"""
    return os.path.relpath(target_abs, from_dir).replace("\\", "/")


def collect():
    """返回 {块目录: {分类: [ (标题, path, url, updatedAt, 相对路径) ]}}。"""
    tree = defaultdict(lambda: defaultdict(list))
    for dirpath, _dirs, files in os.walk(REFS):
        rel = os.path.relpath(dirpath, REFS).replace("\\", "/")
        parts = rel.split("/")
        top = parts[0]
        if top not in BLOCK_TITLES:
            continue
        cat = "/".join(parts[1:]) if len(parts) > 1 else ""
        for fn in sorted(files):
            if not fn.endswith(".md") or fn == "_INDEX.md":
                continue
            full = os.path.join(dirpath, fn)
            text = open(full, encoding="utf-8").read()
            meta, _body = search.parse_md(text)
            tree[top][cat].append({
                "title": meta.get("title", fn[:-3]),
                "path": meta.get("path", ""),
                "url": meta.get("url", ""),
                "updatedAt": meta.get("updatedAt", ""),
                "file": full,
            })
    return tree


def write(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def main():
    tree = collect()
    total = sum(len(v) for cats in tree.values() for v in cats.values())

    # ---------- 总索引 ----------
    L = [BANNER, "", "# 纷享销客开发者手册 · 总索引", "",
         f"共 **{total}** 篇，分 **{len(tree)}** 块。内容由官方开发者手册"
         f"（developer.fxiaoke.com/openapi_v2）批量抓取转换而来。", "",
         "| 块 | 篇数 | 分类数 | 入口 |", "| :--- | ---: | ---: | :--- |"]
    for blk in sorted(tree):
        cats = tree[blk]
        n = sum(len(v) for v in cats.values())
        L.append(f"| {BLOCK_TITLES[blk]} | {n} | {len(cats)} | "
                 f"[`references/{blk}/`](./{blk}/_INDEX.md) |")
    L += ["", "> 全文检索见 `scripts/search.py`，例："
              "`python scripts/search.py 创建产品对象 --scope object`", ""]

    for blk in sorted(tree):
        L += [f"## {BLOCK_TITLES[blk]}", ""]
        for cat in sorted(tree[blk]):
            n = len(tree[blk][cat])
            label = cat or "（未分类）"
            L.append(f"- [{label}](./{blk}/{cat}/_INDEX.md) —— {n} 篇" if cat
                     else f"- {label} —— {n} 篇")
        L.append("")
    write(os.path.join(REFS, "_INDEX.md"), L)

    # ---------- 块索引 ----------
    for blk, cats in tree.items():
        n = sum(len(v) for v in cats.values())
        blk_dir = os.path.join(REFS, blk)
        L = [BANNER, "", f"# {BLOCK_TITLES[blk]} · 索引", "",
             f"共 {n} 篇，{len(cats)} 个分类。", "",
             "| 分类 | 篇数 |", "| :--- | ---: |"]
        for cat in sorted(cats):
            label = cat or "（未分类）"
            L.append(f"| [{label}](./{cat}/_INDEX.md) | {len(cats[cat])} |" if cat
                     else f"| {label} | {len(cats[cat])} |")
        L.append("")
        for cat in sorted(cats):
            if not cat:
                continue
            L += [f"## {cat}", "", "| 标题 | 更新时间 | 原文 |", "| :--- | :--- | :--- |"]
            for it in sorted(cats[cat], key=lambda x: x["title"]):
                L.append(f"| [{it['title']}](./{rel_link(blk_dir, it['file'])}) "
                         f"| {it['updatedAt']} | [link]({it['url']}) |")
            L.append("")
        write(os.path.join(REFS, blk, "_INDEX.md"), L)

        # ---------- 分类索引 ----------
        for cat, items in cats.items():
            if not cat:
                continue
            cat_dir = os.path.join(REFS, blk, cat)
            L = [BANNER, "", f"# {BLOCK_TITLES[blk]} / {cat}", "",
                 f"共 {len(items)} 篇。", "",
                 "| 标题 | 接口路径 | 更新时间 |", "| :--- | :--- | :--- |"]
            for it in sorted(items, key=lambda x: x["title"]):
                L.append(f"| [{it['title']}](./{rel_link(cat_dir, it['file'])}) "
                         f"| `{it['path']}` | {it['updatedAt']} |")
            L.append("")
            write(os.path.join(cat_dir, "_INDEX.md"), L)

    print(f"已生成索引：总索引 1 个，块索引 {len(tree)} 个，"
          f"分类索引 {sum(len(c) for c in tree.values())} 个；共 {total} 篇。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

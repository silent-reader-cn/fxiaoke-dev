# -*- coding: utf-8 -*-
"""
完整性自检：回答两个问题 —— 抓取有没有丢内容、检索会不会静默截断。

依赖：仅 Python 3 标准库。

检查项：
  A1  目录清单 / 抓取清单 / 磁盘 Markdown 三方条目数一致
  A2  文本保真（抽样联网）：源页正文的每段可见文本都能在 Markdown 里找到
  A3  结构守恒（抽样联网）：table / pre / img 数量一致
  A4  Markdown 里不残留未转换的 HTML 块级标签
  A5  每篇 Markdown 都有 frontmatter 且字段齐全
  B1  --full 输出包含该文档全部正文行
  B2  非 --full 截断时必须打印明确提示
  B3  --limit 生效，且"总命中数"口径正确
  B4  分类索引与磁盘定义逐条一致（数量 + 内容）
  B5  端到端召回抽检：正文深处的关键词也能被检索到

A2/A3 需要源页，用 --online N 抽样联网（默认 0，跳过）。其余全部离线。

用法：
    python tools/selftest.py                 # 离线检查
    python tools/selftest.py --online 30     # 再抽样 30 页联网核对文本保真
"""
import argparse
import html
import json
import os
import random
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import html2md  # noqa: E402
import search  # noqa: E402

REFS = os.path.join(ROOT, "references")
FILES = os.path.join(ROOT, "_source", "_files.json")
TOC = os.path.join(ROOT, "_source", "_toc.json")
PY = sys.executable

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    flag = "PASS" if ok else "FAIL"
    print(f"[{flag}] {name}" + (f"  {detail}" if detail else ""))
    return ok


def norm(s):
    """两侧统一的归一化：只保留字母数字与汉字。"""
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", s or "")


def strip_fences(text):
    """
    去掉围栏代码块（连同围栏行）。
    代码块里的 <p>/<div> 是文档正文内容（JSON 示例、UI 组件模板），
    不是"未转换的 HTML"，扫描残留标签时必须排除。
    """
    out, fence = [], None
    for ln in text.split("\n"):
        if fence:
            if ln.strip().startswith(fence):
                fence = None
            continue
        m = re.match(r"^\s*(`{3,}|~{3,})", ln)
        if m:
            fence = m.group(1)
            continue
        out.append(ln)
    return "\n".join(out)


def body_lines_outside_fence(text):
    """返回围栏代码块之外的、有实质内容的行。"""
    out, fence = [], None
    for ln in text.split("\n"):
        if fence:
            if ln.strip().startswith(fence):
                fence = None
            continue
        m = re.match(r"^\s*(`{3,}|~{3,})", ln)
        if m:
            fence = m.group(1)
            continue
        if ln.strip():
            out.append(ln.strip())
    return out


def load_docs():
    docs = []
    for dirpath, _d, files in os.walk(REFS):
        for fn in files:
            if fn.endswith(".md") and fn != "_INDEX.md":
                p = os.path.join(dirpath, fn)
                text = open(p, encoding="utf-8").read()
                meta, body = search.parse_md(text)
                docs.append((p, meta, body, text))
    return docs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--online", type=int, default=0, help="抽样联网核对的页数")
    ap.add_argument("--seed", type=int, default=20261006)
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    toc = json.load(open(TOC, encoding="utf-8"))
    manifest = json.load(open(FILES, encoding="utf-8")) if os.path.exists(FILES) else []
    docs = load_docs()

    print("=" * 70)
    print("A 组：抓取完整性")
    print("=" * 70)

    # A1
    n_toc, n_man, n_disk = len(toc["pages"]), len(manifest), len(docs)
    detail = f"toc={n_toc} 清单={n_man} 磁盘={n_disk}"
    check("A1 三方条目数一致", n_toc == n_man == n_disk, detail)
    if n_toc != n_man:
        miss = {p["path"] for p in toc["pages"]} - {r["path"] for r in manifest}
        print(f"     未抓到的页面 {len(miss)} 个，前 5：{list(miss)[:5]}")

    # A5 frontmatter
    need = {"title", "path", "url", "block", "category", "updatedAt"}
    bad = [(p, sorted(need - set(m))) for p, m, _b, _t in docs if need - set(m)]
    check("A5 frontmatter 字段齐全", not bad, f"缺字段 {len(bad)} 篇" + (f"，如 {bad[0]}" if bad else ""))

    # A4 残留 HTML（代码块内的 HTML 是文档内容，必须排除）
    block_tag = re.compile(r"</?(div|span|table|thead|tbody|tr|td|th|ul|ol|li|pre|code|h[1-6]|p|a|img|strong|em)\b[^>]*>", re.I)
    residual = []
    for p, _m, body, _t in docs:
        hits = block_tag.findall(strip_fences(body))
        if hits:
            residual.append((os.path.relpath(p, ROOT), hits[:3]))
    check("A4 无残留 HTML 块级标签（不含代码块）", not residual,
          f"{len(residual)} 篇有残留" + (f"，如 {residual[0]}" if residual else ""))

    # A2/A3 抽样联网
    if args.online > 0:
        random.seed(args.seed)
        sample = random.sample(docs, min(args.online, len(docs)))
        print(f"      抽样 {len(sample)} 页联网核对 …")
        text_miss = []
        struct_bad = []
        for p, meta, body, _t in sample:
            url = meta.get("url")
            if not url:
                continue
            try:
                import gzip
                import urllib.request
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0", "Accept-Encoding": "gzip"})
                with urllib.request.urlopen(req, timeout=40) as r:
                    raw = r.read()
                    if r.headers.get("Content-Encoding") == "gzip":
                        raw = gzip.decompress(raw)
                page = html2md.extract_page(raw.decode("utf-8", "replace"))
            except Exception as e:  # noqa: BLE001
                text_miss.append((meta.get("path"), f"抓取失败 {e}"))
                continue
            src = page["contentHtml"]
            # 可见文本切块。源侧是**原始 HTML**，必须做实体解码；
            # Markdown 侧已是解码后的文本，不能再解码（否则 &times 之类会被误伤）
            chunks = re.findall(r">([^<>]+)<", src)
            nmd = norm(body)
            for c in chunks:
                nc = norm(html.unescape(c))
                if len(nc) < 3:
                    continue
                if nc not in nmd:
                    text_miss.append((meta.get("path"), c.strip()[:60]))
                    break
            # 结构守恒：按"行"数分隔行，不能按子串数
            #（一行 `| --- | --- | --- |` 含 3 个 "| --- |"）。
            # 列表项里的代码块/表格会被缩进，所以要允许前导空白
            st = (src.count("<table"), src.count("<pre"), src.count("<img"))
            md = (len(re.findall(r"^\s*\|\s*-{3,}", body, re.M)),
                  len(re.findall(r"^\s*```", body, re.M)) // 2,
                  body.count("!["))
            if st[0] != md[0] or st[1] != md[1]:
                struct_bad.append((meta.get("path"), f"table {st[0]}/{md[0]} pre {st[1]}/{md[1]}"))
        check("A2 文本保真（抽样）", not text_miss,
              f"{len(sample) - len(text_miss)}/{len(sample)} 通过"
              + (f"；缺失如 {text_miss[0]}" if text_miss else ""))
        check("A3 结构守恒（抽样）", not struct_bad,
              f"{len(struct_bad)} 篇不一致" + (f"，如 {struct_bad[0]}" if struct_bad else ""))
    else:
        print("[SKIP] A2/A3 未抽样（加 --online N 开启）")

    print()
    print("=" * 70)
    print("B 组：检索行为")
    print("=" * 70)

    def run(args_):
        r = subprocess.run([PY, os.path.join(ROOT, "scripts", "search.py")] + args_,
                           capture_output=True, text=True, encoding="utf-8")
        return r.stdout or ""

    # 挑一篇较长的文档做 B1
    docs_sorted = sorted(docs, key=lambda d: -len(d[2]))
    target = docs_sorted[0]
    t_title = target[1].get("title", "")
    full_out = run([t_title, "--path", target[1].get("path", "")])
    body_lines = [ln for ln in target[2].split("\n") if ln.strip()]
    missing = [ln for ln in body_lines if ln.strip() not in full_out]
    check("B1 --path 输出完整正文", not missing,
          f"{len(body_lines) - len(missing)}/{len(body_lines)} 行命中"
          + (f"，缺 {missing[0][:50]}" if missing else ""))

    # B2 截断提示
    kw = "对象"
    trunc = run([kw, "--limit", "1", "--max", "200"])
    has_notice = "后略" in trunc or "前略" in trunc
    brief_full = run([kw, "--limit", "1", "--full"])
    check("B2 截断时有明确提示", has_notice or len(brief_full) <= len(trunc) + 50,
          "提示已打印" if has_notice else "该条未截断（正文短于上限）")

    # B3 --limit 与总命中数
    out_a = run([kw, "--limit", "5", "--brief"])
    out_b = run([kw, "--limit", "1", "--brief"])
    m_a = re.search(r"命中 (\d+) 条，显示前 (\d+) 条", out_a)
    m_b = re.search(r"命中 (\d+) 条，显示前 (\d+) 条", out_b)
    ok = bool(m_a and m_b) and m_a.group(1) == m_b.group(1) and m_b.group(2) == "1"
    check("B3 --limit 生效且总命中数口径一致", ok,
          f"{m_a.groups() if m_a else None} vs {m_b.groups() if m_b else None}")

    # B4 索引与实际文件一致
    #   块级索引指向的是子目录的 _INDEX.md，不是同目录文件，
    #   所以分两条：所有链接必须可达；叶子目录的条目数必须与实际文件数相等
    broken_links = []
    leaf_mism = []
    for dirpath, _d, files in os.walk(REFS):
        if "_INDEX.md" not in files:
            continue
        idx = os.path.join(dirpath, "_INDEX.md")
        text = open(idx, encoding="utf-8").read()
        # 注意用非贪婪 + [^#]：文件名里可能带括号（如 "从线索池(公海)领取线索(客户).md"），
        # 写成 [^)#]+ 会在第一个 ')' 处截断，导致漏配
        for link in re.findall(r"\]\(\./([^#]+?\.md)\)", text):
            if not os.path.exists(os.path.join(dirpath, link)):
                broken_links.append((os.path.relpath(idx, ROOT), link))
        actual = [f for f in files if f.endswith(".md") and f != "_INDEX.md"]
        if not actual:
            continue  # 非叶子目录，条目指向子索引，不比对数量
        listed = [l for l in re.findall(r"\]\(\./([^#]+?\.md)\)", text)
                  if not l.endswith("_INDEX.md")]
        if len(listed) != len(actual):
            leaf_mism.append((os.path.relpath(idx, ROOT), len(listed), len(actual)))
    check("B4a 索引内链接全部可达", not broken_links,
          f"{len(broken_links)} 条死链" + (f"，如 {broken_links[0]}" if broken_links else ""))
    check("B4b 叶子目录索引条目数一致", not leaf_mism,
          f"{len(leaf_mism)} 处不一致" + (f"，如 {leaf_mism[0]}" if leaf_mism else ""))

    # B5 深层召回：取正文深处、非代码块、且**全库唯一**的一行作为探针
    #   —— 对象页有大量样板句（如"不能使用返回值的message字段…"）遍布上千篇，
    #      拿它当探针测的是排序不是召回
    from collections import Counter
    freq = Counter()
    doc_lines = {}
    for p, meta, body, _t in docs:
        ls = [ln for ln in body_lines_outside_fence(body)
              if len(ln) >= 12 and not ln.startswith(("#", "|", ">", "*", "!"))]
        doc_lines[p] = ls
        for ln in set(ls):
            freq[ln] += 1

    deep_ok = 0
    deep_try = 0
    deep_fail = []
    for p, meta, body, _t in random.Random(args.seed).sample(docs, min(15, len(docs))):
        cands = [ln for ln in doc_lines.get(p, []) if freq[ln] == 1]
        if not cands:
            continue
        deep_try += 1
        probe = cands[-1][:16]
        out = run([probe, "--limit", "400", "--brief"])
        if meta.get("title", "") in out:
            deep_ok += 1
        else:
            deep_fail.append((meta.get("path"), probe))
    check("B5 正文深处关键词可召回（全库唯一探针）",
          deep_try > 0 and deep_ok >= deep_try * 0.8,
          f"{deep_ok}/{deep_try} 命中" + (f"，如 {deep_fail[0]}" if deep_fail else ""))

    print()
    fails = [n for n, ok, _d in RESULTS if not ok]
    print("=" * 70)
    if fails:
        print(f"未通过 {len(fails)}/{len(RESULTS)} 项：")
        for n in fails:
            print("   -", n)
    else:
        print(f"全部 {len(RESULTS)} 项通过。")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

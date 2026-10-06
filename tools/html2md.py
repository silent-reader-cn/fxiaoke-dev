# -*- coding: utf-8 -*-
"""
零依赖 HTML → Markdown 转换器（针对纷享销客开发者手册的 VuePress 2 + Plume 产物）。

只依赖标准库 html.parser。分两步：
  1) extract_page(html) —— 从整页 HTML 里抠出标题 / 面包屑 / 更新日期 / 正文区
  2) html_to_markdown(fragment) —— 把正文区 HTML 渲染成 Markdown

针对本站的三处特殊结构做了专门处理：
  * shiki 代码块：<div class="language-xxx line-numbers-mode"><pre><code> ，
    每个 <span class="line"> 是一行；同级 <div class="line-numbers"> 必须丢弃
  * 标题锚点：<h3 id="x"><a class="header-anchor">…</a></h3> 要剥掉锚点
  * 面包屑：<ol typeof="BreadcrumbList"> 里每个 <meta property="name" content="…">

也可当命令行用：
    python tools/html2md.py page.html            # 输出 Markdown 到 stdout
    python tools/html2md.py page.html --meta     # 只输出 frontmatter 字段
"""
import html as _html
import os
import re
import sys
from html.parser import HTMLParser

ORIGIN = "https://developer.fxiaoke.com"

# 需要整棵子树丢弃的 class **token**（按空格切分后精确比对，
# 不能用子串匹配 —— 正文容器的 class 里带 "external-link-icon-enabled"，
# 子串匹配会把整篇正文丢掉）
DROP_CLASS_TOKENS = {
    "header-anchor",
    "line-numbers",
    "line-number",
    "copy-code-button",
    "vp-copy",
    "external-link-icon",
    "outline-marker",
    "edit-link",
    "last-updated",
    "prev-next",
}

# 自闭合 / 空元素
VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

BLOCK_TAGS = {
    "p", "div", "section", "article", "main", "header", "footer", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "table", "thead",
    "tbody", "tfoot", "tr", "td", "th", "pre", "blockquote", "hr", "figure",
    "figcaption", "dl", "dt", "dd", "details", "summary", "form",
}


class Node:
    __slots__ = ("tag", "attrs", "children", "parent", "text")

    def __init__(self, tag, attrs=None, text=None, parent=None):
        self.tag = tag
        self.attrs = attrs or {}
        self.children = []
        self.parent = parent
        self.text = text

    def cls(self):
        return self.attrs.get("class", "")

    def get(self, key, default=""):
        return self.attrs.get(key, default)

    def __repr__(self):
        return f"<{self.tag} {self.attrs!r} children={len(self.children)}>"


class _DomBuilder(HTMLParser):
    """把 HTML 片段建成轻量 DOM。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root")
        self.stack = [self.root]

    def _cur(self):
        return self.stack[-1]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {k: (v if v is not None else "") for k, v in attrs}, parent=self._cur())
        self._cur().children.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, {k: (v if v is not None else "") for k, v in attrs}, parent=self._cur())
        self._cur().children.append(node)

    def handle_endtag(self, tag):
        # 容错：向上找到匹配的开放标签
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        if not data:
            return
        self._cur().children.append(Node("#text", text=data, parent=self._cur()))

    def handle_comment(self, data):
        pass  # Vue 的 <!--[--> 之类的注释一律忽略


def build_dom(fragment):
    b = _DomBuilder()
    b.feed(fragment)
    b.close()
    return b.root


def _should_drop(node):
    cls = node.cls()
    if not cls:
        return False
    return bool(DROP_CLASS_TOKENS.intersection(cls.split()))


def _norm_ws(s):
    return re.sub(r"[ \t\r\n\u00a0]+", " ", s)


def _abs_url(url):
    if not url:
        return url
    if url.startswith(("http://", "https://", "mailto:", "tel:", "#")):
        return url
    if url.startswith("/"):
        return ORIGIN + url
    return url


# ---------------------------------------------------------------- 行内渲染

def render_inline(node):
    """把节点渲染成行内 Markdown 文本。"""
    if node.tag == "#text":
        return _norm_ws(node.text)
    out = []
    for ch in node.children:
        if ch.tag == "#text":
            out.append(_norm_ws(ch.text))
        elif ch.tag in ("strong", "b"):
            out.append("**" + render_inline(ch).strip() + "**")
        elif ch.tag in ("em", "i"):
            out.append("*" + render_inline(ch).strip() + "*")
        elif ch.tag in ("del", "s", "strike"):
            out.append("~~" + render_inline(ch).strip() + "~~")
        elif ch.tag == "code":
            txt = _text_of(ch)
            out.append("`" + txt + "`" if txt else "")
        elif ch.tag == "br":
            out.append("<br>")
        elif ch.tag == "a":
            if "header-anchor" in ch.cls().split():
                # 标题锚点：只保留其中的文字，不要链接
                out.append(render_inline(ch))
                continue
            if _should_drop(ch):
                continue
            txt = render_inline(ch).strip()
            href = _abs_url(ch.get("href"))
            if not txt:
                continue
            out.append(f"[{txt}]({href})" if href else txt)
        elif ch.tag == "img":
            alt = ch.get("alt") or ch.get("title") or "image"
            src = _abs_url(ch.get("src") or ch.get("data-src"))
            out.append(f"![{alt}]({src})" if src else "")
        elif ch.tag in ("span", "small", "sub", "sup", "abbr", "mark", "u", "time"):
            out.append(render_inline(ch))
        else:
            out.append(render_inline(ch))
    s = "".join(out)
    # 合并因标签切分产生的多余空格
    s = re.sub(r"[ \t]{2,}", " ", s)
    return s


def _text_of(node):
    """取纯文本（用于 code）。"""
    parts = []
    for ch in node.children:
        if ch.tag == "#text":
            parts.append(ch.text)
        else:
            parts.append(_text_of(ch))
    return "".join(parts)


# ---------------------------------------------------------------- 代码块

def _is_code_wrapper(node):
    """
    判断是否是代码块容器，返回语言名（可能为空串）。

    注意语言名可以为空：本站有 `class="language- line-numbers-mode"` 这种
    没有语言的代码块（`data-ext=""`），正则必须用 `*` 而不是 `+`，
    否则这些块会被当成普通 div，围栏直接丢失。
    """
    if node.tag not in ("div", "pre"):
        return None
    cls = node.cls()
    if cls:
        m = re.search(r"\blanguage-([A-Za-z0-9_+#-]*)", cls)
        if m:
            return m.group(1)
    if node.get("data-highlighter") == "shiki":
        return ""
    return None


def render_code_block(node, lang):
    """从 shiki 结构里还原代码文本。"""
    code_el = None
    for el in _iter(node):
        if el.tag == "code":
            code_el = el
            break
    if code_el is None:
        code_el = node
    # 优先按 <span class="line"> 分行（shiki）
    lines = [c for c in code_el.children if c.tag == "span" and "line" in c.cls().split()]
    if lines:
        text = "\n".join(_text_of(ln) for ln in lines)
    else:
        text = _text_of(code_el)
    text = text.replace("\u00a0", " ")
    text = text.rstrip("\n")
    # 反引号围栏长度要大于内容里最长的连续反引号
    fence = "```"
    m = re.findall(r"`{3,}", text)
    if m:
        fence = "`" * (max(len(x) for x in m) + 1)
    return f"{fence}{lang}\n{text}\n{fence}\n"


def _iter(node):
    """先序遍历。"""
    for ch in node.children:
        yield ch
        yield from _iter(ch)


# ---------------------------------------------------------------- 列表

INLINE_TAGS = {"span", "a", "strong", "b", "em", "i", "code", "img", "br",
               "del", "s", "small", "sub", "sup", "u", "mark", "time", "abbr"}


def render_list(node, indent=0, ordered=False):
    lines = []
    idx = 0
    for li in node.children:
        if li.tag != "li":
            continue
        idx += 1
        marker = f"{idx}." if ordered else "-"
        # li 的内容分两路：行内部分拼进条目标题，块级部分挂到条目下面
        inline_parts = []
        sub_blocks = []
        for ch in li.children:
            if ch.tag in ("ul", "ol"):
                sub_blocks.append(render_list(ch, indent + 1, ch.tag == "ol").strip())
            elif ch.tag == "#text":
                t = _norm_ws(ch.text)
                if t.strip():
                    inline_parts.append(t.strip())
            elif ch.tag in INLINE_TAGS:
                t = render_inline(ch)
                if t.strip():
                    inline_parts.append(t.strip())
            else:
                # p / div / blockquote / pre / table / 代码块容器 …
                b = render_block(ch, indent + 1).strip()
                if b:
                    sub_blocks.append(b)
        head = " ".join(p for p in inline_parts if p).strip()
        if not head and not sub_blocks:
            idx -= 1  # 空 li 不占序号
            continue
        pad = "  " * indent
        lines.append(f"{pad}{marker} {head}".rstrip())
        for sb in sub_blocks:
            if not sb:
                continue
            for ln in sb.split("\n"):
                lines.append(ln if ln.startswith("  " * (indent + 1))
                             else f"{'  ' * (indent + 1)}{ln}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- 表格

def render_table(node):
    rows = []
    for tr in _iter(node):
        if tr.tag != "tr":
            continue
        cells = [c for c in tr.children if c.tag in ("td", "th")]
        if not cells:
            continue
        is_head = any(c.tag == "th" for c in cells)
        vals = []
        for c in cells:
            txt = render_inline(c).strip()
            txt = txt.replace("\n", "<br>").replace("|", "\\|")
            vals.append(txt)
        rows.append((is_head, vals))
    if not rows:
        return ""
    ncol = max(len(v) for _, v in rows)
    for _, v in rows:
        while len(v) < ncol:
            v.append("")
    # 表头：取第一个 th 行，否则用空表头
    head_idx = next((i for i, (h, _) in enumerate(rows) if h), None)
    if head_idx is None:
        header = [""] * ncol
        body = [v for _, v in rows]
    else:
        header = rows[head_idx][1]
        body = [v for i, (_, v) in enumerate(rows) if i != head_idx]
    out = ["| " + " | ".join(header) + " |",
           "| " + " | ".join(["---"] * ncol) + " |"]
    for v in body:
        out.append("| " + " | ".join(v) + " |")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- 块渲染

def render_block(node, indent=0):
    """渲染一个块级节点，返回 Markdown（末尾带换行）。"""
    if node.tag == "#text":
        t = _norm_ws(node.text)
        return t
    if node.tag == "#root":
        return render_children(node)
    if _should_drop(node):
        return ""

    lang = _is_code_wrapper(node)
    if lang is not None:
        return render_code_block(node, lang)

    tag = node.tag
    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        level = int(tag[1])
        txt = render_inline(node).strip()
        return f"\n{'#' * level} {txt}\n\n" if txt else ""
    if tag == "p":
        txt = render_inline(node).strip()
        return f"{txt}\n\n" if txt else ""
    if tag == "hr":
        return "\n---\n\n"
    if tag == "br":
        return "\n"
    if tag == "blockquote":
        inner = render_children(node).strip()
        return "\n".join("> " + ln if ln else ">" for ln in inner.split("\n")) + "\n\n"
    if tag == "ul":
        return "\n" + render_list(node, indent, False) + "\n"
    if tag == "ol":
        return "\n" + render_list(node, indent, True) + "\n"
    if tag == "table":
        return "\n" + render_table(node) + "\n"
    if tag == "pre":
        return render_code_block(node, "")
    if tag == "img":
        alt = node.get("alt") or "image"
        src = _abs_url(node.get("src") or node.get("data-src"))
        return f"![{alt}]({src})\n\n" if src else ""
    if tag == "figure":
        return render_children(node) + "\n"
    if tag in BLOCK_TAGS:
        return render_children(node)
    # 行内标签直接落在块位置
    return render_inline(node)


def render_children(node):
    out = []
    for ch in node.children:
        if ch.tag == "#text":
            t = _norm_ws(ch.text)
            if t.strip():
                out.append(t)
            continue
        out.append(render_block(ch, 0))
    return "".join(out)


def normalize_heading_levels(md, target_top=2):
    """
    把正文里的最高一级标题提到 target_top。
    本站正文用 h3 起步（h1 被页面标题占了），不调整就会出现 h1 → h3 的空档。
    只处理围栏代码块之外的行。
    """
    lines = md.split("\n")
    levels = []
    fence = None
    for ln in lines:
        if fence:
            if ln.strip().startswith(fence):
                fence = None
            continue
        m = re.match(r"^\s*(#{1,6}) ", ln)
        if m:
            levels.append(len(m.group(1)))
        else:
            fm = re.match(r"^\s*(`{3,}|~{3,})", ln)
            if fm:
                fence = fm.group(1)
    if not levels:
        return md
    shift = target_top - min(levels)
    if shift == 0:
        return md
    out = []
    fence = None
    for ln in lines:
        if fence:
            out.append(ln)
            if ln.strip().startswith(fence):
                fence = None
            continue
        m = re.match(r"^(\s*)(#{1,6}) (.*)$", ln)
        if m:
            lv = max(1, min(6, len(m.group(2)) + shift))
            out.append(f"{m.group(1)}{'#' * lv} {m.group(3)}")
            continue
        fm = re.match(r"^\s*(`{3,}|~{3,})", ln)
        if fm:
            fence = fm.group(1)
        out.append(ln)
    return "\n".join(out)


def html_to_markdown(fragment, normalize_headings=True):
    dom = build_dom(fragment)
    md = render_children(dom)
    # 收敛空白：行尾空格、3+ 空行 -> 2
    md = re.sub(r"[ \t]+\n", "\n", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    md = md.strip() + "\n"
    if normalize_headings:
        md = normalize_heading_levels(md)
    return md


# ---------------------------------------------------------------- 页面抽取

def extract_page(html):
    """从整页 HTML 抽出元数据与正文区 HTML。"""
    meta = {}

    # 面包屑（只在正文之前的 BreadcrumbList 里）
    bcm = re.search(r'typeof="BreadcrumbList".*?</ol>', html, re.S)
    crumbs = re.findall(r'<meta property="name" content="([^"]*)"', bcm.group(0)) if bcm else []
    meta["breadcrumb"] = crumbs

    # 标题
    m = re.search(r'<h1 class="vp-doc-title page-title"[^>]*>(.*?)</h1>', html, re.S)
    title = ""
    if m:
        title = re.sub(r"<!--.*?-->", "", m.group(1))
        title = _html.unescape(title).strip()
    meta["title"] = title

    # 更新日期
    m = re.search(r'class="create-time"[^>]*>(.*?)</p>', html, re.S)
    if m:
        d = re.search(r">\s*(\d{4}-\d{2}-\d{2})\s*<", m.group(1))
        meta["updatedAt"] = d.group(1) if d else ""
    else:
        meta["updatedAt"] = ""

    # 阅读时长
    m = re.search(r'class="reading-time"[^>]*>(.*?)</p>', html, re.S)
    if m:
        rt = re.findall(r">([^<]*字[^<]*)<", m.group(1))
        meta["readingTime"] = rt[0].strip() if rt else ""

    # 正文区：class 里含 "vp-doc plume-content" 的 div
    i = html.find("vp-doc plume-content")
    content = ""
    if i > 0:
        start = html.rfind("<div", 0, i)
        end = _match_div(html, start)
        content = html[start:end] if end > 0 else html[start:]
    meta["contentHtml"] = content
    return meta


def _match_div(text, start):
    """start 指向 '<div'，返回配对 '</div>' 之后的下标。"""
    depth = 0
    k = start
    while k < len(text):
        nxt_open = text.find("<div", k)
        nxt_close = text.find("</div>", k)
        if nxt_close < 0:
            return -1
        if 0 <= nxt_open < nxt_close:
            depth += 1
            k = nxt_open + 4
        else:
            depth -= 1
            k = nxt_close + 6
            if depth == 0:
                return k
    return -1


def convert_file(path):
    html = open(path, encoding="utf-8").read()
    meta = extract_page(html)
    meta["markdown"] = html_to_markdown(meta.pop("contentHtml"))
    return meta


def main():
    ap = sys.argv[1:]
    if not ap:
        print(__doc__)
        return 1
    path = ap[0]
    meta = convert_file(path)
    if "--meta" in ap:
        for k, v in meta.items():
            if k == "markdown":
                continue
            print(f"{k}: {v!r}")
        return 0
    print(meta["markdown"])
    return 0


if __name__ == "__main__":
    sys.exit(main())

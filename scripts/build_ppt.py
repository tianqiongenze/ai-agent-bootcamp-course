#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_ppt.py — 从 16 份教学方案（docs/03-教学方案/L01–L16）生成每讲授课 PPT。

设计原则：
  1. 教学方案 md 是单一事实源；PPT 由它驱动生成（课随产动：改方案→重跑本脚本）。
  2. 统一双元制工程风格模板（深蓝主色，六步法导航），16:9。
  3. 每讲页面结构固定：封面→议程→学习情境→任务→目标→重点→难点→准备→
     六步法总表→资讯→计划→决策→实施(可多页)→检查→评价/学生讲堂→
     企业站任务→评价设计→课后费曼→结束页。
  4. 内容溢出自动分页（续页标题加"（续）"）与字号自适应。

用法：
  python3 scripts/build_ppt.py            # 生成全部 16 讲
  python3 scripts/build_ppt.py L01 L07    # 只生成指定讲次
"""
import re
import sys
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "docs" / "03-教学方案"
OUT_DIR = ROOT / "docs" / "04-课件PPT"

# ---------- 主题 ----------
C_PRIMARY = RGBColor(0x1B, 0x2A, 0x4A)   # 深藏蓝
C_ACCENT = RGBColor(0x2E, 0x86, 0xDE)    # 强调青蓝
C_HIGHLIGHT = RGBColor(0xF3, 0x9C, 0x12) # 橙（重点）
C_TEXT = RGBColor(0x2C, 0x33, 0x45)
C_MUTED = RGBColor(0x6B, 0x7A, 0x90)
C_BG_LIGHT = RGBColor(0xF2, 0xF5, 0xFA)
C_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
C_TABLE_HEAD = RGBColor(0x24, 0x3B, 0x63)
C_CODE_BG = RGBColor(0x0F, 0x1B, 0x2D)
C_CODE_TX = RGBColor(0xC9, 0xE0, 0xFF)

FONT_EA = "Microsoft YaHei"
FONT_LAT = "Calibri"

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
CONTENT_X = Inches(0.55)
CONTENT_W = SLIDE_W - Inches(1.1)
CONTENT_TOP = Inches(1.28)
CONTENT_BOTTOM = Inches(6.95)
CONTENT_H = CONTENT_BOTTOM - CONTENT_TOP

STEP_NAMES = ["资讯", "计划", "决策", "实施", "检查", "评价＋学生讲堂"]

# ============================================================================
# 一、Markdown 解析（针对本课程规整 GFM 的轻量解析器）
# ============================================================================

def parse_blocks(md_text):
    """把 md 文本解析成块流：
    [('h1', text) | ('h2', text) | ('h3', text) | ('p', text) |
     ('ul', [item...]) | ('ol', [item...]) | ('table', rows) | ('code', text) |
     ('quote', text)]"""
    lines = md_text.splitlines()
    blocks, i, n = [], 0, len(lines)
    while i < n:
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            continue
        if s.startswith("```"):
            buf = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            blocks.append(("code", "\n".join(buf)))
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            level = len(m.group(1))
            blocks.append((f"h{level}", m.group(2).strip()))
            i += 1
            continue
        if s.startswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                raw = lines[i].strip().strip("|")
                cells = [c.strip() for c in raw.split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            if rows:
                blocks.append(("table", rows))
            continue
        if s.startswith("> "):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            blocks.append(("quote", " ".join(x for x in buf if x)))
            continue
        m = re.match(r"^[-*]\s+(.*)$", s)
        if m:
            items, while_i = [], i
            while i < n:
                s2 = lines[i].strip()
                m2 = re.match(r"^[-*]\s+(.*)$", s2)
                if m2:
                    items.append(m2.group(1))
                    i += 1
                elif s2 and items and not s2.startswith("#") and not s2.startswith("|"):
                    items[-1] += " " + s2  # 折行续接
                    i += 1
                else:
                    break
            blocks.append(("ul", items))
            continue
        m = re.match(r"^(\d+)[.、)]\s*(.*)$", s)
        if m:
            items, while_i = [], i
            while i < n:
                s2 = lines[i].strip()
                m2 = re.match(r"^(\d+)[.、)]\s*(.*)$", s2)
                if m2:
                    items.append(m2.group(2))
                    i += 1
                elif s2 and items and not s2.startswith("#") and not s2.startswith("|") and not s2.startswith("```"):
                    items[-1] += " " + s2
                    i += 1
                else:
                    break
            blocks.append(("ol", items))
            continue
        # 普通段落（含粗体行）
        blocks.append(("p", s))
        i += 1
    return blocks


def split_sections(blocks, level=2, pattern=None):
    """把块流按指定级标题切分成 [(title, sub_blocks), ...]，标题前的内容归 '' 组。"""
    sections, cur_title, cur = [], "", []
    for b in blocks:
        if b[0] == f"h{level}":
            if pattern and not re.search(pattern, b[1]):
                cur.append(b)
                continue
            if cur or cur_title:
                sections.append((cur_title, cur))
            cur_title, cur = b[1], []
        else:
            cur.append(b)
    if cur or cur_title:
        sections.append((cur_title, cur))
    return sections


def inline_runs(text):
    """把 **bold** 内联标记解析成 [(text, bold)] 序列。"""
    runs, pos = [], 0
    for m in re.finditer(r"\*\*(.+?)\*\*", text):
        if m.start() > pos:
            runs.append((text[pos:m.start()], False))
        runs.append((m.group(1), True))
        pos = m.end()
    if pos < len(text):
        runs.append((text[pos:], False))
    if not runs:
        runs = [(text, False)]
    return runs


def strip_md(text):
    """去掉行内标记，用于标题/封面等场合。"""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    return text

# ============================================================================
# 二、PPT 低层渲染助手
# ============================================================================

def set_run_font(run, size, bold=False, color=C_TEXT, italic=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = FONT_LAT
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = rPr.makeelement(qn("a:ea"), {})
        rPr.append(ea)
    ea.set("typeface", FONT_EA)


def add_textbox(slide, x, y, w, h, wrap=True):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    return tb, tf


def add_rect(slide, x, y, w, h, fill, line=None):
    from pptx.enum.shapes import MSO_SHAPE
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(0.75)
    sh.shadow.inherit = False
    return sh

# ============================================================================
# 三、页面骨架
# ============================================================================

COURSE_NAME = "AI驱动的数据中台项目实战"


def page_header(slide, title, subtitle=None, step_idx=None, page_no=None, total=None):
    """内容页顶部色带 + 标题 + 页脚。"""
    add_rect(slide, 0, 0, SLIDE_W, Inches(0.16), C_ACCENT)
    add_rect(slide, 0, Inches(0.16), SLIDE_W, Inches(0.86), C_PRIMARY)
    tb, tf = add_textbox(slide, CONTENT_X, Inches(0.24), CONTENT_W, Inches(0.7))
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = title
    set_run_font(r, 26, bold=True, color=C_WHITE)
    if subtitle:
        p2 = tf.add_paragraph()
        r2 = p2.add_run()
        r2.text = subtitle
        set_run_font(r2, 13, color=RGBColor(0xB8, 0xC9, 0xE4))
    # 六步法导航条
    if step_idx is not None:
        seg_w = Inches(1.62)
        gap = Inches(0.06)
        x0 = SLIDE_W - Inches(0.55) - seg_w * 6 - gap * 5
        for k, name in enumerate(STEP_NAMES):
            fill = C_HIGHLIGHT if k == step_idx else RGBColor(0x3A, 0x4E, 0x75)
            add_rect(slide, x0 + k * (seg_w + gap), Inches(1.12), seg_w, Inches(0.30), fill)
            tb2, tf2 = add_textbox(slide, x0 + k * (seg_w + gap), Inches(1.15), seg_w, Inches(0.26))
            p3 = tf2.paragraphs[0]
            p3.alignment = PP_ALIGN.CENTER
            r3 = p3.add_run()
            r3.text = name
            set_run_font(r3, 11, bold=(k == step_idx),
                         color=C_PRIMARY if k == step_idx else C_WHITE)
    page_footer(slide, page_no, total)


def page_footer(slide, page_no=None, total=None):
    tb, tf = add_textbox(slide, CONTENT_X, Inches(7.08), CONTENT_W, Inches(0.3))
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = f"《{COURSE_NAME}》｜德国双元制本土化 · 费曼学习法 · 布鲁姆认知分层"
    set_run_font(r, 9, color=C_MUTED)
    if page_no is not None:
        tb2, tf2 = add_textbox(slide, SLIDE_W - Inches(1.3), Inches(7.08), Inches(0.75), Inches(0.3))
        p2 = tf2.paragraphs[0]
        p2.alignment = PP_ALIGN.RIGHT
        r2 = p2.add_run()
        r2.text = f"{page_no:02d}" + (f" / {total:02d}" if total else "")
        set_run_font(r2, 9, color=C_MUTED)


def new_content_page(prs, title, subtitle=None, step_idx=None, page_no=None, total=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    page_header(slide, title, subtitle, step_idx, page_no, total)
    return slide

# ============================================================================
# 四、内容块渲染（带高度估算与自动分页）
# ============================================================================

def est_block_height(block, width_in, size):
    kind, payload = block
    if kind in ("h3",):
        return size * 1.9 + 6
    if kind in ("p", "quote"):
        chars_per_line = max(int(width_in * 72 / (size * 1.05)), 8)
        text = strip_md(payload)
        lines = max(1, -(-len(text) // chars_per_line))
        return lines * size * 1.45 + 6
    if kind in ("ul", "ol"):
        total = 0
        chars_per_line = max(int(width_in * 72 / (size * 1.02)), 8)
        for it in payload:
            t = strip_md(it)
            lines = max(1, -(-len(t) // chars_per_line))
            total += lines * size * 1.4 + 3
        return total + 2
    if kind == "table":
        rows = payload
        cols = max(len(r) for r in rows) if rows else 1
        col_w = width_in / cols
        total = 0
        body_size = max(size - 3, 9)
        for ri, row in enumerate(rows):
            max_lines = 1
            cpl = max(int(col_w * 72 / (body_size * 1.02)), 4)
            for cell in row:
                lines = max(1, -(-len(strip_md(cell)) // cpl))
                max_lines = max(max_lines, lines)
            total += max_lines * body_size * 1.5 + 6
        return total + 4
    if kind == "code":
        lines = payload.count("\n") + 1
        return min(lines * (size - 2) * 1.35 + 12, CONTENT_H / 914400 * 72 * 0.6)
    return size * 1.6


def render_blocks(slide, blocks, y_start, size=15, step_idx=None, cursor_state=None):
    """在 y_start 起渲染块流，返回结束 y（Emu）。溢出时写入 cursor_state 触发续页。"""
    y = y_start
    for bi, block in enumerate(blocks):
        kind, payload = block
        h = est_block_height(block, CONTENT_W / 914400, size)
        if y + h > CONTENT_BOTTOM and (kind != "p" or strip_md(payload)):
            if cursor_state is not None:
                cursor_state["rest"] = blocks[bi:]
                return y, True
            # 无游标模式：尽力收缩字号后硬放（保守处理，正常路径不应走到）
            continue
        y = render_block(slide, block, y, size)
    return y, False


def render_block(slide, block, y, size):
    kind, payload = block
    if kind == "h3":
        tb, tf = add_textbox(slide, CONTENT_X, y, CONTENT_W, Emu(int(size * 1.9 * 12700) + 6 * 12700))
        p = tf.paragraphs[0]
        r = p.add_run()
        r.text = "▍" + strip_md(payload)
        set_run_font(r, size + 1, bold=True, color=C_ACCENT)
        return y + Emu(int((size * 1.9 + 6) * 12700))
    if kind == "p":
        return render_para(slide, payload, y, size, color=C_TEXT)
    if kind == "quote":
        return render_para(slide, "💡 " + payload, y, size, color=C_MUTED, italic=True)
    if kind in ("ul", "ol"):
        return render_list(slide, payload, y, size, ordered=(kind == "ol"))
    if kind == "table":
        return render_table(slide, payload, y, size)
    if kind == "code":
        return render_code(slide, payload, y, size)
    return y


def render_para(slide, text, y, size, color=C_TEXT, italic=False):
    h_pt = est_block_height(("p", text), CONTENT_W / 914400, size)
    tb, tf = add_textbox(slide, CONTENT_X, y, CONTENT_W, Emu(int(h_pt * 12700) + 20000))
    p = tf.paragraphs[0]
    for seg, bold in inline_runs(text):
        r = p.add_run()
        r.text = seg
        set_run_font(r, size, bold=bold, color=color, italic=italic)
    return y + Emu(int(h_pt * 12700))


def render_list(slide, items, y, size, ordered=False):
    marker = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮"
    for k, item in enumerate(items):
        text = strip_md(item)
        h_pt = est_block_height(("p", text), CONTENT_W / 914400, size)
        tb, tf = add_textbox(slide, CONTENT_X, y, CONTENT_W, Emu(int(h_pt * 12700) + 20000))
        p = tf.paragraphs[0]
        rm = p.add_run()
        rm.text = (f"{k+1}. " if ordered else ("• " if len(items) <= 12 else marker[k % len(marker)] + " "))
        set_run_font(rm, size, bold=True, color=C_ACCENT)
        for seg, bold in inline_runs(item):
            r = p.add_run()
            r.text = seg
            set_run_font(r, size, bold=bold)
        y += Emu(int(h_pt * 12700) + 30000)
    return y


def render_code(slide, code, y, size):
    lines = code.splitlines() or [""]
    line_h = max(size - 2, 9) * 1.35
    max_lines = 14
    shown = lines[:max_lines]
    h = int(len(shown) * line_h + 14)
    sh = add_rect(slide, CONTENT_X, y, CONTENT_W, Emu(int(h * 12700)), C_CODE_BG)
    tf = sh.text_frame
    tf.word_wrap = True
    tf.margin_left = Emu(int(0.12 * 914400))
    tf.margin_top = Emu(int(0.05 * 914400))
    tf.vertical_anchor = MSO_ANCHOR.TOP
    for i, ln in enumerate(shown):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        r = p.add_run()
        r.text = ln[:110]
        set_run_font(r, max(size - 2, 9), color=C_CODE_TX)
    y = y + Emu(int(h * 12700)) + Emu(60000)
    if len(lines) > max_lines:
        tb, tf2 = add_textbox(slide, CONTENT_X, y, CONTENT_W, Inches(0.25))
        p = tf2.paragraphs[0]
        r = p.add_run()
        r.text = f"…（另有 {len(lines)-max_lines} 行，详见教学方案原文）"
        set_run_font(r, 10, color=C_MUTED)
        y += Emu(int(0.28 * 914400 * 914400 // 914400)) if False else Emu(int(0.28 * 914400))
    return y


def render_table(slide, rows, y, size):
    if not rows:
        return y
    ncols = max(len(r) for r in rows)
    body_size = max(size - 3, 9)
    total_h = est_block_height(("table", rows), CONTENT_W / 914400, size)
    max_rows = 16
    shown = rows[:max_rows]
    gf = slide.shapes.add_table(len(shown), ncols, CONTENT_X, y, CONTENT_W, Emu(int(min(total_h, CONTENT_H / 914400 * 72) * 12700)))
    table = gf.table
    # 关闭默认样式的斑马纹，统一配色
    tbl_pr = table._tbl.find(qn("a:tblPr"))
    tbl_pr.set("bandRow", "0")
    tbl_pr.set("firstRow", "0")
    for ri, row in enumerate(shown):
        for ci in range(ncols):
            cell = table.cell(ri, ci)
            cell.margin_left = Emu(int(0.06 * 914400))
            cell.margin_right = Emu(int(0.04 * 914400))
            cell.margin_top = Emu(int(0.02 * 914400))
            cell.margin_bottom = Emu(int(0.02 * 914400))
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            text = strip_md(row[ci]) if ci < len(row) else ""
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            r = p.add_run()
            r.text = text
            if ri == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = C_TABLE_HEAD
                set_run_font(r, body_size, bold=True, color=C_WHITE)
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = C_BG_LIGHT if ri % 2 == 0 else C_WHITE
                set_run_font(r, body_size, color=C_TEXT)
    y = y + gf.height + Emu(50000)
    if len(rows) > max_rows:
        tb, tf = add_textbox(slide, CONTENT_X, y, CONTENT_W, Inches(0.25))
        p = tf.paragraphs[0]
        r = p.add_run()
        r.text = f"…（另有 {len(rows)-max_rows} 行，详见教学方案原文）"
        set_run_font(r, 10, color=C_MUTED)
        y += Emu(int(0.28 * 914400))
    return y

# ============================================================================
# 五、每讲 PPT 组装
# ============================================================================

def parse_lesson(path):
    text = path.read_text(encoding="utf-8")
    blocks = parse_blocks(text)
    # 标题：h1 = 学习情境 Lxx：…
    title = next((strip_md(b[1]) for b in blocks if b[0] == "h1"), path.stem)
    m = re.match(r"学习情境\s*(L\d+)[:：]\s*(.*)", title)
    lesson_no = m.group(1) if m else ""
    lesson_title = (m.group(2) if m else title)
    # 去掉标题尾部学时标注（如"（6 学时）"），封面另有学时信息条
    lesson_title = re.sub(r"[（(]\s*\d+\s*学时\s*[）)]\s*$", "", lesson_title).strip()
    sections = split_sections(blocks, level=2)
    out = {}
    for st, sb in sections:
        key = st[:2] if st[:1].isdigit() or st[:1] in "一二三四五六七八九十" else st
        out[st] = sb
    return lesson_no, lesson_title, out


def get_section(sections, *keywords):
    for title, blocks in sections.items():
        for kw in keywords:
            if kw in title:
                return title, blocks
    return None, []


def step_of(h3_title):
    for k, name in enumerate(STEP_NAMES):
        if name in h3_title or (name == "评价＋学生讲堂" and "评价" in h3_title and "讲堂" in h3_title):
            return k
    if "资讯" in h3_title:
        return 0
    if "计划" in h3_title:
        return 1
    if "决策" in h3_title:
        return 2
    if "实施" in h3_title:
        return 3
    if "检查" in h3_title:
        return 4
    if "评价" in h3_title or "讲堂" in h3_title:
        return 5
    return None


def build_lesson_ppt(md_path, total_pages_hint=None):
    lesson_no, lesson_title, sections = parse_lesson(md_path)
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    # ---------- 预估总页数（用于页码） ----------
    # 简单策略：先构建页面函数列表再统一渲染，这里以"渲染时序号"近似，最后回填。
    # 为避免两遍构建，页码在渲染过程中递增；结束页最后加。
    page_counter = {"n": 0}

    # ---------- 封面 ----------
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, SLIDE_W, SLIDE_H, C_PRIMARY)
    add_rect(slide, 0, Inches(4.9), SLIDE_W, Inches(0.06), C_HIGHLIGHT)
    tb, tf = add_textbox(slide, Inches(0.9), Inches(1.15), Inches(11.5), Inches(1.0))
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = f"《{COURSE_NAME}》"
    set_run_font(r, 30, bold=True, color=RGBColor(0x9E, 0xBE, 0xE8))
    tb, tf = add_textbox(slide, Inches(0.9), Inches(2.15), Inches(11.6), Inches(1.9))
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = lesson_title
    set_run_font(r, 40, bold=True, color=C_WHITE)
    p2 = tf.add_paragraph()
    p2.space_before = Pt(10)
    r2 = p2.add_run()
    r2.text = f"学习情境 {lesson_no} ｜ 授课课件"
    set_run_font(r2, 20, color=C_HIGHLIGHT)
    # 封面信息条
    _, info_blocks = get_section(sections, "学习情境基本信息")
    info_line = ""
    for b in info_blocks:
        if b[0] == "table" and b[1]:
            row = b[1][1] if len(b[1]) > 1 else []
            cells = [strip_md(c) for c in row]
            if len(cells) >= 4:
                info_line = f"学时 {cells[3]}　·　布鲁姆层级 {cells[4] if len(cells) > 4 else ''}　·　{cells[5] if len(cells) > 5 else ''}"
            break
    if not info_line:
        info_line = "六学时 ｜ 校内理实一体 + 企业实训站"
    tb, tf = add_textbox(slide, Inches(0.9), Inches(5.2), Inches(11.6), Inches(0.5))
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = info_line
    set_run_font(r, 15, color=RGBColor(0xC8, 0xD6, 0xEE))
    tb, tf = add_textbox(slide, Inches(0.9), Inches(6.6), Inches(11.6), Inches(0.4))
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = "德国双元制本土化 · 六步工作法 · 费曼学生讲堂 · 布鲁姆认知分层"
    set_run_font(r, 12, color=RGBColor(0x8A, 0x9D, 0xBE))
    page_counter["n"] += 1

    # ---------- 议程 ----------
    page_counter["n"] += 1
    slide = new_content_page(prs, "本讲导航", f"学习情境 {lesson_no} · 六步工作法", page_no=page_counter["n"])
    y = CONTENT_TOP + Inches(0.15)
    agenda = [
        ("01", "学习情境与客户委托单", "来自 DAP-v2 真实任务"),
        ("02", "学习目标（布鲁姆分层）", "记忆 → 理解 → 应用 → 分析 → 评价 → 创造"),
        ("03", "重点与难点", "附突破策略"),
        ("04", "六步工作法", "资讯 30′ → 计划 30′ → 决策 20′ → 实施 90′ → 检查 40′ → 评价+学生讲堂 30′"),
        ("05", "企业站实践任务卡", "2 学时 · 结对编程 · PR 评审"),
        ("06", "课后费曼任务", "以教代学，讲清才算掌握"),
    ]
    card_h = Inches(0.72)
    for no, t, sub in agenda:
        add_rect(slide, CONTENT_X, y, Inches(0.62), card_h - Inches(0.1), C_ACCENT)
        tb, tf = add_textbox(slide, CONTENT_X, y + Inches(0.08), Inches(0.62), Inches(0.4))
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = no
        set_run_font(r, 17, bold=True, color=C_WHITE)
        tb, tf = add_textbox(slide, CONTENT_X + Inches(0.85), y, CONTENT_W - Inches(0.85), card_h)
        p = tf.paragraphs[0]
        r = p.add_run()
        r.text = t
        set_run_font(r, 17, bold=True)
        p2 = tf.add_paragraph()
        r2 = p2.add_run()
        r2.text = sub
        set_run_font(r2, 11, color=C_MUTED)
        y += card_h + Inches(0.12)

    # ---------- 学习情境基本信息 ----------
    st, sb = get_section(sections, "学习情境基本信息")
    if sb:
        page_counter["n"] += 1
        slide = new_content_page(prs, "学习情境基本信息", "双元场所 · 学时 · 布鲁姆层级", page_no=page_counter["n"])
        render_blocks(slide, sb, CONTENT_TOP + Inches(0.1), size=15)

    # ---------- 任务描述 ----------
    st, sb = get_section(sections, "任务描述")
    if sb:
        page_counter["n"] += 1
        slide = new_content_page(prs, "客户委托单（任务描述）", "本讲要解决的真实业务问题", page_no=page_counter["n"])
        render_blocks(slide, sb, CONTENT_TOP + Inches(0.1), size=16)

    # ---------- 学习目标 ----------
    st, sb = get_section(sections, "学习目标")
    if sb:
        page_counter["n"] += 1
        slide = new_content_page(prs, "学习目标（布鲁姆分层）", "可测量的行为化目标 · 考核即按此命题", page_no=page_counter["n"])
        render_blocks(slide, sb, CONTENT_TOP + Inches(0.1), size=15)

    # ---------- 重点 ----------
    st, sb = get_section(sections, "教学重点与难点")
    if sb:
        subs = split_sections(sb, level=3)
        for sub_title, sub_blocks in subs:
            is_key = "重点" in sub_title
            page_counter["n"] += 1
            slide = new_content_page(
                prs,
                "教学重点" if is_key else "教学难点与突破策略",
                sub_title,
                page_no=page_counter["n"],
            )
            render_blocks(slide, sub_blocks, CONTENT_TOP + Inches(0.1), size=15)

    # ---------- 教学准备 ----------
    st, sb = get_section(sections, "教学准备")
    if sb:
        page_counter["n"] += 1
        slide = new_content_page(prs, "教学准备", "环境 · 资料 · 分组 · 安全须知", page_no=page_counter["n"])
        render_blocks(slide, sb, CONTENT_TOP + Inches(0.1), size=13)

    # ---------- 六步法过程 ----------
    st, sb = get_section(sections, "教学过程设计")
    if sb:
        steps = split_sections(sb, level=3)
        for sub_title, sub_blocks in steps:
            if re.match(r"^6\.0", sub_title):
                page_counter["n"] += 1
                slide = new_content_page(prs, "六步工作法 · 过程总表", "校内 4 学时节奏", page_no=page_counter["n"])
                render_blocks(slide, sub_blocks, CONTENT_TOP + Inches(0.1), size=13)
                continue
            idx = step_of(sub_title)
            if idx is None:
                continue
            # 渲染一个步骤（可能自动续页）
            rest = sub_blocks
            part = 0
            while rest is not None:
                cursor = {"rest": None}
                page_counter["n"] += 1
                slide = new_content_page(
                    prs,
                    f"六步法 · {STEP_NAMES[idx]}" + (f"（续{part}）" if part else ""),
                    sub_title,
                    step_idx=idx,
                    page_no=page_counter["n"],
                )
                end_y, overflow = render_blocks(slide, rest, CONTENT_TOP + Inches(0.28), size=14, cursor_state=cursor)
                rest = cursor["rest"] if overflow else None
                part += 1
                if part > 6:
                    break

    # ---------- 企业站任务卡 ----------
    st, sb = get_section(sections, "企业站实践任务卡")
    if sb:
        rest = sb
        part = 0
        while rest is not None:
            cursor = {"rest": None}
            page_counter["n"] += 1
            slide = new_content_page(
                prs,
                "企业站实践任务卡（2 学时）" + (f"（续{part}）" if part else ""),
                "结对编程 · 工程标准三查 · PR 评审",
                page_no=page_counter["n"],
            )
            end_y, overflow = render_blocks(slide, rest, CONTENT_TOP + Inches(0.1), size=14, cursor_state=cursor)
            rest = cursor["rest"] if overflow else None
            part += 1
            if part > 3:
                break

    # ---------- 评价设计 ----------
    st, sb = get_section(sections, "评价设计")
    if sb:
        page_counter["n"] += 1
        slide = new_content_page(prs, "本讲评价设计", "任务单评分 · 证据链要求", page_no=page_counter["n"])
        render_blocks(slide, sb, CONTENT_TOP + Inches(0.1), size=13)

    # ---------- 课后费曼 ----------
    st, sb = get_section(sections, "课后费曼任务")
    if sb:
        page_counter["n"] += 1
        slide = new_content_page(prs, "课后费曼任务", "以教代学 · 讲给非技术听众", page_no=page_counter["n"])
        render_blocks(slide, sb, CONTENT_TOP + Inches(0.1), size=16)

    # ---------- 结束页 ----------
    page_counter["n"] += 1
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, SLIDE_W, SLIDE_H, C_PRIMARY)
    tb, tf = add_textbox(slide, Inches(0.9), Inches(2.3), Inches(11.5), Inches(1.2))
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = f"{lesson_no} · {lesson_title}"
    set_run_font(r, 32, bold=True, color=C_WHITE)
    tb, tf = add_textbox(slide, Inches(0.9), Inches(3.7), Inches(11.5), Inches(2.2))
    reminders = [
        "✓ 提交六步法任务工单（含诚实清单栏，EVAL-01）",
        "✓ 企业站 PR 按评审单三查自查（EVAL-02）",
        "✓ 完成课后费曼任务（讲不清的记入补讲清单）",
        "✓ 未完成事项如实申报 —— 承认未完成不是失败，虚报完成才是（HSA）",
    ]
    for i, t in enumerate(reminders):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_before = Pt(8)
        r = p.add_run()
        r.text = t
        set_run_font(r, 16, color=RGBColor(0xC8, 0xD6, 0xEE))
    tb, tf = add_textbox(slide, Inches(0.9), Inches(6.5), Inches(11.5), Inches(0.4))
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = f"《{COURSE_NAME}》课程仓库 · 教学方案为本课件单一事实源"
    set_run_font(r, 11, color=RGBColor(0x8A, 0x9D, 0xBE))
    page_counter["n"] += 1

    return prs, page_counter["n"]


def main():
    args = [a.upper() for a in sys.argv[1:] if not a.startswith("-")]
    lesson_files = sorted(SRC_DIR.glob("L*.md"))
    if not lesson_files:
        print(f"!! 在 {SRC_DIR} 未找到教学方案")
        sys.exit(1)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    built = 0
    for f in lesson_files:
        m = re.match(r"^(L\d+)", f.stem)
        if not m:
            continue
        no = m.group(1)
        if args and no not in args:
            continue
        prs, pages = build_lesson_ppt(f)
        out = OUT_DIR / f"{f.stem}.pptx"
        prs.save(out)
        print(f"[OK] {f.name} -> {out.name}（{pages} 页）")
        built += 1
    print(f"\n完成：{built} 份课件 -> {OUT_DIR}")


if __name__ == "__main__":
    main()

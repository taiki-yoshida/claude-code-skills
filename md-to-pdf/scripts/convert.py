#!/usr/bin/env python3
"""Convert Markdown files to PDF with CJK font support.

Usage:
    python convert.py INPUT.md OUTPUT.pdf [options]
    python convert.py --dir /path/to/directory [options]

Options:
    --font-size SIZE    Base font size in pt (default: 10)
    --page-size SIZE    A4 or Letter (default: A4)
    --margin MM         Page margin in mm (default: 20)
    --dir DIR           Batch-convert all .md files in DIR
"""

import argparse
import glob
import os
import platform
import re
import sys

try:
    import markdown
except ImportError:
    print("Error: 'markdown' package not found. Install with: pip install markdown")
    sys.exit(1)

try:
    from fpdf import FPDF
except ImportError:
    print("Error: 'fpdf2' package not found. Install with: pip install fpdf2")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Font discovery
# ---------------------------------------------------------------------------

def _find_font_file(*candidates):
    """Return the first path that exists, or None."""
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


def find_cjk_fonts():
    """Return (regular_path, bold_path) for a CJK font, or (None, None)."""
    system = platform.system()

    if system == "Windows":
        fonts = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
        regular = _find_font_file(
            os.path.join(fonts, "YuGothR.ttc"),
            os.path.join(fonts, "meiryo.ttc"),
            os.path.join(fonts, "msgothic.ttc"),
        )
        bold = _find_font_file(
            os.path.join(fonts, "YuGothB.ttc"),
            os.path.join(fonts, "meiryob.ttc"),
            os.path.join(fonts, "msgothic.ttc"),
        )
        return regular, bold or regular

    if system == "Darwin":
        lib = "/System/Library/Fonts"
        regular = _find_font_file(
            os.path.join(lib, "HiraginoSans-W3.ttc"),
            os.path.join(lib, "ヒラギノ角ゴシック W3.ttc"),
            "/Library/Fonts/Arial Unicode.ttf",
        )
        bold = _find_font_file(
            os.path.join(lib, "HiraginoSans-W6.ttc"),
            os.path.join(lib, "ヒラギノ角ゴシック W6.ttc"),
        )
        return regular, bold or regular

    # Linux
    regular = _find_font_file(
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
        "/usr/share/fonts/ipa-gothic/ipag.ttf",
    )
    bold = _find_font_file(
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Bold.ttc",
    )
    return regular, bold or regular


def _has_cjk(text):
    """Quick check for CJK characters in text."""
    for ch in text:
        cp = ord(ch)
        if (0x3000 <= cp <= 0x9FFF) or (0xF900 <= cp <= 0xFAFF) or (0xFF00 <= cp <= 0xFFEF):
            return True
    return False


# ---------------------------------------------------------------------------
# Markdown → PDF renderer
# ---------------------------------------------------------------------------

class MarkdownPDFConverter:
    def __init__(self, font_size=10, page_size="A4", margin=20):
        self.base_size = font_size
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=margin)

        if page_size.upper() == "LETTER":
            self.pdf.add_page(format="Letter")
        else:
            self.pdf.add_page(format="A4")

        # Will be set during convert() based on content
        self.font_family = "Helvetica"
        self._margin = margin
        self.pdf.set_margins(margin, margin, margin)

    def _setup_fonts(self, text):
        """Register CJK fonts if the text contains CJK characters."""
        if _has_cjk(text):
            regular, bold = find_cjk_fonts()
            if regular:
                self.pdf.add_font("CJK", "", regular)
                self.pdf.add_font("CJK", "B", bold or regular)
                self.pdf.add_font("CJK", "I", regular)
                self.pdf.add_font("CJK", "BI", bold or regular)
                self.font_family = "CJK"
                return
            print("Warning: CJK characters detected but no CJK font found. "
                  "Output may have missing glyphs.")
        # Fallback: built-in Helvetica (no file needed)
        self.font_family = "Helvetica"

    def convert(self, md_file, pdf_file):
        with open(md_file, "r", encoding="utf-8") as f:
            text = f.read()
        lines = text.split("\n")

        self._setup_fonts(text)
        self.pdf.set_font(self.font_family, "", self.base_size)

        i = 0
        while i < len(lines):
            line = lines[i].rstrip("\n")

            # Empty line
            if not line.strip():
                self.pdf.ln(3)
                i += 1
                continue

            # Horizontal rule
            if line.strip() in ("---", "***", "___"):
                self.pdf.ln(2)
                y = self.pdf.get_y()
                self.pdf.line(
                    self.pdf.l_margin, y,
                    self.pdf.w - self.pdf.r_margin, y,
                )
                self.pdf.ln(4)
                i += 1
                continue

            # Headers
            if line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                heading = line.lstrip("#").strip()
                heading = _strip_md(heading)
                sizes = {1: 18, 2: 15, 3: 13, 4: 11, 5: 10, 6: 10}
                size = sizes.get(level, self.base_size)
                self.pdf.set_font(self.font_family, "B", size)
                self.pdf.ln(4 if level <= 2 else 2)
                self.pdf.multi_cell(0, size * 0.6, heading)
                if level <= 2:
                    y = self.pdf.get_y()
                    self.pdf.line(
                        self.pdf.l_margin, y,
                        self.pdf.w - self.pdf.r_margin, y,
                    )
                    self.pdf.ln(2)
                self.pdf.set_font(self.font_family, "", self.base_size)
                i += 1
                continue

            # Table (requires separator row on next line)
            if ("|" in line
                    and i + 1 < len(lines)
                    and re.match(r"^\|[\s\-:|]+\|", lines[i + 1].strip())):
                rows = []
                while i < len(lines) and "|" in lines[i]:
                    stripped = lines[i].strip()
                    if re.match(r"^\|[\s\-:|]+\|$", stripped):
                        i += 1
                        continue
                    cells = [_strip_md(c.strip()) for c in stripped.strip("|").split("|")]
                    rows.append(cells)
                    i += 1
                self._render_table(rows)
                continue

            # Fenced code block
            if line.strip().startswith("```"):
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    code_lines.append(lines[i].rstrip("\n"))
                    i += 1
                if i < len(lines):
                    i += 1  # skip closing ```
                self._render_code_block("\n".join(code_lines))
                continue

            # Blockquote
            if line.startswith(">"):
                text_bq = _strip_md(line.lstrip(">").strip())
                self.pdf.set_font(self.font_family, "I", self.base_size - 1)
                self.pdf.set_x(self.pdf.l_margin + 5)
                self.pdf.set_text_color(100, 100, 100)
                width = self.pdf.w - 2 * self.pdf.l_margin - 10
                self.pdf.multi_cell(width, self.base_size * 0.5, text_bq)
                self.pdf.set_text_color(0, 0, 0)
                self.pdf.set_font(self.font_family, "", self.base_size)
                i += 1
                continue

            # List items (bullet or numbered)
            m_bullet = re.match(r"^(\s*)[-*]\s+(.*)", line)
            m_num = re.match(r"^(\s*)(\d+\.)\s+(.*)", line)
            if m_bullet or m_num:
                if m_bullet:
                    indent = len(m_bullet.group(1))
                    item_text = "- " + _strip_md(m_bullet.group(2))
                else:
                    indent = len(m_num.group(1))
                    item_text = m_num.group(2) + " " + _strip_md(m_num.group(3))
                offset = min(5 + (indent // 2) * 5, 20)
                avail = self.pdf.w - 2 * self.pdf.l_margin - offset
                if avail < 30:
                    offset = 5
                    avail = self.pdf.w - 2 * self.pdf.l_margin - offset
                self.pdf.set_x(self.pdf.l_margin + offset)
                self.pdf.set_font(self.font_family, "", self.base_size)
                self.pdf.multi_cell(avail, self.base_size * 0.55, item_text)
                i += 1
                continue

            # Checkbox list items (- [ ] or - [x])
            m_check = re.match(r"^(\s*)[-*]\s+\[([ xX])\]\s+(.*)", line)
            if m_check:
                indent = len(m_check.group(1))
                checked = m_check.group(2).lower() == "x"
                marker = "[x] " if checked else "[ ] "
                item_text = marker + _strip_md(m_check.group(3))
                offset = min(5 + (indent // 2) * 5, 20)
                avail = self.pdf.w - 2 * self.pdf.l_margin - offset
                if avail < 30:
                    offset = 5
                    avail = self.pdf.w - 2 * self.pdf.l_margin - offset
                self.pdf.set_x(self.pdf.l_margin + offset)
                self.pdf.set_font(self.font_family, "", self.base_size)
                self.pdf.multi_cell(avail, self.base_size * 0.55, item_text)
                i += 1
                continue

            # Regular paragraph
            para = _strip_md(line)
            self.pdf.set_font(self.font_family, "", self.base_size)
            width = self.pdf.w - 2 * self.pdf.l_margin
            self.pdf.multi_cell(width, self.base_size * 0.55, para)
            i += 1

        self.pdf.output(pdf_file)

    # ------------------------------------------------------------------

    def _render_table(self, rows):
        if not rows:
            return
        num_cols = max(len(r) for r in rows)
        avail_width = self.pdf.w - 2 * self.pdf.l_margin
        col_width = avail_width / num_cols
        small = max(self.base_size - 1.5, 7)

        self.pdf.set_font(self.font_family, "", small)

        for ri, row in enumerate(rows):
            while len(row) < num_cols:
                row.append("")

            # Page break check
            if self.pdf.get_y() + 8 > self.pdf.h - self._margin:
                self.pdf.add_page()

            y_start = self.pdf.get_y()

            if ri == 0:
                self.pdf.set_font(self.font_family, "B", small)
                self.pdf.set_fill_color(235, 235, 235)
            else:
                self.pdf.set_font(self.font_family, "", small)
                self.pdf.set_fill_color(255, 255, 255)

            max_y = y_start
            for ci, cell in enumerate(row):
                self.pdf.set_xy(self.pdf.l_margin + ci * col_width, y_start)
                self.pdf.multi_cell(col_width, small * 0.5, cell, border=1, fill=(ri == 0))
                max_y = max(max_y, self.pdf.get_y())

            self.pdf.set_y(max_y)

        self.pdf.ln(3)
        self.pdf.set_font(self.font_family, "", self.base_size)

    def _render_code_block(self, code):
        small = max(self.base_size - 1.5, 7)
        self.pdf.set_font(self.font_family, "", small)
        self.pdf.set_fill_color(245, 245, 245)

        for line in code.split("\n"):
            if self.pdf.get_y() > self.pdf.h - self._margin:
                self.pdf.add_page()
            self.pdf.set_x(self.pdf.l_margin + 3)
            self.pdf.cell(
                self.pdf.w - 2 * self.pdf.l_margin - 6,
                small * 0.55,
                line,
                fill=True,
                new_x="LMARGIN",
                new_y="NEXT",
            )

        self.pdf.set_fill_color(255, 255, 255)
        self.pdf.set_font(self.font_family, "", self.base_size)
        self.pdf.ln(3)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_md(text):
    """Remove inline markdown formatting."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)       # images → remove
    text = re.sub(r"\[(.+?)\]\(.*?\)", r"\1", text)   # links → text only
    return text


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert Markdown files to PDF with CJK support.",
    )
    parser.add_argument("input", nargs="?", help="Input .md file")
    parser.add_argument("output", nargs="?", help="Output .pdf file")
    parser.add_argument("--dir", help="Batch-convert all .md files in a directory")
    parser.add_argument("--font-size", type=float, default=10, help="Base font size (default: 10)")
    parser.add_argument("--page-size", default="A4", choices=["A4", "Letter"], help="Page size (default: A4)")
    parser.add_argument("--margin", type=int, default=20, help="Page margin in mm (default: 20)")

    args = parser.parse_args()

    if args.dir:
        md_files = sorted(glob.glob(os.path.join(args.dir, "*.md")))
        if not md_files:
            print(f"No .md files found in {args.dir}")
            sys.exit(1)
        for f in md_files:
            pdf_name = f.rsplit(".", 1)[0] + ".pdf"
            print(f"Converting: {f}")
            converter = MarkdownPDFConverter(args.font_size, args.page_size, args.margin)
            converter.convert(f, pdf_name)
            size_kb = os.path.getsize(pdf_name) // 1024
            print(f"  -> {pdf_name} ({size_kb} KB)")
        print(f"\nDone! Converted {len(md_files)} file(s).")
    elif args.input:
        pdf_out = args.output or args.input.rsplit(".", 1)[0] + ".pdf"
        print(f"Converting: {args.input} -> {pdf_out}")
        converter = MarkdownPDFConverter(args.font_size, args.page_size, args.margin)
        converter.convert(args.input, pdf_out)
        size_kb = os.path.getsize(pdf_out) // 1024
        print(f"Done! Created {pdf_out} ({size_kb} KB)")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

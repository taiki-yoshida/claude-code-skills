---
name: md-to-pdf
description: Convert Markdown files to PDF. Use when user wants to export markdown to PDF, generate PDF documents from .md files, or create formatted PDF reports from markdown content. Handles CJK (Japanese, Chinese, Korean) text, tables, code blocks, and standard markdown formatting.
---

# Markdown to PDF Converter

Convert markdown files to well-formatted PDFs. Supports full markdown syntax including tables, code blocks, headers, lists, blockquotes, and horizontal rules. Handles CJK (Japanese, Chinese, Korean) text out of the box on systems with appropriate fonts installed.

## When to use

- User asks to convert `.md` files to PDF
- User wants to export documentation or reports as PDF
- User mentions "markdown to PDF", "md to pdf", or "generate PDF from markdown"

## Strategy

This skill uses a pure-Python approach (`fpdf2` + `markdown`) that works cross-platform without requiring LaTeX, Pandoc, or system-level dependencies like GTK/Pango. This makes it reliable on Windows, macOS, and Linux.

### Why not Pandoc + LaTeX?

Pandoc with a LaTeX engine (`xelatex`, `lualatex`) produces the highest quality output but requires a full LaTeX distribution (often 2-4 GB). Many developer machines don't have LaTeX installed, and installation is heavyweight. The `fpdf2` approach produces good-quality PDFs with zero system dependencies beyond Python.

### Why not WeasyPrint?

WeasyPrint renders HTML/CSS to PDF beautifully but requires GTK/Pango/GLib system libraries. On Windows this means installing MSYS2 or GTK runtime separately — a common failure point.

## Prerequisites

Install Python dependencies (no system-level packages required):

```bash
pip install fpdf2 markdown
```

## How to convert

Use the helper script bundled with this skill:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/convert.py" INPUT.md OUTPUT.pdf
```

### Batch conversion (all `.md` files in a directory)

```bash
python "${CLAUDE_SKILL_DIR}/scripts/convert.py" --dir /path/to/directory
```

This converts every `.md` file in the directory to a `.pdf` with the same base name.

## Font selection

The script auto-detects fonts based on OS and content:

| OS | CJK font | Fallback |
|---|---|---|
| Windows | Yu Gothic (`YuGothR.ttc` / `YuGothB.ttc`) | Meiryo, MS Gothic |
| macOS | Hiragino Sans (`HiraginoSans-W3.ttc` / `W6`) | Hiragino Kaku Gothic |
| Linux | Noto Sans CJK (`NotoSansCJK-Regular.ttc`) | IPAGothic |

For Latin-only content, the script falls back to Helvetica (built into fpdf2, no file needed).

## Customization

The script accepts these optional flags:

| Flag | Default | Description |
|---|---|---|
| `--font-size` | `10` | Base body font size in points |
| `--page-size` | `A4` | Page size: `A4` or `Letter` |
| `--margin` | `20` | Page margin in mm |

Example:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/convert.py" report.md report.pdf --page-size Letter --font-size 11
```

## Gotchas

1. **TTC vs TTF fonts**: `.ttc` (TrueType Collection) files contain multiple fonts. `fpdf2` handles them correctly but older versions (< 2.5) may not — ensure `fpdf2 >= 2.7`.
2. **Superscript/subscript Unicode**: Some Unicode characters like `\u207b` (superscript minus) may not be present in all CJK fonts. The PDF will render with a missing glyph but won't fail.
3. **Very wide tables**: Tables with many columns may overflow. The script distributes column widths evenly across the page width. For tables wider than the page, consider landscape mode or reducing font size.
4. **Images**: Embedded images (`![alt](path)`) are **not** supported by this script. If the user needs image embedding, suggest Pandoc + LaTeX as an alternative.
5. **`pip install` location**: On some systems `pip install` installs to user site-packages. If `import fpdf` fails after install, try `pip install --user fpdf2` or use a virtual environment.

## Limitations

- No image embedding (markdown `![](...)` syntax is stripped)
- No LaTeX math rendering
- No custom CSS styling (uses built-in formatting)
- Tables use equal column widths (no auto-sizing based on content)

For maximum fidelity, recommend Pandoc + XeLaTeX if the user has LaTeX installed:

```bash
pandoc input.md -o output.pdf --pdf-engine=xelatex -V CJKmainfont="Yu Gothic"
```

# md-to-pdf

Convert Markdown files to PDF with CJK (Japanese, Chinese, Korean) font support. Pure-Python approach — no LaTeX, Pandoc, or system-level dependencies required.

## Features

- Full markdown: headers, tables, code blocks, lists, blockquotes, horizontal rules
- Auto-detects CJK content and selects appropriate system fonts
- Cross-platform: Windows (Yu Gothic), macOS (Hiragino Sans), Linux (Noto Sans CJK)
- Batch conversion of all `.md` files in a directory
- Configurable page size, margins, and font size

## Prerequisites

```bash
pip install fpdf2 markdown
```

## Usage

### As a Claude Code skill

```
/md-to-pdf report.md
```

Or simply ask Claude to convert your markdown files to PDF.

### Standalone

```bash
# Single file
python scripts/convert.py input.md output.pdf

# Batch (all .md files in a directory)
python scripts/convert.py --dir ./docs

# With options
python scripts/convert.py input.md output.pdf --page-size Letter --font-size 11 --margin 25
```

## Limitations

- No image embedding (images are stripped)
- No LaTeX math rendering
- Tables use equal column widths
- No custom CSS/styling

For maximum fidelity with images and math, use Pandoc + XeLaTeX instead:

```bash
pandoc input.md -o output.pdf --pdf-engine=xelatex -V CJKmainfont="Yu Gothic"
```

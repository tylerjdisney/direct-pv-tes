#!/usr/bin/env python3
"""
Combine the docs into one PDF with pandoc.

Runs automatically on every GitHub release. To run it yourself you need pandoc
and a LaTeX engine (xelatex) installed:   python tools/build_pdf.py [VERSION]

Page order comes from the `nav:` section of mkdocs.yml.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
BUILD = ROOT / "build"


def read_mkdocs():
    text = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    title = re.search(r"^site_name:\s*(.+)$", text, re.M).group(1).strip()
    m = re.search(r"^site_author:\s*(.+)$", text, re.M)
    author = m.group(1).strip() if m else ""
    nav = re.search(r"^nav:\s*\n((?:\s+-.*\n?)+)", text, re.M).group(1)
    pages = re.findall(r":\s*([\w\-/]+\.md)\s*$", nav, re.M)
    return title, author, pages


# Relative column widths in the PDF: long text columns get more room.
BOM_WIDTHS = {"item": 6, "spec": 5, "notes": 6, "supplier": 4, "part_no": 3,
              "id": 3, "qty": 1, "unit": 2}


def _num(value):
    try:
        return float(value.replace("$", "").replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def _money(x):
    return f"${x:,.2f}"


def _pipe_table(header, rows):
    """A pipe table pandoc will wrap to the page width."""
    def esc(c):
        return c.replace("|", "\\|").replace("\n", " ").strip()
    weights = [BOM_WIDTHS.get(h.strip().lower(), 2) for h in header]
    lines = ["| " + " | ".join(esc(h).replace("_", " ") for h in header) + " |",
             "|" + "|".join("-" * (w * 6) for w in weights) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(esc(c) for c in r) + " |")
    return "\n".join(lines)


def _cost_summary(header, rows):
    """Subtotal from qty x unit cost. Returns (total, count of rows without a price)."""
    cols = [h.strip().lower() for h in header]
    if "qty" not in cols or "unit_cost_usd" not in cols:
        return None, 0
    qi, ci = cols.index("qty"), cols.index("unit_cost_usd")
    total, missing = 0.0, 0
    for r in rows:
        q, c = _num(r[qi]), _num(r[ci])
        if q is None or c is None:
            missing += 1
        else:
            total += q * c
    return total, missing


def _cost_line(label, total, missing):
    if total is None:
        return ""
    note = f" ({missing} item{'s' if missing != 1 else ''} not yet priced)" if missing else ""
    return f"**{label}: {_money(total)}**{note}"


def bom_table():
    """
    Turn BOM.csv into PDF-ready tables.

    If the CSV has a `section` column, each section becomes its own subheading
    and table (in the order sections first appear), with a subtotal, followed
    by a grand total. Without it, the BOM is one table with a total.
    """
    import csv
    with open(ROOT / "BOM.csv", newline="", encoding="utf-8") as f:
        rows = [r for r in csv.reader(f) if any(c.strip() for c in r)]
    if len(rows) < 2:
        return "*No parts listed yet.*"
    header, body = rows[0], rows[1:]
    body = [(r + [""] * len(header))[:len(header)] for r in body]
    # Drop columns that are empty in every row (e.g. no part numbers yet).
    keep = [i for i, h in enumerate(header)
            if h.strip().lower() == "section" or any(r[i].strip() for r in body)]
    header = [header[i] for i in keep]
    body = [[r[i] for i in keep] for r in body]
    cols = [h.strip().lower() for h in header]

    out = ["\\small", ""]
    if "section" in cols:
        si = cols.index("section")
        sections = {}
        for r in body:
            sections.setdefault(r[si].strip() or "Other", []).append(r)
        sub_header = [h for i, h in enumerate(header) if i != si]
        grand, grand_missing = 0.0, 0
        for name, rows_ in sections.items():
            trimmed = [[c for i, c in enumerate(r) if i != si] for r in rows_]
            total, missing = _cost_summary(sub_header, trimmed)
            out += ["\\needspace{18\\baselineskip}", "", f"## {name}", "", _pipe_table(sub_header, trimmed), ""]
            line = _cost_line("Subtotal", total, missing)
            if line:
                out += [line, ""]
            if total is not None:
                grand += total
                grand_missing += missing
        if _cost_summary(sub_header, [])[0] is not None:
            out += ["\\needspace{4\\baselineskip}", "", "## Total", "",
                    _cost_line("Estimated total", grand, grand_missing), ""]
    else:
        total, missing = _cost_summary(header, body)
        out += [_pipe_table(header, body), "", _cost_line("Estimated total", total, missing), ""]
    out += ["\\normalsize"]
    return "\n".join(out)


def convert_admonitions(md):
    """MkDocs '!!! warning "Watch out"' blocks -> blockquotes pandoc understands."""
    lines, out, i = md.splitlines(), [], 0
    while i < len(lines):
        m = re.match(r'^(\s*)(!!!|\?\?\?\+?)\s+(\w+)(?:\s+"([^"]*)")?\s*$', lines[i])
        if not m:
            out.append(lines[i]); i += 1; continue
        indent, kind, label = m.group(1), m.group(3), m.group(4)
        label = label or kind.capitalize()
        out.append(f"{indent}> **{label}:**")
        i += 1
        while i < len(lines) and (lines[i].startswith(indent + "    ") or not lines[i].strip()):
            if not lines[i].strip() and (i + 1 >= len(lines) or not lines[i + 1].startswith(indent + "    ")):
                break
            out.append(f"{indent}> " + lines[i][len(indent) + 4:]); i += 1
        out.append("")
    return "\n".join(out)


def strip_html_comments(md):
    return re.sub(r"<!--.*?-->", "", md, flags=re.S)


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else ""
    title, author, pages = read_mkdocs()
    BUILD.mkdir(exist_ok=True)

    parts = []
    for page in pages:
        md = (DOCS / page).read_text(encoding="utf-8")
        md = strip_html_comments(md)
        if "read_csv(" in md:
            md = re.sub(r"\{\{\s*read_csv\([^)]*\)\s*\}\}", lambda _: bom_table(), md)
        md = convert_admonitions(md)
        # The overview page repeats the project title; the cover already shows it.
        if page == pages[0]:
            md = re.sub(r"^# .*\n", "# Overview\n", md, count=1)
        parts.append(md)

    combined = BUILD / "combined.md"
    combined.write_text("\n\n\\newpage\n\n".join(parts), encoding="utf-8")

    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    pdf = BUILD / f"{slug}{'-' + version if version else ''}.pdf"
    subtitle = "Mars College Dept of Makers" + (f" · {version}" if version else "")

    cmd = [
        "pandoc", str(combined),
        "--metadata-file", str(ROOT / "pdf" / "metadata.yml"),
        "-M", f"title={title}",
        "-M", f"subtitle={subtitle}",
        "-M", f"author={author}",
        "--resource-path", str(DOCS),
        "--pdf-engine=xelatex",
        "--toc", "--toc-depth=2",
        "-o", str(pdf),
    ]
    subprocess.run(cmd, check=True)
    print(pdf)


if __name__ == "__main__":
    main()

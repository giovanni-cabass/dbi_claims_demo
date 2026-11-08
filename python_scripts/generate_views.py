"""generate_views.py -- regenerates dependency_graph.md and claim_dashboard.html from claims.json.

Both outputs are generated views, never hand-edited: the one source of truth is
latex_notes/structure/claims.json (see check_claims.py). Re-run this script after
claims.json changes; it always overwrites both files from scratch.

    dependency_graph.md    a Mermaid graph of the depends_on edges between claims.
    claim_dashboard.html    a static page listing each claim's statement/formula
                            (KaTeX-rendered via the vendored copy in vendor/katex/),
                            evidence, and dependency links.

Self-contained like check_claims.py: root is resolved from this script's own file
location, no shared `utils` import.

Usage:
    generate_views.py [--root PATH]
"""
import argparse
import html
import json
import os
import re

main_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BOOK_REL = os.path.join("latex_notes", "structure", "claims.json")
GRAPH_REL = os.path.join("latex_notes", "structure", "dependency_graph.md")
DASHBOARD_REL = os.path.join("latex_notes", "structure", "claim_dashboard.html")
KATEX_FROM_STRUCTURE = "../../vendor/katex"  # latex_notes/structure/ -> vendor/katex/


def load_book(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def citable_entries(book: dict):
    """(list_name, entry) for every given/established entry, in book order."""
    out = []
    for lst in ("given", "established"):
        for e in book.get(lst, []):
            out.append((lst, e))
    return out


def build_dependency_graph(book: dict) -> str:
    entries = citable_entries(book)
    header = [
        "# Claim dependency graph",
        "",
        "Generated from `claims.json` by `generate_views.py` -- do not hand-edit.",
        "An arrow `A --> B` means claim B depends on (cites as a premise) claim A.",
        "",
    ]
    if not entries:
        return "\n".join(header + ["_No citable claims yet._", ""])
    lines = ["```mermaid", "graph TD"]
    for _, e in entries:
        # Node label: id plus its `section` (the \label{} name) on a second line,
        # so the graph reads without cross-referencing claims.json -- id alone is
        # not identifying at a glance once the ledger grows past a handful of entries.
        label = f'{e["id"]}<br/>{e.get("section", "")}'.replace('"', "&quot;")
        lines.append(f'    {e["id"]}["{label}"]')
    for _, e in entries:
        for dep in e.get("depends_on", []) or []:
            lines.append(f"    {dep} --> {e['id']}")
    lines.append("```")
    n_given = len(book.get("given", []))
    n_established = len(book.get("established", []))
    n = len(entries)
    footer = [
        "",
        f"**Claim count:** {n} citable claim{'s' if n != 1 else ''} "
        f"({n_given} given, {n_established} established).",
    ]
    return "\n".join(header + lines + footer + [""])


TEXTTT_RE = re.compile(r"\\texttt\{([^{}]*)\}")
EQ_RE = re.compile(r"\\[Ee]q\{([^{}]*)\}")


def clean_bare_latex(escaped: str) -> str:
    """Special-case the small set of bare (outside-$...$) LaTeX macros that
    appear in some claims.json statements. KaTeX's auto-render only ever
    touches text between $...$/$$...$$ delimiters, so a macro used outside
    math mode -- as macros.sty's \\texttt and \\eq are -- would otherwise show
    up as literal backslash-and-braces text. Operates on already-HTML-escaped
    text (see html.escape call at the use site), so the captured groups are
    already safe to splice back in as-is.

    \\texttt{X} -> <code>X</code> (macros.sty: plain monospace, no cross-ref).
    \\eq{LABEL} -> "(eq. LABEL)": macros.sty expands \\eq{label} to (\\ref{label}),
    a resolved equation number only pdflatex's .aux pass can produce; showing
    the label itself (eq: prefix stripped) is honest about what we actually have.
    """
    escaped = TEXTTT_RE.sub(lambda m: f"<code>{m.group(1)}</code>", escaped)
    escaped = EQ_RE.sub(lambda m: f"(eq.&nbsp;{re.sub(r'^eq:', '', m.group(1))})", escaped)
    return escaped


def artifact_html(artifact: str) -> str:
    """One evidence/witness artifact as an HTML fragment, relative to latex_notes/structure/."""
    path_part = artifact.split("::")[0].strip()
    esc = html.escape(artifact)
    if path_part.startswith(("http://", "https://")):
        return f'<a href="{html.escape(path_part)}">{esc}</a>'
    if path_part.startswith(("arXiv:", "doi:", "isbn:")):
        return f"<code>{esc}</code>"
    rel = os.path.join("..", "..", path_part).replace(os.sep, "/")
    return f'<a href="{html.escape(rel)}"><code>{esc}</code></a>'


def entry_section_html(lst: str, e: dict, known_ids: set) -> str:
    eid = e["id"]
    eid_esc = html.escape(eid)
    statement = clean_bare_latex(html.escape(e.get("statement", "")))
    parts = [f'<section id="{eid_esc}" class="claim">']
    # Header + statement + formula are always visible (the actual physics result);
    # file/verification/depends-on/evidence collapse behind a click (the "receipts").
    parts.append(f'  <div class="panel-header" onclick="togglePanel(\'{eid_esc}\')">')
    parts.append(f'    <h2><code>{eid_esc}</code> <span class="tag tag-{html.escape(lst)}">{html.escape(lst)}</span></h2>')
    parts.append(f'    <span class="expand-icon" id="icon-{eid_esc}">+</span>')
    parts.append("  </div>")
    parts.append(f'  <p class="statement">{statement}</p>')
    if e.get("formula"):
        parts.append(f'  <div class="formula" data-formula="{html.escape(e["formula"])}"></div>')
    parts.append(f'  <div class="panel-detail" id="detail-{eid_esc}" style="display:none">')
    meta = []
    if e.get("file"):
        section = e.get("section", "")
        file_rel = os.path.join("..", "..", e["file"]).replace(os.sep, "/")
        meta.append(f'<a href="{html.escape(file_rel)}"><code>{html.escape(e["file"])}</code></a>'
                    + (f' (<code>{html.escape(section)}</code>)' if section else ""))
    if e.get("verification"):
        meta.append(html.escape(e["verification"]))
    if e.get("signed_off"):
        meta.append(f"signed off {html.escape(e['signed_off'])}")
    if meta:
        parts.append(f'  <p class="meta">{" &middot; ".join(meta)}</p>')
    deps = e.get("depends_on") or []
    if deps:
        links = ", ".join(
            f'<a href="#{html.escape(d)}"><code>{html.escape(d)}</code></a>' if d in known_ids
            else f'<code>{html.escape(d)}</code>'
            for d in deps
        )
        parts.append(f'  <p class="meta">depends on: {links}</p>')
    ev = e.get("evidence")
    witness = e.get("witness")
    artifacts = (ev or {}).get("artifacts") or ([witness] if witness else [])
    if artifacts:
        items = "".join(f"<li>{artifact_html(a)}</li>" for a in artifacts)
        parts.append(f'  <p class="meta">evidence:</p>\n  <ul class="evidence">{items}</ul>')
    parts.append("  </div>")
    parts.append("</section>")
    return "\n".join(parts)


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Claims dashboard</title>
<link rel="stylesheet" href="{katex_css}">
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          max-width: 860px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }}
  h1 {{ font-size: 1.4rem; }}
  .claim {{ border: 1px solid color-mix(in srgb, currentColor 20%, transparent);
            border-left: 4px solid #6366f1;
            border-radius: 8px; padding: 1rem 1.25rem; margin: 1.25rem 0; }}
  .claim:target {{ animation: flash 1.6s ease-out; }}
  @keyframes flash {{
    0% {{ background: color-mix(in srgb, gold 35%, transparent); }}
    100% {{ background: transparent; }}
  }}
  .panel-header {{ display: flex; align-items: center; justify-content: space-between;
                   gap: 0.75rem; cursor: pointer; user-select: none; }}
  .claim h2 {{ font-size: 1rem; margin: 0 0 0.5rem 0; }}
  .expand-icon {{ font-size: 1.1rem; font-weight: 300; opacity: 0.55; width: 1.5rem;
                  text-align: center; flex-shrink: 0; }}
  .tag {{ font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.04em;
          border-radius: 4px; padding: 0.15rem 0.5rem;
          background: color-mix(in srgb, currentColor 12%, transparent); }}
  .statement {{ margin: 0.5rem 0; }}
  .formula {{ margin: 0.75rem 0; overflow-x: auto; }}
  .panel-detail {{ margin-top: 0.5rem; padding-top: 0.5rem;
                   border-top: 1px solid color-mix(in srgb, currentColor 15%, transparent); }}
  .meta {{ font-size: 0.85rem; opacity: 0.75; margin: 0.35rem 0; }}
  .evidence {{ font-size: 0.85rem; opacity: 0.85; margin: 0.25rem 0 0.75rem 0; }}
  code {{ font-size: 0.9em; }}
  footer {{ font-size: 0.8rem; opacity: 0.6; margin-top: 2rem; text-align: center;
            border-top: 1px solid color-mix(in srgb, currentColor 15%, transparent);
            padding-top: 1rem; }}
</style>
</head>
<body>
<h1>Claims dashboard</h1>
<p class="meta">Generated from <code>claims.json</code> by <code>generate_views.py</code> --
do not hand-edit this file. See <a href="dependency_graph.md">dependency_graph.md</a> for the
dependency graph.</p>
{sections}
<footer>{count_line}</footer>
<script src="{katex_js}"></script>
<script src="{katex_autorender}"></script>
<script>
  document.querySelectorAll(".formula").forEach(function (el) {{
    katex.render(el.dataset.formula, el, {{ displayMode: true, throwOnError: false }});
  }});
  renderMathInElement(document.body, {{
    delimiters: [
      {{ left: "$$", right: "$$", display: true }},
      {{ left: "$", right: "$", display: false }}
    ],
    ignoredTags: ["script", "noscript", "style", "textarea", "pre", "code"]
  }});

  function togglePanel(id) {{
    var detail = document.getElementById("detail-" + id);
    var icon = document.getElementById("icon-" + id);
    if (!detail) return;
    var open = detail.style.display !== "none";
    detail.style.display = open ? "none" : "block";
    if (icon) icon.textContent = open ? "+" : String.fromCharCode(8722);
  }}
  function expandFromHash() {{
    var id = window.location.hash.slice(1);
    if (!id) return;
    var detail = document.getElementById("detail-" + id);
    var icon = document.getElementById("icon-" + id);
    if (detail && detail.style.display === "none") {{
      detail.style.display = "block";
      if (icon) icon.textContent = String.fromCharCode(8722);
    }}
  }}
  window.addEventListener("hashchange", expandFromHash);
  expandFromHash();
</script>
</body>
</html>
"""


def build_dashboard_html(book: dict) -> str:
    entries = citable_entries(book)
    known_ids = {e["id"] for _, e in entries}
    sections = "\n".join(entry_section_html(lst, e, known_ids) for lst, e in entries)
    if not sections:
        sections = '<p class="meta"><em>No citable claims yet.</em></p>'
    counts = (f"{len(book.get('given', []))} given, {len(book.get('established', []))} established, "
              f"{len(book.get('fenced', []))} fenced, {len(book.get('retired_ids', {}))} retired")
    return PAGE_TEMPLATE.format(
        katex_css=f"{KATEX_FROM_STRUCTURE}/katex.min.css",
        katex_js=f"{KATEX_FROM_STRUCTURE}/katex.min.js",
        katex_autorender=f"{KATEX_FROM_STRUCTURE}/contrib/auto-render.min.js",
        sections=sections,
        count_line=counts,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=main_folder, help="workspace root (default: this workspace)")
    args = parser.parse_args()
    root = os.path.abspath(args.root)
    book_path = os.path.join(root, BOOK_REL)
    graph_path = os.path.join(root, GRAPH_REL)
    dashboard_path = os.path.join(root, DASHBOARD_REL)

    print(f"root: {root}")
    print(f"book: {book_path}")
    book = load_book(book_path)

    with open(graph_path, "w", encoding="utf-8") as fh:
        fh.write(build_dependency_graph(book))
    print(f"wrote: {os.path.relpath(graph_path, root)}")

    with open(dashboard_path, "w", encoding="utf-8") as fh:
        fh.write(build_dashboard_html(book))
    print(f"wrote: {os.path.relpath(dashboard_path, root)}")


if __name__ == "__main__":
    main()

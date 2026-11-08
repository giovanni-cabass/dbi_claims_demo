"""check_claims.py -- the ledger checker and the fold command.

The book is ``latex_notes/structure/claims.json`` (law: ``.cursor/rules/established-results.mdc``).
This script is the only thing that writes to it, and only under ``--write``.

Modes (all paths in entries are relative to ``--root``, default the workspace):

    check_claims.py                                        check the book
    check_claims.py --fragment F.json                      check a fragment against book + fragment
    check_claims.py --promote NOTE.tex --labels a,b        draft entries from the note's ``% claim:`` blocks
                    [--signed YYYY-MM-DD] [--write]        and print them; --write appends them to the book
    check_claims.py --merge F.json [--accept id1,id2]      validate a run's fragment (a PROPOSAL), keep --accept
                                                           (default all), print. --merge NEVER writes: transcribe
                                                           the accepted results into a latex_notes/ note and
                                                           --promote that note. --promote --write is the one
                                                           write path.

Exit code 0 = clean, 1 = at least one FAIL. Every FAIL line names the id and the field.

Sourcing rule (law), enforced on the RESOLVED path (``..`` and symlinks do not escape it): an ``established``
entry's ``file`` -- in every list -- is a ``.tex`` inside ``latex_notes/``. Absolute paths are never sources. The
``section`` is a ``\\label{...}`` that occurs in the note. A note under campaigns/ or tasks/ is never the book's note.

Evidence: a ``script-verified-wl`` entry's ``artifacts`` must name the ``.wl`` script. The checker does not
also require a log file. A ``literature-transcription`` may use
an ``arXiv:``, ``doi:``, ``https://``, or ``isbn:`` token instead of a path. Every other artifact must be a
path under ``--root`` that exists. ``depends_on`` is optional: comma-separated ids of premises in the book or in the
same fragment. Any of ``points``/``tolerance``/``machine`` marks a numerical claim and then all four of those plus
``env`` are required. A ``script-verified-wl`` claim does not need them.

``% claim:`` block (read by --promote). Immediately after a ``\\label{...}`` that states a result, the note
carries comment lines ``% claim: key = value``. Blank lines and ``\\end{...}`` lines are skipped. So is the
rest of an ``equation``/``split`` the label is already inside (the formula line, then ``\\end{equation}``),
and an ``equation``/``split`` that sits between the label and the block and contains no other ``\\label``.
The first other line ends the search, and an environment that contains a different label is not crossed,
so a block after prose or after someone else's equation is not adopted. Blank lines between claim lines
are skipped:

    \\label{eq:c3-final}
    \\end{equation}
    % claim: id = c3_final
    % claim: statement = The temporal flat DBI boost fixes \\tilde{c}_3 = 3(1-c_s^2)/2.
    % claim: verification = script-verified-wl
    % claim: artifacts = mathematica_scripts/04_dbi_boost_invariance_flat_check.wl; out_err_files/04_dbi_boost_invariance_flat_check_errors_<stamp>.txt
    % claim: date = 2026-08-18
    % claim: depends_on = <comma-separated premise ids>                (optional)
    % claim: formula = \\tilde{c}_3 = 3(1-c_s^2)/2           (optional)
    % claim: list = established                                        (optional; default established;
                                                                        `given` for a transcription,
                                                                        `fenced` for a fence: then keys are
                                                                        id, statement, witness only)

Keys ``id``, ``statement``, ``verification``, ``artifacts``, ``date`` are required. Any of ``points``/``tolerance``/
``machine`` marks a numerical claim and then all four of those plus ``env`` are required. ``file`` and ``section`` are filled in from the note path and the label. ``--promote`` and ``--write`` require an explicit ``--signed``
date; the script never stamps today.
"""
import argparse
import datetime
import json
import os
import re
import sys
import time
import traceback
from typing import Dict, List, Optional, Tuple

# Root is just this script's own location -- no hardcoded path.
main_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out_err_folder = os.path.join(main_folder, "out_err_files")
os.makedirs(out_err_folder, exist_ok=True)


class Tee:
    """Write to multiple file-like objects simultaneously."""

    def __init__(self, *files):
        self.files = files

    def write(self, obj):
        if obj is None:
            return
        for f in self.files:
            f.write(obj)
            f.flush()

    def flush(self):
        for f in self.files:
            f.flush()

    def isatty(self):
        return bool(self.files) and hasattr(self.files[0], "isatty") and self.files[0].isatty()


BOOK_REL = os.path.join("latex_notes", "structure", "claims.json")
TOP_KEYS = {"given", "established", "fenced", "retired_ids"}
CITABLE_LISTS = ("given", "established")
VERIFICATION = {"script-verified-wl", "literature-transcription"}
NUMERICAL_KEYS = ("points", "tolerance", "machine", "env")  # all four required for a numerical claim
NUMERICAL_ONLY = ("points", "tolerance", "machine")          # presence of any of these marks the claim numerical
ID_RE = re.compile(r"^[a-z0-9_]+$")
INNER_RE = re.compile(r"^inner::([A-Za-z0-9_]+)$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def is_date(x: object) -> bool:
    """A real calendar date in YYYY-MM-DD (2026-02-31 is not)."""
    if not isinstance(x, str) or not DATE_RE.match(x):
        return False
    try:
        datetime.date.fromisoformat(x)
    except ValueError:
        return False
    return True
CLAIM_LINE_RE = re.compile(r"^\s*%\s*claim:\s*([a-z_]+)\s*=\s*(.*?)\s*$")
KNOWN_KEYS = {"id", "statement", "verification", "artifacts", "date", "depends_on", "formula", "list",
              "witness", "points", "tolerance", "machine", "env"}
LITERATURE_RE = re.compile(r"^(arXiv:|doi:|https?://|isbn:)", re.IGNORECASE)  # external-paper identifiers


class Report:
    """Collects FAIL / ok lines; nonzero exit if any FAIL."""

    def __init__(self) -> None:
        self.fails: List[str] = []

    def bad(self, msg: str) -> None:
        self.fails.append(msg)
        print("FAIL " + msg)

    def ok(self, msg: str) -> None:
        print("ok   " + msg)


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_json_checked(path: str, rep: Report, what: str) -> Optional[dict]:
    """JSON that fails to parse, or is not an object, is a FAIL -- not a crash."""
    try:
        doc = load_json(path)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        rep.bad(f"{what}: {os.path.relpath(path, main_folder) if os.path.isabs(path) else path} is not valid JSON ({exc})")
        return None
    if not isinstance(doc, dict):
        rep.bad(f"{what}: top level must be a JSON object, got {type(doc).__name__}")
        return None
    return doc


def resolve(path: str, root: str) -> str:
    """Absolute, normalized path for an entry path under --root."""
    if os.path.isabs(path):
        return os.path.realpath(path)
    return os.path.realpath(os.path.join(root, path))


def is_under(path_abs: str, folder_abs: str) -> bool:
    """True if the resolved path lies strictly inside the resolved folder (no `..` escapes, no prefix tricks)."""
    folder = os.path.realpath(folder_abs)
    try:
        rel = os.path.relpath(path_abs, folder)
    except ValueError:  # different drives (not on macOS, kept for safety)
        return False
    return rel != "." and not rel.startswith(os.pardir + os.sep) and rel != os.pardir


def source_ok(lst: str, f: object, root: str) -> Optional[str]:
    """Sourcing rule. Returns None if the entry's `file` is an allowed source, else the reason.
    Every list: a .tex inside <root>/latex_notes/ (resolved path; `..`, symlinks and absolute paths do not escape).
A note under campaigns/ or tasks/
    is never the book's note."""
    if not isinstance(f, str) or not f.strip():
        return "no 'file'"
    if os.path.isabs(f):
        return f"file must be repository-relative, got absolute path {f!r}"
    fabs = resolve(f, root)
    if not (is_under(fabs, os.path.join(root, "latex_notes")) and fabs.endswith(".tex")):
        return (f"a {lst!r} entry must be sourced from a .tex under latex_notes/ (got {f!r}) -- "
                f"a note under campaigns/ or tasks/ is not the book's note; transcribe into latex_notes/ first")
    return None


def empty_book() -> dict:
    return {"given": [], "established": [], "fenced": [], "retired_ids": {}}


def load_inner() -> Tuple[Dict[str, dict], Dict[str, dict]]:
    """Returns two empty dicts and opens no file."""
    return {}, {}


def merged_view(book: dict, extra: Optional[dict]) -> dict:
    """Book plus (optionally) a fragment, as one dict with the same four keys."""
    view = {k: list(book.get(k, [])) for k in ("given", "established", "fenced")}
    view["retired_ids"] = dict(book.get("retired_ids", {}))
    if extra is not None:
        for k in ("given", "established", "fenced"):
            view[k].extend(extra.get(k, []))
        view["retired_ids"].update(extra.get("retired_ids", {}))
    return view


def check_structure(doc: dict, rep: Report, what: str) -> bool:
    keys = set(doc.keys())
    if keys != TOP_KEYS:
        rep.bad(f"{what}: top-level keys are {sorted(keys)}, must be exactly {sorted(TOP_KEYS)}")
        return False
    for k in ("given", "established", "fenced"):
        if not isinstance(doc[k], list):
            rep.bad(f"{what}: '{k}' must be a list")
            return False
    if not isinstance(doc["retired_ids"], dict):
        rep.bad(f"{what}: 'retired_ids' must be an object")
        return False
    return True


def check_view(view: dict, root: str, rep: Report, inner: Dict[str, dict], inner_retired: Dict[str, dict]) -> None:
    """All consistency checks on a merged view (book, or book + fragment). Malformed input is a FAIL, never a crash."""
    try:
        _check_view(view, root, rep, inner, inner_retired)
    except (TypeError, AttributeError, KeyError, ValueError) as exc:
        rep.bad(f"malformed entry: {type(exc).__name__}: {exc}")


def _check_view(view: dict, root: str, rep: Report, inner: Dict[str, dict], inner_retired: Dict[str, dict]) -> None:
    all_entries: List[Tuple[str, dict]] = []
    for lst in ("given", "established", "fenced"):
        for e in view[lst]:
            if not isinstance(e, dict):
                rep.bad(f"{lst}: an entry is not a JSON object ({type(e).__name__})")
                continue
            all_entries.append((lst, e))

    # ids: present, unique, well-formed, not retired
    ids: Dict[str, str] = {}
    for lst, e in all_entries:
        i = e.get("id")
        if not isinstance(i, str) or not i:
            rep.bad(f"{lst}: an entry has no 'id'")
            continue
        if i in ids:
            rep.bad(f"{i}: appears in both '{ids[i]}' and '{lst}'")
        ids[i] = lst
        if i in view["retired_ids"]:
            rep.bad(f"{i}: is in retired_ids and still listed in '{lst}'")
        if INNER_RE.match(i):
            rep.bad(f"{i}: this workspace has no inner corpus")
        elif not ID_RE.match(i):
            rep.bad(f"{i}: id must be snake_case [a-z0-9_]+")

    citable = {i for i, lst in ids.items() if lst in CITABLE_LISTS}
    fenced_ids = {i for i, lst in ids.items() if lst == "fenced"}

    # retired_ids shape
    for old, rec in view["retired_ids"].items():
        if not isinstance(rec, dict) or "replaced_by" not in rec or "reason" not in rec:
            rep.bad(f"retired_ids[{old}]: needs 'reason' and 'replaced_by'")
            continue
        rb = rec["replaced_by"]
        if not isinstance(rb, list) or not rb or not all(isinstance(r, str) for r in rb):
            rep.bad(f"retired_ids[{old}]: replaced_by must be a non-empty list of id strings")
            continue
        for r in rb:
            if r not in ids or ids[r] == "fenced":
                rep.bad(f"retired_ids[{old}]: replaced_by {r!r} is not a listed citable id")

    # per-entry fields
    for lst, e in all_entries:
        i = e.get("id", "<no id>")
        allowed = ({"id", "statement", "file", "section", "depends_on", "verification", "evidence",
                    "signed_off", "formula"} if lst in CITABLE_LISTS
                   else {"id", "statement", "witness", "file", "section"})
        unknown = sorted(set(e.keys()) - allowed)
        if unknown:
            rep.bad(f"{i}: unknown field(s) {unknown}")
        if lst in CITABLE_LISTS:
            for fld in ("statement", "file", "section", "depends_on", "verification", "evidence", "signed_off"):
                if fld not in e:
                    rep.bad(f"{i}: missing field '{fld}'")
            if not (isinstance(e.get("statement"), str) and e["statement"].strip()):
                rep.bad(f"{i}: statement must be a non-empty sentence")
            ver = e.get("verification")
            if ver not in VERIFICATION:
                rep.bad(f"{i}: verification {ver!r} not in {sorted(VERIFICATION)}")
            if lst == "established" and ver == "literature-transcription":
                rep.bad(f"{i}: 'established' can never be a literature transcription")
            if lst == "given" and ver != "literature-transcription":
                rep.bad(f"{i}: a 'given' must be a literature transcription (got {ver!r})")
            so = e.get("signed_off")
            if not is_date(so):
                rep.bad(f"{i}: signed_off must be a YYYY-MM-DD date (got {so!r})")
            # file / section -- sourcing rule: every list's file is a .tex under latex_notes/, never a run dir
            f = e.get("file", "")
            why = source_ok(lst, f, root)
            if why:
                rep.bad(f"{i}: {why}")
            fpath = resolve(f, root) if isinstance(f, str) and f else ""
            if not fpath or not os.path.isfile(fpath):
                rep.bad(f"{i}: file {f!r} does not exist")
            else:
                sec = str(e.get("section", ""))
                if not sec:
                    rep.bad(f"{i}: empty 'section'")
                elif fpath.endswith(".tex"):
                    with open(fpath, "r", encoding="utf-8") as fh:
                        if ("\\label{" + sec + "}") not in fh.read():
                            rep.bad(f"{i}: \\label{{{sec}}} not found in {f}")
                else:
                    rep.bad(f"{i}: file {f!r} is not a .tex note")
            # depends_on
            deps = e.get("depends_on", [])
            if not isinstance(deps, list):
                rep.bad(f"{i}: depends_on must be a list")
                deps = []
            for d in deps:
                if not isinstance(d, str):
                    rep.bad(f"{i}: depends_on entries must be id strings, got {type(d).__name__}")
                    continue
                if d == i:
                    rep.bad(f"{i}: depends on itself")
                elif d in fenced_ids:
                    rep.bad(f"{i}: depends_on {d!r} is fenced -- a fence is never a premise")
                elif d not in citable:
                    if d in view["retired_ids"]:
                        rep.bad(f"{i}: depends_on {d!r} is retired, replaced_by {view['retired_ids'][d]['replaced_by']}")
                    else:
                        rep.bad(f"{i}: depends_on {d!r} is not a citable id (book or fragment)")
            # evidence
            ev = e.get("evidence")
            if not isinstance(ev, dict):
                rep.bad(f"{i}: evidence must be an object with 'artifacts' and 'date'")
            else:
                arts = ev.get("artifacts")
                if not isinstance(arts, list) or not arts:
                    rep.bad(f"{i}: evidence.artifacts must be a non-empty list of paths")
                else:
                    for a in arts:
                        if not isinstance(a, str):
                            rep.bad(f"{i}: evidence artifact must be a string, got {type(a).__name__}")
                            continue
                        apath = a.split("::")[0].strip()
                        if ver == "literature-transcription" and LITERATURE_RE.match(apath):
                            continue  # an external paper is cited by identifier, not by path
                        if not apath or apath in (".", ".."):
                            rep.bad(f"{i}: empty evidence artifact {a!r}")
                        elif os.path.isabs(apath):
                            rep.bad(f"{i}: evidence artifact must be repository-relative: {apath}")
                        elif not os.path.isfile(resolve(apath, root)):
                            rep.bad(f"{i}: evidence artifact missing or not a file: {apath}")
                if not is_date(ev.get("date")):
                    rep.bad(f"{i}: evidence.date must be a YYYY-MM-DD date")
                # numerical claim: any of points/tolerance/machine present => all four incl. env
                present = [k for k in NUMERICAL_KEYS if k in ev]
                if any(k in ev for k in NUMERICAL_ONLY) and len(present) != len(NUMERICAL_KEYS):
                    rep.bad(f"{i}: numerical evidence needs all of {NUMERICAL_KEYS}, has {present}")
                if ver == "script-verified-wl":
                    arts_s = arts if isinstance(arts, list) else []
                    paths = []
                    for a in arts_s:
                        if isinstance(a, str):
                            paths.append(a.split("::")[0].strip().replace(os.sep, "/"))
                    if not any(p.endswith(".wl") for p in paths):
                        rep.bad(f"{i}: script-verified-wl evidence needs the .wl script among its artifacts")
        else:  # fenced
            for fld in ("statement", "witness"):
                if fld not in e:
                    rep.bad(f"{i}: fenced entry missing '{fld}'")
            if "signed_off" in e:
                rep.bad(f"{i}: a fence carries no signed_off -- it is not a result")
            for fld in ("verification", "evidence", "depends_on", "formula"):
                if fld in e:
                    rep.bad(f"{i}: a fence carries no '{fld}' -- a result-shaped record does not belong in 'fenced'")
            if not (isinstance(e.get("statement"), str) and e["statement"].strip()):
                rep.bad(f"{i}: fence statement must be a non-empty sentence")
            w = str(e.get("witness", ""))
            if not w.strip():
                rep.bad(f"{i}: empty witness")
            for wpart in w.split(";"):
                wpath = wpart.split("::")[0].strip()
                if not wpath or wpath in (".", ".."):
                    rep.bad(f"{i}: empty witness part {wpart!r}")
                elif os.path.isabs(wpath) or not os.path.isfile(resolve(wpath, root)):
                    rep.bad(f"{i}: witness path missing, not a file, or absolute: {wpath}")
            # a fence recorded in a note obeys the same sourcing rule as a result
            if "file" in e:
                why = source_ok("fenced", e["file"], root)
                if why:
                    rep.bad(f"{i}: fence 'file' -- {why}")
                else:
                    fpath = resolve(e["file"], root)
                    sec = str(e.get("section", ""))
                    if not os.path.isfile(fpath):
                        rep.bad(f"{i}: fence file {e['file']!r} does not exist")
                    elif not sec:
                        rep.bad(f"{i}: fence with 'file' needs a 'section'")
                    else:
                        with open(fpath, "r", encoding="utf-8") as fh:
                            if ("\\label{" + sec + "}") not in fh.read():
                                rep.bad(f"{i}: \\label{{{sec}}} not found in {e['file']}")

    # cycles among citable
    by = {e["id"]: e for lst, e in all_entries if lst in CITABLE_LISTS and "id" in e}
    seen: set = set()
    stack: set = set()

    def visit(node: str) -> None:
        if node in stack:
            rep.bad(f"dependency cycle at {node}")
            return
        if node in seen:
            return
        stack.add(node)
        for d in by.get(node, {}).get("depends_on", []) or []:
            if d in by:
                visit(d)
        stack.discard(node)
        seen.add(node)

    for node in by:
        visit(node)

    counts = (f"{len(view['given'])} given, {len(view['established'])} established, "
              f"{len(view['fenced'])} fenced, {len(view['retired_ids'])} retired")
    if rep.fails:
        print("counts " + counts)
    else:
        rep.ok(counts)


def parse_claim_blocks(note_path: str, labels: List[str], rep: Report) -> Dict[str, Dict[str, str]]:
    """For each label, the key=value pairs of the `% claim:` block that follows it."""
    with open(note_path, "r", encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    out: Dict[str, Dict[str, str]] = {}

    def code_part(line: str) -> str:
        """The line with any LaTeX comment stripped (a `%` not preceded by a backslash starts a comment)."""
        return re.split(r"(?<!\\)%", line, maxsplit=1)[0]

    for lab in labels:
        hits = [n for n, ln in enumerate(lines) if ("\\label{" + lab + "}") in code_part(ln)]
        if not hits:
            rep.bad(f"{lab}: \\label not found in {note_path} (labels inside comments do not count)")
            continue
        if len(hits) > 1:
            rep.bad(f"{lab}: \\label appears {len(hits)} times (lines {[h + 1 for h in hits]}); labels must be unique")
            continue
        idx = hits[0]
        # Skip the rest of an equation/split the label is already inside (formula line, then \end),
        # and an equation/split that sits between the label and the block and holds no other label.
        # Do not cross an environment that contains a different label: that block is theirs.
        # Prose outside those environments ends the search.
        env_re = re.compile(r"\\(begin|end)\{(equation\*?|split)\}")
        label_re = re.compile(r"\\label\{([^}]*)\}")

        def open_depth_at(at: int) -> int:
            depth = 0
            for i in range(at):
                for m_env in env_re.finditer(code_part(lines[i])):
                    if m_env.group(1) == "begin":
                        depth += 1
                    elif depth:
                        depth -= 1
            code = code_part(lines[at])
            lab_at = code.find("\\label{" + lab + "}")
            prefix = code if lab_at < 0 else code[:lab_at]
            for m_env in env_re.finditer(prefix):
                if m_env.group(1) == "begin":
                    depth += 1
                elif depth:
                    depth -= 1
            return depth

        def env_holds_other_label(start: int) -> bool:
            depth = 0
            for i in range(start, len(lines)):
                code = code_part(lines[i])
                pos = 0
                while pos < len(code):
                    m_env = env_re.search(code, pos)
                    m_lab = label_re.search(code, pos)
                    found = [(m.start(), "env", m) for m in (m_env,) if m]
                    found += [(m.start(), "lab", m) for m in (m_lab,) if m]
                    if not found:
                        break
                    found.sort()
                    kind, m = found[0][1], found[0][2]
                    if kind == "lab":
                        if m.group(1) != lab:
                            return True
                    else:
                        if m.group(1) == "begin":
                            depth += 1
                        else:
                            depth -= 1
                            if depth <= 0:
                                return False
                    pos = m.end()
            return False

        block: Dict[str, str] = {}
        n = idx + 1
        env_depth = open_depth_at(idx)
        started = False
        abort = False
        while n < len(lines) and not abort:
            ln = lines[n]
            if env_depth > 0:
                code = code_part(ln)
                if any(m.group(1) != lab for m in label_re.finditer(code)):
                    abort = True
                    break
                for m_env in env_re.finditer(code):
                    if m_env.group(1) == "begin":
                        env_depth += 1
                    elif env_depth:
                        env_depth -= 1
                n += 1
                continue
            m = CLAIM_LINE_RE.match(ln)
            if m:
                started = True
                key = m.group(1)
                if key not in KNOWN_KEYS:
                    rep.bad(f"{lab}: unknown '% claim:' key {key!r} (known: {sorted(KNOWN_KEYS)})")
                if key in block:
                    rep.bad(f"{lab}: duplicate '% claim:' key {key!r}")
                block[key] = m.group(2)
                n += 1
                continue
            if not ln.strip():
                n += 1
                continue
            code = code_part(ln).strip()
            if not code:
                break  # a comment that is not a claim line
            if re.match(r"\\end\{", code):
                n += 1
                continue
            # equation/split may sit between the label and the block, not after the block has started,
            # and not when it holds a different label
            if not started and re.match(r"\\begin\{(equation\*?|split)\}", code):
                if env_holds_other_label(n):
                    break
                env_depth = 1
                n += 1
                continue
            break
        if abort or not block:
            rep.bad(f"{lab}: no '% claim:' block follows the label "
                    f"(stopped at prose, another label, or a \\begin other than equation/split)")
            continue
        out[lab] = block
    return out


def entries_from_blocks(blocks: Dict[str, Dict[str, str]], note_rel: str, signed: str, rep: Report) -> dict:
    """Build a fragment (same four keys) from parsed blocks."""
    frag = empty_book()
    for lab, b in blocks.items():
        lst = b.get("list", "established")
        if lst == "fenced":
            missing = [k for k in ("id", "statement", "witness") if k not in b]
            if missing:
                rep.bad(f"{lab}: fenced claim block missing {missing}")
                continue
            frag["fenced"].append({"id": b["id"], "statement": b["statement"], "witness": b["witness"],
                                   "file": note_rel, "section": lab})
            continue
        if lst not in CITABLE_LISTS:
            rep.bad(f"{lab}: list must be one of {CITABLE_LISTS + ('fenced',)} (got {lst!r})")
            continue
        missing = [k for k in ("id", "statement", "verification", "artifacts", "date") if k not in b]
        if missing:
            rep.bad(f"{lab}: claim block missing {missing}")
            continue
        ev: Dict[str, str] = {
            "artifacts": [a.strip() for a in b["artifacts"].split(";") if a.strip()],
            "date": b["date"],
        }
        for k in NUMERICAL_KEYS:
            if k in b:
                ev[k] = b[k]
        entry: Dict[str, object] = {
            "id": b["id"],
            "statement": b["statement"],
            "file": note_rel,
            "section": lab,
            "depends_on": [d.strip() for d in b.get("depends_on", "").split(",") if d.strip()],
            "verification": b["verification"],
            "evidence": ev,
            "signed_off": signed,
        }
        if "formula" in b:
            entry["formula"] = b["formula"]
        frag[lst].append(entry)
    return frag


def write_book(book_path: str, book: dict, frag: dict) -> None:
    for k in ("given", "established", "fenced"):
        book[k].extend(frag[k])
    book["retired_ids"].update(frag.get("retired_ids", {}))
    os.makedirs(os.path.dirname(book_path), exist_ok=True)
    with open(book_path, "w", encoding="utf-8") as fh:
        json.dump(book, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def run(args: argparse.Namespace, rep: Report) -> None:
    root = os.path.abspath(args.root)
    book_path = os.path.join(root, BOOK_REL)
    print(f"root: {root}")
    print(f"book: {book_path} ({'exists' if os.path.exists(book_path) else 'ABSENT -- ledger empty'})")
    inner, inner_retired = load_inner()

    if os.path.exists(book_path):
        book = load_json_checked(book_path, rep, "book")
        if book is None:
            return
    else:
        book = empty_book()
    if not check_structure(book, rep, "book"):
        return

    modes = [m for m in ("promote", "merge", "fragment") if getattr(args, m)]
    if len(modes) > 1:
        rep.bad(f"choose one mode, got {modes}")
        return
    if args.signed and not is_date(args.signed):
        rep.bad(f"--signed must be a real YYYY-MM-DD date, got {args.signed!r}")
        return
    if (args.write or args.promote) and not args.signed:
        rep.bad("--promote and --write need an explicit --signed YYYY-MM-DD: the script never assumes today")
        return
    signed = args.signed or ""
    signed_note = "" if args.signed else "  (no --signed; this read does not stamp a date)"

    if args.promote:
        note_path = args.promote if os.path.isabs(args.promote) else os.path.join(root, args.promote)
        if not os.path.exists(note_path):
            rep.bad(f"--promote: note {note_path} does not exist")
            return
        note_rel = os.path.relpath(note_path, root)
        labels = [x.strip() for x in (args.labels or "").split(",") if x.strip()]
        if not labels:
            rep.bad("--promote needs --labels a,b,...")
            return
        print(f"\n--promote {note_rel}  labels={labels}  signed_off={signed}{signed_note}")
        blocks = parse_claim_blocks(note_path, labels, rep)
        frag = entries_from_blocks(blocks, note_rel, signed, rep)
        candidate = frag
    elif args.merge:
        fpath = args.merge if os.path.isabs(args.merge) else os.path.join(root, args.merge)
        if not os.path.exists(fpath):
            rep.bad(f"--merge: fragment {fpath} does not exist")
            return
        frag = load_json_checked(fpath, rep, "fragment")
        if frag is None or not check_structure(frag, rep, "fragment"):
            return
        accept = [x.strip() for x in (args.accept or "").split(",") if x.strip()]
        if accept:
            accept_set = set(accept)
            for k in ("given", "established", "fenced"):
                frag[k] = [e for e in frag[k] if isinstance(e, dict) and e.get("id") in accept_set]
            frag["retired_ids"] = {old: rec for old, rec in frag.get("retired_ids", {}).items() if old in accept_set}
            kept = [e["id"] for k in ("given", "established", "fenced") for e in frag[k] if isinstance(e, dict)]
            kept.extend(frag["retired_ids"].keys())
            unknown = [a for a in accept if a not in kept]
            if unknown:
                rep.bad(f"--accept ids not in fragment: {unknown}")
        if args.signed:
            for e in frag["established"] + frag["given"]:
                if isinstance(e, dict):
                    e.setdefault("signed_off", args.signed)  # the date the user just named; never today by default
        print(f"\n--merge {os.path.relpath(fpath, root)}  accept={accept or 'all'}  signed_off={signed or '(none)'}{signed_note}")
        candidate = frag
    elif args.fragment:
        fpath = args.fragment if os.path.isabs(args.fragment) else os.path.join(root, args.fragment)
        if not os.path.exists(fpath):
            rep.bad(f"--fragment: {fpath} does not exist")
            return
        frag = load_json_checked(fpath, rep, "fragment")
        if frag is None or not check_structure(frag, rep, "fragment"):
            return
        print(f"\n--fragment {os.path.relpath(fpath, root)} (check only)")
        candidate = None
        check_view(merged_view(book, frag), root, rep, inner, inner_retired)
        return
    else:
        print("\ncheck book")
        check_view(merged_view(book, None), root, rep, inner, inner_retired)
        return

    # promote / merge: record mode failures before the check, so a later FAIL is not preceded by "ok"
    n_cand = sum(len(candidate[k]) for k in ("given", "established", "fenced"))
    if args.merge and args.write:
        rep.bad("--merge never writes: a run fragment is a proposal. Transcribe the accepted results into a "
                "latex_notes/ note and use --promote on that note (the one write path).")
    if n_cand == 0 and not candidate.get("retired_ids"):
        rep.bad("no candidate entries -- nothing to promote")
    check_view(merged_view(book, candidate), root, rep, inner, inner_retired)
    print("\nCANDIDATE ENTRIES:")
    shown = {k: candidate[k] for k in ("given", "established", "fenced") if candidate[k]}
    if candidate.get("retired_ids"):
        shown["retired_ids"] = candidate["retired_ids"]
    print(json.dumps(shown, indent=2, ensure_ascii=False))
    if rep.fails:
        print(f"\nNOT WRITTEN: {len(rep.fails)} FAIL(s) above. Nothing touched the book.")
        return
    if args.merge:
        print(f"\nPROPOSAL READ: {n_cand} entr{'y' if n_cand == 1 else 'ies'} valid in book + fragment. "
              f"--merge never writes; transcribe the accepted ones into latex_notes/ and --promote.")
        return
    if not args.write:
        print(f"\nDRY RUN: {n_cand} entr{'y' if n_cand == 1 else 'ies'} valid. "
              f"Re-run with --write on the user's explicit word to append them to the book.")
        return
    write_book(book_path, book, candidate)
    rep.ok(f"WRITTEN: {n_cand} entr{'y' if n_cand == 1 else 'ies'} appended to {os.path.relpath(book_path, root)} "
           f"with signed_off={signed}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=main_folder, help="workspace root (default: this workspace)")
    parser.add_argument("--fragment", help="check this fragment against book + fragment (no write)")
    parser.add_argument("--promote", metavar="NOTE.tex", help="draft entries from the note's %% claim: blocks")
    parser.add_argument("--labels", help="comma-separated \\label names to promote")
    parser.add_argument("--merge", metavar="FRAGMENT.json", help="take a run's fragment")
    parser.add_argument("--accept", help="comma-separated ids to keep from the fragment (default all)")
    parser.add_argument("--signed", help="signed_off date YYYY-MM-DD (required for --promote and --write; never defaulted to today)")
    parser.add_argument("--write", action="store_true", help="append the validated candidates to the book")
    args = parser.parse_args()

    # --- SETUP LOGGING ---
    start_time = datetime.datetime.now()
    tz_name = time.tzname[0] if time.tzname else "UTC"
    script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    out_name = f'{script_name}_output_{start_time.strftime("%Y%m%d_%H%M%S_%f")}_{tz_name}.txt'
    err_name = f'{script_name}_errors_{start_time.strftime("%Y%m%d_%H%M%S_%f")}_{tz_name}.txt'
    log_file_path = os.path.join(out_err_folder, out_name)
    error_file_path = os.path.join(out_err_folder, err_name)
    log_file_handle = open(log_file_path, "w", encoding="utf-8")
    error_file_handle = open(error_file_path, "w", encoding="utf-8")
    original_stdout = sys.stdout
    original_stderr = sys.stderr


    rep = Report()
    exit_code = 0
    try:
        sys.stdout = Tee(original_stdout, log_file_handle)
        sys.stderr = Tee(original_stderr, error_file_handle)
        print(f"Script: {script_name}.py")
        print(f"Started: {start_time}")
        print(f"Interpreter: {sys.executable}")
        print(f"Args: {vars(args)}")
        run(args, rep)
        if rep.fails:
            print(f"\nRESULT: {len(rep.fails)} FAIL(s)")
            exit_code = 1
        else:
            print("\nRESULT: clean")
    except Exception as exc:
        print(f"\nUNHANDLED EXCEPTION in main: {exc}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        exit_code = 1
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        log_file_handle.close()
        error_file_handle.close()
        print(f"Logs saved to: {out_err_folder}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

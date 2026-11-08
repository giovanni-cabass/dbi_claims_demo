# Established Results — the law and the lookup recipe

This is the governing rule for `claims.json`, the result ledger. It is **law and recipe, not a
dump**: it says what counts as a citable result in this workspace, where the citable sentences
live, where their proofs live, and how to look one up.

A heading still printed below has not been folded. Once it is gone, the sentence lives only in
`claims.json`.

Not-yet-verified content is quarantined elsewhere.

**Where things live.**
- **The book — citable sentences:** `latex_notes/structure/claims.json` — a JSON object with the four top-level keys `given`, `established`, `fenced`, `retired_ids` (schema below). Only a fold (below) writes to it. The book starts empty, and a heading still printed below the law stays citable until that note is folded. There is no Level 0 corpus. Level 1 is a task note, or later a campaign fragment. Level 2 is `claims.json`, the only thing later work cites.
- **Proofs and derivations:** `latex_notes/*.tex`, one `\label` per citable sentence, each followed by its **`% claim:` block** (the entry's fields as LaTeX comment lines — format in `check_claims.py --help`). The block is how a note states "this label is a result": it is written with the note, read by the fold, and never is a result by itself.
- **Verification artifacts:** `out_err_files/*.txt` (script logs) and `mathematica_outputs/`.
- **Run fragments (campaign mode only):** a campaign run ends with `campaigns/NN/run_MM/claims.json`, a file with the book's schema holding the run's *candidate* entries, extracted from the `% claim:` blocks of the run's own note. It is a **proposal to read**, not a write path: its entries point at the run's note, which the sourcing rule (below) does not accept as a source — the accepted ones are transcribed into a `latex_notes/` note at fold. Ordinary tasks have no fragment: their candidates are the `% claim:` blocks in the note.
- **Checker and fold command:** `python_scripts/check_claims.py`. Plain: checks the book — every `file` exists and obeys the sourcing rule (every list: a `.tex` inside `latex_notes/`); absolute paths and `..` escapes are refused; every `section` label exists in that file, every `depends_on` resolves to a citable id, never to a fence, no self-dependency, no cycle, no id in two lists, every citable entry has `signed_off`, every evidence path exists. Evidence is a `.wl` script and its clean log, or a literature transcription. An `established` entry must be `script-verified-wl` and is refused if it is `literature-transcription`. A `given` must be `literature-transcription` and is refused otherwise. A `script-verified-wl` entry is citable without `points`, `tolerance`, `machine`, or `env`. If any of `points`, `tolerance`, or `machine` is present, all four of those plus `env` are required. A citation token (`arXiv:`, `doi:`, `https://`, `isbn:`) is not a file. `--promote NOTE --labels a,b` drafts entries from those labels' `% claim:` blocks, validates, and prints them — **the one write path**, with `--write` on the user's explicit word. `--merge FRAGMENT [--accept ids]`: validates a run's proposal the same way, for reading and culling — it **never writes**, with or without `--write`; the accepted entries reach the book only by transcription into a `latex_notes/` note and `--promote`. Exit 1 on any FAIL; nothing is written if anything fails.

---

## Trust rule (binary, no exceptions)

A sentence is citable as `established` if and only if it is **machine-verified** *and* **signed off by the user**, with the verification artifact recorded. Both conditions are necessary; neither is sufficient alone.

- **Machine-verified** means one of:
  - **script-verified (`.wl`)** — name of the script in `mathematica_scripts/` and the date of its clean run (0-line error log in `out_err_files/`);
  - **literature transcription, re-checked** — paper + equation number / `\label`, with the transcription re-read against the source. This is the artifact type of a `given`, never of an `established`.
- **Signed off** means the user said so for that entry, on a date recorded in the entry. A clean script that the user has not signed does not qualify. Prose arguments alone never qualify. An agent's own confidence never qualifies.

**Agents never write to the book.** A result lives in the note — the sentence, its `\label`, its `% claim:` block naming the artifact — and in the artifact itself; that is where an agent's work ends. The same holds for a new `given` (a transcription in a `latex_notes/` note, with its own block) and for a `fenced` entry. Entering the book is the **fold**, below, and the fold starts from the user, not from the agent.

## The fold (note → book)

The fold is the only operation that changes `claims.json`, and it adds **no new mathematics**: it transcribes sentences whose artifacts already exist. Two cases, one command.

**Ordinary task (the default).** The task closes with its note, scripts and logs. The user reads the note and the logs. If the task did not succeed, nothing happens — the note stays as a process record. If it did, **the user names the labels** that are results: "promote `eq:a` and `eq:b`, not the third". On that word the agent runs
`check_claims.py --promote latex_notes/<note>.tex --labels eq:a,eq:b --signed <date>`, reads the printed entries back to the user, and on "write" re-runs with `--write`. Typing, not judgment: the agent proposes nothing and strikes nothing. The paste-ready prompt is `latex_notes/structure/README.how_to_fold.txt`.

**Campaign run.** The run delivers its own note (inside the immutable run dir, with `% claim:` blocks) and `campaigns/NN/run_MM/claims.json`, the fragment extracted from those blocks — the run *proposes*, because in campaign mode the user is not the expert who could name the labels. The run's note is **not** the book's note: the sourcing rule still holds, and the checker refuses an `established` entry whose `file` is under `campaigns/`. The fold is therefore: the user dry-runs `check_claims.py --merge <fragment>` to read the proposal and decides which ids to keep; the accepted results are **transcribed** — no new mathematics — into a `latex_notes/<note>.tex` with their blocks carried over and their `artifacts` still pointing into the run dir; then `--promote` on that note, exactly as for a task. The fragment stays in the run dir as the record of what was proposed. Batch in effort, **per-id in effect**: a run that proves three things and overreaches on a fourth lands three.

In both cases there is **one write path** — `--promote` on a `latex_notes/` note, `--write` on the user's word — and the accepted entries land with the `signed_off` date the user gave. A note or fragment whose labels were never promoted stays in place, unsigned, never cited. A task's or run's contribution is recoverable from the book afterwards by filtering `file` / `evidence` paths — never a second book.

## Sourcing rule

The source of a citable sentence is the **`latex_notes/*.tex` note** (plus its verification artifact) — nothing else.
- Task files and campaign files are process records: what was asked, how it unfolded, dead ends, corrections-in-progress. They are **not** a source of results and are not kept synchronized with the notes.
- Chat transcripts, agent reports, and this file are not sources either.
- Copy a `statement` from the note, never from memory and never from another summary.

## Scope rule

An `established` entry covers exactly the sentence it states, in the regime it states, as audited from the task that produced it. No forward-looking flags, predictions, or "open items" in the ledger. If a downstream consequence turns out to matter, it is derived, verified, and signed when a named task reaches it — not guessed at in advance here.

## Correction rule

When a signed entry turns out wrong: the latex note is overwritten cleanly (with a visible correction notice if the note is kept rather than retired), the JSON entry is corrected or moved to `retired_ids`, and the task file that produced it gets a visible `> **Corrected [date].**` blockquote. The old sentence is never silently edited in place in the JSON.

---

## The three lists

| List | Meaning | Citable as a premise? |
|---|---|---|
| `given` | An inherited definition or a literature transcription, re-checked against its source. | Yes |
| `established` | Derived in this workspace, machine-verified, user-signed. | Yes |
| `fenced` | A named class of attempts that failed, with a witness. | **No** — readable only |

There is no `measured` and no `open`. Unsigned work stays out of the ledger entirely — there is no "ran but not signed" status.

### `fenced` atoms

A `fenced` atom names a failed class and its scope, with a `witness` (script, log, or note that closed it). It may be **read** so that a later task does not retry a dead class. It may **not** be used as a premise and may **not** appear in `depends_on` of an `established` claim. A fence closes a class of attempts, not a question. The list starts empty.

---

## Schema (for `latex_notes/structure/claims.json`)

Each **citable** atom (`given` or `established`) has:

| Field | Role |
|---|---|
| `id` | Stable token `[a-z0-9_]+`, unique across all lists. `inner::` is not an id in `given`, `established`, or `fenced`. The checker keeps the pattern only so such an id fails closed. |
| `statement` | One sentence plus the regime (a DBI regime if it needs an example: $H\ell\ll 1$, unitary gauge). No proof. |
| `formula` | Optional. The display equation only, as a TeX string. |
| `file` | `latex_notes/<note>.tex` — for every list. A literature pointer goes in `evidence.artifacts` as an `arXiv:`, `doi:`, `https://`, or `isbn:` token, not as a path. That token is not a file. |
| `section` | A `\label{...}` that exists in `file` (prefer `eq:...` for identities). |
| `depends_on` | The citable ids this sentence actually uses. Never a `fenced` id. |
| `verification` | `script-verified-wl` or `literature-transcription`. An `established` entry must be `script-verified-wl`. A `given` must be `literature-transcription`. |
| `evidence` | A `script-verified-wl` entry is the `.wl` plus the log under `out_err_files/` and the date. If more than one artifact backs an entry, the date is the most recent clean run among them. A `literature-transcription` is the citation token plus the re-check date. The quartet `points`, `tolerance`, `machine`, `env` is optional; if any of `points`, `tolerance`, or `machine` is present, all four are required. |
| `signed_off` | Date. Required for `established`. For `given`, the date the transcription was re-checked. |

Each **fence** atom has `id`, `statement` (the failed class and its scope), `witness`, and `file`/`section` if a note records it. No `signed_off` — it is not a result.

`retired_ids` maps an old id to `{"reason": ..., "replaced_by": [citable ids]}` so that old citations still resolve.

Statuses are kept in **physically separate arrays**; never a single array distinguished only by a `status` field.

---

## Lookup recipe

1. On a **named task**, when a result is needed: search `latex_notes/structure/claims.json` for the `id` (or for a word in `statement`).
2. Read the `statement` (and `formula` if present). If the proof, the caveat in context, or the regime matters, open `file` at `section`. **Do not reconstruct from memory. Do not paste the catalogue into this file.**
3. If the id is in `fenced`: you may note that the class is dead; you may not use it.
4. If the sentence is **not there**: it is not citable. Say so. **Missing from the ledger is not a task** — the user names the work. Do not start deriving it "to fill the hole".
5. A sentence that sits only in a note's `% claim:` block, or only in a campaign run's fragment, is **not** citable. Cite the book, or promote the dependency in the same fold.

The ledger is the **scientific map** of what this workspace may build on; it is not the roadmap and not the record of how work proceeded (that is the task and campaign files, and the unfolded fragments).

## Literature reference folders (pointers only, no physics claims)

- `2203.08232v1` — EFT of inflation review.
- `2404.01894v2` — the DBI Collider scalar paper (flat-space reference).
- `1607.03735v1` and `1806.10587v2` — spinning fields in the cosmological collider (conventions and formulas for spin-1/spin-2 work).
- `1911.04490v2` — Bonifacio et al., flat-space DBI matter couplings (flat-space starting point for the spin extensions).

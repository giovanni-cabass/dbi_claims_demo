HOW TO FOLD A RESULT INTO THE LEDGER (latex_notes/structure/claims.json)

Command: python_scripts/check_claims.py. A person decides what gets promoted; an assisting agent,
if one is used, only types the command and reports what it says. Nothing enters the book without
--write, and --write refuses to run without an explicit --signed YYYY-MM-DD (the date is named by
hand; the script never assumes today).

This procedure is governed by latex_notes/structure/established-results.md ("The fold"); what
follows is the mechanical procedure itself, which check_claims.py actually enforces.

------------------------------------------------------------------------------------------------
THE ORDINARY FOLD (read a note, decide which results are citable, promote them)
------------------------------------------------------------------------------------------------

0. The work behind the note is done, and its logs in out_err_files/ have been read. A decision has
   been made about which of its \label{...}-tagged results are actual, citable claims. If none:
   stop here, nothing happens.

1. Dry run first (no write):

     python3 python_scripts/check_claims.py \
         --promote latex_notes/<note>.tex --labels eq:<a>,eq:<b> --signed <YYYY-MM-DD>

   Read the log it writes to out_err_files/. Any FAIL: the fix belongs in the note's own
   `% claim:` block (see below) — never in loosening the check so it passes. If clean, the command
   prints the CANDIDATE ENTRIES verbatim.

2. Read the candidate entries against the note itself. If a statement isn't the sentence the note
   actually asserts, or an artifact citation is wrong, fix the `% claim:` block and repeat step 1.
   If the entries are right, re-run the same command with --write added, then re-run
   `check_claims.py` with no arguments to confirm the whole book is still clean.

------------------------------------------------------------------------------------------------
THE `% claim:` BLOCK ITSELF
------------------------------------------------------------------------------------------------

Immediately after a `\label{...}` that states a result, the note carries comment lines:

    \label{eq:example}
    % claim: id = some_id
    % claim: statement = Plain-English sentence this equation asserts.
    % claim: verification = script-verified-wl
    % claim: artifacts = mathematica_scripts/some_check.wl; out_err_files/some_check_errors_<stamp>.txt
    % claim: date = YYYY-MM-DD
    % claim: depends_on = <comma-separated ids>              (optional)
    % claim: formula = <LaTeX>                                (optional)

`--promote` reads exactly this block — it never infers a claim's content from the surrounding
prose, and it never writes anything beyond what the block states.

------------------------------------------------------------------------------------------------
THE CAMPAIGN-MODE FOLD
------------------------------------------------------------------------------------------------

A second fold path exists for results proposed by a sealed, pre-registered "campaign" run rather
than an ordinary task: the run's own proposed claims get reviewed and culled, transcribed
(verbatim, no new mathematics) into an ordinary note, and then promoted exactly as above. That
machinery — a `campaigns/` directory, one immutable run record per campaign — is built into
`check_claims.py`.

------------------------------------------------------------------------------------------------
NOTES
------------------------------------------------------------------------------------------------
- A `fenced` entry is never a premise — the checker refuses a `depends_on` that points at one.
- Correcting an already-signed entry never edits its sentence in place: the id is retired and a
  new entry takes its place.

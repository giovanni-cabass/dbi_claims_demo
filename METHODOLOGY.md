# Methodology and tooling

This expands on the methodology summary in [`README.md`](README.md) — the full inventory of rule
files, skills, and subagents behind this project's verification discipline, for both coding tools
used across the project.

## Claude Code

- **Rule files** (`.claude/rules/*.mdc`) fix conventions project-wide, loaded automatically into
  every session rather than trusted to memory: `tensor-calculus-conventions.mdc` (metric
  signature, index notation, which of the three legal DBI-metric forms applies where),
  `mathematica-general-rules.mdc` (script structure, deterministic seeding, the
  run-then-read-the-log verification protocol), `latex-conventions.mdc`, `established-results.mdc`
  (the claim-ledger law itself — trust/sourcing/correction rules), `matrix-cookbook-reference.mdc`,
  `file-lifecycle-conventions.mdc` (how a result gets corrected or retired without destroying its
  history), and `stepwise-task-execution.mdc` (the dual-review process below, as a rule rather
  than an ad hoc habit).
- **Specialized skills** (`.claude/skills/*`), each invoked only when its specific failure mode is
  actually in play, not by default:
  - *Verification methods:* `dimensional-analysis` ($\lambda$-scaling consistency),
    `experimental-algebra` (numerical falsification of a symbolic identity by substituting random
    test functions — a last resort when direct simplification is stuck), `llf-trick`
    (local-Lorentz-frame shortcut for covariant derivatives), `scale-invariance` (the de
    Sitter-invariance check for a Lagrangian density).
  - *Domain-specific discipline:* `stueckelberg-discipline` (what the $t\to t+\pi$ substitution
    does and doesn't touch), `dbi-embedding-scalar` (the $\phi/\kappa/\tilde g$ bookkeeping and the
    curl-obstruction gate from §1 that forces the flat/sub-horizon limit).
  - *The Method B toolchain* (§2 of `README.md`): `ansatz-basis-enumeration`,
    `eom-invariance-imposition`, `eom-crosscheck` — building, constraining, and cross-checking an
    equation-of-motion-level ansatz with no Lagrangian ever written.
  - *Multi-agent deliberation:* `method-search` and `research-council`, structured adversarial
    debates (a champion proposes, independent referees attack, a synthesizer rules) used to decide
    whether a candidate method is even worth pursuing before committing real derivation time to
    it — this is literally how the Lean/general-spin question in §2 was evaluated and parked.
- **Narrow-charter subagents** hand work off to each other rather than one general agent doing
  everything end to end: `physics-theorist` (pure symbolic/LLM reasoning, no code — derivations and
  sign/convention checks), `mathematica-expert` (writes and runs actual Wolfram Language scripts
  to machine-verify a claim), `latex-writer` (typesets an already-verified result into a note).
- **Dual-adversarial review:** a stepwise unit of derivation is checked by two independent
  reviewers using genuinely different methods (e.g. one re-derives by hand, one machine-verifies
  numerically), and any disagreement between them blocks progress until it's reconciled.

## Cursor: the same discipline, scaled up

Cursor's rule-file system mirrors Claude Code's: the same physics/writing conventions (tensor
calculus, LaTeX, Mathematica scripting, established-results) are ported into `.cursor/rules/*.mdc`
so both tools work from one consistent set of conventions, plus Cursor-specific orchestration
rules — `cursor-task-scaffold.mdc`, `cursor-task-execute.mdc`, `no-destructive-commands.mdc` (git
restricted to read-only inspection, every state-mutating command forbidden) — and one generated
`task-NN-orchestration.mdc` file per task actually scaffolded.

Claude Code's dual-adversarial review (above) checks one task unit at a time, triggered
explicitly, no auto-chaining. Cursor runs a heavier version of the same principle for tasks large
enough to span hours and many subagents in a single run — this project's actual highest-usage
case for Cursor, not its lowest. The work splits into two separately-triggered phases:

- **Scaffold** — generation only. Reads a plain task spec and builds the file family:
  phase-by-phase sub-specs, implementer agents, and a dedicated cross-check/post-merge auditor per
  phase. Stops and reports; never executes in the same pass.
- **Execute** — runs the generated scaffold wave by wave: implement → parallel multi-lens audit →
  repeat → merge → post-merge deep audit.

The scaffold step is itself audited before execution ever starts: one auditor checks what the
orchestrating agent built, one more auditor per helper subagent checks what that subagent built
(including whether it quietly pre-loaded an expected answer instead of just stating the goal), and
all of them report to a final auditor that synthesizes a verdict — with further fresh-eyes rounds
available to re-target whatever weak link the previous round found. Same underlying rule as Claude
Code's own review — independent methods required to agree before anything advances — just scaled
to match work that size. Cursor is chosen for this specific class of work because of its
usage-based rate limits: not a bare cost-saving move, but specifically what makes affording
multi-hour, multi-subagent orchestration possible at all.

Cursor is also the designated tool for campaign mode: a sealed, single-shot research-direction
run, reserved for cases where Cabass has set a goal but isn't the one who can specify the next
concrete step — unlike an ordinary task, which Cabass specifies directly. A campaign spec,
written by Cabass, sets the envelope: the method and scope in play, what counts as
progress, what counts as a rewriting rather than a result, and what a credible negative looks
like. Inside that envelope, a run is proposed as a signed intent, then executed in its own
immutable directory; once launched, a run is never edited or widened mid-course — a flawed run is
abandoned and followed by a new one that cites it, not patched in place. A run never writes to the
shared ledger itself: folding its result into `claims.json`/`latex_notes/` is a separate, later
step that adds no new mathematics, under the same fold procedure (`check_claims.py`/
`README.how_to_fold.txt`) as any other result. Two concrete cases this is built for, both named in
`README.md` §2: generalizing Method B from a spin-by-spin construction to a single method for
generic spin $s$, and the on-shell/correlator direction. Campaign mode is built; no campaign has
actually been run in this project yet.

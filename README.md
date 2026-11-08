# Brief: DBI Cosmological Collider project, for website work

This is a cold-start summary for whoever (human or agent) is working on Giovanni Cabass's
website and needs to know what this project is, where it stands, and what might be shown
publicly. It is written to be self-contained — no access to the project's own workspace is
assumed. It describes the state of things as of **2026-11-08**; re-check before relying on any
status claim below if this file is read much later.

## 1. The physics problem

The project constructs the **DBI Cosmological Collider**: a coupled system of a Goldstone mode
and a spinning massive field, built so that the **DBI boost symmetry** — the nonlinearly
realized Lorentz-like boost native to DBI/brane actions — is imposed correctly in a
cosmological (FRW / de Sitter) background, not just in flat spacetime.

Why this is a real gap: a 2024 paper (arXiv:2404.01894) builds the general effective-field-theory
("cosmological collider") Lagrangian for a massive spinning field coupled to inflationary
fluctuations, and separately checks DBI boost invariance — but does that check in flat
spacetime. It is not a priori obvious how the DBI boost is even *defined* once the background is
curved and expanding, let alone how it constrains the EFT's free couplings. Two things follow
once that's settled:

- **Parameter reduction.** In the pure scalar (Goldstone) sector, DBI symmetry is already known
  to fix two parameters that are otherwise free in the generic EFT (the sound speed $c_s$ and a
  cubic coupling $\tilde c_3$). The cosmological, spin-carrying generalization of this fact is the
  target.
- **Spinning fields.** Spin-1 and spin-2 come with explicit candidate Lagrangians in the
  literature (arXiv:1607.03735, arXiv:1806.10587) to cross-check against, and are the concrete
  stepping stones toward a general method, for any spin $s$, that says how many free parameters
  DBI symmetry leaves.

The technical heart of the problem: the DBI boost is defined by pulling back the isometries of a
5D de Sitter ambient space to the inflationary brane. Any action built covariantly out of the
induced metric $\tilde g_{\mu\nu} = g_{\mu\nu} + a^2\,\partial_\mu\phi\,\partial_\nu\phi$ (for a
genuine ambient embedding scalar $\phi$) is automatically DBI-invariant — a clean closure
theorem. But the realistic, Stueckelberg-form metric actually used to build operators,
$\tilde g_{\mu\nu} = \bar g_{\mu\nu} + f\,\partial_\mu(t+\pi)\,\partial_\nu(t+\pi)$, is *not* of
that ambient form once the Goldstone $\pi$ has spatial dependence and $H \neq 0$: there's a
curl/integrability obstruction that blocks exact FRW invariance. The closure theorem only holds
in the flat-space / sub-horizon limit $H\ell \ll 1$. Tracking exactly where this limit is used,
and never silently promoting a flat-space-only invariance claim to an exact FRW one, is a
recurring theme of the whole project.

## 2. Scope: two construction methods, and the longer-term ambition

The scope here is wider than "finish spin-1 and spin-2 and stop." Two independent construction
methods are being pursued:

- **Method A — Lagrangian construction.** Build the action directly, covariantly in the induced
  DBI metric; this is the method described in §1, and the subject of the status in §3.
- **Method B — automated, equation-of-motion-first construction.** Postulate the equation of
  motion directly, with no Lagrangian ever written: build a symmetry-forced candidate-term
  basis, impose DBI invariance on it, then cross-check the result against Method A's. This is
  implemented as a dedicated toolchain of purpose-built workflows handling basis construction,
  symmetry imposition, and cross-checking. It is closed and fully machine-verified at spin 0;
  extending it past spin 0 hasn't started and is itself a genuinely open technical problem — the
  classification step it depends on has only ever been exercised on a scalar-type equation.

Beyond spin-2, the actual long-term goal is a method that settles any spin $s$ at once, rather
than re-running a spin-by-spin construction forever. The hoped-for handle for that: the
background that spontaneously breaks the DBI boost (the inflating FRW background) and a
boost-*preserving* configuration are related by the very symmetry that's broken — the broken
background is reachable from an unbroken one by acting with a DBI boost. If that relation can be
exploited directly at the level of on-shell quantities (correlators / Ward identities for the
broken generator) rather than through an explicit off-shell Lagrangian or equation of motion
built field by field, the hope is that the resulting constraint is structural and spin-blind — in
the same spirit as a soft theorem from a spontaneously broken symmetry not caring about the spin
of the hard particles it's applied to. This is a hope, not a result. (Separately, a
formal-verification tool, Lean/Mathlib, was explored as a possible engine for a general-spin
induction step on the Method B/EOM side specifically, and set aside — Mathematica can check
specific low spins one at a time but can't prove a statement for all $s$ at once.) No method, on
the Lagrangian/EOM side or the on-shell side, has actually been chosen yet for the any-spin step:
this is a live, open research direction, not a solved roadmap.

## 3. Status as of 2026-11-08

- **Scalar (Goldstone) sector:** fully worked out and machine-verified — the ambient-space
  Killing vectors, the Lie-derivative form of the DBI boost, the DBI inflaton action and its
  Stueckelberg/Goldstone expansion. This is the solved, closed part of the problem.
- **Spin-1:** redone from scratch under the stricter verification discipline described in §4; the
  redo is drafted and has passed its internal dual-review process, but has not yet been
  executed/promoted into the project's permanent result ledger.
- **Spin-2:** literature-based scaffolding exists from earlier work but has not yet been
  re-audited to the stricter standard established for spin-1; not yet a settled result.
- **Generic spin $s$:** open question — not yet decided whether/how to generalize beyond
  spin-2, pending the spin-1/spin-2 audits actually closing.

## 4. Methodology and tooling

Tensor-calculus and effective-field-theory derivations in a curved, time-dependent background
are exactly the kind of task where an LLM working unscaffolded is failure-prone: a derivation can
read as fluent and confident while quietly getting a sign, an index placement, or which of
several legal forms of a metric applies in a given step wrong. This project hit that directly —
an early attempt at the spin-1 extension carried exactly this kind of convention mismatch, which
slipped through an initial pass and had to be caught and redone from scratch. That failure mode
is the actual reason this workspace is built the way it is, not an afterthought added for show:

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
  - *The Method B toolchain* (§2): `ansatz-basis-enumeration`, `eom-invariance-imposition`,
    `eom-crosscheck` — building, constraining, and cross-checking an equation-of-motion-level
    ansatz with no Lagrangian ever written.
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

The physics work itself is produced through Claude Code sessions: symbolic derivations and
reasoning by the model, heavy tensor-calculus computations machine-verified in Wolfram
Language/Mathematica, written up in LaTeX. Every claim that matters (an invariance statement, a
sign, a parameter relation) is required to have an actual machine-checked derivation behind it —
never just "this looks right."

**The result ledger** is the most recent and most structured layer on top of all this. As of this month, established results are being migrated into a single
JSON ledger, `latex_notes/structure/claims.json`: each entry is one atomic, citable statement
(a precise sentence plus its formula), pointing at the `.tex` note it's stated in and the
Mathematica script + clean log that verifies it, with explicit `depends_on` links to other
entries. A small Python checker validates the ledger's internal consistency (every dependency
resolves, every cited artifact exists, etc.) before anything is promoted into it. Nothing enters
the ledger without the user reading the note and explicitly naming which statements are results.

This ledger design was arrived at independently, then found to have a close public precedent:
**Matias Zaldarriaga's arXiv:2606.30527** ("Universal distance modes from DESI BAO and Type Ia
supernovae"), whose code repo (`github.com/matiaszaldarriaga/desi-w0wa-svd`) — also written
entirely with Claude Code — ships a `claims.yaml` + `figures.yaml` + `logic.yaml` registry and an
HTML dashboard that traces every quoted number in the paper back to the script and data that
produced it, explicitly "to enable systematic verification that every scientific claim traces to
code and data." The DBI project's ledger does the same thing for a different kind of claim: not a
numerical result traced to a Python script and a data file, but a symbolic tensor-calculus
identity or invariance statement traced to a machine-verified Mathematica derivation. If useful
framing for the website: this project is adapting a verifiable-claims research methodology,
already demonstrated publicly for numerical/data-analysis work, to symbolic/analytic theoretical
physics.

One piece Zaldarriaga's repo has that this project doesn't (yet): a `logic.yaml`-style
section-level argument skeleton linking a paper's narrative sections to the claims they rest on.
That naturally belongs to writing the actual paper, which hasn't started yet — it will be added
once that happens.

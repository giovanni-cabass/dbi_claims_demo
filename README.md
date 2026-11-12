# DBI Cosmological Collider

[![CI](https://github.com/giovanni-cabass/dbi_claims_demo/actions/workflows/ci.yml/badge.svg)](https://github.com/giovanni-cabass/dbi_claims_demo/actions/workflows/ci.yml)

*This demo repository — the excerpt, packaging, and tooling you're looking at — was put
together with Claude Code. [`METHODOLOGY.md`](METHODOLOGY.md) covers how the underlying
research itself is produced.*

(Earlier commits were missing the git trailer so GitHub never recognized Claude Code as co-author.)

This repository is a small, self-contained excerpt from Giovanni Cabass's ongoing research
project on inflationary cosmology — constructing the **DBI Cosmological Collider**, the coupled
Goldstone-plus-spinning-field system that imposes the DBI boost symmetry consistently in a
cosmological (FRW/de Sitter) background, not just in flat spacetime. Rather than only describing
the project, it shows one worked, machine-verified result end to end: the physics note, the
Mathematica scripts that verify it, and the result ledger and checking tool that tie each claim to
its evidence.

State of things as of **2026-11-08**.

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
than re-running a spin-by-spin construction forever. One direction being considered: working
directly at the level of on-shell quantities (correlators / Ward identities for the broken DBI
boost generator) rather than through an explicit off-shell Lagrangian or equation of motion built
field by field, in the hope that the resulting constraint turns out to be structural and
spin-blind — in the same spirit as a soft theorem from a spontaneously broken symmetry not caring
about the spin of the hard particles it's applied to. This is a hope, not a result. (Separately, a
formal-verification tool, Lean/Mathlib, was explored as a possible engine for a general-spin
induction step on the Method B/EOM side specifically, and set aside — Mathematica can check
specific low spins one at a time but can't prove a statement for all $s$ at once.) No method, on
the Lagrangian/EOM side or the on-shell side, has actually been chosen yet for the any-spin step:
this is a live, open research direction, not a solved roadmap.

## 3. Status as of 2026-11-08

- **Scalar (Goldstone) sector:** fully worked out and machine-verified by both construction
  methods described in §2 — Method A (the covariant Lagrangian) and Method B (the blind,
  equation-of-motion-first construction) — cross-checked against each other. This is the solved,
  closed part of the problem. This repository's `claims.json` currently holds only the entries
  folded in from note 01, the ledger's one worked example so far; the rest of the scalar sector is
  already verified and not yet folded into the ledger.
- **Spin-1:** Method A redone from scratch under the stricter verification discipline described in
  §4; drafted and has passed its internal dual-review process, but not yet executed/promoted into
  the project's permanent result ledger. Method B has not been extended past the scalar case.
- **Spin-2:** Method A's literature-based scaffolding exists from earlier work but has not yet
  been re-audited to the stricter standard established for spin-1; not yet a settled result.
  Method B has not been extended here either.
- **Generic spin $s$:** open on every front — not yet decided whether/how to extend Method A or
  Method B beyond spin-2, and the on-shell/correlator idea sketched in §2 is a hope, not yet a
  chosen method.

## 4. Methodology and tooling

Tensor-calculus and effective-field-theory derivations in a curved, time-dependent background
are exactly the kind of task where an LLM working unscaffolded is failure-prone: a derivation can
read as fluent and confident while quietly getting a sign, an index placement, or which of
several legal forms of a metric applies in a given step wrong. This project hit that directly —
an early attempt at the spin-1 extension carried exactly this kind of convention mismatch, which
slipped through an initial pass and had to be caught and redone from scratch. That failure mode
is the actual reason this workspace is built the way it is:
project-wide rule files, task-specific skills, narrow-charter subagents, and a dual-adversarial
review discipline — with a second coding tool (Cursor) running its own heavier version of the same
review discipline for the project's longest, most complex tasks. The full inventory for both
tools, and how Cursor's version compares to Claude Code's, is in
[`METHODOLOGY.md`](METHODOLOGY.md).

The physics work itself is produced through Claude Code sessions: symbolic derivations and
reasoning by the model, heavy tensor-calculus computations machine-verified in Wolfram
Language/Mathematica, written up in LaTeX. Every claim that matters (an invariance statement, a
sign, a parameter relation) is required to have an actual machine-checked derivation behind it —
never just "this looks right."

**The result ledger** is the most recent and most structured layer on top of all this. Established
results live in a single JSON ledger, `latex_notes/structure/claims.json`: each entry is one
atomic, citable statement (a precise sentence plus its formula), pointing at the `.tex` note it's
stated in and the Mathematica script + clean log that verifies it, with explicit `depends_on`
links to other entries. A small Python checker (`python_scripts/check_claims.py`) validates the
ledger's internal consistency (every dependency resolves, every cited artifact exists, etc.)
before anything is promoted into it. Nothing enters the ledger without Cabass reading the note
and explicitly naming which statements are results. The rule governing all of this — what counts
as evidence, how an entry gets promoted, the schema — ships with this repository at
`latex_notes/structure/established-results.md`; the mechanical fold procedure itself is at
`latex_notes/structure/README.how_to_fold.txt`.

This ledger design was arrived at independently, then found to have a close public precedent:
**Matias Zaldarriaga's arXiv:2606.30527** ("Universal distance modes from DESI BAO and Type Ia
supernovae"), whose code repo (`github.com/matiaszaldarriaga/desi-w0wa-svd`) — also written
entirely with Claude Code — ships a `claims.yaml` + `figures.yaml` + `logic.yaml` registry and an
HTML dashboard that traces every quoted number in the paper back to the script and data that
produced it, explicitly "to enable systematic verification that every scientific claim traces to
code and data." The DBI project's ledger does the same thing for a different kind of claim: not a
numerical result traced to a Python script and a data file, but a symbolic tensor-calculus
identity or invariance statement traced to a machine-verified Mathematica derivation. This project
adapts a verifiable-claims research methodology, already demonstrated publicly for
numerical/data-analysis work, to symbolic/analytic theoretical physics.

This repository's two generated views (`latex_notes/structure/dependency_graph.md` and
`claim_dashboard.html`) go further than independent convergence: they were built by directly
reading Zaldarriaga's own `scripts/build_dashboard.py` and `structure/dependency_graph.md`, and
adopt several of his design choices outright — labeling each dependency-graph node with a short
description rather than a bare id, a claim-count summary line, and the dashboard's collapsible
per-claim panels, accent-bordered cards, and jump-to-highlight navigation. (Not adopted: his
dashboard renders claims as plain, LaTeX-stripped text rather than typeset math, since his claims
are numerical/data statements rather than tensor-calculus formulas — this project's claims needed
real rendering, so it vendors KaTeX instead.)

One piece Zaldarriaga's repo has that this project doesn't (yet): a `logic.yaml`-style
section-level argument skeleton linking a paper's narrative sections to the claims they rest on.
That naturally belongs to writing the actual paper, which hasn't started yet — it will be added
once that happens.

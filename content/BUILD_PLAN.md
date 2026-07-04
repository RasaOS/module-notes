# `rasa.module.notes` — Specification & Build Plan

**Status:** v0.1.0 = spine + spec + seam + ledger templates. The skills are
the build phase (M-1..M-3 below), deliberately gated.

This is the author-time specification. The installed spine is
`content/notes-rules.md`; this file is the design record behind it.

---

## Why this module exists (and why only this one)

On 2026-07-04 a cross-vertical survey of the RasaOS substrate asked: which
administrative primitives do all the verticals reinvent? Institutional
memory — a **three-tier working → decision → canon promotion pipeline** —
was found reimplemented independently in:

- **domain-writer** — `seed/ledgers/decisions.md` ("the project's
  institutional memory"; fields Category / Decision / Why / Source /
  Promoted-to) with an explicit `open-question → decision → canon` chain
  and a `/promote` skill.
- **domain-code** — `/decision` (ADRs), `/lessons`, `/regret`, and
  `/codify` (promotes conversation-emergent rules up into
  `CLAUDE.md` / `task-rules.md`).
- **this workspace** — working notes → `AUDIT.md` + decision records →
  `canon/` amendments (which additionally route through a canon *task*).

Unlike the other wave-2 candidates (people, audit, calendar, comms,
billing), notes was the **only one that cleared both** the portfolio
synthesis and the adversarial critic, because:

1. **The three source implementations share a *structure*, not just a
   noun** — the three tiers and the promotion discipline are identical
   across them. (Contrast people/audit, whose source instances diverge on
   every load-bearing field.)
2. **Zero kernel dependency** — it's pure git-versioned markdown, the
   `module.tasks` precedent, buildable today.
3. **It's extract-after-proof** — this workspace *is* a live, running
   instance of the promotion pipeline, so the distillation source has
   actually run in production (the exact bar `module.tasks` set and the
   other candidates failed).

## Non-goals (hard boundaries)

- **Not the kernel's similarity-recall memory.** Facts recalled by vector
  match are `module.ingest` `/remember` / `memory_store` territory. This
  module is ordered, human-ratified, provenance-first. See the boundary
  section of `notes-rules.md`.
- **Not a task tracker.** Open *work* is `module.tasks`. Open *questions*
  (undecided rulings) live in tier 1 here, but they are not assignable
  work items.
- **Not five decision types.** The honest verdict was explicit: ship the
  `/note` + `/decide` + `/promote` MVP, not domain-code's full
  decision/postmortem/regret/retro/lesson taxonomy. Those are a project's
  own categories inside tier 2, not separate skills.

---

## Entity model

Three project-owned ledgers + one project-owned seam.

### `notes/WORKING.md` (tier 1)
Dated headings, freeform bullets. No schema — this is the thinking tier.
Rolls stale sections to `notes/archive/<YYYY-MM>.md`.

### `notes/DECISIONS.md` (tier 2) — the load-bearing ledger
Append-only, ordered. One entry per ratified decision:

```
## DEC-007 — Per-element vector indexes over one global index
- **Category:** architecture
- **Date:** 2026-07-01
- **Decision:** Each element gets its own vector index; no shared global index.
- **Why:** tenant isolation is a hard requirement; a shared index leaks
  cross-element retrieval. Cost is N small indexes vs 1 large — acceptable.
- **Promoted-to:** (none yet)
- **Superseded-by:** (none)
```

Rules: never rewrite; supersede by appending a new entry + a `Superseded-by:`
line on the old. `DEC-NNN` monotonic, never reused. Dates absolute.

### canon (tier 3) — project-owned target, named by the seam
Not a ledger this module ships. The seam points at wherever the project
keeps its authoritative layer.

### `.claude/notes-canon.md` (the seam) — the one per-project thing
See "The adapter seam" below.

---

## The adapter seam — `.claude/notes-canon.md`

The crux of the design, mirroring `module.tasks`' done-gate and
`module.ingest`' ingest-gate. It holds the three things that genuinely vary
per vertical:

1. **`canon_target`** — the file(s) a promoted decision lands in
   (`bible/`, `CLAUDE.md`, `canon/…`). Without it, `/promote` hard-stops.
2. **`categories`** — the project's tier-2 decision categories (writer:
   canon|character|plot|voice|…; code: architecture|process|tooling|…;
   default: `general`).
3. **`promotion_criteria`** — optional project overrides of the default
   "questioned-and-held → decision; stable-and-depended-on → canon" rules.
   May encode a hard gate (this workspace's canon promotion requires a
   canon *task* first — the seam is where that rule lives).

Why a seam and not fixed logic: "what counts as canon and where it lives"
is exactly the vertical moat — the same reason `module.people`'s taxonomy
and `module.audit`'s rule-pack are seams. The horizontal core is the
*promotion discipline*; the vertical part is *what you're promoting into*.

**Honest note on the seam paradox** (flagged by the wave-2 critic): pushing
the canon target into the seam is correct, but it means the module's
horizontal core is "the three-tier discipline + ordered append-only
ledgers", not the canon logic. That core is load-bearing *here* (the
discipline is the reinvented thing) in a way it may not be for the deferred
modules — which is precisely why notes ships and they wait.

---

## Skills (the build phase — M-1..M-3)

Four skills, MVP-scoped. Each is a thin driver over the ledgers + seam; the
discipline lives in `notes-rules.md`, not duplicated per skill.

### M-1 — `/note` and `/notes`
- **`/note <text>`** — append a tier-1 working note under today's heading in
  `notes/WORKING.md`. Zero ceremony. No ratification. The fast path.
- **`/notes [working|decisions|search <term>]`** — read/list the ledgers.
  Default: recent working notes + recent decisions. `search` greps both.
  Read-only.

### M-2 — `/decide`
- **`/decide <ruling>`** — promote a thought (or capture a fresh ruling)
  into tier-2 `notes/DECISIONS.md`. MUST collect a **basis** (refuse to
  file without one — "a decision without a basis is a working note") and a
  **category** (from the seam's list). Assigns the next `DEC-NNN`. Stages
  the entry and asks the human to **ratify** before writing (never
  auto-commits). If superseding a prior decision, appends the new entry and
  adds `Superseded-by:` to the old.

### M-3 — `/promote`
- **`/promote DEC-NNN`** — graduate a tier-2 decision to canon. Reads
  `.claude/notes-canon.md`; **hard-stops if the seam is unfilled or has no
  `canon_target`**. Checks the decision against the project's
  `promotion_criteria` (default: stable + depended-on). Stages the edit to
  the canon target + a `Promoted-to:` pointer on the DEC row, and asks the
  human to ratify. Honors any project hard-gate (e.g. "canon needs a task
  first" → refuses and points at the task workflow).

**Style/quality bar:** match `module.ingest`'s SKILL.md files — a crisp
operation list, honest error/hard-stop behavior, no invented plumbing.
Fan-out plan: author `/decide` as the reference skill, then `/note`+`/notes`
and `/promote` in parallel against it, gate each independently (the
four-engineering-modules build pattern).

---

## The gate — when to build the skills

Per the honest wave-2 verdict, hold the skill build until **one real second
consumer** wants it — a domain or orchestrator that adds
`rasa.module.notes` to its `requires.elements[]`. The natural first
consumers:

- **this workspace** (`rasa.tenant.rasaos`) — already runs the pipeline by
  hand; would be dogfooding its own distillation.
- **domain-writer** — already has the richest hand-rolled version; adopting
  the module would prove the seam against a real, divergent second vertical
  (the decisive test: does the spine survive a second consumer without
  warping? If yes, the horizontal thesis holds; if the seam needs
  reshaping, we were distilling an instance).

Building the skills before that second consumer would repeat the exact
premature-abstraction trap that `module.billing` is deferred to avoid.

---

## Version plan

- **v0.1.0 (this)** — spine (`notes-rules.md`) + spec (this file) + seam
  template + ledger templates. No skills. Local, not pushed.
- **v0.2.0** — M-1..M-3 skills authored, once a second consumer declares
  the module. `bin/init` smoke-tested into that consumer. Push then.
- **v1.0.0** — the seam format + install shape locked after the pipeline
  has run through at least two real verticals unchanged.

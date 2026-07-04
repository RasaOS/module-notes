# Notes Rules

The portable institutional-memory spine that `rasa.module.notes` installs
at `.claude/notes-rules.md`. It covers the three tiers of memory, how a
note is promoted from one to the next, the boundary against the kernel's
similarity-recall memory, and the ledger conventions. **Read this file
when capturing a note, recording a decision, promoting to canon, or asking
"why did we decide this?"**

This file is **Element-owned** — it refreshes on upgrade. It deliberately
does **not** decide the one thing that varies per project:

- **Where a promoted decision becomes law** (the project's authoritative /
  canon file), and the project's decision categories + promotion criteria.

That lives in the project-owned **`.claude/notes-canon.md`** (the notes
analogue of the task module's done-gate and the ingest module's
ingest-gate). This file references the seam; it hardcodes none of it. The
`/promote` step **hard-stops** if the seam is unfilled — guessing where a
decision becomes law is the one inference this module refuses to make.

## The three tiers — the whole model

Institutional memory is not one bucket. Every RasaOS vertical that built
it (domain-writer, domain-code, this workspace) independently discovered
the same three tiers, distinguished by **how durable and how ratified** an
entry is:

| Tier | Ledger | What it holds | Durability | Ratified? |
|---|---|---|---|---|
| **1 — working** | `notes/WORKING.md` | meeting/call notes, open threads, half-formed thoughts, "look at this later" | transient; rolls to `notes/archive/` when stale | no — it's thinking, not a commitment |
| **2 — decision** | `notes/DECISIONS.md` | a ruling made "so it isn't re-litigated", with a stated basis | durable; append-only, ordered, never rewritten | yes — a person ratified it |
| **3 — canon** | project-owned (the seam names it) | the project's authoritative layer that all work is gated against | authoritative | yes — the highest bar |

The value is the **promotion discipline between tiers**, not any single
ledger. A thought becomes a decision when it survives being questioned; a
decision becomes canon when it's stable enough that everything else must
conform to it.

```
working note  ──/decide──▶  durable decision  ──/promote──▶  canon
(cheap, transient)          (ratified, ordered)              (authoritative)
```

## The boundary against kernel memory — read this before you reach for the wrong tool

This module and the kernel's semantic memory are **different primitives**,
and conflating them is the known failure mode:

- **This module (`notes`)** = human-authored, git-versioned, **ordered**
  markdown, read **start-to-finish**. Its unit is a *decision with a
  basis*, recalled by a person reading the log. The point is provenance
  and non-relitigation. It answers "**why** did we decide X, and when, and
  on what basis?"
- **Kernel memory** (reached via `rasa.module.ingest` `/remember` +
  `/recall`, or the injected `memory_store` / `memory_search` tools) =
  machine-authored-or-human, **unordered**, recalled by **similarity**.
  Its unit is a *self-contained fact*, recalled by vector match. It answers
  "**what** do we know that's relevant to this query?"

Rule of thumb:

- A ruling you will cite later to stop an argument → **`/decide`** (this
  module).
- A fact you want a future session to surface automatically when relevant
  → **`memory_store`** / module.ingest `/remember`.
- If you're about to `/decide` something with no basis and no stakes, it's
  a working note.
- If you're about to `/remember` a multi-paragraph rationale with a date
  and a "we chose A over B because", it's a decision — put it here.

These play well together (a decision may ALSO be `memory_store`'d so it
surfaces by similarity) but neither replaces the other, and this module
never writes to the kernel — the cross-reference is soft.

## Tier 1 — working notes

Cheap and transient. Capture without ceremony; do not over-structure.

- Append to `notes/WORKING.md` under a dated heading. Meeting notes, call
  notes, "threads not yet pulled", things to check.
- Working notes are **not** commitments. Nothing downstream is gated on
  them. They are the raw material `/decide` promotes from.
- When `notes/WORKING.md` gets long or a month closes, roll the stale
  section to `notes/archive/<YYYY-MM>.md`. Never delete — archive.
- A working note is allowed to be wrong, tentative, or contradictory. That
  is the point of the tier: somewhere to think out loud before ratifying.

## Tier 2 — durable decisions

The project's institutional memory. **Recorded so it isn't re-litigated.**

Every decision entry carries, at minimum:

- **Decision** — the ruling, one line.
- **Why / basis** — the reasoning it rests on (not "because I said so";
  the basis is what lets a future reader re-evaluate it honestly).
- **Category** — from the project's list in `.claude/notes-canon.md`
  (e.g. domain-writer uses canon|character|plot|voice|period|structure|process;
  domain-code uses architecture|process|tooling|convention). A project
  without a list uses `general`.
- **Date** — absolute (`2026-07-04`), never relative.
- **Promoted-to** — optional pointer, filled by `/promote` when the
  decision graduates to canon.

Hard rules for tier 2:

- **Append-only. Ordered. Never rewritten.** A superseded decision is not
  edited or deleted — a *new* decision is appended that supersedes it, and
  the old one gains a `Superseded-by:` line. The log is a chain of custody,
  not a current-state snapshot; the chain is the value.
- **Ratified, not auto-recorded.** The human confirms a decision before it
  lands. Do not silently promote a working note to a decision — surface the
  candidate and let the person ratify it. (This mirrors the substrate-wide
  "never auto-commit; the human commits" convention.)
- **A decision without a basis is a working note.** If you can't state the
  why, it isn't ready for tier 2.

## Tier 3 — canon (via the seam)

Canon is **project-defined** and lives wherever the project keeps its
authoritative layer — that target is the whole reason `.claude/notes-canon.md`
exists. Examples of what "canon" means per vertical:

- domain-writer: the story `bible/` (world facts all drafting is gated
  against).
- domain-code: `CLAUDE.md` / `task-rules.md` (the rules Claude obeys).
- this workspace: the versioned `canon/` documents (Spec, Brand Kit) —
  where promotion additionally requires a canon *task* first.

`/promote` reads the seam to learn (a) the canon file/target and (b) the
project's promotion criteria, then stages the promotion for the human to
ratify. It **never** writes canon on its own authority, and it **hard-stops**
if the seam is unfilled. When a decision is promoted, its tier-2 row gets a
`Promoted-to:` pointer so the chain from thought → ruling → law stays
traversable.

## Promotion criteria (defaults; the seam overrides)

Absent project-specific criteria in the seam, use these:

- **working → decision**: the point has been questioned at least once and
  held; it now constrains future work; a basis can be stated.
- **decision → canon**: the decision has been stable across multiple
  sessions/work-cycles, other decisions now depend on it, and reversing it
  would be expensive. Canon is for what's settled, not what's current.

Promote **up**, slowly. It is cheap to leave a decision in tier 2; it is
expensive to enshrine something in canon that later churns.

## Ledger conventions

- One `notes/WORKING.md`, one `notes/DECISIONS.md`, an `notes/archive/`
  dir. All git-versioned, all project-owned (seeded skip-if-exists).
- Markdown, human-first. Frontmatter/tables are fine but the ledgers must
  read cleanly top-to-bottom to a person — the retrievability is a person
  reading in order, not a query.
- Dates absolute. IDs, if a project wants them, are `DEC-NNN`
  monotonically; never reuse a number.
- Never delete; supersede or archive. The point of the module is that the
  history survives.

## Soft cross-references (degrade gracefully)

This module stands alone, but plays well with siblings when mounted:

- **`rasa.module.ingest` / kernel memory** — the similarity-recall sibling
  (see the boundary section). A durable decision worth surfacing by meaning
  can ALSO be `memory_store`'d. Convention, not dependency; this module
  never calls the kernel.
- **`rasa.module.tasks`** — a decision that came out of a task can note the
  `TASK-NNN`; a project with `tasks/AUDIT.md` may cross-link. Present-if-mounted.
- **`rasa.module.jobs`** — a scheduled periodic retro (review WORKING.md,
  promote what's ready) is a natural `job.toml` when jobs is mounted.

Do **not** harden any of these into a `requires.elements[]` dependency.

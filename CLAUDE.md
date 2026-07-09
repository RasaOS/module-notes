# CLAUDE.md — `rasa.module.notes`

> **Who you are (SA-025).** `rasa.module.notes` — the RasaOS module for institutional-memory notes. Substrate: **RasaOS**; role: **module**. On install `bin/init` renders this into `.claude/rasa-identity.md`; `/whoami` composes the full identity with the project's deployment layer.


Per-repo working contract for Claude sessions opened inside this folder.
Extends `~/.claude/CLAUDE.md` and the workspace `~/rAI/rasa-os/CLAUDE.md`
(the `rasa.tenant.rasaos` tenant's contract); does not override them.

## What you are when you're in this folder

You are working on **`rasa.module.notes`** — a `module`-kind Element: the
institutional-memory workflow (three-tier working → decision → canon
promotion pipeline) as portable git-versioned markdown. Sibling to
`module.tasks` (the adapter-seam origin), the four engineering modules, and
`module.ingest` (which wraps the kernel's *other* memory primitive).

A `module` (canon Spec §6) is "a focused capability that extends a domain or
orchestrator, mountable into one or more parents." Parents pull it via their
own `requires.elements[]`.

## The load-bearing ideas

**1. Three tiers, and the discipline between them is the product.** Working
(cheap, transient, `notes/WORKING.md`) → decision (ratified, append-only,
`notes/DECISIONS.md`) → canon (the project's authoritative layer). The value
is the promotion discipline, not any single ledger. Don't collapse the tiers.

**2. The boundary against kernel memory is load-bearing.** This module is
ordered, human-ratified, provenance-first markdown ("why did we decide X").
The kernel's similarity-recall memory (via `module.ingest` `/remember`,
`memory_store`) is unordered, vector-recalled facts ("what's relevant").
Different primitives. If you find yourself adding vector search or a
recall-by-similarity feature here — **stop**; that's the kernel's job. The
cross-reference is soft.

**3. The notes-canon seam.** The one per-project thing — where canon lives,
the decision categories, the promotion criteria — is the project-owned
`.claude/notes-canon.md` (seeded skip-if-exists). `/promote` hard-stops if
it's unfilled. `content/` references it; it hardcodes none of it.

**4. Append-only, ratified, never rewritten.** Tier-2 decisions supersede
(never edit/delete); the human ratifies before a decision lands (the
substrate-wide "never auto-commit; the human commits" convention). The log
is a chain of custody — the chain is the value.

## Current status — spec, not built

**v0.1.0 = spine + spec + seam + ledger templates. The skills are NOT built
yet** (see `content/BUILD_PLAN.md` M-1..M-3). This is deliberate: the skill
build is gated on a real second consumer declaring the module (the
`module.tasks` extract-after-proof precedent). Do not author the skills
without the user driving that decision.

## Source of truth

- **`~/rAI/rasa-os/canon/`** — authoritative. Spec §6 defines the `module`
  kind; ELEMENT_CONTRACT.md §7 the install policies.
- **`content/notes-rules.md`** — the installed spine (the discipline).
- **`content/BUILD_PLAN.md`** — the spec + the skill contracts + the gate.
- **`rasa.json`** — the formal declaration + install manifest.

## Don'ts

- **You are NOT the template.** If this contract ever describes
  `domain-core` (or any other Element), the template-CLAUDE.md drift class
  is back — flag it.
- **Don't build the kernel's memory here** (vector search, similarity
  recall). Soft-reference `module.ingest`; never harden it into
  `requires.elements[]`.
- **Don't collapse the three tiers** or auto-promote without ratification.
- **Don't author the skills ahead of the gate** without the user driving.
- **Don't `bin/init` this Element into itself.** `content/` is the source.
- **Don't push from the Cowork sandbox.** Local commit + tag only; the user
  pushes from their machine (workspace rule).

## How a version bump works

- **Patch** — wording/template fix. **Minor (→0.2.0)** — the skills land
  (once the gate opens), a new seed file, a new capability. **Major
  (→1.0.0)** — seam format + install shape locked after two real verticals
  run the pipeline unchanged.

Each bump: edit `VERSION` + `rasa.json#version`, write a CHANGELOG entry,
run `bin/check-manifest`, commit + tag `v<version>`. Update
`~/rAI/rasa-os/elements/REGISTRY.md` + `~/rAI/rasa-os/elements/CHANGELOG.md`
(track #2).

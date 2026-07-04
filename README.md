# Rasa · Module · Notes

**Canonical name:** `rasa.module.notes`
**Repo / folder:** `module-notes`
**Kind:** `module` (canon Spec §6)
**Contract:** Element Contract v1.3.0
**Version:** 0.1.0 (spine + spec + seam; skills are the build phase)
**Status:** Local, not pushed. Skill build gated on a real second consumer.

## What this is

The **institutional-memory** module — the three-tier
working-note → durable-decision → canon promotion pipeline, as portable
git-versioned markdown. Human-authored, ordered, ratified: the Element-layer
counterpart to the kernel's similarity-recall memory (which
`rasa.module.ingest` wraps).

Distilled from three independent RasaOS reimplementations of the *same*
pipeline — domain-writer (`decisions.md` → bible), domain-code (`/decision`
+ `/codify` → `CLAUDE.md`), and this workspace (working notes → AUDIT +
decisions → canon). It was the one wave-2 admin-module candidate that
cleared both the portfolio synthesis and the adversarial critic (see
`content/BUILD_PLAN.md`).

## The three tiers

```
working note  ──/decide──▶  durable decision  ──/promote──▶  canon
(cheap, transient)          (ratified, ordered)              (authoritative)
```

The value is the promotion discipline between tiers. Where "canon" lives —
the one thing that varies per vertical — is the project-owned
`.claude/notes-canon.md` seam; `/promote` hard-stops until it's filled.

## Status / scope

- **v0.1.0 (this):** the spine (`content/notes-rules.md`), the spec
  (`content/BUILD_PLAN.md`), the seam template, and the ledger templates.
- **Deferred to v0.2.0:** the `/note`, `/notes`, `/decide`, `/promote`
  skills — held until a real second consumer declares the module in its
  `requires.elements[]` (the `module.tasks` extract-after-proof precedent).

## Boundary (read this)

Not the kernel's semantic memory. Facts recalled by *similarity* are
`module.ingest` `/remember` / `memory_store`. This module is ordered,
human-ratified, provenance-first: it answers "**why** did we decide X",
not "**what** is relevant to this query." The two are soft siblings, not
substitutes.

## See also

- `content/BUILD_PLAN.md` — full spec, skill contracts, the deferral gate.
- `content/notes-rules.md` — the installed spine.
- `~/rAI/rasa-os/elements/module-ingest/` — the sibling wrapping the kernel's
  similarity-recall memory.
- `~/rAI/rasa-os/elements/REGISTRY.md` — the live workspace snapshot.

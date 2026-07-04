# `rasa.module.notes` — content

What this module ships and where it installs. This file is author-time
documentation (not installed into consumer projects).

## The one-liner

The **institutional-memory** module: the three-tier
working-note → durable-decision → canon promotion pipeline, as portable
git-versioned markdown. Human-authored, ordered, ratified — the Element-layer
counterpart to the kernel's similarity-recall memory (which
`rasa.module.ingest` wraps).

## What installs where

| Source | Installs to | Policy | What it is |
|---|---|---|---|
| `content/notes-rules.md` | `.claude/notes-rules.md` | file-replace | The spine — the three tiers, promotion discipline, the kernel-memory boundary. Element-owned; refreshed on upgrade. |
| `seed/notes-canon.md.template` | `.claude/notes-canon.md` | skip-if-exists | **The seam** — where canon lives + categories + promotion criteria. Project-owned; `/promote` hard-stops until filled. |
| `seed/notes/DECISIONS.md.template` | `notes/DECISIONS.md` | skip-if-exists | Tier-2 decision-log ledger. Project-owned; append-only. |
| `seed/notes/WORKING.md.template` | `notes/WORKING.md` | skip-if-exists | Tier-1 working-notes ledger. Project-owned. |
| `seed/rasa.lock.json.template` | `.claude/rasa.lock.json` | init-only-with-sha | Connection-Contract lockfile, SHA-stamped at init. |

Plus `notes/archive/` scaffolded empty (monthly working-note archive).

## What is NOT here yet

The `/note`, `/notes`, `/decide`, `/promote` **skills** — they are the build
phase. See [`BUILD_PLAN.md`](BUILD_PLAN.md) for their contracts and the
extract-after-proof gate that holds them until a real second consumer
declares the module.

## The shape

Toolkit module, `requires.parent_kind: [domain, orchestrator]`. Pure
Element-layer convention — no kernel engine (contrast `module.ingest`, whose
engine is the kernel's DocumentManager). Cross-refs to kernel memory,
`module.tasks`, and `module.jobs` are all soft (present-if-mounted).

## See also

- [`BUILD_PLAN.md`](BUILD_PLAN.md) — the full spec + build plan.
- `content/notes-rules.md` — the installed spine.
- `elements/module-ingest/` — the sibling that wraps the kernel's *other*
  memory primitive; the boundary between them is load-bearing.
- Canon `ELEMENT_CONTRACT.md` §7 — install policies.

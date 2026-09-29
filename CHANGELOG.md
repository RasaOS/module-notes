# CHANGELOG — `rasa.module.notes`

Reverse-chronological. Each entry is a version bump.

---

## 0.2.0 — 2026-09-28 — notes, notebooks and an enforced decision ledger (records-family/1)

**Breaking.** The ledger shape changes from two markdown files to one file per
record. **No migration is needed:** no project has installed 0.1.x (every
`rasa.lock.json` and `rasa.json` on the workspace volume and under the home
directory was searched on 2026-09-28 — none declares or pins this module).

Owner direction: *"we need modules for each of the following… notes, calendar
events, messages, contacts — as much structure and organization as we can
get."* The owner chose to **extend** this module rather than add a separate
notes module, and to build it to the `rasa.module.tasks` v1.0.0 standard.
Built together with `rasa.module.schedule` 0.2.0, `rasa.module.crm` 0.2.0 and
the new `rasa.module.messages` 0.1.0 as one family.

### Added

- **Notes** — `notes/<notebook>/NOTE-nnnn-<slug>.md`: notebooks as
  directories (≤ 3 levels), tags, types, pins, `about` links to any family
  record, `source`, `[[wiki-links]]`, family-wide backlinks, archive/restore,
  and idempotent daily notes (`notes today`).
- **The decision ledger, enforced** — `notes/decisions/DEC-nnnn-<slug>.md`:
  required `## Basis`, declared categories, `sources`, frozen from the moment
  it is recorded (only `updated` / `promoted_to` / `promoted` may change),
  supersession recorded on the newer decision with "superseded" derived.
- **Canon promotion as a recorded act** — `notes canonize` stamps
  `promoted_to` + `promoted`; hard-stops until `canon_target` is declared in
  `notes/notes.config.yml`; never writes canon itself.
- **Two programs** — `.claude/bin/notes` (13 write verbs, 9 read verbs; each
  write is one atomic act under a lock: record + history line + content
  cache) and `.claude/bin/check-notes` (F-01…F-27 family invariants +
  N-01…N-10; `--fix` repairs history drift and never invents a person or a
  date).
- **JSON Schemas** for the note, the decision and the config, installed under
  `.claude/schemas/notes/` and evaluated by the validator.
- **`records.py`** — the records-family/1 core (strict-YAML grammar and
  serializer, schema evaluator, history, content cache, locking, family-wide
  reference resolution), byte-identical across the four family modules.
- **`notes/history.tsv`**, **`notes/notes.config.yml`** (declare to
  constrain: notebooks, types, tags, categories, actors), and the reworked
  `.claude/notes-canon.md` seam (judgement only; its machine half moved into
  the config).
- **Skills** `/note` and `/decide`.
- **Release gate** — `bin/check-manifest` now runs 14 checks: the nine from
  `rasa.module.tasks` plus family lockstep (core + family block against
  `FAMILY`, compared with every sibling on disk), offline (no network or
  process import in shipped code), schema well-formedness, executable bits,
  and the test suite (which includes an install smoke through `bin/init`).
- **Tests** — `tests/test_records_core.py` (family core; identical in all four
  modules; includes a PyYAML agreement check over ~50 adversarial scalars)
  and `tests/test_notes_cli.py` (walkthrough, refusals, every invariant,
  install smoke).

### Removed

- `notes/WORKING.md` and `notes/DECISIONS.md` seeds — replaced by per-record
  files.
- The `/sync`, `/promote` and `/whoami` skills, the kit/ source clone in the
  consumer tree, the `.claude/rasa-identity.md` stamp and the
  `.claude/rasa-deployment.md` seed — on the `rasa.module.tasks` v1.0.0
  precedent: a mounted module must not claim skill names or identity files a
  parent owns, and this module's own promotion verb collided with `/promote`.

### Changed

- The skill-build gate ("hold until a second consumer declares the module")
  was lifted by the owner's direct request, not by a consumer appearing. The
  1.0.0 bar — two real projects running the shape unchanged — still stands.
- Permissions add `shell:exec` (the installed programs are run).

## 0.1.3 — 2026-07-09

### Element identity layer (canon SA-025)

- Added `rasa.identity` ("the RasaOS module for institutional-memory notes"); `bin/init` generates `.claude/rasa-identity.md` from it every install + stamps project-owned `.claude/rasa-deployment.md`; ships `/whoami`; CLAUDE.md "Who you are" header.

## 0.1.2 — 2026-07-09

### Added generic `/sync` + `/promote` + `/kit`-aware `bin/init` (canon SA-024)

- `bin/init` now clones the Element source into `<project>/kit/<element>/`; `/sync` smart-pulls upstream, `/promote` smart-pushes local edits back upstream (both directory-mirror → installed into consumers).

## 0.1.1 — 2026-07-09

### `parent_kind` → `[domain, tenant]` (canon SA-023)

- The `orchestrator` kind was folded into `tenant`; this module now mounts into a tenant or a domain (`requires.parent_kind: ["domain", "tenant"]`, was `["domain", "orchestrator"]`).

## 0.1.0 — 2026-07-04 — INITIAL (spine + spec + seam)

The **institutional-memory** module — the three-tier
working-note → durable-decision → canon promotion pipeline as portable
git-versioned markdown. The Element-layer counterpart to the kernel's
similarity-recall memory (which `module.ingest` wraps).

Distilled from three independent RasaOS reimplementations of the same
pipeline (domain-writer, domain-code, this workspace) during the 2026-07-04
cross-vertical admin-primitive survey. The sole wave-2 admin-module
candidate to clear both the portfolio synthesis and the adversarial critic
(genuinely convergent structure, zero kernel dependency, extract-after-proof).

### Ships

- `content/notes-rules.md` — the spine: three tiers, promotion discipline,
  the kernel-memory boundary, append-only + ratification rules
  (installs `file-replace` → `.claude/notes-rules.md`).
- `content/BUILD_PLAN.md` — the specification: entity model, the four MVP
  skill contracts, the notes-canon seam, the deferral gate.
- `seed/notes-canon.md.template` — **the adapter seam** (project-owned,
  `skip-if-exists` → `.claude/notes-canon.md`): canon target + categories +
  promotion criteria. `/promote` hard-stops until filled.
- `seed/notes/DECISIONS.md.template`, `seed/notes/WORKING.md.template` —
  the tier-2 and tier-1 ledgers (project-owned).
- Toolkit module shape; `requires.parent_kind: [domain, orchestrator]`;
  soft cross-refs to kernel memory / `module.tasks` / `module.jobs`.

### Deliberately NOT shipped (gated)

- The `/note`, `/notes`, `/decide`, `/promote` skills — the build phase
  (BUILD_PLAN M-1..M-3). Held until a real second consumer declares the
  module in `requires.elements[]`, per the `module.tasks` extract-after-proof
  precedent. Building them now would repeat the premature-abstraction trap
  the wave-2 verdict deferred `module.billing` to avoid.

### Scaffold cleanup

Pruned the domain-core fork's install scaffold (output-style enforcement,
`content/SHAPE.md`, `seed/CLAUDE.md.template`, a stray nested worktree) down
to the toolkit-module shape, mirroring `module-ingest`.

### Notes

- `check-manifest` GREEN; `bin/conformance` 41/41.
- Committed + tagged `v0.1.0`; **pushed PUBLIC** to
  [RasaOS/module-notes](https://github.com/RasaOS/module-notes) (2026-07-04;
  remote HEAD == local + visibility verified).

# CHANGELOG — `rasa.module.notes`

Reverse-chronological. Each entry is a version bump.

---

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

- `check-manifest` GREEN.
- Local commit + tag `v0.1.0`. **Not pushed** (workspace rule; the user
  pushes). Not yet registered as a GitHub repo.

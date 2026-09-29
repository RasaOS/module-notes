# content/ — what `rasa.module.notes` installs

Everything under `content/` is Element-owned: refreshed on every upgrade,
never project state. `bin/init` reads `rasa.json` and applies each entry by
its policy; this table mirrors the manifest and must change with it.

| from | to | policy | what |
|---|---|---|---|
| `content/notes-rules.md` | `.claude/notes-rules.md` | file-replace | the law: the records-family/1 conventions + the notes law |
| `content/schemas/` | `.claude/schemas/notes/` | directory-mirror | JSON Schemas: note, decision, config |
| `content/skills/` | `.claude/skills/` | directory-mirror | `/note`, `/decide` |
| `content/bin/` | `.claude/bin/` | directory-mirror | `notes`, `check-notes`, and the `rasa_notes/` package |
| `content/README.md` | — | opt-in | this file (not installed) |
| `content/BUILD_PLAN.md` | — | opt-in | the design record (not installed) |

Project-owned, copied once (`seed/`, never overwritten):

| from | to | policy |
|---|---|---|
| `seed/notes-canon.md.template` | `.claude/notes-canon.md` | skip-if-exists |
| `seed/notes/notes.config.yml.template` | `notes/notes.config.yml` | skip-if-exists |
| `seed/notes/history.tsv.template` | `notes/history.tsv` | skip-if-exists |
| `seed/notes/inbox/.keep` | `notes/inbox/.keep` | skip-if-exists |
| `seed/notes/decisions/.keep` | `notes/decisions/.keep` | skip-if-exists |
| `seed/rasa.lock.json.template` | `.claude/rasa.lock.json` | init-only-with-sha |

`content/bin/rasa_notes/records.py` is the records-family/1 core, byte-identical
in notes, schedule, crm and messages; `content/bin/rasa_notes/FAMILY` records
its hash and the hash of the family block in `notes-rules.md`.

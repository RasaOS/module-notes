# Rasa · Module · Notes

**Canonical name:** `rasa.module.notes`
**Repo / folder:** `module-notes`
**Kind:** `module` (mounts into a `domain` or a `tenant`)
**Contract:** Element Contract v1.3.0 · records-family/1
**Version:** 0.2.0
**Status:** 0.2.0 built on branch `claude/records-family`; 0.1.3 is the published tag on [RasaOS/module-notes](https://github.com/RasaOS/module-notes).

## What this is

Notes and the decision ledger, one record per file:

- **Notes** in **notebooks** (directories, up to three levels), with tags,
  types, pins, links to any record in the family, archive/restore, and one
  daily note per day.
- **Decisions** — rulings recorded so they are not argued again: a basis, a
  category, the notes or threads they came from. Frozen once recorded;
  changed only by being superseded.
- **Canon** — when a decision becomes the project's law, `notes canonize`
  records where. It never writes canon itself, and it refuses until the
  project has declared where canon lives.

```
note  ──notes decide──▶  decision  ──notes canonize──▶  canon
```

## The records family

One of four modules built to one standard — **records-family/1** — with
`rasa.module.schedule` (the calendar), `rasa.module.crm` (the address book,
accounts and sales funnel) and `rasa.module.messages` (email, texts, chat,
calls, voicemail, letters). Same file grammar, same history log, same
validator conventions, and references that resolve across all four when they
are mounted together. The shared core (`records.py`) is byte-identical in
each, and each module's release gate proves it.

## Install

```bash
bin/init /path/to/project
```

Installs `.claude/notes-rules.md`, `.claude/schemas/notes/`, the `/note` and
`/decide` skills, and two programs — `.claude/bin/notes` and
`.claude/bin/check-notes` — plus the project-owned `notes/` ledger and the
`.claude/notes-canon.md` seam. Pure Python 3 standard library: nothing else
to install, no network, no version control needed.

```bash
.claude/bin/notes new "Kickoff with Acme" --in work/clients --tag acme
.claude/bin/notes today
.claude/bin/notes decide "Quote Acme on tiered pricing" --basis "Flat undercharged." --from NOTE-0001
.claude/bin/check-notes
```

## Boundary

Not similarity memory. Facts recalled by meaning belong to the kernel's
memory (`rasa.module.ingest` `/remember`). This module is ordered,
human-ratified and provenance-first: it answers "**why** did we decide X",
not "what is relevant to this query".

## Layout

- `content/notes-rules.md` — the installed law (family conventions + notes law)
- `content/schemas/` — note, decision and config JSON Schemas
- `content/bin/` — the `notes` tool, the `check-notes` validator, the `rasa_notes` package
- `content/skills/` — `/note`, `/decide`
- `seed/` — the project-owned seam, config, history header and notebook placeholders
- `content/BUILD_PLAN.md` — the design record
- `bin/check-manifest` — the release gate (14 checks); `bin/init` — the installer
- `tests/` — the family-core suite (identical in all four modules) and the notes suite

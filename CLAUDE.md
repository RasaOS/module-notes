# CLAUDE.md — `rasa.module.notes`

Per-repo working contract for Claude sessions opened inside this folder.
Extends `~/.claude/CLAUDE.md` and the workspace `CLAUDE.md` at the workspace
root (the folder holding `canon/` and `elements/` — the `rasa.tenant.rasaos`
tenant's contract); does not override them.

> **There is no identity header here, and none is installed.** Up to 0.1.3
> `bin/init` stamped `.claude/rasa-identity.md` and shipped `/whoami`,
> `/sync` and `/promote`. A mounted module is a capability a project pulled
> in; it does not speak for the project, and `directory-mirror` overwrote the
> parent's same-named skills. Removed in 0.2.0 on the `rasa.module.tasks`
> v1.0.0 precedent. Do not reintroduce them.

## What you are when you're in this folder

You are working on **`rasa.module.notes`** 0.2.0 — a `module`-kind Element:
notes in notebooks plus the ratified decision ledger (note → decision →
canon), one record per file. It is one of the four **records-family/1**
modules, built together on 2026-09-28:

| module | records | root |
|---|---|---|
| `rasa.module.notes` (this) | NOTE, DEC | `notes/` |
| `rasa.module.schedule` | EVT | `schedule/` |
| `rasa.module.crm` | CARD, acct-, LEAD | `crm/` |
| `rasa.module.messages` | THR, MSG | `messages/` |

## The load-bearing ideas

1. **The family core is shared, byte for byte.**
   `content/bin/rasa_notes/records.py` and the family block in
   `content/notes-rules.md` (between `<!-- BEGIN records-family/1 -->` and
   `<!-- END … -->`) are identical in all four modules. `FAMILY` records
   their hashes; `bin/check-manifest` check 10 proves this module matches its
   `FAMILY` and that every sibling found on disk carries the same `FAMILY`.
   **Never edit the core or the family block in one module alone.** Change it
   in all four, run `bin/check-manifest --stamp-family` in each, and run each
   gate. `tests/test_records_core.py` is shared the same way.
2. **The directory tells you where; the tool is the only writer.** A
   notebook is a directory; every change goes through `.claude/bin/notes`,
   which writes the record, appends `notes/history.tsv` and refreshes the
   content cache as one act. The validator catches every hand move, hand
   delete and unrecorded edit.
3. **Decisions are frozen.** A decision changes only by being superseded;
   "superseded" is derived, never written onto the old file (F-19, N-05).
4. **One refused inference: where canon lives.** `notes canonize`
   hard-stops until `canon_target` is declared. The tool records promotions;
   it never writes canon.
5. **Not similarity memory.** Vector recall is the kernel's
   (`rasa.module.ingest`). If you find yourself adding embeddings or
   recall-by-meaning here, stop.

## Source of truth

- **`canon/` at the workspace root** — authoritative; ELEMENT_CONTRACT §2
  (the `module` kind), §7 (install policies), §8 (the vocabulary lock).
  Fetch it before citing it.
- **`content/notes-rules.md`** — the installed law; every rule is an
  invariant id or "judgement".
- **`content/schemas/*.schema.json`** — the field law, evaluated by the
  validator.
- **`content/BUILD_PLAN.md`** — the design record and the invariant map.
- **`rasa.json`** — the manifest; must pass `schema/bin/validate`.

## Don'ts

- **Don't open the network, start a process, or touch version control from
  anything under `content/bin/`.** Check 11 fails the gate. Interop is files.
- **Don't let engineering vocabulary into anything that installs.** A firm, a
  clinic and a novelist read these files; check 9 enforces it. Author-time
  docs (`content/BUILD_PLAN.md`, `content/README.md`) are opt-in and exempt.
- **Don't claim paths a parent owns** — no `CLAUDE.md` seed, no identity
  file, no skill outside `note` / `decide`, no kit/ clone.
- **Don't add a field without adding it to the schema, `x-key-order`, the
  rules table and a test.** The schema is the law the validator runs.
- **Don't `bin/init` this Element into itself.** `content/` is the source.
- **Don't push without the owner's go-ahead.** Local branch + commit only.

## How a version bump works

Pre-1.0 (0.x): a minor may change a record shape, but only with a
CHANGELOG entry that says what a ledger must do (or that no ledger exists
yet). From 1.0.0, strict semver as in `rasa.module.tasks`.

1. Edit `VERSION`, `rasa.json#version`, `content/bin/rasa_notes/model.py`
   `VERSION`, and README's `**Version:**` line together.
2. Write the CHANGELOG entry — honest, including what was not done.
3. If `rasa.json` changed, update `content/README.md`'s table.
4. If the change touches `records.py` or the family block: make it in all four
   modules, `bin/check-manifest --stamp-family` in each.
5. `bin/check-manifest` — all 14 checks GREEN, check 3 "canonical validator
   PASS" (point `RASA_SCHEMA_DIR` at a `RasaOS/schema` checkout whose `.venv`
   has `jsonschema`).
6. Commit + tag `v<version>` on a branch; update the workspace
   `elements/REGISTRY.md` and `elements/CHANGELOG.md` (track 2).

# `rasa.module.notes` — design record

Author-time document; not installed (`opt-in`). The installed law is
`content/notes-rules.md`; this file is the *why* behind it.

---

## 1. What changed in 0.2.0, and why

**Owner direction, 2026-09-28:** *"we need modules for each of the following…
notes, calendar events, messages, contacts — we need as much structure and
organization as we can get."* Asked where general notes should go, the owner
chose **extend `module.notes`** over a separate `module.notebook` or renaming
this module to `module.decisions`. Asked how deep, the owner chose the
**`rasa.module.tasks` v1.0.0 standard**: numbered invariants, JSON Schemas,
one record per file, an atomic tool, an append-only history, a validator and
a release gate.

So 0.2.0 does two things:

1. **Tier 1 becomes real notes.** v0.1.x had one `notes/WORKING.md` scratch
   ledger. Now a note is a first-class record in a notebook: titled, tagged,
   pinnable, linkable to any record in the family, archivable, and one daily
   note per day. The working → decision → canon ladder is unchanged — a note
   *is* the working tier.
2. **The decision ledger becomes enforced.** v0.1.x described "append-only,
   never rewritten, superseded not edited" in prose. Now each decision is a
   frozen file (F-19), supersession is a field on the newer decision with
   "superseded" derived (N-05), the basis is required (N-04), and canon
   promotion is a recorded, checked act behind a hard-stop (N-06).

**The extract-after-proof gate.** v0.1.0 held the skills until a real second
consumer declared the module. That gate was lifted by the owner's direct
request, not by a consumer appearing — there is still **no installed
consumer** (every `rasa.lock.json` under the workspace volume and the home
directory was searched on 2026-09-28). What the gate protected against —
distilling one instance into a false abstraction — is now carried by the
v1.0.0 bar below: the shape is not locked until two real projects run it.

## 2. The records family

notes 0.2.0 is one of four modules built together to one standard,
**records-family/1**:

| module | concern | records |
|---|---|---|
| `rasa.module.notes` 0.2.0 | notes + decisions | NOTE, DEC |
| `rasa.module.schedule` 0.2.0 | the calendar (Booking folded into Event) | EVT |
| `rasa.module.crm` 0.2.0 | the address book + accounts + sales funnel | CARD, acct-, LEAD |
| `rasa.module.messages` 0.1.0 | email, texts, chat, calls, voicemail, letters | THR, MSG |

The shared conventions are stated once — the family block in each module's
rules file, identical in all four — and enforced once, by `records.py`,
identical in all four. `bin/check-manifest` proves both against the
`FAMILY` stamp and compares the stamp with every sibling found on disk.

Design choices that apply to all four, and why:

- **One record, one file, frontmatter + body.** Humans read and edit these
  in any editor; the tool never has to own the whole file. The tasks survey
  showed that per-file records with a directory as state stay honest where
  single ledger files drift.
- **A strict subset of YAML.** Any YAML tool reads the files; our parser
  rejects everything outside the subset with a line number. One level of
  structure (a list of flat maps) is allowed — enough for vCard/iCalendar
  multi-valued properties, and no deeper. Every value parses as text; the
  schema says what it must look like, so there is no YAML type guessing.
  `tests/test_records_core.py` proves PyYAML reads what we write for ~50
  adversarial scalars in both block and flow context.
- **JSON Schema as field law.** The schemas are simultaneously the interop
  artifact (any tool can validate a record) and the enforced law (the
  validator evaluates them). Cross-record law lives in code.
- **Ids are the only join key; references are soft and family-wide.** A
  reference into a mounted sibling must resolve; into an unmounted one it is
  merely unverifiable. No module requires another.
- **The history log is the audit trail and the id-retirement ledger.** A
  project with no version control still has a complete record of every
  change and never reissues an id.
- **`updated` is a fact, frozen records are frozen.** A content cache
  detects edits that did not bump `updated`, and any change to a frozen
  record.
- **No network, ever.** These modules hold personal data about other people.
  Interop is files; sending and syncing belong to Connections (SA-031).

## 3. Notes-specific decisions

| decision | why |
|---|---|
| A notebook is a directory; no `notebook:` key | one fact, one home — the filesystem already says where a file is, and moving it is the act of refiling |
| Depth ≤ 3, lower-case slugs | predictable paths across every operating system and editor |
| `decisions/`, `_archive/`, `.state/` reserved | the ledger, the archive and the cache are not notebooks |
| `pinned` is only ever `true` | "to say nothing, omit the key" — `pinned: false` is a second representation of the default |
| Daily notes are ordinary notes titled by date | no second record type; `notes today` is idempotent |
| Decisions are frozen from the moment they are recorded | the ledger's value is the chain of custody; an editable ruling is not a ruling |
| "Superseded" is derived, never written onto the old decision | writing it would edit a frozen record and store one fact twice |
| `canon_target` lives in config, criteria live in the prose seam | the tool must check the target; only a person can judge the criteria |
| The tool records canon promotion but never writes canon | canon is the project's most valuable file; an automated edit to it is the one write this module will not make |
| Similarity recall stays out | the kernel's memory (via `rasa.module.ingest`) is a different primitive; notes is ordered and ratified |

## 4. Invariant map

| id | rule | where |
|---|---|---|
| F-01…F-27 | the family conventions | `records.py`, family block |
| N-01 | a note lives in a well-formed notebook (not the root, not `decisions/`, depth ≤ 3) | `validate.check_note` |
| N-02 | declared notebooks are closed | `validate.check_note` |
| N-03 | decisions live only in `decisions/`, never archived | `validate.check_decision_local` |
| N-04 | `## Basis` present and non-empty | `validate.check_decision_local` |
| N-05 | supersedes resolve, point backwards, never self, one successor, no loop | `validate.check_decision_graph` |
| N-06 | promotion stamped together, inside a declared target, dated sanely | schema `allOf` + `validate.check_decision_local` |
| N-07 | declared categories are required and closed | `validate.check_decision_local` |
| N-08 | `pinned` is only `true` | schema `const` + `validate.check_note` |
| N-09 | one daily note per date | `validate.check_journal` |
| N-10 | a note is not about itself | `validate.check_note` |

## 5. Deferred, deliberately

- **Note templates** (meeting / call / 1:1 skeletons). Useful, but project
  vocabulary; a project can keep them in its own notebook today.
- **Attachments.** Notes link files by path in the body; a managed
  attachment store is not in scope.
- **Encrypted / locked notes.** Needs a key-management answer the substrate
  does not have yet.
- **Migration from 0.1.x ledgers** (`notes/WORKING.md`, `notes/DECISIONS.md`).
  No consumer ever installed 0.1.x, so there is nothing to migrate. If one
  surfaces, the conversion is mechanical: each WORKING section → a note in
  `inbox/`, each DECISIONS entry → a `DEC` file.

## 6. Version plan

- **0.2.0** — this: the full notes + decision ledger to the records-family/1
  standard. Local branch; merge/tag/push on the owner's go-ahead.
- **0.2.x** — fixes from the first real consumer.
- **1.0.0** — the record shapes, the seam and the install layout locked,
  after at least two real projects have run notes unchanged. A shape change
  after that is a major version with a migration tool, as in
  `rasa.module.tasks`.

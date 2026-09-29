# Notes rules — `rasa.module.notes` 0.2.0

The law for everything under `notes/`: notes in notebooks, and the decision
ledger that turns a working note into a ratified decision and a decision into
canon. **Read this file before capturing a note, filing it, linking it,
recording a decision, or asking "why did we decide this?"**

This file is **Element-owned** — it is replaced on upgrade. It deliberately
does not decide the one thing that varies from project to project:

| seam | owner | holds |
|---|---|---|
| `.claude/notes-canon.md` | the project | what canon means here, the promotion criteria, any hard gate (judgement) |
| `notes/notes.config.yml` | the project | the canon targets, the notebook / type / tag / category vocabularies, actors (checked) |

`notes canonize` **hard-stops** until `canon_target` is declared: guessing
where a decision becomes law is the one inference this module refuses to
make.

Two programs, installed at `.claude/bin/`:

- **`notes <verb>`** — the only sanctioned way to change the ledger.
- **`check-notes [--fix]`** — the enforcement. Run it before you call
  anything finished.

<!-- BEGIN records-family/1 -->
## The family conventions — records-family/1

This module is one of four that share one way of keeping records:
`rasa.module.notes` (notes + decisions), `rasa.module.schedule` (the
calendar), `rasa.module.crm` (the address book, accounts, the sales funnel) and
`rasa.module.messages` (every kind of message). This section is **identical
in all four rules files**; each module's own law follows it. The shared code
that enforces it (`records.py`) is identical in all four as well, and each
module's own gate (`bin/check-manifest`) proves both.

Rules marked **F-nn** are checked by the validator under that id. Rules
marked **judgement** are for a person; no machine can settle them.

### One module, one root

Each module owns one directory at the project root — `notes/`, `schedule/`,
`crm/`, `messages/` — and writes nothing outside it except its installed
surface under `.claude/`. Inside a root, `history.tsv`,
`<module>.config.yml`, `.state/` and `_archive/` are reserved.

### One record, one file

- A record is one UTF-8, LF, newline-terminated `.md` file (**F-01**):
  frontmatter between two `---` lines, then a markdown body.
- The filename is `<ID>-<slug>.md` (or exactly `<ID>.md` for a record type
  without a title) (**F-02**). The slug is lower-case words joined by `-`,
  at most 60 characters, and cosmetic: nothing ever joins on it.
- The id prefix says what the record is, and it must belong to this module
  (**F-03**).
- **The title is the H1.** Exactly one `# ` line, and it is the first
  non-blank line of the body (**F-04**). There is no `title:` key.
- **One fact, one home.** A fact is stored twice only when it is immutable
  and machine-written. Anything derivable — backlinks, "superseded", "past",
  "needs reply", an account's contacts — is computed, never stored.

### The frontmatter grammar — a strict subset of YAML

Any YAML tool can read these files; the validator accepts only this subset
and names the line it rejects (**F-05**).

```yaml
---
# comments are whole lines
id: CARD-0042
tags: [family, climbing]
name: {given: Jane, family: Doe}
email:
  - {label: work, value: jane@acme.com, pref: true}
x-source_system: legacy-crm
---
```

- Keys are lower-case (`a-z 0-9 _`); `x-<name>` is the extension namespace,
  kept verbatim and never interpreted. Any other key the record type does not
  define is an error (**F-06**). A key appears once (**F-07**).
- A value is a scalar, a flow list `[a, b]`, a flow map `{k: v}`, or a block
  list of scalars or flow maps (`  - ` two spaces, dash, space). Nothing
  nests deeper. No null, no `~`, no anchors, no multi-line values, no comment
  after a value. **To say nothing, omit the key.**
- Every value is read as text; the record type's JSON Schema says what it
  must look like. The tools write keys in the schema's order and quote a
  value whenever another YAML reader could misread it.

### Ids and references

- Every record has one id, never reused and never renumbered (**F-08**
  unique, **F-09** grammar). Ids are `PREFIX-NNNN` (four digits or more);
  the one exception is the account, keyed `acct-<slug>`.

  | prefix | record | module |
  |---|---|---|
  | `NOTE`, `DEC` | note, decision | notes |
  | `EVT` | event | schedule |
  | `CARD`, `acct-<slug>`, `LEAD` | contact card, account, lead | crm |
  | `THR`, `MSG` | thread, message | messages |
  | `TASK` | task (read, never written) | `rasa.module.tasks` |

- **Ids are the only join key.** In frontmatter, a reference is a bare id
  (`about: [CARD-0042]`). In a body, it is a wiki-link `[[CARD-0042]]` or
  `[[CARD-0042|Jane]]`; `@acct-<slug>` in prose also names an account.
- References resolve across the whole family. A frontmatter reference into a
  mounted module that names no record is an error (**F-10**); a body link
  that names no record is a warning (**F-11**); a reference into a module
  that is not mounted here is unverifiable and only noted (**F-12**). No
  module ever requires another.

### The history log — `<root>/history.tsv`

```
at	id	verb	from	to	actor	note
2026-09-28T14:03:11Z	NOTE-0001	new	-	inbox	chazz
2026-09-28T14:09:40Z	NOTE-0001	move	inbox	work	chazz
```

- Seven tab-separated columns under that exact header (**F-13**); `at` is a
  UTC stamp and never runs backwards (**F-14**).
- `from` and `to` are the record's place (its directory inside the root) or a
  `key=value` status, or `-`.
- Every record on disk was filed by a `new` or `import` line (**F-15**), and
  sits where its last place line says (**F-16**). A filed id whose file is
  gone is reported (**F-17**); its number is never issued again.
- Only the tools append to it. **Never edit it by hand.** `check --fix`
  repairs F-15/F-16 with a `reconcile` line by `unknown`; it never invents
  a person or a date.

### `updated` is a fact

The tools keep a cache of each record's content in `<root>/.state/` (it has
its own `.gitignore`). A record whose content changed while `updated` did
not is an error (**F-18**) — run `<tool> touch <ID>`. Some records are
**frozen** (a ratified decision; a message once sent or received): changing
their content at all is an error (**F-19**). Frozen records are superseded
or followed by a new record, never rewritten.

### Archive, never delete

The tools never delete a record. `archive` moves it under `_archive/` and
`restore` brings it back; records with a lifecycle end in a terminal state
instead. Deleting by hand is detected (**F-17**). **Judgement:** a person
may still choose to erase personal data for a legal or privacy reason — do
it deliberately, outside the tools, and say so in the project's own record.

### Configuration — `<root>/<module>.config.yml`

- Same grammar; `schema: rasa.module.<module>/1` names the ledger format;
  unknown keys and malformed values are errors (**F-20**). A project with no
  config is valid, except for the one command behind the module's hard-stop.
- **Declare to constrain.** Every vocabulary — tags, types, notebooks,
  calendars, groups, stages, channels, labels — follows one rule: absent or
  `[]` means free (only the grammar is checked); a non-empty list is closed,
  and anything undeclared is an error (**F-21**).
- `actors` (declare to constrain) and `default_actor` are common to all four.

### Actors, dates and times

- Every `created_by` and every history actor is a handle
  (`^[a-z0-9][a-z0-9._-]{0,31}$`) or `unknown` (**F-22**). The tools take
  `--by`, else `$RASA_ACTOR`, else `default_actor`, else they refuse —
  attribution is never invented.
- `created` and `updated` are real `YYYY-MM-DD` dates, never in the future,
  and `updated` is never before `created` (**F-23**).
- A moment is RFC 3339 **with an offset** (`2026-09-28T14:00:00-04:00`),
  never a bare local time (**F-24**). A timezone is an IANA name that
  resolves (**F-25**).
- Relative input — `today`, `tomorrow`, `+3d`, `fri 9am` — is resolved when
  it is captured and stored absolute.
- Every other field obeys its record type's JSON Schema, installed under
  `.claude/schemas/<module>/` (**F-26**).
- A `.md` file inside a root that is not a record is listed once and left
  alone (**F-27**).

### The tools

- Two programs per module under `.claude/bin/`: the tool (`notes`,
  `schedule`, `crm`, `messages`) and its validator (`check-notes`, …).
  Pure Python standard library: no network, no version control, nothing to
  install.
- **Every change goes through the tool.** One command validates, writes the
  record atomically, appends the history line and refreshes the cache — one
  act, under a lock. A refused command writes nothing and exits 1; an
  unusable environment exits 2. `--dry-run` shows what would happen;
  `--json` gives machine output.
- The validator exits 0 when there are no errors (warnings allowed). Run it
  before calling anything finished.

### The outside world

These records hold personal data about other people. **No tool in this
family opens a network connection, sends anything, or syncs anything** — each
module's gate refuses to ship one that tries. Moving data in and out is done with files
(`.ics`, `.vcf`, `.eml`, mbox, SMS backup XML). Sending and syncing belong
to Connections (canon task SA-031), not to this family. **Judgement:**
record about people only what the project's seam allows.
<!-- END records-family/1 -->

## 1. What this module keeps

Memory in a project is not one bucket. It comes in three tiers, told apart by
how settled an entry is:

| tier | where | what it holds | settled? |
|---|---|---|---|
| **1 — notes** | `notes/<notebook>/NOTE-….md` | meeting and call notes, ideas, references, the daily journal, half-formed thinking | no — thinking, not a commitment |
| **2 — decisions** | `notes/decisions/DEC-….md` | a ruling made so it is not argued again, with the basis it rests on | yes — a person ratified it; frozen |
| **3 — canon** | wherever `canon_target` says | the project's authoritative layer | yes — the highest bar |

```
note  ──notes decide──▶  decision  ──notes canonize──▶  canon
(cheap, editable)        (ratified, frozen)             (authoritative)
```

The value is the discipline between the tiers. A thought becomes a decision
when it survives being questioned; a decision becomes canon when everything
else must conform to it.

```
notes/
  notes.config.yml       what the project declares
  history.tsv            every change, one line each
  inbox/                 the default notebook
  journal/               daily notes (notes today)
  work/clients/          any notebook, up to three levels deep
  decisions/             the decision ledger — reserved
  _archive/<notebook>/   archived notes, never deleted
```

## 2. Notebooks

- **A notebook is a directory.** A note's notebook is the directory it sits
  in; there is no `notebook:` key. Moving a note between notebooks is
  `notes move`, which moves the file and logs the move.
- Every note lives in a notebook — never at the top of `notes/`, never in
  `decisions/` — and a notebook path is lower-case words joined by `-`, at
  most three levels deep (`work/clients/acme`) (**N-01**).
- `decisions`, `_archive` and `.state` are reserved and cannot be notebooks
  (**N-01**).
- If `notebooks` is declared in the config, a note may live only in a
  declared notebook (**N-02**). Otherwise notebooks appear as you file into
  them.
- `default_notebook` (default `inbox`) is where `notes new` files a note with
  no `--in`; `journal_notebook` (default `journal`) is where `notes today`
  keeps one note per day.

## 3. The note

```yaml
---
id: NOTE-0042
created: 2026-09-28
created_by: chazz
updated: 2026-09-30
type: meeting
tags: [acme, follow-up]
pinned: true
about: [CARD-0007, EVT-0031]
source: https://example.org/brief
---

# Kickoff with Acme

Talked scope with [[CARD-0007|Dana]]. Next step lives in [[TASK-0012]].
```

| key | required | what it is |
|---|---|---|
| `id` | yes | `NOTE-nnnn`, minted by `notes new` |
| `created`, `created_by`, `updated` | yes | bookkeeping; the tools write them |
| `type` | no | what kind of note; declare `types` to constrain (**F-21**) |
| `tags` | no | labels; declare `tags` to constrain (**F-21**) |
| `pinned` | no | only ever `true`; an unpinned note omits the key (**N-08**) |
| `about` | no | family records the note is about; never itself (**N-10**) |
| `source` | no | a URI or a family id — where the note came from |

- The title is the H1; the body is free markdown. Checklists, tables and
  quotes are all fine; a note is allowed to be wrong, tentative or
  contradictory — that is what the tier is for.
- `notes append` adds a timestamped line to an existing note — the fastest
  way to keep a running log.
- **Daily notes.** `notes today` opens today's note in the journal notebook,
  creating it if needed; its title is the date. One per day (**N-09**).

## 4. Links

- Link any family record from a body with `[[ID]]` or `[[ID|label]]`, and
  from the frontmatter with `about:`. Links are checked across every mounted
  family module (**F-10**, **F-11**, **F-12**).
- **Backlinks are never stored** — they are derived. `notes links ID` shows
  what a record links to and everything, family-wide, that links to it.

## 5. The decision ledger

The project's institutional memory. **Recorded so it is not argued again.**

```yaml
---
id: DEC-0007
created: 2026-09-28
created_by: chazz
updated: 2026-09-28
category: pricing
supersedes: [DEC-0003]
sources: [NOTE-0042, THR-0009]
---

# Quote Acme on tiered pricing

## Basis

Flat pricing undercharged the two largest sites; Acme asked for a price
that tracks usage.
```

- The H1 is the ruling, in one line. **`## Basis` is required and not
  empty** (**N-04**): a ruling without a basis is a working note. `notes
  decide` refuses without `--basis`.
- `category` comes from the declared `categories`; when they are declared,
  every decision carries one (**N-07**).
- `sources` names what the decision was promoted from or rests on — notes,
  threads, events, tasks.
- Decisions live only in `notes/decisions/` and are never archived
  (**N-03**).
- **A decision is frozen the moment it is recorded** (**F-19**). Only
  `updated`, `promoted_to` and `promoted` may ever change. To change a
  decision, record a new one that supersedes it: `notes decide "…" --basis
  "…" --supersedes DEC-0003`. The old file is never touched; "superseded" is
  derived from the newer decision. A decision supersedes only older ones,
  never itself, and each decision is superseded at most once (**N-05**).
- **Ratified, not inferred** — *judgement*. A decision lands only after the
  person it binds agrees to it. Surface the candidate, state its basis, and
  let them ratify; `created_by` names who did.
- `notes decisions` prints the ledger in order — the chain of custody from
  the first ruling to the current one. `--all` includes superseded ones.

## 6. Canon

- `canon_target` in the config names the project's authoritative layer: one
  or more files or directories (`CLAUDE.md`, `bible/`, `style-guide.md`).
  **`notes canonize` refuses until it is declared.**
- `notes canonize DEC-nnnn --to <target>[#section]` records that a decision
  became canon: it stamps `promoted_to` and `promoted` (**N-06**: together,
  inside a declared target, never before the decision or in the future).
  A superseded decision cannot be canonized.
- **The tool never writes canon.** It records the promotion; the person makes
  the edit in the canon file — *judgement*, and the part that matters.
- Default promotion criteria, which `.claude/notes-canon.md` may override —
  *judgement*:
  - **note → decision:** the point has been questioned at least once and
    held; it now constrains future work; its basis fits in a sentence.
  - **decision → canon:** stable across several sessions of work, other
    decisions depend on it, and reversing it would be expensive.
- Promote upward slowly. Leaving a decision in tier 2 is cheap; enshrining
  something in canon that later churns is not.

## 7. The boundary against similarity memory

This module and the kernel's semantic memory are different tools, and
confusing them is the known failure:

- **This module** is human-authored, ordered, ratified markdown, read start
  to finish. It answers "**why** did we decide X, when, and on what basis?"
- **Similarity memory** (`rasa.module.ingest` `/remember`, or the kernel's
  `memory_store` / `memory_search`) holds self-contained facts recalled by
  meaning. It answers "**what** do we know that is relevant here?"
- A ruling you will cite to end an argument → `notes decide`. A fact a
  future session should surface automatically → similarity memory. They
  combine well (a decision may also be stored for recall); neither replaces
  the other. This module never calls the kernel and never grows a vector
  index — *judgement*.

## 8. The tool

| verb | does |
|---|---|
| `notes new "Title" [--in NB] [--tag T]… [--type T] [--about REF]… [--source S] [--pin] [--body …]` | file a note |
| `notes today [--day D]` | open or create the daily note |
| `notes append ID "text"` | add a timestamped line |
| `notes move ID --to NB` · `notes rename ID "Title"` | refile · retitle (H1 and file name) |
| `notes tag ID +a -b` · `notes about ID +REF -REF` · `notes pin/unpin ID` | edit tags · links · pin |
| `notes archive ID` · `notes restore ID` | archive (never delete) · bring back |
| `notes touch ID` | record a hand edit (stamps `updated`) |
| `notes decide "Ruling" --basis "…" [--category C] [--from REF]… [--supersedes DEC]` | record a ratified decision |
| `notes canonize DEC [--to TARGET]` | record that a decision became canon |
| `notes list · show · where · search · links · notebooks · tags · decisions · history` | read |
| `notes check [--fix]` | validate (same as `check-notes`) |

Edit a note's body by hand whenever you like, then `notes touch ID`. Every
other change goes through a verb.

## 9. Soft cross-references

This module stands alone and plays well with its neighbours when they are
mounted. None is ever a `requires.elements[]` dependency.

- **`rasa.module.crm`, `rasa.module.schedule`, `rasa.module.messages`** —
  a note is `about` a contact, an event or a thread; a decision's `sources`
  may be a thread or an event. Links resolve when the module is mounted.
- **`rasa.module.tasks`** — a note can link `[[TASK-…]]`; a decision can cite
  the task it came out of.
- **`rasa.module.jobs`** — a scheduled weekly review of `inbox/` (refile,
  archive, decide what is ready) is a natural job.
- **`rasa.module.ingest`** — see §7.

## 10. What no machine will catch

Every invariant is cited at the rule it enforces: F-01…F-27 in the family
conventions above; N-01 N-02 §2 · N-03 N-04 N-05 N-07 §5 · N-06 §6 · N-08
N-09 N-10 §3. These are the ones nobody checks but you:

- whether a decision was really ratified by the person it binds (§5)
- whether its basis is true and sufficient (§5)
- whether a decision is ready to become canon, and whether the canon edit
  was actually made (§6)
- whether something belongs in similarity memory instead (§7)
- whether the inbox is being refiled and the notebooks still make sense (§2)

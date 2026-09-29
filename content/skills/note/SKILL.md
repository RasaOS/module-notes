---
name: note
description: Capture, find, organize and link notes — file a new note into a notebook, open today's daily note, append a running line, move/retitle/tag/pin/archive a note, link it to a contact, event, thread or task, search notes, or show what links to what. Writes go through .claude/bin/notes so the file, the history line and the content cache change as one act. Use for "/note", "take a note", "jot this down", "add to today's journal", "file this under work", "what did I write about Acme", "tag that note", "archive old notes", "what links to NOTE-12". For recording a ratified decision, use /decide.
---

# /note — notes and notebooks

You decide **what** to capture and where it belongs; `.claude/bin/notes`
makes the change. Never write, move or delete a note file by hand — the tool
keeps the history log and the content cache honest, and a hand move or hand
delete is exactly what `check-notes` reports as an error.

The law is `.claude/notes-rules.md`. This skill executes it; if they ever
disagree, the rules win.

## Before the first write in a session

1. Read `notes/notes.config.yml` — the declared notebooks, tags and types (a
   non-empty list is a closed vocabulary) and `default_actor`.
2. Know who is writing: pass `--by <handle>`, or rely on `$RASA_ACTOR` /
   `default_actor`. Never invent a person; if nobody is declared, ask.

## Capturing

```
.claude/bin/notes new "Kickoff with Acme" --in work/clients --tag acme \
    --about CARD-0007 --body "Scope: two sites. Pricing open."
.claude/bin/notes today                    # today's journal note (created if needed)
.claude/bin/notes append NOTE-0042 "Dana will send the site list Friday"
```

- **Pick the notebook deliberately.** If the user doesn't say, use the
  default (`inbox`) and say so; offer to refile later. Don't invent a new
  notebook when an existing one fits — run `notes notebooks` to see them.
- **Titles are one line and specific** ("Call with Dana re site list", not
  "Call"). The title is the H1; there is no title key.
- **Link what the note is about.** People → `CARD-…` (crm), meetings →
  `EVT-…` (schedule), conversations → `THR-…` (messages), work → `TASK-…`.
  Use `--about` for the main subjects and `[[ID]]` inside the body for
  passing mentions. If you don't know the id, look it up
  (`.claude/bin/crm contact find dana`) rather than guessing.
- For long text, write it to a temp file and pass `--body-file`, or pipe it
  with `--stdin`.

## Organizing

```
.claude/bin/notes move NOTE-0042 --to work/clients/acme
.claude/bin/notes rename NOTE-0042 "Acme kickoff — scope and pricing"
.claude/bin/notes tag NOTE-0042 +follow-up -draft
.claude/bin/notes about NOTE-0042 +EVT-0031
.claude/bin/notes pin NOTE-0042            # unpin to reverse
.claude/bin/notes archive NOTE-0042 --note "superseded by the brief"
```

- Archive, never delete. `restore` brings a note back.
- Editing the body: edit the file directly, then run
  `.claude/bin/notes touch NOTE-0042` so `updated` stays true.

## Finding

```
.claude/bin/notes list [--in NB] [--tag T] [--pinned] [--about REF]
.claude/bin/notes search acme pricing
.claude/bin/notes links NOTE-0042          # outgoing + family-wide backlinks
.claude/bin/notes show NOTE-0042
.claude/bin/notes notebooks · tags
```

Add `--json` when you need to process the result. When answering "what did
I note about X", search, read the hits, and answer with the note ids so the
user can open them.

## When a note turns into a decision

If a note records something the user has now **settled** — questioned, held,
and meant to constrain what comes next — offer to record it with `/decide`.
Don't promote it silently: a decision needs the person's ratification and a
stated basis.

## Finish

Run `.claude/bin/check-notes` after a batch of changes. Report what you
filed (ids and notebooks) in one or two lines; don't paste whole notes back
unless asked.

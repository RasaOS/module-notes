---
name: decide
description: Record a ratified decision in the notes decision ledger, supersede an older decision, list the decision log, or record that a decision became canon. Decisions are frozen once recorded — they change only by being superseded. Writes go through .claude/bin/notes. Use for "/decide", "let's record that decision", "we decided X", "log this as a decision", "that replaces the earlier decision", "what have we decided about pricing", "promote DEC-7 to canon", "make that official in CLAUDE.md".
---

# /decide — the decision ledger

A decision is a ruling recorded **so it is not argued again**. It has a
basis, a date and a person who ratified it, and once recorded it is frozen.
The law is `.claude/notes-rules.md` §5–§6.

## Recording a decision

1. **Get ratification.** State the candidate back in one line plus its
   basis, and ask the person it binds to confirm. Never record a decision
   the user has not agreed to — *judgement*, and the reason this ledger is
   trusted.
2. **Check it isn't already decided.** `.claude/bin/notes decisions` lists
   the ones in force. If this replaces one, you will supersede it.
3. **Record it:**

```
.claude/bin/notes decide "Quote Acme on tiered pricing" \
    --basis "Flat pricing undercharged the two largest sites; Acme asked for usage-based." \
    --category pricing --from NOTE-0042 --from THR-0009 --by chazz
```

- The ruling is one line. The basis is the *why* — what a future reader
  needs to re-evaluate it honestly. "Because we said so" is not a basis.
- `--category` is required when the project declares categories (see
  `notes/notes.config.yml`).
- `--from` names what it came out of: notes, threads, events, tasks.
- `--by` is the person who ratified it.

## Changing a decision

Never edit a decision file — it is frozen, and `check-notes` reports any
change (F-19). Record the new ruling and supersede the old one:

```
.claude/bin/notes decide "Quote Acme on flat pricing after all" \
    --basis "Usage data was unavailable; tiered quotes stalled." --supersedes DEC-0007
```

A decision can be superseded only once; supersede the newest one in a chain.

## Promoting to canon

Canon is the project's authoritative layer, named by `canon_target` in
`notes/notes.config.yml`; what counts as ready is in `.claude/notes-canon.md`.

1. If `canon_target` is not declared, **stop**: `notes canonize` will refuse,
   and so do you. Ask the user where decisions become law here and have them
   declare it. Guessing is the one thing this module refuses to do.
2. Read `.claude/notes-canon.md` for the promotion criteria and any hard gate
   (for example "a canon task must exist first"). Check them; if a hard gate
   is unmet, stop and say what is missing.
3. Make the canon edit itself — in the canon file, with the user's approval.
4. Then record it:

```
.claude/bin/notes canonize DEC-0007 --to "CLAUDE.md#pricing"
```

The tool records the promotion; it never writes canon. Both steps are
required: a recorded promotion with no canon edit is a lie, and a canon edit
with no record loses the chain from note to law.

## Reading the log

```
.claude/bin/notes decisions               # in force, in order
.claude/bin/notes decisions --all         # including superseded
.claude/bin/notes decisions --category pricing
.claude/bin/notes show DEC-0007
```

When the user asks "why did we decide X", find the decision, quote its
ruling and basis, and name its id and date.

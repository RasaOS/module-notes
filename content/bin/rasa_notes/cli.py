# -*- coding: utf-8 -*-
"""cli.py — `notes`, the one way to change a notes ledger.

Every write verb is one act under the ledger lock: check preconditions,
write the record atomically, append the history line, refresh the content
cache. A refused command writes nothing (exit 1). The law is
.claude/notes-rules.md; this file executes it and does not redefine it.

Write verbs
  new "Title"            file a note            today         the daily note
  append ID TEXT         add a stamped line     move ID --to NB
  rename ID "Title"      retitle (H1 + slug)    tag ID +a -b
  pin ID / unpin ID      about ID +REF -REF     archive ID / restore ID
  touch ID               record a hand edit     decide "Ruling" --basis ...
  canonize DEC --to T    record that a decision became canon
Read verbs
  list  show  search  links  notebooks  tags  decisions  history  where  check
"""

import argparse
import datetime as _dt
import os
import sys
from collections import OrderedDict

from . import model as M
from . import records as R
from . import validate as V


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _out(a, human, data):
    if getattr(a, "json", False):
        R.emit_json(data)
    else:
        sys.stdout.write(human if human.endswith("\n") else human + "\n")


def _title(text):
    t = (text or "").strip()
    if not t:
        raise R.Refusal("a title cannot be empty")
    if "\n" in t:
        raise R.Refusal("a title is one line")
    return t


def _check_tags(ctx, tags):
    allowed = ctx.declared("tags")
    for t in tags:
        if not R.RX_SLUG.match(t):
            raise R.Refusal("tag '%s' must be a slug (lower-case words joined by '-')" % t)
        if allowed is not None and t not in allowed:
            raise R.Refusal("tag '%s' is not declared (declared: %s)" % (t, ", ".join(allowed)))
    return tags


def _check_refs(ctx, refs, what="about"):
    index = None
    mounted = R.mounted_modules(ctx.project)
    for ref in refs:
        if not R.is_family_ref(ref):
            raise R.Refusal("'%s' is not a family id (NOTE-0001, CARD-0001, EVT-0001, acct-x, "
                            "THR-0001, TASK-...)" % ref)
        if R.ref_module(ref) in mounted:
            index = index if index is not None else R.family_index(ctx.project)
            if ref not in index:
                raise R.Refusal("%s: %s names a record that does not exist" % (what, ref))
    return refs


def _bump(fm):
    fm["updated"] = R.today().isoformat()
    return fm


def _note_path(ctx, nb, rid, title):
    return ctx.abs("%s/%s-%s.md" % (nb, rid, R.slugify(title)))


def _require_note(rec):
    if rec.prefix != "NOTE":
        raise R.Refusal("%s is a decision; decisions are frozen and change only by being "
                        "superseded (%s decide ... --supersedes %s)" % (rec.id, M.CLI, rec.id))


def _rewrite(ctx, rec, fm, body=None, dry=False):
    schema = ctx.schema_for(rec)
    if dry:
        return R.render_record(fm, rec.body if body is None else body, schema, rec.info)
    text = ctx.write(rec.path, fm, rec.body if body is None else body, schema, rec.info)
    ctx.refresh_digest(rec)
    return text


# ---------------------------------------------------------------------------
# write verbs
# ---------------------------------------------------------------------------

def cmd_new(ctx, a):
    ctx.require_root()
    cfg = ctx.usable_config()
    actor = R.resolve_actor(a.by, cfg)
    title = _title(a.title)
    nb = ctx.check_notebook(a.into or ctx.default_notebook)
    tags = _check_tags(ctx, a.tag or [])
    if a.type:
        types = ctx.declared("types")
        if not R.RX_SLUG.match(a.type) or (types is not None and a.type not in types):
            raise R.Refusal("type '%s' is not %s" % (a.type, "declared (%s)" % ", ".join(types)
                                                     if types else "a slug"))
    about = _check_refs(ctx, a.about or [])
    if a.source and not (R.FORMATS["uri"](a.source) or R.is_family_ref(a.source)):
        raise R.Refusal("--source must be a URI or a family id")
    text = R.read_text_arg(a.body, a.body_file, a.stdin)
    with ctx.lock():
        rows = ctx.history()
        records, _ = ctx.scan()
        rid = R.format_id("NOTE", R.next_number("NOTE", [r.id for r in records if r.id], rows))
        today = R.today().isoformat()
        fm = OrderedDict([("id", rid), ("created", today), ("created_by", actor),
                          ("updated", today)])
        if a.type:
            fm["type"] = a.type
        if tags:
            fm["tags"] = list(OrderedDict.fromkeys(tags))
        if a.pin:
            fm["pinned"] = True
        if about:
            fm["about"] = list(OrderedDict.fromkeys(about))
        if a.source:
            fm["source"] = a.source
        path = _note_path(ctx, nb, rid, title)
        body = R.new_body(title, text)
        if a.dry_run:
            _out(a, "would create %s\n%s" % (R.rel_posix(path, ctx.project),
                                             R.render_record(fm, body, ctx.schemas["note"])),
                 {"dry_run": True, "id": rid, "path": R.rel_posix(path, ctx.project)})
            return 0
        ctx.write(path, fm, body, ctx.schemas["note"])
        ctx.log([(rid, "new", "-", nb, actor, "")])
        ctx.refresh_digest(path, R.rel_posix(path, ctx.root))
    _out(a, "%s  %s" % (rid, R.rel_posix(path, ctx.project)),
         {"id": rid, "path": R.rel_posix(path, ctx.project)})
    return 0


def cmd_today(ctx, a):
    """The daily note for today (idempotent): notes/<journal>/NOTE-nnnn-YYYY-MM-DD.md."""
    ctx.require_root()
    day = R.resolve_day(a.day or "today").isoformat()
    nb = ctx.journal_notebook
    records, _ = ctx.scan()
    for r in records:
        if r.prefix == "NOTE" and not r.archived and M.Ctx.notebook_of(r) == nb and r.h1 == day:
            _out(a, "%s  %s" % (r.id, ctx.rel_of(r)), {"id": r.id, "path": ctx.rel_of(r),
                                                       "created": False})
            return 0
    ns = argparse.Namespace(title=day, into=nb, tag=a.tag, type=None, about=None, source=None,
                            pin=False, body=None, body_file=None, stdin=False, by=a.by,
                            dry_run=a.dry_run, json=a.json)
    return cmd_new(ctx, ns)


def cmd_append(ctx, a):
    ctx.require_root()
    actor = R.resolve_actor(a.by, ctx.usable_config())
    text = R.read_text_arg(a.text, a.body_file, a.stdin)
    if not text or not text.strip():
        raise R.Refusal("nothing to append")
    with ctx.lock():
        rec = ctx.find(a.id)
        _require_note(rec)
        if rec.archived:
            raise R.Refusal("%s is archived; restore it first" % rec.id)
        now = R.now_utc().astimezone()
        stamp = now.strftime("%Y-%m-%d %H:%M")
        lines = text.strip().split("\n")
        chunk = "- **%s** %s" % (stamp, lines[0]) + "".join("\n  " + l for l in lines[1:])
        body = rec.body.rstrip("\n") + "\n\n" + chunk + "\n"
        fm = _bump(OrderedDict(rec.fm))
        if a.dry_run:
            _out(a, _rewrite(ctx, rec, fm, body, dry=True), {"dry_run": True, "id": rec.id})
            return 0
        _rewrite(ctx, rec, fm, body)
        ctx.log([(rec.id, "append", "-", "-", actor, "")])
    _out(a, "%s  appended" % rec.id, {"id": rec.id, "appended": True})
    return 0


def cmd_move(ctx, a):
    ctx.require_root()
    actor = R.resolve_actor(a.by, ctx.usable_config())
    nb = ctx.check_notebook(a.to)
    with ctx.lock():
        rec = ctx.find(a.id)
        _require_note(rec)
        if rec.archived:
            raise R.Refusal("%s is archived; restore it first" % rec.id)
        old = rec.dir
        if old == nb:
            raise R.Refusal("%s is already in %s" % (rec.id, nb))
        dst = ctx.abs("%s/%s" % (nb, rec.name))
        if a.dry_run:
            _out(a, "would move %s: %s -> %s" % (rec.id, old, nb), {"dry_run": True})
            return 0
        R.move_path(rec.path, dst)
        ctx.log([(rec.id, "move", R.place_token(old), nb, actor, "")])
        R.prune_empty_dirs(os.path.dirname(rec.path), ctx.root)
    _out(a, "%s  %s -> %s" % (rec.id, old, nb), {"id": rec.id, "from": old, "to": nb})
    return 0


def cmd_rename(ctx, a):
    ctx.require_root()
    actor = R.resolve_actor(a.by, ctx.usable_config())
    title = _title(a.title)
    with ctx.lock():
        rec = ctx.find(a.id)
        _require_note(rec)
        if rec.h1 is None:
            raise R.Refusal("%s has no H1 to rename; run %s" % (rec.id, M.CHECK))
        lines = rec.body.split("\n")
        idx = rec.h1_lineno - rec.body_lineno
        old_title = lines[idx][2:].strip()
        lines[idx] = "# " + title
        body = "\n".join(lines)
        fm = _bump(OrderedDict(rec.fm))
        new_name = "%s-%s.md" % (rec.id, R.slugify(title))
        dst = os.path.join(os.path.dirname(rec.path), new_name)
        if a.dry_run:
            _out(a, "would retitle %s: %r -> %r (%s)" % (rec.id, old_title, title, new_name),
                 {"dry_run": True})
            return 0
        _rewrite(ctx, rec, fm, body)
        if dst != rec.path:
            R.move_path(rec.path, dst)
        ctx.log([(rec.id, "rename", "-", "-", actor, old_title + " -> " + title)])
    _out(a, "%s  %s" % (rec.id, title), {"id": rec.id, "title": title})
    return 0


def take_flags(a, tokens):
    """Pull --by/--dry-run/--json/--root out of a REMAINDER list, so '+a -b --by x' works."""
    rest, i = [], 0
    while i < len(tokens):
        t = tokens[i]
        if t in ("--by", "--root") and i + 1 < len(tokens):
            setattr(a, t[2:], tokens[i + 1])
            i += 2
            continue
        if t == "--dry-run":
            a.dry_run = True
        elif t == "--json":
            a.json = True
        elif t.startswith("--"):
            raise R.Refusal("unknown option %s" % t)
        else:
            rest.append(t)
        i += 1
    if not rest:
        raise R.Refusal("give at least one change: +add -remove")
    return rest


def _edit_list_field(ctx, a, key, validate, verb):
    a.changes = take_flags(a, a.changes)
    ctx.require_root()
    actor = R.resolve_actor(a.by, ctx.usable_config())
    add, rem = R.split_edits(a.changes)
    validate(add)
    with ctx.lock():
        rec = ctx.find(a.id)
        _require_note(rec)
        cur = list(rec.fm.get(key) or []) if isinstance(rec.fm.get(key), list) else []
        missing = [r for r in rem if r not in cur]
        if missing:
            raise R.Refusal("%s has no %s %s" % (rec.id, key, ", ".join(missing)))
        new = [v for v in cur if v not in rem] + [v for v in add if v not in cur]
        if new == cur:
            raise R.Refusal("nothing changes")
        fm = OrderedDict(rec.fm)
        if new:
            fm[key] = new
        else:
            fm.pop(key, None)
        _bump(fm)
        if a.dry_run:
            _out(a, _rewrite(ctx, rec, fm, dry=True), {"dry_run": True})
            return 0
        _rewrite(ctx, rec, fm)
        ctx.log([(rec.id, verb, "-", "-", actor, " ".join(a.changes))])
    _out(a, "%s  %s: %s" % (rec.id, key, ", ".join(new) or "(none)"), {"id": rec.id, key: new})
    return 0


def cmd_tag(ctx, a):
    return _edit_list_field(ctx, a, "tags", lambda add: _check_tags(ctx, add), "tag")


def cmd_about(ctx, a):
    return _edit_list_field(ctx, a, "about", lambda add: _check_refs(ctx, add), "about")


def cmd_pin(ctx, a, on=True):
    ctx.require_root()
    actor = R.resolve_actor(a.by, ctx.usable_config())
    with ctx.lock():
        rec = ctx.find(a.id)
        _require_note(rec)
        pinned = rec.fm.get("pinned") == "true"
        if pinned == on and rec.fm.get("pinned") != "false":
            raise R.Refusal("%s is already %s" % (rec.id, "pinned" if on else "unpinned"))
        fm = OrderedDict(rec.fm)
        if on:
            fm["pinned"] = True
        else:
            fm.pop("pinned", None)
        _bump(fm)
        if a.dry_run:
            _out(a, _rewrite(ctx, rec, fm, dry=True), {"dry_run": True})
            return 0
        _rewrite(ctx, rec, fm)
        ctx.log([(rec.id, "pin" if on else "unpin", "-", "-", actor, "")])
    _out(a, "%s  %s" % (rec.id, "pinned" if on else "unpinned"), {"id": rec.id, "pinned": on})
    return 0


def cmd_archive(ctx, a, restore=False):
    ctx.require_root()
    actor = R.resolve_actor(a.by, ctx.usable_config())
    with ctx.lock():
        rec = ctx.find(a.id)
        _require_note(rec)
        if restore != rec.archived:
            raise R.Refusal("%s is %s" % (rec.id, "not archived" if restore else "already archived"))
        nb = M.Ctx.notebook_of(rec)
        if restore:
            ctx.check_notebook(nb)
            dst_dir = nb
        else:
            dst_dir = "%s/%s" % (R.ARCHIVE_DIR, nb)
        dst = ctx.abs("%s/%s" % (dst_dir, rec.name))
        if a.dry_run:
            _out(a, "would %s %s: %s -> %s" % ("restore" if restore else "archive", rec.id,
                                                rec.dir, dst_dir), {"dry_run": True})
            return 0
        R.move_path(rec.path, dst)
        ctx.log([(rec.id, "restore" if restore else "archive", rec.dir, dst_dir, actor,
                  a.note or "")])
        R.prune_empty_dirs(os.path.dirname(rec.path), ctx.root)
    _out(a, "%s  %s -> %s" % (rec.id, rec.dir, dst_dir), {"id": rec.id, "to": dst_dir})
    return 0


def cmd_touch(ctx, a):
    ctx.require_root()
    actor = R.resolve_actor(a.by, ctx.usable_config())
    with ctx.lock():
        rec = ctx.find(a.id)
        schema = ctx.schema_for(rec)
        errs = R.schema_errors(schema, rec.fm) if rec.parsed else [("F-05", "", "unparseable")]
        if errs:
            raise R.Refusal("%s does not validate (%s %s); fix it first, then touch" % (
                rec.id, errs[0][1], errs[0][2]))
        fm = _bump(OrderedDict(rec.fm))
        if a.dry_run:
            _out(a, "would stamp %s updated=%s" % (rec.id, fm["updated"]), {"dry_run": True})
            return 0
        # Touch keeps the hand edit byte-for-byte: only the updated line changes.
        lines = rec.text.split("\n")
        ln = rec.line_of("updated")
        lines[ln - 1] = "updated: %s" % fm["updated"]
        R.atomic_write(rec.path, "\n".join(lines))
        ctx.refresh_digest(rec)
        ctx.log([(rec.id, "touch", "-", "-", actor, a.note or "")])
    _out(a, "%s  updated %s" % (rec.id, fm["updated"]), {"id": rec.id, "updated": fm["updated"]})
    return 0


def cmd_decide(ctx, a):
    ctx.require_root()
    cfg = ctx.usable_config()
    actor = R.resolve_actor(a.by, cfg)
    ruling = _title(a.ruling)
    basis = R.read_text_arg(a.basis, a.basis_file, False)
    if not basis or not basis.strip():
        raise R.Refusal("a decision needs --basis: what it rests on. A ruling without a basis "
                        "is a working note (notes new)")
    cats = ctx.declared("categories")
    if cats is not None and not a.category:
        raise R.Refusal("this project declares decision categories; pass --category (%s)"
                        % ", ".join(cats))
    if a.category and (not R.RX_SLUG.match(a.category) or
                       (cats is not None and a.category not in cats)):
        raise R.Refusal("category '%s' is not %s" % (a.category, "declared (%s)" % ", ".join(cats)
                                                     if cats else "a slug"))
    sources = _check_refs(ctx, a.source or [], "--from")
    with ctx.lock():
        rows = ctx.history()
        records, _ = ctx.scan()
        decs = [r for r in records if r.prefix == "DEC"]
        sup = list(OrderedDict.fromkeys(a.supersedes or []))
        for old in sup:
            if not any(d.id == old for d in decs):
                raise R.Refusal("--supersedes %s: no such decision" % old)
            for d in decs:
                if isinstance(d.fm.get("supersedes"), list) and old in d.fm["supersedes"]:
                    raise R.Refusal("%s is already superseded by %s; supersede that one instead"
                                    % (old, d.id))
        rid = R.format_id("DEC", R.next_number("DEC", [r.id for r in records if r.id], rows))
        today = R.today().isoformat()
        fm = OrderedDict([("id", rid), ("created", today), ("created_by", actor),
                          ("updated", today)])
        if a.category:
            fm["category"] = a.category
        if sup:
            fm["supersedes"] = sup
        if sources:
            fm["sources"] = list(OrderedDict.fromkeys(sources))
        body = "\n# %s\n\n## Basis\n\n%s\n" % (ruling, basis.strip())
        if a.context:
            body += "\n## Context\n\n%s\n" % a.context.strip()
        path = ctx.abs("%s/%s-%s.md" % (M.DECISIONS_DIR, rid, R.slugify(ruling)))
        if a.dry_run:
            _out(a, "would record %s\n%s" % (R.rel_posix(path, ctx.project),
                                             R.render_record(fm, body, ctx.schemas["decision"])),
                 {"dry_run": True, "id": rid})
            return 0
        ctx.write(path, fm, body, ctx.schemas["decision"])
        note = ("supersedes " + " ".join(sup)) if sup else ""
        ctx.log([(rid, "new", "-", M.DECISIONS_DIR, actor, note)])
        ctx.refresh_digest(path, R.rel_posix(path, ctx.root))
    _out(a, "%s  %s" % (rid, R.rel_posix(path, ctx.project)),
         {"id": rid, "path": R.rel_posix(path, ctx.project), "supersedes": sup})
    return 0


def cmd_canonize(ctx, a):
    ctx.require_root()
    cfg = ctx.usable_config()
    actor = R.resolve_actor(a.by, cfg)
    targets = ctx.declared("canon_target")
    if targets is None:
        raise R.Refusal("HARD-STOP: this project has not declared where a decision becomes law. "
                        "Set canon_target in %s (see .claude/notes-canon.md). Guessing it is the "
                        "one inference this module refuses to make." % ctx.rel_root(M.CONFIG_NAME))
    with ctx.lock():
        rec = ctx.find(a.id)
        if rec.prefix != "DEC":
            raise R.Refusal("%s is not a decision; only a decision becomes canon (%s decide ...)"
                            % (rec.id, M.CLI))
        records, _ = ctx.scan()
        status = M.decision_status(rec, [r for r in records if r.prefix == "DEC"])
        if status.startswith("superseded"):
            raise R.Refusal("%s is %s; canonize the decision in force" % (rec.id, status))
        if "promoted_to" in rec.fm:
            raise R.Refusal("%s is already canon (%s on %s)" % (rec.id, rec.fm.get("promoted_to"),
                                                               rec.fm.get("promoted")))
        target = a.to
        if not target:
            if len(targets) != 1:
                raise R.Refusal("several canon targets are declared (%s); pass --to"
                                % ", ".join(targets))
            target = targets[0]
        if not any(target == t or target.startswith(t.rstrip("/") + "/") or target.startswith(t + "#")
                   for t in targets):
            raise R.Refusal("'%s' is not inside a declared canon_target (%s)" % (target,
                                                                                ", ".join(targets)))
        fm = OrderedDict(rec.fm)
        fm["promoted_to"] = target
        fm["promoted"] = R.today().isoformat()
        _bump(fm)
        if a.dry_run:
            _out(a, _rewrite(ctx, rec, fm, dry=True), {"dry_run": True})
            return 0
        _rewrite(ctx, rec, fm)
        ctx.log([(rec.id, "canonize", "-", "-", actor, target)])
    _out(a, "%s  recorded as canon in %s  (this tool never writes canon: the edit in %s is "
         "yours, and must match)" % (rec.id, target, target), {"id": rec.id, "promoted_to": target})
    return 0


# ---------------------------------------------------------------------------
# read verbs
# ---------------------------------------------------------------------------

def _row(rec):
    return [rec.id, M.Ctx.notebook_of(rec) or "-", ("* " if rec.fm.get("pinned") == "true" else "")
            + (rec.h1 or "(no title)"), ",".join(rec.fm.get("tags") or []) if
            isinstance(rec.fm.get("tags"), list) else "", rec.fm.get("updated") or ""]


def cmd_list(ctx, a):
    ctx.require_root()
    records, _ = ctx.scan()
    notes = [r for r in records if r.prefix == "NOTE" and r.parsed]
    if a.archived:
        notes = [r for r in notes if r.archived]
    elif not a.all:
        notes = [r for r in notes if not r.archived]
    if a.into:
        nb = a.into.strip("/")
        notes = [r for r in notes if M.Ctx.notebook_of(r) == nb or
                 M.Ctx.notebook_of(r).startswith(nb + "/")]
    if a.tag:
        notes = [r for r in notes if isinstance(r.fm.get("tags"), list) and
                 all(t in r.fm["tags"] for t in a.tag)]
    if a.type:
        notes = [r for r in notes if r.fm.get("type") == a.type]
    if a.pinned:
        notes = [r for r in notes if r.fm.get("pinned") == "true"]
    if a.about:
        notes = [r for r in notes if isinstance(r.fm.get("about"), list) and a.about in r.fm["about"]]
    notes.sort(key=lambda r: r.fm.get("updated") or "", reverse=True)
    notes.sort(key=lambda r: r.fm.get("pinned") != "true")
    if a.json:
        R.emit_json([M.summary(r) for r in notes])
        return 0
    if not notes:
        print("(no notes)")
        return 0
    R.table([_row(r) for r in notes], ["id", "notebook", "title", "tags", "updated"])
    return 0


def cmd_show(ctx, a):
    ctx.require_root()
    rec = ctx.find(a.id)
    if a.json:
        d = M.summary(rec)
        d["body"] = rec.body
        R.emit_json(d)
        return 0
    sys.stdout.write("%s\n\n%s" % (ctx.rel_of(rec), rec.text))
    return 0


def cmd_where(ctx, a):
    ctx.require_root()
    rec = ctx.find(a.id)
    _out(a, ctx.rel_of(rec), {"id": rec.id, "path": ctx.rel_of(rec)})
    return 0


def cmd_search(ctx, a):
    ctx.require_root()
    q = " ".join(a.text).lower()
    if not q.strip():
        raise R.Refusal("search for what?")
    records, _ = ctx.scan()
    hits = []
    for r in records:
        if not r.parsed or (r.archived and not a.all):
            continue
        if a.into and not (M.Ctx.notebook_of(r) + "/").startswith(a.into.strip("/") + "/"):
            continue
        hay_lines = r.body.split("\n")
        tags = " ".join(r.fm.get("tags") or []) if isinstance(r.fm.get("tags"), list) else ""
        snippet = None
        if q in (r.h1 or "").lower() or q in tags.lower():
            snippet = r.h1 or ""
        for line in hay_lines:
            if q in line.lower():
                snippet = snippet or line.strip()
                break
        if snippet is not None:
            hits.append((r, snippet))
    if a.json:
        R.emit_json([OrderedDict([("id", r.id), ("path", ctx.rel_of(r)), ("title", r.h1),
                                  ("match", s)]) for r, s in hits])
        return 0
    if not hits:
        print("(nothing matches %r)" % q)
        return 0
    R.table([[r.id, M.Ctx.notebook_of(r) or r.dir, r.h1 or "", s[:70]] for r, s in hits],
            ["id", "where", "title", "match"])
    return 0


def cmd_links(ctx, a):
    ctx.require_root()
    rec = ctx.find(a.id)
    schema = ctx.schema_for(rec)
    out_refs = [(k, ref) for k, ref in R.frontmatter_refs(rec, schema)] + \
        [("body", ref) for ref, _ in R.body_refs(rec)]
    index = R.family_index(ctx.project)
    back = R.find_backlinks(ctx.project, rec.id, exclude_path=rec.path)
    if a.json:
        R.emit_json(OrderedDict([
            ("id", rec.id),
            ("outgoing", [OrderedDict([("via", k), ("ref", r),
                                       ("path", index.get(r, {}).get("path"))]) for k, r in out_refs]),
            ("backlinks", [OrderedDict([("module", m), ("path", p), ("line", ln)])
                           for m, p, ln, _ in back])]))
        return 0
    print("%s — %s" % (rec.id, rec.h1 or ""))
    print("\noutgoing:")
    for k, r in out_refs or []:
        print("  %-10s %-14s %s" % (k, r, index.get(r, {}).get("path", "(unresolved)")))
    if not out_refs:
        print("  (none)")
    print("\nbacklinks:")
    for m, p, ln, line in back:
        print("  %s:%d  %s" % (p, ln, line[:80]))
    if not back:
        print("  (none)")
    return 0


def cmd_notebooks(ctx, a):
    ctx.require_root()
    records, _ = ctx.scan()
    counts = OrderedDict()
    for nb in (ctx.declared("notebooks") or []):
        counts[nb] = [0, 0]
    for dirpath, dirnames, _ in os.walk(ctx.root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        rel = R.rel_posix(dirpath, ctx.root)
        if rel == "." or rel.split("/")[0] in M.RESERVED_TOP:
            continue
        counts.setdefault(rel, [0, 0])
    for r in records:
        if r.prefix != "NOTE":
            continue
        nb = M.Ctx.notebook_of(r)
        counts.setdefault(nb, [0, 0])[1 if r.archived else 0] += 1
    rows = sorted(counts.items())
    if a.json:
        R.emit_json([OrderedDict([("notebook", k), ("notes", v[0]), ("archived", v[1])])
                     for k, v in rows])
        return 0
    R.table([[("  " * k.count("/")) + k.split("/")[-1], v[0], v[1] or ""] for k, v in rows],
            ["notebook", "notes", "archived"])
    return 0


def cmd_tags(ctx, a):
    ctx.require_root()
    records, _ = ctx.scan()
    counts = OrderedDict((t, 0) for t in (ctx.declared("tags") or []))
    for r in records:
        if r.prefix == "NOTE" and not r.archived and isinstance(r.fm.get("tags"), list):
            for t in r.fm["tags"]:
                counts[t] = counts.get(t, 0) + 1
    rows = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    if a.json:
        R.emit_json(OrderedDict(rows))
        return 0
    R.table([[k, v] for k, v in rows], ["tag", "notes"])
    return 0


def cmd_decisions(ctx, a):
    ctx.require_root()
    records, _ = ctx.scan()
    decs = sorted([r for r in records if r.prefix == "DEC" and r.parsed],
                  key=lambda r: R.parse_id(r.id)[1] if r.id and R.parse_id(r.id) else 0)
    rows = []
    for d in decs:
        st = M.decision_status(d, decs)
        if not a.all and st.startswith("superseded"):
            continue
        if a.category and d.fm.get("category") != a.category:
            continue
        rows.append((d, st))
    if a.json:
        R.emit_json([OrderedDict([("id", d.id), ("created", d.fm.get("created")),
                                  ("category", d.fm.get("category")), ("status", st),
                                  ("ruling", d.h1), ("path", ctx.rel_of(d))]) for d, st in rows])
        return 0
    if not rows:
        print("(no decisions%s)" % ("" if a.all else " in force"))
        return 0
    R.table([[d.id, d.fm.get("created", ""), d.fm.get("category", "-"), st, d.h1 or ""]
             for d, st in rows], ["id", "decided", "category", "status", "ruling"])
    return 0


def cmd_history(ctx, a):
    ctx.require_root()
    rows, problems, exists = R.load_history(ctx.history_path)
    if a.id:
        rows = [r for r in rows if r.id == a.id]
    if a.json:
        R.emit_json([OrderedDict([("at", r.at), ("id", r.id), ("verb", r.verb), ("from", r.frm),
                                  ("to", r.to), ("actor", r.actor), ("note", r.note)])
                     for r in rows])
        return 0
    R.table([[r.at, r.id, r.verb, r.frm, r.to, r.actor, r.note] for r in rows],
            ["at", "id", "verb", "from", "to", "actor", "note"])
    return 0


def cmd_check(ctx, a):
    report = V.run(ctx, fix=a.fix)
    report.render(as_json=a.json, quiet=a.quiet)
    return report.exit_code()


# ---------------------------------------------------------------------------
# the parser
# ---------------------------------------------------------------------------

def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", help="project root (default: the project that owns this tool)")
    common.add_argument("--json", action="store_true", help="machine-readable output")
    writer = argparse.ArgumentParser(add_help=False)
    writer.add_argument("--by", help="who is doing this (else $RASA_ACTOR, else default_actor)")
    writer.add_argument("--dry-run", action="store_true", help="show what would happen; write nothing")

    ap = argparse.ArgumentParser(prog=M.CLI, description="rasa.module.notes %s — notes, notebooks, "
                                 "and the decision ledger (records-family/1). The law: "
                                 ".claude/notes-rules.md" % M.VERSION)
    ap.add_argument("--version", action="version", version="%s %s (%s, core %s)" % (
        M.ELEMENT, M.VERSION, R.FAMILY, R.CORE_VERSION))
    sub = ap.add_subparsers(dest="verb", metavar="<verb>")

    def body_args(p, flag="--body"):
        p.add_argument(flag, dest="body", help="the text")
        p.add_argument("--body-file", help="read the text from a file")
        p.add_argument("--stdin", action="store_true", help="read the text from stdin")

    p = sub.add_parser("new", parents=[common, writer], help="file a new note")
    p.add_argument("title")
    p.add_argument("--in", dest="into", metavar="NOTEBOOK", help="notebook path (default: inbox)")
    p.add_argument("--tag", action="append", help="a tag (repeatable)")
    p.add_argument("--type", help="the note type")
    p.add_argument("--about", action="append", metavar="REF", help="a family id it is about (repeatable)")
    p.add_argument("--source", help="where it came from: a URI or a family id")
    p.add_argument("--pin", action="store_true")
    body_args(p)
    p.set_defaults(fn=cmd_new)

    p = sub.add_parser("today", parents=[common, writer], help="open or create the daily note")
    p.add_argument("--day", help="another day (yesterday, 2026-09-01, -1d)")
    p.add_argument("--tag", action="append")
    p.set_defaults(fn=cmd_today)

    p = sub.add_parser("append", parents=[common, writer], help="append a timestamped line")
    p.add_argument("id")
    p.add_argument("text", nargs="?")
    p.add_argument("--body-file")
    p.add_argument("--stdin", action="store_true")
    p.set_defaults(fn=cmd_append)

    p = sub.add_parser("move", parents=[common, writer], help="move a note to another notebook")
    p.add_argument("id")
    p.add_argument("--to", required=True, metavar="NOTEBOOK")
    p.set_defaults(fn=cmd_move)

    p = sub.add_parser("rename", parents=[common, writer], help="retitle a note (H1 + slug)")
    p.add_argument("id")
    p.add_argument("title")
    p.set_defaults(fn=cmd_rename)

    p = sub.add_parser("tag", parents=[common, writer], help="add/remove tags: +a -b")
    p.add_argument("id")
    p.add_argument("changes", nargs=argparse.REMAINDER)
    p.set_defaults(fn=cmd_tag)

    p = sub.add_parser("about", parents=[common, writer], help="add/remove about refs: +CARD-0001 -EVT-0002")
    p.add_argument("id")
    p.add_argument("changes", nargs=argparse.REMAINDER)
    p.set_defaults(fn=cmd_about)

    p = sub.add_parser("pin", parents=[common, writer], help="pin a note")
    p.add_argument("id")
    p.set_defaults(fn=lambda c, a: cmd_pin(c, a, True))
    p = sub.add_parser("unpin", parents=[common, writer], help="unpin a note")
    p.add_argument("id")
    p.set_defaults(fn=lambda c, a: cmd_pin(c, a, False))

    for name, restore in (("archive", False), ("restore", True)):
        p = sub.add_parser(name, parents=[common, writer], help="%s a note" % name)
        p.add_argument("id")
        p.add_argument("--note", help="why (goes in the history line)")
        p.set_defaults(fn=(lambda r: (lambda c, a: cmd_archive(c, a, r)))(restore))

    p = sub.add_parser("touch", parents=[common, writer], help="record a hand edit (stamps updated)")
    p.add_argument("id")
    p.add_argument("--note")
    p.set_defaults(fn=cmd_touch)

    p = sub.add_parser("decide", parents=[common, writer], help="record a ratified decision")
    p.add_argument("ruling", help="the decision, one line")
    p.add_argument("--basis", help="what it rests on (required)")
    p.add_argument("--basis-file")
    p.add_argument("--category")
    p.add_argument("--from", dest="source", action="append", metavar="REF",
                   help="a note/thread/event/task it came from (repeatable)")
    p.add_argument("--supersedes", action="append", metavar="DEC")
    p.add_argument("--context", help="optional context paragraph")
    p.set_defaults(fn=cmd_decide)

    p = sub.add_parser("canonize", parents=[common, writer],
                       help="record that a decision became canon (you make the canon edit)")
    p.add_argument("id")
    p.add_argument("--to", help="the canon target (one of canon_target, optionally #section)")
    p.set_defaults(fn=cmd_canonize)

    p = sub.add_parser("list", parents=[common], help="list notes")
    p.add_argument("--in", dest="into", metavar="NOTEBOOK")
    p.add_argument("--tag", action="append")
    p.add_argument("--type")
    p.add_argument("--about", metavar="REF")
    p.add_argument("--pinned", action="store_true")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--archived", action="store_true", help="only archived notes")
    g.add_argument("--all", action="store_true", help="include archived notes")
    p.set_defaults(fn=cmd_list)

    for name, fn, h in (("show", cmd_show, "print a record"), ("where", cmd_where, "print its path"),
                        ("links", cmd_links, "outgoing links and backlinks, family-wide")):
        p = sub.add_parser(name, parents=[common], help=h)
        p.add_argument("id")
        p.set_defaults(fn=fn)

    p = sub.add_parser("search", parents=[common], help="search titles, tags and bodies")
    p.add_argument("text", nargs="+")
    p.add_argument("--in", dest="into", metavar="NOTEBOOK")
    p.add_argument("--all", action="store_true", help="include archived notes")
    p.set_defaults(fn=cmd_search)

    p = sub.add_parser("notebooks", parents=[common], help="the notebook tree with counts")
    p.set_defaults(fn=cmd_notebooks)
    p = sub.add_parser("tags", parents=[common], help="tags with counts")
    p.set_defaults(fn=cmd_tags)

    p = sub.add_parser("decisions", parents=[common], help="the decision log, in order")
    p.add_argument("--all", action="store_true", help="include superseded decisions")
    p.add_argument("--category")
    p.set_defaults(fn=cmd_decisions)

    p = sub.add_parser("history", parents=[common], help="the history log")
    p.add_argument("id", nargs="?")
    p.set_defaults(fn=cmd_history)

    p = sub.add_parser("check", parents=[common], help="run the validator (same as check-notes)")
    p.add_argument("--fix", action="store_true")
    p.add_argument("--quiet", action="store_true")
    p.set_defaults(fn=cmd_check)
    return ap


def main(argv=None, bin_dir=None):
    def _main(argv):
        ap = build_parser()
        a = ap.parse_args(argv)
        if not getattr(a, "fn", None):
            ap.print_help()
            return R.EXIT_REFUSED
        if getattr(a, "json", False) is None:
            a.json = False
        ctx = M.Ctx(getattr(a, "root", None), bin_dir)
        return a.fn(ctx, a)
    return R.run_main(_main, argv)

# -*- coding: utf-8 -*-
"""validate.py — check-notes: every invariant in .claude/notes-rules.md, mechanically.

Family invariants F-01..F-27 come from records.py; the notes invariants
N-01..N-10 are here. Exit 0 = no errors (warnings allowed), 1 = errors,
2 = cannot run.
"""

import argparse
import os
import re
import sys
from collections import OrderedDict

from . import model as M
from . import records as R


def run(ctx, fix=False):
    report = R.Report(M.CHECK)
    if not os.path.isdir(ctx.root):
        report.error("F-15", "there is no %s/ directory here (%s)" % (M.ROOT, ctx.project),
                     fix="install rasa.module.notes with its bin/init, or pass --root")
        return report
    today = R.today()

    # ---- config ---------------------------------------------------------
    for inv, line, msg in ctx.config_problems:
        report.error(inv, msg, where=ctx.rel_root(M.CONFIG_NAME), line=line)
    cfg = ctx.config if not ctx.config_problems else {}
    actors = R.declared(cfg, "actors")

    # ---- the files ------------------------------------------------------
    records, strays = ctx.scan()
    report.records = len(records)
    if strays:
        report.info("F-27", "not records, left alone: %s" % ", ".join(
            ctx.rel_root(s) for s in strays), where=M.ROOT)

    index = R.family_index(ctx.project)
    mounted = R.mounted_modules(ctx.project)
    usable = []
    for rec in records:
        where = ctx.rel_of(rec)
        schema = ctx.schema_for(rec)
        if schema is None:
            report.error("F-03", "%s is not a notes record type (NOTE, DEC)" % rec.stem,
                         where=where)
            continue
        if not R.check_record_common(rec, schema, report, where, actors=actors, today_=today):
            continue
        if rec.prefix not in M.PREFIX_TYPE:
            continue
        usable.append(rec)
        if rec.prefix == "NOTE":
            check_note(ctx, rec, where, report, cfg)
        else:
            check_decision_local(ctx, rec, where, report, cfg, today)
        # references
        for key, ref in R.frontmatter_refs(rec, schema):
            R.check_ref(ref, index, mounted, report, where, rec.line_of(key), key=key)
        for ref, line in R.body_refs(rec):
            R.check_ref(ref, index, mounted, report, where, line, body=True)

    R.check_unique_ids(usable, report, ctx.rel_of)
    check_decision_graph(ctx, [r for r in usable if r.prefix == "DEC"], report)
    check_journal(ctx, [r for r in usable if r.prefix == "NOTE"], report)

    # ---- history ----------------------------------------------------------
    rows, problems, exists = R.load_history(ctx.history_path)
    hrel = ctx.rel_root("history.tsv")
    for inv, line, msg in problems:
        report.error(inv, msg, where=hrel, line=line)
    fixes = []
    R.check_history_common(usable, rows, exists, report,
                           module_ids_ok=lambda rid: R.ref_prefix(rid) in M.PREFIX_TYPE,
                           place_of=M.Ctx.place_of, rel_of=ctx.rel_of, history_rel=hrel,
                           cli=M.CLI, fixes=fixes)
    for row in rows:
        if R.ref_prefix(row.id) not in M.PREFIX_TYPE:
            report.error("F-13", "%s does not belong to notes" % row.id, where=hrel,
                         line=row.lineno)
        if actors is not None and row.actor not in actors and row.actor != "unknown":
            report.error("F-22", "actor '%s' is not declared" % row.actor, where=hrel,
                         line=row.lineno)

    # ---- digests ----------------------------------------------------------
    table, had_table = R.load_digests(ctx.root)
    schemas = {r.id: ctx.schema_for(r) for r in usable}
    fresh = R.check_digests(usable, table, report, ctx.rel_of, M.CLI,
                            is_frozen=lambda r: M.is_frozen(r, schemas.get(r.id)),
                            mutable_keys_of=lambda r: M.mutable_keys(r, schemas.get(r.id)),
                            today_=today)

    # ---- --fix: the mechanical subset, then re-check ------------------------
    if fix and fixes:
        with ctx.lock():
            entries = []
            seen = set()
            for kind, rec in fixes:
                if rec.id in seen:
                    continue
                seen.add(rec.id)
                entries.append((rec.id, "reconcile", "-", M.Ctx.place_of(rec), "unknown",
                                "reconciled"))
            if not exists:
                entries.sort(key=lambda e: e[0])
            ctx.log(entries)
        report.notes.append("--fix appended %d reconcile line(s) to %s" % (len(entries), hrel))
        return run(ctx, fix=False)

    if report.ok:
        if fresh != table or not had_table:
            R.save_digests(ctx.root, fresh)
            if not had_table and usable:
                report.notes.append("seeded the content cache (%s/.state/digests.tsv)" % M.ROOT)
    return report


def check_note(ctx, rec, where, report, cfg):
    nb = M.Ctx.notebook_of(rec)
    # N-01 a note lives in a notebook: not at the root, not in decisions/, depth <= 3
    if nb == "":
        report.error("N-01", "a note must live in a notebook directory, not at the top of notes/",
                     where=where, fix="%s move %s --to %s" % (M.CLI, rec.id, ctx.default_notebook))
        return
    top = nb.split("/")[0]
    if top == M.DECISIONS_DIR:
        report.error("N-01", "a note may not live in decisions/ (that is the decision ledger)",
                     where=where, fix="%s move %s --to <notebook>" % (M.CLI, rec.id))
        return
    if not M.RX_NOTEBOOK.match(nb):
        report.error("N-01", "'%s' is not a notebook path: lower-case words joined by '-', at "
                             "most %d levels" % (nb, M.MAX_DEPTH), where=where)
        return
    # N-02 declared notebooks
    allowed = R.declared(cfg, "notebooks")
    if allowed is not None and nb not in allowed:
        report.error("N-02", "notebook '%s' is not declared in %s" % (
            nb, ctx.rel_root(M.CONFIG_NAME)), where=where)
    # F-21 declared vocabularies
    if isinstance(rec.fm.get("type"), str):
        R.check_declared(rec.fm["type"], R.declared(cfg, "types"), report, "type", where,
                         rec.line_of("type"))
    tags = rec.fm.get("tags")
    if isinstance(tags, list):
        allowed_tags = R.declared(cfg, "tags")
        for t in tags:
            R.check_declared(t, allowed_tags, report, "tag", where, rec.line_of("tags"))
    # N-08 pinned is only ever true (the schema already says so; this names the fix)
    if rec.fm.get("pinned") == "false":
        report.error("N-08", "'pinned: false' says nothing; omit the key", where=where,
                     line=rec.line_of("pinned"), fix="%s unpin %s" % (M.CLI, rec.id))
    # N-10 a note does not reference itself
    about = rec.fm.get("about")
    if isinstance(about, list) and rec.id in about:
        report.error("N-10", "a note cannot be about itself", where=where, line=rec.line_of("about"))


def check_decision_local(ctx, rec, where, report, cfg, today):
    # N-03 decisions live only in decisions/, never archived
    if rec.dir != M.DECISIONS_DIR:
        report.error("N-03", "a decision lives only in %s/%s/ (never in a notebook, never "
                             "archived)" % (M.ROOT, M.DECISIONS_DIR), where=where)
    # N-04 the basis
    basis = M.basis_text(rec)
    if basis is None:
        report.error("N-04", "a decision needs a '## Basis' section; a ruling without a basis is "
                             "a working note", where=where)
    elif not basis:
        report.error("N-04", "'## Basis' is empty; state what the decision rests on", where=where)
    # N-07 category
    cat = rec.fm.get("category")
    cats = R.declared(cfg, "categories")
    if cats is not None and not isinstance(cat, str):
        report.error("N-07", "this project declares decision categories (%s); every decision "
                             "carries one" % ", ".join(cats), where=where)
    elif isinstance(cat, str):
        R.check_declared(cat, cats, report, "category", where, rec.line_of("category"))
    # N-06 promotion
    promoted = R.parse_date(rec.fm.get("promoted")) if isinstance(rec.fm.get("promoted"), str) \
        else None
    created = R.parse_date(rec.fm.get("created")) if isinstance(rec.fm.get("created"), str) \
        else None
    if promoted and created and promoted < created:
        report.error("N-06", "promoted %s is earlier than created %s" % (promoted, created),
                     where=where, line=rec.line_of("promoted"))
    if promoted and promoted > today:
        report.error("N-06", "promoted %s is in the future" % promoted, where=where,
                     line=rec.line_of("promoted"))
    target = rec.fm.get("promoted_to")
    if isinstance(target, str):
        targets = R.declared(cfg, "canon_target")
        if targets is None:
            report.warn("N-06", "promoted to '%s' but this project declares no canon_target"
                        % target, where=where, line=rec.line_of("promoted_to"))
        elif not any(target == t or target.startswith(t.rstrip("/") + "/") or
                     target.startswith(t + "#") for t in targets):
            report.error("N-06", "promoted_to '%s' is not inside a declared canon_target (%s)"
                         % (target, ", ".join(targets)), where=where,
                         line=rec.line_of("promoted_to"))


def check_decision_graph(ctx, decs, report):
    """N-05: supersedes resolve, point backwards, never self, no cycles, one successor each."""
    by_id = OrderedDict((d.id, d) for d in decs)
    successor = {}
    for d in decs:
        sup = d.fm.get("supersedes")
        if not isinstance(sup, list):
            continue
        where = ctx.rel_of(d)
        for old in sup:
            if old == d.id:
                report.error("N-05", "a decision cannot supersede itself", where=where,
                             line=d.line_of("supersedes"))
                continue
            if old not in by_id:
                report.error("N-05", "supersedes %s, which is not in the decision ledger" % old,
                             where=where, line=d.line_of("supersedes"))
                continue
            if R.parse_id(old)[1] > R.parse_id(d.id)[1]:
                report.error("N-05", "supersedes %s, which is newer; a decision only replaces "
                                     "older ones" % old, where=where,
                             line=d.line_of("supersedes"))
            if old in successor:
                report.error("N-05", "%s is superseded by both %s and %s; supersede the newer "
                                     "one instead" % (old, successor[old], d.id), where=where,
                             line=d.line_of("supersedes"))
            else:
                successor[old] = d.id
    # cycles (only possible with forward references, which are already errors; belt and braces)
    for start in by_id:
        seen, cur = set(), start
        while cur in successor:
            if cur in seen:
                report.error("N-05", "the supersedes chain loops through %s" % cur,
                             where=ctx.rel_of(by_id[start]))
                break
            seen.add(cur)
            cur = successor[cur]


def check_journal(ctx, notes, report):
    """N-09: one daily note per date in the journal notebook."""
    jn = ctx.journal_notebook
    seen = {}
    for n in notes:
        if M.Ctx.notebook_of(n) != jn or n.archived:
            continue
        if n.h1 and R.parse_date(n.h1):
            if n.h1 in seen:
                report.warn("N-09", "two daily notes for %s: %s and %s" % (
                    n.h1, seen[n.h1], n.id), where=ctx.rel_of(n))
            else:
                seen[n.h1] = n.id


def main(argv=None, bin_dir=None):
    def _main(argv):
        ap = argparse.ArgumentParser(prog=M.CHECK, description="Validate the notes ledger "
                                     "against .claude/notes-rules.md (records-family/1).")
        ap.add_argument("--root", help="project root (default: the project that owns this tool)")
        ap.add_argument("--fix", action="store_true",
                        help="repair the mechanical subset (history reconcile lines); never "
                             "invents a person or a date")
        ap.add_argument("--json", action="store_true", help="machine-readable report")
        ap.add_argument("--quiet", action="store_true", help="errors only")
        a = ap.parse_args(argv)
        ctx = M.Ctx(a.root, bin_dir)
        report = run(ctx, fix=a.fix)
        report.render(as_json=a.json, quiet=a.quiet)
        return report.exit_code()
    return R.run_main(_main, argv)

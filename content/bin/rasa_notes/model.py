# -*- coding: utf-8 -*-
"""model.py — what a notes ledger is: its paths, its record types, its config.

Everything the CLI and the validator share about rasa.module.notes lives
here, so neither re-derives it. The family conventions live in records.py.
"""

import os
import re
from collections import OrderedDict

from . import records as R

MODULE = "notes"
ELEMENT = "rasa.module.notes"
VERSION = "0.2.0"
ROOT = "notes"
CLI = "notes"
CHECK = "check-notes"
CONFIG_NAME = "notes.config.yml"
CONFIG_SCHEMA_VALUE = "rasa.module.notes/1"

DECISIONS_DIR = "decisions"
DEFAULT_NOTEBOOK = "inbox"
JOURNAL_NOTEBOOK = "journal"
MAX_DEPTH = 3
RESERVED_TOP = (DECISIONS_DIR, R.ARCHIVE_DIR, R.STATE_DIR)
RX_NOTEBOOK = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*(?:/[a-z0-9]+(?:-[a-z0-9]+)*){0,2}$")
RX_RECORD_STEM = re.compile(r"^(NOTE|DEC)-[0-9]{4,}(?:-[a-z0-9]+(?:-[a-z0-9]+)*)?$")
RX_BASIS = re.compile(r"^##[ \t]+Basis[ \t]*$")

PREFIX_TYPE = {"NOTE": "note", "DEC": "decision"}
HERE = os.path.dirname(os.path.abspath(__file__))


def schema_dir():
    """Installed: .claude/schemas/notes/. Element source: content/schemas/."""
    for cand in (os.path.join(HERE, "..", "..", "schemas", MODULE),
                 os.path.join(HERE, "..", "..", "schemas")):
        if os.path.exists(os.path.join(cand, "note.schema.json")):
            return os.path.normpath(cand)
    raise R.EnvError("cannot find the notes schemas next to %s (expected "
                     ".claude/schemas/notes/note.schema.json)" % HERE)


class Ctx(object):
    """One project's notes ledger."""

    def __init__(self, project_root=None, bin_dir=None):
        self.project = R.find_project_root(project_root, bin_dir)
        self.root = os.path.join(self.project, ROOT)
        self.history_path = os.path.join(self.root, "history.tsv")
        self.config_path = os.path.join(self.root, CONFIG_NAME)
        sd = schema_dir()
        self.schemas = {
            "note": R.load_json(os.path.join(sd, "note.schema.json")),
            "decision": R.load_json(os.path.join(sd, "decision.schema.json")),
            "config": R.load_json(os.path.join(sd, "config.schema.json")),
        }
        self.config, self.config_problems, self.config_exists = R.load_config(
            self.config_path, self.schemas["config"], self.rel_root(CONFIG_NAME))

    # -- paths -------------------------------------------------------------

    def rel_root(self, rel):
        return ROOT + "/" + rel if rel else ROOT

    def rel_of(self, rec):
        return self.rel_root(rec.rel)

    def abs(self, rel):
        return os.path.join(self.root, *rel.split("/"))

    def require_root(self):
        if not os.path.isdir(self.root):
            raise R.EnvError("no notes ledger at %s — install rasa.module.notes (bin/init) "
                             "or pass --root" % self.root)

    # -- config ------------------------------------------------------------

    def usable_config(self):
        if self.config_problems:
            first = self.config_problems[0]
            raise R.EnvError("%s is not valid (line %s: %s); run %s" % (
                self.rel_root(CONFIG_NAME), first[1], first[2], CHECK))
        return self.config

    @property
    def default_notebook(self):
        return self.config.get("default_notebook") or DEFAULT_NOTEBOOK

    @property
    def journal_notebook(self):
        return self.config.get("journal_notebook") or JOURNAL_NOTEBOOK

    def declared(self, key):
        return R.declared(self.config, key)

    # -- records -----------------------------------------------------------

    @staticmethod
    def is_record_name(stem, rel):
        return bool(RX_RECORD_STEM.match(stem))

    def scan(self):
        found, strays = R.scan_root(self.root, self.is_record_name)
        return [R.read_record(p, rel) for p, rel in found], strays

    def schema_for(self, rec):
        t = PREFIX_TYPE.get(rec.prefix or "")
        if t is None:
            m = RX_RECORD_STEM.match(rec.stem)
            t = PREFIX_TYPE.get(m.group(1)) if m else None
        return self.schemas.get(t) if t else None

    def find(self, rid):
        """-> the Record for an id, or Refusal."""
        if not R.RX_NUMBERED_ID.match(rid or "") or R.ref_prefix(rid) not in PREFIX_TYPE:
            raise R.Refusal("'%s' is not a note or decision id (NOTE-0001, DEC-0001)" % rid)
        records, _ = self.scan()
        hits = [r for r in records if r.id == rid]
        if not hits:
            raise R.Refusal("no record %s in %s/" % (rid, ROOT))
        if len(hits) > 1:
            raise R.Refusal("%s is used by %d files; run %s" % (rid, len(hits), CHECK))
        return hits[0]

    # -- places ------------------------------------------------------------

    @staticmethod
    def notebook_of(rec):
        """The notebook a note lives in ('' for none), archive prefix removed."""
        d = rec.dir
        if d == R.ARCHIVE_DIR:
            return ""
        if d.startswith(R.ARCHIVE_DIR + "/"):
            return d[len(R.ARCHIVE_DIR) + 1:]
        return d

    @staticmethod
    def place_of(rec):
        return R.place_token(rec.dir)

    def check_notebook(self, nb, for_write=True):
        """Validate a notebook path a note is being filed into. -> nb or Refusal."""
        nb = (nb or "").strip().strip("/")
        if not RX_NOTEBOOK.match(nb):
            raise R.Refusal("'%s' is not a notebook path: lower-case words joined by '-', up to "
                            "%d levels separated by '/' (e.g. work/clients)" % (nb, MAX_DEPTH))
        top = nb.split("/")[0]
        if top in RESERVED_TOP or top.startswith("_") or top.startswith("."):
            raise R.Refusal("'%s' is reserved inside notes/ and cannot be a notebook" % top)
        allowed = self.declared("notebooks")
        if allowed is not None and nb not in allowed:
            raise R.Refusal("notebook '%s' is not declared in %s (declared: %s)" % (
                nb, self.rel_root(CONFIG_NAME), ", ".join(allowed)))
        return nb

    # -- writing -----------------------------------------------------------

    def lock(self):
        return R.Lock(self.root)

    def history(self):
        rows, _, _ = R.load_history(self.history_path)
        return rows

    def write(self, abs_path, fm, body, schema, info=None):
        """Render, self-validate, and atomically write one record. -> text."""
        text = R.render_record(fm, body, schema, info)
        problems = R.schema_errors(schema, fm)
        if problems:
            inv, path, msg = problems[0]
            raise R.Refusal("refusing to write an invalid record: %s %s (%s)" % (path, msg, inv))
        R.atomic_write(abs_path, text)
        return text

    def refresh_digest(self, rec_or_path, rel=None):
        """Re-read a record just written and store its digest (keeping a frozen hash)."""
        if isinstance(rec_or_path, R.Record):
            rec = R.read_record(rec_or_path.path, rec_or_path.rel)
        else:
            rec = R.read_record(rec_or_path, rel)
        table, _ = R.load_digests(self.root)
        schema = self.schema_for(rec) or {}
        frozen = is_frozen(rec, schema)
        table[rec.id] = R.digest_entry(rec, frozen, mutable_keys(rec, schema), table.get(rec.id))
        R.save_digests(self.root, table)
        return rec

    def log(self, entries):
        return R.append_history(self.history_path, entries)


def is_frozen(rec, schema):
    return (schema or {}).get("x-frozen") == "always"


def mutable_keys(rec, schema):
    return list((schema or {}).get("x-mutable-when-frozen") or [])


def basis_text(rec):
    """The text under '## Basis' up to the next heading (None when there is no such heading)."""
    lines = rec.body.split("\n")
    marks = R.fence_map(lines)
    start = None
    for idx, line in enumerate(lines):
        if marks[idx]:
            continue
        if start is None:
            if RX_BASIS.match(line):
                start = idx + 1
            continue
        if line.startswith("#"):
            return "\n".join(lines[start:idx]).strip()
    if start is None:
        return None
    return "\n".join(lines[start:]).strip()


def decision_status(dec, all_decs):
    """Derived, never stored: 'superseded by DEC-x', 'canon: target', or 'in force'."""
    for other in all_decs:
        sup = other.fm.get("supersedes")
        if isinstance(sup, list) and dec.id in sup:
            return "superseded by %s" % other.id
    if isinstance(dec.fm.get("promoted_to"), str):
        return "canon: %s" % dec.fm["promoted_to"]
    return "in force"


def summary(rec):
    """A JSON-ready view of a record."""
    return OrderedDict([("id", rec.id), ("type", PREFIX_TYPE.get(rec.prefix or "", "?")),
                        ("path", ROOT + "/" + rec.rel), ("title", rec.h1),
                        ("archived", rec.archived), ("frontmatter", rec.fm)])

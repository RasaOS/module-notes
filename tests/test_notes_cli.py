# -*- coding: utf-8 -*-
"""End-to-end checks for the notes tool and check-notes.

Every scenario runs the real programs in a scratch project, with the clock
and the actor pinned through $RASA_TODAY / $RASA_NOW / $RASA_ACTOR.
Run:  python3 -B -m unittest discover -s tests
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ELEMENT = os.path.dirname(HERE)
BIN = os.path.join(ELEMENT, "content", "bin")
NOTES = os.path.join(BIN, "notes")
CHECK = os.path.join(BIN, "check-notes")
TODAY = "2026-09-28"


class Base(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.proj = os.path.join(self.tmp, "proj")
        for d in (".claude", "notes/inbox", "notes/decisions"):
            os.makedirs(os.path.join(self.proj, d))
        with open(os.path.join(self.proj, "notes", "history.tsv"), "w") as fh:
            fh.write("at\tid\tverb\tfrom\tto\tactor\tnote\n")
        self.env = dict(os.environ)
        self.env.update({"RASA_PROJECT_ROOT": self.proj, "RASA_ACTOR": "chazz",
                         "RASA_TODAY": TODAY, "RASA_NOW": TODAY + "T12:00:00Z",
                         "PYTHONDONTWRITEBYTECODE": "1"})

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_(self, prog, *args, expect=0, env=None):
        e = dict(self.env)
        e.update(env or {})
        p = subprocess.run([sys.executable, "-B", prog] + list(args), capture_output=True,
                           text=True, env=e)
        if expect is not None:
            self.assertEqual(p.returncode, expect, "%s %s\nstdout:%s\nstderr:%s" % (
                os.path.basename(prog), " ".join(args), p.stdout, p.stderr))
        return p

    def notes(self, *args, **kw):
        return self.run_(NOTES, *args, **kw)

    def check(self, *args, **kw):
        return self.run_(CHECK, *args, **kw)

    def check_json(self, expect=None, env=None):
        p = self.run_(CHECK, "--json", expect=expect, env=env)
        return json.loads(p.stdout)

    def invariants(self, env=None):
        d = self.check_json(env=env)
        return sorted(set(f["invariant"] for f in d["findings"] if f["severity"] != "INFO"))

    def path(self, *parts):
        return os.path.join(self.proj, "notes", *parts)

    def read(self, rel):
        with open(self.path(*rel.split("/"))) as fh:
            return fh.read()

    def config(self, text):
        with open(self.path("notes.config.yml"), "w") as fh:
            fh.write("schema: rasa.module.notes/1\n" + text)


class WalkthroughTests(Base):

    def test_capture_organize_decide_canonize(self):
        out = self.notes("new", "Kickoff with Acme", "--in", "work/clients", "--tag", "meeting",
                         "--body", "Talked scope.").stdout
        self.assertIn("NOTE-0001  notes/work/clients/NOTE-0001-kickoff-with-acme.md", out)
        self.notes("new", "Groceries", "--pin")
        self.notes("today")
        self.assertIn("created\": false", self.notes("today", "--json").stdout)
        self.notes("append", "NOTE-0001", "Follow up on pricing")
        self.notes("tag", "NOTE-0001", "+acme", "-meeting")
        self.notes("move", "NOTE-0002", "--to", "personal")
        self.notes("rename", "NOTE-0002", "Weekly groceries")
        self.assertTrue(os.path.exists(self.path("personal", "NOTE-0002-weekly-groceries.md")))
        self.notes("decide", "Flat pricing for Acme", "--basis", "Simpler to quote.",
                   "--from", "NOTE-0001")
        self.notes("decide", "Tiered pricing for Acme", "--basis", "Flat undercharged.",
                   "--supersedes", "DEC-0001")
        # the hard-stop, then the real thing
        p = self.notes("canonize", "DEC-0002", expect=1)
        self.assertIn("HARD-STOP", p.stderr)
        self.config("canon_target: [CLAUDE.md, docs/]\n")
        self.assertIn("superseded by DEC-0002", self.notes("canonize", "DEC-0001", expect=1).stderr)
        self.assertIn("pass --to", self.notes("canonize", "DEC-0002", expect=1).stderr)
        self.notes("canonize", "DEC-0002", "--to", "docs/pricing.md")
        dec = self.read("decisions/DEC-0002-tiered-pricing-for-acme.md")
        self.assertIn("promoted_to: docs/pricing.md\npromoted: 2026-09-28", dec)
        self.assertIn("supersedes: [DEC-0001]", dec)
        note = self.read("work/clients/NOTE-0001-kickoff-with-acme.md")
        self.assertIn("tags: [acme]", note)
        self.assertIn("**2026-09-28", note)
        # read verbs
        lst = json.loads(self.notes("list", "--json").stdout)
        self.assertEqual([n["id"] for n in lst][0], "NOTE-0002")  # pinned first
        decs = json.loads(self.notes("decisions", "--all", "--json").stdout)
        self.assertEqual([d["status"] for d in decs],
                         ["superseded by DEC-0002", "canon: docs/pricing.md"])
        links = json.loads(self.notes("links", "NOTE-0001", "--json").stdout)
        self.assertEqual([b["path"] for b in links["backlinks"]],
                         ["notes/decisions/DEC-0001-flat-pricing-for-acme.md"])
        hits = json.loads(self.notes("search", "undercharged", "--json").stdout)
        self.assertEqual([h["id"] for h in hits], ["DEC-0002"])
        hist = json.loads(self.notes("history", "--json").stdout)
        self.assertEqual([h["verb"] for h in hist], [
            "new", "new", "new", "append", "tag", "move", "rename", "new", "new", "canonize"])
        # and the ledger is valid
        self.assertEqual(self.check_json()["counts"]["error"], 0)

    def test_archive_restore_and_pins(self):
        self.notes("new", "Old idea", "--in", "ideas")
        self.notes("archive", "NOTE-0001", "--note", "stale")
        self.assertTrue(os.path.exists(self.path("_archive", "ideas", "NOTE-0001-old-idea.md")))
        self.assertEqual(json.loads(self.notes("list", "--json").stdout), [])
        self.assertEqual(len(json.loads(self.notes("list", "--archived", "--json").stdout)), 1)
        self.notes("move", "NOTE-0001", "--to", "x", expect=1)   # archived: restore first
        self.notes("restore", "NOTE-0001")
        self.notes("pin", "NOTE-0001")
        self.notes("pin", "NOTE-0001", expect=1)
        self.notes("unpin", "NOTE-0001")
        self.assertNotIn("pinned", self.read("ideas/NOTE-0001-old-idea.md"))
        self.check()

    def test_dry_run_writes_nothing(self):
        self.notes("new", "Ghost", "--dry-run")
        self.assertEqual(os.listdir(self.path("inbox")), [])
        with open(self.path("history.tsv")) as fh:
            self.assertEqual(len(fh.read().strip().split("\n")), 1)

    def test_ids_are_never_reissued(self):
        self.notes("new", "One")
        os.remove(self.path("inbox", "NOTE-0001-one.md"))
        out = self.notes("new", "Two").stdout
        self.assertIn("NOTE-0002", out)
        self.assertEqual(self.check_json()["counts"]["error"], 0)   # F-17 is a warning
        warns = [f["invariant"] for f in self.check_json()["findings"] if f["severity"] == "WARN"]
        self.assertEqual(warns, ["F-17"])


class RefusalTests(Base):

    def test_actor_is_never_invented(self):
        p = self.notes("new", "x", expect=1, env={"RASA_ACTOR": ""})
        self.assertIn("who is doing this", p.stderr)
        self.config("default_actor: claude\nactors: [chazz, claude]\n")
        self.notes("new", "x", env={"RASA_ACTOR": ""})
        self.notes("new", "y", "--by", "zed", expect=1)

    def test_declared_vocabularies_are_closed(self):
        self.config("notebooks: [inbox, work]\ntags: [acme]\ntypes: [meeting]\n"
                    "categories: [pricing]\n")
        self.notes("new", "x", "--in", "personal", expect=1)
        self.notes("new", "x", "--tag", "nope", expect=1)
        self.notes("new", "x", "--type", "idea", expect=1)
        self.notes("new", "x", "--in", "work", "--tag", "acme", "--type", "meeting")
        self.notes("decide", "R", "--basis", "b", expect=1)                   # category required
        self.notes("decide", "R", "--basis", "b", "--category", "other", expect=1)
        self.notes("decide", "R", "--basis", "b", "--category", "pricing")

    def test_reserved_and_malformed_notebooks(self):
        for nb in ("decisions", "_archive", "Work", "a/b/c/d", "../x"):
            self.notes("new", "x", "--in", nb, expect=1)

    def test_decisions_need_a_basis_and_are_frozen(self):
        self.notes("decide", "R", expect=1)
        self.notes("decide", "R", "--basis", "   ", expect=1)
        self.notes("decide", "R", "--basis", "b")
        for verb in (("tag", "DEC-0001", "+x"), ("move", "DEC-0001", "--to", "x"),
                     ("archive", "DEC-0001"), ("rename", "DEC-0001", "y")):
            self.assertIn("frozen", self.notes(*verb, expect=1).stderr)
        self.notes("decide", "R2", "--basis", "b", "--supersedes", "DEC-0001")
        self.assertIn("already superseded",
                      self.notes("decide", "R3", "--basis", "b", "--supersedes", "DEC-0001",
                                 expect=1).stderr)
        self.notes("decide", "R3", "--basis", "b", "--supersedes", "DEC-0009", expect=1)

    def test_dangling_about_is_refused_when_mounted(self):
        self.notes("new", "x", "--about", "NOTE-0099", expect=1)
        self.notes("new", "x", "--about", "CARD-0001")          # crm not mounted: allowed
        os.makedirs(os.path.join(self.proj, "crm", "contacts"))
        self.notes("new", "y", "--about", "CARD-0001", expect=1)  # crm mounted: must resolve
        self.notes("new", "z", "--about", "NOT-A-REF", expect=1)

    def test_canon_target_must_contain_the_target(self):
        self.config("canon_target: [CLAUDE.md]\n")
        self.notes("decide", "R", "--basis", "b")
        self.notes("canonize", "DEC-0001", "--to", "README.md", expect=1)
        self.notes("canonize", "DEC-0001", "--to", "CLAUDE.md#rules")
        self.notes("canonize", "DEC-0001", expect=1)          # already canon

    def test_unknown_id_and_wrong_kind(self):
        self.notes("show", "NOTE-0404", expect=1)
        self.notes("show", "EVT-0001", expect=1)
        self.notes("canonize", "NOTE-0001", expect=1)


class InvariantTests(Base):
    """Every hand-made break is caught, under the right id."""

    def seed(self):
        self.notes("new", "Alpha", "--in", "work")
        self.notes("new", "Beta")
        self.notes("decide", "Ruling", "--basis", "Because.", "--from", "NOTE-0001")
        self.check()  # seeds the content cache

    def later(self):
        return {"RASA_TODAY": "2026-10-02", "RASA_NOW": "2026-10-02T12:00:00Z"}

    def test_hand_edit_without_touch(self):
        self.seed()
        with open(self.path("inbox", "NOTE-0002-beta.md"), "a") as fh:
            fh.write("more\n")
        self.assertEqual(self.invariants(env=self.later()), ["F-18"])
        self.notes("touch", "NOTE-0002", env=self.later())
        self.assertEqual(self.invariants(env=self.later()), [])
        self.assertIn("updated: 2026-10-02", self.read("inbox/NOTE-0002-beta.md"))

    def test_same_day_edit_is_already_true(self):
        self.seed()
        with open(self.path("inbox", "NOTE-0002-beta.md"), "a") as fh:
            fh.write("more\n")
        self.assertEqual(self.invariants(), [])

    def test_frozen_decision_tamper(self):
        self.seed()
        p = self.path("decisions", "DEC-0001-ruling.md")
        with open(p) as fh:
            text = fh.read()
        with open(p, "w") as fh:
            fh.write(text.replace("Because.", "Because I said so."))
        self.assertIn("F-19", self.invariants())
        self.assertIn("F-19", self.invariants(env=self.later()))

    def test_hand_move_and_fix(self):
        self.seed()
        os.makedirs(self.path("elsewhere"))
        os.rename(self.path("inbox", "NOTE-0002-beta.md"),
                  self.path("elsewhere", "NOTE-0002-beta.md"))
        self.assertEqual(self.invariants(), ["F-16"])
        self.check("--fix")
        self.assertEqual(self.invariants(), [])
        with open(self.path("history.tsv")) as fh:
            self.assertIn("reconcile\t-\telsewhere\tunknown\treconciled", fh.read())

    def test_unfiled_record_and_fix(self):
        self.seed()
        with open(self.path("inbox", "NOTE-0010-stray.md"), "w") as fh:
            fh.write("---\nid: NOTE-0010\ncreated: 2026-09-28\ncreated_by: chazz\n"
                     "updated: 2026-09-28\n---\n\n# Stray\n")
        self.assertEqual(self.invariants(), ["F-15"])
        self.check("--fix")
        self.assertEqual(self.invariants(), [])
        self.assertIn("NOTE-0011", self.notes("new", "Next").stdout)

    def test_grammar_keys_refs_and_titles(self):
        self.seed()
        cases = {
            "NOTE-0020-a.md": ("---\nid: NOTE-0020\ntags: [a b\n---\n# A\n", "F-05"),
            "NOTE-0021-b.md": ("---\nid: NOTE-0021\ncreated: 2026-09-28\ncreated_by: chazz\n"
                               "updated: 2026-09-28\nbogus: 1\n---\n\n# B\n", "F-06"),
            "NOTE-0022-c.md": ("---\nid: NOTE-0022\ncreated: 2026-09-28\ncreated_by: chazz\n"
                               "updated: 2026-09-28\nabout: [NOTE-0099]\n---\n\n# C\n", "F-10"),
            "NOTE-0023-d.md": ("---\nid: NOTE-0023\ncreated: 2026-09-28\ncreated_by: chazz\n"
                               "updated: 2026-09-28\n---\n\nno title here\n", "F-04"),
            "NOTE-0024-e.md": ("---\nid: NOTE-0024\ncreated: 2026-09-28\ncreated_by: chazz\n"
                               "updated: 2026-09-27\n---\n\n# E\n", "F-23"),
            "NOTE-0025-f.md": ("---\nid: NOTE-0025\ncreated: 2026-09-28\ncreated_by: chazz\n"
                               "updated: 2026-09-28\npinned: false\n---\n\n# F\n", "N-08"),
            "NOTE-0026-g.md": ("---\nid: NOTE-0001\ncreated: 2026-09-28\ncreated_by: chazz\n"
                               "updated: 2026-09-28\n---\n\n# G\n", "F-08"),
        }
        for name, (text, inv) in cases.items():
            with open(self.path("inbox", name), "w") as fh:
                fh.write(text)
            found = self.invariants()
            self.assertIn(inv, found, "%s should raise %s, got %s" % (name, inv, found))
            os.remove(self.path("inbox", name))

    def test_decision_law(self):
        self.seed()
        base = "---\nid: DEC-00%s\ncreated: 2026-09-28\ncreated_by: chazz\nupdated: 2026-09-28\n%s---\n\n# R\n%s"
        cases = [
            ("decisions/DEC-0030-x.md", base % ("30", "", "\nno basis\n"), "N-04"),
            ("decisions/DEC-0031-x.md", base % ("31", "", "\n## Basis\n\n## Next\n"), "N-04"),
            ("decisions/DEC-0032-x.md", base % ("32", "supersedes: [DEC-0032]\n", "\n## Basis\nb\n"), "N-05"),
            ("decisions/DEC-0033-x.md", base % ("33", "supersedes: [DEC-0099]\n", "\n## Basis\nb\n"), "N-05"),
            ("decisions/DEC-0034-x.md", base % ("34", "promoted_to: CLAUDE.md\n", "\n## Basis\nb\n"), "F-26"),
            ("work/DEC-0035-x.md", base % ("35", "", "\n## Basis\nb\n"), "N-03"),
        ]
        for rel, text, inv in cases:
            with open(self.path(*rel.split("/")), "w") as fh:
                fh.write(text)
            found = self.invariants()
            self.assertIn(inv, found, "%s should raise %s, got %s" % (rel, inv, found))
            os.remove(self.path(*rel.split("/")))

    def test_notebook_law(self):
        self.seed()
        with open(self.path("NOTE-0040-top.md"), "w") as fh:
            fh.write("---\nid: NOTE-0040\ncreated: 2026-09-28\ncreated_by: chazz\n"
                     "updated: 2026-09-28\n---\n\n# Top\n")
        self.assertIn("N-01", self.invariants())
        os.remove(self.path("NOTE-0040-top.md"))
        self.config("notebooks: [inbox]\n")
        self.assertIn("N-02", self.invariants())

    def test_bad_config_is_reported(self):
        self.config("bogus: 1\n")
        self.assertIn("F-20", self.invariants())
        self.config("tags: [a b\n")
        self.assertIn("F-20", self.invariants())


class InstallSmokeTests(unittest.TestCase):
    """bin/init into a scratch project, then drive the INSTALLED tools with no env help."""

    def test_install_and_use(self):
        tmp = tempfile.mkdtemp()
        try:
            proj = os.path.join(tmp, "clinic")
            os.makedirs(proj)
            env = {k: v for k, v in os.environ.items()
                   if not k.startswith("RASA_")}
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            p = subprocess.run([os.path.join(ELEMENT, "bin", "init"), proj], capture_output=True,
                               text=True, env=env)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            for rel in (".claude/notes-rules.md", ".claude/notes-canon.md",
                        ".claude/schemas/notes/note.schema.json", ".claude/skills/note/SKILL.md",
                        ".claude/skills/decide/SKILL.md", ".claude/bin/notes",
                        ".claude/bin/check-notes", ".claude/bin/rasa_notes/records.py",
                        ".claude/bin/rasa_notes/FAMILY", "notes/notes.config.yml",
                        "notes/history.tsv", "notes/inbox/.keep", "notes/decisions/.keep",
                        ".claude/rasa.lock.json"):
                self.assertTrue(os.path.exists(os.path.join(proj, rel)), rel)
            for gone in (".claude/skills/sync", ".claude/skills/promote", ".claude/skills/whoami",
                         ".claude/rasa-identity.md", "kit"):
                self.assertFalse(os.path.exists(os.path.join(proj, gone)), gone)
            with open(os.path.join(proj, ".claude", "rasa.lock.json")) as fh:
                json.load(fh)
            tool = os.path.join(proj, ".claude", "bin", "notes")
            chk = os.path.join(proj, ".claude", "bin", "check-notes")
            # run from somewhere else entirely: the tool finds its own project
            r = subprocess.run([tool, "new", "Intake form ideas", "--by", "nurse1"],
                               capture_output=True, text=True, cwd=tmp, env=env)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("notes/inbox/NOTE-0001-intake-form-ideas.md", r.stdout)
            r = subprocess.run([chk], capture_output=True, text=True, cwd=tmp, env=env)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertFalse(any("__pycache__" in d for d, _, _ in
                                 os.walk(os.path.join(proj, ".claude"))))
            # re-init is non-destructive for everything the project owns
            with open(os.path.join(proj, "notes", "notes.config.yml"), "a") as fh:
                fh.write("default_actor: nurse1\n")
            p = subprocess.run([os.path.join(ELEMENT, "bin", "init"), proj], capture_output=True,
                               text=True, env=env)
            self.assertEqual(p.returncode, 0)
            with open(os.path.join(proj, "notes", "notes.config.yml")) as fh:
                self.assertIn("default_actor: nurse1", fh.read())
            with open(os.path.join(proj, "notes", "history.tsv")) as fh:
                self.assertEqual(len(fh.read().strip().split("\n")), 2)
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()

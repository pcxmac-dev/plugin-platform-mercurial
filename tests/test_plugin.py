"""Mercurial's version through the stand-in runner, the folders you name and the repositories found under them, read
from their files alone; its two changes asked from its page alone."""
from __future__ import annotations

import subprocess

import pytest

from liminal_libs.apps import asking
from liminal_libs.instances import Refusal
from liminal_libs.machines import standins

from plugin_platform_mercurial import MercurialPlugin, folders as F, repos
from stand_ins import FakeSpawn, repository, runner, share


def plugin(found=("hg",), spawn=None, pairs=None):
    r, s = runner(found, spawn)
    p = MercurialPlugin(runner=r)
    p.login = standins.login(dict(pairs or {}))
    return p, s


def as_page(p, hook, *args):
    with asking.asking(asking.PAGE):
        return getattr(p, hook)(*args)


def test_its_version_is_hg_run_once_plain_without_a_window_and_reading_no_configuration():
    p, s = plugin()
    st = p.status()
    assert st["hg"] == "6.9.4" and st["summary"].startswith("Mercurial 6.9.4")
    [(argv, kw)] = s.calls
    assert argv[1:] == ["version", "--quiet"] and kw["stdin"] is subprocess.DEVNULL and kw["timeout"] <= 5
    assert kw["env"]["HGPLAIN"] == "1" and kw["env"]["HGRCPATH"] == "" and kw["cwd"]
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        assert kw["creationflags"] & 0x08000000
    p.status()
    assert len(s.calls) == 1
    p.refresh()
    assert len(s.calls) == 2


def test_no_hg_here_is_said_and_nothing_runs():
    p, s = plugin(found=())
    assert "not on PATH" in p.status()["summary"] and s.calls == [] and p.present() is False


def test_hg_that_waits_too_long_is_said_in_words():
    p, _ = plugin(spawn=FakeSpawn({("version", "--quiet"): subprocess.TimeoutExpired("hg", 5)}))
    assert "did not answer within" in p.status()["hg"]


def test_folders_are_named_from_its_page_alone(tmp_path):
    p, _ = plugin()
    for who in ("a-harness", None):
        with asking.asking(who), pytest.raises(Refusal, match="from its page alone"):
            p.add_folder(str(tmp_path))
    as_page(p, "add_folder", str(tmp_path))
    with asking.asking("a-harness"), pytest.raises(Refusal, match="from its page alone"):
        p.remove_folder(str(tmp_path))
    as_page(p, "remove_folder", str(tmp_path))
    assert p._folders().all() == []
    with pytest.raises(Refusal, match="whole disk"):
        as_page(p, "add_folder", tmp_path.anchor)


def test_repositories_are_found_and_read_from_their_files_never_their_hgrc_run(tmp_path):
    r = repository(tmp_path, "proj", branch="stable", default="https://ciara:s3cretpass@hg.example.org/proj")
    plain = repository(tmp_path / "more", "plain", default="")
    sh = share(tmp_path, r, "proj-share")
    p, s = plugin()
    as_page(p, "add_folder", str(tmp_path))
    st = p.status()
    rows = {x[0]["sub"]: x for x in st["tables"][1]["rows"]}
    assert set(rows) == {str(r), str(plain), str(sh)}
    assert rows[str(r)][1] == "repository" and rows[str(r)][2]["text"] == "stable"
    assert rows[str(r)][3] == "default: https://ciara@hg.example.org/proj" and "s3cretpass" not in str(st)
    assert rows[str(plain)][2]["text"] == "default" and rows[str(plain)][3] == "none"
    assert rows[str(sh)][1] == "share" and rows[str(sh)][4] != "–"  # its store's changelog time
    assert [argv[1:] for argv, _ in s.calls] == [["version", "--quiet"]]  # hg was never run in one


def test_only_the_paths_section_is_read(tmp_path):
    r = repository(tmp_path, "proj")
    found = repos.read(str(r))
    assert found.paths == (("default", "https://hg.example.org/proj"),)
    assert "rm -rf" not in str(found) and "Ciara" not in str(found)


def test_the_look_is_bounded(tmp_path, monkeypatch):
    for i in range(4):
        repository(tmp_path, f"r{i}")
    monkeypatch.setattr(F, "MAX_FOUND", 2)
    assert len(F.look([str(tmp_path)], repos.kind_of).found) == 2


def test_its_facts_ask_nothing():
    p, s = plugin()
    assert p.api_facts() == {}
    p.status()
    n = len(s.calls)
    assert p.api_facts()["Mercurial's command line"]["Mercurial"].startswith("6.9.4 at ") and len(s.calls) == n

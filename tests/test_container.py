"""hg serve in a container, through a container plugin's plans (the library's ContainedService), on the library's
stand-ins alone: no docker, no process, no socket, no download. Its image is built here (liminal-libs 1.97.0's build
plan): Install… is offered, its plan says what is fetched and built, and a stand-in wheel stands in for Mercurial's; with a
test's pin, it installs read-only, on this PC alone, and Expose… is refused (hg serve has no sign-in of its own)."""
from __future__ import annotations

import hashlib
import re

import pytest

from liminal_libs.instances import Refusal
from liminal_libs.machines.containedservice import UNREAD
from liminal_libs.machines.servicestandins import ServiceWorld, quick_pace

from plugin_platform_mercurial import MercurialPlugin, recipe
from stand_ins import runner

PIN = {"linux": {"server": dict(ref="docker.io/example/hg-serve:6.9", digest="sha256:" + "f" * 64, size=60_000_000,
                                system="linux", platforms=["linux/amd64"], version="6.9", licence="GPL-2.0",
                                page="https://hub.docker.com/r/example/hg-serve", tar=True)}}


def world(tmp_path, pins=PIN, files=None):
    p = MercurialPlugin(runner=runner()[0], pace=quick_pace(), pins=pins)
    return ServiceWorld(p, folder=tmp_path, files=files), p


WHEEL = b"a stand-in for Mercurial's wheel " * 32


@pytest.fixture
def stand_in_wheel(monkeypatch):
    """Its BUILD with a stand-in wheel's sha256 and size (the real wheel is never downloaded in a test)."""
    wheel = {**recipe.BUILD["linux"]["wheel"], "sha256": hashlib.sha256(WHEEL).hexdigest(), "size": len(WHEEL)}
    monkeypatch.setitem(recipe.BUILD, "linux", {**recipe.BUILD["linux"], "wheel": wheel})
    return {wheel["url"]: WHEEL}


def test_its_image_is_built_here_and_install_is_offered(tmp_path):
    assert recipe.PINS == {}
    w, p = world(tmp_path, pins=None)
    w.grant()
    [t] = w.service.hosts(fresh=True)["plugins"][0]["targets"]
    assert t["offer"] == "" and t["fit"]["takes"] == ""
    spec = recipe.spec("linux", "hgserve", {})
    b = spec.parts[0].build
    assert b.tag == "liminal/mercurial-server:7.2.4-py3.13.18" and b.base.digest == recipe.BUILD["linux"]["base"]["digest"]
    assert [f.name for f in b.files] == [recipe.BUILD["linux"]["wheel"]["name"]]
    answer = w.ask("service_install", w.HOST, w.TARGET, "hgserve", "no")
    words = w.page(w.HOST, "plan_words", answer["plan"])
    assert "accept_build" in [a["name"] for a in words["accepts"]]
    step = next(s for s in words["steps"] if s.startswith("build liminal/mercurial-server"))
    assert "fetch mercurial-7.2.4-cp313" in step and "files.pythonhosted.org" in step and recipe.dockerfile().strip() in step
    assert w.fetch.asked == [] and w.fake.changes() == []
    with pytest.raises(Refusal, match="hg serve's image is built here for Linux alone"):
        recipe.spec("windows", "hgserve", {})


def test_it_is_built_from_its_two_pins_alone_and_installed(tmp_path, stand_in_wheel):
    w, p = world(tmp_path, pins=None, files=stand_in_wheel)
    end = w.install("hgserve", "no")
    assert end["ok"], end
    [b] = w.fake.builds
    name = recipe.BUILD["linux"]["wheel"]["name"]
    assert set(b["files"]) == {"Dockerfile", name} and b["files"][name] == WHEEL
    assert b["dockerfile"] == recipe.dockerfile() and b["tag"] == "liminal/mercurial-server:7.2.4-py3.13.18"
    base = recipe.BUILD["linux"]["base"]
    assert any(f"{base['ref']}@{base['digest']}" in " ".join(a) for a in w.fake.argv_of("pull"))
    c = w.fake.containers["liminal-mercurial-hgserve-server"]
    assert c["image"] == b["id"] and c["labels"]["liminal.built"] == b["id"]
    assert p.placement("hgserve")["image"] == {"server": b["id"]}
    with pytest.raises(Refusal, match="runs this plugin's pins already"):
        w.ask("service_change", "update", "hgserve")


def test_its_build_pins_are_read_and_its_dockerfile_reaches_nothing():
    b = recipe.BUILD["linux"]
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", b["base"]["digest"]) and b["base"]["digest"] != UNREAD
    assert re.fullmatch(r"[0-9a-f]{64}", b["wheel"]["sha256"]) and b["wheel"]["size"] > 0
    assert b["wheel"]["name"].startswith("mercurial-7.2.4-cp313-cp313-manylinux") and "3.13" in b["base"]["ref"]
    assert b["wheel"]["url"].startswith("https://files.pythonhosted.org/") and b["wheel"]["url"].endswith(b["wheel"]["name"])
    d = recipe.dockerfile()
    assert d.startswith(f"FROM docker.io/library/python@{b['base']['digest']}\n")
    assert f"COPY {b['wheel']['name']} " in d and "--no-index --no-deps" in d and f"USER {recipe.UID}" in d
    assert "http" not in d and "apt-get" not in d and "curl" not in d


def test_an_unread_pin_is_refused(tmp_path):
    unread = {"linux": {"server": {**PIN["linux"]["server"], "digest": UNREAD}}}
    w, p = world(tmp_path, pins=unread)
    w.grant()
    with pytest.raises(Refusal, match="not pinned by digest yet"):
        w.ask("service_install", w.HOST, w.TARGET, "hgserve", "no")


def test_it_installs_read_only_on_this_pc_alone(tmp_path):
    w, p = world(tmp_path)
    w.grant()
    with pytest.raises(Refusal, match="this PC alone first"):
        w.ask("service_install", w.HOST, w.TARGET, "hgserve", "yes")
    end = w.install("hgserve", "no")
    assert end["ok"], end
    conf = w.fake.volumes["liminal-mercurial-hgserve-repos"]["files"][recipe.WEB_CONF].decode()
    assert "allow-push =\n" in conf and "push_ssl = true" in conf and "/ = /srv/hg/**" in conf
    [made] = w.fake.argv_of("create")
    said = " ".join(made)
    assert "-p 127.0.0.1:8000:8000/tcp" in said and "hg init /srv/hg/main" in said and "--web-conf" in said
    assert any("hg clone http://127.0.0.1:8000/main" in line for line in end["lines"])


def test_expose_is_refused_it_has_no_sign_in(tmp_path):
    w, p = world(tmp_path)
    assert w.install("hgserve", "no")["ok"]
    with pytest.raises(Refusal, match="no sign-in of its own"):
        w.ask("service_change", "expose", "hgserve", "on")

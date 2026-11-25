"""hg serve in a container, through a container plugin's plans (the library's ContainedService), on the library's
stand-ins alone: no docker, no process, no socket. No image is pinned in this release, so Install… refuses in words; with
a test's pin, it installs read-only, on this PC alone, and Expose… is refused (hg serve has no sign-in of its own)."""
from __future__ import annotations

import pytest

from liminal_libs.instances import Refusal
from liminal_libs.machines.containedservice import UNREAD
from liminal_libs.machines.servicestandins import ServiceWorld, quick_pace

from plugin_platform_mercurial import MercurialPlugin, recipe
from stand_ins import runner

PIN = {"linux": {"server": dict(ref="docker.io/example/hg-serve:6.9", digest="sha256:" + "f" * 64, size=60_000_000,
                                system="linux", platforms=["linux/amd64"], version="6.9", licence="GPL-2.0",
                                page="https://hub.docker.com/r/example/hg-serve", tar=True)}}


def world(tmp_path, pins=PIN):
    p = MercurialPlugin(runner=runner()[0], pace=quick_pace(), pins=pins)
    return ServiceWorld(p, folder=tmp_path), p


def test_no_image_is_pinned_and_install_says_so(tmp_path):
    assert recipe.PINS == {}
    w, p = world(tmp_path, pins=None)
    w.grant()
    with pytest.raises(Refusal, match="its recipe has no linux image"):
        w.ask("service_install", w.HOST, w.TARGET, "hgserve", "no")
    with pytest.raises(Refusal, match="no image pinned yet"):
        recipe.spec("linux", "hgserve", {}, None)


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

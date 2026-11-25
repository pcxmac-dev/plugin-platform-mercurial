"""hg serve's recipe for a container (0.1.0; Monday list item 35, with the user's answers of 2026-11-23 and 2026-11-25:
every server in a container through the container plugin you pick, a seeded sign-in, this PC alone first, then
Expose…, images pinned by digest).

One part, `server`: `hg serve` on 8000, its repositories in the `repos` volume (/srv/hg), served by hgweb from a
configuration seeded into the new volume (.liminal/hgweb.config: every repository under /srv/hg, pushes refused); a
first repository, `main`, made at the first start (hg init).

Two things hold it back, both said on its page:
- **No image is pinned.** Mercurial's makers publish no image of hg serve, and no maintained one was found on Docker
  Hub for this release (heptapod/heptapod, the one maintained image with Mercurial, is a whole GitLab, not hg serve):
  PINS is empty and Install… refuses in words until a release pins one (an image with /bin/sh and hg on PATH; a choice
  that is yours: such an image, heptapod, or one built here from pinned downloads, as decision 14 has it for the CI
  servers).
- **hg serve has no sign-in of its own** (Mercurial's own words: it is for quick sharing; a sign-in is a web server's
  in front of hgweb). So it is read-only and stays on this PC: Expose… is refused (lan_ready), and a push is refused
  by its configuration (allow-push empty)."""
from __future__ import annotations

from collections.abc import Mapping

from liminal_libs.instances import Refusal
from liminal_libs.machines.containers import ServiceSpec

OWNER = "mercurial"
WEB_PORT = 8000
MEMORY_MB = 256
WEB_CONF = ".liminal/hgweb.config"  # inside the repos volume
PINS: dict = {}  # none pinned yet (the module's docstring)
NO_IMAGE = ("hg serve has no image pinned yet: Mercurial's makers publish none and no maintained one was found, so "
            "nothing is installed until a release pins one (yours to choose)")
NO_SIGN_IN = ("hg serve has no sign-in of its own (a web server in front of hgweb gives one): it stays on this PC, "
              "read-only")
HGWEB = """# seeded by Liminal (plugin-platform-mercurial 0.1.0) into a new volume, once: yours from then on
[paths]
/ = /srv/hg/**
[web]
allow-push =
push_ssl = true
allow-archive =
"""
START = "; ".join((
    "set -eu",
    "[ -d /srv/hg/main/.hg ] || hg init /srv/hg/main",
    f"exec hg serve --web-conf /srv/hg/{WEB_CONF} --address 0.0.0.0 --port {WEB_PORT}"))


def spec(system: str, name: str, options: Mapping, pins: Mapping | None = None) -> ServiceSpec:
    """hg serve's spec for a system (Linux alone), from `pins` (PINS unless a test's)."""
    pins = pins if pins is not None else PINS
    if system not in pins:
        raise Refusal(NO_IMAGE if not pins else f"hg serve has no {system} image")
    fit = bool(options.get("fit"))
    ports = list(options.get("ports") or [])
    host = int(ports[0]) if ports else WEB_PORT
    server = {
        "name": "server", "image": dict(pins[system]["server"]),
        "ports": [{"name": "web", "container": WEB_PORT, "host": host, "lan": bool(options.get("lan")),
                   "about": "hgweb: browse, clone and pull (no push)"}],
        "volumes": [{"name": "repos", "path": "/srv/hg", "holds": "its repositories and its configuration",
                     "owner": None}],
        "seeds": [] if fit else [{"volume": "repos", "path": WEB_CONF, "text": HGWEB, "mode": 0o644}],
        "env": {"HGPLAIN": "1"},
        "command": ["/bin/sh", "-c", START],
        "memory": (int(options.get("memory_mb") or 0) or MEMORY_MB) << 20,
        "health": {"port": "web", "path": "/", "ready_s": 60}, "stop_s": 10}
    return ServiceSpec.of({"owner": OWNER, "name": name, "title": "hg serve", "system": system, "parts": [server]})

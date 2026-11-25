"""hg serve's recipe for a container (0.1.0; Monday list item 35, with the user's answers of 2026-11-23 and 2026-11-25:
every server in a container through the container plugin you pick, a seeded sign-in, this PC alone first, then
Expose…, images pinned by digest).

One part, `server`: `hg serve` on 8000, its repositories in the `repos` volume (/srv/hg), served by hgweb from a
configuration seeded into the new volume (.liminal/hgweb.config: every repository under /srv/hg, pushes refused); a
first repository, `main`, made at the first start (hg init).

Two things are its own, both said on its page:
- **Its image is built here** (the user, 2026-11-25: "Build one here"): Mercurial's makers publish no image of hg serve
  and no maintained one was found, so `BUILD` says one made on this PC from two pins read on 2026-11-25, nothing
  downloaded then: the Python base image by its amd64 manifest's digest (Docker Hub) and Mercurial's wheel by its
  sha256 (PyPI's JSON API), with the Dockerfile that joins them (`dockerfile()`: the wheel installed with no index and
  no dependency, a user of its own, uid 1000). Since 0.2.0 the part says them as the library's build pin (liminal-libs
  1.97.0's `containers.BuildPin`, `build_pin()`): its container plugin's plan says the base pulled by digest, the wheel
  fetched from files.pythonhosted.org and checked by its sha256, and the Dockerfile whole, and asks accept_build;
  nothing is fetched or built before your approval. PINS (a maker's image by digest) stays empty: a test's alone.
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
PINS: dict = {}  # none: its image is built here (BUILD); a test may hand a maker's image instead
UID = 1000  # the image's own user, made by DOCKERFILE
BUILD = {  # read 2026-11-25; nothing downloaded then
    "linux": {
        "base": dict(ref="docker.io/library/python:3.13.18-slim-trixie",
                     index="sha256:7249d5587b78209a006dc4a3b5340678f84ea729239193aa559962cd8c1fce50",
                     digest="sha256:e123d49d13f666b842ae2b925bf30703910481c67c89edc0a6b42e09d2b2168d",  # linux/amd64
                     platform="linux/amd64", size=43062348, licence="PSF-2.0 (Python); Debian's (trixie)",
                     page="https://hub.docker.com/_/python"),
        "wheel": dict(name="mercurial-7.2.4-cp313-cp313-manylinux_2_17_x86_64.manylinux2014_x86_64.manylinux_2_28_x86_64.whl",
                      url=("https://files.pythonhosted.org/packages/7a/8c/09072956ebd5ea250d43818ac2c688deb96939b5ed16beac"
                           "99e07764c5a4/mercurial-7.2.4-cp313-cp313-manylinux_2_17_x86_64.manylinux2014_x86_64."
                           "manylinux_2_28_x86_64.whl"),
                      sha256="75a2277a5691d28fa2a5a791e033f0c2b72a09b9ac9b83ebd8d3dd736c114729", size=7587835,
                      version="7.2.4", licence="GPL-2.0-or-later", page="https://pypi.org/project/mercurial/7.2.4/"),
        "version": "7.2.4-py3.13.18",  # tagged liminal/mercurial-server:<version> (the library's rule)
    },
}
NO_IMAGE = "hg serve's image is built here for Linux alone: no Windows one"
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


def build_pin(system: str = "linux") -> dict:
    """The server part's build pin (liminal-libs 1.97.0's containers.BuildPin), from BUILD and dockerfile()."""
    b = BUILD[system]
    base, wheel = b["base"], b["wheel"]
    return {"base": {"ref": base["ref"], "digest": base["digest"], "system": system, "platforms": [base["platform"]],
                     "size": base["size"], "licence": base["licence"], "page": base["page"]},
            "files": [{k: wheel[k] for k in ("name", "url", "sha256", "size", "licence", "page")}],
            "dockerfile": dockerfile(system), "tag": f"liminal/{OWNER}-server:{b['version']}", "version": b["version"],
            "licence": f"{wheel['licence']} (Mercurial {wheel['version']}); {base['licence']}",
            "page": "https://www.mercurial-scm.org/", "tar": True}


def dockerfile(system: str = "linux") -> str:
    """The Dockerfile its image is built from: the base by digest, the wheel copied in (the one pinned file of its
    context, checked by its sha256 before the build) and installed with no index and no dependency, then a user of its
    own. Nothing in it reaches the network."""
    b = BUILD[system]
    wheel = b["wheel"]["name"]
    return "\n".join((
        f"FROM {b['base']['ref'].rsplit(':', 1)[0]}@{b['base']['digest']}",
        f"COPY {wheel} /tmp/{wheel}",
        f"RUN python -m pip install --no-index --no-deps --no-cache-dir /tmp/{wheel} && rm /tmp/{wheel} \\",
        f"    && useradd --uid {UID} --create-home --shell /usr/sbin/nologin hg && install -d -o hg -g hg /srv/hg",
        "ENV HGPLAIN=1",
        f"USER {UID}",
        "WORKDIR /srv/hg",
        f"EXPOSE {WEB_PORT}/tcp",
        ""))


START = "; ".join((
    "set -eu",
    "[ -d /srv/hg/main/.hg ] || hg init /srv/hg/main",
    f"exec hg serve --web-conf /srv/hg/{WEB_CONF} --address 0.0.0.0 --port {WEB_PORT}"))


def spec(system: str, name: str, options: Mapping, pins: Mapping | None = None) -> ServiceSpec:
    """hg serve's spec for a system (Linux alone): its image built here (BUILD), or a test's pinned image (`pins`)."""
    pins = pins if pins is not None else PINS
    if system in pins:
        image = {"image": dict(pins[system]["server"])}
    elif system in BUILD:
        image = {"build": build_pin(system)}
    else:
        raise Refusal(NO_IMAGE)
    fit = bool(options.get("fit"))
    ports = list(options.get("ports") or [])
    host = int(ports[0]) if ports else WEB_PORT
    server = {
        "name": "server", **image,
        "ports": [{"name": "web", "container": WEB_PORT, "host": host, "lan": bool(options.get("lan")),
                   "about": "hgweb: browse, clone and pull (no push)"}],
        "volumes": [{"name": "repos", "path": "/srv/hg", "holds": "its repositories and its configuration",
                     "owner": UID}],
        "seeds": [] if fit else [{"volume": "repos", "path": WEB_CONF, "text": HGWEB, "mode": 0o644}],
        "env": {"HGPLAIN": "1"},
        "command": ["/bin/sh", "-c", START],
        "memory": (int(options.get("memory_mb") or 0) or MEMORY_MB) << 20,
        "health": {"port": "web", "path": "/", "ready_s": 60}, "stop_s": 10}
    return ServiceSpec.of({"owner": OWNER, "name": name, "title": "hg serve", "system": system, "parts": [server]})

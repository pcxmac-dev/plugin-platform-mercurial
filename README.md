# plugin-platform-mercurial

Mercurial for Liminal, one of the platform's Source Control plugins (Monday list item 35). `SECTION` "scm", icon
`mercurial`.

## What it does

- **Mercurial's version**: `hg version --quiet`, run once per look without a window, outside any repository, plain
  (HGPLAIN) and reading no configuration file (HGRCPATH empty), five seconds at most.
- **The folders you name** on its page (Add a folder…, Remove…), kept through the login as `MERCURIAL_FOLDERS`: an
  absolute path to a folder that is there, never a drive's or the file system's root, 16 at most. It looks four
  folders down at most, follows no link (symbolic link, junction), steps over `node_modules`, `.venv` and the like,
  and never goes into what it found. Nothing is ever looked for across a whole disk.
- **Each repository read from its own files** (`repos.py`): repositories and shares; the branch from `.hg/branch`,
  the paths from `.hg/hgrc`'s [paths] section alone (as text, each address without a password), when it changed from
  its changelog's time. hg is never run in a repository: its hgrc can name extensions and hooks hg would run.
- **hg serve in a container** (`recipe.py`, the library's ContainedService): read-only (pushes refused by a seeded
  hgweb.config), its repositories in a volume (/srv/hg), a first repository `main` made at its first start, on this
  PC alone (127.0.0.1:8000). hg serve has no sign-in of its own, so Expose… is always refused.

## Its image, built here

Mercurial's makers publish no image of hg serve, and no maintained one was found on Docker Hub (heptapod/heptapod is
a whole GitLab with Mercurial, not hg serve). The user's answer of 2026-11-25, "Build one here": `recipe.BUILD` names
an image made on this PC from two pins, both read on 2026-11-25 with nothing downloaded:

- the base, `docker.io/library/python:3.13.18-slim-trixie`, by its linux/amd64 manifest's digest
  `sha256:e123d49d…d2b2168d` (its index `sha256:7249d558…8c1fce50`; 43.1 MB compressed), read from Docker Hub;
- Mercurial 7.2.4's wheel for CPython 3.13 on manylinux x86_64 (GPL-2.0-or-later, 7.6 MB), by its sha256
  `75a2277a…8c114729`, read from PyPI's JSON API.

`recipe.dockerfile()` joins them: `FROM` the base by digest, the wheel copied in (the build context's one file, checked
against its sha256 first) and installed with `--no-index --no-deps`, a user `hg` of uid 1000 owning `/srv/hg`,
`HGPLAIN=1`. Nothing in it reaches the network. Since 0.2.0 the server part says them as liminal-libs 1.97.0's build
pin (`recipe.build_pin()`, tagged `liminal/mercurial-server:7.2.4-py3.13.18`), so **Install… is offered** on a
container plugin that builds images (Docker 0.5.0): its plan says the base pulled by digest, the wheel fetched from
files.pythonhosted.org and checked by its sha256, and the Dockerfile whole, and asks `accept_build`; nothing is fetched
or built before your approval, and the same pins are never built twice.

## Tests

Stand-ins alone: no hg, docker or network is run or reached (`tests/conftest.py` refuses every process and
connection while a test runs). Run them with the library on the path:

    PYTHONPATH="src;<liminal-libs>/src" python -m pytest -q -p no:cacheprovider

`LIMINAL_VENDOR_PAGES=1` lets `tests/test_apis.py` ask every address on its API cards once (the only test that reaches
the network). Each gate was taken out once and a test seen to fail.

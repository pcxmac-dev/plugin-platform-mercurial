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

## No image yet

Mercurial's makers publish no image of hg serve, and no maintained one was found on Docker Hub (heptapod/heptapod is
a whole GitLab with Mercurial, not hg serve). `PINS` is empty: **Install… refuses in words until a release pins one**
(an image with /bin/sh and hg on PATH). Which image is yours to choose.

## Tests

Stand-ins alone: no hg, docker or network is run or reached (`tests/conftest.py` refuses every process and
connection while a test runs). Run them with the library on the path:

    PYTHONPATH="src;<liminal-libs>/src" python -m pytest -q -p no:cacheprovider

`LIMINAL_VENDOR_PAGES=1` lets `tests/test_apis.py` ask every address on its API cards once (the only test that reaches
the network). Each gate was taken out once and a test seen to fail.

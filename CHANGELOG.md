# Changelog

## 0.2.0 (2026-11-25)

hg serve's image built here, on liminal-libs 1.97.0's build plan (SERVICE-INTERFACE.md §10). Needs liminal-libs>=1.97.0.
- Its server part says `build` (`recipe.build_pin()`: the Python base by its amd64 manifest's digest, Mercurial
  7.2.4's wheel by its sha256, the Dockerfile that joins them, tagged liminal/mercurial-server:7.2.4-py3.13.18) in
  place of an image, so **Install… is offered** on a container plugin that builds images (Docker 0.5.0) and not where
  none does ("not yet: this container plugin builds no image"). Its plan says the base pulled by digest, the wheel
  fetched from files.pythonhosted.org and checked, the Dockerfile whole, and asks accept_build; nothing is fetched or
  built before your approval, and the same pins are never built twice.
- 0.1.0's refusal ("waits for the library's build plan") is gone.

## 0.1.0 (2026-11-25)

The first release (Monday list item 35, the Source Control class of platform plugins; SECTION "scm", drawn by liminal-platform 0.39.0). Mercurial's version, the repositories under the folders you name (read from their files alone), and hg serve's recipe (read-only, this PC alone, never exposed: no sign-in of its own); no image is pinned yet, so Install… refuses until one is.

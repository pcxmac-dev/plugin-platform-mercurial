"""Mercurial for Liminal, one of the platform's Source Control plugins (Monday list item 35; the user, 2026-11-22:
"add github, gitlab and Subversion, Mercurial open source installable popular version control software"). Its SECTION is
"scm": a platform that draws that section (0.39.0) shows it under Source Control plugins, an older one under Machine
plugins.

What it reads, when the platform asks and never on its own:
- Mercurial's version (`hg version --quiet`, run without a window, outside any repository, reading no configuration
  file: tool.py);
- the repositories under the folders you name on its page (folders.py: never across a whole disk), each read from its
  own files alone (repos.py): its branch, its paths (without a password in their addresses) and when it changed.
  What was read is kept READ_S; Read again looks now.

What it changes, from its page alone (PAGE_ONLY_HOOKS, and checked again inside each): the folders it looks under
(kept through the login as MERCURIAL_FOLDERS); and hg serve, installed, started, stopped and removed only as a
container, through the container plugin you pick, in that plugin's plans you approve (the library's ContainedService):
read-only, on this PC alone (hg serve has no sign-in of its own, so Expose… is refused). Its image is built here from
two pins (recipe.BUILD: a Python base by digest, Mercurial's wheel by sha256), and Install… refuses in words until the
library has a build plan (SERVICE-INTERFACE.md §10). No repository here is touched."""
from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from liminal_libs.apps import asking
from liminal_libs.instances import Refusal
from liminal_libs.machines.containedservice import ContainedService, Pace

from . import apis as cards
from . import folders as F
from . import recipe, repos
from .tool import Runner, ToolError, version_of

__version__ = "0.1.0"
READ_S = 30.0
ROWS = 200
FOLDERS = "MERCURIAL_FOLDERS"


def local(seconds: float) -> str:
    if not seconds:
        return "–"
    try:
        return datetime.fromtimestamp(seconds, timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
    except (OSError, OverflowError, ValueError):
        return "–"


@dataclass(frozen=True)
class Reading:
    at: float
    when: float
    folders: tuple[str, ...]
    path: str = ""
    version: str = ""
    trouble: str = ""
    found: tuple = field(default=())
    notes: tuple[str, ...] = ()


class MercurialPlugin(ContainedService):
    """Mercurial here: its version, the repositories under your folders, and hg serve in a container."""

    name = "mercurial"
    title = "Mercurial"
    about = ("Mercurial on this machine: its version and the repositories under the folders you name, each read from its "
             "own files; hg serve (read-only, this PC alone) run in a container through the plugin you pick")
    api = "2.2"
    apis = cards.APIS
    order = 784
    ICON = "mercurial"
    SECTION = "scm"
    SERVICE = "hgserve"
    LAN_FIRST = False  # this PC alone (hg serve has no sign-in of its own: never exposed)
    DEFAULT_MEMORY_MB = recipe.MEMORY_MB
    HOOKS = (*ContainedService.HOOKS, "refresh", "add_folder", "remove_folder")
    READ_HOOKS = ("refresh",)
    PAGE_ONLY_HOOKS = ("add_folder", "remove_folder")
    INTERNAL_NOTES = (
        "hg is run for its version alone (hg version --quiet), without a window, outside any repository and reading no "
        "configuration file; a repository is read from its own files, so its hgrc never makes hg run code.",
        f"Repositories are looked for under the folders you name alone ({FOLDERS}, through the login): never across a "
        f"whole disk, {F.MAX_DEPTH} folders down at most, no link followed.",
        "Its folders and hg serve's changes are its page's alone (PAGE_ONLY_HOOKS); hg serve runs only as a container, in "
        "a container plugin's plans you approve, read-only and on this PC alone.",
    )
    keys = ()

    def __init__(self, runner: Runner | None = None, pace: Pace | None = None, pins=None, clock=None, wall=None):
        ContainedService.__init__(self, pace)
        self._runner = runner or Runner()
        self._pins = pins
        self._clock = clock or time.monotonic
        self._wall = wall or time.time
        self._lock = threading.Lock()
        self._reading: Reading | None = None

    @property
    def KEEPS(self):  # noqa: N802 - read as a declared word
        return (*ContainedService.KEEPS.fget(self), (FOLDERS, "the folders its repositories are looked for under"))

    # -- reading -------------------------------------------------------------------------------------------------------
    def _folders(self) -> F.Folders:
        return F.Folders(FOLDERS, lambda: self.login)

    def _read(self, fresh: bool = False) -> Reading:
        folders = tuple(self._folders().all())
        with self._lock:
            kept = self._reading
        if kept is not None and not fresh and kept.folders == folders and self._clock() - kept.at < READ_S:
            return kept
        path = self._runner.find("hg")
        version, trouble = "", ""
        if path:
            try:
                ran = self._runner.run("hg", "version", "--quiet")
                version = version_of(ran.out) if ran.code == 0 else ""
                trouble = "" if version else f"hg version said nothing of a version ({(ran.err or ran.out)[:120]})"
            except ToolError as e:
                trouble = str(e)
        look = F.look(list(folders), repos.kind_of)
        found = tuple(repos.read(p, k) for p, k in look.found)
        r = Reading(self._clock(), self._wall(), folders, path, version, trouble, found, tuple(look.notes))
        with self._lock:
            self._reading = r
        return r

    def _forget(self) -> None:
        with self._lock:
            self._reading = None

    # -- hg serve (ContainedService) ------------------------------------------------------------------------------------
    def spec_for(self, system, name, options):
        """hg serve's recipe (recipe.py): read-only, its repositories in a volume."""
        return recipe.spec(system, name, options, self._pins)

    def lan_ready(self, hosted):
        """Never: hg serve has no sign-in of its own, so it stays on this PC."""
        return False, recipe.NO_SIGN_IN

    def after(self, action, hosted, line):
        """After its install: where it is browsed and cloned."""
        if action != "install":
            return []
        at = self.address(hosted) or f"http://127.0.0.1:{recipe.WEB_PORT}"
        return [f"browse it at {at}/; clone its first repository: hg clone {at}/main (read-only: pushes are refused)"]

    def detach(self) -> None:
        self._forget()
        super().detach()

    # -- the hooks -------------------------------------------------------------------------------------------------------
    def present(self) -> bool:
        """Whether hg is on PATH here, or hg serve is placed in a container."""
        return self.service_present() or bool(self._runner.find("hg"))

    def refresh(self) -> dict:
        """Mercurial and the folders looked at again now."""
        r = self._read(fresh=True)
        return {"said": self._summary(r), "ok": True, "lines": list(r.notes) or [f"{len(r.found)} repositories"]}

    def _page(self, hook: str) -> None:
        who = asking.asker()
        if who != asking.PAGE:
            raise Refusal(f"mercurial's {hook} is yours, from its page alone: {who or 'no one'} asked it")

    def add_folder(self, path) -> dict:
        """A folder its repositories are looked for under, added from its page alone (kept through the login)."""
        self._page("add_folder")
        added, where = self._folders().add(path)
        self._forget()
        return {"said": f"{added} is looked under now", "ok": True, "lines": [f"kept in {where}"]}

    def remove_folder(self, path) -> dict:
        """A folder taken off its list, from its page alone: nothing on the disk is touched."""
        self._page("remove_folder")
        gone, where = self._folders().remove(path)
        self._forget()
        return {"said": f"{gone} is no longer looked under (nothing on the disk was touched)", "ok": True,
                "lines": [f"kept in {where}"]}

    def api_facts(self) -> dict:
        """What it learned while it ran, asking nothing."""
        with self._lock:
            r = self._reading
        if r is None:
            return {}
        return {cards.CLI: {"Mercurial": f"{r.version} at {r.path}" if r.version else (r.trouble or "not on PATH here"),
                            "Read": local(r.when)},
                cards.FILES: {"Folders": str(len(r.folders)), "Repositories": str(len(r.found))}}

    # -- the page --------------------------------------------------------------------------------------------------------
    @staticmethod
    def _summary(r: Reading) -> str:
        hg = (f"Mercurial {r.version}" if r.version else
              ("hg is not on PATH here" if not r.path else "Mercurial (its version not read)"))
        if not r.folders:
            return f"{hg} · no folder named to look for repositories under"
        return f"{hg} · {len(r.found)} repositories under {len(r.folders)} folders"

    def status(self) -> dict:
        """Mercurial's version, the folders and their repositories, and hg serve's containers."""
        r = self._read()
        out: dict = {"present": bool(r.path) or self.service_present(), "summary": self._summary(r),
                     "valid": self.service_valid() or bool(r.path), "why": "",
                     "hg": r.version or r.trouble or "not on PATH here", "folders": len(r.folders),
                     "repositories": len(r.found), "readAt": f"{local(r.when)} (kept {READ_S:g} s; Read again looks now)"}
        if r.trouble:
            out["note"] = r.trouble
        out["tables"] = [self._folders_table(r), self._repos_table(r)]
        out["forms"] = self._forms(r)
        out["actions"] = [{"hook": "refresh", "args": [], "title": "Read again", "note": "looks at hg and the folders now"},
                          {"form": "add_folder", "title": "Add a folder…"}]
        if self.app is not None:
            svc = self.service_status()
            out["tables"] += svc.get("tables") or []
            out["forms"] += svc.get("forms") or []
        return out

    @staticmethod
    def _folders_table(r: Reading) -> dict:
        rows = [[f, {"form": "remove_folder", "title": "Remove…", "values": {"path": f}}] for f in r.folders]
        return {"title": "Folders looked under", "columns": [{"title": "Folder"}, {"title": "Remove"}], "rows": rows,
                "empty": "No folder yet: Add a folder… names one (repositories are never looked for across a disk).",
                "note": f"{F.MAX_DEPTH} folders down at most; no link followed; "
                        + ("; ".join(r.notes) if r.notes else "everything under them looked at")}

    @staticmethod
    def _repos_table(r: Reading) -> dict:
        rows = []
        for x in r.found[:ROWS]:
            paths = ", ".join(f"{n}: {u}" for n, u in x.paths) or "none"
            rows.append([{"text": os.path.basename(x.path) or x.path, "sub": x.path}, x.kind,
                         {"text": x.branch, "sub": x.why or None}, paths, local(x.changed)])
        note = "read from each repository's files: hg is never run in one"
        if len(r.found) > ROWS:
            note += f" · the first {ROWS} of {len(r.found):,}"
        return {"title": "Repositories", "columns": [{"title": "Repository"}, {"title": "Kind"}, {"title": "Branch"},
                                                     {"title": "Paths"}, {"title": "Changed"}],
                "rows": rows, "note": note, "empty": "None found under the folders named."}

    @staticmethod
    def _forms(r: Reading) -> list[dict]:
        forms = [{"id": "add_folder", "hook": "add_folder", "title": "Add a folder to look under", "submit": "Review",
                  "fields": [{"name": "path", "label": "Folder", "type": "text", "value": "",
                              "placeholder": r"C:\Users\you\source"}],
                  "confirm": {"title": "Look for repositories under {path}?",
                              "words": "Its folders are looked at, four down at most, each time the page reads; nothing "
                                       "in them is changed.", "yes": "Add it"}}]
        if r.folders:
            forms.append({"id": "remove_folder", "hook": "remove_folder", "title": "Stop looking under a folder",
                          "fields": [{"name": "path", "label": "Folder", "type": "fixed"}],
                          "confirm": {"title": "Stop looking under {path}?", "words": "Nothing on the disk is touched.",
                                      "yes": "Remove it"}})
        return forms


MACHINE = MercurialPlugin()

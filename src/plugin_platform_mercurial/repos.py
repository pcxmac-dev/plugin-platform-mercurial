"""A Mercurial repository found under a folder you named, read from its own files alone: no hg is run in it. Running hg
in a repository reads that repository's .hg/hgrc, whose [extensions] and [hooks] can name Python code and programs hg
then runs, so this plugin never does: its branch is read from .hg/branch, its paths from .hg/hgrc's [paths] (as text:
nothing in it is run), its last change from its changelog's time. An address is said without a password in it."""
from __future__ import annotations

import configparser
import os
import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit, urlunsplit

MOST_READ = 64 * 1024
REPOSITORY, SHARED = "repository", "share"


def _read(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return f.read(MOST_READ).decode("utf-8", "replace")
    except OSError:
        return ""


def kind_of(path: str) -> str:
    dot = os.path.join(path, ".hg")
    if not os.path.isdir(dot):
        return ""
    if os.path.isfile(os.path.join(dot, "sharedpath")):
        return SHARED
    if os.path.isfile(os.path.join(dot, "requires")) or os.path.isfile(os.path.join(dot, "00changelog.i")):
        return REPOSITORY
    return ""


def bare_address(url: str) -> str:
    """An address without a password in it (https://user:pw@host/x -> https://user@host/x)."""
    text = str(url or "").strip()
    if "://" not in text:
        return text
    try:
        parts = urlsplit(text)
    except ValueError:
        return "an address not read"
    if "@" not in parts.netloc:
        return text
    who, host = parts.netloc.rsplit("@", 1)
    who = who.split(":", 1)[0]
    return urlunsplit((parts.scheme, f"{who}@{host}" if who else host, parts.path, parts.query, parts.fragment))


@dataclass(frozen=True)
class Repo:
    path: str
    kind: str
    branch: str = "default"
    paths: tuple[tuple[str, str], ...] = field(default=())
    requires: tuple[str, ...] = ()
    changed: float = 0.0
    why: str = ""


def _paths(hgrc: str) -> tuple[tuple[str, str], ...]:
    # only the [paths] section's lines are given to the parser: an %include or a continuation elsewhere never matters
    lines, inside = [], False
    for line in hgrc.splitlines():
        head = re.match(r"\s*\[([^\]]+)\]", line)
        if head:
            inside = head.group(1).strip() == "paths"
            continue
        if inside and re.match(r"\s*[^#;%\s][^=]*=", line):
            lines.append(line.strip())
    parser = configparser.RawConfigParser(strict=False, interpolation=None)
    try:
        parser.read_string("[paths]\n" + "\n".join(lines))
    except configparser.Error:
        return ()
    return tuple((k, bare_address(v)) for k, v in list(parser.items("paths"))[:8])


def read(path: str, kind: str = "") -> Repo:
    kind = kind or kind_of(path)
    dot = os.path.join(path, ".hg")
    branch = _read(os.path.join(dot, "branch")).strip() or "default"
    store = dot
    if kind == SHARED:
        shared = _read(os.path.join(dot, "sharedpath")).strip()
        if shared:
            store = shared if os.path.isabs(shared) else os.path.normpath(os.path.join(dot, shared))
    requires = tuple(x.strip() for x in _read(os.path.join(dot, "requires")).splitlines() if x.strip())[:24]
    changed = 0.0
    for p in (os.path.join(store, "store", "00changelog.i"), os.path.join(store, "00changelog.i"),
              os.path.join(dot, "dirstate")):
        try:
            changed = max(changed, os.path.getmtime(p))
        except OSError:
            pass
    return Repo(path, kind or "?", branch[:120], _paths(_read(os.path.join(dot, "hgrc"))), requires, changed,
                "" if os.path.isdir(dot) else "its .hg is not there")

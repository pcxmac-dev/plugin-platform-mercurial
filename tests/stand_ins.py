"""hg as a stand-in, and repositories as a few files. `FakeSpawn` is the runner's spawn (subprocess.run's shape): it
answers `hg version --quiet` as hg prints it and keeps every call with its keywords; `runner()` makes a Runner whose
`which` finds only the programs given. `repository` and `share` write a repository's few files as Mercurial lays them
out: nothing runs."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from plugin_platform_mercurial.tool import Runner

HG = "C:\\Program Files\\Mercurial\\hg.exe"


@dataclass
class Done:
    returncode: int
    stdout: str
    stderr: str = ""


class FakeSpawn:
    def __init__(self, answers=None):
        self.answers = {("version", "--quiet"): Done(0, "Mercurial Distributed SCM (version 6.9.4)\n"), **(answers or {})}
        self.calls: list[tuple[list, dict]] = []

    def __call__(self, argv, **kw):
        self.calls.append((list(argv), dict(kw)))
        got = self.answers.get(tuple(argv[1:]))
        if isinstance(got, BaseException):
            raise got
        return got or Done(255, "", f"hg: unknown command {argv[1:]}")


def runner(found=("hg",), spawn: FakeSpawn | None = None):
    s = spawn or FakeSpawn()
    return Runner(which=lambda name: HG if name in found else None, spawn=s), s


def repository(root: Path, name: str, branch="", default="https://hg.example.org/proj") -> Path:
    p = root / name
    (p / ".hg" / "store").mkdir(parents=True)
    (p / ".hg" / "requires").write_text("dotencode\nfncache\ngeneraldelta\nrevlogv1\nsparserevlog\nstore\n")
    (p / ".hg" / "store" / "00changelog.i").write_bytes(b"\x00\x01\x00\x01")
    if branch:
        (p / ".hg" / "branch").write_text(branch + "\n")
    if default:
        (p / ".hg" / "hgrc").write_text("%include ../shared.rc\n[ui]\nusername = Ciara\n[paths]\n"
                                        f"default = {default}\n[hooks]\nprecommit = rm -rf /\n")
    return p


def share(root: Path, source: Path, name: str) -> Path:
    p = root / name
    (p / ".hg").mkdir(parents=True)
    (p / ".hg" / "requires").write_text("shared\n")
    (p / ".hg" / "sharedpath").write_text(str(source / ".hg"))
    return p

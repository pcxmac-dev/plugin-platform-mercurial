"""What the Mercurial plugin attaches to (plugin API 2.2): Mercurial's command line, which it asks for its version alone;
a repository's own files, which it reads a repository's branch and paths from; and hg serve, which it runs in a
container.

These cards were written on 2026-11-25 from Mercurial's documentation as known to their writer; no page was fetched for
this build. `LIMINAL_VENDOR_PAGES=1 pytest tests/test_apis.py` asks every address on them once."""
from __future__ import annotations

from liminal_libs.sources.apis import Api, Area, Call, Link

VERIFIED = "2026-11-25"
CLI, FILES, SERVER = "Mercurial's command line", "A Mercurial repository's files", "hg serve (hgweb)"
_HELP = "https://www.mercurial-scm.org/doc/hg.1.html"

HG_CLI = Api(
    name=CLI, maker="The Mercurial project (open source, GPL-2.0)", kind="command",
    about=("hg, Mercurial's program: its commands make, change, inspect and exchange repositories. The plugin runs it "
           "once per look, `hg version --quiet`, without a window, outside any repository, plain (HGPLAIN) and reading "
           "no configuration file (HGRCPATH empty): never in a repository, whose hgrc can name code hg would run."),
    base="hg on PATH", version="any Mercurial: version --quiet's line is read as it prints it",
    auth="none: a local program, run as the signed-in user", limits="", costs="nothing: Mercurial is free and open source",
    links=(Link("hg(1)", _HELP, "reference"), Link("Mercurial's wiki", "https://wiki.mercurial-scm.org/", "docs"),
           Link("Downloads", "https://www.mercurial-scm.org/downloads", "tool"),
           Link("Release notes", "https://wiki.mercurial-scm.org/Release", "changelog"),
           Link("Mercurial's sources", "https://foss.heptapod.net/mercurial/mercurial-devel", "source")),
    areas=(Area("Version", "the program's own version", _HELP + "#version", covered="Mercurial's version on the page"),
           Area("Repositories", "hg init, clone, pull, push, update, commit"),
           Area("History", "hg log, annotate, diff, status"),
           Area("Configuration", "hgrc files: extensions, hooks, paths"),
           Area("Server", "hg serve")),
    calls=(Call("hg version --quiet", "Mercurial's version", "Version", used="Mercurial's version, once per look",
                docs=_HELP + "#version"),
           Call("hg summary", "a working directory's state (reads its hgrc: extensions and hooks run)", "History"),
           Call("hg init", "a new repository", "Repositories", writes=True),
           Call("hg pull", "new changesets fetched", "Repositories", writes=True)),
    verified=VERIFIED)

HG_FILES = Api(
    name=FILES, maker="The Mercurial project", kind="file",
    about=("A repository's .hg folder: requires (its format's features), branch (the working directory's named "
           "branch), hgrc (its paths among its settings), sharedpath (a share's store), store/00changelog.i (its "
           "history). The plugin reads these as text and the changelog's time: nothing is written, nothing run."),
    base="<repository>/.hg", version="the repository formats of Mercurial 4 and later (store, fncache, revlogv1, …)",
    auth="none: files the signed-in user can read", limits="each file read up to 64 KB", costs="",
    links=(Link("The .hg folder", "https://wiki.mercurial-scm.org/FileFormats", "reference"),
           Link("hgrc(5)", "https://www.mercurial-scm.org/doc/hgrc.5.html", "docs")),
    areas=(Area("branch", "the working directory's named branch", covered="the Branch column"),
           Area("hgrc [paths]", "the repository's default and other paths", covered="the Paths column, without passwords"),
           Area("requires and sharedpath", "its format's features; a share's store", covered="shares found and read"),
           Area("store", "the changelog, manifest and file revlogs", covered="the Changed column (the changelog's time)"),
           Area("hgrc [extensions] and [hooks]", "code and programs hg runs (never run by the plugin)")),
    calls=(Call("read .hg/branch", "the named branch", "branch", used="the Branch column"),
           Call("read .hg/hgrc [paths]", "the paths, as text", "hgrc [paths]", used="the Paths column"),
           Call("read .hg/requires, .hg/sharedpath", "its features; a share's store", "requires and sharedpath",
                used="a share's store found"),
           Call("stat .hg/store/00changelog.i, .hg/dirstate", "when it last changed", "store", used="the Changed column"),
           Call("read .hg/store/00changelog.i", "the history itself", "store")),
    verified=VERIFIED)

HG_SERVE = Api(
    name=SERVER, maker="The Mercurial project", kind="rest",
    about=("hg serve, Mercurial's built-in web server (hgweb), run by the plugin in a container: its repositories in a "
           "volume, browsed, cloned and pulled over http; pushes refused by its seeded configuration. It has no "
           "sign-in of its own, so it stays on this PC."),
    base="http://127.0.0.1:8000/ (this PC alone)", version="the image pinned (none in this release)",
    auth="none: hg serve has no sign-in (a web server in front of hgweb gives one)", limits="", costs="nothing",
    links=(Link("hg serve", _HELP + "#serve", "reference"),
           Link("Publishing repositories (hgweb)", "https://wiki.mercurial-scm.org/PublishingRepositories", "guide")),
    areas=(Area("Browsing", "hgweb's pages: repositories, changesets, files", covered="said on the page after its install"),
           Area("Wire protocol", "clone and pull over http", covered="said on the page: how to clone"),
           Area("Push", "push over http (allow-push, push_ssl)", covered="refused by its seeded hgweb.config")),
    calls=(Call("GET /", "the repositories' index", "Browsing", used="its health: the container plugin's check"),
           Call("hg clone http://<host>:8000/main", "its first repository cloned", "Wire protocol",
                used="said on the page after its install"),
           Call("hg push http://<host>:8000/main", "changesets sent to it (refused)", "Push", writes=True)),
    verified=VERIFIED)

APIS = (HG_CLI, HG_FILES, HG_SERVE)

"""What the plugin attaches to (plugin API 2.2): its cards are sound, the command-line card names the one command the
plugin runs and claims none it does not, the server card's commands are the ones its seeds give; and, with
LIMINAL_VENDOR_PAGES=1 alone, every address on them answers (the only test here that reaches the network)."""
from __future__ import annotations

import os

import pytest

from liminal_libs.sources import apis as A
from liminal_libs.sources.conformance import problems
from plugin_platform_mercurial import MACHINE, MercurialPlugin, recipe
from plugin_platform_mercurial import apis as cards
from liminal_libs.machines import standins
from stand_ins import runner


def card(name):
    return next(a for a in MACHINE.apis if a.name == name)


def test_its_cards_are_sound_and_written_for_plugin_api_2_2():
    p = MACHINE
    assert p.api == "2.2" and problems(p) == [] and A.problems(p.apis) == []
    assert [a.name for a in p.apis] == [cards.CLI, cards.FILES, cards.SERVER]
    for a in p.apis:
        assert a.verified == cards.VERIFIED and a.docs.startswith("https://") and a.used and a.covered
        assert all(c.area in {x.name for x in a.areas} for c in a.calls), a.name
        assert len(a.areas) > len(a.covered) or len(a.calls) > len(a.used)


def test_the_command_line_card_names_every_command_it_runs_and_no_other():
    r, s = runner()
    p = MercurialPlugin(runner=r)
    p.login = standins.login({})
    p.status()
    p.refresh()
    ran = {"hg " + " ".join(argv[1:]) for argv, _ in s.calls}
    assert ran == {c.name for c in card(cards.CLI).used} == {"hg version --quiet"}
    assert not any(c.writes for c in card(cards.CLI).used) and not any(c.writes for c in card(cards.FILES).used)


def test_the_server_card_says_it_has_no_sign_in():
    server = card(cards.SERVER)
    assert "no sign-in" in server.auth and recipe.PINS == {} and recipe.BUILD["linux"]["base"]["digest"]
    assert not any(c.costs for a in MACHINE.apis for c in a.calls)


@pytest.mark.skipif(os.environ.get("LIMINAL_VENDOR_PAGES") != "1",
                    reason="reaches the makers' pages: LIMINAL_VENDOR_PAGES=1")
def test_every_address_on_its_cards_answers(monkeypatch):
    monkeypatch.undo()
    assert A.dead_links(MACHINE.apis) == []

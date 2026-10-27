"""Tests for the poster-studio UI: keyboards, texts and the inline-button router.

These exercise real code paths - the real keyboard builders, the real text helpers and the real
router in cmds.on_button. Telegram itself is replaced by a tiny recorder so no network is touched;
everything inside the bot is the production code.

Run:  python -m pytest test_ui.py -v
"""
from __future__ import annotations

import asyncio

import pytest

import cmds

import dataset
from dataset import POSTERS


N = len(POSTERS)


def run(coro):
    return asyncio.run(coro)


def labels(markup) -> list[str]:
    return [b.text for row in markup.inline_keyboard for b in row]


def datas(markup) -> list[str]:
    return [b.callback_data for row in markup.inline_keyboard for b in row if b.callback_data]


def plain(s: str) -> str:
    """Static words are rendered in small caps (ui.sc); map them back to ascii for assertions."""
    import ui
    rev = {v: chr(k) for k, v in ui._SC.items()}
    return "".join(rev.get(ord(c), c) for c in s).lower()


# ======================================================================
# keyboards - every screen must be reachable and must offer a way home
# ======================================================================
def test_home_has_studio_and_trending():
    d = datas(cmds.start_keyboard())
    assert "studio" in d
    assert "tr" in d


def test_every_screen_offers_a_way_home():
    for name, markup in {
        "about": cmds.about_keyboard(),
        "help": cmds.help_keyboard(back=True),
        "styles": cmds.styles_keyboard(),
        "viewer": cmds.viewer_keyboard(3),
        "result": cmds.result_keyboard(3),
        "cancel": cmds.cancel_keyboard(),
    }.items():
        assert "home" in datas(markup), f"{name} screen has no home button"


def test_style_grid_lists_all_styles_once():
    d = datas(cmds.styles_keyboard())
    for sid in POSTERS:
        assert f"st:{sid}" in d, f"style {sid} missing from the grid"
    assert len([x for x in d if x.startswith("st:")]) == N


def test_style_grid_marks_the_current_style():
    assert "✅ 4" in labels(cmds.styles_keyboard(4))
    assert "✅ 4" not in labels(cmds.styles_keyboard(9))


def test_viewer_wraps_around_both_ends():
    first = datas(cmds.viewer_keyboard(1))
    assert f"sv:{N}" in first, "back from style 1 should wrap to the last style"
    last = datas(cmds.viewer_keyboard(N))
    assert "sv:1" in last, "next from the last style should wrap to style 1"


def test_viewer_use_button_selects_the_shown_style():
    assert "st:7" in datas(cmds.viewer_keyboard(7))


def test_result_has_prev_next_and_home():
    d = datas(cmds.result_keyboard(5))
    for expected in ("pv", "nx", "fl", "na", "op", "rg", "home"):
        assert expected in d


def test_options_has_back_to_poster_and_home():
    d = datas(cmds.options_keyboard(3, {"button": dataset.BUTTON_PRESETS[0], "pic": 0}))
    assert "ob" in d
    assert "home" in d


# ======================================================================
# texts
# ======================================================================
def test_start_text_has_no_link_provider_left():
    class U:
        id, first_name = 1, "Ann"
    t = plain(cmds.start_text(U()))
    assert "link provider" not in t
    assert "force" not in t


def test_help_lists_no_removed_commands():
    text = " ".join(c for c, _ in cmds.HELP_CMDS)
    for gone in ("/link", "/channels", "/profile"):
        assert gone not in text, f"{gone} should be gone"
    assert "/trending" in text


def test_style_info_mentions_the_style_number():
    info = plain(cmds.style_info(3))
    assert "3" in info
    assert f"/ {N}" in info


def test_pick_style_text_lists_every_style():
    t = cmds.pick_style_text()
    for sid in POSTERS:
        assert f"<b>{sid}</b>" in t


# ======================================================================
# router - the callback data must actually be parsed the way it is sent
# ======================================================================
class FakeMessage:
    def __init__(self, mid=10, photo=True):
        self.id = mid
        self.photo = object() if photo else None
        self.chat = type("C", (), {"id": 99})()

    async def edit_text(self, *a, **k):
        return self

    async def edit_caption(self, *a, **k):
        return self

    async def edit_reply_markup(self, *a, **k):
        return self


class FakeQuery:
    def __init__(self, data, photo=True):
        self.data = data
        self.message = FakeMessage(photo=photo)
        self.from_user = type("U", (), {"id": 5, "first_name": "Ann"})()
        self.answers = []

    async def answer(self, text=None, show_alert=False):
        self.answers.append((text, show_alert))


class FakeClient:
    def __init__(self):
        self.sent = []

    async def send_message(self, chat_id, text, reply_markup=None, **k):
        self.sent.append(text)
        return FakeMessage(photo=False)

    async def send_chat_action(self, *a, **k):
        pass

    async def send_photo(self, *a, **k):
        return FakeMessage()

    async def send_document(self, *a, **k):
        pass

    async def delete_messages(self, *a, **k):
        pass


@pytest.fixture()
def fresh_state(monkeypatch):
    """A clean per-user state so tests do not leak into each other.

    Uses the same defaultdict(dict) the module builds at import time.
    """
    from collections import defaultdict
    state = defaultdict(dict)
    monkeypatch.setattr(cmds, "STATE", state)
    return state


def test_noop_does_not_crash(fresh_state):
    q = FakeQuery("noop")
    run(cmds.on_button(FakeClient(), q))
    assert q.answers and q.answers[0][0] is None


def test_home_button_answers_and_edits(fresh_state):
    q = FakeQuery("home")
    run(cmds.on_button(FakeClient(), q))
    assert q.answers, "home must be answered"


def test_trending_button_reaches_anilist_path(fresh_state, monkeypatch):
    """tr must route to the trending runner (not silently fall through to the poster code)."""
    called = {}

    async def fake_trending(client, uid, cid, source_msg=None):
        called["hit"] = (uid, cid)

    monkeypatch.setattr(cmds, "_run_trending", fake_trending)
    q = FakeQuery("tr")
    run(cmds.on_button(FakeClient(), q))
    assert called.get("hit") == (5, 99)


def test_style_button_with_no_anime_asks_for_a_name(fresh_state):
    q = FakeQuery("st:3")
    run(cmds.on_button(FakeClient(), q))
    assert fresh_state[5]["await"] == "name"
    assert fresh_state[5]["style"] == 3


def test_pick_sets_a_default_style_when_none_chosen(fresh_state, monkeypatch):
    """A trending pick can arrive before any style was chosen - it must still render."""
    async def fake_load(_id):
        return dataset.Anime(raw={"id": 1, "title": {"romaji": "X"}})

    rendered = {}

    async def fake_generate(client, uid, cid, panel=False, source_msg=None):
        rendered["style"] = fresh_state[uid]["style"]

    monkeypatch.setattr(dataset, "load_anime", fake_load)
    monkeypatch.setattr(cmds, "generate", fake_generate)
    q = FakeQuery("pk:1")
    run(cmds.on_button(FakeClient(), q))
    assert rendered.get("style") == 1


def test_pick_keeps_a_previously_chosen_style(fresh_state, monkeypatch):
    fresh_state[5]["style"] = 9

    async def fake_load(_id):
        return dataset.Anime(raw={"id": 1, "title": {"romaji": "X"}})

    rendered = {}

    async def fake_generate(client, uid, cid, panel=False, source_msg=None):
        rendered["style"] = fresh_state[uid]["style"]

    monkeypatch.setattr(dataset, "load_anime", fake_load)
    monkeypatch.setattr(cmds, "generate", fake_generate)
    q = FakeQuery("pk:1")
    run(cmds.on_button(FakeClient(), q))
    assert rendered.get("style") == 9


def test_poster_buttons_need_an_anime(fresh_state):
    """Without a loaded anime the poster buttons must warn instead of crashing."""
    q = FakeQuery("nx")
    run(cmds.on_button(FakeClient(), q))
    assert q.answers and q.answers[-1][1] is True          # show_alert


def test_unknown_callback_is_answered_not_ignored(fresh_state):
    q = FakeQuery("totally_unknown")
    run(cmds.on_button(FakeClient(), q))
    assert q.answers, "an unknown callback must still be answered so the client stops spinning"


# ======================================================================
# trending - real query shape
# ======================================================================
def test_trending_query_is_wellformed():
    q = dataset.TRENDING_QUERY
    assert "TRENDING_DESC" in q
    assert "isAdult: false" in q
    assert "title" in q and "seasonYear" in q


def test_trending_runner_handles_empty(monkeypatch, fresh_state):
    async def empty(_limit=10):
        return []

    monkeypatch.setattr(dataset, "trending_anime", empty)
    client = FakeClient()
    run(cmds._run_trending(client, 5, 99))
    assert client.sent, "the runner must report something even with no results"


def test_trending_runner_renders_pick_buttons(monkeypatch, fresh_state):
    async def rows(_limit=10):
        return [dict(id=11, title="Naruto", year=2002, format="TV"),
                dict(id=22, title="Bleach", year=2004, format="TV")]

    monkeypatch.setattr(dataset, "trending_anime", rows)

    seen = {}

    async def fake_edit_text(self, text, reply_markup=None):
        seen["markup"] = reply_markup
        return self

    monkeypatch.setattr(FakeMessage, "edit_text", fake_edit_text)
    run(cmds._run_trending(FakeClient(), 5, 99, source_msg=FakeMessage(photo=False)))
    assert "pk:11" in datas(seen["markup"])
    assert "pk:22" in datas(seen["markup"])
    assert "home" in datas(seen["markup"])

"""Tests for the link-provider half of the bot.

These exercise real code paths: the real json storage backend, the real pure helpers and the real
keyboard builders. No external service is contacted and nothing is mocked - the modules are imported
for real and their functions are called for real.

Run:  python -m pytest test_links.py -v
"""
from __future__ import annotations

import asyncio
import importlib

import pytest


@pytest.fixture()
def store(tmp_path, monkeypatch):
    """A real json-backed linkstore writing into a throwaway DATA_DIR."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.delenv("MONGO_URI", raising=False)
    monkeypatch.delenv("MONGO_DB_URI", raising=False)
    import config
    importlib.reload(config)
    import linkstore
    importlib.reload(linkstore)
    return linkstore


def run(coro):
    return asyncio.run(coro)


def plain(s: str) -> str:
    """The bot renders static words in small caps (ui.sc). Map them back to ascii for assertions."""
    import ui
    rev = {v: chr(k) for k, v in ui._SC.items()}
    return "".join(rev.get(ord(c), c) for c in s).lower()


# ======================================================================
# linkstore - json backend
# ======================================================================
def test_touch_user_creates_and_updates(store):
    rec = run(store.touch_user(7, "Ann", "ann"))
    assert rec["first_name"] == "Ann"
    assert rec["links"] == 0
    again = run(store.touch_user(7, "", ""))
    assert again["first_name"] == "Ann"          # empty values do not wipe the stored name
    assert run(store.get_user(7))["username"] == "ann"
    assert store.user_count() == 1


def test_touch_user_persists_to_disk(store, tmp_path):
    run(store.touch_user(11, "Bo", "bo"))
    path = tmp_path / store.USERS_FILE
    assert path.exists()
    assert '"11"' in path.read_text("utf-8")


def test_bump_counts_user_and_global(store):
    run(store.touch_user(5, "Cy", "cy"))
    run(store.bump(5, "links"))
    run(store.bump(5, "links"))
    assert run(store.get_user(5))["links"] == 2
    assert store.counters()["links"] == 2


def test_all_users(store):
    run(store.touch_user(1, "a", "a"))
    run(store.touch_user(2, "b", "b"))
    assert sorted(run(store.all_users())) == [1, 2]


def test_add_and_remove_fsub(store):
    run(store.add_fsub({"id": -100, "title": "Main", "username": "main", "invite": "https://t.me/+x"}))
    chans = run(store.fsub_channels())
    assert len(chans) == 1
    assert chans[0]["ref"] == "main"              # a normalised reference is stored
    # the same channel sent as a t.me link must replace, not duplicate
    run(store.add_fsub({"id": -100, "title": "Main", "username": "main", "invite": None}))
    assert len(run(store.fsub_channels())) == 1
    gone = run(store.remove_fsub("@main"))
    assert gone["title"] == "Main"
    assert run(store.fsub_channels()) == []


def test_remove_fsub_by_id(store):
    run(store.add_fsub({"id": -100123, "title": "X", "username": None, "invite": None}))
    assert run(store.remove_fsub("-100123")) is not None
    assert run(store.fsub_channels()) == []
    assert run(store.remove_fsub("-999")) is None


def test_fsub_persists_across_reload(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.delenv("MONGO_URI", raising=False)
    monkeypatch.delenv("MONGO_DB_URI", raising=False)
    import config
    importlib.reload(config)
    import linkstore
    importlib.reload(linkstore)
    run(linkstore.add_fsub({"id": -5, "title": "Persisted", "username": "persisted", "invite": None}))

    importlib.reload(linkstore)                    # fresh module state, same DATA_DIR
    assert [c["title"] for c in run(linkstore.fsub_channels())] == ["Persisted"]


def test_norm_handles_all_reference_forms(store):
    for ref in ("https://t.me/Channel", "t.me/Channel", "@Channel", "Channel", "telegram.me/channel/"):
        assert store._norm(ref) == "channel"


# ======================================================================
# links.py - pure helpers
# ======================================================================
def test_clean_ref(store):
    import links
    assert links._clean_ref("https://t.me/Chan") == "Chan"
    assert links._clean_ref("@Chan") == "Chan"
    assert links._clean_ref("  t.me/Chan/  ") == "Chan"
    assert links._clean_ref("-1001234567890") == "-1001234567890"


def test_is_admin(monkeypatch):
    import config
    import links
    monkeypatch.setattr(config, "OWNER_ID", 42, raising=False)
    assert links._is_admin(42) is True
    assert links._is_admin(7) is False
    monkeypatch.setattr(config, "OWNER_ID", 0, raising=False)
    assert links._is_admin(0) is False            # unset owner must never grant admin


# ======================================================================
# links.py - keyboards & texts
# ======================================================================
def test_home_keyboard_has_admin_row_only_for_admins(store):
    import links
    plain_rows = lambda m: [plain(b.text) for row in m.inline_keyboard for b in row]
    assert any("link" in t for t in plain_rows(links.home_kb(False)))
    assert not any("admin" in t for t in plain_rows(links.home_kb(False)))
    assert any("admin" in t for t in plain_rows(links.home_kb(True)))


def test_locked_keyboard_lists_missing_channels(store):
    import links
    chans = [{"id": -1, "title": "Main", "username": "main", "invite": "https://t.me/+a"},
             {"id": -2, "title": "Backup", "username": None, "invite": "https://t.me/+b"}]
    markup = links.locked_kb(chans)
    texts = [plain(b.text) for row in markup.inline_keyboard for b in row]
    urls = [b.url for row in markup.inline_keyboard for b in row if b.url]
    assert any("main" in t for t in texts)
    assert any("backup" in t for t in texts)
    assert "https://t.me/+a" in urls and "https://t.me/+b" in urls
    assert any("joined" in t for t in texts)


def test_locked_keyboard_skips_channels_without_a_url(store):
    import links
    markup = links.locked_kb([{"id": -3, "title": "Private", "username": None, "invite": None}])
    urls = [b.url for row in markup.inline_keyboard for b in row if b.url]
    assert urls == []                             # nothing to link to -> only the "i joined" button remains


def test_channels_text_and_kb(store):
    import links
    assert "no channels" in plain(links.channels_text([]))
    chans = [{"id": -1, "title": "Main", "username": "main", "invite": "https://t.me/+a"}]
    body = plain(links.channels_text(chans))
    assert "main" in body
    assert links.channels_kb(chans).inline_keyboard


def test_link_text_expiring_and_permanent(store):
    import datetime
    import links
    future = datetime.datetime.now() + datetime.timedelta(minutes=5)
    expiring = links.link_text("https://t.me/+abc", future)
    assert "https://t.me/+abc" in expiring
    assert "expires" in plain(expiring)
    permanent = links.link_text("https://t.me/chan", None)
    assert "permanent" in plain(permanent)


def test_profile_text_handles_empty_record(store):
    import links
    assert "0" in links.profile_text(None)
    assert "—" in links.profile_text({})


def test_admin_text_reports_counters(store):
    import links
    run(store.touch_user(1, "a", "a"))
    run(store.bump(1, "links"))
    text = links.admin_text([])
    assert "1" in text


# ======================================================================
# registration wiring
# ======================================================================
def test_register_adds_handlers(store):
    import links
    added = []
    class FakeApp:
        def add_handler(self, handler, *a, **k):
            added.append(handler)
    links.register(FakeApp())
    assert len(added) >= 5                        # /link, /channels, /profile, text flow, forward flow, callbacks


def test_commands_include_link_and_channels(store):
    import links
    names = [c for c, _ in links.commands()]
    assert "link" in names and "channels" in names


# ======================================================================
# integration: real handler code paths against a stand-in Telegram client
# ======================================================================
class FakeLink:
    def __init__(self, url, expire=None):
        self.invite_link, self.expire_date = url, expire


class FakeClient:
    """Minimal stand-in for the Kurigram client.

    A fake client is used here because the alternative is talking to the real Telegram Bot API, which
    needs live credentials. Everything below the client boundary - the gate, the link delivery, the
    keyboards, the store - is the real code being exercised.
    """
    def __init__(self, member_status=None, invite=None, fail_invite=False):
        self.member_status = member_status
        self.invite = invite
        self.fail_invite = fail_invite
        self.photos = []
        self.messages = []
        self.member_calls = []
        self.invite_calls = []

    async def get_chat_member(self, chat_id, user_id):
        from pyrogram import enums
        from pyrogram.errors import UserNotParticipant
        self.member_calls.append((chat_id, user_id))
        if self.member_status == "not_participant":
            raise UserNotParticipant("no")
        return type("M", (), {"status": self.member_status or enums.ChatMemberStatus.MEMBER})()

    async def create_chat_invite_link(self, chat_id, name=None, expire_date=None):
        from pyrogram.errors import RPCError
        self.invite_calls.append((chat_id, expire_date))
        if self.fail_invite:
            raise RPCError("nope")
        return FakeLink(self.invite or "https://t.me/+fresh", expire_date)

    async def send_photo(self, chat_id, photo, caption=None, reply_markup=None, **kw):
        self.photos.append((photo, caption, reply_markup))
        return type("Msg", (), {"id": len(self.photos), "photo": True})()

    async def send_message(self, chat_id, text, reply_markup=None, **kw):
        self.messages.append((text, reply_markup))
        return type("Msg", (), {"id": len(self.messages), "photo": None})()


def test_deliver_link_is_blocked_until_the_user_joined(store):
    import links
    run(store.add_fsub({"id": -100, "title": "Main", "username": "main", "invite": "https://t.me/+a"}))
    client = FakeClient(member_status="not_participant")
    run(links.deliver_link(client, 9, 9))
    caption, markup, _ = client.photos[-1][1], client.photos[-1][2], None
    assert "join required" in plain(caption)
    assert any(b.url == "https://t.me/+a" for row in markup.inline_keyboard for b in row)
    assert client.invite_calls == []                    # a locked user never gets an invite


def test_deliver_link_hands_out_an_invite_after_joining(store):
    import links
    run(store.add_fsub({"id": -100, "title": "Main", "username": "main", "invite": "https://t.me/+a"}))
    client = FakeClient(member_status="member", invite="https://t.me/+fresh")
    run(links.deliver_link(client, 9, 9))
    caption = client.photos[-1][1]
    assert "https://t.me/+fresh" in caption
    assert client.invite_calls and client.invite_calls[0][1] is not None   # expiring link requested
    assert run(store.get_user(9))["links"] == 1


def test_deliver_link_falls_back_to_public_link_when_invite_fails(store):
    import links
    run(store.add_fsub({"id": -100, "title": "Main", "username": "main", "invite": None}))
    client = FakeClient(member_status="member", fail_invite=True)
    run(links.deliver_link(client, 9, 9))
    assert "https://t.me/main" in client.photos[-1][1]


def test_deliver_link_reports_when_there_is_no_link_at_all(store):
    import links
    run(store.add_fsub({"id": -100, "title": "Private", "username": None, "invite": None}))
    client = FakeClient(member_status="member", fail_invite=True)
    run(links.deliver_link(client, 9, 9))
    assert "couldn't make a link" in plain(client.photos[-1][1])


def test_deliver_link_without_channels_points_at_the_admin_panel(store):
    import links
    client = FakeClient(member_status="member")
    run(links.deliver_link(client, 9, 9))
    assert "no link source" in plain(client.photos[-1][1])


def test_deep_link_picks_the_named_channel(store):
    import links
    run(store.add_fsub({"id": -1, "title": "First", "username": "first", "invite": None}))
    run(store.add_fsub({"id": -2, "title": "Second", "username": "second", "invite": None}))
    client = FakeClient(member_status="member", invite="https://t.me/+x")
    run(links.deliver_link(client, 9, 9, ref="second"))
    assert client.invite_calls[-1][0] == -2


def test_touch_start_follows_a_link_deep_link(store):
    import links
    run(store.add_fsub({"id": -1, "title": "Main", "username": "main", "invite": None}))
    client = FakeClient(member_status="member", invite="https://t.me/+d")
    message = type("Msg", (), {
        "chat": type("C", (), {"id": 9})(),
        "from_user": type("U", (), {"id": 9, "first_name": "Zoe", "username": "zoe"})(),
        "command": ["start", "link_main"],
    })()
    run(links.touch_start(client, message))
    assert "https://t.me/+d" in client.photos[-1][1]
    assert run(store.get_user(9))["first_name"] == "Zoe"


def test_touch_start_plain_start_only_registers(store):
    import links
    client = FakeClient(member_status="member")
    message = type("Msg", (), {
        "chat": type("C", (), {"id": 9})(),
        "from_user": type("U", (), {"id": 9, "first_name": "Zoe", "username": "zoe"})(),
        "command": ["start"],
    })()
    run(links.touch_start(client, message))
    assert client.photos == []
    assert run(store.get_user(9)) is not None


# ======================================================================
# integration: the inline router (on_cb)
# ======================================================================
class FakeMsg:
    def __init__(self, chat_id=9, photo=False):
        self.chat = type("C", (), {"id": chat_id})()
        self.photo = photo
        self.edits = []

    async def edit_text(self, text, reply_markup=None, **kw):
        self.edits.append(("text", text, reply_markup))

    async def edit_caption(self, text, reply_markup=None, **kw):
        self.edits.append(("caption", text, reply_markup))


class FakeCQ:
    def __init__(self, data, uid=9, msg=None):
        self.data = data
        self.from_user = type("U", (), {"id": uid})()
        self.message = msg or FakeMsg()
        self.answers = []

    async def answer(self, text=None, show_alert=False):
        self.answers.append((text, show_alert))


def test_on_cb_home_renders_the_link_provider(store):
    import links
    cq = FakeCQ("lk_home")
    run(links.on_cb(FakeClient(member_status="member"), cq))
    kind, text, markup = cq.message.edits[-1]
    assert kind == "text"
    assert "link provider" in plain(text)
    assert cq.answers                                # acknowledged


def test_on_cb_admin_panel_is_denied_for_non_admins(store, monkeypatch):
    import config
    import links
    monkeypatch.setattr(config, "OWNER_ID", 42, raising=False)
    cq = FakeCQ("lk_admin", uid=9)
    run(links.on_cb(FakeClient(member_status="member"), cq))
    assert cq.message.edits == []                    # nothing rendered
    assert cq.answers[-1][1] is True                 # alert shown


def test_on_cb_admin_panel_opens_for_the_owner(store, monkeypatch):
    import config
    import links
    monkeypatch.setattr(config, "OWNER_ID", 42, raising=False)
    cq = FakeCQ("lk_admin", uid=42)
    run(links.on_cb(FakeClient(member_status="member"), cq))
    assert "admin panel" in plain(cq.message.edits[-1][1])


def test_on_cb_broadcast_start_asks_for_text(store, monkeypatch):
    import config
    import links
    import cmds
    monkeypatch.setattr(config, "OWNER_ID", 42, raising=False)
    cq = FakeCQ("lk_bc", uid=42)
    run(links.on_cb(FakeClient(member_status="member"), cq))
    assert cmds.STATE[42]["await"] == "lk_bc"
    assert "broadcast text" in plain(cq.message.edits[-1][1])


def test_on_cb_remove_channel_updates_the_panel(store, monkeypatch):
    import config
    import links
    monkeypatch.setattr(config, "OWNER_ID", 42, raising=False)
    run(store.add_fsub({"id": -77, "title": "Gone", "username": "gone", "invite": None}))
    cq = FakeCQ("lk_rm:-77", uid=42)
    run(links.on_cb(FakeClient(member_status="member"), cq))
    assert run(store.fsub_channels()) == []
    assert cq.answers[-1][1] is False                # plain ack, no alert


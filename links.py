"""links.py - the link-provider half of the bot (README (7).txt: "Link Provider").

What it does:
  • force-sub  - the bot only hands out links after the user joined every channel in the force-sub list.
  • get link   - makes a fresh invite link (expiring after config.LINK_EXPIRY_MINUTES when Telegram allows it,
                 otherwise the channel's public / stored link) and shows it with its expiry.
  • deep link  - /start link_<ref> hands out the invite for that channel, same force-sub gate.
  • admin panel- add / remove force-sub channels, broadcast to every user, see stats.

Every screen is a thumbnail photo with inline buttons, the same look as the poster studio, so the whole bot
feels like one app. Group management from README (7).txt is deliberately NOT implemented.

Text flows register BEFORE cmds (like chnl.py) and raise StopPropagation so the poster studio's
"send an anime name" listener never eats a channel link or a broadcast draft.
"""
from __future__ import annotations

import asyncio
import datetime
import html
import logging
import random
import time

from pyrogram import StopPropagation, enums, filters
from pyrogram.errors import FloodWait, RPCError, UserNotParticipant
from pyrogram.handlers import CallbackQueryHandler, MessageHandler

import cmds
import config
import linkstore
from ui import BLUE, GREEN, RED, bq, btn, kb, sc

log = logging.getLogger("links")

HTML = enums.ParseMode.HTML
MODES = ("lk_add", "lk_bc")
_BC_CHUNK = 25          # users contacted at once
_BC_PAUSE = 0.6         # seconds between chunks - stays under Telegram's broadcast limits


# ======================================================================
# thumbnails (the bot's menu pictures; MENU_IMAGES is shared with the poster studio)
# ======================================================================
def _thumb() -> str:
    return random.choice(config.MENU_IMAGES)


async def _screen(client, chat_id: int, text: str, markup, message=None):
    """Show a thumbnail photo + caption + buttons. message=None sends a new one, else edits in place."""
    if message is not None:
        await cmds._edit(message, text, markup)
        return
    try:
        await client.send_photo(chat_id, _thumb(), caption=text, reply_markup=markup)
    except RPCError as e:
        log.warning("menu thumbnail failed (%s) -> text only", e)
        await client.send_message(chat_id, text, reply_markup=markup)


# ======================================================================
# texts
# ======================================================================
def home_text() -> str:
    return (bq(sc("🔗 link provider") + "\n\n" +
               sc("join our channels once, then pull a fresh anime link whenever you want one.\n"
                  "links are made for you and expire after a few minutes - grab a new one any time.")) + "\n" +
            bq(sc("🔓 get link  ·  your personal invite, ready to share\n"
                  "📢 channels  ·  what you must join first\n"
                  "👤 profile  ·  your links so far")))


def channels_text(chans: list[dict]) -> str:
    if not chans:
        return bq(sc("📢 no channels are set up yet.\nask the owner to add the force-sub channels."))
    lines = "\n".join(f"<b>{i}. {html.escape(c['title'])}</b>"
                      + (f" · @{html.escape(c['username'])}" if c.get("username") else "")
                      for i, c in enumerate(chans, 1))
    return bq(sc(f"📢 join these channels ({len(chans)})") + "\n\n" + lines)


def locked_text(missing: list[dict]) -> str:
    lines = "\n".join(f"• <b>{html.escape(c['title'])}</b>" for c in missing)
    return bq(sc("🔒 join required") + "\n\n" +
              sc("to use the link provider, join every channel below, then tap ") + sc("i joined") + ".\n\n" + lines)


def link_text(url: str, expires_at) -> str:
    body = bq(sc("✅ here is your link") + "\n\n" + f'<a href="{url}">🔗 {html.escape(url)}</a>')
    stamp = expires_at.timestamp() if hasattr(expires_at, "timestamp") else expires_at
    if stamp:
        left = max(0, int((stamp - time.time()) / 60))
        body += "\n" + bq(sc("⏳ expires in about ") + f"<b>{left}</b> " + sc("minutes."))
    else:
        body += "\n" + bq(sc("🔗 permanent link - it never expires."))
    return body


def profile_text(rec: dict | None) -> str:
    rec = rec or {}
    joined = rec.get("joined")
    when = time.strftime("%d %b %Y", time.localtime(joined)) if joined else "—"
    return (bq(sc("👤 your profile") + "\n\n" +
               sc("🔗 links pulled: ") + f"<b>{int(rec.get('links', 0))}</b>\n" +
               sc("📅 with us since: ") + f"<b>{when}</b>") + "\n" +
            bq(sc("need help? tap support on the home screen.")))


def admin_text(chans: list[dict]) -> str:
    c = linkstore.counters()
    return (bq(sc("⚙️ admin panel") + "\n\n" +
               sc("👥 users: ") + f"<b>{linkstore.user_count()}</b>\n" +
               sc("📢 force-sub channels: ") + f"<b>{len(chans)}</b>\n" +
               sc("🔗 links pulled: ") + f"<b>{int(c.get('links', 0))}</b>\n" +
               sc("📢 broadcasts sent: ") + f"<b>{int(c.get('broadcasts', 0))}</b>"))


# ======================================================================
# keyboards
# ======================================================================
def home_kb(is_admin: bool = False):
    rows = [[btn("🔓 get link", "lk_get", color=GREEN)],
            [btn("📢 channels", "lk_ch", color=BLUE), btn("👤 profile", "lk_me", color=BLUE)],
            [btn("🏠 home", "home", color=RED)]]
    if is_admin:
        rows.insert(0, [btn("⚙️ admin panel", "lk_admin", color=GREEN)])
    return kb(*rows)


def locked_kb(missing: list[dict]):
    rows = []
    for c in missing:
        url = c.get("invite") or (f"https://t.me/{c['username']}" if c.get("username") else None)
        if url:
            rows.append([btn(f"➕ {c['title']}"[:40], url=url, raw=True, color=BLUE)])
    rows.append([btn("✅ i joined — continue", "lk_check", color=GREEN)])
    rows.append([btn("🏠 home", "lk_home", color=RED)])
    return kb(*rows)


def link_kb(url: str):
    return kb([btn("🔗 open link", url=url, color=GREEN)],
              [btn("🔓 new link", "lk_get", color=BLUE), btn("🏠 home", "lk_home", color=RED)])


def channels_kb(chans: list[dict]):
    rows = []
    for c in chans:
        url = c.get("invite") or (f"https://t.me/{c['username']}" if c.get("username") else None)
        if url:
            rows.append([btn(f"➕ join {c['title']}"[:40], url=url, raw=True, color=BLUE)])
    rows.append([btn("🏠 home", "lk_home", color=RED)])
    return kb(*rows)


def admin_kb():
    return kb([btn("➕ add channel", "lk_add", color=GREEN), btn("📢 channels", "lk_ch", color=BLUE)],
              [btn("📢 broadcast", "lk_bc", color=GREEN), btn("📊 stats", "lk_stats", color=BLUE)],
              [btn("🏠 home", "lk_home", color=RED)])


def manage_kb(chans: list[dict]):
    rows = [[btn(f"🗑 {c['title']}"[:40], f"lk_rm:{c['id']}", raw=True, color=RED)] for c in chans]
    rows.append([btn("➕ add channel", "lk_add", color=GREEN)])
    rows.append([btn("⚙️ admin panel", "lk_admin", color=RED)])
    return kb(*rows)


def cancel_kb(back: str = "lk_admin"):
    return kb([btn("✖️ cancel", back, color=RED)])


def bc_confirm_kb():
    return kb([btn("📢 send to everyone", "lk_bcgo", color=GREEN)],
              [btn("✏️ edit text", "lk_bc", color=BLUE), btn("✖️ cancel", "lk_admin", color=RED)])


# ======================================================================
# force-sub gate
# ======================================================================
async def missing_subs(client, uid: int) -> list[dict]:
    """Force-sub channels the user has not joined. Channels we cannot check are never used to block."""
    out = []
    for ch in await linkstore.fsub_channels():
        try:
            m = await client.get_chat_member(ch["id"], uid)
            if m.status in (enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED):
                out.append(ch)
        except UserNotParticipant:
            out.append(ch)
        except RPCError as e:
            log.info("can't check membership of %s: %s", ch.get("ref"), e)
    return out


# ======================================================================
# link generation
# ======================================================================
async def _invite(client, ch: dict):
    """-> (url, expire_date). Fresh expiring invite when the bot may create one, else the stored / public link."""
    expire = None
    if config.LINK_EXPIRY_MINUTES:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=config.LINK_EXPIRY_MINUTES)
    try:
        link = await client.create_chat_invite_link(ch["id"], name="bot link", expire_date=expire)
        return link.invite_link, link.expire_date
    except RPCError as e:
        log.info("can't create an invite for %s (%s) -> stored link", ch.get("ref"), e)
    if ch.get("invite"):
        return ch["invite"], None
    if ch.get("username"):
        return f"https://t.me/{ch['username']}", None
    return None, None


async def deliver_link(client, uid: int, chat_id: int, message=None, ref: str | None = None):
    """Gate -> pick a channel -> hand out a link. ref=None uses the first force-sub channel."""
    chans = await linkstore.fsub_channels()
    if not chans:
        await _screen(client, chat_id,
                      bq(sc("🔗 no link source is set up yet.\nask the owner to add channels in the admin panel.")),
                      kb([btn("🏠 home", "lk_home", color=RED)]), message)
        return
    missing = await missing_subs(client, uid)
    if missing:
        await _screen(client, chat_id, locked_text(missing), locked_kb(missing), message)
        return
    ch = next((c for c in chans if ref and (c.get("ref") == linkstore._norm(ref)
                                            or str(c.get("id")) == str(ref))), None) or chans[0]
    url, expire = await _invite(client, ch)
    if not url:
        await _screen(client, chat_id,
                      bq(sc("😕 i couldn't make a link for ") + f"<b>{html.escape(ch['title'])}</b>" + sc(".\n"
                         "make me an admin there with the right to invite users, then try again.")),
                      kb([btn("🔁 try again", "lk_get", color=GREEN), btn("🏠 home", "lk_home", color=RED)]), message)
        return
    await linkstore.bump(uid, "links")
    await _screen(client, chat_id, link_text(url, expire), link_kb(url), message)


# ======================================================================
# commands
# ======================================================================
async def cmd_link(client, message):
    await linkstore.touch_user(message.from_user.id, message.from_user.first_name or "",
                               message.from_user.username or "")
    await deliver_link(client, message.from_user.id, message.chat.id)


async def touch_start(client, message) -> None:
    """Called by the poster studio's /start: remembers the user and follows a deep link.

    /start link_<ref>  (the "permanent link" a user shares) hands out the invite for that channel,
    still behind the force-sub gate. Plain /start does nothing extra here."""
    u = message.from_user
    await linkstore.touch_user(u.id, u.first_name or "", u.username or "")
    args = message.command[1:] if message.command else []
    if args and args[0].startswith("link_"):
        await deliver_link(client, u.id, message.chat.id, ref=args[0][5:])


async def cmd_channels(client, message):
    chans = await linkstore.fsub_channels()
    await _screen(client, message.chat.id, channels_text(chans), channels_kb(chans))


async def cmd_profile(client, message):
    rec = await linkstore.touch_user(message.from_user.id, message.from_user.first_name or "",
                                     message.from_user.username or "")
    await _screen(client, message.chat.id, profile_text(rec), home_kb(_is_admin(message.from_user.id)))


def _is_admin(uid: int) -> bool:
    return bool(config.OWNER_ID and uid == config.OWNER_ID)


# ======================================================================
# text flows (channel reference / broadcast draft)
# ======================================================================
def _clean_ref(text: str) -> str:
    """'@Chan' / 't.me/chan' / 'https://t.me/chan' / '-100123...' -> the bare reference."""
    t = (text or "").strip()
    for pre in ("https://", "http://"):
        if t.lower().startswith(pre):
            t = t[len(pre):]
    for pre in ("t.me/", "telegram.me/", "telegram.dog/"):
        if t.lower().startswith(pre):
            t = t[len(pre):]
    return t.strip().strip("/").lstrip("@") or t.strip()


async def _add_channel(client, message) -> None:
    uid, cid = message.from_user.id, message.chat.id
    ud = cmds._ud(uid)
    fc = getattr(message, "forward_from_chat", None)
    ref = fc.id if fc is not None else _clean_ref(message.text or "")
    if not ref:
        await message.reply_text(bq(sc("😕 i couldn't read that. send the channel @username or its link.")),
                                 reply_markup=cancel_kb())
        return
    try:
        chat = await client.get_chat(ref)
    except (RPCError, KeyError, ValueError):
        await message.reply_text(
            bq(sc("😕 i can't find that channel.\nadd me there first, then send its @username or link.")),
            reply_markup=cancel_kb())
        return
    if chat.type != enums.ChatType.CHANNEL:
        await message.reply_text(bq(sc("😕 that is not a channel.")), reply_markup=cancel_kb())
        return
    invite = None
    try:                                   # remember a permanent invite so the join button always has a url
        link = await client.create_chat_invite_link(chat.id, name="force-sub")
        invite = link.invite_link
    except RPCError:
        pass
    await linkstore.add_fsub({"id": chat.id, "title": chat.title or "channel",
                              "username": chat.username, "invite": invite})
    ud["await"] = None
    chans = await linkstore.fsub_channels()
    await _screen(client, cid,
                  bq(sc("✅ channel added\n") + f"<b>{html.escape(chat.title or 'channel')}</b>\n" +
                     sc("users must join it before they get a link.")),
                  manage_kb(chans), message)


async def _broadcast_go(client, uid: int, cid: int, ctl_msg) -> None:
    ud = cmds._ud(uid)
    bc = ud.get("bc") or {}
    if not bc.get("text"):
        await cmds._edit(ctl_msg, bq(sc("⚠️ nothing to send.")), admin_kb())
        return
    users = await linkstore.all_users()
    await cmds._edit(ctl_msg, bq(sc(f"📢 sending to {len(users)} users…")))
    sent = failed = 0
    for i in range(0, len(users), _BC_CHUNK):
        chunk = users[i:i + _BC_CHUNK]
        results = await asyncio.gather(*[
            client.send_message(u, bc["text"], entities=bc.get("ents") or None,
                                parse_mode=enums.ParseMode.DISABLED, disable_web_page_preview=True)
            if bc.get("ents") else
            client.send_message(u, bc["text"], parse_mode=HTML, disable_web_page_preview=True)
            for u in chunk], return_exceptions=True)
        for r in results:
            if isinstance(r, FloodWait):
                await asyncio.sleep(r.value + 1)
            elif isinstance(r, Exception):
                failed += 1
            else:
                sent += 1
        if i + _BC_CHUNK < len(users):
            await asyncio.sleep(_BC_PAUSE)
    await linkstore.bump(uid, "broadcasts")
    ud.pop("bc", None)
    ud["await"] = None
    await cmds._edit(ctl_msg,
                     bq(sc("✅ broadcast finished\n\n") + sc("delivered: ") + f"<b>{sent}</b>\n" +
                        sc("failed: ") + f"<b>{failed}</b>"), admin_kb())


async def on_mode_text(client, message):
    ud = cmds._ud(message.from_user.id)
    mode = ud.get("await")
    if mode == "lk_add":
        await _add_channel(client, message)
        raise StopPropagation
    if mode == "lk_bc":
        cid = message.chat.id
        ud["await"] = None
        ud["bc"] = {"text": message.text or "", "ents": list(message.entities) if message.entities else None}
        await cmds._safe_delete(client, cid, message.id)
        try:
            await client.send_message(cid, ud["bc"]["text"], entities=ud["bc"].get("ents") or None,
                                      parse_mode=enums.ParseMode.DISABLED, disable_web_page_preview=True)
        except RPCError:
            await client.send_message(cid, ud["bc"]["text"], parse_mode=HTML, disable_web_page_preview=True)
        await client.send_message(cid, bq(sc("👆 this is how the broadcast will look.\nsend it to everyone?")),
                                  reply_markup=bc_confirm_kb())
        raise StopPropagation


# ======================================================================
# inline router  (callback data "lk_...")
# ======================================================================
async def on_cb(client, cq):
    uid, msg = cq.from_user.id, cq.message
    cid = msg.chat.id
    cmd, _, arg = cq.data.partition(":")

    if cmd in ("lk_home", "lk_back"):
        await cq.answer()
        await _screen(client, cid, home_text(), home_kb(_is_admin(uid)), msg)
    elif cmd == "lk_get":
        await cq.answer(sc("checking…"))
        await deliver_link(client, uid, cid, msg)
    elif cmd == "lk_check":
        await cq.answer(sc("checking…"))
        missing = await missing_subs(client, uid)
        if missing:
            await _screen(client, cid, locked_text(missing), locked_kb(missing), msg)
        else:
            await cq.answer(sc("thanks! unlocked"), show_alert=True)
            await deliver_link(client, uid, cid, msg)
    elif cmd == "lk_ch":
        await cq.answer()
        chans = await linkstore.fsub_channels()
        await _screen(client, cid, channels_text(chans), channels_kb(chans), msg)
    elif cmd == "lk_me":
        await cq.answer()
        await _screen(client, cid, profile_text(await linkstore.get_user(uid)), home_kb(_is_admin(uid)), msg)
    elif cmd == "lk_stats":
        await cq.answer()
        await _screen(client, cid, admin_text(await linkstore.fsub_channels()), admin_kb(), msg)
    elif cmd == "lk_admin":
        if not _is_admin(uid):
            await cq.answer(sc("admins only"), show_alert=True)
            return
        await cq.answer()
        await _screen(client, cid, admin_text(await linkstore.fsub_channels()), admin_kb(), msg)
    elif cmd == "lk_add":
        if not _is_admin(uid):
            await cq.answer(sc("admins only"), show_alert=True)
            return
        await cq.answer()
        ud = cmds._ud(uid)
        ud["await"] = "lk_add"
        await _screen(client, cid,
                      bq(sc("➕ add a force-sub channel\n\n"
                            "1️⃣ add me to the channel as an admin with the right to invite users\n"
                            "2️⃣ send me its @username, its link, or forward a post from it")),
                      cancel_kb(), msg)
    elif cmd == "lk_bc":
        if not _is_admin(uid):
            await cq.answer(sc("admins only"), show_alert=True)
            return
        await cq.answer()
        ud = cmds._ud(uid)
        ud["await"] = "lk_bc"
        await _screen(client, cid,
                      bq(sc("📢 send me the broadcast text.\nformatting you use in telegram (bold, links, spoiler) "
                            "is kept exactly.")), cancel_kb(), msg)
    elif cmd == "lk_bcgo":
        if not _is_admin(uid):
            await cq.answer(sc("admins only"), show_alert=True)
            return
        await cq.answer(sc("sending…"))
        await _broadcast_go(client, uid, cid, msg)
    elif cmd == "lk_rm":
        if not _is_admin(uid):
            await cq.answer(sc("admins only"), show_alert=True)
            return
        ch = await linkstore.remove_fsub(arg)
        await cq.answer(sc("🗑 removed") if ch else sc("not found"), show_alert=ch is None)
        chans = await linkstore.fsub_channels()
        await _screen(client, cid, channels_text(chans) if not chans else admin_text(chans),
                      manage_kb(chans) if chans else admin_kb(), msg)
    else:
        await cq.answer()


# ======================================================================
# wiring
# ======================================================================
def _mode_filter(*modes):
    return filters.create(lambda _, __, m: bool(m.from_user) and cmds.STATE[m.from_user.id].get("await") in modes)


def commands() -> list[tuple[str, str]]:
    return [("link", "Get an anime link (join our channels first)"),
            ("channels", "Force-sub channels")]


def register(app):
    """Call BEFORE cmds.register(): these handlers must see the text before the poster studio's name listener."""
    app.add_handler(MessageHandler(cmd_link, filters.command("link")))
    app.add_handler(MessageHandler(cmd_channels, filters.command("channels")))
    app.add_handler(MessageHandler(cmd_profile, filters.command("profile")))
    app.add_handler(MessageHandler(on_mode_text, filters.private & filters.create(cmds._not_command) & _mode_filter(*MODES)))
    app.add_handler(MessageHandler(cmd_addchnl_forward, filters.private & filters.forwarded & ~filters.text & _mode_filter("lk_add")))
    app.add_handler(CallbackQueryHandler(on_cb, filters.regex(r"^lk_")))


async def cmd_addchnl_forward(client, message):
    """A forwarded post from the channel = the admin pointing at the channel to add."""
    await _add_channel(client, message)
    raise StopPropagation

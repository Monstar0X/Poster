"""linkstore.py - storage for the link-provider half of the bot.

Keeps three things, all in one document per key:

  users       -> {"users": {uid: {"first_name", "username", "joined", "last_seen", "links", "sub"}}}
  fsub        -> {"channels": [{"id", "title", "username", "invite"}]}
  meta        -> {"counters": {"links": int, "broadcasts": int}, "seen": {"broadcasts": [uid, ...]}}

Backend is chosen exactly like chstore.py: MongoDB when MONGO_URI is set, otherwise a json
file under DATA_DIR. The json file is written atomically (temp file + os.replace) so a crash
never leaves a half-written store behind.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile

import config

log = logging.getLogger("linkstore")

USERS_FILE = "linkusers.json"          # written next to chstore's users.json
FSUB_FILE = "links.json"

_users: dict[int, dict] = {}
_fsub: list[dict] = []
_meta: dict = {"counters": {"links": 0, "broadcasts": 0}, "seen": {}}
_lock = asyncio.Lock()
_ready = False


# ----------------------------------------------------------------------
# backends
# ----------------------------------------------------------------------
def _json_read(name: str, default):
    path = config.DATA_DIR / name
    try:
        if path.exists():
            return json.loads(path.read_text("utf-8"))
    except Exception as e:
        log.warning("could not read %s: %s", path, e)
    return default


def _json_write(name: str, data) -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=config.DATA_DIR, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, config.DATA_DIR / name)


def _mongo():
    """-> the collection, or None when MongoDB is not configured / cannot be used."""
    if not config.MONGO_URI:
        return None
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        return AsyncIOMotorClient(config.MONGO_URI)[config.MONGO_DB]["link_provider"]
    except Exception as e:
        log.warning("MONGO_URI is set but MongoDB can't be used (%s) -> json files instead", e)
        return None


_coll = None


async def _init() -> None:
    global _ready, _coll, _users, _fsub, _meta
    if _ready:
        return
    _ready = True
    _coll = _mongo()
    if _coll is not None:
        try:
            doc = await _coll.find_one({"_id": "root"}) or {}
        except Exception as e:
            log.warning("MongoDB read failed (%s) -> json files instead", e)
            _coll = None
            doc = {}
        if _coll is not None:
            _users = {int(k): v for k, v in (doc.get("users") or {}).items()}
            _fsub = list(doc.get("fsub") or [])
            _meta = doc.get("meta") or _meta
            log.info("link provider is stored in MongoDB (%s)", config.MONGO_DB)
            return
    _users = {int(k): v for k, v in (_json_read(USERS_FILE, {}) or {}).items()}
    _fsub = list(_json_read(FSUB_FILE, []) or [])
    _meta = _json_read("linkmeta.json", _meta) or _meta
    log.info("link provider is stored in %s", config.DATA_DIR)


async def _save() -> None:
    async with _lock:
        if _coll is not None:
            await _coll.replace_one({"_id": "root"},
                                    {"_id": "root", "users": {str(k): v for k, v in _users.items()},
                                     "fsub": _fsub, "meta": _meta}, upsert=True)
            return
        await asyncio.to_thread(_json_write, USERS_FILE, {str(k): v for k, v in _users.items()})
        await asyncio.to_thread(_json_write, FSUB_FILE, _fsub)
        await asyncio.to_thread(_json_write, "linkmeta.json", _meta)


# ----------------------------------------------------------------------
# users
# ----------------------------------------------------------------------
async def touch_user(uid: int, first_name: str = "", username: str = "") -> dict:
    """Remember a user (called on /start) and return their record."""
    import time
    await _init()
    rec = _users.get(uid) or {"joined": time.time(), "links": 0}
    rec.update({"first_name": first_name or rec.get("first_name", ""),
                "username": username or rec.get("username", ""),
                "last_seen": time.time()})
    _users[uid] = rec
    await _save()
    return rec


async def get_user(uid: int) -> dict | None:
    await _init()
    return _users.get(uid)


async def all_users() -> list[int]:
    await _init()
    return list(_users)


async def bump(uid: int, field: str) -> None:
    await _init()
    if uid not in _users:                      # a link can be pulled before /start was ever seen
        import time
        _users[uid] = {"joined": time.time(), "links": 0}
    _users[uid][field] = int(_users[uid].get(field, 0)) + 1
    _meta["counters"][field] = int(_meta["counters"].get(field, 0)) + 1
    await _save()


def user_count() -> int:
    return len(_users)


def counters() -> dict:
    return dict(_meta.get("counters") or {})


async def mark_seen_broadcast(uid: int) -> None:
    seen = _meta.setdefault("seen", {}).setdefault("broadcasts", [])
    if uid not in seen:
        seen.append(uid)
        await _save()


# ----------------------------------------------------------------------
# force-sub channels
# ----------------------------------------------------------------------
async def fsub_channels() -> list[dict]:
    await _init()
    return list(_fsub)


def _norm(ref: str) -> str:
    ref = (ref or "").strip().rstrip("/")
    for pre in ("https://", "http://"):
        if ref.lower().startswith(pre):
            ref = ref[len(pre):]
    for pre in ("t.me/", "telegram.me/", "telegram.dog/"):
        if ref.lower().startswith(pre):
            ref = ref[len(pre):]
    return ref.lstrip("@").lower()


async def add_fsub(ch: dict) -> None:
    """Add / replace a force-sub channel. ch = {"id", "title", "username", "invite"}."""
    await _init()
    ch = {**ch, "ref": _norm(ch.get("username") or str(ch.get("id", "")))}
    _fsub[:] = [c for c in _fsub if c.get("id") != ch["id"] and c.get("ref") != ch["ref"]]
    _fsub.append(ch)
    await _save()


async def remove_fsub(ref: str) -> dict | None:
    await _init()
    want = _norm(ref)
    found = next((c for c in _fsub if c.get("ref") == want or str(c.get("id")) == (ref or "").strip()), None)
    if not found:
        return None
    _fsub.remove(found)
    await _save()
    return found

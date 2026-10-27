# AGENTS.md

Persistent notes for working on this repository.

## What this bot is

A single Kurigram/Pyrogram Telegram bot: **poster studio only**.

`cmds.py` + `chnl.py` + `dataset.py` + `chname.py` + `Templates/` render **14 poster styles** from
AniList + fanart.tv and can publish them to a user's channel.

**Two features are deliberately NOT implemented. Do not add them:**

1. **Group management / moderation** (bans, mutes, warns, locks, filters, welcome/greeting, night mode,
   logging) — explicitly excluded by the task.
2. **The link provider** (force-sub gate, expiring invite links, admin panel, broadcast) — it was built
   once and then removed on request. `links.py`, `linkstore.py` and `test_links.py` are gone; do not
   reintroduce them.

## Architecture conventions

- `config.py` is imported first everywhere; it reads env vars and prepares `POSTER_FONT_DIR` for the templates.
- Handler registration order in `main.py` matters: `chnl.register()` then `cmds.register()`. `chnl` owns text
  flows and raises `StopPropagation` so the poster studio's "send an anime name" listener (`cmds.on_text`)
  does not swallow its input.
- Storage: `chstore.py` picks MongoDB when `MONGO_URI` is set, else a JSON file under `DATA_DIR`. JSON writes
  are atomic (temp file + `os.replace`).
- UI: all static text goes through `ui.sc()` (small caps). Dynamic user data is inserted raw. Use
  `ui.btn()/kb()` to build keyboards, and pass `raw=True` for labels that must keep their exact text.
- Screens are thumbnail photos (`config.MENU_IMAGES`) with captions + inline buttons, edited in place.

## Navigation contract (added when the UI was reworked)

- **Every** screen must expose a 🏠 home button (`callback_data="home"`). `test_ui.py` enforces this for
  every keyboard builder — add new keyboards to that test when you add a screen.
- `cmds.on_button` parses callback data as `cmd[:arg]`. Always branch on the part before `:`
  (`data.startswith("st:")` / `int(data[3:])`), never compare the whole string, or `pk:11` style
  payloads silently fail to match.
- Poster-studio callbacks in `cmds.py`: `home ab hp tr sv: st: sl sl0 bk cx na pk: nx pv rg fl op ob
  ipp ipn obt obc ocp ocn occ cxo noop`. `chnl.py` owns everything starting `ch_`.
- `on_pick` defaults `style` to 1 when the user arrives via 🔥 trending without having picked a style.

## Gotchas

- `ui.sc()` transliterates to small-caps unicode. Tests asserting on rendered text must normalise via
  `test_ui.plain()` — a plain `assert "text" in caption` will fail.
- Poster style ids: 1,2,4,5 use fanart.tv character PNGs; 3,6,7,9,10,11,13,14 use AniList posters;
  8,12 use AniList banners. See `dataset.POSTERS` and `dataset.art_kind()`.
- Fonts are **not** committed: both `fonts/` and `Templates/fonts/` are gitignored and downloaded on
  first start by `dataset.ensure_fonts()` (which writes into both dirs). A fresh checkout therefore needs
  network access on its first run; the zip is otherwise self-sufficient. `.dockerignore` ignores only
  `/fonts/` (root-anchored) so a committed `Templates/fonts/` would still ship if you ever add one.
- `Templates/assets/lines_navy.png` is generated at runtime by `dataset.ensure_assets()` when missing, so it
  is gitignored too — do not commit it.
- `numpy` must stay **< 2.5** while the image is Python 3.11 — 2.5+ requires Python 3.12+ and breaks the
  build. Verify with `docker build` after touching `requirements.txt`.
- `PORT=0` (the default) means the health server is **off**. The Dockerfile sets `PORT=8080`; a `.env` that
  sets its own `PORT` overrides it.
- The `TgCrypto` **package** installs its module as lowercase `tgcrypto`. `import TgCrypto` fails while
  `pip show TgCrypto` succeeds — this is normal, not a broken install. Check with `import tgcrypto`.
- In a fresh sandbox the installed packages are wiped (`.env` and the fonts survive). Re-run
  `pip install -r requirements.txt` before `python main.py`, or the first import fails with
  `ModuleNotFoundError: pyrogram`.

## Liveness check

`getWebhookInfo.pending_update_count` is **not** a liveness signal: with no webhook set it stays frozen
while the bot works, because MTProto polling does not drain that HTTP queue. Prove the bot is alive by
looking for an established socket to a Telegram DC (149.154.160.0/20 or 91.108.0.0/16) in `/proc/net/tcp`:

```python
import socket, struct
ip = lambda h: socket.inet_ntoa(struct.pack("<I", int(h, 16)))
for l in open("/proc/net/tcp"):
    f = l.split()
    if len(f) > 3 and f[3] == "01":
        r = ip(f[2].split(":")[0])
        if r.startswith(("149.154.", "91.108.")): print("MTProto LIVE ->", r)
```

`ALLOWED_USERS` blank means the `guard` handler is a no-op and the bot answers everyone.

## Commands

```bash
pip install -r requirements.txt
python -m pytest test_ui.py -v          # interface + router tests (23)
python main.py                          # run the bot (needs API_ID/API_HASH/BOT_TOKEN)
python -c "import dataset; dataset.ensure_fonts()"   # pre-download poster fonts
```

## Verification without Telegram credentials

The poster engine and the data layer can be exercised directly:

```python
import asyncio, dataset
a = asyncio.run(dataset.load_anime(1535))          # Death Note
r = asyncio.run(dataset.make_poster(8, a, {}))     # -> Rendered(jpg, png, size)
t = asyncio.run(dataset.trending_anime(5))         # -> [{id,title,year,format}, ...]
```

## Docker

```bash
docker build -t poster-bot .           # ~2 min; pins every dep
docker run -d --env-file .env -p 8080:8080 poster-bot
```

Run **only one** instance per bot token — two pollers fight over the update stream. `.env` is
`.dockerignore`d, so pass credentials with `--env-file`/`-e` at run time.

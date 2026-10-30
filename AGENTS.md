# AGENTS.md

Persistent notes for working on this repository.

## What this bot is

A single Kurigram/Pyrogram Telegram bot with **two halves**:

1. **Poster studio** (`cmds.py`, `chnl.py`, `dataset.py`, `chname.py`, `Templates/`) — renders 18 poster
   styles from AniList + fanart.tv, and can publish them to a user's channel.
2. **Link provider** (`links.py`, `linkstore.py`) — force-sub gate + expiring invite links + admin panel.

**Group management is deliberately NOT implemented.** Do not add moderation features (bans, mutes, warns,
locks, filters, welcome/greeting, night mode, logging) — the task explicitly excluded them.

## Architecture conventions

- `config.py` is imported first everywhere; it reads env vars and prepares `POSTER_FONT_DIR` for the templates.
- Handler registration order in `main.py` matters: `links.register()` then `chnl.register()` then
  `cmds.register()`. The first two own text flows and raise `StopPropagation` so the poster studio's
  "send an anime name" listener (`cmds.on_text`) does not swallow their input.
- Storage: `chstore.py` (poster channels) and `linkstore.py` (link provider) each pick MongoDB when
  `MONGO_URI` is set, else a JSON file under `DATA_DIR`. JSON writes are atomic (temp file + `os.replace`).
- UI: all static text goes through `ui.sc()` (small caps). Dynamic user data is inserted raw. Use
  `ui.btn()/kb()` to build keyboards, and pass `raw=True` for labels that must keep their exact text.
- Screens are thumbnail photos (`config.MENU_IMAGES`) with captions + inline buttons, edited in place.

## Gotchas

- `ui.sc()` transliterates to small-caps unicode. Tests asserting on rendered text must normalise via
  `test_links.plain()` — a plain `assert "text" in caption` will fail.
- `client.create_chat_invite_link(expire_date=...)` takes a **`datetime`**, not a float timestamp.
  `links.link_text()` accepts either so it stays testable.
- Poster style ids are contiguous 1-18 (the next / back buttons do `% N_STYLES + 1`, so never leave a gap). Styles 1, 4, 5, 6, 10, 16, 17 use
  fanart.tv character PNGs (no PNG -> the AniList poster); 3, 8, 12, 15 use the AniList banner (one big image); every
  other style uses the AniList poster (album).
  See `dataset.POSTERS`, `PNG_STYLES`, `BANNER_STYLES` and `dataset.art_kind()`.
- The "nova" styles (1, 2, 3, 6, 10, 11, 14-18) are `Templates/posterN.py` with `render(meta, art, button, character=None)`; they share
  `Templates/nova_kit.py` and are drawn on a 1280x720 grid at 1.5x. Each leaves its top-left corner empty for the channel
  branding (`chname.SPECS`). To add a style: write `posterN.py`, add it to `POSTERS`, `NOVA_STYLES` (and `BANNER_STYLES`
  if it wants a banner) and give it a `chname.SPECS` entry.
- `linkstore.bump()` creates the user record if missing — a link can be pulled before `/start` is seen.

## Commands

```bash
pip install -r requirements.txt
python -m pytest test_links.py -v      # link-provider tests (27)
python main.py                          # run the bot (needs API_ID/API_HASH/BOT_TOKEN)
python -c "import dataset; dataset.ensure_fonts()"   # pre-download poster fonts
```

## Verification without Telegram credentials

The poster engine can be exercised directly:

```python
import asyncio, dataset
a = asyncio.run(dataset.load_anime(1535))          # Death Note
r = asyncio.run(dataset.make_poster(8, a, {}))     # -> Rendered(jpg, png, size)
```

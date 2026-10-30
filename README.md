# 🎬 Anime Poster & Link Provider Bot

<div align="center">

[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-Channel-2CA5E0?logo=telegram&logoColor=white)](https://t.me/cantarellabots)
[![Support](https://img.shields.io/badge/Telegram-Support%20Chat-0088cc?logo=telegram&logoColor=white)](https://t.me/CantarellaBotschat)
[![Library](https://img.shields.io/badge/Library-Kurigram%20%2F%20Pyrogram-blue)](https://github.com/Kurigram/Kurigram)
[![Engine](https://img.shields.io/badge/Image%20Engine-Pillow-yellow)](https://python-pillow.org/)

One Telegram bot that does two jobs: it turns anime metadata into **18 poster / thumbnail styles**, and it runs a
**link provider** — users join your channels once, then pull fresh anime links whenever they want one.

Every screen is a thumbnail photo with inline buttons, so the whole thing feels like a single app.

</div>

---

## ✨ What's inside

This project merges two systems into one bot:

| Half | What it does |
| :--- | :--- |
| 🎨 **Poster studio** | 18 poster / thumbnail styles from AniList + fanart.tv, with live previews, character and art switching, custom button text and channel branding, plus a one-tap "post to channel". |
| 🔗 **Link provider** | Force-sub gate, expiring invite links, deep links, an admin panel and a broadcast tool. |

> **Group management is intentionally out of scope.** The moderation suite from the original specification
> (bans, mutes, warns, locks, filters, welcome messages, night mode, logging, …) is **not** part of this bot.
> This is a poster + link-provider bot only.

---

## 🎨 Poster studio

- **18 professional styles** at Full HD (1920×1080) and HD (1280×720). Styles 4, 5, 7, 8, 9, 12, 13 are the original set; 1, 2, 3, 6, 10, 11, 14-18 are the "nova" layouts from the Thumbnail- repo.
- **Dynamic art selection** — cycle transparent character cut-outs from fanart.tv, or the alternative AniList posters and banners, straight from the buttons.
- **Custom channel branding** — your channel name is rendered onto every poster in that poster's own typography and colours.
- **Direct-to-channel publishing** — attach a rich caption (formatting and custom emoji preserved) and inline URL buttons, preview it, then send it to a channel you administer.
- **High-quality export** — instant JPEG previews in chat, plus a `📁 full quality file` button for the lossless PNG.

## 🔗 Link provider

- **Force-sub gate** — the bot only hands out links after the user has joined every channel on the force-sub list.
- **Expiring links** — a fresh invite is created per request and expires after `LINK_EXPIRY_MINUTES`; if Telegram refuses, it falls back to the channel's stored or public link.
- **Deep links** — `/start link_<ref>` hands out the invite for a specific channel, still behind the gate.
- **Admin panel** — add / remove force-sub channels, broadcast to every user (formatting preserved), and read live stats.

---

## 🤖 Commands

| Command | Description |
| :--- | :--- |
| `/start` | Home screen: choose **poster studio** or **link provider** |
| `/link` | Get an anime link (join the channels first) |
| `/channels` | The force-sub channels you must join |
| `/profile` | Your profile and how many links you have pulled |
| `/poster <anime>` | Make a poster for the given anime |
| `/styles` | Preview every poster style |
| `/help` | Command guide and support links |
| `/addchnl` | Register **your** channel (bot must be full admin there) |
| `/mychnls` | List your registered channels |
| `/removechnl` | Unlink a registered channel |

> Tip: send any anime title in the private chat and the bot opens the search picker automatically.

---

## 🚀 Quick start

```bash
git clone <your-repo-url>
cd Poster
python -m venv venv && source venv/bin/activate   # Windows: .\venv\Scripts\activate
pip install -r requirements.txt

export API_ID=1234567
export API_HASH="your_api_hash"
export BOT_TOKEN="123456:ABC-DEF..."

python main.py
```

The bot downloads its fonts on first start. To fetch them in advance:

```bash
python -c "import dataset; print('Missing fonts:', dataset.ensure_fonts())"
```

---

## ⚙️ Configuration

Create a `.env` file or set these in your deployment environment.

### 🔑 Required

| Variable | Description |
| :--- | :--- |
| `API_ID` | Telegram API ID from [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | Telegram API Hash from [my.telegram.org](https://my.telegram.org) |
| `BOT_TOKEN` | Bot token from [@BotFather](https://t.me/BotFather) |

### 🔗 Link provider

| Variable | Description | Default |
| :--- | :--- | :--- |
| `ADMIN_ID` | Owner user id — unlocks the link-provider admin panel and broadcast | `0` |
| `OWNER_ID` | Owner user id (falls back to `ADMIN_ID`) | `ADMIN_ID` |
| `PUBLIC_ANIME_CHANNEL_URL` | Channel link used when a user is not subscribed | `MAIN_CHANNEL_URL` |
| `LINK_EXPIRY_MINUTES` | How long a generated invite stays valid (`0` = permanent) | `5` |
| `BOT_NAME` | Display name | `Anime Poster Bot` |

### 🗄️ Storage

| Variable | Description | Default |
| :--- | :--- | :--- |
| `MONGO_URI` | MongoDB URI. Empty = local JSON under `DATA_DIR` | *Empty* |
| `MONGO_DB` | MongoDB database name | `poster_bot` |
| `DATA_DIR` | Folder for the JSON stores | `./data` |
| `MAX_CHANNELS` | Channels one user may register for posting | `5` |

### 🎨 Rendering

| Variable | Description | Default |
| :--- | :--- | :--- |
| `BRAND_TOP` / `BRAND_BOTTOM` | Two-tone brand lockup (styles 8 & 13) | `ANI` / `CROX` |
| `FANART_API_KEY` | [fanart.tv](https://fanart.tv/) key for character art | *Pre-configured* |
| `TMDB_API_KEY` | TMDB key for fallback title matching | *Pre-configured* |
| `USE_CHARACTER_PNG` | Enable fanart.tv transparent character search | `1` |
| `USE_ANILIST_CUTOUT` | Cut out AniList characters with `rembg` | `0` |
| `POSTER_CHOICES` / `BANNER_CHOICES` | Alternative posters / banners to index | `12` / `12` |
| `RENDER_WORKERS` | Simultaneous render workers | `2` |

### 🌐 Server

| Variable | Description | Default |
| :--- | :--- | :--- |
| `MAIN_CHANNEL_URL` / `SUPPORT_URL` | Links shown in the help menu | Cantarella Bots |
| `PORT` | Health-check port (binds `0.0.0.0:PORT` when `> 0`) | `0` (off) |
| `LOG_LEVEL` | `INFO`, `DEBUG`, `WARNING`, `ERROR` | `INFO` |
| `ALLOWED_USERS` | Comma-separated ids for private-bot mode (blank = public) | *Empty* |

---

## 🐳 Docker

```bash
docker build -t anime-bot .
docker run -d --name anime-bot --restart unless-stopped \
  -e API_ID=1234567 -e API_HASH=... -e BOT_TOKEN=... \
  -e ADMIN_ID=123456789 -e MONGO_URI="mongodb+srv://..." -e PORT=8080 \
  -p 8080:8080 anime-bot
```

A `Procfile` (`worker: python main.py`) is included for Heroku-style hosts. On Render / Koyeb / Railway set
the start command to `python main.py` and `PORT=8080` to switch on the health-check server.

---

## 🧪 Tests

```bash
pip install pytest
python -m pytest test_links.py -v
```

The suite covers the link provider: the real JSON storage backend, the force-sub gate, link delivery with all
its fallbacks, deep links, the keyboards and the handler wiring.

---

## 🗂️ Project layout

```
Poster/
├── main.py            # entry point: health server, client, handler registration
├── config.py          # all environment settings
├── cmds.py            # poster studio: commands, style picker, poster buttons
├── chnl.py            # channel registration + 📣 post-to-channel flow
├── links.py           # 🔗 link provider: gate, link generation, admin panel, broadcast
├── linkstore.py       # link-provider storage (MongoDB or JSON)
├── chstore.py         # poster-studio channel storage (MongoDB or JSON)
├── dataset.py         # AniList + fanart.tv data, font download, render dispatch
├── chname.py          # channel branding typography
├── watermark.py       # watermark seal / verify tool
├── ui.py              # small-caps styling + button/keyboard helpers
├── Templates/         # the 18 poster renderers (+ nova_kit.py, the shared drawing kit of the nova styles)
└── test_links.py      # link-provider tests
```

---

## 🔒 Watermark tools

```bash
python watermark.py newkey                 # generate a WATERMARK_KEY
python watermark.py seal "Your Brand"      # seal text with the key
python watermark.py verify poster.png      # check an image for your signature
```

---

## 👥 Credits

- **Main channel**: [Cantarella Bots (@cantarellabots)](https://t.me/cantarellabots)
- **Support chat**: [Cantarella Bots Chat (@CantarellaBotschat)](https://t.me/CantarellaBotschat)
- **Data**: [AniList GraphQL API](https://anilist.gitbook.io/anilist-apiv2-docs/) · [fanart.tv](https://fanart.tv/)
- **Framework**: [Kurigram / Pyrogram](https://github.com/Kurigram/Kurigram)

<div align="center">
Made with ❤️ by <a href="https://t.me/cantarellabots"><b>Cantarella Bots</b></a>
</div>

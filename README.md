# 🎨 Anime Poster Studio Bot

<div align="center">

[![Python Version](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-Channel-2CA5E0?logo=telegram&logoColor=white)](https://t.me/cantarellabots)
[![Support](https://img.shields.io/badge/Telegram-Support%20Chat-0088cc?logo=telegram&logoColor=white)](https://t.me/CantarellaBotschat)
[![Library](https://img.shields.io/badge/Library-Kurigram%20%2F%20Pyrogram-blue)](https://github.com/Kurigram/Kurigram)
[![Engine](https://img.shields.io/badge/Image%20Engine-Pillow-yellow)](https://python-pillow.org/)

A Telegram bot that turns any anime into **14 ready-to-post poster / thumbnail styles**, straight from AniList.

Send a title, tap a style, fine-tune it, and download the full-quality PNG — or push it straight to your channel.

Every screen is a thumbnail photo with inline buttons and a way back home, so the whole thing feels like one app.

</div>

---

## ✨ What's inside

| Feature | What it does |
| :--- | :--- |
| 🎨 **14 poster styles** | Full HD (1920×1080), HD (1280×720) and 1600×900 designs, rendered live. |
| 🖼️ **Dynamic artwork** | Cycle transparent fanart.tv character cut-outs, AniList posters and banners right from the buttons. |
| 🔥 **Trending** | One tap shows what AniList is buzzing about, ready to turn into a poster. |
| ⚙️ **Fine-tune** | Swap the character / artwork, change the button text, add your channel branding. |
| 📁 **Full-quality export** | Instant JPEG preview in chat, plus a lossless PNG on demand. |
| 📣 **Direct to channel** | Attach a rich caption (formatting and custom emoji preserved) and inline URL buttons, preview, then post. |

> **Out of scope on purpose:** the moderation suite (bans, mutes, warns, locks, filters, welcome messages,
> night mode, logging) and the link-provider feature are **not** part of this bot. This is a poster studio only.

---

## 🕹️ How to use it

1. **Send an anime name** — or tap 🔥 **trending** to pick from what's hot right now.
2. **Choose a style** — tap a number, or browse with 👀 **previews**.
3. **Fine-tune it** — ◀ ▶ flips styles, ⚙️ **options** swaps the art, the button text and your branding.
4. **Take it away** — 📁 **full quality file** for the PNG, 📣 **post to channel** to publish it.

Every screen keeps a 🏠 **home** button, so you can never get stuck.

---

## 🤖 Commands

| Command | Description |
| :--- | :--- |
| `/start` | Home screen |
| `/poster <anime>` | Make a poster for the given anime |
| `/styles` | Preview every poster style, one by one |
| `/trending` | What's hot on AniList right now |
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

The bot downloads its fonts on first start (into both `fonts/` and `Templates/fonts/`), so the very first
run needs network access. To fetch them in advance:

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

### 🤖 Identity

| Variable | Description | Default |
| :--- | :--- | :--- |
| `BOT_NAME` | Display name | `Anime Poster Bot` |
| `ADMIN_ID` | Owner user id | `0` |

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

The image deliberately uses **Python 3.11** (not the newest release) and pins every dependency, because the
Kurigram/Pyrogram MTProto stack is best tested there. `numpy` is held below 2.5 for the same reason — 2.5+
requires Python 3.12+. A `.dockerignore` keeps `.env`, session files and runtime data out of the image.

---

## 🧪 Tests

```bash
pip install pytest
python -m pytest test_ui.py -v
```

The suite covers the interface: every keyboard is checked for a way back home, the style grid is checked to
list all 14 styles, and the inline-button router is driven with real callback data to prove each button
reaches the right screen.

---

## 🗂️ Project layout

```
Poster/
├── main.py            # entry point: health server, client, handler registration
├── config.py          # all environment settings
├── cmds.py            # poster studio: commands, style picker, poster buttons
├── chnl.py            # channel registration + 📣 post-to-channel flow
├── chstore.py         # poster-studio channel storage (MongoDB or JSON)
├── dataset.py         # AniList + fanart.tv data, font download, render dispatch
├── chname.py          # channel branding typography
├── watermark.py       # watermark seal / verify tool
├── ui.py              # small-caps styling + button/keyboard helpers
├── Templates/         # the 14 poster renderers
└── test_ui.py         # interface + router tests
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

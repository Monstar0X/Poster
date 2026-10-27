# Python 3.11 - deliberately NOT the newest release: Pyrogram/Kurigram's
# MTProto stack is best tested here, and it avoids the 3.13 asyncio changes.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

WORKDIR /app

# DejaVu = last-resort font the templates fall back to
RUN apt-get update \
 && apt-get install -y --no-install-recommends fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/*

# deps first so code edits don't bust the pip layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# pre-download Poppins / Lora / Anton / Noto Sans JP ... ; never fail the build
# if it has no internet - main.py retries at start-up
RUN python -c "import dataset; print('missing fonts:', dataset.ensure_fonts())" || true

RUN useradd -m bot && chown -R bot:bot /app
USER bot

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request;urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8080')+'/').read()" || exit 1

CMD ["python", "main.py"]

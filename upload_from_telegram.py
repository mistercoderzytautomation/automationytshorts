import os
import json
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# ========= ENV =========
API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
SESSION = os.environ["TELEGRAM_SESSION"]
CHANNEL_ID = int(os.environ["TELEGRAM_CHANNEL_ID"])
YOUTUBE_JSON = os.environ["YOUTUBE_CLIENT_SECRET_JSON"]

# ========= FILES =========
STATE_FILE = "uploaded_ids.json"
VIDEO_FILE = "video.mp4"

# ========= LOAD STATE =========
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        uploaded_ids = set(json.load(f))
else:
    uploaded_ids = set()

# ========= YOUTUBE =========
creds = Credentials.from_authorized_user_info(json.loads(YOUTUBE_JSON))
youtube = build("youtube", "v3", credentials=creds)

# ========= TELEGRAM =========
client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

async def main():
    await client.start()

    async for msg in client.iter_messages(CHANNEL_ID, limit=20):
        if not msg.video:
            continue

        if msg.id in uploaded_ids:
            continue

        print(f"Uploading video from Telegram msg {msg.id}")

        await msg.download_media(file=VIDEO_FILE)

        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": msg.text[:100] if msg.text else "Daily Short",
                    "description": msg.text or "",
                    "tags": ["shorts"],
                    "categoryId": "22"
                },
                "status": {
                    "privacyStatus": "public"
                }
            },
            media_body=MediaFileUpload(VIDEO_FILE, chunksize=-1, resumable=True)
        )

        response = request.execute()
        print("Uploaded:", response["id"])

        uploaded_ids.add(msg.id)
        break  # ✅ upload ONLY ONE per run

    with open(STATE_FILE, "w") as f:
        json.dump(list(uploaded_ids), f)

    await client.disconnect()

asyncio.run(main())

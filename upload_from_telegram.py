import os
import json
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import MessageMediaVideo

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ================== ENV ==================
API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
SESSION = os.environ["TELEGRAM_SESSION"]
CHANNEL_ID = int(os.environ["TELEGRAM_CHANNEL_ID"])
YOUTUBE_JSON = os.environ["YOUTUBE_CLIENT_SECRET_JSON"]

STATE_FILE = "uploaded_ids.json"
VIDEO_FILE = "video.mp4"

# ================== STATE ==================
def load_uploaded_ids():
    if not os.path.exists(STATE_FILE):
        return set()
    with open(STATE_FILE, "r") as f:
        return set(json.load(f))

def save_uploaded_ids(ids):
    with open(STATE_FILE, "w") as f:
        json.dump(list(ids), f)

# ================== YOUTUBE ==================
def get_youtube():
    creds = Credentials.from_authorized_user_info(json.loads(YOUTUBE_JSON))
    return build("youtube", "v3", credentials=creds)

def upload_to_youtube(path, title, description):
    yt = get_youtube()

    request = yt.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title[:100],
                "description": description,
                "tags": ["shorts", "viral"],
                "categoryId": "22",
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False,
            },
        },
        media_body=MediaFileUpload(path, resumable=True),
    )

    response = request.execute()
    print("✅ Uploaded:", response["id"])

# ================== MAIN ==================
async def main():
    uploaded_ids = load_uploaded_ids()

    async with TelegramClient(StringSession(SESSION), API_ID, API_HASH) as client:
        async for msg in client.iter_messages(CHANNEL_ID):
            if not msg.video:
                continue

            if msg.id in uploaded_ids:
                continue

            print("⬇ Downloading video...")
            await msg.download_media(VIDEO_FILE)

            title = msg.text.split("\n")[0] if msg.text else "YouTube Short"
            description = msg.text if msg.text else "Uploaded via automation"

            upload_to_youtube(VIDEO_FILE, title, description)

            uploaded_ids.add(msg.id)
            save_uploaded_ids(uploaded_ids)

            os.remove(VIDEO_FILE)
            return

        print("⚠ No new videos found.")

asyncio.run(main())

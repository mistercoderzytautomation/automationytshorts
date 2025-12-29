import os
import json
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# ---------------- CONFIG ----------------

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
SESSION_STRING = os.environ.get("TELEGRAM_SESSION", "")

CHANNEL_ID = int(os.environ["TELEGRAM_CHANNEL_ID"])

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

USED_FILE = "used_messages.json"
VIDEO_FILE = "video.mp4"

# ---------------------------------------


def load_used():
    if os.path.exists(USED_FILE):
        with open(USED_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_used(data):
    with open(USED_FILE, "w") as f:
        json.dump(list(data), f)


def get_youtube():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            "client_secret.json", SCOPES
        )
        creds = flow.run_console()
        with open("token.json", "w") as f:
            f.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


async def main():
    used = load_used()

    client = TelegramClient(
        StringSession(SESSION_STRING) if SESSION_STRING else "session",
        API_ID,
        API_HASH,
    )

    await client.start()

    async for msg in client.iter_messages(CHANNEL_ID, reverse=True):
        if msg.id in used:
            continue

        if not msg.video:
            continue

        # ---------- DOWNLOAD ----------
        await client.download_media(msg.video, VIDEO_FILE)

        title = msg.text.strip() if msg.text else "Daily Short"
        description = title

        # ---------- UPLOAD ----------
        youtube = get_youtube()

        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title[:95],
                    "description": description,
                    "categoryId": "22",
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False,
                },
            },
            media_body=MediaFileUpload(VIDEO_FILE, chunksize=-1, resumable=True),
        )

        response = request.execute()
        print("Uploaded:", response["id"])

        used.add(msg.id)
        save_used(used)

        os.remove(VIDEO_FILE)
        break

    else:
        print("No new videos left.")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

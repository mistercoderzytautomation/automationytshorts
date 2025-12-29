import os
import json
import tempfile
from telethon import TelegramClient
from telethon.tl.types import MessageMediaVideo
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# ===== ENV =====
API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
PHONE = os.environ["TG_PHONE"]
CHANNEL_ID = int(os.environ["TELEGRAM_CHANNEL_ID"])
YOUTUBE_JSON = os.environ["YOUTUBE_CLIENT_SECRET_JSON"]

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
STATE_FILE = "state.json"
TOKEN_FILE = "token.json"

# ===== STATE =====
def load_state():
    if not os.path.exists(STATE_FILE):
        return {"last_msg_id": 0}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# ===== YOUTUBE =====
def get_youtube():
    with open("client_secret.json", "w") as f:
        f.write(YOUTUBE_JSON)

    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            "client_secret.json", SCOPES
        )
        creds = flow.run_console()
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)

def upload_to_youtube(path, title):
    yt = get_youtube()
    yt.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": title,
                "tags": ["shorts"],
                "categoryId": "22"
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=MediaFileUpload(path)
    ).execute()

# ===== MAIN =====
async def main():
    state = load_state()

    client = TelegramClient("session", API_ID, API_HASH)
    await client.start(phone=PHONE)

    async for msg in client.iter_messages(CHANNEL_ID, min_id=state["last_msg_id"]):
        if msg.id <= state["last_msg_id"]:
            continue

        if msg.video:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            await client.download_media(msg.video, tmp.name)

            upload_to_youtube(tmp.name, f"Daily Short #{msg.id}")

            state["last_msg_id"] = msg.id
            save_state(state)
            print("Uploaded video, message ID:", msg.id)
            return

    print("No new videos found.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

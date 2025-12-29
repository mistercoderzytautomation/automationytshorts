import os
import json
import requests
import tempfile
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]
CLIENT_SECRET_JSON = os.environ["YOUTUBE_CLIENT_SECRET_JSON"]

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
STATE_FILE = "state.json"
TOKEN_FILE = "token.json"

def get_updates():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    return requests.get(url).json()["result"]

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"last_index": 0}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def get_youtube_service():
    with open("client_secret.json", "w") as f:
        f.write(CLIENT_SECRET_JSON)

    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            "client_secret.json", SCOPES
        )
        creds = flow.run_console()
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)

def download_video(file_id):
    file_info = requests.get(
        f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
    ).json()
    file_path = file_info["result"]["file_path"]

    video_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    video_data = requests.get(video_url).content

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tmp.write(video_data)
    tmp.close()
    return tmp.name

def upload_to_youtube(video_path, title):
    youtube = get_youtube_service()

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": title,
                "tags": ["shorts"],
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(video_path)
    )
    request.execute()

def main():
    updates = get_updates()
    videos = []

    for u in updates:
        post = u.get("channel_post")
        if post and "video" in post:
            if str(post["chat"]["id"]) == CHANNEL_ID:
                videos.append(post["video"]["file_id"])

    videos.sort()
    state = load_state()

    if state["last_index"] >= len(videos):
        print("No videos left.")
        return

    file_id = videos[state["last_index"]]
    print("Uploading video index:", state["last_index"])

    video_path = download_video(file_id)
    upload_to_youtube(video_path, f"Daily Short #{state['last_index'] + 1}")

    state["last_index"] += 1
    save_state(state)
    print("Upload complete.")

if __name__ == "__main__":
    main()

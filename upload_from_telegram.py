import os
import json
import requests

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]

STATE_FILE = "state.json"

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
        print("No more videos left.")
        return

    video_file_id = videos[state["last_index"]]
    print("Ready video file_id:", video_file_id)

    # 🚧 PLACEHOLDER
    # In next step we will upload this to YouTube

    state["last_index"] += 1
    save_state(state)
    print("State updated")

if __name__ == "__main__":
    main()

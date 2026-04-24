import os
import json
import feedparser
import requests
import threading
import websocket
import json
import time
import re
from html import unescape
from datetime import datetime, timezone
from apscheduler.schedulers.blocking import BlockingScheduler


RSS_URL = "https://steamcommunity.com/groups/GrabFreeGames/rss/"
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
STATE_FILE = "last_items.json"

DISCORD_API_URL = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/messages"


def load_state():
    # If file doesn't exist → create it with default state
    if not os.path.exists(STATE_FILE):
        save_state({"seen_ids": []})
        return {"seen_ids": []}

    try:
        with open(STATE_FILE, "r") as f:
            data = f.read().strip()

            # Empty file → reset it
            if not data:
                save_state({"seen_ids": []})
                return {"seen_ids": []}

            return json.loads(data)

    except Exception:
        # Corrupted JSON → reset it
        save_state({"seen_ids": []})
        return {"seen_ids": []}


def save_state(state):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE_FILE)



def send_embed_to_discord(title, link, description=None, image=None):
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json"
    }
    # Clean the description (HTML → Markdown)
    cleaned_description = html_to_markdown(description) if description else "A new free game has been posted!"
    
    embed = {
        "title": title,
        "url": link,
        "description": cleaned_description,
        "color": 0x00AEEF,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if image:
        embed["thumbnail"] = {"url": image}
    payload = {"embeds": [embed]}
    response = requests.post(DISCORD_API_URL, headers=headers, json=payload)
    if response.status_code not in (200, 201):
        print(f"Failed to send embed: {response.status_code} - {response.text}")



def extract_image(entry):
    # Steam RSS sometimes includes media:thumbnail or images in summary
    if "media_thumbnail" in entry:
        return entry.media_thumbnail[0]["url"]
    if "media_content" in entry:
        return entry.media_content[0]["url"]
    return None


def check_rss():
    print(f"[{datetime.now()}] Checking RSS feed...")
    feed = feedparser.parse(RSS_URL)

    state = load_state()
    seen_ids = set(state.get("seen_ids", []))
    new_seen_ids = set(seen_ids)

    for entry in feed.entries:
        entry_id = entry.get("id") or entry.get("link")

        if entry_id not in seen_ids:
            print(f"New item found: {entry.title}")

            image = extract_image(entry)
            description = getattr(entry, "summary", None)

            send_embed_to_discord(
                title=entry.title,
                link=entry.link,
                description=description,
                image=image
            )

            new_seen_ids.add(entry_id)

    state["seen_ids"] = list(new_seen_ids)
    save_state(state)
    print("RSS check complete.")

def start_presence_thread():
    def run():
        ws = websocket.WebSocket()
        ws.connect("wss://gateway.discord.gg/?v=10&encoding=json")

        hello = json.loads(ws.recv())
        heartbeat_interval = hello["d"]["heartbeat_interval"] / 1000

        identify = {
            "op": 2,
            "d": {
                "token": DISCORD_TOKEN,
                "intents": 0,
                "properties": {
                    "os": "linux",
                    "browser": "my_library",
                    "device": "my_library"
                }
            }
        }

        ws.send(json.dumps(identify))

        while True:
            ws.send(json.dumps({"op": 1, "d": None}))
            time.sleep(heartbeat_interval)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

def send_startup_embed():
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json"
    }

    embed = {
        "title": "🟢 Bot Online",
        "description": "The Free Games bot has started successfully and is now watching for new items.",
        "color": 0x00FF00,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    payload = {"embeds": [embed]}

    response = requests.post(DISCORD_API_URL, headers=headers, json=payload)
    if response.status_code not in (200, 201):
        print(f"Failed to send startup embed: {response.status_code} - {response.text}")


def html_to_markdown(raw_html):
    if not raw_html:
        return ""
    text = raw_html
    # Convert <li> to "- "
    text = re.sub(r'<li[^>]*>', '- ', text)
    text = text.replace('</li>', '\n')
    # Convert <br> to newline
    text = re.sub(r'<br\s*/?>', '\n', text)
    # Convert <blockquote> to Markdown quote
    text = re.sub(r'<blockquote[^>]*>', '> ', text)
    text = text.replace('</blockquote>', '\n')
    # Remove all remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities (&amp;, &quot;, etc.)
    text = unescape(text)
    # Clean up whitespace
    text = re.sub(r'\n\s*\n+', '\n', text).strip()
    return text



def main():
    start_presence_thread()
    send_startup_embed()
    scheduler = BlockingScheduler()
    scheduler.add_job(check_rss, "interval", minutes=10)
    print("Bot started. Checking every 10 minutes...")
    scheduler.start()


if __name__ == "__main__":
    main()

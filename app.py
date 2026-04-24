import os
import json
import feedparser
import requests
from datetime import datetime, timezone
from apscheduler.schedulers.blocking import BlockingScheduler

RSS_URL = "https://steamcommunity.com/groups/GrabFreeGames/rss/"
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
STATE_FILE = "last_items.json"

DISCORD_API_URL = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/messages"


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"seen_ids": []}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def send_embed_to_discord(title, link, description=None, image=None):
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json"
    }

    embed = {
        "title": title,
        "url": link,
        "description": description or "A new free game has been posted!",
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


def main():
    scheduler = BlockingScheduler()
    scheduler.add_job(check_rss, "interval", minutes=10)
    print("Bot started. Checking every 10 minutes...")
    scheduler.start()


if __name__ == "__main__":
    main()

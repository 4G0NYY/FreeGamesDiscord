import os
import json
import feedparser
import requests
from datetime import datetime
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


def send_to_discord(title, link):
    if not DISCORD_TOKEN or not DISCORD_CHANNEL_ID:
        print("Missing DISCORD_TOKEN or DISCORD_CHANNEL_ID environment variables")
        return

    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "content": f"🎮 **New Free Game Posted!**\n**{title}**\n{link}"
    }

    response = requests.post(DISCORD_API_URL, headers=headers, json=payload)

    if response.status_code not in (200, 201):
        print(f"Failed to send message: {response.status_code} - {response.text}")


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
            send_to_discord(entry.title, entry.link)
            new_seen_ids.add(entry_id)

    state["seen_ids"] = list(new_seen_ids)
    save_state(state)
    print("RSS check complete.")


def main():
    scheduler = BlockingScheduler()
    scheduler.add_job(check_rss, "cron", hour=7, minute=0)
    print("Scheduler started. Waiting for next run at 07:00...")
    scheduler.start()


if __name__ == "__main__":
    main()

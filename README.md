# FreeGamesDiscord

A lightweight Discord bot that checks the Steam Grab Free Games RSS feed every 10 minutes and posts new free game entries to a Discord channel using rich embeds.

## What This Project Does

- Polls the RSS feed: `https://steamcommunity.com/groups/GrabFreeGames/rss/`
- Tracks already-posted items in `last_items.json`
- Sends new items to a Discord channel with:
	- Title and link
	- Summary/description
	- Thumbnail (when available)
- Runs continuously with a scheduler (`APScheduler`)

## Tech Stack

- Python 3.12
- `feedparser` for RSS parsing
- `requests` for Discord API calls
- `apscheduler` for periodic jobs
- Docker + Docker Compose support

## Project Structure

```text
.
|- app.py
|- requirements.txt
|- Dockerfile
|- docker-compose.yml
|- env.template
`- README.md
```

## Prerequisites

Before starting, make sure you have:

- A Discord server where you can add a bot
- A Discord bot token
- A Discord channel ID
- One of the following runtime options:
	- Python 3.12+ (for local run)
	- Docker Desktop (for container run)

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd FreeGamesDiscord
```

### 2. Create Environment File

Create a `.env` file in the project root using `env.template` as a reference.

Example `.env`:

```env
DISCORD_TOKEN=your_bot_token_here
DISCORD_CHANNEL_ID=123456789012345678
```

### 3. Configure Discord Bot Permissions

Ensure your bot can post in the target channel.

Minimum required permissions:

- View Channel
- Send Messages
- Embed Links

## Run Option A: Local Python

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the bot

```bash
python app.py
```

You should see:

- `Bot started. Checking every 10 minutes...`
- RSS check logs every 10 minutes

## Run Option B: Docker

### Build image

```bash
docker build -t freegames-discord-bot .
```

### Run container

```bash
docker run -d \
	--name freegames-discord-bot \
	--env-file .env \
	--restart unless-stopped \
	freegames-discord-bot
```

### View logs

```bash
docker logs -f freegames-discord-bot
```

## Run Option C: Docker Compose

```bash
docker compose up -d --build
```

Then check logs:

```bash
docker compose logs -f
```

## Configuration Reference

Environment variables used by the app:

- `DISCORD_TOKEN`: Discord bot token
- `DISCORD_CHANNEL_ID`: Target Discord channel ID where messages are posted

Hardcoded runtime behavior in `app.py`:

- RSS URL: Steam Grab Free Games feed
- Check interval: 10 minutes
- State file: `last_items.json`

## How Duplicate Prevention Works

The bot stores seen entry IDs/links in `last_items.json`. On each RSS check:

1. It loads previous IDs
2. It compares current feed entries
3. It sends only unseen entries
4. It saves the updated seen list

This prevents reposting the same giveaway repeatedly.

## Troubleshooting

### No messages in Discord channel

- Verify `DISCORD_TOKEN` is valid
- Verify `DISCORD_CHANNEL_ID` is correct
- Verify bot permissions in that channel
- Confirm the bot is online and present in the server

### Discord API errors in logs

- `401 Unauthorized`: token is invalid
- `403 Forbidden`: missing permissions for the channel
- `404 Not Found`: channel ID is invalid or inaccessible

### Docker Compose note about state persistence

The current `docker-compose.yml` mounts `./data` to `/app`. This can hide files copied into the image if `./data` does not contain the app files.

If this happens, either:

- Run with Docker (Option B), or
- Adjust the volume mapping so only the state file (or a state directory) is persisted.

## Operations

### Stop local run

Press `Ctrl+C` in the terminal.

### Stop Docker container

```bash
docker stop freegames-discord-bot
```

### Stop Docker Compose

```bash
docker compose down
```

## License

Add your preferred license (for example, MIT) in a `LICENSE` file.

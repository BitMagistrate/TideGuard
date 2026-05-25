# TideGuard Telegram bot

Lightweight Telegram bot acting as an entry point for citizen reports
and "where is plastic right now?" queries. The bot is intentionally
*thin* — it doesn't replicate the web platform, it just relays user
input to the public API.

## Why

Many volunteers in coastal towns of Russia have Telegram but not the
mobile app. The bot is a parallel onboarding ramp, not a replacement.

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message + brief description |
| `/forecast <lat> <lon>` | Returns the latest debris-concentration forecast for the given coordinates |
| `/report <lat> <lon> <severity> <debris_type>` | Submits a citizen report (anonymous) |
| `/lessons` | Lists the 10 open-source lessons |
| `/cleanup` | Shows nearest upcoming organised cleanup |
| `/help` | Lists all commands |

## Running

```bash
cd apps/bot
uv venv && uv pip install -e .
export TIDEGUARD_BOT_TOKEN=...
export TIDEGUARD_API_BASE=https://api.tideguard.app
uv run python -m tideguard_bot
```

## Privacy

- The bot does not retain user IDs after a single session.
- Geolocations are forwarded to the API only if the user explicitly
  invokes `/report` or `/forecast` with coordinates.
- The bot is read-only for `/lessons`, `/cleanup` and `/forecast` —
  no auth is required.

## Deployment

The bot is intentionally not deployed automatically. Once a Telegram
token is provisioned, deploy as a single Fly.io machine using the
`fly.toml` in this directory.

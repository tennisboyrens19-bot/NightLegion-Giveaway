# NightLegion Giveaway Bot — Standalone

This is a completely separate Discord bot. It does **not** import, modify, read, or depend on the BOTW bot.

## What it does

- `/giveaway_start prize duration winners`
- Automatic OSRS item matching
- OSRS Wiki item thumbnails
- Live OSRS Wiki/GE price at giveaway creation
- Custom generated giveaway banner
- Persistent **Enter Giveaway**, **My Stats**, **Entrants**, and **Info** buttons
- No required Discord role to enter
- Automatic ending and cryptographically strong random winner selection (`SystemRandom`)
- Tracks every member's number of entries and wins
- Owner/admin-only full entrant list with Discord ID, previous wins, and entry time
- `/giveaway_reroll`, `/giveaway_cancel`, `/giveaway_mark_paid`
- `/giveaway_history`
- Data survives bot restarts when `DATA_DIR` points at a persistent disk

## Separate from BOTW

Use a **new Discord Application / Bot token**, a **new GitHub repository**, and a **new Render Web Service/Background Worker** for this bot.

The only runtime data file is:

`DATA_DIR/giveaways.json`

It does not touch BOTW JSON files.

## Local test

1. Install Python 3.11+.
2. Copy `.env.example` to `.env`.
3. Put the **new giveaway bot token** in `DISCORD_TOKEN`.
4. Optional: put your Discord server ID in `TEST_GUILD_ID` for immediate slash-command sync.
5. Run:

```powershell
py -m pip install -r requirements.txt
py bot.py
```

## Render

Recommended settings:

- Build command: `pip install -r requirements.txt`
- Start command: `python bot.py`
- Environment: `DISCORD_TOKEN=<new giveaway bot token>`
- Persistent disk mount: `/var/data`
- Environment: `DATA_DIR=/var/data`

Never reuse or expose the BOTW bot token.

## Examples

```text
/giveaway_start prize:Twisted bow duration:2d winners:1
/giveaway_start prize:500m duration:12h winners:2
/giveaway_start prize:2x Bond duration:7d winners:1
```

Normal users press **Enter Giveaway**. The **Entrants** button exists on the post but only the server owner/admin/manage-server users can open the private entrant list.

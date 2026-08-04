from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)

GIVEAWAYS_FILE = DATA_DIR / "giveaways.json"

# Optional: set this to a single Discord server ID while testing so slash commands
# sync instantly to that server. Leave blank for global commands in production.
TEST_GUILD_ID = int(os.getenv("TEST_GUILD_ID", "0") or 0)

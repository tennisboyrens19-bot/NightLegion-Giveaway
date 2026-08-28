from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path

from discord.ext import commands, tasks

from config import DATA_DIR, GIVEAWAYS_FILE
from storage import load_json, save_json
from giveaway.cog import member_has_required_role, required_role_id

log = logging.getLogger("giveaway-bot.runelite")
REQUESTS_FILE = Path(DATA_DIR) / "runelite_requests.jsonl"
RESULTS_FILE = Path(DATA_DIR) / "runelite_results.jsonl"
MAX_LINE_BYTES = 16 * 1024
RESULT_TTL = 15 * 60


def _append_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line)
        fh.flush()


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    try:
        with path.open("r", encoding="utf-8") as fh:
            for raw in fh:
                if len(raw.encode("utf-8", "ignore")) > MAX_LINE_BYTES:
                    continue
                try:
                    row = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(row, dict):
                    rows.append(row)
    except OSError:
        return []
    return rows


class RuneLiteGiveawayBridge(commands.Cog):
    """Processes RuneLite giveaway entry requests inside the real Giveaway bot.

    Both Discord bots run in the same Render worker and share /var/data. The
    NightLegion companion appends tiny JSONL requests; this cog validates them
    against the authoritative Giveaway data and refreshes the real Discord post.
    """

    def __init__(self, bot):
        self.bot = bot
        self.processed = set()
        self.bridge_loop.start()

    async def cog_load(self):
        now = int(time.time())
        for row in _read_jsonl(RESULTS_FILE):
            if now - int(row.get("at") or 0) <= RESULT_TTL:
                request_id = str(row.get("request_id") or "")
                if request_id:
                    self.processed.add(request_id)

    def cog_unload(self):
        self.bridge_loop.cancel()

    @tasks.loop(seconds=1)
    async def bridge_loop(self):
        for request in _read_jsonl(REQUESTS_FILE):
            request_id = str(request.get("request_id") or "")
            if not request_id or request_id in self.processed:
                continue
            self.processed.add(request_id)
            try:
                result = await self._process(request)
            except Exception as exc:
                log.exception("RuneLite giveaway request failed")
                result = {"ok": False, "error": f"internal_error:{type(exc).__name__}"}
            result["request_id"] = request_id
            result["at"] = int(time.time())
            _append_json(RESULTS_FILE, result)

    @bridge_loop.before_loop
    async def before_bridge_loop(self):
        await self.bot.wait_until_ready()

    async def _process(self, request: dict) -> dict:
        cog = self.bot.get_cog("Giveaways")
        if cog is None:
            return {"ok": False, "error": "giveaway_cog_not_loaded"}

        gid = str(request.get("giveaway_id") or "")
        try:
            user_id = int(request.get("user_id") or 0)
        except (TypeError, ValueError):
            user_id = 0
        if not gid or not user_id:
            return {"ok": False, "error": "invalid_request"}

        async with cog.data_lock:
            data = load_json(GIVEAWAYS_FILE, {})
            giveaway = data.get(gid)
            if not giveaway:
                return {"ok": False, "error": "giveaway_not_found"}
            if giveaway.get("ended") or giveaway.get("cancelled") or int(giveaway.get("end_time") or 0) <= int(time.time()):
                return {"ok": False, "error": "giveaway_ended"}

            guild_id = int(giveaway.get("guild_id") or 0)
            guild = self.bot.get_guild(guild_id) if guild_id else None
            if guild is None:
                return {"ok": False, "error": "guild_not_found"}
            try:
                member = await guild.fetch_member(user_id)
            except Exception:
                return {"ok": False, "error": "member_not_found"}

            if required_role_id(giveaway) is not None and not member_has_required_role(member, giveaway):
                return {
                    "ok": False,
                    "error": "rank_required",
                    "required_role_name": giveaway.get("required_role_name"),
                }

            uid = str(user_id)
            entries = [str(v) for v in giveaway.setdefault("entries", [])]
            if uid in entries:
                return {"ok": True, "message": "✅ You are already entered in this giveaway."}

            giveaway["entries"].append(uid)
            giveaway.setdefault("entry_times", {})[uid] = int(time.time())
            save_json(GIVEAWAYS_FILE, data)

        await cog.refresh_message(gid)
        stats = cog.user_stats(user_id)
        return {
            "ok": True,
            "message": f"🎉 You're entered! You have entered {stats['entered']} giveaway(s) and won {stats['won']} so far.",
        }


async def setup(bot):
    await bot.add_cog(RuneLiteGiveawayBridge(bot))

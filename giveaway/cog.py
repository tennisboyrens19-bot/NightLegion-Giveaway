from __future__ import annotations

import asyncio
import random
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands, tasks

from config import GIVEAWAYS_FILE
from storage import load_json, save_json

from .graphics import FILENAME, build_giveaway_card
from .osrs import close_session, enrich_giveaway_prize
from .utils import format_gp, now_ts, parse_duration, prettify_item_name
from .views import GiveawayView

BRAND = discord.Color.from_rgb(176, 105, 255)


def is_admin(interaction: discord.Interaction) -> bool:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return False
    perms = interaction.user.guild_permissions
    return (
        interaction.guild.owner_id == interaction.user.id
        or perms.administrator
        or perms.manage_guild
    )


def _member_name(guild: Optional[discord.Guild], user_id: str) -> str:
    if guild:
        member = guild.get_member(int(user_id))
        if member:
            return member.display_name
    return f"User {user_id}"


def required_role_id(giveaway: dict) -> Optional[int]:
    """Return the optional required role while keeping old giveaways open."""
    role_id = giveaway.get("required_role_id")
    if role_id in (None, ""):
        return None
    try:
        return int(role_id)
    except (TypeError, ValueError):
        return None


def member_has_required_role(member: discord.Member, giveaway: dict) -> bool:
    role_id = required_role_id(giveaway)
    if role_id is None:
        return True
    return any(role.id == role_id for role in member.roles)


def required_rank_text(giveaway: dict) -> str:
    role_id = required_role_id(giveaway)
    return f"<@&{role_id}>" if role_id is not None else "None — everyone can enter."


class Giveaways(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data_lock = asyncio.Lock()
        self.giveaway_check_loop.start()

    async def cog_load(self):
        data = load_json(GIVEAWAYS_FILE, {})
        for gid, giveaway in data.items():
            message_id = giveaway.get("message_id")
            if not message_id:
                continue
            # Persistent views survive bot restarts. Ended giveaways still keep
            # Stats/Entrants/Info available, with Enter disabled.
            self.bot.add_view(
                GiveawayView(self, gid, ended=bool(giveaway.get("ended"))),
                message_id=int(message_id),
            )

    def cog_unload(self):
        self.giveaway_check_loop.cancel()
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(close_session())
        except RuntimeError:
            pass

    # ------------------------------------------------------------------
    # Data / display helpers
    # ------------------------------------------------------------------
    @staticmethod
    def prize_label(giveaway: dict) -> str:
        meta = giveaway.get("prize_meta") or {}
        qty = int(meta.get("quantity") or 1)
        if meta.get("type") == "cash":
            return meta.get("price_text") or giveaway.get("prize", "Prize")
        name = prettify_item_name(meta.get("name") or giveaway.get("prize", "Prize"))
        return f"{qty}x {name}" if qty > 1 else name

    def build_embed(self, giveaway: dict) -> discord.Embed:
        ended = bool(giveaway.get("ended"))
        cancelled = bool(giveaway.get("cancelled"))
        meta = giveaway.get("prize_meta") or {}

        if cancelled:
            title = "🚫 NIGHTLEGION GIVEAWAY — CANCELLED"
            color = discord.Color.dark_grey()
        elif ended:
            title = "🏆 NIGHTLEGION GIVEAWAY — ENDED"
            color = discord.Color.gold()
        else:
            title = "🎉 NIGHTLEGION GIVEAWAY 🎉"
            color = BRAND

        label = discord.utils.escape_markdown(self.prize_label(giveaway))
        embed = discord.Embed(
            title=title,
            description=f"# {label}\n{'The winners are in!' if ended and not cancelled else 'Click **Enter Giveaway** below for your chance to win.'}",
            color=color,
        )

        if meta.get("type") == "item" and meta.get("item_id"):
            value = meta.get("total_value")
            if value is not None:
                embed.add_field(name="💰 Live GE Value", value=f"**{format_gp(value)}**", inline=True)
            else:
                embed.add_field(name="💰 Live GE Value", value="Price unavailable", inline=True)
        elif meta.get("type") == "cash":
            embed.add_field(name="💰 Prize Value", value=f"**{format_gp(meta.get('total_value'))}**", inline=True)
        else:
            embed.add_field(name="🎁 Prize Type", value="Custom prize", inline=True)

        embed.add_field(name="👥 Entries", value=f"**{len(giveaway.get('entries', []))}**", inline=True)
        embed.add_field(name="🏆 Winners", value=f"**{giveaway.get('winners_count', 1)}**", inline=True)

        if not ended:
            end_time = int(giveaway["end_time"])
            embed.add_field(name="⏳ Ends", value=f"<t:{end_time}:R>\n<t:{end_time}:f>", inline=False)
            embed.add_field(name="👑 Hosted by", value=f"<@{giveaway['host_id']}>", inline=True)
            requirements = required_rank_text(giveaway)
            if required_role_id(giveaway) is None:
                requirements = "None — one Discord account, one entry."
            else:
                requirements += "\nMust still have this rank when winners are drawn."
            embed.add_field(name="✅ Requirements", value=requirements, inline=True)
        elif not cancelled:
            winners = [str(uid) for uid in giveaway.get("winner_ids", [])]
            winner_text = "\n".join(f"🏆 <@{uid}>" for uid in winners) if winners else "No valid entrants."
            embed.add_field(name="🎊 Winner(s)", value=winner_text, inline=False)
            paid = "✅ Marked paid" if giveaway.get("paid") else "⏳ Not marked paid yet"
            embed.add_field(name="💸 Payout", value=paid, inline=True)
            final_entries = giveaway.get("eligible_entries_count", len(giveaway.get("entries", [])))
            embed.add_field(name="📊 Final entries", value=str(final_entries), inline=True)
            if required_role_id(giveaway) is not None:
                embed.add_field(name="✅ Required rank", value=required_rank_text(giveaway), inline=True)

        if giveaway.get("has_banner"):
            embed.set_image(url=f"attachment://{FILENAME}")
        elif meta.get("image_url"):
            embed.set_thumbnail(url=meta["image_url"])

        lookup_note = "OSRS Wiki artwork + live RuneScape Wiki price data"
        embed.set_footer(text=f"NightLegion Giveaway • {lookup_note} • ID {giveaway.get('id', '')}")
        return embed

    def find_by_message(self, message_id: str) -> tuple[Optional[str], Optional[dict]]:
        data = load_json(GIVEAWAYS_FILE, {})
        for gid, giveaway in data.items():
            if str(giveaway.get("message_id")) == str(message_id):
                return gid, giveaway
        return None, None

    async def get_message(self, giveaway: dict) -> Optional[discord.Message]:
        channel = self.bot.get_channel(int(giveaway.get("channel_id", 0)))
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(int(giveaway.get("channel_id", 0)))
            except Exception:
                return None
        try:
            return await channel.fetch_message(int(giveaway.get("message_id", 0)))
        except Exception:
            return None

    async def refresh_message(self, gid: str):
        data = load_json(GIVEAWAYS_FILE, {})
        giveaway = data.get(gid)
        if not giveaway or not giveaway.get("message_id"):
            return
        message = await self.get_message(giveaway)
        if not message:
            return
        view = GiveawayView(self, gid, ended=bool(giveaway.get("ended")))
        try:
            await message.edit(embed=self.build_embed(giveaway), view=view)
        except discord.HTTPException:
            pass

    def user_stats(self, user_id: int) -> dict:
        uid = str(user_id)
        data = load_json(GIVEAWAYS_FILE, {})
        entered = 0
        won = 0
        total_value = 0
        biggest = 0
        last_win_at = 0
        last_win_prize = None

        for g in data.values():
            entries = [str(x) for x in g.get("entries", [])]
            if uid in entries:
                entered += 1
            if g.get("ended") and not g.get("cancelled") and uid in [str(x) for x in g.get("winner_ids", [])]:
                won += 1
                value = (g.get("prize_meta") or {}).get("total_value")
                if isinstance(value, int):
                    total_value += value
                    biggest = max(biggest, value)
                when = int(g.get("ended_at") or g.get("end_time") or 0)
                if when >= last_win_at:
                    last_win_at = when
                    last_win_prize = self.prize_label(g)

        return {
            "entered": entered,
            "won": won,
            "value": total_value,
            "biggest": biggest,
            "last_win_at": last_win_at,
            "last_win_prize": last_win_prize,
        }

    # ------------------------------------------------------------------
    # Button callbacks
    # ------------------------------------------------------------------
    async def handle_entry(self, interaction: discord.Interaction, gid: str):
        async with self.data_lock:
            data = load_json(GIVEAWAYS_FILE, {})
            giveaway = data.get(gid)
            if not giveaway:
                await interaction.response.send_message("This giveaway no longer exists.", ephemeral=True)
                return
            if giveaway.get("ended") or now_ts() >= int(giveaway.get("end_time", 0)):
                await interaction.response.send_message("This giveaway has ended.", ephemeral=True)
                return

            if required_role_id(giveaway) is not None:
                if not isinstance(interaction.user, discord.Member) or not member_has_required_role(interaction.user, giveaway):
                    rank_name = giveaway.get("required_role_name")
                    rank_text = f"**{rank_name}**" if rank_name else required_rank_text(giveaway)
                    await interaction.response.send_message(
                        f"🔒 You need the {rank_text} rank to enter this giveaway.",
                        ephemeral=True,
                    )
                    return

            uid = str(interaction.user.id)
            entries = [str(x) for x in giveaway.setdefault("entries", [])]
            if uid in entries:
                await interaction.response.send_message("✅ You are already entered in this giveaway.", ephemeral=True)
                return

            giveaway["entries"].append(uid)
            giveaway.setdefault("entry_times", {})[uid] = now_ts()
            save_json(GIVEAWAYS_FILE, data)

        stats = self.user_stats(interaction.user.id)
        await interaction.response.send_message(
            f"🎉 **You're entered!**\nYou have entered **{stats['entered']}** giveaway(s) and won **{stats['won']}** so far.",
            ephemeral=True,
        )
        await self.refresh_message(gid)

    async def send_user_stats(self, interaction: discord.Interaction, user_id: int):
        stats = self.user_stats(user_id)
        member = interaction.guild.get_member(user_id) if interaction.guild else None
        name = member.display_name if member else str(user_id)
        win_rate = (stats["won"] / stats["entered"] * 100) if stats["entered"] else 0

        embed = discord.Embed(title=f"🏆 {name} — Giveaway Stats", color=BRAND)
        embed.add_field(name="🎟️ Entered", value=f"**{stats['entered']}**", inline=True)
        embed.add_field(name="🏆 Won", value=f"**{stats['won']}**", inline=True)
        embed.add_field(name="📈 Win rate", value=f"**{win_rate:.1f}%**", inline=True)
        embed.add_field(name="💰 Total value won", value=f"**{format_gp(stats['value'])}**", inline=True)
        embed.add_field(name="👑 Biggest win", value=f"**{format_gp(stats['biggest'])}**", inline=True)
        if stats["last_win_at"]:
            embed.add_field(name="🕒 Last win", value=f"**{stats['last_win_prize']}**\n<t:{stats['last_win_at']}:R>", inline=False)
        else:
            embed.add_field(name="🕒 Last win", value="No wins yet — good luck!", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def send_entrants(self, interaction: discord.Interaction, gid: str):
        if not is_admin(interaction):
            await interaction.response.send_message("🔒 Only the server owner/admins can view the entrant list.", ephemeral=True)
            return

        data = load_json(GIVEAWAYS_FILE, {})
        giveaway = data.get(gid)
        if not giveaway:
            await interaction.response.send_message("Giveaway not found.", ephemeral=True)
            return

        entries = [str(x) for x in giveaway.get("entries", [])]
        embed = discord.Embed(
            title=f"👥 Entrants — {self.prize_label(giveaway)}",
            description=f"**{len(entries)} total entries**\nOnly admins can see this panel.",
            color=BRAND,
        )
        if not entries:
            embed.add_field(name="Entrants", value="Nobody has entered yet.", inline=False)
        else:
            lines = []
            for index, uid in enumerate(entries, 1):
                wins = self.user_stats(int(uid))["won"]
                entered_at = int((giveaway.get("entry_times") or {}).get(uid, 0))
                time_text = f"<t:{entered_at}:R>" if entered_at else "unknown time"
                lines.append(f"`{index:>3}.` <@{uid}> • ID `{uid}` • 🏆 {wins} wins • {time_text}")

            chunks = []
            current = ""
            for line in lines:
                if len(current) + len(line) + 1 > 1000:
                    chunks.append(current)
                    current = line
                else:
                    current = f"{current}\n{line}" if current else line
            if current:
                chunks.append(current)

            for i, chunk in enumerate(chunks[:10], 1):
                embed.add_field(name="Entrants" if i == 1 else f"Entrants continued ({i})", value=chunk, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def send_info(self, interaction: discord.Interaction, gid: str):
        data = load_json(GIVEAWAYS_FILE, {})
        giveaway = data.get(gid)
        if not giveaway:
            await interaction.response.send_message("Giveaway not found.", ephemeral=True)
            return
        meta = giveaway.get("prize_meta") or {}
        embed = discord.Embed(title="ℹ️ Giveaway Info", color=BRAND)
        embed.add_field(name="🎁 Prize", value=self.prize_label(giveaway), inline=False)
        if meta.get("item_id"):
            embed.add_field(name="🧾 OSRS item ID", value=str(meta["item_id"]), inline=True)
        if meta.get("total_value") is not None:
            embed.add_field(name="💰 Current value", value=format_gp(meta["total_value"]), inline=True)
        embed.add_field(name="🎟️ Entries", value=str(len(giveaway.get("entries", []))), inline=True)
        embed.add_field(name="🏆 Winners", value=str(giveaway.get("winners_count", 1)), inline=True)
        embed.add_field(name="👑 Host", value=f"<@{giveaway['host_id']}>", inline=True)
        embed.add_field(name="✅ Required rank", value=required_rank_text(giveaway), inline=True)
        if not giveaway.get("ended"):
            embed.add_field(name="⏳ Ends", value=f"<t:{int(giveaway['end_time'])}:R>", inline=True)
        embed.add_field(name="How it works", value="Press **Enter Giveaway** once. The bot automatically locks the giveaway at the end time and randomly selects the winner(s).", inline=False)
        if meta.get("image_url"):
            embed.set_thumbnail(url=meta["image_url"])
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------
    # Automatic end
    # ------------------------------------------------------------------
    async def eligible_entries(self, giveaway: dict) -> list[str]:
        entries = [str(x) for x in giveaway.get("entries", [])]
        role_id = required_role_id(giveaway)
        if role_id is None:
            return entries

        guild_id = giveaway.get("guild_id")
        guild = self.bot.get_guild(int(guild_id)) if guild_id else None
        if guild is None or guild.get_role(role_id) is None:
            return []

        eligible = []
        for uid in entries:
            try:
                member = await guild.fetch_member(int(uid))
            except (TypeError, ValueError, discord.HTTPException):
                continue
            if member_has_required_role(member, giveaway):
                eligible.append(uid)
        return eligible

    async def finish_giveaway(self, gid: str):
        async with self.data_lock:
            data = load_json(GIVEAWAYS_FILE, {})
            giveaway = data.get(gid)
            if not giveaway or giveaway.get("ended"):
                return []
            entries = await self.eligible_entries(giveaway)
            count = min(int(giveaway.get("winners_count", 1)), len(entries))
            winners = random.SystemRandom().sample(entries, count) if count else []
            giveaway["ended"] = True
            giveaway["ended_at"] = now_ts()
            giveaway["winner_ids"] = winners
            giveaway["eligible_entries_count"] = len(entries)
            save_json(GIVEAWAYS_FILE, data)

        await self.refresh_message(gid)
        message = await self.get_message(giveaway)
        if message and winners:
            try:
                await message.reply(
                    "🎊 **GIVEAWAY WINNER" + ("S" if len(winners) != 1 else "") + "!**\n"
                    + " ".join(f"<@{uid}>" for uid in winners)
                    + f"\nYou won **{self.prize_label(giveaway)}**!",
                    allowed_mentions=discord.AllowedMentions(users=True),
                )
            except discord.HTTPException:
                pass
        return winners

    @tasks.loop(seconds=20)
    async def giveaway_check_loop(self):
        now = now_ts()
        data = load_json(GIVEAWAYS_FILE, {})
        due = [gid for gid, g in data.items() if not g.get("ended") and int(g.get("end_time", 0)) <= now]
        for gid in due:
            try:
                await self.finish_giveaway(gid)
            except Exception as exc:
                print(f"Giveaway auto-end failed for {gid}: {exc}")

    @giveaway_check_loop.before_loop
    async def before_giveaway_loop(self):
        await self.bot.wait_until_ready()

    # ------------------------------------------------------------------
    # Slash commands
    # ------------------------------------------------------------------
    @app_commands.command(name="giveaway_create", description="Create an automatic NightLegion giveaway.")
    @app_commands.describe(
        prize="Dragon boots, tbow, 100m, 2x Bond, etc.",
        duration="30m, 2h, 7d, 2w",
        winners="Number of winners",
        required_rank="Optional Discord rank required to enter and win",
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def giveaway_create(
        self,
        interaction: discord.Interaction,
        prize: str,
        duration: str,
        winners: app_commands.Range[int, 1, 25] = 1,
        required_rank: Optional[discord.Role] = None,
    ):
        try:
            seconds = parse_duration(duration)
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return

        await interaction.response.defer(thinking=True)
        meta = await enrich_giveaway_prize(prize)
        gid = str(int(now_ts() * 1000) + random.randint(0, 999))
        giveaway = {
            "id": gid,
            "guild_id": interaction.guild_id,
            "channel_id": interaction.channel_id,
            "message_id": None,
            "host_id": interaction.user.id,
            "prize": prize,
            "prize_meta": meta,
            "winners_count": int(winners),
            "created_at": now_ts(),
            "end_time": now_ts() + seconds,
            "entries": [],
            "entry_times": {},
            "ended": False,
            "cancelled": False,
            "winner_ids": [],
            "reroll_history": [],
            "paid": False,
            "has_banner": False,
            "required_role_id": required_rank.id if required_rank else None,
            "required_role_name": required_rank.name if required_rank else None,
        }

        banner = await build_giveaway_card(meta)
        giveaway["has_banner"] = banner is not None
        view = GiveawayView(self, gid)
        attachments = [banner] if banner else []
        message = await interaction.edit_original_response(
            embed=self.build_embed(giveaway),
            view=view,
            attachments=attachments,
        )
        giveaway["message_id"] = message.id
        async with self.data_lock:
            data = load_json(GIVEAWAYS_FILE, {})
            data[gid] = giveaway
            save_json(GIVEAWAYS_FILE, data)
        self.bot.add_view(view, message_id=message.id)

    @app_commands.command(name="giveaway_end", description="End a giveaway now and choose the winner(s).")
    @app_commands.describe(message_id="Discord message ID of the giveaway")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def giveaway_end(self, interaction: discord.Interaction, message_id: str):
        gid, giveaway = self.find_by_message(message_id)
        if not gid or not giveaway:
            await interaction.response.send_message("Could not find that giveaway.", ephemeral=True)
            return
        if giveaway.get("ended"):
            await interaction.response.send_message("That giveaway has already ended.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        winners = await self.finish_giveaway(gid)
        text = "✅ Giveaway ended." + (" Winner(s): " + ", ".join(f"<@{u}>" for u in winners) if winners else " No entrants.")
        await interaction.followup.send(text, ephemeral=True)

    @app_commands.command(name="giveaway_reroll", description="Reroll the winner(s) of an ended giveaway.")
    @app_commands.describe(message_id="Discord message ID of the giveaway")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def giveaway_reroll(self, interaction: discord.Interaction, message_id: str):
        gid, giveaway = self.find_by_message(message_id)
        if not gid or not giveaway:
            await interaction.response.send_message("Could not find that giveaway.", ephemeral=True)
            return
        if not giveaway.get("ended") or giveaway.get("cancelled"):
            await interaction.response.send_message("The giveaway must be ended before rerolling.", ephemeral=True)
            return
        entries = await self.eligible_entries(giveaway)
        if not entries:
            await interaction.response.send_message("Nobody currently eligible entered this giveaway.", ephemeral=True)
            return
        old = [str(x) for x in giveaway.get("winner_ids", [])]
        candidates = [uid for uid in entries if uid not in old] or entries
        count = min(int(giveaway.get("winners_count", 1)), len(candidates))
        selected = random.SystemRandom().sample(candidates, count)
        async with self.data_lock:
            data = load_json(GIVEAWAYS_FILE, {})
            current = data[gid]
            current.setdefault("reroll_history", []).append({
                "at": now_ts(), "by": interaction.user.id,
                "old_winner_ids": old, "new_winner_ids": selected,
            })
            current["winner_ids"] = selected
            current["eligible_entries_count"] = len(entries)
            current["paid"] = False
            current.pop("paid_by", None)
            current.pop("paid_at", None)
            save_json(GIVEAWAYS_FILE, data)
        await self.refresh_message(gid)
        await interaction.response.send_message("🎲 New winner(s): " + ", ".join(f"<@{uid}>" for uid in selected))

    @app_commands.command(name="giveaway_entries", description="Admin-only entrant list for a giveaway.")
    @app_commands.describe(message_id="Discord message ID of the giveaway")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def giveaway_entries(self, interaction: discord.Interaction, message_id: str):
        gid, giveaway = self.find_by_message(message_id)
        if not gid or not giveaway:
            await interaction.response.send_message("Could not find that giveaway.", ephemeral=True)
            return
        await self.send_entrants(interaction, gid)

    @app_commands.command(name="giveaway_profile", description="Show giveaway stats for yourself or another member.")
    @app_commands.describe(member="Member to view; leave blank for yourself")
    async def giveaway_profile(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        await self.send_user_stats(interaction, target.id)

    @app_commands.command(name="giveaway_history", description="Show recent completed giveaways.")
    async def giveaway_history(self, interaction: discord.Interaction):
        data = load_json(GIVEAWAYS_FILE, {})
        completed = [g for g in data.values() if g.get("ended") and not g.get("cancelled")]
        completed.sort(key=lambda g: int(g.get("ended_at") or g.get("end_time") or 0), reverse=True)
        if not completed:
            await interaction.response.send_message("No completed giveaways yet.", ephemeral=True)
            return
        lines = []
        for g in completed[:10]:
            winners = ", ".join(f"<@{uid}>" for uid in g.get("winner_ids", [])) or "No winner"
            paid = "✅" if g.get("paid") else "⏳"
            lines.append(f"{paid} **{self.prize_label(g)}** — {winners} — {len(g.get('entries', []))} entries")
        embed = discord.Embed(title="📜 NightLegion Giveaway History", description="\n".join(lines), color=BRAND)
        embed.set_footer(text="✅ paid • ⏳ not marked paid")
        await interaction.response.send_message(embed=embed, ephemeral=True)

"""Formatting and parsing helpers.

The OSRS prize formatting helpers are carried over from the working BOTW V2
implementation; giveaway-only duration/cash parsing is kept here too.
"""
from __future__ import annotations

import re
import time


def now_ts() -> int:
    return int(time.time())


def format_gp(value: int | None) -> str:
    # Same formatting used by BOTW V2.
    if value is None:
        return "price unavailable"
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}b".replace(".00b", "b")
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}m".replace(".0m", "m")
    if value >= 1_000:
        return f"{value / 1_000:.1f}k".replace(".0k", "k")
    return f"{value:,} gp"


def clean_item_name(item_name: str | None) -> str:
    return (item_name or "").strip()


def prettify_item_name(item_name: str) -> str:
    name = (item_name or "").strip()
    name = re.sub(r"\s*\([^)]*\)", "", name).strip()
    return name[:1].upper() + name[1:] if name else name


def cash_stack_color(price: int | None) -> tuple[int, int, int, int]:
    if price is None:
        return (255, 255, 0, 255)
    if price >= 10_000_000:
        return (0, 255, 0, 255)
    if price >= 100_000:
        return (255, 255, 255, 255)
    return (255, 255, 0, 255)


def truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)] + "..."


def parse_duration(value: str) -> int:
    match = re.fullmatch(r"\s*(\d+)\s*([smhdw])\s*", value.lower())
    if not match:
        raise ValueError("Use a duration like 30m, 2h, 7d, or 2w.")
    amount = int(match.group(1))
    if amount <= 0:
        raise ValueError("Duration must be greater than zero.")
    multiplier = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}[match.group(2)]
    seconds = amount * multiplier
    if seconds > 60 * 86400:
        raise ValueError("Giveaways are capped at 60 days.")
    return seconds


_CASH_RE = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*([kmbt])?\s*(?:gp|coins?)?\s*$", re.I)
_QUANTITY_RE = re.compile(r"^\s*(?:(\d+)\s*[x×]\s*)?(.+?)\s*$", re.I)


def parse_cash_value(text: str) -> int | None:
    match = _CASH_RE.fullmatch(text)
    if not match:
        return None
    amount = float(match.group(1))
    suffix = (match.group(2) or "").lower()
    multiplier = {"": 1, "k": 1_000, "m": 1_000_000, "b": 1_000_000_000, "t": 1_000_000_000_000}[suffix]
    return int(round(amount * multiplier))


def split_quantity(prize: str) -> tuple[int, str]:
    match = _QUANTITY_RE.match(prize)
    if not match:
        return 1, prize.strip()
    return max(1, int(match.group(1) or 1)), match.group(2).strip()

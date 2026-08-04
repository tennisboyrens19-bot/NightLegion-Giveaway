"""OSRS Wiki + price API layer.

The network/cache/matching code below is directly based on the proven BOTW V2
wom.py prize implementation, isolated here so this standalone bot never imports
or reads anything from the BOTW bot.
"""
from __future__ import annotations

import asyncio
import time
from difflib import SequenceMatcher

import aiohttp

from .constants import (
    ITEM_ALIASES,
    OSRS_PRICES_LATEST_URL,
    OSRS_PRICES_MAPPING_URL,
    OSRS_WIKI_API_URL,
    OSRS_WIKI_USER_AGENT,
)
from .utils import clean_item_name, format_gp, parse_cash_value, split_quantity

_session: aiohttp.ClientSession | None = None
_session_lock = asyncio.Lock()
_MAPPING_TTL = 60 * 60 * 6
_PRICE_TTL = 60 * 10
_THUMB_TTL = 60 * 60 * 24
_IMAGE_TTL = 60 * 60 * 6
_cache: dict[str, tuple[float, object]] = {}
_mapping_cache: tuple[float, list[dict]] | None = None


async def get_session() -> aiohttp.ClientSession:
    global _session
    async with _session_lock:
        if _session is None or _session.closed:
            _session = aiohttp.ClientSession(
                headers={"User-Agent": OSRS_WIKI_USER_AGENT},
                timeout=aiohttp.ClientTimeout(total=30),
            )
        return _session


async def close_session() -> None:
    global _session
    if _session is not None and not _session.closed:
        await _session.close()
    _session = None


def _cache_get(key: str, ttl: int):
    entry = _cache.get(key)
    if not entry:
        return None
    stored_at, value = entry
    if time.time() - stored_at > ttl:
        _cache.pop(key, None)
        return None
    return value


def _cache_set(key: str, value) -> None:
    _cache[key] = (time.time(), value)


async def fetch_json(url: str, params: dict | None = None) -> dict | list:
    session = await get_session()
    async with session.get(url, params=params) as response:
        response.raise_for_status()
        return await response.json()


async def download_image_bytes(url: str) -> bytes | None:
    cached = _cache_get(f"img:{url}", _IMAGE_TTL)
    if cached is not None:
        return cached or None
    session = await get_session()
    try:
        async with session.get(url) as response:
            if response.status >= 400:
                return None
            data = await response.read()
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return None
    _cache_set(f"img:{url}", data)
    return data


async def get_wiki_thumbnail_url(title: str, size: int = 96) -> str | None:
    key = f"thumb:{title.lower()}:{size}"
    cached = _cache_get(key, _THUMB_TTL)
    if cached is not None:
        return cached or None
    params = {
        "action": "query",
        "format": "json",
        "prop": "pageimages",
        "piprop": "thumbnail",
        "pithumbsize": str(size),
        "redirects": "1",
        "titles": title,
    }
    session = await get_session()
    try:
        async with session.get(OSRS_WIKI_API_URL, params=params) as response:
            if response.status >= 400:
                return None
            data = await response.json()
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return None
    for page in (data.get("query", {}).get("pages", {}) or {}).values():
        source = (page.get("thumbnail", {}) or {}).get("source")
        if source:
            _cache_set(key, source)
            return source
    _cache_set(key, "")
    return None


async def get_item_mapping() -> list[dict]:
    global _mapping_cache
    if _mapping_cache and time.time() - _mapping_cache[0] <= _MAPPING_TTL:
        return _mapping_cache[1]
    mapping = await fetch_json(OSRS_PRICES_MAPPING_URL)
    if not isinstance(mapping, list):
        mapping = []
    _mapping_cache = (time.time(), mapping)
    return mapping


def find_best_item_match(item_name: str, mapping: list[dict]) -> dict | None:
    wanted = item_name.strip().lower()
    exact = [item for item in mapping if item.get("name", "").lower() == wanted]
    if exact:
        exact.sort(key=lambda item: len(item.get("name", "")))
        return exact[0]
    best_item = None
    best_score = 0.0
    for item in mapping:
        name = item.get("name", "")
        score = SequenceMatcher(None, wanted, name.lower()).ratio()
        if wanted in name.lower():
            score += 0.25
        if score > best_score:
            best_score = score
            best_item = item
    return best_item if best_score >= 0.72 else None


async def get_item_price(item_id: int) -> int | None:
    key = f"price:{item_id}"
    cached = _cache_get(key, _PRICE_TTL)
    if cached is not None:
        return cached if cached != -1 else None
    latest = await fetch_json(OSRS_PRICES_LATEST_URL, params={"id": str(item_id)})
    entry = (latest.get("data", {}) or {}).get(str(item_id), {}) if isinstance(latest, dict) else {}
    high, low = entry.get("high"), entry.get("low")
    if high is not None and low is not None:
        price = round((int(high) + int(low)) / 2)
    elif high is not None:
        price = int(high)
    elif low is not None:
        price = int(low)
    else:
        price = None
    _cache_set(key, price if price is not None else -1)
    return price


async def enrich_item(item_name: str | None) -> dict | None:
    cleaned_name = clean_item_name(item_name)
    if not cleaned_name:
        return None
    alias = ITEM_ALIASES.get(cleaned_name.lower(), cleaned_name)
    prize = {
        "name": alias,
        "item_id": None,
        "price": None,
        "price_text": "price unavailable",
        "image_url": None,
    }
    try:
        item = find_best_item_match(alias, await get_item_mapping())
        if item:
            item_id = int(item["id"])
            price = await get_item_price(item_id)
            prize["name"] = item.get("name", alias)
            prize["item_id"] = item_id
            prize["price"] = price
            prize["price_text"] = format_gp(price)
    except Exception:
        pass
    try:
        prize["image_url"] = await get_wiki_thumbnail_url(prize["name"], size=320)
    except Exception:
        pass
    return prize


async def enrich_giveaway_prize(raw_prize: str) -> dict:
    quantity, cleaned = split_quantity(raw_prize)
    cash = parse_cash_value(cleaned)
    if cash is not None:
        total = cash * quantity
        return {
            "type": "cash",
            "input": raw_prize,
            "name": "Coins",
            "quantity": quantity,
            "item_id": 995,
            "unit_value": cash,
            "total_value": total,
            "price": total,
            "price_text": format_gp(total),
            "image_url": await get_wiki_thumbnail_url("Coins", size=320),
        }

    item = await enrich_item(cleaned)
    if item and item.get("item_id") is not None:
        unit = item.get("price")
        total = unit * quantity if unit is not None else None
        return {
            "type": "item",
            "input": raw_prize,
            "name": item["name"],
            "quantity": quantity,
            "item_id": item["item_id"],
            "unit_value": unit,
            "total_value": total,
            "price": total,
            "price_text": format_gp(total),
            "image_url": item.get("image_url"),
        }

    # Custom prizes still try Wiki artwork, but are clearly labelled custom.
    title = ITEM_ALIASES.get(cleaned.lower(), cleaned)
    return {
        "type": "custom",
        "input": raw_prize,
        "name": title,
        "quantity": quantity,
        "item_id": None,
        "unit_value": None,
        "total_value": None,
        "price": None,
        "price_text": "Custom prize",
        "image_url": await get_wiki_thumbnail_url(title, size=320),
    }

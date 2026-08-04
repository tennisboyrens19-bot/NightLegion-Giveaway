"""Giveaway prize graphic using the same Wiki sprite/downloading approach as BOTW V2."""
from __future__ import annotations

import io

import discord

from .osrs import download_image_bytes, get_wiki_thumbnail_url
from .utils import cash_stack_color, prettify_item_name, truncate

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    Image = ImageDraw = ImageFont = None

FILENAME = "nightlegion_giveaway.png"
CLASSIC_YELLOW = (255, 255, 0, 255)
PANEL_FILL = (28, 22, 14, 225)
PANEL_EDGE = (124, 92, 43, 255)
SHADOW = (0, 0, 0, 255)

FONT_CANDIDATES = [
    "assets/fonts/RuneScape.ttf", "assets/fonts/runescape.ttf", "RuneScape.ttf", "runescape.ttf",
    "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
_font_cache = {}


def _font(size: int):
    if size in _font_cache:
        return _font_cache[size]
    for candidate in FONT_CANDIDATES:
        try:
            font = ImageFont.truetype(candidate, size)
            _font_cache[size] = font
            return font
        except Exception:
            pass
    font = ImageFont.load_default()
    _font_cache[size] = font
    return font


def graphics_available() -> bool:
    return Image is not None and ImageDraw is not None and ImageFont is not None


async def build_giveaway_card(meta: dict) -> discord.File | None:
    if not graphics_available() or not meta:
        return None

    width, height = 1800, 760
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle([20, 20, width - 20, height - 20], radius=42, fill=PANEL_FILL, outline=PANEL_EDGE, width=5)

    title_font = _font(74)
    name_font = _font(100)
    value_font = _font(72)
    small_font = _font(46)

    def centered(y: int, text: str, fill, font):
        box = draw.textbbox((0, 0), text, font=font)
        x = int(width / 2 - (box[2] - box[0]) / 2)
        draw.text((x + 4, y + 4), text, fill=SHADOW, font=font)
        draw.text((x, y), text, fill=fill, font=font)

    centered(62, "NIGHTLEGION GIVEAWAY", (214, 195, 143, 255), title_font)

    image_url = meta.get("image_url")
    if image_url:
        raw = await download_image_bytes(image_url)
        if raw:
            try:
                sprite = Image.open(io.BytesIO(raw)).convert("RGBA")
                max_size = 310
                scale = min(max_size / sprite.width, max_size / sprite.height)
                sprite = sprite.resize((max(1, int(sprite.width * scale)), max(1, int(sprite.height * scale))), Image.Resampling.NEAREST)
                image.paste(sprite, (int(width / 2 - sprite.width / 2), 170), sprite)
            except Exception:
                pass

    qty = int(meta.get("quantity") or 1)
    name = prettify_item_name(meta.get("name") or meta.get("input") or "Prize")
    display = f"{qty}x {name}" if qty > 1 else name
    centered(500, truncate(display, 28), CLASSIC_YELLOW, name_font)

    price = meta.get("total_value")
    if price is not None:
        label = f"{meta.get('price_text', '')} GP"
        centered(624, label, cash_stack_color(price), value_font)
    else:
        centered(630, "GOOD LUCK!", (255, 255, 255, 255), small_font)

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename=FILENAME)

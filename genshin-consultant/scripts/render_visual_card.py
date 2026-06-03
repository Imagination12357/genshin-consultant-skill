#!/usr/bin/env python3
"""Render or validate Genshin consultation visual card metadata.

This renderer is for compact report cards that benefit from character art:

- party_card: four character icons in one row, themed by the first character.
- build_card: one character card image on the left with build targets on the right.
- weapon_card/artifact_card/mechanics_card: structured row cards.

Image-heavy weapon TOP 5 and artifact set showcase cards are rendered by
render_showcase_card.py.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps
except Exception as exc:  # noqa: BLE001
    print(f"ERROR: Pillow is required for visual card rendering: {exc}", file=sys.stderr)
    raise


Color = tuple[int, int, int]
Theme = dict[str, Color]

ALLOWED_CARD_TYPES = {
    "party_card",
    "build_card",
    "weapon_card",
    "artifact_card",
    "mechanics_card",
}

ELEMENT_THEMES: dict[str, Theme] = {
    "pyro": {
        "bg_top": (255, 246, 240),
        "bg_bottom": (126, 34, 18),
        "accent": (220, 82, 45),
        "accent_dark": (126, 34, 18),
        "accent_soft": (255, 226, 214),
        "panel": (255, 250, 247),
        "text": (44, 34, 30),
        "muted": (126, 101, 91),
    },
    "hydro": {
        "bg_top": (239, 250, 255),
        "bg_bottom": (18, 88, 128),
        "accent": (46, 139, 196),
        "accent_dark": (18, 88, 128),
        "accent_soft": (216, 240, 253),
        "panel": (248, 253, 255),
        "text": (27, 42, 52),
        "muted": (78, 101, 114),
    },
    "electro": {
        "bg_top": (249, 245, 255),
        "bg_bottom": (74, 38, 132),
        "accent": (126, 87, 210),
        "accent_dark": (74, 38, 132),
        "accent_soft": (233, 224, 255),
        "panel": (253, 251, 255),
        "text": (40, 34, 52),
        "muted": (96, 86, 116),
    },
    "cryo": {
        "bg_top": (245, 253, 255),
        "bg_bottom": (57, 121, 144),
        "accent": (89, 174, 205),
        "accent_dark": (42, 102, 126),
        "accent_soft": (220, 245, 250),
        "panel": (251, 254, 255),
        "text": (32, 45, 51),
        "muted": (84, 106, 116),
    },
    "anemo": {
        "bg_top": (239, 255, 250),
        "bg_bottom": (34, 122, 104),
        "accent": (50, 166, 137),
        "accent_dark": (24, 105, 87),
        "accent_soft": (212, 246, 236),
        "panel": (249, 255, 253),
        "text": (30, 47, 43),
        "muted": (78, 107, 100),
    },
    "geo": {
        "bg_top": (255, 250, 237),
        "bg_bottom": (132, 91, 28),
        "accent": (194, 138, 50),
        "accent_dark": (132, 91, 28),
        "accent_soft": (248, 231, 195),
        "panel": (255, 253, 247),
        "text": (48, 40, 29),
        "muted": (119, 98, 71),
    },
    "dendro": {
        "bg_top": (247, 255, 241),
        "bg_bottom": (70, 117, 40),
        "accent": (106, 158, 55),
        "accent_dark": (70, 117, 40),
        "accent_soft": (226, 244, 204),
        "panel": (252, 255, 248),
        "text": (37, 48, 29),
        "muted": (91, 112, 76),
    },
    "physical": {
        "bg_top": (250, 250, 252),
        "bg_bottom": (83, 88, 98),
        "accent": (112, 120, 134),
        "accent_dark": (83, 88, 98),
        "accent_soft": (230, 233, 238),
        "panel": (254, 254, 255),
        "text": (36, 38, 43),
        "muted": (92, 96, 105),
    },
}

ELEMENT_ALIASES = {
    "pyro": "pyro",
    "fire": "pyro",
    "\ubd88": "pyro",
    "\ubd88\uc6d0\uc18c": "pyro",
    "hydro": "hydro",
    "water": "hydro",
    "\ubb3c": "hydro",
    "\ubb3c\uc6d0\uc18c": "hydro",
    "electro": "electro",
    "lightning": "electro",
    "\ubc88\uac1c": "electro",
    "\ubc88\uac1c\uc6d0\uc18c": "electro",
    "cryo": "cryo",
    "ice": "cryo",
    "\uc5bc\uc74c": "cryo",
    "\uc5bc\uc74c\uc6d0\uc18c": "cryo",
    "anemo": "anemo",
    "wind": "anemo",
    "\ubc14\ub78c": "anemo",
    "\ubc14\ub78c\uc6d0\uc18c": "anemo",
    "geo": "geo",
    "rock": "geo",
    "\ubc14\uc704": "geo",
    "\ubc14\uc704\uc6d0\uc18c": "geo",
    "dendro": "dendro",
    "grass": "dendro",
    "\ud480": "dendro",
    "\ud480\uc6d0\uc18c": "dendro",
    "physical": "physical",
    "\ubb3c\ub9ac": "physical",
    "neutral": "physical",
}

CARD_TYPE_THEME = {
    "party_card": "electro",
    "build_card": "dendro",
    "weapon_card": "electro",
    "artifact_card": "geo",
    "mechanics_card": "pyro",
}

KO_CORE_PLAY = "\uad6c\ub3d9 \ubc29\ubc95"
KO_ROTATION = "\ub85c\ud14c\uc774\uc158"
KO_NOTES = "\uc8fc\uc758\uc810"
KO_TARGET_STATS = "\uc885\uacb0 \uccb4\uae09 \ubaa9\ud45c"
KO_WEAPON = "\ubb34\uae30"
KO_ARTIFACT = "\uc131\uc720\ubb3c"
KO_FIRST_FIX = "\uba3c\uc800 \uace0\uce60 \uac83"


def load_metadata(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("metadata root must be an object")
    return data


def errors_for_metadata(meta: dict[str, Any], output_override: str | None = None) -> list[str]:
    errors: list[str] = []
    card_type = meta.get("card_type")
    if card_type not in ALLOWED_CARD_TYPES:
        errors.append(f"card_type must be one of {sorted(ALLOWED_CARD_TYPES)}")
    if not isinstance(meta.get("title"), str) or not meta["title"].strip():
        errors.append("title must be a non-empty string")
    if not output_override and not str(meta.get("output_image_path", "")).strip():
        errors.append("output_image_path must be a non-empty string when --output is not provided")
    for key in ("source_ids", "image_source_ids"):
        if key in meta and not isinstance(meta[key], list):
            errors.append(f"{key} must be a list when present")
    if card_type == "party_card":
        chars = meta.get("characters")
        if not isinstance(chars, list) or len(chars) != 4:
            errors.append("party_card requires exactly four characters[] entries")
        elif any(not isinstance(c, dict) or not str(c.get("name", "")).strip() for c in chars):
            errors.append("each party_card character requires a non-empty name")
    elif "rows" in meta and not isinstance(meta.get("rows"), list):
        errors.append("rows must be a list when present")
    if "sections" in meta and not isinstance(meta.get("sections"), list):
        errors.append("sections must be a list when present")
    if "target_stats" in meta and not isinstance(meta.get("target_stats"), (dict, list)):
        errors.append("target_stats must be an object or list when present")
    suspicious = find_encoding_corruption(meta)
    if suspicious:
        errors.append(
            "metadata appears to contain encoding-corrupted text; "
            f"regenerate it with UTF-8 input/output. Example field: {suspicious}"
        )
    return errors


def looks_encoding_corrupted(value: str) -> bool:
    if "\ufffd" in value or "???" in value:
        return True
    question_count = value.count("?")
    has_non_ascii = any(ord(ch) > 127 for ch in value)
    return question_count >= 2 and has_non_ascii


def find_encoding_corruption(value: Any, path: str = "$") -> str | None:
    if isinstance(value, str):
        if looks_encoding_corrupted(value):
            return path
        return None
    if isinstance(value, dict):
        for key, item in value.items():
            found = find_encoding_corruption(item, f"{path}.{key}")
            if found:
                return found
    if isinstance(value, list):
        for idx, item in enumerate(value):
            found = find_encoding_corruption(item, f"{path}[{idx}]")
            if found:
                return found
    return None


def get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates: list[Path] = []
    if sys.platform.startswith("win"):
        candidates.extend(
            [
                Path(r"C:\Windows\Fonts\malgunbd.ttf") if bold else Path(r"C:\Windows\Fonts\malgun.ttf"),
                Path(r"C:\Windows\Fonts\NanumGothicBold.ttf") if bold else Path(r"C:\Windows\Fonts\NanumGothic.ttf"),
                Path(r"C:\Windows\Fonts\segoeuib.ttf") if bold else Path(r"C:\Windows\Fonts\segoeui.ttf"),
                Path(r"C:\Windows\Fonts\arialbd.ttf") if bold else Path(r"C:\Windows\Fonts\arial.ttf"),
            ]
        )
    candidates.extend(
        [
            Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc") if bold else Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc") if bold else Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf") if bold else Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            try:
                return ImageFont.truetype(str(candidate), size)
            except Exception:
                continue
    return ImageFont.load_default()


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def wrap_text(draw: ImageDraw.ImageDraw, text: Any, font: ImageFont.ImageFont, max_width: int, max_lines: int = 2) -> list[str]:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if not value:
        return [""]
    units = value.split(" ") if " " in value else list(value)
    sep = " " if " " in value else ""
    lines: list[str] = []
    current = ""
    truncated = False
    for idx, unit in enumerate(units):
        candidate = unit if not current else current + sep + unit
        if text_size(draw, candidate, font)[0] <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = unit
        if len(lines) >= max_lines:
            truncated = True
            break
        if idx < len(units) - 1 and text_size(draw, current, font)[0] > max_width:
            while current and text_size(draw, current, font)[0] > max_width:
                lines.append(current[: max(1, len(current) - 1)])
                current = current[max(1, len(current) - 1) :]
                if len(lines) >= max_lines:
                    truncated = True
                    break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        truncated = True
    if truncated and lines:
        last = lines[-1]
        suffix = "..."
        while last and text_size(draw, last + suffix, font)[0] > max_width:
            last = last[:-1]
        lines[-1] = (last + suffix) if last else suffix
    return lines[:max_lines] or [""]


def draw_text_lines(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    xy: tuple[int, int],
    font: ImageFont.ImageFont,
    fill: Color,
    line_gap: int = 8,
    max_width: int | None = None,
    max_lines: int | None = None,
) -> int:
    x, y = xy
    drawn = 0
    for line in lines:
        wrapped = [line]
        if max_width is not None:
            wrapped = wrap_text(draw, line, font, max_width, max_lines or 2)
        for piece in wrapped:
            if max_lines is not None and drawn >= max_lines:
                return y
            draw.text((x, y), piece, font=font, fill=fill)
            y += text_size(draw, piece, font)[1] + line_gap
            drawn += 1
    return y


def draw_centered(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, font: ImageFont.ImageFont, fill: Color) -> None:
    w, h = text_size(draw, text, font)
    x1, y1, x2, y2 = box
    draw.text((x1 + (x2 - x1 - w) / 2, y1 + (y2 - y1 - h) / 2), text, font=font, fill=fill)


def draw_gradient(draw: ImageDraw.ImageDraw, width: int, height: int, top: Color, bottom: Color) -> None:
    for y in range(height):
        ratio = y / max(1, height - 1)
        color = tuple(int(top[i] * (1 - ratio) + bottom[i] * ratio) for i in range(3))
        draw.line([(0, y), (width, y)], fill=color)


def lighten(color: Color, ratio: float) -> Color:
    return tuple(int(color[i] + (255 - color[i]) * ratio) for i in range(3))


def darken(color: Color, ratio: float) -> Color:
    return tuple(int(color[i] * (1 - ratio)) for i in range(3))


def normalize_element(value: Any) -> str | None:
    text = re.sub(r"[\s_\-]+", "", str(value or "")).casefold()
    if not text:
        return None
    return ELEMENT_ALIASES.get(text)


def theme_from_meta(meta: dict[str, Any]) -> tuple[str, Theme]:
    candidates: list[Any] = [
        meta.get("theme_element"),
        meta.get("element"),
        meta.get("main_element"),
    ]
    character = meta.get("character")
    if isinstance(character, dict):
        candidates.append(character.get("element"))
    characters = meta.get("characters")
    if isinstance(characters, list) and characters and isinstance(characters[0], dict):
        candidates.append(characters[0].get("element"))
    for candidate in candidates:
        key = normalize_element(candidate)
        if key and key in ELEMENT_THEMES:
            return key, ELEMENT_THEMES[key]
    fallback = CARD_TYPE_THEME.get(str(meta.get("card_type")), "physical")
    return fallback, ELEMENT_THEMES[fallback]


def draw_card_background(base: Image.Image, theme: Theme) -> None:
    draw = ImageDraw.Draw(base, "RGBA")
    draw_gradient(draw, base.width, base.height, theme["bg_top"], theme["bg_bottom"])
    accent = theme["accent"]
    for idx, x in enumerate(range(-160, base.width, 260)):
        y = 120 + (idx % 3) * 120
        draw.rounded_rectangle((x, y, x + 360, y + 18), radius=9, fill=(*lighten(accent, 0.72), 42))
    draw.polygon([(0, base.height), (base.width, base.height), (base.width, int(base.height * 0.58))], fill=(*darken(theme["accent_dark"], 0.08), 72))


def rounded_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    radius: int,
    fill: tuple[int, int, int, int],
    outline: tuple[int, int, int, int] | None = None,
    width: int = 1,
    shadow: bool = True,
) -> None:
    x1, y1, x2, y2 = box
    if shadow:
        draw.rounded_rectangle((x1 + 6, y1 + 8, x2 + 6, y2 + 8), radius=radius, fill=(0, 0, 0, 42))
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def load_image(path_text: Any) -> Image.Image | None:
    if not path_text:
        return None
    path = Path(str(path_text))
    if not path.exists():
        return None
    try:
        return Image.open(path).convert("RGBA")
    except Exception:
        return None


def paste_rounded_cover(
    base: Image.Image,
    image: Image.Image,
    box: tuple[int, int, int, int],
    radius: int,
    centering: tuple[float, float] = (0.5, 0.5),
) -> None:
    x1, y1, x2, y2 = box
    size = (x2 - x1, y2 - y1)
    fitted = ImageOps.fit(image, size, method=Image.Resampling.LANCZOS, centering=centering)
    mask = Image.new("L", size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    alpha = ImageChops.multiply(fitted.getchannel("A"), mask)
    fitted.putalpha(alpha)
    base.alpha_composite(fitted, (x1, y1))


def paste_contained_image(base: Image.Image, image: Image.Image, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    size = (x2 - x1, y2 - y1)
    contained = ImageOps.contain(image, size, method=Image.Resampling.LANCZOS)
    px = x1 + (size[0] - contained.width) // 2
    py = y1 + (size[1] - contained.height) // 2
    base.alpha_composite(contained, (px, py))


def draw_pill(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: ImageFont.ImageFont, fill: Color, text_fill: Color = (255, 255, 255)) -> tuple[int, int, int, int]:
    x, y = xy
    w, h = text_size(draw, text, font)
    box = (x, y, x + w + 28, y + h + 14)
    draw.rounded_rectangle(box, radius=(h + 14) // 2, fill=fill)
    draw.text((x + 14, y + 7), text, font=font, fill=text_fill)
    return box


def row_value(row: dict[str, Any]) -> str:
    parts = [str(row.get("value") or "").strip(), str(row.get("note") or "").strip()]
    return " - ".join(part for part in parts if part)


def find_row_text(meta: dict[str, Any], keys: list[str]) -> str:
    rows = meta.get("rows")
    if not isinstance(rows, list):
        return ""
    for row in rows:
        if not isinstance(row, dict):
            continue
        label = str(row.get("label") or row.get("title") or "").casefold()
        for key in keys:
            if key.casefold() in label:
                return row_value(row) or str(row.get("label") or "")
    return ""


def character_image_path(char: dict[str, Any], preferred: str = "icon") -> Any:
    if preferred == "icon":
        return char.get("icon_path") or char.get("image_path") or char.get("card_path")
    return char.get("card_path") or char.get("image_path") or char.get("icon_path")


def render_party_card(meta: dict[str, Any], base: Image.Image, theme_key: str, theme: Theme) -> None:
    draw = ImageDraw.Draw(base, "RGBA")
    title_font = get_font(34, True)
    subtitle_font = get_font(19)
    name_font = get_font(23, True)
    role_font = get_font(17)
    small_font = get_font(16)
    section_font = get_font(20, True)

    width = base.width
    accent = theme["accent"]
    accent_dark = theme["accent_dark"]
    text = theme["text"]
    muted = theme["muted"]
    panel = theme["panel"]

    title = str(meta.get("title", "Party Report"))
    subtitle = str(meta.get("subtitle") or meta.get("summary") or "")

    draw.rectangle((54, 42, 68, 98), fill=accent)
    draw.text((92, 40), title, font=title_font, fill=text)
    if subtitle:
        draw.text((94, 84), subtitle, font=subtitle_font, fill=muted)
    draw_pill(draw, (width - 250, 50), theme_key.title(), small_font, accent_dark)

    chars = meta.get("characters", [])[:4]
    start_x = 58
    y = 136
    slot_w = 360
    slot_h = 300
    gap = 26
    for idx, char in enumerate(chars):
        x = start_x + idx * (slot_w + gap)
        char_element = normalize_element(char.get("element")) or theme_key
        char_theme = ELEMENT_THEMES.get(char_element, theme)
        char_accent = char_theme["accent"]
        rounded_panel(
            draw,
            (x, y, x + slot_w, y + slot_h),
            radius=24,
            fill=(*panel, 236),
            outline=(*lighten(char_accent, 0.3), 190),
            width=2,
            shadow=True,
        )
        draw.rounded_rectangle((x, y, x + slot_w, y + 12), radius=6, fill=char_accent)
        image_box = (x + 22, y + 40, x + 166, y + 184)
        draw.rounded_rectangle(image_box, radius=20, fill=(*char_theme["accent_soft"], 255), outline=(*char_accent, 210), width=2)
        icon = load_image(character_image_path(char, "icon"))
        if icon:
            paste_contained_image(base, icon, (image_box[0] + 8, image_box[1] + 8, image_box[2] - 8, image_box[3] - 8))
        else:
            draw_centered(draw, image_box, str(char.get("name", "?"))[:1] or "?", get_font(48, True), char_accent)

        name = str(char.get("name", "Unknown"))
        draw.text((x + 188, y + 42), name, font=name_font, fill=text)
        role = str(char.get("role") or "")
        role_y = y + 82
        for line in wrap_text(draw, role, role_font, slot_w - 206, 3):
            draw.text((x + 188, role_y), line, font=role_font, fill=muted)
            role_y += 24

        contribution = str(char.get("contribution") or char.get("note") or char.get("element") or "")
        if contribution:
            draw.rounded_rectangle((x + 22, y + 205, x + slot_w - 22, y + 255), radius=16, fill=(*char_theme["accent_soft"], 230))
            lines = wrap_text(draw, contribution, small_font, slot_w - 60, 2)
            draw_text_lines(draw, lines, (x + 38, y + 216), small_font, darken(char_accent, 0.25), line_gap=4)
        build = str(char.get("build") or char.get("artifact") or "")
        if build:
            draw.text((x + 28, y + 266), build, font=small_font, fill=muted)

    operation = str(meta.get("operation") or meta.get("playstyle") or find_row_text(meta, ["operation", "\uad6c\ub3d9", "\uc6b4\uc6a9"]) or "")
    rotation = str(meta.get("rotation") or find_row_text(meta, ["rotation", "\ub85c\ud14c"]) or "")
    notes_value = meta.get("notes") or meta.get("note") or find_row_text(meta, ["note", "\uc8fc\uc758", "caveat"])
    if isinstance(notes_value, list):
        notes = " / ".join(str(item) for item in notes_value)
    else:
        notes = str(notes_value or "")

    section_y = 482
    sections = [
        (58, 520, KO_CORE_PLAY, operation, 4),
        (598, 610, KO_ROTATION, rotation, 5),
        (1238, width - 1238 - 58, KO_NOTES, notes, 4),
    ]
    for x, w, label, value, max_lines in sections:
        rounded_panel(
            draw,
            (x, section_y, x + w, section_y + 152),
            radius=20,
            fill=(*panel, 234),
            outline=(*lighten(accent, 0.48), 170),
            shadow=True,
        )
        draw.text((x + 22, section_y + 18), label, font=section_font, fill=accent_dark)
        if value:
            lines = wrap_text(draw, value, role_font, w - 44, max_lines)
            draw_text_lines(draw, lines, (x + 22, section_y + 56), role_font, text, line_gap=8)
        else:
            draw.text((x + 22, section_y + 60), "Fill this from the consultation.", font=role_font, fill=muted)


def rows_from_target_stats(target_stats: Any) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    if isinstance(target_stats, dict):
        for key, value in target_stats.items():
            if isinstance(value, (list, dict)):
                rendered = json.dumps(value, ensure_ascii=False)
            else:
                rendered = str(value)
            rows.append((str(key), rendered))
    elif isinstance(target_stats, list):
        for item in target_stats:
            if isinstance(item, dict):
                rows.append((str(item.get("label") or item.get("name") or ""), str(item.get("value") or item.get("target") or "")))
            else:
                rows.append(("", str(item)))
    return [(label, value) for label, value in rows if label or value]


def render_stat_grid(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    rows: list[tuple[str, str]],
    theme: Theme,
) -> None:
    x1, y1, x2, _ = box
    label_font = get_font(14, True)
    value_font = get_font(17, True)
    cell_w = (x2 - x1 - 18) // 2
    cell_h = 56
    for idx, (label, value) in enumerate(rows[:6]):
        col = idx % 2
        row = idx // 2
        x = x1 + col * (cell_w + 18)
        y = y1 + row * (cell_h + 10)
        draw.rounded_rectangle((x, y, x + cell_w, y + cell_h), radius=16, fill=(*theme["accent_soft"], 230))
        draw.text((x + 18, y + 8), label, font=label_font, fill=theme["muted"])
        clipped = wrap_text(draw, value, value_font, cell_w - 36, 1)[0]
        draw.text((x + 18, y + 30), clipped, font=value_font, fill=theme["text"])


def summarize_dict(value: Any, fallback_name: str = "") -> tuple[str, str, Any]:
    if isinstance(value, dict):
        name = str(value.get("name") or fallback_name)
        details = []
        for key in ("refinement", "level", "main_stat", "set", "summary", "note"):
            if value.get(key):
                details.append(str(value[key]))
        return name, " / ".join(details), value.get("image_path")
    return str(value or fallback_name), "", None


def sections_from_meta(meta: dict[str, Any]) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    raw_sections = meta.get("sections")
    if isinstance(raw_sections, list):
        for section in raw_sections:
            if not isinstance(section, dict):
                continue
            title = str(section.get("title") or section.get("label") or "")
            lines_raw = section.get("lines") or section.get("items") or section.get("value") or []
            if isinstance(lines_raw, str):
                lines = [lines_raw]
            elif isinstance(lines_raw, list):
                lines = [str(item) for item in lines_raw]
            else:
                lines = [str(lines_raw)]
            if title or lines:
                sections.append((title, lines))
    if sections:
        return sections
    rows = meta.get("rows")
    if isinstance(rows, list):
        lines = []
        for row in rows[:5]:
            if isinstance(row, dict):
                label = str(row.get("label") or "")
                value = row_value(row)
                lines.append(f"{label}: {value}" if label and value else label or value)
        if lines:
            sections.append((KO_FIRST_FIX, lines))
    return sections


def render_build_card(meta: dict[str, Any], base: Image.Image, theme_key: str, theme: Theme) -> None:
    draw = ImageDraw.Draw(base, "RGBA")
    width = base.width
    accent = theme["accent"]
    accent_dark = theme["accent_dark"]
    text = theme["text"]
    muted = theme["muted"]
    panel = theme["panel"]

    character = meta.get("character") if isinstance(meta.get("character"), dict) else {}
    name = str(character.get("name") or meta.get("character_name") or meta.get("title") or "Character")
    role = str(character.get("role") or meta.get("role") or meta.get("subtitle") or "")
    level = str(character.get("level") or meta.get("level") or "")
    constellation = str(character.get("constellation") or meta.get("constellation") or "")

    left_box = (42, 42, 640, 878)
    rounded_panel(draw, left_box, 28, fill=(*panel, 228), outline=(*lighten(accent, 0.35), 190), width=2, shadow=True)
    card_path = character.get("card_path") or meta.get("card_path") or character_image_path(character, "card") if character else meta.get("image_path")
    card = load_image(card_path)
    if card:
        paste_rounded_cover(base, card, (54, 54, 628, 866), radius=24, centering=(0.5, 0.34))
    else:
        draw.rounded_rectangle((54, 54, 628, 866), radius=24, fill=(*theme["accent_soft"], 255))
        draw_centered(draw, (54, 300, 628, 520), name[:2], get_font(74, True), accent_dark)
    draw.rounded_rectangle((54, 696, 628, 866), radius=24, fill=(*darken(accent_dark, 0.15), 190))
    draw.text((82, 724), name, font=get_font(42, True), fill=(255, 255, 255))
    sub_parts = [part for part in [role, level, constellation] if part]
    if sub_parts:
        draw.text((84, 782), " / ".join(sub_parts), font=get_font(22, True), fill=(255, 238, 225))
    draw_pill(draw, (84, 820), theme_key.title(), get_font(16, True), accent)

    x = 690
    draw.rectangle((x, 54, x + 14, 108), fill=accent)
    draw.text((x + 36, 46), str(meta.get("title") or f"{name} Build Report"), font=get_font(36, True), fill=text)
    subtitle = str(meta.get("subtitle") or role)
    if subtitle:
        draw.text((x + 38, 94), subtitle, font=get_font(19), fill=muted)

    weapon_name, weapon_detail, weapon_image = summarize_dict(meta.get("weapon"), "")
    artifact_name, artifact_detail, artifact_image = summarize_dict(meta.get("artifact") or meta.get("artifact_set"), "")
    info_y = 142
    panel_w = (width - x - 66 - 24) // 2
    info_boxes = [
        (x, info_y, x + panel_w, info_y + 148, KO_WEAPON, weapon_name, weapon_detail, weapon_image),
        (x + panel_w + 24, info_y, x + panel_w * 2 + 24, info_y + 148, KO_ARTIFACT, artifact_name, artifact_detail, artifact_image),
    ]
    for x1, y1, x2, y2, label, main, detail, image_path in info_boxes:
        rounded_panel(draw, (x1, y1, x2, y2), 20, fill=(*panel, 235), outline=(*lighten(accent, 0.5), 170), shadow=True)
        draw.text((x1 + 20, y1 + 18), label, font=get_font(18, True), fill=accent_dark)
        if image_path:
            asset = load_image(image_path)
            if asset:
                paste_contained_image(base, asset, (x1 + 18, y1 + 54, x1 + 88, y1 + 124))
                text_x = x1 + 106
            else:
                text_x = x1 + 20
        else:
            text_x = x1 + 20
        if main:
            draw_text_lines(draw, wrap_text(draw, main, get_font(21, True), x2 - text_x - 20, 2), (text_x, y1 + 54), get_font(21, True), text, line_gap=7)
        if detail:
            draw_text_lines(draw, wrap_text(draw, detail, get_font(15), x2 - text_x - 20, 2), (text_x, y1 + 104), get_font(15), muted, line_gap=5)

    target_rows = rows_from_target_stats(meta.get("target_stats"))
    if not target_rows:
        target_rows = [(str(row.get("label", "")), row_value(row)) for row in meta.get("rows", [])[:6] if isinstance(row, dict)]
    stats_box = (x, 328, width - 66, 602)
    rounded_panel(draw, stats_box, 22, fill=(*panel, 235), outline=(*lighten(accent, 0.5), 170), shadow=True)
    draw.text((stats_box[0] + 22, stats_box[1] + 18), KO_TARGET_STATS, font=get_font(22, True), fill=accent_dark)
    render_stat_grid(draw, (stats_box[0] + 22, stats_box[1] + 62, stats_box[2] - 22, stats_box[3] - 16), target_rows, theme)

    sections = sections_from_meta(meta)
    section_y = 622
    section_h = 66
    for idx, (title, lines) in enumerate(sections[:3]):
        y = section_y + idx * (section_h + 12)
        rounded_panel(draw, (x, y, width - 66, y + section_h), 20, fill=(*panel, 232), outline=(*lighten(accent, 0.55), 150), shadow=True)
        draw.text((x + 22, y + 12), title or KO_FIRST_FIX, font=get_font(18, True), fill=accent_dark)
        value = " / ".join(line for line in lines if line)
        draw_text_lines(draw, wrap_text(draw, value, get_font(15), width - x - 110, 1), (x + 22, y + 40), get_font(15), text, line_gap=4)


def render_rows_card(meta: dict[str, Any], base: Image.Image, theme: Theme) -> None:
    draw = ImageDraw.Draw(base, "RGBA")
    title_font = get_font(32, True)
    subtitle_font = get_font(18)
    label_font = get_font(18, True)
    value_font = get_font(18)
    width = base.width
    title = str(meta.get("title", "Genshin Card"))
    subtitle = str(meta.get("subtitle") or meta.get("summary") or meta.get("card_type", ""))
    accent = theme["accent"]
    text = theme["text"]
    muted = theme["muted"]

    draw.rectangle((42, 34, 56, 88), fill=accent)
    draw.text((82, 30), title, font=title_font, fill=text)
    if subtitle:
        draw.text((84, 78), subtitle, font=subtitle_font, fill=muted)

    rows = meta.get("rows") if isinstance(meta.get("rows"), list) else []
    y = 132
    for row in rows[:8]:
        if not isinstance(row, dict):
            continue
        rounded_panel(draw, (50, y, width - 50, y + 68), 16, fill=(*theme["panel"], 236), outline=(*lighten(accent, 0.52), 150), shadow=True)
        draw.text((76, y + 18), str(row.get("label", "")), font=label_font, fill=text)
        value = row_value(row)
        draw_text_lines(draw, wrap_text(draw, value, value_font, width - 430, 2), (388, y + 18), value_font, (55, 55, 60), line_gap=5)
        y += 82


def render_footer(base: Image.Image, meta: dict[str, Any], theme: Theme) -> None:
    draw = ImageDraw.Draw(base, "RGBA")
    footer_font = get_font(14)
    footer_y = base.height - 48
    draw.rectangle((0, footer_y, base.width, base.height), fill=(255, 255, 255, 180))
    source_ids = ", ".join(str(x) for x in meta.get("source_ids", [])[:6]) or "source ids pending"
    generated_at = str(meta.get("generated_at") or datetime.now(timezone.utc).isoformat())[:19]
    draw.text((34, footer_y + 15), f"Sources: {source_ids} | Generated: {generated_at}", font=footer_font, fill=theme["muted"])


def render_card(meta: dict[str, Any], output: Path) -> None:
    card_type = str(meta.get("card_type"))
    theme_key, theme = theme_from_meta(meta)
    if card_type == "party_card":
        width, height = 1600, 720
    elif card_type == "build_card":
        width, height = 1680, 920
    else:
        width, height = 1400, 820

    base = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    draw_card_background(base, theme)

    if card_type == "party_card":
        render_party_card(meta, base, theme_key, theme)
    elif card_type == "build_card":
        render_build_card(meta, base, theme_key, theme)
    else:
        render_rows_card(meta, base, theme)

    render_footer(base, meta, theme)
    output.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render/validate genshin-consultant visual card metadata")
    parser.add_argument("metadata_json", type=Path)
    parser.add_argument("--output", type=Path, help="PNG output path; defaults to metadata.output_image_path")
    parser.add_argument("--validate-only", action="store_true", help="Validate metadata without writing a PNG")
    args = parser.parse_args()

    try:
        meta = load_metadata(args.metadata_json)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: cannot read metadata JSON: {exc}", file=sys.stderr)
        return 2

    errors = errors_for_metadata(meta, str(args.output) if args.output else None)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.validate_only:
        print("OK: visual card metadata is valid")
        return 0

    output = args.output or Path(str(meta["output_image_path"]))
    try:
        render_card(meta, output)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: cannot render PNG: {exc}", file=sys.stderr)
        return 2

    print(f"OK: rendered {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

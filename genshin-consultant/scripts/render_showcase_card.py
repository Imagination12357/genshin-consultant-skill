#!/usr/bin/env python3
"""Render image-based Genshin weapon/artifact showcase cards.

This renderer is intentionally aligned with render_html_report.py's dark HUD
visual language so build reports, weapon rankings, and artifact recommendations
look like one design system.
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
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except Exception as exc:  # noqa: BLE001
    print(f"ERROR: Pillow is required for showcase rendering: {exc}", file=sys.stderr)
    raise


ALLOWED_CARD_TYPES = {"weapon_top5_card", "artifact_showcase_card"}

THEMES = {
    "hydro": {
        "bg1": (6, 58, 111),
        "bg2": (44, 138, 200),
        "bg3": (6, 23, 43),
        "accent": (99, 199, 255),
        "accent2": (213, 243, 255),
        "panel": (6, 42, 76),
        "panel2": (20, 79, 120),
        "line": (187, 231, 255),
    },
    "pyro": {
        "bg1": (127, 23, 11),
        "bg2": (212, 90, 50),
        "bg3": (53, 16, 6),
        "accent": (255, 122, 69),
        "accent2": (255, 208, 184),
        "panel": (82, 18, 8),
        "panel2": (120, 35, 18),
        "line": (255, 199, 169),
    },
    "electro": {
        "bg1": (52, 20, 109),
        "bg2": (129, 88, 219),
        "bg3": (18, 8, 36),
        "accent": (184, 149, 255),
        "accent2": (234, 220, 255),
        "panel": (40, 18, 77),
        "panel2": (86, 48, 140),
        "line": (222, 204, 255),
    },
    "physical": {
        "bg1": (61, 65, 72),
        "bg2": (138, 144, 155),
        "bg3": (21, 23, 27),
        "accent": (217, 224, 234),
        "accent2": (246, 248, 251),
        "panel": (42, 45, 51),
        "panel2": (78, 83, 92),
        "line": (232, 237, 245),
    },
}

ELEMENT_ALIASES = {
    "water": "hydro",
    "\ubb3c": "hydro",
    "fire": "pyro",
    "\ubd88": "pyro",
    "lightning": "electro",
    "\ubc88\uac1c": "electro",
}


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("metadata root must be an object")
    return data


def validate(meta: dict[str, Any], output_override: Path | None = None) -> list[str]:
    errors: list[str] = []
    card_type = meta.get("card_type")
    if card_type not in ALLOWED_CARD_TYPES:
        errors.append(f"card_type must be one of {sorted(ALLOWED_CARD_TYPES)}")
    if not isinstance(meta.get("title"), str) or not meta["title"].strip():
        errors.append("title must be a non-empty string")
    if not output_override and not str(meta.get("output_image_path", "")).strip():
        errors.append("output_image_path must be set when --output is not provided")
    items = meta.get("items")
    if not isinstance(items, list) or not items:
        errors.append("items must be a non-empty list")
    else:
        if len(items) > 5:
            errors.append("items must contain at most 5 entries")
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"items[{idx}] must be an object")
                continue
            if not str(item.get("name", "")).strip():
                errors.append(f"items[{idx}].name must be a non-empty string")
    for key in ("source_ids", "image_source_ids", "summary_lines"):
        if key in meta and not isinstance(meta[key], list):
            errors.append(f"{key} must be a list when present")
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


def normalize_element(value: Any) -> str:
    text = str(value or "").strip().casefold().replace(" ", "")
    return ELEMENT_ALIASES.get(text, text if text in THEMES else "hydro")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = []
    if sys.platform.startswith("win"):
        candidates.extend(
            [
                r"C:\Windows\Fonts\malgunbd.ttf" if bold else r"C:\Windows\Fonts\malgun.ttf",
                r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
                r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
            ]
        )
    candidates.extend(
        [
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    )
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def wrap_text(draw: ImageDraw.ImageDraw, text: Any, fnt: ImageFont.ImageFont, max_width: int, max_lines: int) -> list[str]:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if not value:
        return [""]
    words = value.split(" ") if " " in value else list(value)
    sep = " " if " " in value else ""
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else current + sep + word
        if text_size(draw, candidate, fnt)[0] <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
    if lines and len(lines) == max_lines:
        last = lines[-1]
        source = value.replace(sep, "")
        if len("".join(lines)) < len(source):
            while last and text_size(draw, last + "...", fnt)[0] > max_width:
                last = last[:-1]
            lines[-1] = (last + "...") if last else "..."
    return lines or [""]


def draw_gradient(draw: ImageDraw.ImageDraw, width: int, height: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> None:
    for y in range(height):
        ratio = y / max(1, height - 1)
        color = tuple(int(top[i] * (1 - ratio) + bottom[i] * ratio) for i in range(3))
        draw.line([(0, y), (width, y)], fill=color)


def draw_background(base: Image.Image, theme: dict[str, tuple[int, int, int]]) -> None:
    draw = ImageDraw.Draw(base, "RGBA")
    draw_gradient(draw, base.width, base.height, theme["bg1"], theme["bg3"])
    for x in range(0, base.width, 220):
        draw.rounded_rectangle((x - 80, 120, x + 120, 132), radius=6, fill=(*theme["accent"], 28))
    draw.polygon([(0, base.height), (base.width, base.height), (base.width, int(base.height * 0.58))], fill=(0, 0, 0, 24))


def load_icon(path_text: Any, size: int) -> Image.Image | None:
    if not path_text:
        return None
    path = Path(str(path_text))
    if not path.exists():
        return None
    try:
        img = Image.open(path).convert("RGBA")
    except Exception:
        return None
    img.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    canvas.alpha_composite(img, ((size - img.width) // 2, (size - img.height) // 2))
    return canvas


def placeholder_icon(label: str, size: int, theme: dict[str, tuple[int, int, int]]) -> Image.Image:
    img = Image.new("RGBA", (size, size), (*theme["panel2"], 180))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((12, 12, size - 12, size - 12), radius=20, outline=(*theme["line"], 180), width=3)
    fnt = font(40, bold=True)
    initials = "".join(part[:1].upper() for part in label.split()[:2]) or "?"
    initials = initials[:2]
    w, h = text_size(draw, initials, fnt)
    draw.text(((size - w) / 2, (size - h) / 2), initials, font=fnt, fill=theme["accent2"])
    return img


def paste_icon(base: Image.Image, icon: Image.Image, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    bg = Image.new("RGBA", (x2 - x1, y2 - y1), (255, 255, 255, 0))
    bg.alpha_composite(icon, ((bg.width - icon.width) // 2, (bg.height - icon.height) // 2))
    base.alpha_composite(bg, (x1, y1))


def draw_panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], theme: dict[str, tuple[int, int, int]]) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle((x1 + 6, y1 + 7, x2 + 6, y2 + 7), radius=18, fill=(0, 0, 0, 54))
    draw.rounded_rectangle(box, radius=18, fill=(*theme["panel"], 178), outline=(*theme["line"], 120), width=1)
    draw.rounded_rectangle((x1, y1, x2, y1 + 8), radius=4, fill=(*theme["accent"], 230))


def draw_chip(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, theme: dict[str, tuple[int, int, int]], fnt: ImageFont.ImageFont) -> None:
    if not text:
        return
    w, h = text_size(draw, text, fnt)
    draw.rounded_rectangle((x, y, x + w + 24, y + h + 12), radius=10, fill=(*theme["panel2"], 220), outline=(*theme["line"], 110))
    draw.text((x + 12, y + 6), text, font=fnt, fill=theme["accent2"])


def item_detail_lines(item: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    main = item.get("main_option") or item.get("main_stat")
    sub = item.get("substats") or item.get("substat_priority")
    if main:
        lines.append(f"주옵: {main}")
    if isinstance(sub, list):
        sub_text = " > ".join(str(x) for x in sub if str(x).strip())
    else:
        sub_text = str(sub or "")
    if sub_text:
        lines.append(f"부옵: {sub_text}")
    if not lines and item.get("note"):
        lines.append(str(item.get("note")))
    return lines


def render(meta: dict[str, Any], output: Path) -> None:
    card_type = str(meta["card_type"])
    is_weapon = card_type == "weapon_top5_card"
    width = int(meta.get("width") or 1600)
    height = int(meta.get("height") or (720 if is_weapon else 760))
    theme = THEMES[normalize_element(meta.get("theme_element") or meta.get("element") or "hydro")]

    base = Image.new("RGBA", (width, height), (*theme["bg3"], 255))
    draw_background(base, theme)
    draw = ImageDraw.Draw(base, "RGBA")

    title_font = font(38, bold=True)
    subtitle_font = font(18, bold=True)
    summary_font = font(22, bold=True)
    name_font = font(22, bold=True)
    detail_font = font(16, bold=True)
    note_font = font(15, bold=True)
    badge_font = font(16, bold=True)
    rank_font = font(24, bold=True)

    title = str(meta.get("title", "Genshin Showcase"))
    subtitle = str(meta.get("subtitle") or "")
    draw.rectangle((48, 38, 62, 92), fill=theme["accent"])
    draw.text((88, 34), title, font=title_font, fill=(255, 255, 255))
    if subtitle:
        draw.text((90, 82), subtitle, font=subtitle_font, fill=theme["accent2"])

    header_bottom = 112
    summary_lines = [str(x) for x in meta.get("summary_lines", []) if str(x).strip()]
    if summary_lines:
        summary = " / ".join(summary_lines[:2])
        wrapped_summary = wrap_text(draw, summary, summary_font, width - 180, 2)
        summary_h = len(wrapped_summary) * 30 + 10
        draw.rounded_rectangle((84, 100, width - 84, 100 + summary_h), radius=10, fill=(*theme["bg1"], 218))
        for idx, line in enumerate(wrapped_summary):
            draw.text((90, 105 + idx * 30), line, font=summary_font, fill=(255, 255, 255))
            header_bottom = 138 + idx * 30

    items = meta.get("items", [])[:5]
    count = max(1, len(items))
    margin_x = 48
    gap = 22
    slot_w = (width - margin_x * 2 - gap * (count - 1)) // count
    slot_h = 470 if is_weapon else 500
    y_slots = max(148, header_bottom + 22)
    icon_size = 178 if is_weapon else 188

    for idx, item in enumerate(items):
        x = margin_x + idx * (slot_w + gap)
        y = y_slots
        draw_panel(draw, (x, y, x + slot_w, y + slot_h), theme)

        rank_text = f"#{item.get('rank', idx + 1)}"
        draw.rounded_rectangle((x + 18, y + 18, x + 88, y + 52), radius=11, fill=(*theme["accent"], 230))
        draw.text((x + 30, y + 21), rank_text, font=rank_font, fill=(255, 255, 255))
        badge = str(item.get("badge") or item.get("rating") or "")
        if badge:
            bw, _ = text_size(draw, badge, badge_font)
            draw_chip(draw, x + slot_w - bw - 46, y + 18, badge, theme, badge_font)

        name = str(item.get("name", "Unknown"))
        icon = load_icon(item.get("image_path"), icon_size) or placeholder_icon(name, icon_size, theme)
        paste_icon(base, icon, (x + (slot_w - icon_size) // 2, y + 70, x + (slot_w + icon_size) // 2, y + 70 + icon_size))

        name_y = y + 70 + icon_size + 18
        for line in wrap_text(draw, name, name_font, slot_w - 34, 2):
            lw, _ = text_size(draw, line, name_font)
            draw.text((x + (slot_w - lw) / 2, name_y), line, font=name_font, fill=(255, 255, 255))
            name_y += 28

        detail_y = name_y + 8
        detail_lines = item_detail_lines(item)
        for line in detail_lines[:3]:
            for piece in wrap_text(draw, line, detail_font, slot_w - 36, 2):
                lw, _ = text_size(draw, piece, detail_font)
                draw.text((x + (slot_w - lw) / 2, detail_y), piece, font=detail_font, fill=theme["accent2"])
                detail_y += 23

        note = str(item.get("note") or "")
        if note and not detail_lines:
            for piece in wrap_text(draw, note, note_font, slot_w - 36, 3):
                lw, _ = text_size(draw, piece, note_font)
                draw.text((x + (slot_w - lw) / 2, detail_y), piece, font=note_font, fill=(230, 242, 250))
                detail_y += 22

    output.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render image-based Genshin showcase cards")
    parser.add_argument("metadata_json", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    try:
        meta = read_json(args.metadata_json)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: cannot read metadata JSON: {exc}", file=sys.stderr)
        return 2

    errors = validate(meta, args.output)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.validate_only:
        print("OK: showcase metadata is valid")
        return 0

    output = args.output or Path(str(meta["output_image_path"]))
    try:
        render(meta, output)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: cannot render showcase card: {exc}", file=sys.stderr)
        return 2
    print(f"OK: rendered {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

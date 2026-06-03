#!/usr/bin/env python3
"""Compose multiple rendered Genshin cards into one vertical page PNG."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception as exc:  # noqa: BLE001
    print(f"ERROR: Pillow is required for page composition: {exc}", file=sys.stderr)
    raise


THEMES = {
    "pyro": {
        "bg1": (70, 14, 6),
        "bg2": (155, 31, 16),
        "bg3": (12, 12, 14),
        "accent": (255, 119, 65),
        "accent2": (255, 210, 185),
        "line": (255, 180, 140),
    },
    "hydro": {
        "bg1": (6, 42, 76),
        "bg2": (22, 104, 165),
        "bg3": (8, 14, 24),
        "accent": (99, 199, 255),
        "accent2": (213, 243, 255),
        "line": (187, 231, 255),
    },
    "electro": {
        "bg1": (35, 16, 74),
        "bg2": (93, 55, 160),
        "bg3": (12, 10, 22),
        "accent": (184, 149, 255),
        "accent2": (234, 220, 255),
        "line": (222, 204, 255),
    },
    "physical": {
        "bg1": (35, 38, 44),
        "bg2": (74, 80, 90),
        "bg3": (14, 15, 18),
        "accent": (217, 224, 234),
        "accent2": (246, 248, 251),
        "line": (232, 237, 245),
    },
}

ELEMENT_ALIASES = {
    "fire": "pyro",
    "불": "pyro",
    "불원소": "pyro",
    "water": "hydro",
    "물": "hydro",
    "물원소": "hydro",
    "lightning": "electro",
    "번개": "electro",
    "번개원소": "electro",
}


def normalize_element(value: Any) -> str:
    text = str(value or "").strip().casefold().replace(" ", "")
    return ELEMENT_ALIASES.get(text, text if text in THEMES else "physical")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates: list[str] = []
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


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("metadata root must be an object")
    return data


def validate(meta: dict[str, Any], output_override: Path | None = None) -> list[str]:
    errors: list[str] = []
    if meta.get("card_type") not in {"visual_page", "page"}:
        errors.append("card_type must be visual_page or page")
    cards = meta.get("cards")
    if not isinstance(cards, list) or not cards:
        errors.append("cards must be a non-empty list")
    else:
        for idx, card in enumerate(cards):
            if not isinstance(card, dict):
                errors.append(f"cards[{idx}] must be an object")
                continue
            image_path = Path(str(card.get("image_path") or ""))
            if not image_path.exists():
                errors.append(f"cards[{idx}].image_path does not exist: {image_path}")
    if not output_override and not str(meta.get("output_image_path") or "").strip():
        errors.append("output_image_path must be set when --output is not provided")
    return errors


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def draw_gradient(draw: ImageDraw.ImageDraw, width: int, height: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> None:
    for y in range(height):
        ratio = y / max(1, height - 1)
        color = tuple(int(top[i] * (1 - ratio) + bottom[i] * ratio) for i in range(3))
        draw.line((0, y, width, y), fill=color)


def rounded_card_shadow(page: Image.Image, box: tuple[int, int, int, int], radius: int = 26) -> None:
    draw = ImageDraw.Draw(page, "RGBA")
    x1, y1, x2, y2 = box
    draw.rounded_rectangle((x1 + 10, y1 + 12, x2 + 10, y2 + 12), radius=radius, fill=(0, 0, 0, 92))
    draw.rounded_rectangle(box, radius=radius, fill=(255, 255, 255, 18), outline=(255, 255, 255, 46), width=1)


def compose(meta: dict[str, Any], output: Path) -> None:
    theme = THEMES[normalize_element(meta.get("theme_element"))]
    width = int(meta.get("width") or 1800)
    margin_x = int(meta.get("margin_x") or 72)
    gap = int(meta.get("gap") or 48)
    header_h = int(meta.get("header_height") or 160)
    footer_h = int(meta.get("footer_height") or 28)
    label_gap = int(meta.get("label_gap") or 42)
    fit_width = bool(meta.get("fit_width", False))
    target_w = width - margin_x * 2

    prepared: list[tuple[dict[str, Any], Image.Image, int]] = []
    total_cards_h = 0
    for card in meta["cards"]:
        img = Image.open(str(card["image_path"])).convert("RGBA")
        scale = target_w / img.width if fit_width else min(1.0, target_w / img.width)
        if "scale" in card:
            explicit_scale = float(card["scale"])
            scale = explicit_scale if fit_width else min(scale, explicit_scale)
        new_size = (int(img.width * scale), int(img.height * scale))
        if new_size != img.size:
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        label_space = label_gap if str(card.get("label") or "").strip() else 0
        prepared.append((card, img, label_space))
        total_cards_h += img.height + label_space

    height = header_h + total_cards_h + gap * (len(prepared) - 1) + footer_h
    page = Image.new("RGBA", (width, height), (*theme["bg3"], 255))
    draw = ImageDraw.Draw(page, "RGBA")
    draw_gradient(draw, width, height, theme["bg1"], theme["bg3"])
    draw.rectangle((0, 0, width, header_h), fill=(*theme["bg1"], 220))
    draw.rectangle((0, header_h - 8, width, header_h), fill=(*theme["accent"], 230))

    title = str(meta.get("title") or "Genshin Consultation")
    subtitle = str(meta.get("subtitle") or "")
    title_font = font(46, bold=True)
    subtitle_font = font(22, bold=True)
    draw.rectangle((46, 42, 62, 96), fill=theme["accent"])
    draw.text((86, 34), title, font=title_font, fill=(255, 255, 255))
    if subtitle:
        draw.text((88, 94), subtitle, font=subtitle_font, fill=theme["accent2"])

    y = header_h + 30
    label_font = font(20, bold=True)
    for card, img, label_space in prepared:
        x = (width - img.width) // 2
        label = str(card.get("label") or "")
        if label:
            lw, lh = text_size(draw, label, label_font)
            label_y = y
            draw.rounded_rectangle((x, label_y, x + lw + 28, label_y + lh + 12), radius=12, fill=(*theme["accent"], 230))
            draw.text((x + 14, label_y + 4), label, font=label_font, fill=(255, 255, 255))
        card_y = y + label_space
        rounded_card_shadow(page, (x - 8, card_y - 8, x + img.width + 8, card_y + img.height + 8))
        page.alpha_composite(img, (x, card_y))
        y = card_y + img.height + gap

    output.parent.mkdir(parents=True, exist_ok=True)
    page.convert("RGB").save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compose rendered Genshin cards into one vertical page")
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
        print("OK: visual page metadata is valid")
        return 0

    output = args.output or Path(str(meta["output_image_path"]))
    try:
        compose(meta, output)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: cannot compose visual page: {exc}", file=sys.stderr)
        return 2
    print(f"OK: composed {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

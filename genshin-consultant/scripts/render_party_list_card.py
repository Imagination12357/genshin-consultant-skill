#!/usr/bin/env python3
"""Render a five-team Genshin party recommendation list card."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception as exc:  # noqa: BLE001
    print(f"ERROR: Pillow is required for party list rendering: {exc}", file=sys.stderr)
    raise


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
    "물": "hydro",
    "fire": "pyro",
    "불": "pyro",
    "lightning": "electro",
    "번개": "electro",
}


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("metadata root must be an object")
    return data


def validate(meta: dict[str, Any], output_override: Path | None = None) -> list[str]:
    errors: list[str] = []
    if meta.get("card_type") not in {"party_list_card", "party_recommendation_list"}:
        errors.append("card_type must be party_list_card")
    teams = meta.get("teams")
    if not isinstance(teams, list) or not teams:
        errors.append("teams must be a non-empty list")
    elif len(teams) > 5:
        errors.append("teams must contain at most 5 entries")
    else:
        for idx, team in enumerate(teams):
            if not isinstance(team, dict):
                errors.append(f"teams[{idx}] must be an object")
                continue
            members = team.get("characters")
            if not isinstance(members, list) or len(members) != 4:
                errors.append(f"teams[{idx}].characters must contain exactly 4 entries")
    if not output_override and not str(meta.get("output_image_path") or "").strip():
        errors.append("output_image_path must be set when --output is not provided")
    suspicious = find_encoding_corruption(meta)
    if suspicious:
        errors.append(f"metadata appears encoding-corrupted at {suspicious}")
    return errors


def looks_encoding_corrupted(value: str) -> bool:
    if "\ufffd" in value or "???" in value:
        return True
    return value.count("?") >= 2 and any(ord(ch) > 127 for ch in value)


def find_encoding_corruption(value: Any, path: str = "$") -> str | None:
    if isinstance(value, str):
        return path if looks_encoding_corrupted(value) else None
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


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def wrap_text(draw: ImageDraw.ImageDraw, text: Any, fnt: ImageFont.ImageFont, max_width: int, max_lines: int) -> list[str]:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if not value:
        return []
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
    if len(lines) == max_lines and len("".join(lines).replace(" ", "")) < len(value.replace(" ", "")):
        last = lines[-1]
        while last and text_size(draw, last + "...", fnt)[0] > max_width:
            last = last[:-1]
        lines[-1] = last + "..." if last else "..."
    return lines[:max_lines]


def draw_gradient(draw: ImageDraw.ImageDraw, width: int, height: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> None:
    for y in range(height):
        ratio = y / max(1, height - 1)
        color = tuple(int(top[i] * (1 - ratio) + bottom[i] * ratio) for i in range(3))
        draw.line((0, y, width, y), fill=color)


def draw_background(base: Image.Image, theme: dict[str, tuple[int, int, int]]) -> None:
    draw = ImageDraw.Draw(base, "RGBA")
    draw_gradient(draw, base.width, base.height, theme["bg1"], theme["bg3"])
    for x in range(0, base.width, 240):
        draw.rounded_rectangle((x - 80, 124, x + 130, 138), radius=7, fill=(*theme["accent"], 18))
    draw.polygon([(0, base.height), (base.width, base.height), (base.width, int(base.height * 0.66))], fill=(0, 0, 0, 28))


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
    img = Image.new("RGBA", (size, size), (*theme["panel2"], 220))
    draw = ImageDraw.Draw(img, "RGBA")
    draw.rounded_rectangle((5, 5, size - 5, size - 5), radius=16, outline=(*theme["line"], 160), width=2)
    fnt = font(30, bold=True)
    initials = "".join(part[:1].upper() for part in label.split()[:2])[:2] or "?"
    w, h = text_size(draw, initials, fnt)
    draw.text(((size - w) / 2, (size - h) / 2), initials, font=fnt, fill=theme["accent2"])
    return img


def draw_chip(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, theme: dict[str, tuple[int, int, int]], fnt: ImageFont.ImageFont) -> None:
    if not text:
        return
    w, h = text_size(draw, text, fnt)
    draw.rounded_rectangle((x, y, x + w + 22, y + h + 12), radius=10, fill=(*theme["panel2"], 225), outline=(*theme["line"], 105))
    draw.text((x + 11, y + 6), text, font=fnt, fill=theme["accent2"])


def draw_member(
    base: Image.Image,
    draw: ImageDraw.ImageDraw,
    member: dict[str, Any],
    box: tuple[int, int, int, int],
    theme: dict[str, tuple[int, int, int]],
    fonts: dict[str, ImageFont.ImageFont],
) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=15, fill=(*theme["panel2"], 165), outline=(*theme["line"], 90), width=1)
    name = str(member.get("name") or "Unknown")
    icon = load_icon(member.get("icon_path") or member.get("image_path"), 78) or placeholder_icon(name, 78, theme)
    icon_box = (x1 + 12, y1 + 18, x1 + 90, y1 + 96)
    draw.rounded_rectangle(icon_box, radius=14, fill=(0, 0, 0, 56), outline=(*theme["line"], 120), width=1)
    base.alpha_composite(icon, (icon_box[0], icon_box[1]))

    text_x = x1 + 104
    max_w = max(80, x2 - text_x - 12)
    draw.text((text_x, y1 + 18), name, font=fonts["member_name"], fill=(255, 255, 255))
    role = str(member.get("role") or "")
    y = y1 + 53
    role_lines = wrap_text(draw, role, fonts["member_role"], max_w, 1 if member.get("build") else 2)
    for line in role_lines:
        draw.text((text_x, y), line, font=fonts["member_role"], fill=theme["accent2"])
        y += 22
    build = str(member.get("build") or "")
    if build:
        for line in wrap_text(draw, build, fonts["member_small"], max_w, 1):
            draw.text((text_x, y1 + 80), line, font=fonts["member_small"], fill=(230, 244, 252))


def render(meta: dict[str, Any], output: Path) -> None:
    teams = meta.get("teams", [])[:5]
    width = int(meta.get("width") or 1800)
    height = int(meta.get("height") or max(920, 205 + len(teams) * 158))
    theme = THEMES[normalize_element(meta.get("theme_element") or "hydro")]

    base = Image.new("RGBA", (width, height), (*theme["bg3"], 255))
    draw_background(base, theme)
    draw = ImageDraw.Draw(base, "RGBA")

    fonts = {
        "title": font(42, bold=True),
        "subtitle": font(20, bold=True),
        "rank": font(24, bold=True),
        "team": font(28, bold=True),
        "badge": font(16, bold=True),
        "note": font(18, bold=True),
        "member_name": font(22, bold=True),
        "member_role": font(16, bold=True),
        "member_small": font(14, bold=True),
    }

    draw.rectangle((52, 42, 66, 96), fill=theme["accent"])
    draw.text((94, 34), str(meta.get("title") or "Party Recommendations"), font=fonts["title"], fill=(255, 255, 255))
    subtitle = str(meta.get("subtitle") or "")
    if subtitle:
        draw.text((96, 92), subtitle, font=fonts["subtitle"], fill=theme["accent2"])
    element_label = str(meta.get("element_label") or "")
    if element_label:
        draw_chip(draw, width - 190, 50, element_label, theme, fonts["badge"])

    x = 70
    inner_w = width - 140
    header_h = 142
    footer_h = 18
    row_gap = 16
    available_h = height - header_h - footer_h - 36 - row_gap * max(0, len(teams) - 1)
    row_h = max(132, available_h // max(1, len(teams)))
    y = header_h + 18

    for idx, team in enumerate(teams):
        y2 = y + row_h
        draw.rounded_rectangle((x + 8, y + 9, x + inner_w + 8, y2 + 9), radius=20, fill=(0, 0, 0, 74))
        draw.rounded_rectangle((x, y, x + inner_w, y2), radius=20, fill=(*theme["panel"], 188), outline=(*theme["line"], 118), width=1)
        draw.rounded_rectangle((x, y, x + inner_w, y + 8), radius=5, fill=(*theme["accent"], 235))

        rank = str(team.get("rank") or idx + 1).zfill(2)
        draw.rounded_rectangle((x + 24, y + 22, x + 86, y + 58), radius=11, fill=(*theme["accent"], 235))
        draw.text((x + 39, y + 25), rank, font=fonts["rank"], fill=(255, 255, 255))

        title_x = x + 104
        draw.text((title_x, y + 18), str(team.get("name") or f"추천 파티 {idx + 1}"), font=fonts["team"], fill=(255, 255, 255))
        draw_chip(draw, title_x, y + 60, str(team.get("reaction") or ""), theme, fonts["badge"])
        note_text = str(team.get("note") or "")
        rotation = str(team.get("rotation") or "")
        detail_text = note_text if not rotation else f"{note_text} / 로테이션: {rotation}"
        detail_y = y + 96
        for line in wrap_text(draw, detail_text, fonts["note"], 520, 2):
            draw.text((x + 28, detail_y), line, font=fonts["note"], fill=(235, 247, 255))
            detail_y += 23

        member_x = x + 640
        member_gap = 16
        member_w = (inner_w - 640 - 28 - member_gap * 3) // 4
        member_y = y + 22
        member_h = row_h - 44
        for cidx, member in enumerate(team.get("characters", [])[:4]):
            mx = member_x + cidx * (member_w + member_gap)
            draw_member(base, draw, member, (mx, member_y, mx + member_w, member_y + member_h), theme, fonts)

        y = y2 + row_gap

    output.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a Genshin party recommendation list card")
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
        print("OK: party list metadata is valid")
        return 0

    output = args.output or Path(str(meta["output_image_path"]))
    try:
        render(meta, output)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: cannot render party list card: {exc}", file=sys.stderr)
        return 2
    print(f"OK: rendered {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

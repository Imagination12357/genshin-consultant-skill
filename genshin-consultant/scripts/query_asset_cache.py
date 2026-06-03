#!/usr/bin/env python3
"""Query the reusable Genshin image asset cache."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILL_ASSET_ROOT = SKILL_ROOT / "assets" / "genshin-assets" / "current"
DEFAULT_CACHE_ROOT = Path(os.environ.get("GENSHIN_ASSET_ROOT", str(SKILL_ASSET_ROOT)))


def normalize(text: str) -> str:
    return re.sub(r"[\s_'\-\"’:/]+", "", text).casefold()


def read_index(cache_root: Path) -> dict[str, Any]:
    path = cache_root / "index.json"
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("index root must be an object")
    return data


def choose_variant(asset: dict[str, Any], preferred: str | None) -> dict[str, Any] | None:
    variants = asset.get("variants")
    if not isinstance(variants, dict) or not variants:
        return None
    if preferred and preferred in variants:
        return variants[preferred]
    for key in ("card", "icon"):
        if key in variants:
            return variants[key]
    first = next(iter(variants.values()))
    return first if isinstance(first, dict) else None


def asset_matches(asset: dict[str, Any], kind: str | None, tag: str | None) -> bool:
    if kind and asset.get("kind") != kind:
        return False
    if tag and tag not in set(asset.get("tags") or []):
        return False
    return True


def sort_key(asset: dict[str, Any]) -> tuple[int, str]:
    tags = set(asset.get("tags") or [])
    slot_order = [
        "flower-of-life-artifacts",
        "plume-of-death-artifacts",
        "sands-of-eon-artifacts",
        "goblet-of-eonothem-artifacts",
        "circlet-of-logos-artifacts",
    ]
    for idx, tag in enumerate(slot_order):
        if tag in tags:
            return (idx, str(asset.get("name", "")))
    return (99, str(asset.get("name", "")))


def find_assets(index: dict[str, Any], query: str, kind: str | None, tag: str | None, limit: int) -> list[dict[str, Any]]:
    assets_by_id = {asset["id"]: asset for asset in index.get("assets", []) if isinstance(asset, dict) and asset.get("id")}
    norm = normalize(query)
    ids = list(index.get("lookup", {}).get(norm, []))
    results = [assets_by_id[item_id] for item_id in ids if item_id in assets_by_id and asset_matches(assets_by_id[item_id], kind, tag)]

    if len(results) < limit:
        for asset in assets_by_id.values():
            if asset in results or not asset_matches(asset, kind, tag):
                continue
            haystack = " ".join(str(value) for value in [asset.get("name"), asset.get("slug"), asset.get("set_name"), " ".join(asset.get("aliases", []))])
            if norm and norm in normalize(haystack):
                results.append(asset)
            if len(results) >= limit:
                break
    return sorted(results, key=sort_key)[:limit]


def shape_result(asset: dict[str, Any], variant_name: str | None) -> dict[str, Any]:
    variant = choose_variant(asset, variant_name) or {}
    return {
        "id": asset.get("id"),
        "kind": asset.get("kind"),
        "name": asset.get("name"),
        "set_name": asset.get("set_name"),
        "tags": asset.get("tags", []),
        "variant": variant.get("variant"),
        "image_path": variant.get("local_path"),
        "image_source_id": asset.get("id"),
        "source_page": asset.get("source_page"),
        "asset_url": variant.get("asset_url"),
    }


def make_thumbnail(image_path: str | None, cache_root: Path, size: int | None) -> str | None:
    if not image_path or not size:
        return image_path
    try:
        from PIL import Image, ImageOps
    except Exception as exc:  # noqa: BLE001
        print(f"WARN: Pillow unavailable for thumbnails: {exc}", file=sys.stderr)
        return image_path

    src = Path(image_path)
    if not src.exists():
        return image_path
    try:
        rel = src.relative_to(cache_root)
    except ValueError:
        rel = Path(src.name)
    dst = cache_root / "thumbnails" / str(size) / rel
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return dst.as_posix()

    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as image:
        image = image.convert("RGBA")
        image.thumbnail((size, size), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        canvas.alpha_composite(image, ((size - image.width) // 2, (size - image.height) // 2))
        canvas.save(dst)
    return dst.as_posix()


def apply_thumbnails(rows: list[dict[str, Any]], cache_root: Path, size: int | None) -> list[dict[str, Any]]:
    if not size:
        return rows
    for row in rows:
        thumb_path = make_thumbnail(row.get("image_path"), cache_root, size)
        if thumb_path:
            row["thumb_path"] = thumb_path
            row["image_path"] = thumb_path
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Query Genshin image asset cache")
    parser.add_argument("queries", nargs="+", help="asset names, set names, or fuzzy text")
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE_ROOT)
    parser.add_argument("--kind", choices=["character", "weapon", "artifact", "artifact_set"])
    parser.add_argument("--tag")
    parser.add_argument("--variant", help="preferred variant, e.g. card or icon")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--format", choices=["json", "paths", "manifest-items"], default="json")
    parser.add_argument("--thumb-size", type=int, help="create square thumbnail PNGs and return those paths")
    args = parser.parse_args()

    try:
        index = read_index(args.cache_root)
        rows = []
        for query in args.queries:
            matches = find_assets(index, query, args.kind, args.tag, args.limit)
            rows.extend(shape_result(asset, args.variant) for asset in matches)
        rows = apply_thumbnails(rows, args.cache_root, args.thumb_size)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.format == "paths":
        for row in rows:
            if row.get("image_path"):
                print(row["image_path"])
    elif args.format == "manifest-items":
        print(json.dumps([{"name": row["name"], "image_path": row["image_path"], "image_source_id": row["image_source_id"]} for row in rows], ensure_ascii=False, indent=2))
    else:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())

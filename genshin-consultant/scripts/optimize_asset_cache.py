#!/usr/bin/env python3
"""Optimize large local Genshin asset-cache images.

This script targets the bulky cache entries that are used as visual inputs:

- character card variants are resized to half width/height and stored as WebP
- artifact-set representative previews preserve animation frames when possible

Use --dry-run first. Use --apply only after reviewing the planned changes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageSequence


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CACHE_ROOT = SKILL_ROOT / "assets" / "genshin-assets" / "current"


def cache_local_path(path: Path, cache_root: Path) -> str:
    return path.relative_to(cache_root).as_posix()


def sha1(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def load_index(cache_root: Path) -> dict[str, Any]:
    path = cache_root / "index.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("index root must be an object")
    return data


def save_index(cache_root: Path, index: dict[str, Any]) -> None:
    (cache_root / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


def webp_save(image: Image.Image, target: Path, quality: int) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, format="WEBP", quality=quality, method=6)


def first_frame(path: Path) -> Image.Image:
    image = Image.open(path)
    try:
        image.seek(0)
        return image.convert("RGBA")
    finally:
        image.close()


def image_frame_count(path: Path) -> int:
    with Image.open(path) as image:
        return int(getattr(image, "n_frames", 1))


def resize_half(image: Image.Image) -> Image.Image:
    width = max(1, image.width // 2)
    height = max(1, image.height // 2)
    return image.resize((width, height), Image.Resampling.LANCZOS)


def resize_to_max_width(image: Image.Image, max_width: int) -> Image.Image:
    if image.width <= max_width:
        return image
    height = max(1, round(image.height * (max_width / image.width)))
    return image.resize((max_width, height), Image.Resampling.LANCZOS)


def animated_webp_save(source: Path, target: Path, max_width: int, quality: int, frame_step: int, method: int) -> tuple[int, int, int]:
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        frames: list[Image.Image] = []
        durations: list[int] = []
        for idx, frame in enumerate(ImageSequence.Iterator(image)):
            duration = int(frame.info.get("duration", image.info.get("duration", 100)) or 100)
            if idx % frame_step != 0 and durations:
                durations[-1] += duration
                continue
            frame_image = resize_to_max_width(frame.convert("RGBA"), max_width)
            frames.append(frame_image)
            durations.append(duration)
        if not frames:
            raise ValueError(f"no animation frames found in {source}")
        loop = int(image.info.get("loop", 0) or 0)
        frames[0].save(
            target,
            format="WEBP",
            save_all=len(frames) > 1,
            append_images=frames[1:],
            duration=durations,
            loop=loop,
            quality=quality,
            method=method,
        )
        return frames[0].width, frames[0].height, len(frames)


def update_variant(variant: dict[str, Any], target: Path, cache_root: Path) -> None:
    variant["local_path"] = cache_local_path(target, cache_root)
    if target.suffix.casefold() == ".gif":
        variant["mime"] = "image/gif"
    else:
        variant["mime"] = "image/webp"
    variant["bytes"] = target.stat().st_size
    variant["sha1"] = sha1(target)
    with Image.open(target) as image:
        variant["width"] = image.width
        variant["height"] = image.height
        variant["frames"] = int(getattr(image, "n_frames", 1))


def optimize_variant(
    *,
    variant: dict[str, Any],
    cache_root: Path,
    mode: str,
    quality: int,
    artifact_max_width: int,
    artifact_frame_step: int,
    animated_webp_method: int,
    apply: bool,
) -> dict[str, Any] | None:
    local_path = variant.get("local_path")
    if not isinstance(local_path, str):
        return None
    source = cache_root / local_path
    if not source.exists():
        return {"source": local_path, "error": "missing source"}
    if source.suffix.casefold() == ".webp" and mode != "artifact_set":
        return {"source": local_path, "skipped": "already webp"}

    target = source.with_suffix(".webp")
    before = source.stat().st_size
    if mode == "character_card":
        image = first_frame(source)
        output = resize_half(image)
    elif mode == "artifact_set":
        with Image.open(source) as source_image:
            source_format = source_image.format
            source_width = source_image.width
            source_height = source_image.height
            frame_count = int(getattr(source_image, "n_frames", 1))
        if artifact_frame_step > 1:
            return {
                "source": local_path,
                "before": before,
                "width": source_width,
                "height": source_height,
                "frames": frame_count,
                "frame_step": artifact_frame_step,
                "mode": mode,
                "skipped": "duration-preserving frame reduction requires webpmux or equivalent tooling",
            }
        if source_format in {"GIF", "WEBP"} and source_width <= artifact_max_width and (frame_count <= 1 or artifact_frame_step <= 1):
            if apply:
                if target != source:
                    target = source
                update_variant(variant, target, cache_root)
            return {
                "source": local_path,
                "target": cache_local_path(target, cache_root),
                "before": before,
                "after": target.stat().st_size if apply else None,
                "width": source_width,
                "height": source_height,
                "frames": frame_count,
                "mode": mode,
                "optimized": "preserved animated WebP source",
            }
        if apply:
            tmp = target.with_name(target.name + ".tmp")
            if tmp.exists():
                tmp.unlink()
            width, height, output_frames = animated_webp_save(
                source,
                tmp,
                artifact_max_width,
                quality,
                max(1, artifact_frame_step),
                animated_webp_method,
            )
            tmp.replace(target)
            after = target.stat().st_size
            if after >= before and target != source:
                target.unlink()
                return {"source": local_path, "target": cache_local_path(target, cache_root), "before": before, "after": after, "skipped": "not smaller"}
            update_variant(variant, target, cache_root)
            variant["frames"] = output_frames
            if target != source:
                source.unlink()
        else:
            with Image.open(source) as image:
                preview = resize_to_max_width(image.convert("RGBA"), artifact_max_width)
                width, height = preview.width, preview.height
            after = None
        return {
            "source": local_path,
            "target": cache_local_path(target, cache_root),
            "before": before,
            "after": after,
            "width": width,
            "height": height,
            "frames": frame_count if not apply else variant.get("frames"),
            "frame_step": artifact_frame_step,
            "mode": mode,
        }
    else:
        raise ValueError(f"unsupported mode: {mode}")

    if apply:
        webp_save(output, target, quality)
        after = target.stat().st_size
        if after >= before and target != source:
            target.unlink()
            return {"source": local_path, "target": cache_local_path(target, cache_root), "before": before, "after": after, "skipped": "not smaller"}
        update_variant(variant, target, cache_root)
        if target != source:
            source.unlink()
    else:
        after = None

    return {
        "source": local_path,
        "target": cache_local_path(target, cache_root),
        "before": before,
        "after": after,
        "width": output.width,
        "height": output.height,
        "mode": mode,
    }


def optimize(index: dict[str, Any], cache_root: Path, args: argparse.Namespace) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for asset in index.get("assets", []):
        if not isinstance(asset, dict):
            continue
        variants = asset.get("variants")
        if not isinstance(variants, dict):
            continue
        if asset.get("kind") == "character" and isinstance(variants.get("card"), dict):
            result = optimize_variant(
                variant=variants["card"],
                cache_root=cache_root,
                mode="character_card",
                quality=args.quality,
                artifact_max_width=args.artifact_max_width,
                artifact_frame_step=args.artifact_frame_step,
                animated_webp_method=args.animated_webp_method,
                apply=args.apply,
            )
            if result:
                results.append(result)
        if asset.get("kind") == "artifact_set" and isinstance(variants.get("icon"), dict):
            result = optimize_variant(
                variant=variants["icon"],
                cache_root=cache_root,
                mode="artifact_set",
                quality=args.quality,
                artifact_max_width=args.artifact_max_width,
                artifact_frame_step=args.artifact_frame_step,
                animated_webp_method=args.animated_webp_method,
                apply=args.apply,
            )
            if result:
                results.append(result)
    return results


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    before = sum(int(row.get("before") or 0) for row in results)
    after_known = [row for row in results if isinstance(row.get("after"), int)]
    after = sum(int(row["after"]) for row in after_known)
    return {
        "items": len(results),
        "before_bytes": before,
        "after_bytes": after if after_known else None,
        "saved_bytes": before - after if after_known else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Optimize large Genshin asset-cache images")
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE_ROOT)
    parser.add_argument("--quality", type=int, default=82)
    parser.add_argument("--artifact-max-width", type=int, default=480)
    parser.add_argument("--artifact-frame-step", type=int, default=1, help="experimental: keep every Nth artifact-set animation frame")
    parser.add_argument("--animated-webp-method", type=int, default=0, help="libwebp method for animated WebP encoding, 0 is fastest")
    parser.add_argument("--apply", action="store_true", help="write optimized files and update index.json")
    parser.add_argument("--details", action="store_true", help="print per-file results")
    args = parser.parse_args()

    index = load_index(args.cache_root)
    results = optimize(index, args.cache_root, args)
    if args.apply:
        save_index(args.cache_root, index)

    print(json.dumps(summarize(results), ensure_ascii=False, indent=2))
    if args.details:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

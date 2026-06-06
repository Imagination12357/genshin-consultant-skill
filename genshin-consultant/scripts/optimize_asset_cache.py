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
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageSequence


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CACHE_ROOT = SKILL_ROOT / "assets" / "genshin-assets" / "current"


@dataclass(frozen=True)
class WebPMuxFrame:
    index: int
    width: int
    height: int
    duration: int
    x_offset: int
    y_offset: int
    dispose: str
    blend: str


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


def resize_to_max_width(image: Image.Image, max_width: int | None) -> Image.Image:
    if max_width is None:
        return image
    if image.width <= max_width:
        return image
    height = max(1, round(image.height * (max_width / image.width)))
    return image.resize((max_width, height), Image.Resampling.LANCZOS)


def webpmux_frames(path: Path, webpmux: str) -> list[WebPMuxFrame]:
    output = subprocess.check_output([webpmux, "-info", str(path)], text=True)
    frames: list[WebPMuxFrame] = []
    for line in output.splitlines():
        parts = line.split()
        if not parts or not parts[0].endswith(":") or not parts[0][:-1].isdigit():
            continue
        if len(parts) >= 10:
            frames.append(
                WebPMuxFrame(
                    index=int(parts[0][:-1]),
                    width=int(parts[1]),
                    height=int(parts[2]),
                    x_offset=int(parts[4]),
                    y_offset=int(parts[5]),
                    duration=int(parts[6]),
                    dispose=parts[7],
                    blend=parts[8],
                )
            )
    return frames


def webpmux_animation_options(path: Path, webpmux: str) -> tuple[int, tuple[int, int, int, int]]:
    output = subprocess.check_output([webpmux, "-info", str(path)], text=True)
    loop = 0
    rgba = (255, 255, 255, 255)
    for line in output.splitlines():
        parts = line.replace(":", " ").split()
        if "Background color" in line:
            color = next((part for part in parts if part.startswith("0x")), None)
            if color and len(color) == 10:
                value = int(color, 16)
                alpha = (value >> 24) & 0xFF
                red = (value >> 16) & 0xFF
                green = (value >> 8) & 0xFF
                blue = value & 0xFF
                rgba = (red, green, blue, alpha)
        if "Loop Count" in line:
            loop = int(parts[-1])
    return loop, rgba


def webpmux_frame_durations(path: Path, webpmux: str) -> list[int]:
    return [frame.duration for frame in webpmux_frames(path, webpmux)]


def scale_durations_to_total(durations: list[int], total: int) -> list[int]:
    current_total = sum(durations)
    if not durations or current_total <= 0 or total <= 0 or current_total == total:
        return durations
    scaled = [max(1, round(duration * total / current_total)) for duration in durations]
    scaled[-1] = max(1, scaled[-1] + total - sum(scaled))
    return scaled


def animated_webp_save(source: Path, target: Path, max_width: int | None, quality: int, frame_step: int, method: int) -> tuple[int, int, int]:
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


def animated_webp_mux_save(source: Path, target: Path, max_width: int | None, quality: int, frame_step: int, method: int) -> tuple[int, int, int]:
    cwebp = shutil.which("cwebp")
    webpmux = shutil.which("webpmux")
    if not cwebp or not webpmux:
        raise RuntimeError("cwebp and webpmux are required for duration-preserving frame reduction")

    target.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix.casefold() == ".webp":
        with Image.open(source) as source_image:
            if max_width is None or source_image.width <= max_width:
                return animated_webp_mux_container_save(source, target, frame_step, webpmux, cwebp, quality, method)

    with tempfile.TemporaryDirectory(prefix="asset-webp-") as temp_name:
        temp_dir = Path(temp_name)
        frame_entries: list[tuple[Path, int]] = []
        width = 0
        height = 0
        source_total_duration = 0
        if source.suffix.casefold() == ".webp":
            source_total_duration = sum(webpmux_frame_durations(source, webpmux))
        with Image.open(source) as image:
            loop = int(image.info.get("loop", 0) or 0)
            for idx, frame in enumerate(ImageSequence.Iterator(image)):
                duration = int(frame.info.get("duration", image.info.get("duration", 100)) or 100)
                if source.suffix.casefold() != ".webp":
                    source_total_duration += duration
                if idx % frame_step != 0 and frame_entries:
                    previous_frame, previous_duration = frame_entries[-1]
                    frame_entries[-1] = (previous_frame, previous_duration + duration)
                    continue
                frame_image = resize_to_max_width(frame.convert("RGBA"), max_width)
                width = frame_image.width
                height = frame_image.height
                png_frame = temp_dir / f"frame-{len(frame_entries):04d}.png"
                webp_frame = temp_dir / f"frame-{len(frame_entries):04d}.webp"
                frame_image.save(png_frame, format="PNG")
                subprocess.run(
                    [cwebp, "-quiet", "-q", str(quality), "-m", str(method), str(png_frame), "-o", str(webp_frame)],
                    check=True,
                )
                frame_entries.append((webp_frame, duration))

        if not frame_entries:
            raise ValueError(f"no animation frames found in {source}")

        if source_total_duration:
            frame_paths = [frame_path for frame_path, _duration in frame_entries]
            durations = scale_durations_to_total([duration for _frame_path, duration in frame_entries], source_total_duration)
            frame_entries = list(zip(frame_paths, durations))

        mux_args: list[str] = [webpmux]
        for frame_path, duration in frame_entries:
            mux_args.extend(["-frame", str(frame_path), f"+{duration}+0+0"])
        mux_args.extend(["-loop", str(loop), "-o", str(target)])
        subprocess.run(mux_args, check=True)
        return width, height, len(frame_entries)


def animated_webp_mux_container_save(
    source: Path,
    target: Path,
    frame_step: int,
    webpmux: str,
    cwebp: str,
    quality: int,
    method: int,
) -> tuple[int, int, int]:
    with tempfile.TemporaryDirectory(prefix="asset-webpmux-") as temp_name:
        temp_dir = Path(temp_name)
        frames = webpmux_frames(source, webpmux)
        if not frames:
            raise ValueError(f"no animation frames found in {source}")

        source_entries: list[tuple[Path, WebPMuxFrame, int]] = []
        for idx, frame in enumerate(frames):
            frame_path = temp_dir / f"frame-{idx + 1:04d}.webp"
            subprocess.run([webpmux, "-get", "frame", str(frame.index), str(source), "-o", str(frame_path)], check=True)
            source_entries.append((frame_path, frame, frame.duration))

        loop, background = webpmux_animation_options(source, webpmux)
        canvas_width = max(frame.x_offset + frame.width for _path, frame, _duration in source_entries)
        canvas_height = max(frame.y_offset + frame.height for _path, frame, _duration in source_entries)
        canvas = Image.new("RGBA", (canvas_width, canvas_height), background)
        output_entries: list[tuple[Path, int]] = []

        for idx, (frame_path, frame, duration) in enumerate(source_entries):
            previous_canvas = canvas.copy()
            with Image.open(frame_path) as frame_image:
                patch = frame_image.convert("RGBA")
            box = (frame.x_offset, frame.y_offset)
            if frame.blend.lower() == "yes":
                canvas.alpha_composite(patch, dest=box)
            else:
                canvas.paste(patch, box, patch)

            if idx % frame_step == 0:
                png_frame = temp_dir / f"canvas-{len(output_entries):04d}.png"
                webp_frame = temp_dir / f"canvas-{len(output_entries):04d}.webp"
                canvas.save(png_frame, format="PNG")
                subprocess.run(
                    [cwebp, "-quiet", "-q", str(quality), "-m", str(method), str(png_frame), "-o", str(webp_frame)],
                    check=True,
                )
                output_entries.append((webp_frame, duration))
            elif output_entries:
                previous_frame, previous_duration = output_entries[-1]
                output_entries[-1] = (previous_frame, previous_duration + duration)

            if frame.dispose.lower() == "background":
                clear = Image.new("RGBA", (frame.width, frame.height), background)
                canvas.paste(clear, box)
            elif frame.dispose.lower() == "previous":
                canvas = previous_canvas

        if not output_entries:
            raise ValueError(f"no animation frames selected from {source}")

        durations = scale_durations_to_total([duration for _frame_path, duration in output_entries], sum(frame.duration for _path, frame, _duration in source_entries))
        output_entries = list(zip([frame_path for frame_path, _duration in output_entries], durations))

        mux_args: list[str] = [webpmux]
        for frame_path, duration in output_entries:
            mux_args.extend(["-frame", str(frame_path), f"+{duration}+0+0"])
        mux_args.extend(["-loop", str(loop), "-o", str(target)])
        subprocess.run(mux_args, check=True)
        return canvas_width, canvas_height, len(output_entries)


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
    artifact_frame_step: int,
    animated_webp_method: int,
    apply: bool,
) -> dict[str, Any] | None:
    local_path = variant.get("local_path")
    if not isinstance(local_path, str):
        return None
    source = cache_root / local_path
    target = source.with_suffix(".webp")
    if mode == "static_webp" and not source.exists() and target.exists():
        if apply:
            update_variant(variant, target, cache_root)
        with Image.open(target) as target_image:
            return {
                "source": local_path,
                "target": cache_local_path(target, cache_root),
                "before": None,
                "after": target.stat().st_size if apply else None,
                "width": target_image.width,
                "height": target_image.height,
                "frames": int(getattr(target_image, "n_frames", 1)),
                "mode": mode,
                "optimized": "resumed existing WebP target",
            }
    if not source.exists():
        return {"source": local_path, "error": "missing source"}
    if source.suffix.casefold() == ".webp" and mode != "artifact_set":
        return {"source": local_path, "skipped": "already webp"}

    before = source.stat().st_size
    if mode == "character_card":
        image = first_frame(source)
        output = resize_half(image)
    elif mode == "static_webp":
        with Image.open(source) as source_image:
            source_width = source_image.width
            source_height = source_image.height
            frame_count = int(getattr(source_image, "n_frames", 1))
        if source.suffix.casefold() == ".webp":
            return {"source": local_path, "skipped": "already webp"}
        if frame_count > 1:
            return {
                "source": local_path,
                "before": before,
                "width": source_width,
                "height": source_height,
                "frames": frame_count,
                "mode": mode,
                "skipped": "animated source is not handled by static webp mode",
            }
        output = first_frame(source)
    elif mode == "artifact_set":
        with Image.open(source) as source_image:
            source_format = source_image.format
            source_width = source_image.width
            source_height = source_image.height
            frame_count = int(getattr(source_image, "n_frames", 1))
        optimization = variant.get("optimization")
        if (
            isinstance(optimization, dict)
            and optimization.get("type") == "artifact_set_frame_step"
            and optimization.get("frame_step") == artifact_frame_step
            and source_format == "WEBP"
        ):
            return {
                "source": local_path,
                "target": cache_local_path(source, cache_root),
                "before": before,
                "after": before if apply else None,
                "width": source_width,
                "height": source_height,
                "frames": frame_count,
                "frame_step": artifact_frame_step,
                "mode": mode,
                "skipped": "already optimized with this artifact frame step",
            }
        if frame_count <= 1:
            if source_format == "WEBP":
                if apply:
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
                    "optimized": "preserved static WebP source",
                }
            if apply:
                tmp = target.with_name(target.name + ".tmp")
                if tmp.exists():
                    tmp.unlink()
                output = first_frame(source)
                webp_save(output, tmp, quality)
                tmp.replace(target)
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
                "width": source_width,
                "height": source_height,
                "frames": frame_count,
                "mode": mode,
                "optimized": "converted static source",
            }
        if apply:
            tmp = target.with_name(target.name + ".tmp")
            if tmp.exists():
                tmp.unlink()
            width, height, output_frames = animated_webp_mux_save(
                source,
                tmp,
                None,
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
            variant["optimization"] = {
                "type": "artifact_set_frame_step",
                "frame_step": artifact_frame_step,
                "source_frames": frame_count,
                "source_width": source_width,
                "source_height": source_height,
            }
            if target != source:
                source.unlink()
        else:
            width, height = source_width, source_height
            after = None
            output_frames = (frame_count + max(1, artifact_frame_step) - 1) // max(1, artifact_frame_step)
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
                artifact_frame_step=args.artifact_frame_step,
                animated_webp_method=args.animated_webp_method,
                apply=args.apply,
            )
            if result:
                results.append(result)
        if args.include_weapons and asset.get("kind") == "weapon" and isinstance(variants.get("icon"), dict):
            result = optimize_variant(
                variant=variants["icon"],
                cache_root=cache_root,
                mode="static_webp",
                quality=args.quality,
                artifact_frame_step=args.artifact_frame_step,
                animated_webp_method=args.animated_webp_method,
                apply=args.apply,
            )
            if result:
                results.append(result)
        if args.include_artifacts and asset.get("kind") == "artifact" and isinstance(variants.get("icon"), dict):
            result = optimize_variant(
                variant=variants["icon"],
                cache_root=cache_root,
                mode="static_webp",
                quality=args.quality,
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
    parser.add_argument("--artifact-frame-step", type=int, default=1, help="experimental: keep every Nth artifact-set animation frame")
    parser.add_argument("--animated-webp-method", type=int, default=0, help="libwebp method for animated WebP encoding, 0 is fastest")
    parser.add_argument("--include-weapons", action="store_true", help="convert static weapon icons to WebP without resizing")
    parser.add_argument("--include-artifacts", action="store_true", help="convert static artifact icons to WebP without resizing")
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

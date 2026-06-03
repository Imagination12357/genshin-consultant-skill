#!/usr/bin/env python3
"""Fetch official/wiki image assets for Genshin visual cards.

Input manifest:
{
  "output_root": "generated/visuals/assets",
  "assets": [
    {
      "id": "img-columbina",
      "name": "Columbina",
      "kind": "character|weapon|artifact",
      "source_url": "https://...",
      "asset_url": "https://.../image.png optional",
      "filename": "columbina.png optional"
    }
  ]
}

If asset_url is missing, the script fetches source_url and tries common page
metadata such as og:image, twitter:image, and link rel=image_src.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import mimetypes
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


USER_AGENT = "Mozilla/5.0 (Codex genshin-consultant asset fetcher)"
IMAGE_META_PATTERNS = [
    re.compile(r'<meta[^>]+property=["\']og:image(?::secure_url)?["\'][^>]+content=["\']([^"\']+)["\']', re.I),
    re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image(?::secure_url)?["\']', re.I),
    re.compile(r'<meta[^>]+name=["\']twitter:image(?::src)?["\'][^>]+content=["\']([^"\']+)["\']', re.I),
    re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image(?::src)?["\']', re.I),
    re.compile(r'<link[^>]+rel=["\']image_src["\'][^>]+href=["\']([^"\']+)["\']', re.I),
    re.compile(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']image_src["\']', re.I),
]
FALLBACK_IMG_PATTERN = re.compile(r'<img[^>]+(?:src|data-src)=["\']([^"\']+\.(?:png|jpg|jpeg|webp)(?:\?[^"\']*)?)["\']', re.I)


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("manifest root must be an object")
    return data


def request_bytes(url: str) -> tuple[bytes, str]:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=30) as resp:  # noqa: S310 - skill intentionally fetches user-selected public assets
        content_type = resp.headers.get("Content-Type", "")
        return resp.read(), content_type


def discover_image_url(source_url: str) -> str | None:
    body, content_type = request_bytes(source_url)
    if content_type.lower().startswith("image/"):
        return source_url
    text = body.decode("utf-8", errors="replace")
    for pattern in IMAGE_META_PATTERNS:
        match = pattern.search(text)
        if match:
            return urljoin(source_url, html.unescape(match.group(1)))
    match = FALLBACK_IMG_PATTERN.search(text)
    if match:
        return urljoin(source_url, html.unescape(match.group(1)))
    return None


def safe_filename(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9가-힣._-]+", "-", text)
    text = text.strip("-._")
    return text or "asset"


def extension_from_url_or_type(url: str, content_type: str) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return suffix
    guessed = mimetypes.guess_extension(content_type.split(";")[0].strip().lower())
    if guessed in {".png", ".jpg", ".jpeg", ".webp"}:
        return guessed
    return ".png"


def fetch_asset(asset: dict[str, Any], output_root: Path) -> dict[str, Any]:
    source_url = str(asset.get("source_url") or "").strip()
    asset_url = str(asset.get("asset_url") or "").strip()
    if not asset_url:
        if not source_url:
            raise ValueError("asset requires asset_url or source_url")
        asset_url = discover_image_url(source_url) or ""
    if not asset_url:
        raise ValueError(f"could not discover image URL for {asset.get('id') or asset.get('name')}")

    raw, content_type = request_bytes(asset_url)
    if not content_type.lower().startswith("image/"):
        # Some CDNs omit or mislabel image content-type; keep the file if it has an image extension.
        suffix = Path(urlparse(asset_url).path).suffix.lower()
        if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise ValueError(f"asset URL did not return an image content-type: {asset_url}")

    digest = hashlib.sha1(raw).hexdigest()[:10]
    filename = str(asset.get("filename") or "").strip()
    if filename:
        path = output_root / filename
    else:
        stem = safe_filename(str(asset.get("name") or asset.get("id") or "asset"))
        path = output_root / f"{stem}-{digest}{extension_from_url_or_type(asset_url, content_type)}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)

    result = dict(asset)
    result["asset_url"] = asset_url
    result["local_path"] = str(path).replace("\\", "/")
    result["content_type"] = content_type or "not_visible"
    result["sha1"] = hashlib.sha1(raw).hexdigest()
    result["bytes"] = len(raw)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch official/wiki image assets for Genshin cards")
    parser.add_argument("manifest_json", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--output-manifest", type=Path)
    args = parser.parse_args()

    try:
        manifest = read_json(args.manifest_json)
        output_root = args.output_root or Path(str(manifest.get("output_root") or "generated/visuals/assets"))
        results = []
        errors = []
        for asset in manifest.get("assets", []):
            if not isinstance(asset, dict):
                errors.append({"error": "asset entry must be an object", "asset": asset})
                continue
            try:
                results.append(fetch_asset(asset, output_root))
            except Exception as exc:  # noqa: BLE001
                failed = dict(asset)
                failed["error"] = str(exc)
                errors.append(failed)
        output = {"assets": results, "errors": errors}
        output_manifest = args.output_manifest or args.manifest_json.with_name(args.manifest_json.stem + ".fetched.json")
        output_manifest.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"OK: fetched {len(results)} assets, {len(errors)} errors -> {output_manifest}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build a reusable Genshin image asset cache.

The cache is sourced from the Genshin Impact Fandom MediaWiki API. The files
are official in-game/wiki asset images, not fan art. The script stores images
locally and writes an index that visual card renderers can query quickly.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import mimetypes
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


API_URL = "https://genshin-impact.fandom.com/api.php"
USER_AGENT = "Mozilla/5.0 (Codex genshin-consultant asset cache builder)"
SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILL_ASSET_ROOT = SKILL_ROOT / "assets" / "genshin-assets" / "current"
DEFAULT_CACHE_ROOT = Path(os.environ.get("GENSHIN_ASSET_ROOT", str(SKILL_ASSET_ROOT)))

EXTRA_CHARACTER_PAGES = [
    "Durin",
    "Nicole",
]

SKIP_WEAPON_TITLES = {
    "Musou Isshin",
    "Weapon",
    "Weapon Series",
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = text.replace('"', "")
    text = re.sub(r"['’]", "", text)
    text = re.sub(r"[^a-z0-9가-힣]+", "-", text)
    text = text.strip("-")
    return text or "asset"


def normalize(text: str) -> str:
    return re.sub(r"[\s_'\-\"’:/]+", "", text).casefold()


def api_get(params: dict[str, Any]) -> dict[str, Any]:
    query = dict(params)
    query.setdefault("format", "json")
    url = API_URL + "?" + urlencode(query)
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=45) as resp:  # noqa: S310 - public MediaWiki API
        return json.loads(resp.read().decode("utf-8"))


def category_members(category_title: str, namespace: int = 0) -> list[str]:
    titles: list[str] = []
    params: dict[str, Any] = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": category_title,
        "cmnamespace": namespace,
        "cmlimit": "500",
    }
    while True:
        data = api_get(params)
        titles.extend(member["title"] for member in data.get("query", {}).get("categorymembers", []))
        cont = data.get("continue")
        if not cont:
            break
        params.update(cont)
    return titles


def query_pages(titles: list[str], props: str = "pageimages|categories") -> dict[str, dict[str, Any]]:
    pages: dict[str, dict[str, Any]] = {}
    for idx in range(0, len(titles), 40):
        batch = titles[idx : idx + 40]
        data = api_get(
            {
                "action": "query",
                "titles": "|".join(batch),
                "prop": props,
                "piprop": "original|name",
                "cllimit": "500",
                "imlimit": "500",
            }
        )
        for page in data.get("query", {}).get("pages", {}).values():
            title = page.get("title")
            if isinstance(title, str):
                pages[title] = page
    return pages


def query_wikitexts(titles: list[str]) -> dict[str, str]:
    pages: dict[str, str] = {}
    for idx in range(0, len(titles), 40):
        batch = titles[idx : idx + 40]
        data = api_get(
            {
                "action": "query",
                "titles": "|".join(batch),
                "prop": "revisions",
                "rvprop": "content",
                "rvslots": "main",
            }
        )
        for page in data.get("query", {}).get("pages", {}).values():
            title = page.get("title")
            revisions = page.get("revisions") or []
            content = ""
            if revisions:
                content = revisions[0].get("slots", {}).get("main", {}).get("*", "")
            if isinstance(title, str) and isinstance(content, str):
                pages[title] = content
    return pages


def strip_wiki_markup(text: str) -> str:
    text = html.unescape(text.strip())
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\{\{(?:ko|lang)\|([^{}|]+)(?:\|[^{}]*)?\}\}", r"\1", text, flags=re.I)
    text = re.sub(r"\[\[[^|\]]+\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"'{2,}", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def korean_aliases_from_wikitext(text: str) -> list[str]:
    aliases: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^\|\s*(?:\d+_)?ko\s*=\s*(.+?)\s*$", line)
        if not match:
            continue
        value = strip_wiki_markup(match.group(1))
        if value and any("가" <= ch <= "힣" for ch in value):
            aliases.append(value)
    return sorted(set(aliases))


def query_korean_aliases(titles: list[str]) -> dict[str, list[str]]:
    texts = query_wikitexts(titles)
    return {title: korean_aliases_from_wikitext(texts.get(title, "")) for title in titles}


def file_imageinfo(file_titles: list[str]) -> dict[str, dict[str, Any]]:
    infos: dict[str, dict[str, Any]] = {}
    unique = []
    seen = set()
    for title in file_titles:
        if not title.startswith("File:"):
            title = "File:" + title
        if title not in seen:
            seen.add(title)
            unique.append(title)

    for idx in range(0, len(unique), 40):
        batch = unique[idx : idx + 40]
        data = api_get(
            {
                "action": "query",
                "titles": "|".join(batch),
                "prop": "imageinfo",
                "iiprop": "url|mime|size|sha1",
            }
        )
        for page in data.get("query", {}).get("pages", {}).values():
            title = page.get("title")
            imageinfo = page.get("imageinfo") or []
            if isinstance(title, str) and imageinfo:
                infos[title] = imageinfo[0]
    return infos


def category_tags(categories: list[dict[str, Any]] | None) -> list[str]:
    tags: list[str] = []
    for item in categories or []:
        title = str(item.get("title", ""))
        if not title.startswith("Category:"):
            continue
        clean = title.removeprefix("Category:")
        tags.append(slugify(clean))
    return tags


def tags_for_character(categories: list[dict[str, Any]] | None) -> list[str]:
    tags = ["character"]
    for tag in category_tags(categories):
        if tag.endswith("-characters") or tag in {
            "pyro-characters",
            "hydro-characters",
            "electro-characters",
            "cryo-characters",
            "anemo-characters",
            "geo-characters",
            "dendro-characters",
            "5-star-characters",
            "4-star-characters",
            "sword-characters",
            "claymore-characters",
            "polearm-characters",
            "bow-characters",
            "catalyst-characters",
        }:
            tags.append(tag)
    return sorted(set(tags))


def tags_for_weapon(categories: list[dict[str, Any]] | None) -> list[str]:
    tags = ["weapon"]
    for tag in category_tags(categories):
        if tag.endswith("-weapons") or tag in {
            "swords",
            "claymores",
            "polearms",
            "bows",
            "catalysts",
            "5-star-weapons",
            "4-star-weapons",
            "3-star-weapons",
            "2-star-weapons",
            "1-star-weapons",
        }:
            tags.append(tag)
    return sorted(set(tags))


def tags_for_artifact_piece(piece_page: dict[str, Any], set_name: str) -> list[str]:
    tags = ["artifact", "artifact-piece", f"set-{slugify(set_name)}"]
    for tag in category_tags(piece_page.get("categories")):
        if tag.endswith("-artifacts") or tag in {
            "flower-of-life-artifacts",
            "plume-of-death-artifacts",
            "sands-of-eon-artifacts",
            "goblet-of-eonothem-artifacts",
            "circlet-of-logos-artifacts",
        }:
            tags.append(tag)
    return sorted(set(tags))


def extension_from_url_or_mime(url: str, mime: str | None) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return suffix
    guessed = mimetypes.guess_extension((mime or "").split(";")[0].strip())
    if guessed in IMAGE_EXTENSIONS:
        return guessed
    return ".png"


def download_asset(url: str, target: Path, refresh: bool = False) -> dict[str, Any]:
    if target.exists() and not refresh:
        raw = target.read_bytes()
        return {
            "local_path": str(target).replace("\\", "/"),
            "bytes": len(raw),
            "sha1": hashlib.sha1(raw).hexdigest(),
            "downloaded": False,
        }

    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=60) as resp:  # noqa: S310 - public wiki CDN URL
        raw = resp.read()
        content_type = resp.headers.get("Content-Type", "")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    return {
        "local_path": str(target).replace("\\", "/"),
        "content_type": content_type or "not_visible",
        "bytes": len(raw),
        "sha1": hashlib.sha1(raw).hexdigest(),
        "downloaded": True,
    }


def add_variant(
    *,
    entry: dict[str, Any],
    variant: str,
    file_title: str,
    imageinfo: dict[str, Any],
    target_dir: Path,
    refresh: bool,
) -> None:
    url = str(imageinfo.get("url") or "")
    if not url:
        return
    mime = str(imageinfo.get("mime") or "")
    ext = extension_from_url_or_mime(url, mime)
    target = target_dir / f"{variant}{ext}"
    info = download_asset(url, target, refresh=refresh)
    entry.setdefault("variants", {})[variant] = {
        "variant": variant,
        "file_title": file_title,
        "asset_url": url,
        "source_url": f"https://genshin-impact.fandom.com/wiki/{file_title.replace('File:', 'File:').replace(' ', '_')}",
        "mime": mime or info.get("content_type", "not_visible"),
        "width": imageinfo.get("width"),
        "height": imageinfo.get("height"),
        **info,
    }


def imageinfo_from_pageimage(page: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    pageimage = page.get("pageimage")
    original = page.get("original")
    if not pageimage or not isinstance(original, dict) or not original.get("source"):
        return None
    return f"File:{pageimage}", {
        "url": original["source"],
        "width": original.get("width"),
        "height": original.get("height"),
        "mime": "",
    }


def collect_characters(cache_root: Path, refresh: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    titles = category_members("Category:Playable Characters")
    for extra in EXTRA_CHARACTER_PAGES:
        if extra not in titles:
            titles.append(extra)
    pages = query_pages(titles)
    ko_aliases = query_korean_aliases(titles)
    icon_infos = file_imageinfo([f"File:{title} Icon.png" for title in titles])

    assets: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for title in sorted(titles):
        page = pages.get(title, {})
        aliases = sorted(set([title, normalize(title)] + ko_aliases.get(title, [])))
        entry = {
            "id": f"character:{slugify(title)}",
            "kind": "character",
            "name": title,
            "slug": slugify(title),
            "aliases": aliases,
            "tags": tags_for_character(page.get("categories")),
            "source_page": f"https://genshin-impact.fandom.com/wiki/{title.replace(' ', '_')}",
            "variants": {},
        }
        target_dir = cache_root / "images" / "characters" / entry["slug"]
        page_image = imageinfo_from_pageimage(page)
        if page_image:
            add_variant(entry=entry, variant="card", file_title=page_image[0], imageinfo=page_image[1], target_dir=target_dir, refresh=refresh)
        icon_title = f"File:{title} Icon.png"
        if icon_title in icon_infos:
            add_variant(entry=entry, variant="icon", file_title=icon_title, imageinfo=icon_infos[icon_title], target_dir=target_dir, refresh=refresh)
        if not entry["variants"]:
            errors.append({"kind": "character", "name": title, "error": "no image variants found"})
        else:
            assets.append(entry)
    return assets, errors


def collect_weapons(cache_root: Path, refresh: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    titles = [title for title in category_members("Category:Weapons") if title not in SKIP_WEAPON_TITLES]
    pages = query_pages(titles)
    ko_aliases = query_korean_aliases(titles)

    assets: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for title in sorted(titles):
        page = pages.get(title, {})
        aliases = sorted(set([title, normalize(title)] + ko_aliases.get(title, [])))
        entry = {
            "id": f"weapon:{slugify(title)}",
            "kind": "weapon",
            "name": title,
            "slug": slugify(title),
            "aliases": aliases,
            "tags": tags_for_weapon(page.get("categories")),
            "source_page": f"https://genshin-impact.fandom.com/wiki/{title.replace(' ', '_')}",
            "variants": {},
        }
        target_dir = cache_root / "images" / "weapons" / entry["slug"]
        page_image = imageinfo_from_pageimage(page)
        if page_image:
            add_variant(entry=entry, variant="icon", file_title=page_image[0], imageinfo=page_image[1], target_dir=target_dir, refresh=refresh)
        if not entry["variants"]:
            errors.append({"kind": "weapon", "name": title, "error": "no image variants found"})
        else:
            assets.append(entry)
    return assets, errors


def fallback_artifact_images(set_page_title: str) -> list[str]:
    pages = query_pages([set_page_title], props="images")
    page = pages.get(set_page_title, {})
    result = []
    for item in page.get("images", []) or []:
        title = str(item.get("title") or "")
        if not title.startswith("File:Item "):
            continue
        if "Strongbox" in title or "Inventory" in title:
            continue
        result.append(title.removeprefix("File:"))
    return result


def collect_artifacts(cache_root: Path, refresh: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    set_titles = category_members("Category:Artifact Sets")
    set_pages = query_pages(set_titles)
    set_ko_aliases = query_korean_aliases(set_titles)
    assets: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for set_title in sorted(set_titles):
        piece_titles = category_members(f"Category:{set_title} Artifacts")
        if not piece_titles:
            piece_titles = fallback_artifact_images(set_title)
        piece_pages = query_pages(piece_titles) if piece_titles else {}
        piece_ko_aliases = query_korean_aliases(piece_titles) if piece_titles else {}
        for piece_title in sorted(piece_titles):
            piece_page = piece_pages.get(piece_title, {})
            aliases = sorted(set([piece_title, set_title, normalize(piece_title), normalize(set_title)] + set_ko_aliases.get(set_title, []) + piece_ko_aliases.get(piece_title, [])))
            entry = {
                "id": f"artifact:{slugify(set_title)}:{slugify(piece_title)}",
                "kind": "artifact",
                "name": piece_title,
                "set_name": set_title,
                "slug": slugify(piece_title),
                "set_slug": slugify(set_title),
                "aliases": aliases,
                "tags": tags_for_artifact_piece(piece_page, set_title),
                "source_page": f"https://genshin-impact.fandom.com/wiki/{piece_title.replace(' ', '_')}",
                "set_source_page": f"https://genshin-impact.fandom.com/wiki/{set_title.replace(' ', '_')}",
                "variants": {},
            }
            target_dir = cache_root / "images" / "artifacts" / entry["set_slug"] / entry["slug"]
            page_image = imageinfo_from_pageimage(piece_page)
            if page_image:
                add_variant(entry=entry, variant="icon", file_title=page_image[0], imageinfo=page_image[1], target_dir=target_dir, refresh=refresh)
            if not entry["variants"]:
                errors.append({"kind": "artifact", "set": set_title, "name": piece_title, "error": "no image variants found"})
            else:
                assets.append(entry)

        # Add the set page as a separate representative asset when pageimage exists.
        set_page = set_pages.get(set_title, {})
        page_image = imageinfo_from_pageimage(set_page)
        if page_image:
            entry = {
                "id": f"artifact-set:{slugify(set_title)}",
                "kind": "artifact_set",
                "name": set_title,
                "set_name": set_title,
                "slug": slugify(set_title),
                "set_slug": slugify(set_title),
                "aliases": sorted(set([set_title, normalize(set_title)] + set_ko_aliases.get(set_title, []))),
                "tags": sorted(set(["artifact", "artifact-set", f"set-{slugify(set_title)}"] + category_tags(set_page.get("categories")))),
                "source_page": f"https://genshin-impact.fandom.com/wiki/{set_title.replace(' ', '_')}",
                "variants": {},
            }
            add_variant(
                entry=entry,
                variant="icon",
                file_title=page_image[0],
                imageinfo=page_image[1],
                target_dir=cache_root / "images" / "artifact-sets" / entry["set_slug"],
                refresh=refresh,
            )
            assets.append(entry)
    return assets, errors


def build_lookup(assets: list[dict[str, Any]]) -> dict[str, list[str]]:
    lookup: dict[str, list[str]] = {}
    for asset in assets:
        keys = set(asset.get("aliases", []))
        keys.add(asset.get("name", ""))
        keys.add(asset.get("slug", ""))
        if asset.get("set_name"):
            keys.add(asset["set_name"])
            keys.add(asset.get("set_slug", ""))
        for key in keys:
            normalized = normalize(str(key))
            if normalized:
                lookup.setdefault(normalized, []).append(asset["id"])
    return {key: sorted(set(value)) for key, value in lookup.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Genshin character/weapon/artifact image cache")
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE_ROOT)
    parser.add_argument("--kinds", default="characters,weapons,artifacts", help="comma list: characters,weapons,artifacts")
    parser.add_argument("--refresh", action="store_true", help="redownload existing image files")
    parser.add_argument("--summary-only", action="store_true", help="do not download; print planned source counts")
    args = parser.parse_args()

    cache_root = args.cache_root
    cache_root.mkdir(parents=True, exist_ok=True)
    kinds = {part.strip().lower() for part in args.kinds.split(",") if part.strip()}

    all_assets: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    started = time.time()

    if "characters" in kinds:
        assets, errs = collect_characters(cache_root, args.refresh)
        all_assets.extend(assets)
        errors.extend(errs)
        print(f"characters: {len(assets)} assets, {len(errs)} errors")
    if "weapons" in kinds:
        assets, errs = collect_weapons(cache_root, args.refresh)
        all_assets.extend(assets)
        errors.extend(errs)
        print(f"weapons: {len(assets)} assets, {len(errs)} errors")
    if "artifacts" in kinds:
        assets, errs = collect_artifacts(cache_root, args.refresh)
        all_assets.extend(assets)
        errors.extend(errs)
        print(f"artifacts: {len(assets)} assets, {len(errs)} errors")

    if args.summary_only:
        return 0

    counts: dict[str, int] = {}
    for asset in all_assets:
        counts[asset["kind"]] = counts.get(asset["kind"], 0) + 1

    index = {
        "schema_version": "1.0",
        "built_at": now_iso(),
        "source": {
            "name": "Genshin Impact Fandom MediaWiki API",
            "api_url": API_URL,
            "usage_note": "Official in-game/wiki asset images cached locally for active consultation visuals.",
        },
        "cache_root": str(cache_root).replace("\\", "/"),
        "counts": counts,
        "asset_count": len(all_assets),
        "error_count": len(errors),
        "assets": all_assets,
        "lookup": build_lookup(all_assets),
        "errors": errors,
        "elapsed_seconds": round(time.time() - started, 2),
    }
    (cache_root / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    (cache_root / "errors.json").write_text(json.dumps(errors, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: wrote {cache_root / 'index.json'}")
    print(f"assets={len(all_assets)} errors={len(errors)} counts={counts}")
    return 0 if len(all_assets) else 1


if __name__ == "__main__":
    raise SystemExit(main())

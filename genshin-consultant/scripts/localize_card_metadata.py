#!/usr/bin/env python3
"""Localize Genshin visual-card metadata for Korean display.

The renderers should receive Korean display strings. Canonical English names are
still allowed in source ids, paths, URLs, and asset identifiers.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any


SKIP_KEYS = {
    "card_type",
    "id",
    "kind",
    "variant",
    "tags",
    "source_ids",
    "image_source_ids",
    "source_page",
    "source_url",
    "asset_url",
    "image_path",
    "icon_path",
    "card_path",
    "output_image_path",
    "generated_at",
    "theme_element",
    "element",
}

FALLBACK_KO_NAMES = {
    "Nicole": "니콜",
    "Varka": "바르카",
    "Prune": "프루네",
    "Durin": "꼬마 두린",
    "Columbina": "콜롬비나",
    "Clorinde": "클로린드",
    "Arlecchino": "아를레키노",
    "Kinich": "키니치",
    "Emilie": "에밀리",
    "Fischl": "피슬",
    "Chevreuse": "슈브르즈",
    "Skyward Atlas": "천공의 두루마리",
    "Starcaller's Watch": "별지기의 시선",
    "Memory of Dust": "속세의 자물쇠",
    "Oathsworn Eye": "맹세의 눈동자",
    "Favonius Codex": "페보니우스 비전",
    "Flowing Purity": "순수의 흐름",
    "Celestial Gift": "하늘의 은총",
    "Noblesse Oblige": "옛 왕실의 의식",
    "Gladiator's Finale": "검투사의 피날레",
    "A Day Carved From Rising Winds": "솟구치는 바람에 새겨진 날",
    "은은한 빛의 해연 백성": "맹세의 눈동자",
    "프룬": "프루네",
    "두린": "꼬마 두린",
}

TERM_MAP = {
    "Pyro": "불 원소",
    "Hydro": "물 원소",
    "Electro": "번개 원소",
    "Cryo": "얼음 원소",
    "Anemo": "바람 원소",
    "Geo": "바위 원소",
    "Dendro": "풀 원소",
    "Physical": "물리",
    "Celestial": "하늘의 은총",
}


def has_hangul(text: str) -> bool:
    return any("\uac00" <= ch <= "\ud7a3" for ch in text)


def strip_wiki_templates(text: str) -> str:
    """Turn simple wiki tt templates into readable Korean text."""
    previous = None
    value = text
    pattern = re.compile(r"\{\{tt\|([^|{}]+)\|[^{}]+\}\}")
    while previous != value:
        previous = value
        value = pattern.sub(r"\1", value)
    value = re.sub(r"\{\{[^{}]+\}\}", "", value)
    return value.strip()


def normalized_lookup_key(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z]+", "", text).casefold()


def best_hangul_alias(aliases: list[Any], *, prefer_first: bool = False) -> str | None:
    candidates = [strip_wiki_templates(str(alias)) for alias in aliases]
    candidates = [alias for alias in candidates if has_hangul(alias)]
    if not candidates:
        return None
    return candidates[0] if prefer_first else candidates[-1]


def load_asset_aliases(index_path: Path | None) -> dict[str, str]:
    mapping: dict[str, str] = {}
    if not index_path or not index_path.exists():
        return mapping
    try:
        index = json.loads(index_path.read_text(encoding="utf-8-sig"))
    except Exception:
        return mapping
    assets = index.get("assets") if isinstance(index, dict) else None
    if not isinstance(assets, list):
        return mapping

    for asset in assets:
        if not isinstance(asset, dict):
            continue
        aliases = asset.get("aliases")
        if not isinstance(aliases, list):
            aliases = []
        name = str(asset.get("name") or "")
        set_name = str(asset.get("set_name") or "")
        ko_name = best_hangul_alias(aliases)
        ko_set = best_hangul_alias(aliases, prefer_first=True)
        if name and ko_name:
            mapping[name] = ko_name
            key = normalized_lookup_key(name)
            if key:
                mapping[key] = ko_name
        if set_name and ko_set:
            mapping[set_name] = ko_set
            key = normalized_lookup_key(set_name)
            if key:
                mapping[key] = ko_set
    return mapping


def build_mapping(index_path: Path | None) -> dict[str, str]:
    mapping = load_asset_aliases(index_path)
    mapping.update(FALLBACK_KO_NAMES)
    for key, value in list(mapping.items()):
        normalized = normalized_lookup_key(key)
        if normalized:
            mapping[normalized] = value
    return mapping


def localize_string(value: str, mapping: dict[str, str]) -> str:
    if not value:
        return value
    normalized = normalized_lookup_key(value)
    exact = mapping.get(value) or (mapping.get(normalized) if normalized else None)
    if exact:
        return exact
    result = value
    replacements = dict(TERM_MAP)
    for key, mapped in FALLBACK_KO_NAMES.items():
        if re.search(r"[A-Za-z]", key):
            replacements[key] = mapped
    for english, korean in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        if english and english in result:
            result = result.replace(english, korean)
    return result


def localize_value(value: Any, mapping: dict[str, str], key: str | None = None) -> Any:
    if key in SKIP_KEYS:
        return value
    if isinstance(value, str):
        return localize_string(value, mapping)
    if isinstance(value, list):
        return [localize_value(item, mapping, key=None) for item in value]
    if isinstance(value, dict):
        return {k: localize_value(v, mapping, key=k) for k, v in value.items()}
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Localize Genshin card metadata into Korean display names")
    parser.add_argument("metadata_json", nargs="+", type=Path)
    default_asset_index = Path(os.environ.get("GENSHIN_ASSET_INDEX", str(Path(__file__).resolve().parents[1] / "assets" / "genshin-assets" / "current" / "index.json")))
    parser.add_argument("--asset-index", type=Path, default=default_asset_index)
    parser.add_argument("--in-place", action="store_true")
    parser.add_argument("--suffix", default="-ko", help="suffix for non in-place output files")
    args = parser.parse_args()

    mapping = build_mapping(args.asset_index)
    for path in args.metadata_json:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        localized = localize_value(data, mapping)
        output = path if args.in_place else path.with_name(path.stem + args.suffix + path.suffix)
        output.write_text(json.dumps(localized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"OK: localized {path} -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

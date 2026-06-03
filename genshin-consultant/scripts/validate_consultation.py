#!/usr/bin/env python3
"""Validate a genshin-consultant JSON artifact.

This is intentionally lightweight: it checks that another agent preserved the
required high-level structure, confidence labels, UX-grade consulting sections,
and visual artifact contract introduced in consultation_version 1.2.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ALLOWED_CONFIDENCE = {"confirmed", "inferred", "needs_confirmation"}
ALLOWED_SOURCE_TIERS = {"A", "B", "C"}
ALLOWED_WEAPON_RATINGS = {
    "best",
    "excellent",
    "good",
    "usable",
    "temporary",
    "not_recommended",
}
ALLOWED_TEAM_CATEGORIES = {
    "best_current",
    "stable_budget",
    "second_side_or_growth",
    "alternative",
}
ALLOWED_VISUAL_TYPES = {
    "weapon_top5_card",
    "artifact_showcase_card",
    "party_card",
    "build_card",
    "weapon_card",
    "artifact_card",
    "mechanics_card",
}
ALLOWED_DISPLAY_HINTS = {"markdown_inline", "path_only", "tool_view"}

REQUIRED_TOP_LEVEL = {
    "consultation_version",
    "analyzed_at",
    "input_images",
    "character",
    "weapon",
    "talents",
    "stats",
    "artifacts",
    "build_targets",
    "artifact_plan",
    "weapon_rankings",
    "mechanics_checklist",
    "resource_plan",
    "team_recommendations",
    "visual_artifacts",
    "source_pack",
    "uncertainties",
}

REQUIRED_OBJECTS = {
    "character",
    "weapon",
    "talents",
    "stats",
    "build_targets",
    "artifact_plan",
    "resource_plan",
}

REQUIRED_LISTS = {
    "input_images",
    "artifacts",
    "weapon_rankings",
    "mechanics_checklist",
    "team_recommendations",
    "visual_artifacts",
    "source_pack",
    "uncertainties",
}


def iter_confidence_values(obj: Any, path: str = "$"):
    if isinstance(obj, dict):
        for key, value in obj.items():
            next_path = f"{path}.{key}"
            if key == "confidence":
                yield next_path, value
            else:
                yield from iter_confidence_values(value, next_path)
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            yield from iter_confidence_values(value, f"{path}[{idx}]")


def require_non_empty_string(obj: dict[str, Any], key: str, path: str) -> list[str]:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        return [f"{path}.{key} must be a non-empty string"]
    return []


def require_list_if_present(obj: dict[str, Any], key: str, path: str) -> list[str]:
    if key in obj and not isinstance(obj.get(key), list):
        return [f"{path}.{key} must be a list when present"]
    return []


def validate_source_pack(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    source_pack = data.get("source_pack")
    if not isinstance(source_pack, list):
        return errors
    seen_ids: set[str] = set()
    for idx, source in enumerate(source_pack):
        path = f"source_pack[{idx}]"
        if not isinstance(source, dict):
            errors.append(f"{path} must be an object")
            continue
        source_id = source.get("id")
        if not isinstance(source_id, str) or not source_id.strip():
            errors.append(f"{path}.id must be a non-empty string")
        elif source_id in seen_ids:
            errors.append(f"{path}.id is duplicated: {source_id!r}")
        else:
            seen_ids.add(source_id)
        tier = source.get("tier")
        if tier not in ALLOWED_SOURCE_TIERS:
            errors.append(f"{path}.tier must be one of {sorted(ALLOWED_SOURCE_TIERS)}")
    return errors


def validate_weapon_rankings(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rows = data.get("weapon_rankings")
    if not isinstance(rows, list):
        return errors
    for idx, row in enumerate(rows):
        path = f"weapon_rankings[{idx}]"
        if not isinstance(row, dict):
            errors.append(f"{path} must be an object")
            continue
        if row.get("rating") not in ALLOWED_WEAPON_RATINGS:
            errors.append(f"{path}.rating must be one of {sorted(ALLOWED_WEAPON_RATINGS)}")
        if "refinement" not in row:
            errors.append(f"{path}.refinement is required")
    return errors


def validate_team_recommendations(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rows = data.get("team_recommendations")
    if not isinstance(rows, list):
        return errors
    for idx, row in enumerate(rows):
        path = f"team_recommendations[{idx}]"
        if not isinstance(row, dict):
            errors.append(f"{path} must be an object")
            continue
        category = row.get("category")
        if category not in ALLOWED_TEAM_CATEGORIES:
            errors.append(f"{path}.category must be one of {sorted(ALLOWED_TEAM_CATEGORIES)}")
        members = row.get("members")
        if members is not None and not isinstance(members, list):
            errors.append(f"{path}.members must be a list when present")
    return errors


def validate_visual_artifacts(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rows = data.get("visual_artifacts")
    if not isinstance(rows, list):
        return errors

    for idx, row in enumerate(rows):
        path = f"visual_artifacts[{idx}]"
        if not isinstance(row, dict):
            errors.append(f"{path} must be an object")
            continue

        visual_type = row.get("type")
        if visual_type not in ALLOWED_VISUAL_TYPES:
            errors.append(f"{path}.type must be one of {sorted(ALLOWED_VISUAL_TYPES)}")

        errors.extend(require_non_empty_string(row, "path", path))
        errors.extend(require_non_empty_string(row, "metadata_path", path))
        errors.extend(require_list_if_present(row, "source_ids", path))
        errors.extend(require_list_if_present(row, "image_source_ids", path))

        display_hint = row.get("display_hint")
        if display_hint is not None and display_hint not in ALLOWED_DISPLAY_HINTS:
            errors.append(f"{path}.display_hint must be one of {sorted(ALLOWED_DISPLAY_HINTS)} when present")

    return errors


def validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_TOP_LEVEL - set(data))
    if missing:
        errors.append(f"missing top-level keys: {', '.join(missing)}")

    for key in sorted(REQUIRED_OBJECTS):
        if key in data and not isinstance(data.get(key), dict):
            errors.append(f"{key} must be an object")

    for key in sorted(REQUIRED_LISTS):
        if key in data and not isinstance(data.get(key), list):
            errors.append(f"{key} must be a list")

    for path, value in iter_confidence_values(data):
        if value not in ALLOWED_CONFIDENCE:
            errors.append(f"invalid confidence at {path}: {value!r}")

    errors.extend(validate_source_pack(data))
    errors.extend(validate_weapon_rankings(data))
    errors.extend(validate_team_recommendations(data))
    errors.extend(validate_visual_artifacts(data))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_path", type=Path)
    args = parser.parse_args()

    try:
        data = json.loads(args.json_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: cannot read JSON: {exc}", file=sys.stderr)
        return 2

    if not isinstance(data, dict):
        print("ERROR: root must be an object", file=sys.stderr)
        return 2

    errors = validate(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("OK: consultation JSON structure is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

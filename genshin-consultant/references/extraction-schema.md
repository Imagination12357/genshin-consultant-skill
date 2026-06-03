# Extraction Schema

Use this reference when extracting Genshin Impact screenshots or producing machine-readable consultation artifacts. Never fill a field with a guessed value. Use `null` plus `needs_confirmation` when unreadable.

## Confidence labels

- `confirmed` — directly readable from an image or user-provided text.
- `inferred` — not directly shown, but strongly derived from visible evidence; explain why.
- `needs_confirmation` — unreadable, cropped, missing, ambiguous, or dependent on another screen.

## Required JSON shape

```json
{
  "consultation_version": "1.3",
  "analyzed_at": "ISO-8601 timestamp",
  "game_version_context": "visible version or current searched version",
  "input_images": [
    {
      "path_or_label": "string",
      "screen_type": "character-profile|details-1|details-2|weapon|weapon-inventory|artifact|talent|constellation|roster|unknown",
      "display_role": "character|weapon|artifact|artifact-flower|artifact-plume|artifact-sands|artifact-goblet|artifact-circlet|details|roster|unknown",
      "display_path": "absolute concrete path used in Markdown image tag or null",
      "render_status": "rendered|path_only|not_renderable|not_applicable",
      "quality_notes": "string"
    }
  ],
  "character": {
    "name": {"value": "string|null", "confidence": "confirmed|inferred|needs_confirmation"},
    "element": {"value": "string|null", "confidence": "confirmed|inferred|needs_confirmation"},
    "level": {"value": "number|null", "confidence": "confirmed|inferred|needs_confirmation"},
    "ascension_phase": {"value": "string|null", "confidence": "confirmed|inferred|needs_confirmation"},
    "constellation": {"value": "C0-C6|null", "confidence": "confirmed|inferred|needs_confirmation"},
    "role_hypothesis": {"value": "string|null", "confidence": "confirmed|inferred|needs_confirmation", "basis": "string"}
  },
  "weapon": {
    "name": {"value": "string|null", "confidence": "confirmed|inferred|needs_confirmation"},
    "level": {"value": "number|null", "confidence": "confirmed|inferred|needs_confirmation"},
    "refinement": {"value": "R1-R5|null", "confidence": "confirmed|inferred|needs_confirmation"},
    "notes": "string"
  },
  "talents": {
    "normal_attack": {"value": "number|null", "confidence": "confirmed|inferred|needs_confirmation"},
    "elemental_skill": {"value": "number|null", "confidence": "confirmed|inferred|needs_confirmation"},
    "elemental_burst": {"value": "number|null", "confidence": "confirmed|inferred|needs_confirmation"}
  },
  "stats": {
    "max_hp": {"value": "number|null", "confidence": "confirmed|inferred|needs_confirmation"},
    "atk": {"value": "number|null", "confidence": "confirmed|inferred|needs_confirmation"},
    "def": {"value": "number|null", "confidence": "confirmed|inferred|needs_confirmation"},
    "elemental_mastery": {"value": "number|null", "confidence": "confirmed|inferred|needs_confirmation"},
    "crit_rate_percent": {"value": "number|null", "confidence": "confirmed|inferred|needs_confirmation"},
    "crit_dmg_percent": {"value": "number|null", "confidence": "confirmed|inferred|needs_confirmation"},
    "energy_recharge_percent": {"value": "number|null", "confidence": "confirmed|inferred|needs_confirmation"},
    "damage_bonus_percent": {"value": "number|null", "type": "elemental|physical|null", "confidence": "confirmed|inferred|needs_confirmation"}
  },
  "artifacts": [
    {
      "slot": "flower|plume|sands|goblet|circlet",
      "set_name": {"value": "string|null", "confidence": "confirmed|inferred|needs_confirmation"},
      "level": {"value": "number|null", "confidence": "confirmed|inferred|needs_confirmation"},
      "main_stat": {"stat": "string|null", "value": "number|string|null", "confidence": "confirmed|inferred|needs_confirmation"},
      "substats": [
        {"stat": "string", "value": "number|string|null", "confidence": "confirmed|inferred|needs_confirmation"}
      ],
      "notes": "string"
    }
  ],
  "build_targets": {
    "role": "string",
    "target_stats": [
      {
        "stat": "crit_rate|crit_dmg|energy_recharge|elemental_mastery|hp|atk|def|damage_bonus|other",
        "minimum_usable": "string|null",
        "stable": "string|null",
        "near_endgame": "string|null",
        "endgame": "string|null",
        "conditions": "team/weapon/set assumptions",
        "confidence": "confirmed|inferred|needs_confirmation",
        "source_ids": ["string"]
      }
    ]
  },
  "artifact_plan": {
    "best_sets": ["string"],
    "substitute_sets": ["string"],
    "temporary_sets": ["string"],
    "main_stats": {"sands": "string|null", "goblet": "string|null", "circlet": "string|null"},
    "substat_priority": ["string"],
    "minimum_requirements": ["string"],
    "stop_farming_point": "string"
  },
  "weapon_rankings": [
    {
      "rank": 1,
      "weapon": "string",
      "refinement": "R1|R2|R3|R4|R5|range",
      "rating": "best|excellent|good|usable|temporary|not_recommended",
      "owned": true,
      "reason": "string",
      "requirements_or_caveats": "string",
      "source_ids": ["string"]
    }
  ],
  "mechanics_checklist": [
    {
      "mechanic": "string",
      "what_to_do": "string",
      "common_mistake": "string",
      "how_to_verify": "string",
      "confidence": "confirmed|inferred|needs_confirmation",
      "source_ids": ["string"]
    }
  ],
  "resource_plan": {
    "character_level_target": "string",
    "weapon_level_target": "string",
    "talent_targets": {"normal_attack": "string", "elemental_skill": "string", "elemental_burst": "string"},
    "weekly_or_boss_material_notes": ["string"],
    "resin_priorities": ["string"]
  },
  "team_recommendations": [
    {
      "category": "best_current|stable_budget|second_side_or_growth|alternative",
      "members": ["string"],
      "roles": ["string"],
      "why_it_works": "string",
      "rotation_sketch": "string",
      "minimum_conditions": ["string"],
      "replacements_or_future_upgrades": ["string"],
      "source_ids": ["string"]
    }
  ],
  "visual_artifacts": [
    {
      "type": "weapon_top5_card|artifact_showcase_card|party_card|build_card|weapon_card|artifact_card|mechanics_card",
      "path": "generated/visuals/example.png",
      "metadata_path": "generated/visuals/example.json",
      "display_hint": "markdown_inline|path_only|tool_view",
      "alt_text": "string",
      "source_ids": ["string"],
      "image_source_ids": ["string"]
    }
  ],
  "source_pack": [
    {
      "id": "string",
      "title": "string",
      "url": "string",
      "tier": "A|B|C",
      "date_or_version": "string|null",
      "supports": "string"
    }
  ],
  "uncertainties": [
    {"field": "string", "reason": "string", "needed_input": "string"}
  ]
}
```

## Extraction rules

- Preserve exact visible numbers, including percent signs.
- Normalize common Korean stat names: 치명타 확률→CRIT Rate, 치명타 피해→CRIT DMG, 원소 충전 효율→Energy Recharge, 원소 마스터리→Elemental Mastery.
- Do not compute artifact roll quality unless all substats and levels are visible.
- If only total stats are visible, do not infer exact artifact substats.
- If a character name is inferred from portrait, mark `inferred` unless the name text is visible.
- For source-backed target stats, weapon ranking, materials, or mechanics, use `source_ids` to connect advice to `source_pack`.

## Input image display rules

- Record every supplied attached image or local image path in `input_images[]`.
- Use `display_role` to separate character, weapon, artifact slot, details, roster, and unknown images.
- Use `display_path` for the exact absolute path placed inside Markdown image syntax. Prefer privacy-safe aliases such as `/absolute/path/to/...` when they resolve to the same file.
- Use `render_status: rendered` only when the final answer embeds a Markdown image for that file. Use `path_only` if the path is listed but not embedded, `not_renderable` if the surface cannot display it, and `not_applicable` for non-image inputs.
- Do not add original user screenshots to `visual_artifacts[]`; that array is for generated PNG cards and their metadata.

## Visual artifact rules

- Add `visual_artifacts[]` whenever the consultation generates or links a local PNG card.
- Allowed visual artifact types: `weapon_top5_card`, `artifact_showcase_card`, `party_card`, `build_card`, `weapon_card`, `artifact_card`, `mechanics_card`.
- `path` must point to the generated PNG card.
- `metadata_path` must point to the paired card metadata JSON.
- `source_ids` connects the card's build/team/stat claims to `source_pack`.
- `image_source_ids` connects any portrait/icon/image assets to the image metadata recorded under the source policy.
- Card metadata should store downloaded official/wiki asset paths as `characters[].image_path` for party cards and `items[].image_path` for weapon/artifact/showcase cards.
- Use `display_hint: markdown_inline` when the surface can render `![alt](path)`, `tool_view` when an image-viewing tool was used, and `path_only` when visual display is unavailable.
- If no safe official/wiki image is found, use a placeholder card and keep `image_source_ids` empty with an uncertainty note.
- Add `weapon_top5_card` whenever the consultation includes weapon recommendations.
- Add `artifact_showcase_card` whenever the consultation includes artifact set recommendations.

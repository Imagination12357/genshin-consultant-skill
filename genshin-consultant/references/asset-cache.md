# Genshin Asset Cache

Use this reference when generating visual cards or when adding lightweight inline images to a text consultation from cached character, weapon, or artifact images.

## Default Asset Store

- Canonical skill root: `/absolute/path/to/genshin_agent/genshin-consultant`
- Physical asset store: `/absolute/path/to/genshin_agent/genshin-consultant/assets/genshin-assets/current`
- Installed Codex skill path: `~/.codex/skills/genshin-consultant` should be a junction to the canonical skill root.
- Index: `/absolute/path/to/genshin_agent/genshin-consultant/assets/genshin-assets/current/index.json`
- Source: Genshin Impact Fandom MediaWiki API, using official in-game/wiki asset images.
- Cached kinds:
  - `character`: card and icon variants when available.
  - `weapon`: icon variants.
  - `artifact`: individual artifact piece icons.
  - `artifact_set`: representative set icons when page images exist.
- Optimized storage uses WebP for most source images: character card art, weapon icons, artifact piece icons, and artifact-set previews. A few tiny PNG sources may remain PNG when WebP is larger.
- Artifact-set previews may be animated WebP. Frame reduction preserves total animation duration and canvas dimensions.
- Generated thumbnail files under `thumbnails/` intentionally remain PNG. `query_asset_cache.py --thumb-size` emits those PNG thumbnails for compact Markdown tables, rich text answers, and report metadata.
- Korean aliases are extracted from wiki `ko` / `1_ko` fields when visible, so common Korean queries such as `유라`, `라이덴`, `예초`, `창백`, and `절연` should resolve without manual relabeling.

## Required lookup workflow

Before doing per-answer image web fetching:

1. Query the local cache with `scripts/query_asset_cache.py`.
2. Use the returned `image_path` in `characters[].image_path` or `items[].image_path`.
3. Only call `scripts/fetch_card_assets.py` if the cache has no suitable match.
4. If a new official/wiki asset is fetched during a consultation, add it to the cache or record it as a one-off image gap.

## Lightweight inline usage

Use this mode for normal rich text consultations when the user did not request a full image report.

- Query only after the text recommendation list is known.
- Limit lookups to the main character plus the final visible recommendations, usually 6-8 items maximum.
- Use only cached thumbnail paths returned by `query_asset_cache.py --thumb-size 48`; do not call `fetch_card_assets.py`.
- Do not create metadata JSON, PNG cards, or composed pages.
- If a cache lookup misses, omit the image and continue with text.
- Use Markdown image tags with generated thumbnail paths. Codex desktop prints HTML `<img>` tags as literal text, so never use HTML for inline rich text:
  `![벤티](/absolute/path/to/genshin_agent/genshin-consultant/assets/genshin-assets/current/thumbnails/48/images/characters/venti/icon.png)`.
- Attach each icon to the relevant recommendation item. Do not emit several standalone raw Markdown image lines in a vertical stack.
- Party rows may use a horizontal 4-column image table. Artifact sets may use a horizontal 5-piece image table. Weapon recommendations should use one icon beside each weapon name.

## Character variant usage

- Party composition cards use `--variant icon` and write the returned path to `characters[].icon_path`.
- Single-character build/endgame report cards use `--variant card` and write the returned path to `character.card_path` or top-level `card_path`.
- Do not use large `card` art for four-person party rows; it makes the card crowded and slow to scan.
- Do not use small `icon` art as the main image in a single-character report when a `card` variant exists.
- Rich text consultations normally use `icon` for characters, weapons, and party rows. Use `card` only when the user asks to inspect a single character visually but does not need a rendered report.

Example character lookup:

```powershell
$env:PYTHONUTF8='1'
python "$env:USERPROFILE\.codex\skills\genshin-consultant\scripts\query_asset_cache.py" Nicole Durin --kind character --variant icon --limit 1 --thumb-size 48
```

Example artifact set lookup:

```powershell
$env:PYTHONUTF8='1'
python "$env:USERPROFILE\.codex\skills\genshin-consultant\scripts\query_asset_cache.py" "Pale Flame" --kind artifact --limit 5 --format manifest-items --thumb-size 48
```

For artifact set cards, preserve slot order:

1. Flower of Life
2. Plume of Death
3. Sands of Eon
4. Goblet of Eonothem
5. Circlet of Logos

`query_asset_cache.py` sorts artifact pieces in this slot order.

## Rebuild workflow

Use this when the game updates, new characters are released, or the user asks to refresh the image pack:

```powershell
$env:PYTHONUTF8='1'
python "$env:USERPROFILE\.codex\skills\genshin-consultant\scripts\build_asset_cache.py" --kinds characters,weapons,artifacts
```

Use `--refresh` only when existing files are stale or corrupted.
After a full rebuild, run `scripts/optimize_asset_cache.py --include-weapons --include-artifacts --artifact-frame-step 2 --apply` to restore the optimized WebP layout before committing the cache.

## Output contract

Every cached match returns fields suitable for card metadata:

```json
{
  "id": "character:nicole",
  "kind": "character",
  "name": "Nicole",
  "variant": "card",
  "image_path": "/absolute/path/to/genshin_agent/genshin-consultant/assets/genshin-assets/current/images/characters/nicole/card.webp",
  "image_source_id": "character:nicole",
  "source_page": "https://genshin-impact.fandom.com/wiki/Nicole",
  "asset_url": "https://static.wikia.nocookie.net/..."
}
```

Use `image_source_id` as the visual card metadata source identifier. Keep `source_page` and `asset_url` in notes or metadata when citing image provenance.

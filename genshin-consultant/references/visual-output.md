# Visual Output Policy

Use this reference only when image report mode is explicitly triggered or when the user directly asks for a local visual card: party composition, build summary, weapon ranking, artifact options, target stats, or mechanics/rotation checklist. Ordinary text consultations must not load this file or generate PNGs.

## Report mode

- Default report visual format: **local PNG card** with a paired metadata JSON file.
- Default output root: `generated/visuals/` under the `genshin-consultant` skill/project directory.
- Alternative output root when the consultation is an OMX workflow: `.omx/artifacts/genshin-consultant/visuals/`.
- Do not overwrite a PNG path that has already been displayed in the current Codex conversation. The app may cache local image paths; use a unique suffix such as `-utf8-v3`, timestamp, or content hash for regenerated cards.
- Do not store user account screenshots as reusable assets. Generated cards are consultation artifacts only.
- If local rendering is not available in report mode, still create metadata JSON and provide a compact Markdown/table fallback.
- Party/team recommendation requests generate `party_card` or `party_list_card` only in report mode.
- When the user asks for several parties, best teams, or a ranked party list in report mode, generate a `party_list_card` with up to five 4-character teams using `scripts/render_party_list_card.py`. If the user asks for "best 3" use three teams; if they ask for "5" or "추천 리스트" use five.
- Weapon recommendation requests generate `weapon_top5_card` only in report mode.
- Artifact recommendation requests generate `artifact_showcase_card` only in report mode.
- When two or more cards are generated for a single consultation, compose the rendered card PNGs into one final `visual_page` PNG with `scripts/compose_visual_page.py` and display that page first. Individual card PNGs are supporting artifacts.
- Do not print source footers inside generated PNGs. Keep source citations in the text answer, not at the bottom of each visual layer.
- Multi-card pages must use consistent outer-card alignment: set `fit_width: true` in `visual_page` metadata or render every card at the same width. Section labels must have their own vertical space and must not overlap the card border.
- If the build card already states constellation or ownership context such as `C0 기준`, do not repeat that same context in weapon, artifact, or party subtitles.
- Do not use repeating horizontal stripe backgrounds in final card/page renders. Subtle panels, gradients, borders, and accent bars are acceptable; white grid/stripe lines behind layers are not.
- Report-mode cards are still allowed when some icons are missing; use placeholders for missing images and list the missing image sources.
- When generating metadata or card scripts from PowerShell on Windows, force UTF-8 before piping Korean text into Python:
  `$OutputEncoding = [System.Text.UTF8Encoding]::new($false); [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); [Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false); $env:PYTHONUTF8='1'`.
- Do not render a card if Korean text has already become `???`, replacement characters, or mojibake-style mixed `?` + non-ASCII text in metadata. Regenerate the metadata from clean UTF-8 input first.
- Do not render from English display-name metadata. Run `scripts/localize_card_metadata.py` before rendering so visible character, weapon, artifact, set, role, and element names are Korean where aliases exist.

## Official/wiki image asset workflow

When report mode uses web research for card images, cards must use real official/wiki images whenever available. Query the local asset cache before downloading anything.

Required sequence:

1. Load `references/asset-cache.md`.
2. Run `scripts/query_asset_cache.py` for every character/weapon/artifact shown in a card.
3. Use cached `image_path` values in card metadata when available.
4. During web search, collect page URLs only for cache misses. Prefer official HoYoverse/HoYoLAB pages, then Fandom/wiki pages.
5. Build a small asset manifest with one entry per missing card image.
6. Run `scripts/fetch_card_assets.py` to download direct `asset_url`s or discover `og:image` / `twitter:image` from the source page.
7. Use the downloaded `local_path` as `image_path` in card metadata.
8. Render the card. Do not use a placeholder for an item if a safe cached or official/wiki `image_path` exists.

Asset manifest example:

```json
{
  "output_root": "/absolute/path/to/genshin_agent/generated/visuals/assets",
  "assets": [
    {
      "id": "img-columbina",
      "name": "콜롬비나",
      "kind": "character",
      "source_url": "https://genshin-impact.fandom.com/wiki/Columbina",
      "asset_url": null,
      "filename": "columbina.png"
    }
  ]
}
```

The fetched manifest contains `local_path`. Copy that path into:

- `characters[].image_path` for party cards.
- `items[].image_path` for weapon/artifact/showcase cards.

If `fetch_card_assets.py` cannot discover an image from an official page because the site is dynamic, retry with the relevant Fandom/wiki page before using a placeholder. Record the failed source in metadata or notes.

## Original input image preview mode

When the user supplies character, weapon, or artifact screenshots, show the original images in the Codex response before detailed diagnosis. This is separate from generated cards.

Required preview groups:

- `캐릭터 이미지` — character profile, character info, or details screenshot.
- `무기 이미지` — weapon detail or weapon inventory image. If the user only names the weapon in text, show `무기 이미지: 제공 없음`.
- `성유물 이미지` — individual artifact screenshots when available. If artifacts are not individually visible, show the supplied details screenshot and state which artifact slots still need images.

Markdown rendering rules:

- Use `![alt](absolute/path.png)` for every local image that should render inline.
- The path inside the image URL must be a concrete absolute filesystem path, not `~`, `$env:USERPROFILE`, or another shell expression.
- Prefer privacy-safe absolute aliases such as `/absolute/path/to/genshin_agent/...` when they resolve to the same file. If no alias exists, use the real absolute path only inside the Markdown image URL and use redacted paths in surrounding prose.
- Use forward slashes in Markdown image URLs for Windows paths when possible, e.g. `/absolute/path/to/genshin_agent/캐릭터/캐릭터 정보.png`.
- If the current surface cannot render Markdown images, list the concrete display path and say `렌더링 확인 필요`.

Recommended layout:

```markdown
**입력 이미지 미리보기**

캐릭터 이미지
![캐릭터 이미지](/absolute/path/to/genshin_agent/캐릭터/캐릭터 정보.png)

무기 이미지
무기 이미지: 제공 없음

성유물 이미지
| 꽃 | 깃털 | 시계 | 성배 | 왕관 |
|---|---|---|---|---|
| ![꽃](/absolute/path/to/.../flower.png) | ![깃털](/absolute/path/to/.../plume.png) | ![시계](/absolute/path/to/.../sands.png) | ![성배](/absolute/path/to/.../goblet.png) | ![왕관](/absolute/path/to/.../circlet.png) |
```

If the user supplies only mixed screenshots rather than five artifact detail images, use a compact labeled gallery instead of pretending slot-level artifact images exist.

## Supported card types

For `party_card`, `party_list_card`, and `build_card`, also load `references/report-design.md`. That file defines the Enka-inspired but original report layout, the `card` vs `icon` asset rules, the element-theme metadata contract, and when to use the HTML report renderer.

### `visual_page` (report mode, when multiple cards exist)

Purpose: stitch the generated build, weapon, artifact, party, and mechanics cards into one scrollable page image for Codex display.

Renderer: `scripts/compose_visual_page.py`.

Required content:

- `title` and optional `subtitle`
- `theme_element`
- `cards[]` with rendered PNG `image_path` entries in desired display order
- `output_image_path`
- `fit_width: true` unless every card image has already been rendered to the same width

Layout rule:

```text
[ build/card summary ]
[ weapon ranking ]
[ artifact recommendation ]
[ party recommendation ]
```

Run this after all individual cards are rendered. The final answer should embed the composed page first.

### `weapon_top5_card` (report mode for weapon advice)

Purpose: show the top 5 recommended weapons as a visual row with icons, not just a text table.

Visual style: use the same dark HUD theme as `build_card`; do not render final cards as plain white grids.

Required content:

- card title, e.g. `콜롬비나 추천 무기 TOP 5`
- up to five ranked weapon items in one horizontal row
- each item: rank, weapon name, icon or placeholder, rating/role label, one-line reason
- source IDs and image source IDs for build claims and icon provenance

Layout rule:

```text
[ #1 weapon ][ #2 weapon ][ #3 weapon ][ #4 weapon ][ #5 weapon ]
```

If the answer includes a longer weapon table, still put this image card before the table.

### `artifact_showcase_card` (report mode for artifact advice)

Purpose: show the recommended artifact set visually, including five set pieces or representative set icons.

Visual style: use the same dark HUD theme as `build_card`; show main option and substat priority, not detailed fake roll values.

Required content:

- card title, e.g. `콜롬비나 추천 성유물`
- one-line summary at the top: `한줄 요약: ...`
- primary set name and recommendation rating
- five artifact pieces in one row when set-piece icons are available; otherwise set icon(s) or placeholders
- main stat line: sands/goblet/circlet
- source IDs and image source IDs
- Use full Korean artifact slot names in visible text: `생명의 꽃`, `죽음의 깃털`, `시간의 모래`, `공간의 성배`, `이성의 왕관`. Do not abbreviate these to `꽃`, `깃털`, `시계`, `성배`, `왕관` in final visuals.

Layout rule:

```text
[ flower ][ plume ][ sands ][ goblet ][ circlet ]
```

If several sets are valid, create either one `artifact_showcase_card` for the best default set plus text alternatives, or a second showcase card for the most important alternative when the choice is team-dependent.

### `party_card`

Purpose: show a 4-person party in one horizontal row.

Preferred renderer: `scripts/render_html_report.py --width 1600 --height 720` for primary party recommendations. Use `scripts/render_visual_card.py` only as a compact fallback.

Required content:

- team title, e.g. `라이덴 국대`, `라이덴 하이퍼`, `뉴비 안정 파티`
- exactly four character slots in order of intended usage or rotation priority
- each slot must prefer `icon_path` from the local asset cache; `image_path` is only a fallback
- character name, role, element/reaction contribution if known
- one-line core mechanic/reaction explanation
- short rotation sketch
- source IDs and image source IDs

Layout rule:

```text
[ Character 1 ][ Character 2 ][ Character 3 ][ Character 4 ]
```

Use rounded rectangular icon slots, not circular portraits. Theme the card from `theme_element`; if omitted, theme from `characters[0].element`. Use placeholder blocks if safe official/wiki images are unavailable.

### `party_list_card`

Purpose: show several ranked party recommendations in one visual card.

Renderer: `scripts/render_party_list_card.py`.

Required content:

- card title, e.g. `콜롬비나 추천 파티 BEST 5`
- `teams[]` containing 3-5 entries, each with `rank`, `name`, `reaction`, `note`, optional `rotation`, and exactly four `characters[]`
- each character must use cached `icon_path` when available
- source IDs and image source IDs

Use this instead of separate one-team cards when the user asks for a ranked list or when a composed page needs one compact party section.

### `build_card`

Purpose: summarize one character's current state and target build.

Preferred renderer: `scripts/render_html_report.py`. This should be the default for a serious single-character build/endgame/spec report because it can place character art, weapon, artifacts, and stats in one designed screen.

Recommended content:

- character name / role / constellation / weapon
- `character.card_path` or top-level `card_path` for the large left-side character art
- `weapon.image_path` for the selected/current weapon image
- five `artifacts[].image_path` or `artifact.pieces[].image_path` entries for artifact piece images when available
- target stat tiers: minimum usable, stable, near-endgame, endgame
- CR/CD/ER/EM or HP/ATK/DEF/scaling-stat targets
- artifact main stats and substat priorities
- first fix: the single highest-impact action
- `weapon`, `artifact`, `target_stats`, and `sections[]` for the right-side report panels

### `weapon_card`

Purpose: show refinement-aware weapon ranking.

Recommended content:

- ranking rows split by refinement when order changes
- owned vs unowned marker
- rating: `best`, `excellent`, `good`, `usable`, `temporary`, `not_recommended`
- caveat: ER requirement, team lock, passive uptime, gacha/event/BP/craft source, opportunity cost

### `artifact_card`

Purpose: show best / substitute / temporary artifact options.

Recommended content:

- best set, substitute sets, temporary sets
- sands/goblet/circlet main stats
- substat priority
- minimum ER or other cycle condition before chasing crit
- stop-farming point

### `mechanics_card`

Purpose: prevent common play mistakes that ruin damage or rotation.

Recommended content:

- key stack/resource/stance/mark/reaction-owner rule
- what to do
- common mistake
- how to verify in game

Examples of mechanics worth highlighting:

- 스택을 소비하지 않아 피증/추가타가 비는 상황
- 핏값/Bond of Life 회수 전 평타만 치는 상황
- 원충 부족으로 폭발 사이클이 끊기는 상황
- 증발/융해/격화/만개 트리거 소유자가 바뀌는 상황

## Image source policy

Use official/wiki-first sourcing for character/weapon/artifact images:

1. Local preprocessed cache built from official/wiki MediaWiki image URLs.
2. Official HoYoverse, HoYoLAB, or in-game screenshots supplied by the user.
3. Fandom/wiki-style pages with visible page title and URL.
4. Other clearly attributed guide pages only when official/wiki images are unavailable.
5. Text/icon placeholder card if no safe source is found.

Do **not** do broad fanart scraping or unsourced Google image harvesting by default. Do not download or cache a full image pack. Do not claim image licensing is guaranteed; record the visible source and keep usage limited to active consultation artifacts.

For every external image used, record:

- `image_source_id`
- source title/site
- source URL
- asset URL when visible
- license/usage note if visible, otherwise `not_visible`
- character/weapon/artifact represented
- retrieval date

## Metadata JSON contract

Each PNG card must have a paired `.json` metadata file.

```json
{
  "card_type": "weapon_top5_card|artifact_showcase_card|party_card|party_list_card|build_card|weapon_card|artifact_card|mechanics_card",
  "title": "string",
  "subtitle": "string|null",
  "summary_lines": ["string"],
  "items": [
    {
      "rank": 1,
      "name": "string",
      "image_path": "absolute local path or null",
      "image_source_id": "img-1|null",
      "badge": "string|null",
      "rating": "string|null",
      "note": "string|null"
    }
  ],
  "characters": [
    {"name": "string", "role": "string", "element": "pyro|hydro|electro|cryo|anemo|geo|dendro|physical", "icon_path": "absolute local path or null", "image_path": "fallback absolute local path or null", "image_source_id": "img-1"}
  ],
  "teams": [
    {"rank": 1, "name": "string", "reaction": "string", "note": "string", "rotation": "string|null", "characters": ["exactly four character objects"]}
  ],
  "character": {
    "name": "string",
    "element": "pyro|hydro|electro|cryo|anemo|geo|dendro|physical",
    "role": "string",
    "card_path": "absolute local path or null",
    "icon_path": "absolute local path or null"
  },
  "theme_element": "pyro|hydro|electro|cryo|anemo|geo|dendro|physical|null",
  "operation": "party_card playstyle text|null",
  "rotation": "party_card rotation text|null",
  "notes": "party_card caveat text|null",
  "weapon": {"name": "string", "summary": "string|null"},
  "artifact": {"name": "string", "summary": "string|null"},
  "artifacts": [
    {"slot": "Flower|Plume|Sands|Goblet|Circlet", "image_path": "absolute local path or null", "main_stat": "string", "substats": ["string"]}
  ],
  "target_stats": {"stat": "target string"},
  "sections": [{"title": "string", "lines": ["string"]}],
  "rows": [
    {"label": "string", "value": "string", "note": "string|null"}
  ],
  "source_ids": ["src-1"],
  "image_source_ids": ["img-1"],
  "generated_at": "ISO-8601 timestamp",
  "output_image_path": "generated/visuals/example.png"
}
```

`weapon_top5_card` should contain 3-5 `items[]` entries, ideally five. `artifact_showcase_card` should contain 1-5 `items[]` entries, ideally five set-piece entries. Party cards should contain exactly four `characters[]` entries. `party_list_card` should contain 3-5 `teams[]`, and each team must contain exactly four `characters[]`. Other card types may use `rows[]` as their main content.

## Consultation JSON linkage

When a visual card is produced, add a top-level entry to `visual_artifacts[]` in the consultation JSON:

```json
{
  "type": "weapon_top5_card",
  "path": "generated/visuals/raiden-party.png",
  "metadata_path": "generated/visuals/raiden-party.json",
  "display_hint": "markdown_inline|path_only|tool_view",
    "alt_text": "콜롬비나 추천 무기 TOP 5 카드",
  "source_ids": ["src-1", "src-2"],
  "image_source_ids": ["img-1", "img-2", "img-3", "img-4"]
}
```

## Codex display rules

For original input image previews:

1. Render the available character, weapon, and artifact screenshots inline with Markdown images.
2. Use a one-row Markdown table for up to five artifact slot images when possible.
3. Explicitly mark missing categories or slots as `제공 없음` or `확인 필요`.
4. Keep original user screenshots out of `visual_artifacts[]`; record them in `input_images[]`.

After generating a card:

1. Mention the saved PNG path.
2. Mention the metadata JSON path.
3. If the current surface can render Markdown images, embed `![alt text](absolute/path.png)`. Convert relative generated paths to concrete absolute paths before embedding.
4. If an image viewing tool is available, use it for local inspection/display when appropriate.
5. If images cannot be displayed, provide a one-sentence visual description and keep the paths.

For weapon/artifact recommendation answers, the generated showcase card must appear before the detailed text table:

```markdown
무기 TOP 5 카드
![콜롬비나 추천 무기 TOP 5](/absolute/path/to/genshin_agent/generated/visuals/columbina-weapon-top5.png)

성유물 추천 카드
![콜롬비나 추천 성유물](/absolute/path/to/genshin_agent/generated/visuals/columbina-artifacts.png)
```

Do not hide uncertainty behind visuals. If a portrait, source, stat, or team assumption is uncertain, show that in text and metadata.

# Source Policy

Use this reference before web research. Current character build advice is time-sensitive, so browse for every character-specific consultation.

## Source tiers

### Tier A — mechanics and facts
Use for formulas, kit facts, release/version status, material data, and system mechanics.

- Official HoYoverse announcements and character pages
- HoYoLAB official or clearly attributed official posts
- KQM guides and Theorycrafting Library
- Fandom/wiki pages for structured game data
- In-game text when visible from screenshots

### Tier B — Korean practical guidance
Use for Korean-friendly explanations, rotations, artifact priorities, weapon comparisons, and community practical advice.

- 원신-specialized YouTube guides from recognizable creators
- Naver/Tistory/blog posts dedicated to Genshin builds
- HoYoLAB guide posts
- Korean community guide compilations, if source/date are visible

### Tier C — general tier lists and low-context posts
Use only as weak signals. Never make a firm recommendation from Tier C alone.

## Minimum source pack per consultation

### Normal consultation: minimum 5 sources when available

Use this for a normal single-character build consultation or screenshot diagnosis.

Required mix:

1. **Tier A mechanics/facts source** — kit, talent, material, or system data.
2. **Korean practical guide source** — 뉴비가 이해하기 쉬운 빌드/로테이션/세팅 설명.
3. **Current/recent cross-check source** — update date/version context visible when possible.
4. **Build claim source** — target stats, artifacts, weapon, or talent priority.
5. **Team or usage source** — team fit, rotation, mechanics mistake, or practical caveat.

If fewer than five credible sources exist, state `근거 부족`, explain which slot is missing, and narrow the advice.

### Precision consultation: minimum 8 sources when available

Use this stricter mode whenever the answer includes any of these:

- refinement-aware weapon ranking
- party recommendation or 3-team roster plan
- mechanics/rotation checklist
- artifact best/substitute/temporary comparison
- target stat card or exact CR/CD/ER/EM/scaling-stat thresholds
- material/resin planning with exact farming guidance
- local PNG visual cards or image-source-backed visual artifacts

Recommended 8-source mix:

1. Tier A mechanics/facts source.
2. Official/wiki-style data source for materials, kit text, or images.
3. Korean practical guide source.
4. Recent/current cross-check source with visible date/version when possible.
5. Weapon ranking/refinement source.
6. Artifact/stat target source.
7. Team/rotation source.
8. Image source metadata or additional claim-specific source for generated cards.

When producing multiple high-impact claims, add more sources instead of stretching one source across unrelated claims.

## Image source metadata and local assets for visual cards

For local PNG cards, use the local preprocessed asset cache first, then official/wiki-first image sourcing:

1. Local asset cache from `references/asset-cache.md`.
2. Official HoYoverse, HoYoLAB, or user-provided in-game screenshots.
3. Fandom/wiki-style images/icons with visible page title and URL.
4. Other clearly attributed guide pages only when official/wiki images are unavailable.
5. Text/icon placeholder card if no safe source is found.

Do not broad-scrape fanart or unsourced Google Images. Do not download or cache a full asset pack during ordinary consultations. If the user explicitly asks to build or refresh a reusable image pack, use `scripts/build_asset_cache.py` and store it as a local preprocessed cache. Do not claim image licensing is guaranteed.

For every character, weapon, or artifact displayed in a generated visual card:

1. Query `scripts/query_asset_cache.py` for that exact item.
2. Put the cached `image_path` into the card metadata as `characters[].image_path` or `items[].image_path` when found.
3. If the cache misses, find an official HoYoverse/HoYoLAB page or a Fandom/wiki page for that exact item.
4. Use `scripts/fetch_card_assets.py` to download a local image asset from `asset_url`, `og:image`, `twitter:image`, or `image_src`.
5. Use placeholders only after cache lookup and official/wiki image discovery both fail, and record the failure.

For every external image used, record:

- `image_source_id`
- source title/site name
- page URL
- direct asset URL if visible
- represented character/weapon/artifact
- retrieval date
- visible license/usage note, or `not_visible`
- local downloaded path used in card metadata
- whether it was used in `weapon_top5_card`, `artifact_showcase_card`, `party_card`, `build_card`, `weapon_card`, `artifact_card`, or `mechanics_card`

## Claims that require browsing

Browse before making any of these character-specific claims:

- target stat numbers, CR/CD/ER/EM/scaling-stat thresholds
- weapon ranking order, especially refinement-dependent ranking
- best artifact and substitute artifact comparisons
- exact material lists or resin domain recommendations
- key mechanics/rotation details, stack/resource handling, or common mistakes
- current banner/pull value, new character status, or post-release meta
- team ranking or best-in-slot teammates
- visual-card image source or icon/portrait provenance

## Required source metadata

For every cited source, record:

- title or channel/site name
- URL
- publication or update date if visible
- game version if visible
- claim supported by the source
- source tier: A, B, or C

## Search query patterns

Use Korean and English searches. Replace `{character}` with the actual character name and also try the Korean name if known.

### Build and stats

- `원신 {character} 성유물 무기 특성 조합 최신`
- `원신 {character} 공략 성유물 무기 특성 별자리`
- `원신 {character} 치확 치피 원충 원마 스펙`
- `Genshin {character} guide artifacts weapons talents teams KQM`
- `Genshin {character} build guide version`

### Weapon and refinement rankings

- `원신 {character} 무기 순위 재련 R1 R5`
- `원신 {character} 전무 대체 무기 기행 단조 이벤트`
- `Genshin {character} weapon ranking R1 R5`
- `site:keqingmains.com {character} weapon ranking`

### Mechanics and usage pitfalls

- `원신 {character} 사용법 메커니즘 스택 콤보`
- `원신 {character} 실수 주의점 사이클`
- `Genshin {character} mechanics rotation mistakes stacks`
- `site:genshin-impact.fandom.com {character}`

### Materials

- `원신 {character} 육성 재료 특성 재료 돌파 재료`
- `Genshin {character} ascension talent materials`
- `site:genshin-impact.fandom.com {character} materials`

### Korean video/blog practical sources

- `원신 {character} 유튜브 공략 최신`
- `원신 {character} 블로그 공략 최신`
- `원신 {character} 호요랩 공략`

### Visual card image sources

- `site:genshin.hoyoverse.com {character} character`
- `site:hoyolab.com {character} official image`
- `site:genshin-impact.fandom.com {character} image icon`
- `Genshin {character} official portrait wiki`

## Conflict handling

- Prefer Tier A for mechanics, material data, and exact kit/stat claims.
- Prefer recent Korean practical sources for how to explain priorities to a newbie.
- Prefer official/wiki-first image sources for visual cards; use placeholders if provenance is unclear.
- If sources disagree, present the disagreement and choose a conservative recommendation.
- Mark claims as `확인 필요` if the source is old, version context is unclear, or the character is newly released.
- Do not cite comments, unsourced community claims, or AI-generated pages as primary evidence.
- Do not invent exact DPS percentages; cite them only if the source provides comparable assumptions.

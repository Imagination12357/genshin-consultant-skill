# Report Design Rules

Use this reference only in report mode when generating `party_card` or `build_card` PNGs. Do not load this file during ordinary text-only consultations. The layout is Enka-inspired for readability, but it must not copy Enka assets, CSS, or exact composition.

## Renderer Choice

- For a single-character build/endgame/spec report, prefer `scripts/render_html_report.py`.
- For a party recommendation card, also prefer `scripts/render_html_report.py` when a polished visual is expected.
- The HTML renderer creates a designed `.html` file and a PNG screenshot. Use it when the answer discusses one main character's build, weapon, artifacts, target stats, current account screenshot, or a primary party lineup.
- Use `scripts/render_visual_card.py` only for compact fallback/mechanics/secondary cards.
- The HTML report must include character card art, weapon image, and artifact images when the asset cache has them.
- Text in the HTML report is intentionally bold by CSS; do not weaken it with light font weights.
- Weapon and artifact showcase cards must use the same dark HUD theme as the build report. Do not use plain white card grids for final recommendation visuals.
- Keep text layers off character art. Use separate HUD panels for identity, stats, weapon, and artifact labels.
- When a consultation creates a build card plus weapon/artifact/party cards, compose them into one vertical page with `scripts/compose_visual_page.py` and display that page as the primary visual.
- Rendered card content should use Korean display names. Run `scripts/localize_card_metadata.py` before rendering if metadata contains English canonical names.
- Composed pages should align every card to the same outer width. Use `fit_width: true` in `visual_page` metadata when source cards have different widths.
- Do not print source footers inside card or page PNGs. Put citations in the text answer instead.
- Build report center stat/weapon panels must leave visible breathing room before the right artifact column; avoid center panel borders touching artifact cards.
- Do not repeat constellation text such as `C0 기준` in weapon, artifact, or party cards when the first build card already states it.
- Do not add repeating horizontal stripe/grid backgrounds. Use element-themed gradients, panels, borders, and accent bars instead.

## Asset Variant Rules

- Party recommendations must use character `icon` assets from the local cache.
  - Query: `scripts/query_asset_cache.py <names...> --kind character --variant icon --limit 1`
  - Put the result in `characters[].icon_path`.
  - Keep `characters[].image_path` only as a backwards-compatible fallback.
- Single-character build reports must use the character `card` asset as the left hero image.
  - Query: `scripts/query_asset_cache.py <name> --kind character --variant card --limit 1`
  - Put the result in `character.card_path` or top-level `card_path`.
  - Add `character.icon_path` only if the report also needs a compact identity badge.
- Weapon and artifact recommendation showcase cards use `render_showcase_card.py`; this renderer is styled to match the HTML report. A single-character HTML build report must still embed the selected weapon image and artifact piece images in the same report screen.
- Artifact piece labels in visuals must use full Korean slot names: `생명의 꽃`, `죽음의 깃털`, `시간의 모래`, `공간의 성배`, `이성의 왕관`.

## Theme Rules

- Set `theme_element` explicitly when the main character is known.
- If `theme_element` is missing, the renderer uses the first `characters[0].element` for `party_card` or `character.element` for `build_card`.
- Supported theme values: `pyro`, `hydro`, `electro`, `cryo`, `anemo`, `geo`, `dendro`, `physical`.
- Korean aliases such as `불`, `물`, `번개`, `얼음`, `바람`, `바위`, `풀`, `물리` are accepted in metadata.

## Party Report Contract

Use this shape for party recommendations:

```json
{
  "card_type": "party_card",
  "title": "가명 + 향릉 4성 파티",
  "subtitle": "온필드 증발/불 공명",
  "theme_element": "pyro",
  "characters": [
    {
      "name": "가명",
      "element": "pyro",
      "role": "온필드 낙공 딜러",
      "contribution": "증발 트리거와 메인 딜",
      "build": "마녀 4 / 공격-불-치명",
      "icon_path": "/absolute/path/to/.../gaming/icon.png",
      "image_source_id": "character:gaming"
    }
  ],
  "operation": "누가 반응을 먹는지와 파티의 핵심 원리를 한 문장으로 쓴다.",
  "rotation": "실전 입력 순서를 짧게 쓴다. 예: 베넷 EQ > 행추 EQ > 향릉 QE > 가명 E/Q.",
  "notes": "주의할 점, 에너지 조건, 대체 캐릭터를 적는다.",
  "source_ids": ["src-1"],
  "image_source_ids": ["character:gaming"],
  "output_image_path": "/absolute/path/to/genshin_agent/generated/visuals/example-party.png"
}
```

Layout expectations:

- Exactly four characters in one horizontal row.
- Icons are displayed in rounded rectangular HUD slots, not circular portraits or plain white cards.
- Slot order should match practical rotation priority or the user's main DPS first.
- Put playstyle, rotation, and caveats in separate bottom panels.
- Do not put long paragraphs inside character slots; use `operation`, `rotation`, and `notes` for prose.
- When the answer needs multiple ranked team options, prefer `scripts/render_party_list_card.py` with `card_type: "party_list_card"` over multiple separate `party_card` images. Keep each team to exactly four character icons and include one concise operation or rotation line per team.

## Build Report Contract

Use this shape for single-character build/endgame/spec reports:

```json
{
  "card_type": "build_card",
  "title": "클로린드 종결 체급 리포트",
  "subtitle": "해연의 피날레 기준",
  "theme_element": "electro",
  "character": {
    "name": "클로린드",
    "element": "electro",
    "role": "온필드 번개 딜러",
    "level": "90/90",
    "constellation": "C0",
    "card_path": "/absolute/path/to/.../clorinde/card.png",
    "icon_path": "/absolute/path/to/.../clorinde/icon.png"
  },
  "weapon": {
    "name": "해연의 피날레",
    "refinement": "R1",
    "level": "90/90",
    "summary": "공격력 무기라 치명/원충을 성유물에서 더 챙긴다."
  },
  "artifact": {
    "name": "조화로운 공상의 단편 4세트",
    "summary": "생명의 계약 운용이면 기본값."
  },
  "target_stats": {
    "치확": "70-85%",
    "치피": "170-210%+",
    "원충": "120-140%",
    "공격력": "2,000+"
  },
  "sections": [
    {
      "title": "먼저 고칠 것",
      "lines": ["치확 70% 전까지 치명타 확률을 우선한다."]
    }
  ],
  "source_ids": ["src-1"],
  "image_source_ids": ["character:clorinde"],
  "output_image_path": "/absolute/path/to/genshin_agent/generated/visuals/example-build.png"
}
```

Layout expectations:

- Character `card` art is the large left panel.
- Center/right side contains weapon image, artifact images, target stats, and prioritized fixes in one polished screen.
- If artifact pieces are available, include all five artifact images in `artifacts[]` or `artifact.pieces[]`.
- If the weapon image is available, put it in `weapon.image_path`.
- Artifact recommendation cards should show recommended main options and substat priority, not fake rolled substat values.
- Use short, scannable labels. Long coaching text belongs in the answer body after the image.
- If `card_path` is unavailable, render a placeholder but list the image gap in the text answer.

# Output Template

Use this Korean consultation shape unless the user asks otherwise. Rich text consultations should feel expert and complete: concise, but not bare. Prefer 4-8 short sections and 0-3 compact tables when the request includes builds, target stats, weapons, artifacts, or teams.

## UI-safe layout contract

This contract overrides any wider table examples below.

- Use prose tables only for short, scannable data. Keep them to 2 columns by default and 3 columns maximum.
- Do not use 4+ column prose tables in normal Codex thread answers. Image-only exceptions are allowed for horizontal party lineups and artifact-piece rows.
- Do not place long explanations, rotations, caveats, source links, or multiple code chips inside table cells.
- Use numbered card blocks for parties, weapons, artifacts, rotations, and target-stat tiers when the content needs sentences.
- Put citations after each section as a short `근거:` line instead of inside table rows.
- Keep local image previews attached to relevant text items. Do not stack standalone raw images vertically.

## Tone default

Use `info-first-flavor`: facts/tables/source claims stay precise, while one-line diagnosis and priority advice may use light Korean Genshin veteran/broadcast flavor.

## 1. 한줄 결론
- 현재 상태를 한 문장으로 요약한다.
- 예: `지금은 딜 부족보다 원충/사용법/성유물 주옵 정리가 먼저입니다.`

## 2. 핵심 이미지 요약
Use when local asset icons are available from the cache. This is still text mode, not report mode. If the answer names specific characters, weapons, or artifact sets and cache entries exist, this section is required.

- Put only small images in compact rows or image-only horizontal tables.
- Never use HTML `<img>` or HTML `<br>` for cached icons; Codex desktop may print them as text. Generate thumbnails with `query_asset_cache.py --thumb-size 48` and render them with Markdown image syntax.
- Use character `icon.png` for party/build rows, weapon icons beside each weapon recommendation, and artifact piece/set icons in artifact recommendations.
- Do not create PNG cards, metadata JSON, or composed pages here.
- Omit this section only if no useful asset is found or the user explicitly asks for text-only output.

Preferred example. Use this item-attached layout; do not copy malformed, standalone gallery, or wide prose-table examples:

```markdown
**추천 파티**
| 온필드 | 서브딜 | 풀/버퍼 | 바람/방어 |
|---|---|---|---|
| 클로린드 | 피슬 | 나히다 | 카즈하 |
| ![클로린드](/absolute/path/to/genshin_agent/genshin-consultant/assets/genshin-assets/current/thumbnails/48/images/characters/clorinde/icon.png) | ![피슬](/absolute/path/to/genshin_agent/genshin-consultant/assets/genshin-assets/current/thumbnails/48/images/characters/fischl/icon.png) | ![나히다](/absolute/path/to/genshin_agent/genshin-consultant/assets/genshin-assets/current/thumbnails/48/images/characters/nahida/icon.png) | ![카즈하](/absolute/path/to/genshin_agent/genshin-consultant/assets/genshin-assets/current/thumbnails/48/images/characters/kaedehara-kazuha/icon.png) |

핵심: 촉진 유지, 피슬 배터리, 카즈하 번개 확산.

**무기**
![해연의 피날레](/absolute/path/to/genshin_agent/genshin-consultant/assets/genshin-assets/current/thumbnails/48/images/weapons/finale-of-the-deep/icon.png) **해연의 피날레 R5**: 현재 유지 추천.

![사면](/absolute/path/to/genshin_agent/genshin-consultant/assets/genshin-assets/current/thumbnails/48/images/weapons/absolution/icon.png) **사면**: 확실한 업그레이드.

**성유물**
| 꽃 | 깃털 | 시계 | 성배 | 왕관 |
|---|---|---|---|---|
| ![꽃](/absolute/path/to/.../thumbnails/48/images/artifacts/fragment-of-harmonic-whimsy/harmonious-symphony-prelude/icon.png) | ![깃털](/absolute/path/to/.../thumbnails/48/images/artifacts/fragment-of-harmonic-whimsy/ancient-seas-nocturnal-musing/icon.png) | ![시계](/absolute/path/to/.../thumbnails/48/images/artifacts/fragment-of-harmonic-whimsy/the-grand-jape-of-the-turning-of-fate/icon.png) | ![성배](/absolute/path/to/.../thumbnails/48/images/artifacts/fragment-of-harmonic-whimsy/ichor-shower-rhapsody/icon.png) | ![왕관](/absolute/path/to/.../thumbnails/48/images/artifacts/fragment-of-harmonic-whimsy/whimsical-dance-of-the-withered/icon.png) |
```

Deprecated legacy example:

```markdown
**아이콘**
![슈브르즈](/absolute/path/to/genshin_agent/genshin-consultant/assets/genshin-assets/current/images/characters/chevreuse/icon.png)
![두린](/absolute/path/to/genshin_agent/genshin-consultant/assets/genshin-assets/current/images/characters/durin/icon.png)

**추천 무기**
![흑술창](/absolute/path/to/genshin_agent/genshin-consultant/assets/genshin-assets/current/images/weapons/black-tassel/icon.png)
![페보니우스 장창](/absolute/path/to/genshin_agent/genshin-consultant/assets/genshin-assets/current/images/weapons/favonius-lance/icon.png)
```

Legacy example:

```markdown
| 항목 | 이미지 | 요약 |
|---|---|---|
| 메인 캐릭터 | ![말라니](/absolute/path/to/genshin_agent/genshin-consultant/assets/genshin-assets/current/images/characters/mualani/icon.png) | HP 기반 물 온필드 딜러 |
| 추천 무기 | ![서핑 타임](/absolute/path/to/.../weapons/surf-s-up/icon.png) | 치피/HP 계열 고점 |
```

## 3. 입력 이미지 미리보기
Use whenever the user supplied attached images or local image paths. Put this near the top of the report, before build diagnosis.

- Character: render the best character/profile/details image with Markdown image syntax.
- Weapon: render the weapon image when provided; otherwise write `무기 이미지: 제공 없음`.
- Artifacts: render individual artifact images when provided. Use a one-row table for five slots when possible; otherwise use a compact labeled gallery.
- Local image URLs must be concrete absolute paths. Prefer privacy-safe aliases such as `/absolute/path/to/...`; do not use `~` or `$env:USERPROFILE` inside the image URL.

Example:

```markdown
캐릭터 이미지
![캐릭터 이미지](/absolute/path/to/genshin_agent/캐릭터/캐릭터 정보.png)

무기 이미지
무기 이미지: 제공 없음

성유물 이미지
| 꽃 | 깃털 | 시계 | 성배 | 왕관 |
|---|---|---|---|---|
| ![꽃](/absolute/path/to/.../flower.png) | ![깃털](/absolute/path/to/.../plume.png) | ![시계](/absolute/path/to/.../sands.png) | ![성배](/absolute/path/to/.../goblet.png) | ![왕관](/absolute/path/to/.../circlet.png) |
```

## 4. 시각자료 / 카드 출력
Use only when report mode was explicitly triggered and visual artifacts were generated.

- In report mode, weapon advice should include `weapon_top5_card`.
- In report mode, artifact advice should include `artifact_showcase_card`.
- Put report images before the detailed text tables.
- PNG: `generated/visuals/...png`
- Metadata: `generated/visuals/...json`
- Display: `![카드 설명](absolute/path.png)` when Markdown image rendering works; otherwise provide the path and one-line description.

| 카드 | 경로 | 메타데이터 | 근거 | 메모 |
|---|---|---|---|---|
| weapon_top5/artifact_showcase/party/build/weapon/artifact/mechanics |  |  | source_ids / image_source_ids |  |

Example:

```markdown
무기 TOP 5 카드
![콜롬비나 추천 무기 TOP 5](/absolute/path/to/genshin_agent/generated/visuals/columbina-weapon-top5.png)

성유물 추천 카드
![콜롬비나 추천 성유물](/absolute/path/to/genshin_agent/generated/visuals/columbina-artifacts.png)
```

## 5. 이미지에서 확인한 현재 상태
| 항목 | 값 | 신뢰도 | 메모 |
|---|---|---|---|
| 캐릭터 |  | confirmed/inferred/needs_confirmation |  |
| 레벨/돌파/별자리 |  |  |  |
| 무기/재련 |  |  |  |
| 특성 |  |  |  |
| 주요 스탯 |  |  |  |
| 성유물 |  |  |  |
| 보유 로스터/무기 |  |  | 계정 상담일 때 |

## 6. 확인 필요
- 안 보이는 값, 흐릿한 값, 추가 스크린샷이 필요한 값을 bullet로 적는다.
- 조언이 팀/무기/로스터에 따라 달라지는 경우 필요한 정보를 명시한다.

## 7. 현재 빌드 진단
Use for screenshots or when the user provides current stats. If no current stats exist, write assumptions instead.

| 항목 | 판단 | 이유 | 바로 할 일 |
|---|---|---|---|
| 세팅 방향 |  |  |  |
| 원충/사이클 |  |  |  |
| 치명/주스탯 |  |  |  |
| 성유물 |  |  |  |

## 8. 목표 스펙 카드
| 구간 | 치확/치피 | 원충 | 원마/HP/ATK/DEF 등 주력 스탯 | 조건/메모 |
|---|---|---|---|---|
| 최소 실전 |  |  |  |  |
| 안정권 |  |  |  |  |
| 준종결 |  |  |  |  |
| 종결/고점 |  |  |  |  |

Rules:

- 조건부 치확/피증/버프를 반영한다.
- ER은 가능한 경우 추천 파티 기준으로 적는다.
- 팀 정보가 없으면 `team-dependent`라고 표시한다.

## 9. 세팅 논리
Explain why the recommended stat balance works. This should be 2-5 short bullets, not a vague summary.

- 어떤 스탯이 딜 증가에 직접 연결되는지.
- 조건부 치확/버프/반응이 어떤 식으로 표기 스탯을 바꾸는지.
- 무기나 파티에 따라 목표치가 어떻게 달라지는지.
- 사용법 실수가 스펙보다 더 큰 병목이 되는 지점.

## 10. 핵심 사용법 / 메커니즘 체크리스트
| 체크 | 해야 할 행동 | 놓치면 생기는 문제 | 확인 방법 |
|---|---|---|---|
|  |  |  |  |

Include stack/resource/stance/mark/Bond of Life/summon/reaction ownership mistakes when relevant.

## 11. 우선순위 처방
### 오늘 할 일
- 즉시 바꿀 수 있는 무기/성유물/특성/레벨/로테이션 조치.

### 이번 주 레진 계획
- 보스, 특성책, 무기재료, 성유물 도메인 우선순위.

### 장기 목표
- 준종결/종결 방향과 언제 멈춰도 되는지.

## 12. 성유물
In rich text mode, answer with the table directly and optional inline cached icons. In report mode, embed the `artifact_showcase_card` before this table.

| 항목 | 이미지 | 추천 | 대체 | 메모 |
|---|---|---|---|---|
| 세트 |  |  |  |  |
| 생명의 꽃 |  | HP 고정 |  | 부옵 우선순위 |
| 죽음의 깃털 |  | 공격력 고정 |  | 부옵 우선순위 |
| 시간의 모래 |  |  |  |  |
| 공간의 성배 |  |  |  |  |
| 이성의 왕관 |  |  |  |  |
| 부옵 |  |  |  | ER 최소조건 먼저 |

## 13. 무기 추천 순위
In rich text mode, answer with the table directly and optional inline cached icons. In report mode, embed the `weapon_top5_card` before this table.

| 순위 | 이미지 | 무기 | 재련 | 평가 | 조건/주의점 |
|---|---|---|---:|---|---|
| 1 |  |  | R1/R5 | best/excellent/good/usable/temporary |  |

Rules:

- 재련에 따라 순위가 바뀌면 행을 분리한다.
- 보유 무기 우선 추천 후, 미보유 대체/미래 선택지를 분리한다.
- 이벤트/기행/한정/단조 여부와 기회비용을 표시한다.

## 14. 특성/돌파/재료
| 항목 | 목표 | 우선순위 | 멈출 지점 | 메모 |
|---|---|---:|---|---|
| 일반공격 |  |  |  |  |
| 원소전투 스킬 |  |  |  |  |
| 원소폭발 |  |  |  |  |
| 캐릭터 레벨/돌파 |  |  |  |  |
| 무기 레벨 |  |  |  |  |

If exact material counts are requested, cite official/wiki-style data.

## 15. 추천 파티
Use when roster data exists.

| 구분 | 파티 이미지/구성 | 역할 | 왜 좋은지 | 로테이션 | 대체 |
|---|---|---|---|---|---|
| 최우선 |  |  |  |  |  |
| 안정형 |  |  |  |  |  |
| 저투자/임시 |  |  |  |  |  |

## 16. 뽑기 조언
- 뽑을 가치가 있는 경우와 아닌 경우.
- 기회비용과 4성/보유 캐릭 대체안.
- 과금 권유처럼 말하지 않는다.

## 17. 출처
| 출처 | 등급 | 날짜/버전 | 근거로 사용한 내용 | 링크 |
|---|---|---|---|---|
|  | Tier A/B/C |  |  |  |

## 18. 다음에 보내면 좋은 이미지
- 캐릭터 상세 1/2
- 성유물 각 부위 상세
- 무기 화면과 무기 보유 목록
- 특성 화면
- 별자리 화면
- 전체 로스터/캐릭터 보유 현황

## 19. 리포트 제안
Use when the answer was rich text and the user did not explicitly request report mode. End with a short single sentence:

`리포트도 발행해드릴까요?`

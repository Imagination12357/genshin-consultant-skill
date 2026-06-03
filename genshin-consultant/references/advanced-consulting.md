# Advanced Consulting Playbook

Use this reference for any serious character build, roster, team, or account-planning request. It converts real player UX needs into repeatable consulting output.

## Codex thread layout override

Some matrices below are schema examples for complete reasoning, not mandatory visual layout. In a Codex desktop thread, do not render wide 4+ column prose tables for parties, weapon rankings, artifacts, rotations, or target stats. Convert them into compact 2-column tables or numbered card blocks with labeled lines (`편성:`, `핵심:`, `조건:`, `교체:`, `근거:`). Keep citations outside table cells.

Asset layout override: party recommendations should use a horizontal 4-slot icon row when cached character icons exist, then put the explanation below. Artifact recommendations should use a horizontal 5-piece icon row when cached artifact piece icons exist, then put main stats and substat priority below. Weapon recommendations should attach one generated thumbnail Markdown image directly beside each weapon name, not as a separate gallery. Never use HTML `<img>` in Codex thread rich text because it renders as literal text.

## Required consulting modules

For a main character consultation, include these modules unless the user explicitly asks for a shorter answer:

1. **Target stat card** — the character's role-specific target stats.
2. **Weapon ranking matrix** — usable weapons ranked by role and refinement.
3. **Artifact plan** — best set, substitute sets, transition sets, main stats, substat priority, and minimum ER/EM/crit thresholds.
4. **Mechanics and usage checklist** — what the player must actually do in rotation, plus common mistakes that ruin the build.
5. **Resource plan** — character/weapon/talent/artifact farming priorities and resin stop points.
6. **Team recommendations** — if roster is provided, recommend 3 teams with roles, rotation notes, and missing pieces.
7. **Visual cards** — produce mandatory weapon/artifact showcase cards for weapon or artifact recommendations, and optional party/build/mechanics card metadata and local PNG output paths when useful.

## Target stat card

Always separate the target into tiers. Do not present one number as universal truth.

| Tier | Meaning |
|---|---|
| 최소 실전 | Works for story/field/basic domains if rotation and main stats are correct. |
| 안정권 | Comfortable for Abyss-style use or harder combat; this is the default recommendation. |
| 준종결 | Strong investment; stop here for most accounts unless the character is a favorite. |
| 종결/고점 | Luxury optimization; explain resin cost and opportunity cost. |

For each tier, include the relevant stats only:

- CRIT Rate / CRIT DMG, with conditional crit buffs noted.
- ER minimum for the listed team/rotation, not a generic number.
- EM target only when reaction ownership benefits from EM.
- HP/ATK/DEF target only for characters that scale meaningfully from that stat.
- Elemental/Physical DMG bonus or special stats when relevant.

Rules:

- If team, weapon, or rotation is unknown, give a conservative range and label it `team-dependent`.
- If a set gives conditional crit or damage bonus, show both sheet stats and effective stats.
- If sources disagree, give a safe range and cite the disagreement.
- For transformative reaction triggers, level 90 can matter more than crit; say so clearly.

## Weapon ranking matrix

Players often ask “what weapon should I use?” but need a ranking that accounts for ownership and refinement.

Include a table like:

| Rank | Weapon | Refinement | Why it ranks here | Requirements / caveats | Source |
|---|---:|---:|---|---|---|

Rules:

- Start with owned weapons if the user provides a weapon inventory.
- Then list the practical full matrix for the character's role: signature, limited 5-star alternatives, standard 5-star, battle pass, craftable, event, gacha 4-star, and realistic 3-star options when relevant.
- Split rankings by refinement when it changes the order, e.g. `R1`, `R3`, `R5`.
- Do not claim exact DPS percentages unless a source provides them. Prefer relative labels: `best`, `excellent`, `good`, `usable`, `temporary`, `not recommended`.
- Mark unobtainable event weapons and paid Battle Pass weapons clearly.
- If a weapon needs extra ER/CR/EM to work, include that in caveats.
- If the user asks for “all weapons,” include all materially viable weapons and a short omitted bucket for obviously incompatible weapons.

## Artifact plan

For each character role, include:

- Best set and why.
- Substitute sets and when they are close enough.
- Transition/2pc+2pc options for new accounts.
- Main stats for sands/goblet/circlet.
- Substat priority in order.
- Minimum ER or EM thresholds needed for the recommended rotation/team.
- When to stop farming.

Use this shape:

| Slot/Set | Best | Substitute | Temporary | Notes |
|---|---|---|---|---|
| Set |  |  |  |  |
| Sands |  |  |  |  |
| Goblet |  |  |  |  |
| Circlet |  |  |  |  |

Stop-point examples:

- `주옵+세트 완성 전`: do not over-evaluate substats.
- `안정권 도달`: switch resin to another bottleneck.
- `준종결 이후`: only farm if favorite/high-end goal.

## Mechanics and usage checklist

Many build failures are actually usage failures. Always include a short `핵심 사용법` section for the consulted character.

Include:

- Skill/burst sequence and what to consume/avoid.
- Stack, mark, stance, Bond of Life, special resource, summon, or field-state mechanics.
- Reaction ownership: who triggers the important reaction.
- Common mistakes that make the character look weak.
- Visual or UI cues the player can check.

Examples of the kind of pitfall to capture, without making uncited current claims:

- A character loses damage if the player fails to build/consume the intended stacks.
- A charged attack, stance, or special object may be required to gain a buff.
- A Bond of Life or special mark may need to be collected/managed before damage windows.
- A reaction carry may fail if the aura is overwritten by the wrong teammate.

For named character mechanics, browse current sources and cite kit/mechanics references before giving exact instructions.

## Team recommendation module

When the user provides a roster, recommend exactly 3 teams unless fewer than 3 coherent teams exist.

Default team categories:

1. **Best current team** — strongest practical team using owned characters.
2. **Budget/stable team** — easier rotation, safer survival, lower artifact pressure.
3. **Second-side or growth team** — useful for Abyss/Theater/account development.

For each team:

| Team | Members | Roles | Why it works | Rotation sketch | ER/min conditions | Replacements |
|---|---|---|---|---|---|---|

Rules:

- Avoid assigning the same character to multiple simultaneous Abyss teams unless clearly labeled as an alternative.
- Include one defensive option when practical for new players.
- State missing characters/roles honestly.
- If the roster lacks core enablers, recommend the best temporary team and the next account role to acquire.
- If the user gives weapon inventory, match weapons to each team and avoid conflicts.

## Resource and material plan

Include resource guidance at the level useful to a player, not just a build list.

- Character ascension target: e.g. `80/90 first`, `90 only if transformative/HP/DEF/EM scaling warrants it`.
- Talent stop levels: `1/8/8`, `8/10/8`, etc. depending on kit priority.
- Weapon level target: generally weapon 90 for damage characters; explain exceptions.
- Weekly boss / local specialty / enemy material reminders if source-confirmed or visible.
- Artifact farming domain priority and whether the domain is resin-efficient for the account.

If exact materials are requested, browse official/wiki data and cite them.

## Visual card triggers

Use `references/visual-output.md` when any of these would improve player UX:

- User asks for weapon recommendations: create and display a mandatory `weapon_top5_card`.
- User asks for artifact recommendations: create and display a mandatory `artifact_showcase_card`.
- User asks for a party recommendation: create a `party_card` for the best or highlighted 4-person team.
- Weapon ranking is long or refinement-dependent: create a `weapon_card`.
- Artifact advice includes best/substitute/temporary paths: create an `artifact_card`.
- Target stats are the main answer: create a `build_card`.
- The character has common stack/resource/rotation pitfalls: create a `mechanics_card`.

Cards do not replace text; they compress the decision. Keep source IDs and image source IDs traceable.

## Output quality rules

- Answer as a consultant, not a database dump: start with what the user should do first.
- Put hard requirements before luxury optimization.
- Separate `확인된 사실`, `추정`, and `추가 확인 필요` when screenshot or source confidence is limited.
- Always include the player-facing reason: “왜 이걸 먼저 해야 하는지”.
- If advice depends on current banners, new characters, or post-release balance knowledge, browse before advising.

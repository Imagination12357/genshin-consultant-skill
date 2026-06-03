#!/usr/bin/env python3
"""Render an Enka-inspired Genshin build report with HTML/CSS.

This renderer is intentionally used for polished single-character build reports.
It generates a local HTML file and, when Playwright can launch a browser, a PNG
screenshot. The layout requires character card art, weapon image, and artifact
images when those assets are available.
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


THEMES: dict[str, dict[str, str]] = {
    "pyro": {
        "bg1": "#7f170b",
        "bg2": "#d45a32",
        "bg3": "#351006",
        "accent": "#ff7a45",
        "accent2": "#ffd0b8",
        "panel": "rgba(82, 18, 8, .72)",
        "panel2": "rgba(120, 35, 18, .68)",
        "line": "rgba(255, 199, 169, .42)",
        "glow": "rgba(255, 125, 68, .26)",
    },
    "hydro": {
        "bg1": "#063a6f",
        "bg2": "#2c8ac8",
        "bg3": "#06172b",
        "accent": "#63c7ff",
        "accent2": "#d5f3ff",
        "panel": "rgba(6, 42, 76, .72)",
        "panel2": "rgba(20, 79, 120, .66)",
        "line": "rgba(187, 231, 255, .42)",
        "glow": "rgba(80, 191, 255, .24)",
    },
    "electro": {
        "bg1": "#34146d",
        "bg2": "#8158db",
        "bg3": "#120824",
        "accent": "#b895ff",
        "accent2": "#eadcff",
        "panel": "rgba(40, 18, 77, .74)",
        "panel2": "rgba(86, 48, 140, .66)",
        "line": "rgba(222, 204, 255, .42)",
        "glow": "rgba(184, 149, 255, .24)",
    },
    "cryo": {
        "bg1": "#185875",
        "bg2": "#83d8f0",
        "bg3": "#061d2a",
        "accent": "#b7f2ff",
        "accent2": "#e9fbff",
        "panel": "rgba(18, 68, 88, .72)",
        "panel2": "rgba(57, 129, 155, .64)",
        "line": "rgba(220, 250, 255, .42)",
        "glow": "rgba(183, 242, 255, .24)",
    },
    "anemo": {
        "bg1": "#0c6255",
        "bg2": "#5bd8b6",
        "bg3": "#06251f",
        "accent": "#8dffe0",
        "accent2": "#dcfff6",
        "panel": "rgba(10, 66, 57, .72)",
        "panel2": "rgba(38, 126, 105, .64)",
        "line": "rgba(213, 255, 244, .42)",
        "glow": "rgba(141, 255, 224, .22)",
    },
    "geo": {
        "bg1": "#674010",
        "bg2": "#d59a38",
        "bg3": "#261604",
        "accent": "#ffd36a",
        "accent2": "#fff0bd",
        "panel": "rgba(75, 48, 12, .74)",
        "panel2": "rgba(126, 83, 22, .64)",
        "line": "rgba(255, 229, 166, .42)",
        "glow": "rgba(255, 211, 106, .22)",
    },
    "dendro": {
        "bg1": "#2e5d18",
        "bg2": "#95c94f",
        "bg3": "#101f09",
        "accent": "#c8ff7a",
        "accent2": "#f0ffd0",
        "panel": "rgba(38, 74, 18, .74)",
        "panel2": "rgba(79, 123, 42, .64)",
        "line": "rgba(225, 255, 178, .42)",
        "glow": "rgba(200, 255, 122, .22)",
    },
    "physical": {
        "bg1": "#3d4148",
        "bg2": "#8a909b",
        "bg3": "#15171b",
        "accent": "#d9e0ea",
        "accent2": "#f6f8fb",
        "panel": "rgba(42, 45, 51, .74)",
        "panel2": "rgba(78, 83, 92, .64)",
        "line": "rgba(232, 237, 245, .38)",
        "glow": "rgba(217, 224, 234, .18)",
    },
}

ELEMENT_ALIASES = {
    "fire": "pyro",
    "\ubd88": "pyro",
    "water": "hydro",
    "\ubb3c": "hydro",
    "lightning": "electro",
    "\ubc88\uac1c": "electro",
    "ice": "cryo",
    "\uc5bc\uc74c": "cryo",
    "wind": "anemo",
    "\ubc14\ub78c": "anemo",
    "rock": "geo",
    "\ubc14\uc704": "geo",
    "grass": "dendro",
    "\ud480": "dendro",
    "\ubb3c\ub9ac": "physical",
}


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("metadata root must be an object")
    return data


def normalize_element(value: Any) -> str:
    text = str(value or "").strip().casefold().replace(" ", "")
    return ELEMENT_ALIASES.get(text, text if text in THEMES else "physical")


def element_label(element: str) -> str:
    return {
        "pyro": "불 원소",
        "hydro": "물 원소",
        "electro": "번개 원소",
        "cryo": "얼음 원소",
        "anemo": "바람 원소",
        "geo": "바위 원소",
        "dendro": "풀 원소",
        "physical": "물리",
    }.get(element, element.title())


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def file_uri(path_text: Any) -> str:
    if not path_text:
        return ""
    path = Path(str(path_text))
    if not path.exists():
        return ""
    return path.resolve().as_uri()


def css_vars(theme: dict[str, str]) -> str:
    return "\n".join(f"  --{key}: {value};" for key, value in theme.items())


def stars(count: int = 5) -> str:
    return "★" * max(0, min(5, count))


def stat_rows(meta: dict[str, Any]) -> list[tuple[str, str, str | None]]:
    rows = meta.get("stats")
    result: list[tuple[str, str, str | None]] = []
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict):
                result.append((str(row.get("label") or ""), str(row.get("value") or ""), str(row.get("note") or "") or None))
    if result:
        return result[:8]
    target = meta.get("target_stats")
    if isinstance(target, dict):
        return [(str(key), str(value), None) for key, value in target.items()][:8]
    return []


def artifact_cards(meta: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts = meta.get("artifacts")
    if isinstance(artifacts, list):
        return [item for item in artifacts if isinstance(item, dict)][:5]
    artifact = meta.get("artifact")
    if isinstance(artifact, dict) and isinstance(artifact.get("pieces"), list):
        return [item for item in artifact["pieces"] if isinstance(item, dict)][:5]
    return []


def image_tag(src: str, cls: str, alt: str = "") -> str:
    if not src:
        return f'<div class="{cls} placeholder">{esc(alt[:2] or "?")}</div>'
    return f'<img class="{cls}" src="{src}" alt="{esc(alt)}" />'


def render_artifact(item: dict[str, Any], idx: int) -> str:
    src = file_uri(item.get("image_path"))
    substats = item.get("substats") if isinstance(item.get("substats"), list) else []
    substats = [str(x) for x in substats][:4]
    substat_priority = item.get("substat_priority")
    if isinstance(substat_priority, list):
        substat_text = " > ".join(str(x) for x in substat_priority if str(x).strip())
    else:
        substat_text = str(substat_priority or "")
    if not substat_text:
        substat_text = " > ".join(x for x in substats if x)
    main_option = item.get("main_option") or item.get("main_stat") or ""
    return f"""
      <div class="artifact artifact-{idx}">
        <div class="artifact-icon-wrap">
          {image_tag(src, "artifact-icon", item.get("name") or item.get("slot") or "")}
          <div class="artifact-stars">{stars(int(item.get("rarity") or 5))}</div>
          <div class="artifact-level">+{esc(item.get("level") or 20)}</div>
        </div>
        <div class="artifact-main">
          <div class="artifact-slot">{esc(item.get("slot") or item.get("name") or "")}</div>
          <div class="artifact-value">{esc(main_option)}</div>
        </div>
        <div class="artifact-subs">
          <div class="artifact-sub-label">부옵 우선</div>
          <div class="artifact-sub-value">{esc(substat_text)}</div>
        </div>
      </div>
    """


def render_party_html(meta: dict[str, Any], width: int, height: int) -> str:
    chars = meta.get("characters") if isinstance(meta.get("characters"), list) else []
    first_element = chars[0].get("element") if chars and isinstance(chars[0], dict) else None
    element = normalize_element(meta.get("theme_element") or first_element)
    theme = THEMES[element]
    member_html = ""
    for idx, char in enumerate(chars[:4], 1):
        if not isinstance(char, dict):
            continue
        icon = file_uri(char.get("icon_path") or char.get("image_path"))
        member_element = normalize_element(char.get("element") or element)
        member_html += f"""
        <article class="member member-{idx}" data-element="{esc(member_element)}">
          <div class="member-index">0{idx}</div>
          <div class="member-image-frame">
            {image_tag(icon, "member-image", char.get("name") or "")}
          </div>
          <div class="member-body">
            <div class="member-name">{esc(char.get("name") or "")}</div>
            <div class="member-role">{esc(char.get("role") or "")}</div>
            <div class="member-note">{esc(char.get("contribution") or char.get("note") or "")}</div>
            <div class="member-build">{esc(char.get("build") or "")}</div>
          </div>
        </article>
        """

    def panel(title: str, value: Any) -> str:
        return f"""
        <section class="party-panel">
          <div class="party-panel-title">{esc(title)}</div>
          <div class="party-panel-text">{esc(value or "")}</div>
        </section>
        """
    operation_panel = panel("구동 방법", meta.get("operation") or meta.get("playstyle"))
    rotation_panel = panel("로테이션", meta.get("rotation"))
    notes_panel = panel("주의점", meta.get("notes") or meta.get("note"))

    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width={width}, initial-scale=1" />
<style>
:root {{
{css_vars(theme)}
}}
* {{
  box-sizing: border-box;
  font-family: "Pretendard", "Toss Product Sans", "Malgun Gothic", "Noto Sans KR", "Segoe UI", sans-serif;
  font-weight: 900;
  letter-spacing: 0;
}}
body {{ margin: 0; background: #111; }}
.party-report {{
  position: relative;
  width: {width}px;
  height: {height}px;
  overflow: hidden;
  color: #fff;
  background:
    radial-gradient(circle at 22% 25%, var(--glow) 0, transparent 30%),
    radial-gradient(circle at 78% 26%, rgba(255,255,255,.14) 0, transparent 22%),
    linear-gradient(118deg, var(--bg1) 0%, var(--bg2) 54%, var(--bg3) 100%);
}}
.party-report::before {{
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(0,0,0,.18), transparent 45%, rgba(0,0,0,.28));
}}
.party-header {{
  position: absolute;
  left: 48px;
  right: 48px;
  top: 36px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  text-shadow: 0 4px 12px rgba(0,0,0,.54);
}}
.party-title {{
  font-size: 42px;
  line-height: 1.05;
}}
.party-subtitle {{
  margin-top: 8px;
  font-size: 20px;
  color: var(--accent2);
}}
.party-badge {{
  padding: 10px 18px;
  border-radius: 999px;
  background: rgba(0,0,0,.34);
  border: 1px solid var(--line);
  font-size: 18px;
}}
.lineup {{
  position: absolute;
  left: 48px;
  right: 48px;
  top: 130px;
  height: 330px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 22px;
}}
.member {{
  position: relative;
  display: grid;
  grid-template-columns: 128px 1fr;
  gap: 16px;
  padding: 22px;
  border-radius: 18px;
  background: linear-gradient(115deg, var(--panel2), var(--panel));
  border: 1px solid var(--line);
  box-shadow: 0 18px 26px rgba(0,0,0,.24), inset 0 1px 0 rgba(255,255,255,.14);
  overflow: hidden;
}}
.member::before {{
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 7px;
  background: var(--accent);
}}
.member-index {{
  position: absolute;
  right: 18px;
  top: 12px;
  color: rgba(255,255,255,.18);
  font-size: 54px;
}}
.member-image-frame {{
  position: relative;
  z-index: 1;
  width: 124px;
  height: 124px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: rgba(0,0,0,.28);
  border: 1px solid var(--line);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.08);
}}
.member-image {{
  width: 114px;
  height: 114px;
  object-fit: contain;
  filter: drop-shadow(0 10px 12px rgba(0,0,0,.32));
}}
.member-image.placeholder {{
  color: var(--accent2);
  font-size: 42px;
}}
.member-body {{
  position: relative;
  z-index: 1;
  min-width: 0;
  padding-top: 18px;
}}
.member-name {{
  font-size: 29px;
  line-height: 1.05;
}}
.member-role {{
  margin-top: 10px;
  color: var(--accent2);
  font-size: 17px;
}}
.member-note {{
  margin-top: 18px;
  min-height: 56px;
  font-size: 16px;
  line-height: 1.32;
}}
.member-build {{
  margin-top: 14px;
  padding-top: 10px;
  border-top: 1px solid var(--line);
  color: rgba(255,255,255,.78);
  font-size: 15px;
}}
.party-panels {{
  position: absolute;
  left: 48px;
  right: 48px;
  bottom: 44px;
  display: grid;
  grid-template-columns: 1fr 1.25fr .9fr;
  gap: 22px;
}}
.party-panel {{
  min-height: 132px;
  padding: 22px 24px;
  border-radius: 16px;
  background: rgba(0,0,0,.28);
  border: 1px solid var(--line);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.12);
}}
.party-panel-title {{
  color: var(--accent2);
  font-size: 22px;
}}
.party-panel-text {{
  margin-top: 12px;
  font-size: 19px;
  line-height: 1.38;
}}
</style>
</head>
<body>
<main class="party-report">
  <header class="party-header">
    <div>
      <div class="party-title">{esc(meta.get("title") or "")}</div>
      <div class="party-subtitle">{esc(meta.get("subtitle") or "")}</div>
    </div>
    <div class="party-badge">{esc(element_label(element))}</div>
  </header>
  <section class="lineup">
    {member_html}
  </section>
  <section class="party-panels">
    {operation_panel}
    {rotation_panel}
    {notes_panel}
  </section>
</main>
</body>
</html>
"""


def render_html(meta: dict[str, Any], width: int, height: int) -> str:
    if meta.get("card_type") == "party_card":
        return render_party_html(meta, width, height)

    character = meta.get("character") if isinstance(meta.get("character"), dict) else {}
    weapon = meta.get("weapon") if isinstance(meta.get("weapon"), dict) else {}
    artifact = meta.get("artifact") if isinstance(meta.get("artifact"), dict) else {}
    element = normalize_element(meta.get("theme_element") or character.get("element") or meta.get("element"))
    theme = THEMES[element]
    card_src = file_uri(character.get("card_path") or meta.get("card_path") or meta.get("image_path"))
    icon_src = file_uri(character.get("icon_path"))
    weapon_src = file_uri(weapon.get("image_path"))
    art_items = artifact_cards(meta)
    stat_items = stat_rows(meta)
    bottom_stats = meta.get("bottom_stats") if isinstance(meta.get("bottom_stats"), list) else []
    sections = meta.get("sections") if meta.get("show_notes_on_report") and isinstance(meta.get("sections"), list) else []

    stat_html = "\n".join(
        f"""
        <div class="stat-row">
          <div class="stat-label">{esc(label)}</div>
          <div class="stat-value">{esc(value)}</div>
          <div class="stat-note">{esc(note or "")}</div>
        </div>
        """
        for label, value, note in stat_items
    )
    artifact_html = "\n".join(render_artifact(item, idx) for idx, item in enumerate(art_items, 1))
    if not artifact_html:
        artifact_html = '<div class="empty-artifacts">Artifact image data required</div>'

    section_html = ""
    for section in sections[:2]:
        if not isinstance(section, dict):
            continue
        lines = section.get("lines") if isinstance(section.get("lines"), list) else [section.get("value") or ""]
        section_html += f"""
        <div class="note-box">
          <div class="note-title">{esc(section.get("title") or "")}</div>
          <div class="note-text">{esc(" / ".join(str(line) for line in lines if line))}</div>
        </div>
        """

    bottom_html = "\n".join(
        f'<div class="bottom-stat"><span>{esc(item.get("label") if isinstance(item, dict) else "")}</span><strong>{esc(item.get("value") if isinstance(item, dict) else item)}</strong></div>'
        for item in bottom_stats[:8]
    )

    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width={width}, initial-scale=1" />
<style>
:root {{
{css_vars(theme)}
}}
* {{
  box-sizing: border-box;
  font-family: "Pretendard", "Toss Product Sans", "Malgun Gothic", "Noto Sans KR", "Segoe UI", sans-serif;
  font-weight: 900;
  letter-spacing: 0;
}}
body {{
  margin: 0;
  background: #111;
}}
.report {{
  position: relative;
  width: {width}px;
  height: {height}px;
  overflow: hidden;
  color: #fff;
  background:
    radial-gradient(circle at 32% 32%, var(--glow) 0, transparent 28%),
    radial-gradient(circle at 78% 14%, rgba(255,255,255,.16) 0, transparent 16%),
    linear-gradient(118deg, var(--bg1) 0%, var(--bg2) 52%, var(--bg3) 100%);
}}
.report::before {{
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(0,0,0,.18), transparent 35%, rgba(0,0,0,.28));
}}
.bg-card {{
  position: absolute;
  left: 30px;
  top: -80px;
  width: 760px;
  height: 1050px;
  object-fit: cover;
  opacity: .22;
  filter: blur(1px) saturate(1.1);
}}
.left {{
  position: absolute;
  left: 44px;
  top: 36px;
  width: 690px;
  height: 810px;
}}
.identity {{
  position: absolute;
  left: 0;
  top: 0;
  z-index: 3;
  min-width: 430px;
  padding: 18px 22px 20px 22px;
  border-radius: 18px;
  background: rgba(0,0,0,.22);
  border: 1px solid var(--line);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.12);
  text-shadow: 0 4px 12px rgba(0,0,0,.55);
}}
.name-line {{
  display: flex;
  align-items: baseline;
  gap: 18px;
  font-size: 46px;
  line-height: 1;
}}
.element {{
  font-size: 21px;
  color: var(--accent2);
}}
.level {{
  margin-top: 14px;
  font-size: 28px;
}}
.constellation {{
  margin-top: 12px;
  font-size: 28px;
}}
.hero {{
  position: absolute;
  left: 100px;
  top: 214px;
  width: 500px;
  height: 600px;
  object-fit: cover;
  object-position: 50% 30%;
  filter: drop-shadow(0 28px 24px rgba(0,0,0,.42));
}}
.hero.placeholder {{
  display: grid;
  place-items: center;
  background: rgba(255,255,255,.16);
  border-radius: 26px;
  font-size: 76px;
}}
.talents {{
  position: absolute;
  right: 26px;
  top: 430px;
  display: grid;
  gap: 22px;
}}
.talent {{
  width: 74px;
  height: 74px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: rgba(0,0,0,.34);
  border: 2px solid rgba(255,255,255,.34);
  font-size: 28px;
  box-shadow: 0 12px 20px rgba(0,0,0,.22);
}}
.center {{
  position: absolute;
  left: 720px;
  top: 42px;
  width: 442px;
  height: 770px;
}}
.weapon {{
  display: grid;
  grid-template-columns: 144px 1fr;
  gap: 24px;
  align-items: center;
  min-height: 178px;
}}
.weapon-icon {{
  width: 138px;
  height: 138px;
  object-fit: contain;
  filter: drop-shadow(0 14px 18px rgba(0,0,0,.34));
}}
.weapon-icon.placeholder {{
  display: grid;
  place-items: center;
  border-radius: 20px;
  background: rgba(255,255,255,.14);
}}
.weapon-title {{
  font-size: 34px;
  line-height: 1.08;
  text-shadow: 0 4px 12px rgba(0,0,0,.52);
}}
.stars {{
  margin-top: 12px;
  color: #ffd957;
  font-size: 28px;
  text-shadow: 0 3px 8px rgba(0,0,0,.46);
}}
.weapon-chips {{
  display: flex;
  gap: 12px;
  margin-top: 14px;
  flex-wrap: wrap;
}}
.chip {{
  padding: 9px 16px;
  border-radius: 8px;
  background: rgba(0,0,0,.36);
  border: 1px solid var(--line);
  font-size: 20px;
}}
.stats {{
  margin-top: 26px;
  display: grid;
  gap: 16px;
}}
.stat-row {{
  display: grid;
  grid-template-columns: 162px 1fr;
  align-items: center;
  min-height: 54px;
  padding: 0 18px;
  background: linear-gradient(90deg, rgba(0,0,0,.24), rgba(255,255,255,.08));
  border-left: 4px solid var(--accent);
  border-radius: 10px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.16);
}}
.stat-label {{
  color: #fff;
  font-size: 21px;
  white-space: nowrap;
  text-shadow: 0 3px 10px rgba(0,0,0,.42);
}}
.stat-value {{
  text-align: right;
  font-size: 27px;
  text-shadow: 0 4px 12px rgba(0,0,0,.52);
}}
.stat-note {{
  grid-column: 2;
  text-align: right;
  margin-top: -5px;
  color: var(--accent2);
  font-size: 15px;
}}
.note-box {{
  margin-top: 18px;
  padding: 16px 18px;
  border-radius: 12px;
  background: rgba(0,0,0,.24);
  border: 1px solid var(--line);
}}
.note-title {{
  color: var(--accent2);
  font-size: 21px;
}}
.note-text {{
  margin-top: 7px;
  font-size: 18px;
  line-height: 1.35;
}}
.right {{
  position: absolute;
  right: 32px;
  top: 24px;
  width: 574px;
  display: grid;
  gap: 16px;
}}
.artifact {{
  height: 150px;
  display: grid;
  grid-template-columns: 126px 126px 1fr;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 14px;
  background: linear-gradient(90deg, var(--panel2), var(--panel));
  border: 1px solid var(--line);
  box-shadow: 0 14px 24px rgba(0,0,0,.22), inset 0 1px 0 rgba(255,255,255,.12);
}}
.artifact-icon-wrap {{
  position: relative;
  width: 118px;
  height: 118px;
  border-radius: 12px;
  overflow: hidden;
  background: rgba(0,0,0,.2);
}}
.artifact-icon {{
  width: 118px;
  height: 118px;
  object-fit: cover;
}}
.artifact-icon.placeholder {{
  display: grid;
  place-items: center;
  color: var(--accent2);
  font-size: 28px;
}}
.artifact-stars {{
  position: absolute;
  left: 8px;
  bottom: 5px;
  color: #ffd957;
  font-size: 17px;
  text-shadow: 0 2px 6px rgba(0,0,0,.7);
}}
.artifact-level {{
  position: absolute;
  right: 5px;
  bottom: 5px;
  padding: 2px 7px;
  border-radius: 5px;
  background: rgba(0,0,0,.62);
  font-size: 15px;
}}
.artifact-slot {{
  color: var(--accent2);
  font-size: 18px;
}}
.artifact-value {{
  margin-top: 8px;
  font-size: 32px;
  line-height: 1.05;
  text-shadow: 0 4px 10px rgba(0,0,0,.42);
}}
.artifact-subs {{
  min-width: 0;
  display: grid;
  gap: 8px;
}}
.artifact-sub-label {{
  color: var(--accent2);
  font-size: 17px;
}}
.artifact-sub-value {{
  min-width: 0;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(0,0,0,.20);
  border: 1px solid rgba(255,255,255,.20);
  font-size: 17px;
  line-height: 1.25;
}}
.bottom {{
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 54px;
  display: flex;
  justify-content: center;
  gap: 28px;
  align-items: center;
  background: rgba(0,0,0,.28);
  border-top: 1px solid var(--line);
}}
.bottom-stat {{
  display: flex;
  gap: 8px;
  align-items: baseline;
  font-size: 18px;
  color: rgba(255,255,255,.78);
}}
.bottom-stat strong {{
  color: #fff;
  font-size: 24px;
}}
.set-name {{
  display: none;
}}
.empty-artifacts {{
  height: 760px;
  display: grid;
  place-items: center;
  border: 2px dashed var(--line);
  border-radius: 18px;
}}
</style>
</head>
<body>
<main class="report">
  {image_tag(card_src, "bg-card", character.get("name") or "")}
  <section class="left">
    <div class="identity">
      <div class="name-line">
        <div>{esc(character.get("name") or meta.get("title") or "")}</div>
        <div class="element">{esc(character.get("element_label") or element.title())}</div>
      </div>
      <div class="level">{esc(character.get("level") or "")}</div>
      <div class="constellation">{esc(character.get("constellation") or "")}</div>
    </div>
    {image_tag(card_src or icon_src, "hero", character.get("name") or "")}
    <div class="talents">
      <div class="talent">{esc(character.get("normal_talent") or "10")}</div>
      <div class="talent">{esc(character.get("skill_talent") or "10")}</div>
      <div class="talent">{esc(character.get("burst_talent") or "10")}</div>
    </div>
  </section>
  <section class="center">
    <div class="weapon">
      {image_tag(weapon_src, "weapon-icon", weapon.get("name") or "")}
      <div>
        <div class="weapon-title">{esc(weapon.get("name") or "")}</div>
        <div class="stars">{stars(int(weapon.get("rarity") or 5))}</div>
        <div class="weapon-chips">
          <span class="chip">{esc(weapon.get("refinement") or "R1")}</span>
          <span class="chip">{esc(weapon.get("level") or "Lv.90/90")}</span>
          <span class="chip">{esc(weapon.get("main_stat") or "")}</span>
        </div>
      </div>
    </div>
    <div class="stats">
      {stat_html}
    </div>
    {section_html}
  </section>
  <section class="right">
    {artifact_html}
  </section>
  <div class="set-name">{esc(artifact.get("name") or artifact.get("set_name") or "")}</div>
  <section class="bottom">
    {bottom_html}
  </section>
</main>
</body>
</html>
"""


def validate(meta: dict[str, Any], output_override: Path | None = None) -> list[str]:
    errors: list[str] = []
    card_type = meta.get("card_type")
    if card_type not in {"build_card", "build_report", "party_card"}:
        errors.append("card_type must be build_card, build_report, or party_card")
    if not str(meta.get("title") or "").strip():
        errors.append("title must be a non-empty string")
    if card_type == "party_card":
        chars = meta.get("characters")
        if not isinstance(chars, list) or len(chars) != 4:
            errors.append("party_card requires exactly four characters[] entries")
        return errors
    character = meta.get("character")
    if not isinstance(character, dict):
        errors.append("character must be an object")
    elif not str(character.get("name") or "").strip():
        errors.append("character.name must be set")
    weapon = meta.get("weapon")
    if not isinstance(weapon, dict):
        errors.append("weapon must be an object with image_path when available")
    artifacts = artifact_cards(meta)
    if len(artifacts) < 1:
        errors.append("artifacts[] or artifact.pieces[] must contain at least one entry")
    if not output_override and not str(meta.get("output_image_path") or "").strip():
        errors.append("output_image_path must be set when --output is not provided")
    return errors


def write_html(meta: dict[str, Any], html_path: Path, width: int, height: int) -> None:
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(render_html(meta, width, height), encoding="utf-8")


def screenshot_html(html_path: Path, output_path: Path, width: int, height: int) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Playwright is not importable: {exc}") from exc

    errors: list[str] = []
    with sync_playwright() as play:
        launchers = [
            ("chromium", {}),
            ("msedge", {"channel": "msedge"}),
            ("chrome", {"channel": "chrome"}),
        ]
        for name, kwargs in launchers:
            browser = None
            try:
                browser = play.chromium.launch(headless=True, **kwargs)
                page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
                page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
                output_path.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(output_path), full_page=False)
                return name
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{name}: {str(exc).splitlines()[0]}")
            finally:
                if browser:
                    browser.close()
    raise RuntimeError("cannot launch browser for screenshot; " + " | ".join(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description="Render polished HTML/CSS Genshin build report")
    parser.add_argument("metadata_json", type=Path)
    parser.add_argument("--output", type=Path, help="PNG output path; defaults to metadata.output_image_path")
    parser.add_argument("--html-output", type=Path, help="HTML output path; defaults to PNG path with .html suffix")
    parser.add_argument("--width", type=int, default=1800)
    parser.add_argument("--height", type=int, default=900)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--html-only", action="store_true")
    args = parser.parse_args()

    try:
        meta = read_json(args.metadata_json)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: cannot read metadata JSON: {exc}", file=sys.stderr)
        return 2

    errors = validate(meta, args.output)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if args.validate_only:
        print("OK: HTML report metadata is valid")
        return 0

    output_path = args.output or Path(str(meta["output_image_path"]))
    html_path = args.html_output or output_path.with_suffix(".html")
    try:
        write_html(meta, html_path, args.width, args.height)
        if args.html_only:
            print(f"OK: wrote HTML {html_path}")
            return 0
        browser_name = screenshot_html(html_path, output_path, args.width, args.height)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: cannot render HTML report: {exc}", file=sys.stderr)
        return 2

    print(f"OK: rendered {output_path}")
    print(f"OK: wrote HTML {html_path}")
    print(f"OK: browser {browser_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

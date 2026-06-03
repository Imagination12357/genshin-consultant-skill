# Korean Localization Rules

Use this reference whenever generated visual cards contain character, weapon, artifact, artifact-set, element, role, or team names.

## Default Display Language

- Final user-facing text and every rendered card should use Korean display names by default.
- Keep English canonical names only in IDs, source IDs, paths, URLs, and internal cache keys.
- Do not mix English names into card titles, character slots, weapon rankings, artifact labels, or party subtitles when a Korean name is known.

## Required Workflow

Before rendering cards:

1. Query the asset cache as usual.
2. Build card metadata with the best available names.
3. Run `scripts/localize_card_metadata.py` on every card metadata JSON.
4. Render from the localized metadata, not the unlocalized draft.

Example:

```powershell
$env:PYTHONUTF8='1'
python "/absolute/path/to/genshin_agent/genshin-consultant/scripts/localize_card_metadata.py" `
  "/absolute/path/to/genshin_agent/generated/visuals/example/build.json" `
  "/absolute/path/to/genshin_agent/generated/visuals/example/weapons.json" `
  --in-place
```

## Name Source Priority

1. Korean aliases from `assets/genshin-assets/current/index.json`.
2. Official Korean HoYoverse / HoYoLAB / in-game text when available.
3. Fandom/wiki Korean aliases when present in the cache.
4. The built-in fallback map in `scripts/localize_card_metadata.py`.
5. If no reliable Korean name exists, use a conservative Korean transliteration and mark it as `가칭` in the text answer, not inside tiny card labels.

## Renderer Requirements

- Party cards should show Korean character names and Korean element badges such as `불 원소`, not `Pyro`.
- Weapon cards should show Korean weapon names such as `천공의 두루마리`, not `Skyward Atlas`.
- Artifact cards should show Korean set/piece names such as `하늘의 은총`, not `Celestial Gift`.
- English may remain in source footers because source IDs are internal provenance, but card content should be Korean.


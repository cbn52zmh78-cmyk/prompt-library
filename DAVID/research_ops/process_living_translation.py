"""CLI handoff processor for LIVING translation browser pass."""
import json
import os
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_PATH = os.path.join(ROOT, "research_ops", "outputs", "LIVING_translation_raw.json")

REGISTRY_META = {
    "spanish": {
        "name": "Spanish",
        "family": "Romance > Indo-European",
        "script": "Latin alphabet",
        "notes": "Translation service profile; LatAm/Castilian variants. Neutral LA default for broad reach.",
    },
    "french": {
        "name": "French",
        "family": "Romance > Indo-European",
        "script": "Latin alphabet",
        "notes": "Translation service profile; European/Canadian variants.",
    },
    "italian": {
        "name": "Italian",
        "family": "Romance > Indo-European",
        "script": "Latin alphabet",
        "notes": "Translation service profile; standard Italian.",
    },
    "german": {
        "name": "German",
        "family": "West Germanic > Indo-European",
        "script": "Latin alphabet (umlauts, ß)",
        "notes": "Translation service profile; standard German (Hochdeutsch).",
    },
    "japanese": {
        "name": "Japanese",
        "family": "Japonic",
        "script": "Kanji + hiragana + katakana",
        "notes": "Translation service profile; keigo critical for documents. HIGH-VALUE SERIES: keigo_notes.",
    },
    "mandarin": {
        "name": "Mandarin Chinese",
        "family": "Sino-Tibetan",
        "script": "Chinese characters (simplified/traditional); pinyin romanization",
        "notes": "Translation service profile; script variant must match audience (PRC vs Taiwan/HK).",
    },
    "arabic": {
        "name": "Modern Standard Arabic",
        "family": "Semitic > Afro-Asiatic",
        "script": "Arabic abjad (RTL)",
        "notes": "Translation service profile; MSA for formal docs. HIGH-VALUE SERIES: diglossia_note.",
    },
    "portuguese": {
        "name": "Portuguese",
        "family": "Romance > Indo-European",
        "script": "Latin alphabet",
        "notes": "Translation service profile; Brazilian/European variants.",
    },
}


def build_lesson_plan(slug: str, profile: dict) -> str:
    name = REGISTRY_META[slug]["name"]
    lines = [
        f"# {name} — Tutoring Lesson Plan (Stub)",
        "",
        f"Generated from LIVING translation browser pass ({date.today().isoformat()}).",
        "",
        "## Pronunciation hooks",
        "",
    ]
    for hook in profile.get("tutoring_pronunciation_hooks", []):
        lines.append(f"- {hook}")

    if slug == "japanese" and profile.get("keigo_notes"):
        lines.extend(["", "## Keigo (series priority)", "", profile["keigo_notes"]])
    if slug == "arabic" and profile.get("diglossia_note"):
        lines.extend(["", "## Diglossia (series priority)", "", profile["diglossia_note"]])

    lines.extend(["", "## Status", "", "Stub — expand into full lesson sequence.", ""])
    return "\n".join(lines)


def main() -> None:
    with open(RAW_PATH, encoding="utf-8") as f:
        data = json.load(f)

    gaps: list[str] = []
    series_flags: list[str] = []

    for slug, profile in data.items():
        if slug not in REGISTRY_META:
            gaps.append(f"{slug}: unknown slug — skipped")
            continue

        lang_dir = os.path.join(ROOT, "languages", "living", slug)
        os.makedirs(os.path.join(lang_dir, "tutoring"), exist_ok=True)

        profile_path = os.path.join(lang_dir, "translation_profile.json")
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        print(f"Saved {profile_path}")

        lesson_path = os.path.join(lang_dir, "tutoring", "lesson_plan.md")
        with open(lesson_path, "w", encoding="utf-8") as f:
            f.write(build_lesson_plan(slug, profile))
        print(f"Saved {lesson_path}")

        if slug == "japanese" and profile.get("keigo_notes"):
            series_flags.append("japanese: keigo_notes")
        if slug == "arabic" and profile.get("diglossia_note"):
            series_flags.append("arabic: diglossia_note")
        if not profile.get("orthography_notes") and slug in ("japanese", "mandarin", "arabic"):
            gaps.append(f"{slug}: orthography_notes empty")

    registry_path = os.path.join(ROOT, "data", "language_registry.json")
    with open(registry_path, encoding="utf-8") as f:
        registry = json.load(f)

    existing_slugs = {lang["slug"] for lang in registry["languages"]}
    added: list[str] = []
    for slug, meta in REGISTRY_META.items():
        if slug in existing_slugs:
            gaps.append(f"{slug}: already in registry — skipped duplicate")
            continue
        registry["languages"].append(
            {
                "id": slug,
                "name": meta["name"],
                "slug": slug,
                "status": "living",
                "revival_tier": "active",
                "family": meta["family"],
                "period": "present",
                "script": meta["script"],
                "corpus_size": "native_speaker",
                "decipherment": "native",
                "history_links": [],
                "research_type": "translation_service",
                "notes": meta["notes"],
            }
        )
        added.append(slug)

    registry["updated"] = date.today().isoformat()
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
    print(f"Registry updated: added {added}")

    gaps_path = os.path.join(ROOT, "research_ops", "outputs", "LIVING_translation_gaps.md")
    with open(gaps_path, "w", encoding="utf-8") as f:
        f.write("# LIVING Translation Pass — Gaps & Flags\n\n")
        f.write(f"Processed: {date.today().isoformat()}\n\n")
        f.write("## Series planning flags (high-value tutoring content)\n\n")
        for flag in series_flags:
            f.write(f"- **{flag}**\n")
        f.write("\n## Schema / follow-up gaps\n\n")
        if gaps:
            for gap in gaps:
                f.write(f"- {gap}\n")
        else:
            f.write("- None\n")
        f.write("\n## Italian/German variant_notes\n\n")
        f.write(
            "- `latin_american` / `castilian` keys present but empty "
            "(schema carryover; N/A for these languages)\n"
        )
    print(f"Saved {gaps_path}")


if __name__ == "__main__":
    main()
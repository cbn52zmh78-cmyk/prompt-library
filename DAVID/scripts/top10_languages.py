"""Top-10 living languages by total speakers (Ethnologue 2026) — loader and profile sync.

Source of truth: DAVID/data/top10_languages_ranking_2026.json
Per-language artifacts: DAVID/languages/living/<slug>/
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from _paths import DAVID_ROOT, LANGUAGES_DIR, REGISTRY_FILE

RANKING_FILE = DAVID_ROOT / "data" / "top10_languages_ranking_2026.json"
LIVING_DIR = LANGUAGES_DIR / "living"
RESEARCH_DOC = DAVID_ROOT / "research" / "top10_languages_ethnologue_2026_v1.md"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_ranking() -> dict[str, Any]:
    if not RANKING_FILE.is_file():
        return {}
    return _read_json(RANKING_FILE)


def list_top10() -> list[dict[str, Any]]:
    data = load_ranking()
    langs = data.get("languages") or []
    return sorted(langs, key=lambda x: x.get("rank", 99))


def get_by_rank(rank: int) -> dict[str, Any] | None:
    return next((l for l in list_top10() if l.get("rank") == rank), None)


def get_by_slug(slug: str) -> dict[str, Any] | None:
    key = slug.strip().lower()
    return next((l for l in list_top10() if l.get("slug") == key), None)


def universal_resources() -> list[dict[str, Any]]:
    return list(load_ranking().get("universal_pronunciation_resources") or [])


def methodology() -> dict[str, Any]:
    return dict(load_ranking().get("_methodology") or {})


def language_dir(slug: str) -> Path:
    return LIVING_DIR / slug


def pronunciation_profile_path(slug: str) -> Path:
    return language_dir(slug) / "pronunciation" / "pronunciation_profile.json"


def profile_path(slug: str) -> Path:
    return language_dir(slug) / "profile.json"


def build_pronunciation_profile(entry: dict[str, Any]) -> dict[str, Any]:
    slug = entry["slug"]
    return {
        "language": slug,
        "status": "living",
        "research_type": "pronunciation",
        "ingested_from": "data/top10_languages_ranking_2026.json",
        "ingested_at": load_ranking().get("_captured", "2026-06-29"),
        "ethnologue": {
            "rank_2026": entry["rank"],
            "total_speakers": entry["total_speakers"],
            "total_speakers_display": entry["total_speakers_display"],
            "native_l1": entry.get("native_l1"),
            "native_l1_display": entry.get("native_l1_display"),
            "l2_dominant": entry.get("l2_dominant", False),
            "iso639_1": entry.get("iso639_1"),
            "forvo_code": entry.get("forvo_code"),
        },
        "family": entry.get("family"),
        "script": entry.get("script"),
        "primary_regions": entry.get("primary_regions") or [],
        "major_varieties": entry.get("major_varieties") or [],
        "phonology_highlights": entry.get("phonology_highlights") or [],
        "dialect_notes": entry.get("dialect_notes"),
        "pronunciation_resources": entry.get("pronunciation_resources") or {},
        "universal_resources": [r["id"] for r in universal_resources()],
        "grok_imagine_guidance": entry.get("grok_imagine_guidance", ""),
        "tutoring_hooks": entry.get("tutoring_hooks") or [],
        "phonology_status": "attested_native",
        "ipa_coverage": "full",
        "sources": [
            {"name": "Ethnologue 2026", "url": "https://www.ethnologue.com/"},
            {"name": "Grok browser research pass", "path": str(RESEARCH_DOC)},
        ],
    }


def build_profile(entry: dict[str, Any]) -> dict[str, Any]:
    slug = entry["slug"]
    return {
        "id": entry["id"],
        "name": entry["name"],
        "slug": slug,
        "status": "living",
        "revival_tier": "active",
        "research_type": "living_top10",
        "top10_rank_2026": entry["rank"],
        "family": entry.get("family"),
        "script": entry.get("script"),
        "total_speakers": entry["total_speakers"],
        "total_speakers_display": entry["total_speakers_display"],
        "native_l1_display": entry.get("native_l1_display"),
        "primary_regions": entry.get("primary_regions") or [],
        "major_varieties": entry.get("major_varieties") or [],
        "pronunciation_profile": f"languages/living/{slug}/pronunciation/pronunciation_profile.json",
        "profile_path": f"languages/living/{slug}/profile.json",
    }


def build_translation_stub(entry: dict[str, Any]) -> dict[str, Any]:
    slug = entry["slug"]
    return {
        "language": slug,
        "status": "living",
        "research_type": "translation_service",
        "top10_rank_2026": entry["rank"],
        "variant_notes": {
            "major_varieties": entry.get("major_varieties") or [],
            "dialect_notes": entry.get("dialect_notes"),
        },
        "register_system": "Formal vs informal varies by language; see major_varieties for regional targets.",
        "translationese_traps": [
            "Literal calques from English",
            "Wrong regional variety for target audience",
            "Ignoring diglossia or script conventions where applicable",
        ],
        "tutoring_pronunciation_hooks": entry.get("tutoring_hooks") or [],
        "professional_resources": list((entry.get("pronunciation_resources") or {}).values()),
        "orthography_notes": entry.get("script", ""),
        "ingested_from": "data/top10_languages_ranking_2026.json",
        "ingested_at": load_ranking().get("_captured", "2026-06-29"),
    }


def build_lesson_plan_stub(entry: dict[str, Any]) -> str:
    hooks = entry.get("tutoring_hooks") or []
    hook_lines = "\n".join(f"- {h}" for h in hooks)
    resources = entry.get("pronunciation_resources") or {}
    res_lines = "\n".join(f"- [{k}]({v})" for k, v in resources.items())
    return f"""# {entry['name']} — Tutoring Lesson Plan

Generated from Top-10 Languages Ethnologue 2026 pass ({load_ranking().get('_captured', '2026-06-29')}).

**Rank:** #{entry['rank']} globally ({entry['total_speakers_display']} total speakers)

## Pronunciation hooks

{hook_lines}

## Primary resources

{res_lines}

## Status

Stub — expand into full lesson sequence. Pronunciation profile: `pronunciation/pronunciation_profile.json`.
"""


def sync_language_files(entry: dict[str, Any], *, force_translation: bool = False) -> list[str]:
    """Materialize profile, pronunciation, tutoring stub for one language. Returns paths written."""
    slug = entry["slug"]
    root = language_dir(slug)
    pron_dir = root / "pronunciation"
    tutor_dir = root / "tutoring"
    pron_dir.mkdir(parents=True, exist_ok=True)
    tutor_dir.mkdir(parents=True, exist_ok=True)

    written: list[str] = []

    profile_file = profile_path(slug)
    profile_file.write_text(
        json.dumps(build_profile(entry), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    written.append(str(profile_file))

    pron_file = pronunciation_profile_path(slug)
    pron_file.write_text(
        json.dumps(build_pronunciation_profile(entry), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    written.append(str(pron_file))

    lesson_file = tutor_dir / "lesson_plan.md"
    if not lesson_file.exists() or lesson_file.read_text(encoding="utf-8").strip().startswith("# Mandarin"):
        lesson_file.write_text(build_lesson_plan_stub(entry), encoding="utf-8")
        written.append(str(lesson_file))
    elif "Top-10 Languages" not in lesson_file.read_text(encoding="utf-8"):
        lesson_file.write_text(build_lesson_plan_stub(entry), encoding="utf-8")
        written.append(str(lesson_file))

    trans_file = root / "translation_profile.json"
    if not trans_file.exists() or force_translation:
        trans_file.write_text(
            json.dumps(build_translation_stub(entry), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        written.append(str(trans_file))

    research_dir = root / "research" / "brain"
    research_dir.mkdir(parents=True, exist_ok=True)
    scrape_file = research_dir / "latest_scrape.json"
    scrape_file.write_text(
        json.dumps(
            {
                "slug": slug,
                "source": "top10_languages_ranking_2026",
                "captured": load_ranking().get("_captured"),
                "rank": entry["rank"],
                "ethnologue_summary": {
                    "total_speakers_display": entry["total_speakers_display"],
                    "native_l1_display": entry.get("native_l1_display"),
                    "family": entry.get("family"),
                },
                "pronunciation_notes": entry.get("phonology_highlights") or [],
                "resources": entry.get("pronunciation_resources") or {},
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    written.append(str(scrape_file))

    return written


def sync_all_top10(*, force_translation: bool = False) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for entry in list_top10():
        out[entry["slug"]] = sync_language_files(entry, force_translation=force_translation)
    return out


def update_registry() -> dict[str, Any]:
    """Merge top-10 metadata into language_registry.json."""
    registry = _read_json(REGISTRY_FILE)
    languages: list[dict[str, Any]] = list(registry.get("languages") or [])
    by_slug = {e["slug"]: e for e in languages}

    added = 0
    updated = 0
    for entry in list_top10():
        slug = entry["slug"]
        patch = {
            "top10_rank_2026": entry["rank"],
            "total_speakers_display": entry["total_speakers_display"],
            "native_l1_display": entry.get("native_l1_display"),
            "profile_path": f"languages/living/{slug}/profile.json",
            "pronunciation_profile": f"languages/living/{slug}/pronunciation/pronunciation_profile.json",
            "phonology_status": "attested_native",
            "ipa_coverage": "full",
        }
        if slug in by_slug:
            by_slug[slug].update(patch)
            if not by_slug[slug].get("tutoring_path"):
                by_slug[slug]["tutoring_path"] = f"languages/living/{slug}/tutoring/lesson_plan.md"
            if not by_slug[slug].get("translation_profile"):
                by_slug[slug]["translation_profile"] = f"languages/living/{slug}/translation_profile.json"
            updated += 1
        else:
            new_entry = {
                "id": entry["id"],
                "name": entry["name"],
                "slug": slug,
                "status": "living",
                "revival_tier": "active",
                "family": entry.get("family", ""),
                "research_type": "living_top10",
                "translation_profile": f"languages/living/{slug}/translation_profile.json",
                "tutoring_path": f"languages/living/{slug}/tutoring/lesson_plan.md",
                **patch,
            }
            languages.append(new_entry)
            by_slug[slug] = new_entry
            added += 1

    registry["languages"] = sorted(languages, key=lambda e: (e.get("top10_rank_2026") or 999, e["name"]))
    registry["total_languages"] = len(languages)
    registry["updated"] = load_ranking().get("_captured", "2026-06-29")
    registry["top10_ranking_file"] = "data/top10_languages_ranking_2026.json"
    registry["version"] = "2.1"

    REGISTRY_FILE.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"added": added, "updated": updated, "total": len(languages)}


def pronunciation_guidance_for_prompt(slug: str) -> str | None:
    """Compact clause for Grok native AV / tutor lip-sync prompts."""
    entry = get_by_slug(slug)
    if not entry:
        pron = pronunciation_profile_path(slug)
        if pron.is_file():
            data = _read_json(pron)
            return data.get("grok_imagine_guidance")
        return None
    parts = [
        f"LANGUAGE DNA [{slug}]: {entry['name']} — {entry.get('dialect_notes', '')}".strip(),
        entry.get("grok_imagine_guidance", ""),
    ]
    hooks = entry.get("tutoring_hooks") or []
    if hooks:
        parts.append("Key phonology: " + "; ".join(hooks[:4]))
    return " ".join(p for p in parts if p)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Top-10 languages sync and lookup.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")
    sub.add_parser("sync")

    show = sub.add_parser("show")
    show.add_argument("slug")

    prompt = sub.add_parser("prompt")
    prompt.add_argument("slug")

    args = parser.parse_args()
    if args.cmd == "list":
        for e in list_top10():
            print(f"  #{e['rank']:2d}  {e['name']:<22}  {e['total_speakers_display']:>12}  ({e['slug']})")
        return 0
    if args.cmd == "sync":
        files = sync_all_top10()
        reg = update_registry()
        print(f"Synced {len(files)} languages; registry +{reg['added']} / ~{reg['updated']} updated (total {reg['total']})")
        return 0
    if args.cmd == "show":
        entry = get_by_slug(args.slug)
        if not entry:
            print(f"Not in top 10: {args.slug}")
            return 1
        print(json.dumps(entry, indent=2, ensure_ascii=False))
        return 0
    if args.cmd == "prompt":
        clause = pronunciation_guidance_for_prompt(args.slug)
        print(clause or f"No guidance for {args.slug}")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
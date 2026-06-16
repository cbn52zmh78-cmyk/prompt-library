"""DAVID Brain — orchestrates deep linguistic scrapes per language."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .parsers import extract_phonology_keywords
from .sources import (
    corpus_lemma_titles,
    fetch_wikidata,
    fetch_wikipedia,
    fetch_wiktionary,
    load_wiki_map,
)

DAVID_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_FILE = DAVID_ROOT / "data" / "language_registry.json"
BRAIN_CACHE = DAVID_ROOT / "data" / "brain_cache"
SCRAPE_LOG = BRAIN_CACHE / "scrape_log.json"


def _load_registry() -> dict:
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))


def _registry_entry(slug: str) -> dict:
    data = _load_registry()
    entry = next((e for e in data["languages"] if e["slug"] == slug), None)
    if not entry:
        raise ValueError(f"Unknown language slug: {slug}")
    return entry


def _language_dir(slug: str, status: str) -> Path:
    return DAVID_ROOT / "languages" / status / slug


def _corpus_lemmas(slug: str, status: str) -> list[str]:
    corpus_file = _language_dir(slug, status) / "corpus" / "known_texts.json"
    if not corpus_file.exists():
        return []
    corpus = json.loads(corpus_file.read_text(encoding="utf-8"))
    lemmas: list[str] = []
    for text in corpus.get("texts", []):
        lemmas.extend(corpus_lemma_titles(text.get("transliteration", "")))
    return list(dict.fromkeys(lemmas))


def scrape_language(slug: str, *, deep: bool = False) -> dict[str, Any]:
    entry = _registry_entry(slug)
    wiki_map = load_wiki_map()
    mapping = wiki_map.get(slug)
    if not mapping:
        raise ValueError(f"No wiki mapping for {slug}. Add to data/wiki_language_map.json")

    errors: list[str] = []
    result: dict[str, Any] = {
        "slug": slug,
        "name": entry["name"],
        "status": entry["status"],
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "deep": deep,
        "sources_used": [],
        "errors": errors,
    }

    # Wikipedia
    try:
        wp = fetch_wikipedia(mapping["wikipedia"])
        wikitext = wp.pop("_wikitext", "")
        wp["phonology_keywords"] = extract_phonology_keywords(wp.get("extract", "") + wikitext[:8000])
        result["wikipedia"] = wp
        result["sources_used"].append("wikipedia")
    except Exception as exc:
        errors.append(f"wikipedia: {exc}")

    # Wikidata
    if mapping.get("wikidata"):
        try:
            result["wikidata"] = fetch_wikidata(mapping["wikidata"])
            result["sources_used"].append("wikidata")
        except Exception as exc:
            errors.append(f"wikidata: {exc}")

    # Wiktionary — language page + corpus lemmas in deep mode
    extra: list[str] = []
    if deep:
        extra = _corpus_lemmas(slug, entry["status"])
    try:
        result["wiktionary"] = fetch_wiktionary(
            mapping["wiktionary"],
            extra,
            mapping.get("wiktionary_fallbacks"),
        )
        result["sources_used"].append("wiktionary")
    except Exception as exc:
        errors.append(f"wiktionary: {exc}")

    # Accent / quality summary
    ipa_all = []
    if "wiktionary" in result:
        ipa_all.extend(result["wiktionary"].get("ipa_entries", []))
    if "wikidata" in result:
        for stmt in result["wikidata"].get("ipa_statements", []):
            ipa_all.append(
                {
                    "ipa": stmt["value"],
                    "accent": "wikidata",
                    "quality": "scholarly_ipa",
                    "language_code": "",
                }
            )
    result["pronunciation_summary"] = _summarize_pronunciation(ipa_all)
    result["etymology_count"] = len(result.get("wiktionary", {}).get("etymology_blocks", []))

    _persist(slug, entry["status"], result)
    _append_log(slug, result)
    return result


def _summarize_pronunciation(ipa_entries: list[dict[str, str]]) -> dict[str, Any]:
    by_quality: dict[str, list] = {}
    by_accent: dict[str, list] = {}
    for e in ipa_entries:
        q = e.get("quality", "unknown")
        a = e.get("accent", "unspecified")
        by_quality.setdefault(q, []).append(e.get("ipa"))
        by_accent.setdefault(a, []).append(e.get("ipa"))
    return {
        "total_ipa_entries": len(ipa_entries),
        "by_quality": {k: v[:6] for k, v in by_quality.items()},
        "by_accent": {k: v[:4] for k, v in by_accent.items()},
        "accent_count": len(by_accent),
    }


def _persist(slug: str, status: str, result: dict[str, Any]) -> Path:
    lang_dir = _language_dir(slug, status)
    brain_dir = lang_dir / "research" / "brain"
    brain_dir.mkdir(parents=True, exist_ok=True)

    out_file = brain_dir / "latest_scrape.json"
    out_file.write_text(json.dumps(result, indent=2), encoding="utf-8")

    BRAIN_CACHE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    cache_file = BRAIN_CACHE / f"{stamp}_{slug}.json"
    cache_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return out_file


def _append_log(slug: str, result: dict[str, Any]) -> None:
    BRAIN_CACHE.mkdir(parents=True, exist_ok=True)
    log: list = []
    if SCRAPE_LOG.exists():
        log = json.loads(SCRAPE_LOG.read_text(encoding="utf-8"))
    log.append(
        {
            "slug": slug,
            "scraped_at": result["scraped_at"],
            "sources": result["sources_used"],
            "errors": result["errors"],
            "ipa_count": result.get("pronunciation_summary", {}).get("total_ipa_entries", 0),
        }
    )
    SCRAPE_LOG.write_text(json.dumps(log[-200:], indent=2), encoding="utf-8")


def scrape_batch(*, tier: str | None = None, deep: bool = False) -> list[dict[str, Any]]:
    data = _load_registry()
    entries = data["languages"]
    if tier:
        entries = [e for e in entries if e.get("revival_tier") == tier]
    results = []
    for entry in entries:
        try:
            results.append(scrape_language(entry["slug"], deep=deep))
        except Exception as exc:
            results.append({"slug": entry["slug"], "errors": [str(exc)]})
    return results
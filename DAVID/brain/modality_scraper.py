"""DAVID Scraper 2 — public-source ingestion for communication modalities."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .modality_parsers import (
    build_modality_summary,
    extract_category_keywords,
    extract_wikidata_modality_claims,
    flag_uncertain_claims,
    parse_script_sections,
)
from .parsers import parse_etymology_blocks, parse_pronunciation_section
from .sources import fetch_wikidata, fetch_wikipedia, fetch_wiktionary

DAVID_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_FILE = DAVID_ROOT / "data" / "communication_modality_registry.json"
LANGUAGE_REGISTRY_FILE = DAVID_ROOT / "data" / "language_registry.json"
WIKI_MAP_FILE = DAVID_ROOT / "data" / "wiki_modality_map.json"
MODALITIES_ROOT = DAVID_ROOT / "communication-modalities"
LANGUAGES_ROOT = DAVID_ROOT / "languages"
MODALITY_CACHE = DAVID_ROOT / "data" / "brain_cache"
MODALITY_LOG = MODALITY_CACHE / "modality_scrape_log.json"


def _load_registry() -> dict[str, Any]:
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))


def _load_wiki_map() -> dict[str, dict[str, Any]]:
    return json.loads(WIKI_MAP_FILE.read_text(encoding="utf-8"))


def _registry_topic(slug: str) -> dict[str, Any]:
    data = _load_registry()
    topic = next((t for t in data["topics"] if t["slug"] == slug), None)
    if not topic:
        raise ValueError(f"Unknown modality slug: {slug}")
    return topic


def _topic_dir(category: str, slug: str) -> Path:
    return MODALITIES_ROOT / category / slug


def _scaffold_profile(topic: dict[str, Any]) -> None:
    root = _topic_dir(topic["category"], topic["slug"])
    root.mkdir(parents=True, exist_ok=True)
    (root / "research" / "brain").mkdir(parents=True, exist_ok=True)

    profile_path = root / "profile.json"
    profile = {
        "id": topic["slug"],
        "name": topic["name"],
        "category": topic["category"],
        "priority": topic.get("priority", "medium"),
        "notes": topic.get("notes", ""),
        "language_corpus_links": topic.get("language_corpus_links", []),
        "modality_links": topic.get("modality_links", []),
        "source_policy": "public_only",
        "licenses": ["CC BY-SA 3.0 (Wikipedia/Wiktionary)", "CC0 (Wikidata)"],
    }
    profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

    notes_path = root / "research" / "notes.md"
    if not notes_path.exists():
        cat_label = _load_registry()["categories"][topic["category"]]["label"]
        notes_path.write_text(
            f"# {topic['name']} — research notes\n\n"
            f"Category: **{cat_label}**\n\n"
            f"Public sources only. Cite retrieval date and license.\n",
            encoding="utf-8",
        )


def scrape_modality(slug: str, *, deep: bool = False) -> dict[str, Any]:
    topic = _registry_topic(slug)
    mapping = _load_wiki_map().get(slug)
    if not mapping:
        raise ValueError(f"No wiki mapping for modality {slug}. Add to data/wiki_modality_map.json")

    _scaffold_profile(topic)
    category = topic["category"]
    errors: list[str] = []
    retrieved_at = datetime.now(timezone.utc).isoformat()

    result: dict[str, Any] = {
        "slug": slug,
        "name": topic["name"],
        "category": category,
        "category_label": _load_registry()["categories"][category]["label"],
        "scraped_at": retrieved_at,
        "retrieval_date": retrieved_at[:10],
        "deep": deep,
        "source_policy": "public_only",
        "licenses": {
            "wikipedia": "CC BY-SA 3.0",
            "wiktionary": "CC BY-SA 3.0",
            "wikidata": "CC0",
        },
        "sources_used": [],
        "citations": [],
        "errors": errors,
    }

    wikitext = ""
    combined_text = ""

    # Wikipedia
    try:
        wp = fetch_wikipedia(mapping["wikipedia"])
        wikitext = wp.pop("_wikitext", "")
        combined_text = wp.get("extract", "") + wikitext[:12000]
        wp["modality_keywords"] = extract_category_keywords(combined_text, category)
        wp["retrieved_at"] = retrieved_at
        wp["citation"] = {
            "source": "Wikipedia",
            "title": mapping["wikipedia"].replace("_", " "),
            "url": wp.get("url", ""),
            "retrieved": retrieved_at[:10],
            "license": "CC BY-SA 3.0",
        }
        if category == "writing-systems":
            wp["script_sections"] = parse_script_sections(wikitext)
        result["wikipedia"] = wp
        result["sources_used"].append("wikipedia")
        result["citations"].append(wp["citation"])
    except Exception as exc:
        errors.append(f"wikipedia: {exc}")

    # Wikidata
    if mapping.get("wikidata"):
        try:
            wd = fetch_wikidata(mapping["wikidata"])
            entity_claims = _fetch_wikidata_entity(mapping["wikidata"])
            wd["modality_claims"] = extract_wikidata_modality_claims(entity_claims, category)
            wd["retrieved_at"] = retrieved_at
            wd["citation"] = {
                "source": "Wikidata",
                "qid": mapping["wikidata"],
                "url": f"https://www.wikidata.org/wiki/{mapping['wikidata']}",
                "retrieved": retrieved_at[:10],
                "license": "CC0",
            }
            result["wikidata"] = wd
            result["sources_used"].append("wikidata")
            result["citations"].append(wd["citation"])
        except Exception as exc:
            errors.append(f"wikidata: {exc}")

    # Wiktionary (when mapped)
    wikt_title = mapping.get("wiktionary")
    if wikt_title:
        try:
            wt = fetch_wiktionary(
                wikt_title,
                None,
                mapping.get("wiktionary_fallbacks"),
            )
            wt["retrieved_at"] = retrieved_at
            wt["citation"] = {
                "source": "Wiktionary",
                "title": wikt_title,
                "url": f"https://en.wiktionary.org/wiki/{wikt_title.replace(' ', '_')}",
                "retrieved": retrieved_at[:10],
                "license": "CC BY-SA 3.0",
            }
            result["wiktionary"] = wt
            result["sources_used"].append("wiktionary")
            result["citations"].append(wt["citation"])
        except Exception as exc:
            errors.append(f"wiktionary: {exc}")

    preset_flags = mapping.get("uncertainty_flags", [])
    result["uncertainty_flags"] = flag_uncertain_claims(combined_text, preset_flags)
    result["modality_summary"] = build_modality_summary(
        category=category,
        wikipedia=result.get("wikipedia"),
        wikidata=result.get("wikidata"),
        wiktionary=result.get("wiktionary"),
        uncertainty_flags=result["uncertainty_flags"],
    )

    if deep and wikitext:
        result["deep_sections"] = {
            "etymology_blocks": parse_etymology_blocks(wikitext)[:6],
            "pronunciation_notes": parse_pronunciation_section(wikitext)[:4],
        }

    corpus_links = topic.get("language_corpus_links", [])
    modality_links = topic.get("modality_links", [])
    if corpus_links or modality_links:
        result["corpus_cross_links"] = _build_corpus_cross_links(corpus_links, modality_links)

    _persist(topic["category"], slug, result)
    _append_log(slug, result)
    return result


def _load_language_registry() -> list[dict[str, Any]]:
    return json.loads(LANGUAGE_REGISTRY_FILE.read_text(encoding="utf-8"))["languages"]


def _language_brain_path(slug: str, status: str) -> Path:
    return LANGUAGES_ROOT / status / slug / "research" / "brain" / "latest_scrape.json"


def _build_corpus_cross_links(
    language_slugs: list[str],
    modality_slugs: list[str],
) -> dict[str, Any]:
    """Link modality scrape to DAVID language brain data and sibling modality topics."""
    languages: list[dict[str, Any]] = []
    registry = {e["slug"]: e for e in _load_language_registry()}

    for slug in language_slugs:
        entry = registry.get(slug)
        if not entry:
            languages.append({"slug": slug, "linked": False, "reason": "not_in_registry"})
            continue
        brain_path = _language_brain_path(slug, entry["status"])
        link: dict[str, Any] = {
            "slug": slug,
            "name": entry["name"],
            "status": entry["status"],
            "script": entry.get("script", ""),
            "decipherment": entry.get("decipherment", ""),
            "brain_scrape_path": str(brain_path.relative_to(DAVID_ROOT)).replace("\\", "/"),
            "linked": brain_path.exists(),
        }
        if brain_path.exists():
            brain = json.loads(brain_path.read_text(encoding="utf-8"))
            link["brain_scraped_at"] = brain.get("scraped_at")
            link["brain_sources"] = brain.get("sources_used", [])
            link["ipa_count"] = brain.get("pronunciation_summary", {}).get("total_ipa_entries", 0)
            wp = brain.get("wikipedia", {})
            link["wikipedia_url"] = wp.get("url", "")
            link["phonology_keywords"] = wp.get("phonology_keywords", [])[:8]
        languages.append(link)

    modalities: list[dict[str, Any]] = []
    for mslug in modality_slugs:
        try:
            mtopic = _registry_topic(mslug)
        except ValueError:
            modalities.append({"slug": mslug, "linked": False, "reason": "not_in_modality_registry"})
            continue
        mpath = _topic_dir(mtopic["category"], mslug) / "research" / "brain" / "latest_scrape.json"
        mlink: dict[str, Any] = {
            "slug": mslug,
            "name": mtopic["name"],
            "category": mtopic["category"],
            "modality_scrape_path": str(mpath.relative_to(DAVID_ROOT)).replace("\\", "/"),
            "linked": mpath.exists(),
        }
        if mpath.exists():
            mdata = json.loads(mpath.read_text(encoding="utf-8"))
            mlink["modality_scraped_at"] = mdata.get("scraped_at")
            mlink["uncertainty_flags"] = len(mdata.get("uncertainty_flags", []))
        modalities.append(mlink)

    return {
        "language_corpus": languages,
        "modality_topics": modalities,
        "language_link_count": sum(1 for x in languages if x.get("linked")),
        "modality_link_count": sum(1 for x in modalities if x.get("linked")),
    }


def _fetch_wikidata_entity(qid: str) -> dict[str, Any]:
    from .client import get_json

    url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
    data = get_json(url)
    return data.get("entities", {}).get(qid, {})


def _persist(category: str, slug: str, result: dict[str, Any]) -> Path:
    brain_dir = _topic_dir(category, slug) / "research" / "brain"
    brain_dir.mkdir(parents=True, exist_ok=True)

    out_file = brain_dir / "latest_scrape.json"
    out_file.write_text(json.dumps(result, indent=2), encoding="utf-8")

    MODALITY_CACHE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    cache_file = MODALITY_CACHE / f"{stamp}_modality_{slug}.json"
    cache_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return out_file


def _append_log(slug: str, result: dict[str, Any]) -> None:
    MODALITY_CACHE.mkdir(parents=True, exist_ok=True)
    log: list = []
    if MODALITY_LOG.exists():
        log = json.loads(MODALITY_LOG.read_text(encoding="utf-8"))
    log.append(
        {
            "slug": slug,
            "category": result.get("category"),
            "scraped_at": result["scraped_at"],
            "sources": result["sources_used"],
            "errors": result["errors"],
            "uncertainty_flags": len(result.get("uncertainty_flags", [])),
            "keywords": result.get("modality_summary", {}).get("keyword_count", 0),
        }
    )
    MODALITY_LOG.write_text(json.dumps(log[-300:], indent=2), encoding="utf-8")


def scrape_modality_batch(
    *,
    category: str | None = None,
    deep: bool = False,
) -> list[dict[str, Any]]:
    data = _load_registry()
    topics = data["topics"]
    if category:
        topics = [t for t in topics if t["category"] == category]
    results: list[dict[str, Any]] = []
    for topic in topics:
        try:
            results.append(scrape_modality(topic["slug"], deep=deep))
        except Exception as exc:
            results.append({"slug": topic["slug"], "category": topic["category"], "errors": [str(exc)]})
    return results


def build_crosslink_index_report() -> str:
    """Markdown index of language corpus + modality sibling links for all topics."""
    data = _load_registry()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# DAVID Modality Cross-Link Index",
        f"Generated: {now}",
        "",
        "Public sources only. Links resolve against `language_registry.json` brain scrapes",
        "and sibling modality `latest_scrape.json` files.",
        "",
        f"**Topics indexed:** {len(data['topics'])}",
        "",
        "---",
        "",
    ]

    by_cat: dict[str, list[dict[str, Any]]] = {}
    for topic in data["topics"]:
        by_cat.setdefault(topic["category"], []).append(topic)

    for cat_key in sorted(by_cat.keys(), key=lambda k: data["categories"][k]["label"]):
        cat_label = data["categories"][cat_key]["label"]
        lines.append(f"## {cat_label} (`{cat_key}`)")
        lines.append("")

        for topic in sorted(by_cat[cat_key], key=lambda t: t["slug"]):
            slug = topic["slug"]
            lang_slugs = topic.get("language_corpus_links", [])
            mod_slugs = topic.get("modality_links", [])
            links = _build_corpus_cross_links(lang_slugs, mod_slugs)

            scrape_path = (
                _topic_dir(cat_key, slug) / "research" / "brain" / "latest_scrape.json"
            )
            scraped = scrape_path.exists()
            flag_count = 0
            if scraped:
                scrape = json.loads(scrape_path.read_text(encoding="utf-8"))
                flag_count = len(scrape.get("uncertainty_flags", []))

            lines.append(f"### {topic['name']} (`{slug}`)")
            lines.append("")
            lines.append(f"- **Scraped:** {'yes' if scraped else 'no'}")
            lines.append(f"- **Uncertainty flags:** {flag_count}")
            lines.append("")

            lines.append("**Language corpus links:**")
            if links["language_corpus"]:
                lines.append("")
                lines.append("| Language | Status | Brain scrape path | IPA count | Linked |")
                lines.append("|----------|--------|-------------------|-----------|--------|")
                for lang in links["language_corpus"]:
                    if lang.get("reason"):
                        lines.append(
                            f"| `{lang['slug']}` | — | — | — | no ({lang['reason']}) |"
                        )
                        continue
                    ipa = lang.get("ipa_count", "—")
                    linked = "yes" if lang.get("linked") else "no"
                    path = lang.get("brain_scrape_path", "—")
                    status = lang.get("status", "—")
                    lines.append(
                        f"| {lang.get('name', lang['slug'])} | {status} | `{path}` | {ipa} | {linked} |"
                    )
            else:
                lines.append("")
                lines.append("_None configured._")
            lines.append("")

            lines.append("**Sibling modality links:**")
            if links["modality_topics"]:
                lines.append("")
                lines.append("| Modality | Category | Scrape path | Linked | Flags |")
                lines.append("|----------|----------|-------------|--------|-------|")
                for mod in links["modality_topics"]:
                    if mod.get("reason"):
                        lines.append(
                            f"| `{mod['slug']}` | — | — | no ({mod['reason']}) | — |"
                        )
                        continue
                    linked = "yes" if mod.get("linked") else "no"
                    flags = mod.get("uncertainty_flags", "—")
                    path = mod.get("modality_scrape_path", "—")
                    lines.append(
                        f"| {mod.get('name', mod['slug'])} | `{mod.get('category', '—')}` | `{path}` | {linked} | {flags} |"
                    )
            else:
                lines.append("")
                lines.append("_None configured._")
            lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines)


def write_crosslink_index_report() -> Path:
    REPORTS_DIR = DAVID_ROOT / "reports"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "modality_crosslink_index.md"
    out.write_text(build_crosslink_index_report(), encoding="utf-8")
    return out


def coverage_report() -> dict[str, Any]:
    data = _load_registry()
    by_category: dict[str, dict[str, Any]] = {}
    scraped = 0
    for topic in data["topics"]:
        cat = topic["category"]
        by_category.setdefault(
            cat,
            {
                "label": data["categories"][cat]["label"],
                "total": 0,
                "scraped": 0,
                "topics": [],
            },
        )
        by_category[cat]["total"] += 1
        path = _topic_dir(cat, topic["slug"]) / "research" / "brain" / "latest_scrape.json"
        entry = {"slug": topic["slug"], "name": topic["name"], "scraped": path.exists()}
        if path.exists():
            scraped += 1
            by_category[cat]["scraped"] += 1
            scrape = json.loads(path.read_text(encoding="utf-8"))
            entry["sources"] = scrape.get("sources_used", [])
            entry["uncertainty_flags"] = len(scrape.get("uncertainty_flags", []))
        by_category[cat]["topics"].append(entry)
    return {
        "total_topics": len(data["topics"]),
        "scraped_topics": scraped,
        "categories": by_category,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
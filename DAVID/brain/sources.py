"""Public-source fetchers: Wikipedia, Wiktionary, Wikidata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .client import mediawiki_api
from .parsers import (
    parse_etymology_blocks,
    parse_ipa_from_wikitext,
    parse_pronunciation_section,
    wikidata_ipa_claims,
)

WIKI_MAP_FILE = Path(__file__).resolve().parents[1] / "data" / "wiki_language_map.json"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
WIKTIONARY_API = "https://en.wiktionary.org/w/api.php"
WIKIDATA_API = "https://www.wikidata.org/wiki/Special:EntityData"


def load_wiki_map() -> dict[str, dict[str, Any]]:
    return json.loads(WIKI_MAP_FILE.read_text(encoding="utf-8"))


def fetch_wikipedia(title: str) -> dict[str, Any]:
    extract_data = mediawiki_api(
        WIKIPEDIA_API,
        action="query",
        prop="extracts|info",
        titles=title,
        explaintext=1,
        inprop="url",
    )
    pages = extract_data.get("query", {}).get("pages", {})
    page = next(iter(pages.values()), {})
    wikitext_data = mediawiki_api(
        WIKIPEDIA_API,
        action="parse",
        page=title,
        prop="wikitext",
    )
    wikitext = wikitext_data.get("parse", {}).get("wikitext", {}).get("*", "")
    return {
        "title": title,
        "url": page.get("fullurl", ""),
        "extract": page.get("extract", ""),
        "wikitext_length": len(wikitext),
        "phonology_keywords": [],
        "source": "wikipedia",
        "license": "CC BY-SA 3.0",
        "_wikitext": wikitext,
    }


LEMMA_STOPWORDS = frozenset(
    {
        "the", "and", "for", "from", "with", "this", "that", "excerpt", "pending",
        "text", "language", "unknown", "partial", "ritual", "portion",
    }
)


def fetch_wiktionary(
    title: str,
    extra_titles: list[str] | None = None,
    fallbacks: list[str] | None = None,
) -> dict[str, Any]:
    titles = list(
        dict.fromkeys([title, *(fallbacks or []), *(extra_titles or [])])
    )
    combined_ipa: list[dict[str, str]] = []
    etymologies: list[dict[str, str]] = []
    pron_notes: list[dict[str, str]] = []
    pages_fetched: list[str] = []

    for t in titles[:8]:
        try:
            data = mediawiki_api(
                WIKTIONARY_API,
                action="parse",
                page=t,
                prop="wikitext",
            )
        except Exception as exc:
            pages_fetched.append(f"{t} (error: {exc})")
            continue

        wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
        if not wikitext:
            continue
        pages_fetched.append(t)
        combined_ipa.extend(parse_ipa_from_wikitext(wikitext))
        etymologies.extend(parse_etymology_blocks(wikitext))
        pron_notes.extend(parse_pronunciation_section(wikitext))

    return {
        "pages": pages_fetched,
        "ipa_entries": _dedupe_ipa(combined_ipa),
        "etymology_blocks": etymologies[:12],
        "pronunciation_notes": pron_notes[:8],
        "source": "wiktionary",
        "license": "CC BY-SA 3.0",
    }


def fetch_wikidata(qid: str) -> dict[str, Any]:
    url = f"{WIKIDATA_API}/{qid}.json"
    from .client import get_json

    data = get_json(url)
    entity = data.get("entities", {}).get(qid, {})
    labels = entity.get("labels", {}).get("en", {}).get("value", "")
    descriptions = entity.get("descriptions", {}).get("en", {}).get("value", "")
    ipa = wikidata_ipa_claims(entity)

    iso639_3 = _claim_value(entity, "P220")
    family = _claim_value(entity, "P279", label=True)
    ext_status = _claim_value(entity, "P2184")

    return {
        "qid": qid,
        "label": labels,
        "description": descriptions,
        "iso639_3": iso639_3,
        "language_family": family,
        "extinction_status": ext_status,
        "ipa_statements": ipa,
        "source": "wikidata",
        "license": "CC0",
    }


def _claim_value(entity: dict, prop: str, label: bool = False) -> str | None:
    claims = entity.get("claims", {}).get(prop, [])
    if not claims:
        return None
    try:
        val = claims[0]["mainsnak"]["datavalue"]["value"]
        if label and isinstance(val, dict):
            return val.get("id")
        if isinstance(val, str):
            return val
    except (KeyError, TypeError):
        pass
    return None


def _dedupe_ipa(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for e in entries:
        key = f"{e.get('ipa')}|{e.get('accent')}"
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


def corpus_lemma_titles(transliteration: str) -> list[str]:
    """Pull lookup candidates from attested transliteration (conservative)."""
    words = []
    for token in transliteration.replace(",", " ").split():
        cleaned = "".join(c for c in token if c.isalpha() or c in "āēīōūăĕĭŏŭχ")
        low = cleaned.lower()
        if len(cleaned) >= 5 and low not in LEMMA_STOPWORDS:
            words.append(cleaned)
    return list(dict.fromkeys(words))[:4]
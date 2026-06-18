"""Extract communication-modality signals from public wikitext."""

from __future__ import annotations

import re
from typing import Any

from .parsers import (
    _clean_wiki,
    extract_phonology_keywords,
    parse_ipa_from_wikitext,
)

UNCERTAINTY_PATTERNS = (
    (r"\bundeciphered\b", "undeciphered"),
    (r"\breconstruct(?:ed|ion)\b", "reconstructed"),
    (r"\bhypothes(?:is|ized|ized)\b", "hypothetical"),
    (r"\bdisputed\b", "disputed"),
    (r"\buncertain\b", "uncertain"),
    (r"\bproposed\b", "proposed"),
    (r"\bdebated\b", "debated"),
    (r"\bspeculat(?:ion|ive)\b", "speculative"),
    (r"\bpartly\s+known\b", "partly_known"),
    (r"\bnot\s+yet\s+deciphered\b", "undeciphered"),
)

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "phonetics-ipa": (
        r"\bIPA\b",
        r"\bphonet\w*\b",
        r"\barticulat\w*\b",
        r"\bvocal\s+tract\b",
        r"\bconsonant\b",
        r"\bvowel\b",
        r"\bvoicing\b",
        r"\bplace\s+of\s+articulation\b",
        r"\bmanner\s+of\s+articulation\b",
        r"\bspeech\s+production\b",
        r"\bprosod\w*\b",
        r"\bintonation\b",
        r"\bpitch\s+accent\b",
        r"\bstress\b",
        r"\brhythm\b",
        r"\bsuprasegmental\b",
    ),
    "non-verbal": (
        r"\bgesture\b",
        r"\bfacial\s+expression\b",
        r"\bproxemic\w*\b",
        r"\bparalinguist\w*\b",
        r"\bkinesic\w*\b",
        r"\bbody\s+language\b",
        r"\bnon-?verbal\b",
        r"\bemblematic\b",
        r"\bposture\b",
        r"\bgaze\b",
        r"\bintonation\b",
        r"\bprosod\w*\b",
        r"\bturn-?taking\b",
        r"\bconversation\s+analysis\b",
        r"\boverlap\b",
        r"\bbackchannel\b",
    ),
    "sign-languages": (
        r"\bsign\s+language\b",
        r"\bcherolog\w*\b",
        r"\bmanual\s+alphabet\b",
        r"\bfingerspell\w*\b",
        r"\bDeaf\b",
        r"\bhandshape\b",
        r"\bsigning\b",
        r"\bBANZSL\b",
    ),
    "writing-systems": (
        r"\bwriting\s+system\b",
        r"\bscript\b",
        r"\borthograph\w*\b",
        r"\bsyllab\w*\b",
        r"\balphabet\b",
        r"\blogograph\w*\b",
        r"\babjad\b",
        r"\babugida\b",
        r"\bdecipher\w*\b",
        r"\btransliterat\w*\b",
        r"\bgrapheme\b",
    ),
    "pragmatics": (
        r"\bdeixis\b",
        r"\bdeictic\b",
        r"\bspeech\s+act\b",
        r"\billocution\w*\b",
        r"\bperlocution\w*\b",
        r"\bdiscourse\s+marker\b",
        r"\bpragmatic\w*\b",
        r"\bimplicature\b",
        r"\bcode-?switch\w*\b",
        r"\bmultilingual\w*\b",
        r"\bcontext\b",
        r"\breference\b",
    ),
}

SCRIPT_INFO_SECTION = re.compile(
    r"==\s*(?:Alphabet|Script|Characters|Sign inventory|Letters)\s*==(.*?)(?=\n==|\Z)",
    re.DOTALL | re.IGNORECASE,
)


def extract_category_keywords(text: str, category: str) -> list[str]:
    patterns = CATEGORY_KEYWORDS.get(category, ())
    found: list[str] = []
    for pat in patterns:
        if re.search(pat, text, re.IGNORECASE):
            found.append(pat.replace(r"\b", "").replace("\\w*", "").replace("\\s+", " "))
    phonology = extract_phonology_keywords(text)
    return sorted(set(found + phonology))


def flag_uncertain_claims(text: str, preset_flags: list[str] | None = None) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []
    seen: set[str] = set()
    for pat, label in UNCERTAINTY_PATTERNS:
        for match in re.finditer(pat, text, re.IGNORECASE):
            if label in seen:
                continue
            seen.add(label)
            start = max(0, match.start() - 60)
            end = min(len(text), match.end() + 60)
            snippet = re.sub(r"\s+", " ", text[start:end]).strip()
            flags.append({"flag": label, "context_snippet": snippet[:200]})
    for label in preset_flags or []:
        if label not in seen:
            seen.add(label)
            flags.append({"flag": label, "context_snippet": "(preset from registry mapping)"})
    return flags[:12]


def parse_script_sections(wikitext: str) -> list[dict[str, str]]:
    blocks: list[dict[str, str]] = []
    for match in SCRIPT_INFO_SECTION.finditer(wikitext):
        body = _clean_wiki(match.group(1))
        if body and len(body) >= 30:
            blocks.append({"section": "script_inventory", "text": body[:4000]})
    return blocks


def extract_wikidata_modality_claims(entity: dict[str, Any], category: str) -> dict[str, Any]:
    claims = entity.get("claims", {})
    out: dict[str, Any] = {"category": category, "statements": []}

    prop_map = {
        "sign-languages": ("P218", "P279", "P910"),
        "writing-systems": ("P282", "P31", "P361"),
        "phonetics-ipa": ("P898", "P443"),
        "pragmatics": ("P31", "P279", "P1269"),
    }
    for prop in prop_map.get(category, ()):
        for claim in claims.get(prop, [])[:4]:
            try:
                val = claim["mainsnak"]["datavalue"]["value"]
                if isinstance(val, str):
                    out["statements"].append({"property": prop, "value": val})
                elif isinstance(val, dict) and "id" in val:
                    out["statements"].append({"property": prop, "value": val["id"]})
            except (KeyError, TypeError):
                continue
    return out


def build_modality_summary(
    *,
    category: str,
    wikipedia: dict[str, Any] | None,
    wikidata: dict[str, Any] | None,
    wiktionary: dict[str, Any] | None,
    uncertainty_flags: list[dict[str, str]],
) -> dict[str, Any]:
    ipa_count = 0
    if wiktionary:
        ipa_count = len(wiktionary.get("ipa_entries", []))

    keywords: list[str] = []
    if wikipedia:
        keywords = wikipedia.get("modality_keywords", [])

    return {
        "category": category,
        "keyword_count": len(keywords),
        "top_keywords": keywords[:10],
        "ipa_entries": ipa_count,
        "uncertainty_flag_count": len(uncertainty_flags),
        "has_wikidata_statements": bool(wikidata and wikidata.get("modality_claims", {}).get("statements")),
        "extract_chars": len((wikipedia or {}).get("extract", "")),
    }
"""Extract etymology, IPA, accent variants, and diction from wikitext."""

from __future__ import annotations

import re
from typing import Any

IPA_TEMPLATE = re.compile(
    r"\{\{IPA(?:\|[^|]*)?\|([^}|]+)(?:\|([^}]*))?\}\}",
    re.IGNORECASE,
)
IPAC_EN = re.compile(r"\{\{IPAc-en\|([^}]+)\}\}", re.IGNORECASE)
ETYMOLOGY_SECTION = re.compile(
    r"==\s*Etymology\s*==(.*?)(?=\n==|\Z)",
    re.DOTALL | re.IGNORECASE,
)
PRONUNCIATION_SECTION = re.compile(
    r"==\s*Pronunciation\s*==(.*?)(?=\n==|\Z)",
    re.DOTALL | re.IGNORECASE,
)
ACCENT_PARAM = re.compile(r"a=([^|\s}]+)", re.IGNORECASE)
LANG_PARAM = re.compile(r"\bl=([^|\s}]+)", re.IGNORECASE)


def _clean_wiki(text: str) -> str:
    text = re.sub(r"\{\{[^}]+\}\}", "", text)
    text = re.sub(r"\[\[(?:[^|\]]+\|)?([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"''+", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def parse_ipa_from_wikitext(wikitext: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    seen: set[str] = set()

    for match in IPA_TEMPLATE.finditer(wikitext):
        ipa = match.group(1).strip()
        extras = match.group(2) or ""
        accent = ""
        am = ACCENT_PARAM.search(extras)
        if am:
            accent = am.group(1)
        lang = ""
        lm = LANG_PARAM.search(extras)
        if lm:
            lang = lm.group(1)
        key = f"{ipa}|{accent}|{lang}"
        if key in seen:
            continue
        seen.add(key)
        entries.append(
            {
                "ipa": ipa,
                "accent": accent or "unspecified",
                "language_code": lang,
                "quality": _classify_pronunciation_quality(accent, ipa),
            }
        )

    for match in IPAC_EN.finditer(wikitext):
        raw = match.group(1)
        ipa_approx = "/" + raw.replace("|", "") + "/"
        key = f"en-{ipa_approx}"
        if key in seen:
            continue
        seen.add(key)
        entries.append(
            {
                "ipa": ipa_approx,
                "accent": "English approximation",
                "language_code": "en",
                "quality": "learner_approximation",
            }
        )

    return entries


def _classify_pronunciation_quality(accent: str, ipa: str) -> str:
    accent_l = accent.lower()
    if any(x in accent_l for x in ("recon", "hypoth", "proposed")):
        return "reconstructed"
    if any(x in accent_l for x in ("us", "uk", "au", "ca", "in", "nz", "ie")):
        return "regional_variant"
    if "flawed" in accent_l or "common error" in accent_l:
        return "learner_common_error"
    if ipa.startswith("[") or "?" in ipa:
        return "disputed"
    return "scholarly_ipa"


def parse_etymology_blocks(wikitext: str) -> list[dict[str, str]]:
    blocks: list[dict[str, str]] = []
    for match in ETYMOLOGY_SECTION.finditer(wikitext):
        body = _clean_wiki(match.group(1))
        if body and len(body) >= 40 and body.count("=") < 3:
            blocks.append({"section": "Etymology", "text": body[:4000]})
    return blocks


def parse_pronunciation_section(wikitext: str) -> list[dict[str, str]]:
    notes: list[dict[str, str]] = []
    for match in PRONUNCIATION_SECTION.finditer(wikitext):
        body = _clean_wiki(match.group(1))
        if body:
            notes.append({"section": "Pronunciation", "text": body[:3000]})
    return notes


def extract_phonology_keywords(text: str) -> list[str]:
    keywords = []
    patterns = (
        r"\bIPA\b",
        r"\bphonolog\w*\b",
        r"\bvowel\b",
        r"\bconsonant\b",
        r"\baccent\b",
        r"\bdialect\b",
        r"\bpronunciation\b",
        r"\betymolog\w*\b",
        r"\breconstructed\b",
        r"\bextinct\b",
    )
    for pat in patterns:
        if re.search(pat, text, re.IGNORECASE):
            keywords.append(pat.replace(r"\b", "").replace("\\w*", ""))
    return sorted(set(keywords))


def wikidata_ipa_claims(entity: dict[str, Any]) -> list[dict[str, str]]:
    claims = entity.get("claims", {})
    results: list[dict[str, str]] = []
    for prop in ("P898", "P443"):
        for claim in claims.get(prop, []):
            try:
                value = claim["mainsnak"]["datavalue"]["value"]
            except (KeyError, TypeError):
                continue
            if isinstance(value, str):
                results.append({"property": prop, "value": value, "source": "wikidata"})
    return results
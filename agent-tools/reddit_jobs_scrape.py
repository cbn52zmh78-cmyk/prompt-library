"""Scrape r/forhire and r/slavelabour via Reddit RSS (last 24h)."""
from __future__ import annotations

import json
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

OUT = Path(r"C:\Users\NCG\Claude\Projects\NEXUS\freelance\reddit_jobs_20260623.json")
SUBS = ("forhire", "slavelabour")
PHRASE_KEYWORDS = (
    "web dev",
    "webdev",
    "web development",
    "web site",
    "full stack",
    "fullstack",
    "bug fix",
    "bugfix",
    "artificial intelligence",
    "machine learning",
)
WORD_KEYWORDS = (
    "python",
    "javascript",
    "wordpress",
    "automation",
    "automate",
    "script",
    "scripting",
    "scraper",
    "scraping",
    "react",
    "flask",
    "django",
    "website",
)
BOUNDARY_KEYWORDS = ("js", "wp", "ai", "bot", "api", "node")
WORD_PATTERNS = tuple(
    re.compile(rf"\b{re.escape(w)}\b", re.I) for w in WORD_KEYWORDS + BOUNDARY_KEYWORDS
)
CUTOFF = datetime.now(timezone.utc) - timedelta(hours=24)
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
BUDGET_PATTERNS = (
    re.compile(
        r"\$\s?\d[\d,]*(?:\.\d{2})?(?:\s*-\s*\$?\s?\d[\d,]*(?:\.\d{2})?)?",
        re.I,
    ),
    re.compile(r"\b\d+\s*(?:USD|usd|dollars?)\b", re.I),
    re.compile(r"\b(?:budget|pay(?:ing)?|rate|compensation)\s*[:\-]?\s*\$?\s?\d+", re.I),
    re.compile(r"\b(?:\$|USD)\s*\d+", re.I),
    re.compile(r"\[\s*\$\s*\d+", re.I),
)
TAG_RE = re.compile(r"<[^>]+>")


def fetch_rss(sub: str, *, retries: int = 4) -> bytes:
    url = f"https://www.reddit.com/r/{sub}/new/.rss"
    last_err: Exception | None = None
    for attempt in range(retries):
        if attempt:
            time.sleep(15 * attempt)
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": UA,
                "Accept": "application/atom+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                return resp.read()
        except Exception as exc:
            last_err = exc
            if "429" not in str(exc):
                raise
    assert last_err is not None
    raise last_err


def parse_posted_at(entry: ET.Element, ns: dict[str, str]) -> datetime | None:
    for tag in ("published", "updated"):
        el = entry.find(f"a:{tag}", ns)
        if el is None or not (el.text or "").strip():
            continue
        text = el.text.strip()
        try:
            if text.endswith("Z"):
                return datetime.fromisoformat(text.replace("Z", "+00:00"))
            return datetime.fromisoformat(text)
        except ValueError:
            try:
                dt = parsedate_to_datetime(text)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except (TypeError, ValueError):
                continue
    return None


def strip_html(text: str) -> str:
    return unescape(TAG_RE.sub(" ", text or "")).strip()


def matches_keywords(text: str) -> bool:
    t = text.lower()
    if any(p in t for p in PHRASE_KEYWORDS):
        return True
    return any(pat.search(text) for pat in WORD_PATTERNS)


def extract_budget(title: str, body: str) -> str | None:
    blob = f"{title} {body}"
    found: list[str] = []
    for pat in BUDGET_PATTERNS:
        found.extend(m.group(0).strip() for m in pat.finditer(blob))
    if found:
        seen: set[str] = set()
        out: list[str] = []
        for item in found:
            key = item.lower()
            if key not in seen:
                seen.add(key)
                out.append(item)
        return "; ".join(out[:3])
    low = blob.lower()
    if any(w in low for w in ("paid", "payment", "budget", "negotiable", "hourly", "fixed")):
        return "mentioned (no amount)"
    return None


def parse_subreddit(sub: str) -> list[dict]:
    raw = fetch_rss(sub)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(raw)
    results: list[dict] = []

    for entry in root.findall("a:entry", ns):
        posted_at = parse_posted_at(entry, ns)
        if posted_at is None or posted_at < CUTOFF:
            continue

        title_el = entry.find("a:title", ns)
        title = (title_el.text or "").strip() if title_el is not None else ""

        content_el = entry.find("a:content", ns)
        content = strip_html(content_el.text if content_el is not None else "")

        if not matches_keywords(f"{title} {content}"):
            continue

        link_el = entry.find("a:link", ns)
        post_url = link_el.get("href", "") if link_el is not None else ""

        results.append(
            {
                "subreddit": sub,
                "title": title,
                "budget_mentioned": extract_budget(title, content),
                "url": post_url,
                "posted_at": posted_at.isoformat(),
            }
        )

    return results


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    all_jobs: list[dict] = []
    errors: list[str] = []

    for idx, sub in enumerate(SUBS):
        if idx > 0:
            time.sleep(20)
        try:
            all_jobs.extend(parse_subreddit(sub))
            print(f"r/{sub}: {len([j for j in all_jobs if j['subreddit']==sub])} matches")
        except Exception as exc:
            errors.append(f"r/{sub}: {exc}")
            print(f"ERROR r/{sub}: {exc}")

    all_jobs.sort(key=lambda x: x["posted_at"], reverse=True)

    payload = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "window_hours": 24,
        "subreddits": list(SUBS),
        "keyword_filter": list(PHRASE_KEYWORDS) + list(WORD_KEYWORDS) + list(BOUNDARY_KEYWORDS),
        "count": len(all_jobs),
        "errors": errors,
        "jobs": all_jobs,
    }

    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(all_jobs)} jobs -> {OUT}")
    for job in all_jobs[:12]:
        print(f"  [{job['subreddit']}] {job['title'][:72]} | {job.get('budget_mentioned')}")


if __name__ == "__main__":
    main()
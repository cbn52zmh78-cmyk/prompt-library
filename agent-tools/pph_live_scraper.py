#!/usr/bin/env python3
"""Scrape PeoplePerHour freelance jobs via SSR initialState JSON."""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
BASE = "https://www.peopleperhour.com"
KEYWORDS = [
    "python",
    "automation",
    "web development",
    "web dev",
    "AI",
    "script",
    "bug fix",
]
FILTER_TERMS = [
    "python",
    "automation",
    "web dev",
    "web development",
    "ai",
    "artificial intelligence",
    "script",
    "bug fix",
    "bugfix",
    "api",
    "scraping",
    "scraper",
    "llm",
    "machine learning",
]
OUTPUT_DIR = Path(r"C:\Users\NCG\Claude\Projects\NEXUS\freelance")
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
OUTPUT_FILE = OUTPUT_DIR / f"pph_live_scan_{TODAY}.json"


def fetch_html(url: str, retries: int = 3) -> str:
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": UA,
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}: {last_err}")


def parse_initial_state(html: str) -> dict:
    m = re.search(r"window\.PPHReact\.initialState\s*=\s*(\{.*)", html, re.DOTALL)
    if not m:
        raise ValueError("initialState not found")
    raw = m.group(1).split("</script>")[0].strip().rstrip(";")
    obj, _ = json.JSONDecoder().raw_decode(raw)
    return obj


def fetch_listing_page(keyword: str | None, page: int, category_path: str | None = None) -> dict:
    if category_path:
        url = f"{BASE}{category_path}"
        if page > 1:
            url += f"?page={page}"
    else:
        params = {"page": page}
        if keyword:
            params["keyword"] = keyword
        url = f"{BASE}/freelance-jobs?{urllib.parse.urlencode(params)}"
    html = fetch_html(url)
    return parse_initial_state(html)


def format_budget(attrs: dict) -> str:
    budget = attrs.get("budget")
    currency = attrs.get("currency") or ""
    ptype = attrs.get("project_type") or "unknown"
    if budget is None:
        return "not specified"
    return f"{currency} {budget} ({ptype})"


def derive_skills(attrs: dict, matched_keywords: list[str]) -> list[str]:
    skills: list[str] = []
    cat = attrs.get("category") or {}
    sub = attrs.get("sub_category") or {}
    if cat.get("cate_name"):
        skills.append(cat["cate_name"])
    if sub.get("subcate_name") and sub.get("subcate_name") not in skills:
        skills.append(sub["subcate_name"])
    for kw in matched_keywords:
        if kw.lower() not in {s.lower() for s in skills}:
            skills.append(kw)
    return skills


def matches_filter(attrs: dict, matched_keywords: list[str]) -> bool:
    if matched_keywords:
        return True
    blob = " ".join(
        [
            attrs.get("title") or "",
            attrs.get("proj_desc") or "",
            (attrs.get("sub_category") or {}).get("subcate_name", ""),
            (attrs.get("category") or {}).get("cate_name", ""),
        ]
    ).lower()
    return any(term in blob for term in FILTER_TERMS)


def fetch_client_rating(client_url: str, cache: dict[str, float | None]) -> float | None:
    if not client_url:
        return None
    if client_url in cache:
        return cache[client_url]
    try:
        html = fetch_html(client_url)
        stars = re.search(
            r'property="peopleperhourcom:stars"\s+content="([^"]+)"',
            html,
        )
        if stars:
            val = float(stars.group(1))
            cache[client_url] = val
            return val
    except Exception:  # noqa: BLE001
        pass
    cache[client_url] = None
    return None


def collect_jobs() -> tuple[list[dict], dict]:
    jobs_by_id: dict[str, dict] = {}
    sources: list[str] = []

    def ingest_state(state: dict, source: str, keyword: str | None = None) -> None:
        projects = state.get("entities", {}).get("projects", {})
        for proj in projects.values():
            attrs = proj.get("attributes", {})
            pid = str(attrs.get("proj_id") or proj.get("id"))
            title = attrs.get("title") or ""
            desc = attrs.get("proj_desc") or ""
            blob = f"{title} {desc}".lower()

            matched = []
            if keyword:
                matched.append(keyword)
            else:
                for term in FILTER_TERMS:
                    if term in blob and term not in matched:
                        matched.append(term)

            if not matches_filter(attrs, matched if keyword else []):
                continue

            if pid in jobs_by_id:
                jobs_by_id[pid]["matched_keywords"] = sorted(
                    set(jobs_by_id[pid]["matched_keywords"]) | set(matched)
                )
                jobs_by_id[pid]["sources"] = sorted(
                    set(jobs_by_id[pid].get("sources", [])) | {source}
                )
                continue

            jobs_by_id[pid] = {
                "id": pid,
                "title": title,
                "budget": format_budget(attrs),
                "skills_required": derive_skills(attrs, matched),
                "posted_date": (attrs.get("posted_dt") or "").strip(),
                "bid_count": attrs.get("proposalCount"),
                "url": attrs.get("url") or "",
                "client_rating": None,
                "client_url": (attrs.get("client") or {}).get("url"),
                "client_name": (attrs.get("client") or {}).get("public_name"),
                "category": (attrs.get("category") or {}).get("cate_name"),
                "sub_category": (attrs.get("sub_category") or {}).get("subcate_name"),
                "currency": attrs.get("currency"),
                "project_type": attrs.get("project_type"),
                "matched_keywords": matched,
                "sources": [source],
            }

    # Keyword searches with pagination
    for keyword in KEYWORDS:
        page = 1
        total_pages = 1
        while page <= total_pages:
            state = fetch_listing_page(keyword=keyword, page=page)
            meta = state.get("freelanceJobs", {}).get("main", {}).get("meta", {})
            total_pages = int(meta.get("total-pages") or 1)
            source = f"keyword:{keyword}:page:{page}"
            sources.append(source)
            ingest_state(state, source, keyword=keyword)
            page += 1
            time.sleep(0.35)

    # Technology & Programming category (filter locally)
    page = 1
    total_pages = 1
    while page <= total_pages:
        state = fetch_listing_page(keyword=None, page=page, category_path="/freelance-jobs/technology-programming")
        meta = state.get("freelanceJobs", {}).get("main", {}).get("meta", {})
        total_pages = int(meta.get("total-pages") or 1)
        source = f"category:technology-programming:page:{page}"
        sources.append(source)
        ingest_state(state, source, keyword=None)
        page += 1
        time.sleep(0.35)

    return list(jobs_by_id.values()), {"sources": sources, "raw_count": len(jobs_by_id)}


def enrich_ratings(jobs: list[dict]) -> None:
    cache: dict[str, float | None] = {}
    for job in jobs:
        job["client_rating"] = fetch_client_rating(job.pop("client_url", None), cache)
        time.sleep(0.15)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    jobs, scrape_meta = collect_jobs()
    jobs.sort(key=lambda j: j.get("posted_date") or "", reverse=True)
    enrich_ratings(jobs)

    payload = {
        "scan_date": TODAY,
        "scan_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source": "peopleperhour.com/freelance-jobs",
        "filters": KEYWORDS,
        "job_count": len(jobs),
        "scrape_meta": scrape_meta,
        "jobs": [
            {
                "title": j["title"],
                "budget": j["budget"],
                "skills_required": j["skills_required"],
                "posted_date": j["posted_date"],
                "bid_count": j["bid_count"],
                "url": j["url"],
                "client_rating": j["client_rating"],
            }
            for j in jobs
        ],
    }

    OUTPUT_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(jobs)} jobs to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
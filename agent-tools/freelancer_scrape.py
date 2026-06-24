"""Scrape freelancer.com job listings for NEXUS freelance scan."""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

CATEGORIES = [
    "python",
    "web-development",
    "wordpress",
    "automation",
    "ai-development",
    "api-integration",
]

BASE = "https://www.freelancer.com"
MAX_PAGES_PER_CAT = 3
MIN_JOBS = 50


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read().decode("utf-8", errors="replace")


def strip_tags(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def parse_budget(text: str) -> tuple[float | None, float | None]:
    text = text.replace(",", "")
    m = re.search(r"\$\s*([\d.]+)\s*-\s*\$\s*([\d.]+)", text)
    if m:
        return float(m.group(1)), float(m.group(2))
    m = re.search(r"\$\s*([\d.]+)\s*/\s*hr", text, re.I)
    if m:
        v = float(m.group(1))
        return v, v
    m = re.search(r"\$\s*([\d.]+)", text)
    if m:
        v = float(m.group(1))
        return v, v
    return None, None


def parse_card(block: str) -> dict | None:
    title_m = re.search(
        r'<a[^>]*href="(/projects/[^"]+)"[^>]*class="JobSearchCard-primary-heading-link"[^>]*>(.*?)</a>',
        block,
        re.I | re.S,
    )
    if not title_m:
        title_m = re.search(
            r'<a[^>]*class="JobSearchCard-primary-heading-link"[^>]*href="(/projects/[^"]+)"[^>]*>(.*?)</a>',
            block,
            re.I | re.S,
        )
    if not title_m:
        return None

    path = title_m.group(1)
    title = strip_tags(title_m.group(2))
    if not title or title.lower() == "bid now":
        return None

    posted_m = re.search(
        r'class="JobSearchCard-primary-heading-days"[^>]*>([^<]+)</span>',
        block,
        re.I,
    )
    posted = strip_tags(posted_m.group(1)) if posted_m else None

    price_m = re.search(
        r'class="JobSearchCard-secondary-price"[^>]*>(.*?)</div>',
        block,
        re.I | re.S,
    )
    budget_min = budget_max = None
    if price_m:
        budget_min, budget_max = parse_budget(strip_tags(price_m.group(1)))

    bids_m = re.search(
        r'class="JobSearchCard-secondary-entry"[^>]*>(\d+)\s+bids?',
        block,
        re.I,
    )
    bids = int(bids_m.group(1)) if bids_m else None

    skills = []
    for sm in re.finditer(
        r'class="JobSearchCard-primary-tagsLink"[^>]*>([^<]+)</a>',
        block,
        re.I,
    ):
        sk = strip_tags(sm.group(1))
        if sk and sk not in skills:
            skills.append(sk)

    return {
        "title": title,
        "budget_min": budget_min,
        "budget_max": budget_max,
        "skills": skills,
        "bids": bids,
        "posted": posted,
        "url": f"{BASE}{path}",
    }


def parse_page(html: str) -> list[dict]:
    cards = re.split(r'<div class="JobSearchCard-item-inner"', html)
    jobs: list[dict] = []
    for card in cards[1:]:
        rec = parse_card(card)
        if rec:
            jobs.append(rec)
    return jobs


def scrape_all() -> list[dict]:
    """Preserve Freelancer newest-first order: page 1 before page 2, top-of-page first."""
    by_url: dict[str, dict] = {}
    rank = 0
    for cat in CATEGORIES:
        for page in range(1, MAX_PAGES_PER_CAT + 1):
            url = f"{BASE}/jobs/{cat}/" if page == 1 else f"{BASE}/jobs/{cat}/{page}/"
            try:
                html = fetch(url)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    break
                continue
            except Exception:
                continue
            for job in parse_page(html):
                if job["url"] in by_url:
                    continue
                job["_scrape_rank"] = rank
                rank += 1
                by_url[job["url"]] = job

    jobs = list(by_url.values())
    jobs.sort(key=lambda j: j.get("_scrape_rank", 999999))
    for j in jobs:
        j.pop("_scrape_rank", None)
    return jobs


def main() -> None:
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out = Path(r"C:\Users\NCG\Claude\Projects\NEXUS\freelance") / f"freelancer_live_scan_{date_str}.json"
    jobs = scrape_all()

    payload = {
        "source": "freelancer.com/jobs",
        "categories": CATEGORIES,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "sort": "newest_first",
        "sort_note": "Freelancer newest-first per category page; merged by first-seen scrape order",
        "count": len(jobs),
        "jobs": jobs,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(jobs)} jobs to {out}")
    if len(jobs) < MIN_JOBS:
        raise SystemExit(f"Only {len(jobs)} jobs scraped; expected {MIN_JOBS}+")


if __name__ == "__main__":
    main()
"""Scrape We Work Remotely + Contra into NEXUS freelance remote_boards JSON."""
from __future__ import annotations

import json
import re
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

OUT = Path(r"C:\Users\NCG\Claude\Projects\NEXUS\freelance") / (
    f"remote_boards_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
)

WWR_FEEDS = [
    ("https://weworkremotely.com/categories/remote-programming-jobs.rss", "remote-programming-jobs"),
    ("https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss", "remote-full-stack-programming-jobs"),
    ("https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss", "remote-back-end-programming-jobs"),
    ("https://weworkremotely.com/categories/remote-front-end-programming-jobs.rss", "remote-front-end-programming-jobs"),
    ("https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss", "remote-devops-sysadmin-jobs"),
]

CONTRA_DISCOVER = [
    ("https://contra.com/discover?roles=Web+Developer&view=projects", "Web Developer"),
    ("https://contra.com/discover?roles=AI+Developer&view=projects", "AI Developer"),
]

CONTRA_CHALLENGES = [
    "https://contra.com/community/topic/renoisechallenge",
    "https://contra.com/community/topic/promptandcircumstance",
    "https://contra.com/community/topic/characterchallenge",
    "https://contra.com/community/topic/ommabuildathon",
    "https://contra.com/community/topic/bubble",
    "https://contra.com/community/topic/anything",
    "https://contra.com/community/topic/creativeaiflow",
]

SALARY_RE = re.compile(
    r"\$\s*([\d,]+(?:\.\d+)?)\s*(?:-\s*\$?\s*([\d,]+(?:\.\d+)?))?\s*(?:USD|/hr|per hour)?",
    re.I,
)
PRIZE_RE = re.compile(r"\$\s*([\d,]+)\s*K?\s*(?:Prize|prize)", re.I)
TAG_RE = re.compile(r"<[^>]+>")


def fetch(url: str, *, insecure_ssl: bool = False) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    ctx = None
    if insecure_ssl:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, timeout=45, context=ctx) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_budget(text: str) -> tuple[float | None, float | None]:
    if not text:
        return None, None
    m = SALARY_RE.search(text.replace(",", ""))
    if not m:
        return None, None
    lo = float(m.group(1))
    hi = float(m.group(2)) if m.group(2) else lo
    return lo, hi


def parse_prize(text: str) -> tuple[float | None, float | None]:
    m = PRIZE_RE.search(text)
    if not m:
        return None, None
    val = float(m.group(1).replace(",", ""))
    if "K" in text[m.start() : m.end() + 2].upper():
        val *= 1000
    return val, val


def strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", unescape(TAG_RE.sub(" ", text or ""))).strip()


def split_title_company(raw_title: str) -> tuple[str, str | None]:
    if ":" in raw_title:
        company, title = raw_title.split(":", 1)
        return title.strip(), company.strip()
    return raw_title.strip(), None


def posted_from_pubdate(pub: str | None) -> str | None:
    if not pub:
        return None
    try:
        dt = parsedate_to_datetime(pub)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        days = max(0, delta.days)
        return f"{days}d ago" if days else "today"
    except (TypeError, ValueError):
        return pub


def scrape_wwr_rss() -> list[dict]:
    jobs: list[dict] = []
    seen: set[str] = set()

    for feed_url, feed_cat in WWR_FEEDS:
        try:
            raw = fetch(feed_url)
        except Exception as exc:
            print(f"WWR feed skip {feed_cat}: {exc}")
            continue

        root = ET.fromstring(raw)
        channel = root.find("channel")
        if channel is None:
            continue

        for item in channel.findall("item"):
            link_el = item.find("link")
            url = (link_el.text or "").strip() if link_el is not None else ""
            if not url or url in seen:
                continue
            seen.add(url)

            title_el = item.find("title")
            raw_title = (title_el.text or "").strip() if title_el is not None else ""
            title, company = split_title_company(raw_title)

            region_el = item.find("region")
            region = (region_el.text or "").strip() if region_el is not None else None

            cat_el = item.find("category")
            category = (cat_el.text or "").strip() if cat_el is not None else feed_cat

            desc_el = item.find("description")
            desc = strip_html(desc_el.text if desc_el is not None else "")

            pub_el = item.find("pubDate")
            posted = posted_from_pubdate(pub_el.text if pub_el is not None else None)

            budget_min, budget_max = parse_budget(desc)
            skills = [category] if category else []
            if region and region not in skills:
                skills.append(region)

            jobs.append(
                {
                    "source": "weworkremotely.com",
                    "title": title,
                    "company": company,
                    "budget_min": budget_min,
                    "budget_max": budget_max,
                    "skills": skills,
                    "bids": None,
                    "posted": posted,
                    "url": url,
                }
            )

    return jobs


def extract_json_ld(html: str) -> dict | list | None:
    for block in re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.I | re.S,
    ):
        try:
            return json.loads(block.strip())
        except json.JSONDecodeError:
            continue
    return None


def scrape_contra_discover() -> list[dict]:
    jobs: list[dict] = []
    seen: set[str] = set()

    for page_url, role in CONTRA_DISCOVER:
        try:
            html = fetch(page_url, insecure_ssl=True)
        except Exception as exc:
            print(f"Contra discover skip {role}: {exc}")
            continue

        data = extract_json_ld(html)
        if not isinstance(data, dict):
            continue

        graph = data.get("@graph") or [data]
        items: list[dict] = []
        for node in graph:
            if not isinstance(node, dict):
                continue
            main = node.get("mainEntity") or {}
            if main.get("@type") == "ItemList":
                items.extend(main.get("itemListElement") or [])

        for entry in items:
            if not isinstance(entry, dict):
                continue
            item = entry.get("item") or {}
            url = item.get("url") or ""
            if not url or url in seen:
                continue
            seen.add(url)

            author = item.get("author") or {}
            company = author.get("name")
            title = item.get("name") or ""
            stats = item.get("interactionStatistic") or {}
            likes = stats.get("userInteractionCount")

            addr = author.get("address") or {}
            loc_parts = [addr.get("addressLocality"), addr.get("addressCountry")]
            location = ", ".join(p for p in loc_parts if p)

            jobs.append(
                {
                    "source": "contra.com",
                    "title": title,
                    "company": company,
                    "budget_min": None,
                    "budget_max": None,
                    "skills": [role, *( [location] if location else [] )],
                    "bids": likes,
                    "posted": None,
                    "url": url,
                }
            )

    return jobs


def scrape_contra_challenges() -> list[dict]:
    jobs: list[dict] = []
    seen: set[str] = set()

    # Homepage trending block (prize challenges)
    try:
        home = fetch("https://contra.com/", insecure_ssl=True)
    except Exception as exc:
        print(f"Contra home skip: {exc}")
        home = ""

    for m in re.finditer(
        r'href="(https://contra\.com/community/topic/[^"]+)"[^>]*>.*?'
        r'(\$[\d,]+K?)\s*Prize.*?(\d+)d\s*Left',
        home,
        re.I | re.S,
    ):
        url, prize_txt, days_left = m.group(1), m.group(2), m.group(3)
        if url in seen:
            continue
        seen.add(url)
        slug = url.rsplit("/", 1)[-1]
        bmin, bmax = parse_prize(prize_txt + " Prize")
        jobs.append(
            {
                "source": "contra.com",
                "title": f"Community Challenge: {slug}",
                "company": "Contra",
                "budget_min": bmin,
                "budget_max": bmax,
                "skills": ["challenge", slug],
                "bids": None,
                "posted": f"{days_left}d left",
                "url": url,
            }
        )

    for topic_url in CONTRA_CHALLENGES:
        if topic_url in seen:
            continue
        try:
            html = fetch(topic_url, insecure_ssl=True)
        except Exception as exc:
            print(f"Contra topic skip {topic_url}: {exc}")
            continue

        title_m = re.search(r"<title>([^<]+)</title>", html, re.I)
        title = strip_html(title_m.group(1)) if title_m else topic_url.rsplit("/", 1)[-1]
        title = title.replace(" on Contra", "").strip()
        if title.startswith("#"):
            title = title[1:].strip()

        og_desc = re.search(
            r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)',
            html,
            re.I,
        )
        desc = og_desc.group(1) if og_desc else ""
        bmin, bmax = parse_prize(desc + " " + html[:2000])

        posted = None
        dm = re.search(r"(\d+)\s*d\s*Left", html, re.I)
        if dm:
            posted = f"{dm.group(1)}d left"

        seen.add(topic_url)
        jobs.append(
            {
                "source": "contra.com",
                "title": f"Community Challenge: {title}",
                "company": "Contra",
                "budget_min": bmin,
                "budget_max": bmax,
                "skills": ["challenge", title.lower().replace(" ", "-")],
                "bids": None,
                "posted": posted,
                "url": topic_url,
            }
        )

    return jobs


def main() -> None:
    jobs: list[dict] = []
    errors: list[str] = []

    try:
        wwr = scrape_wwr_rss()
        jobs.extend(wwr)
        print(f"WWR: {len(wwr)} jobs")
    except Exception as exc:
        errors.append(f"weworkremotely: {exc}")
        print(f"WWR error: {exc}")

    try:
        contra_proj = scrape_contra_discover()
        jobs.extend(contra_proj)
        print(f"Contra discover: {len(contra_proj)} entries")
    except Exception as exc:
        errors.append(f"contra discover: {exc}")
        print(f"Contra discover error: {exc}")

    try:
        contra_ch = scrape_contra_challenges()
        # dedupe challenges already in list
        existing = {j["url"] for j in jobs}
        added = [j for j in contra_ch if j["url"] not in existing]
        jobs.extend(added)
        print(f"Contra challenges: {len(added)} entries")
    except Exception as exc:
        errors.append(f"contra challenges: {exc}")
        print(f"Contra challenges error: {exc}")

    payload = {
        "sources": ["weworkremotely.com/categories/remote-programming-jobs", "contra.com"],
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "sort": "source_then_feed_order",
        "sort_note": "WWR RSS pubDate order per feed; Contra discover JSON-LD + community challenges",
        "count": len(jobs),
        "errors": errors,
        "jobs": jobs,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(jobs)} total -> {OUT}")


if __name__ == "__main__":
    main()
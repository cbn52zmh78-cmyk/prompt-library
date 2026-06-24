#!/usr/bin/env python3
"""One-shot fetch helpers for R3 uncertainty calibration research."""
from __future__ import annotations

import re
import sys
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (research-bot)"}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read().decode("utf-8", "replace")


def strip_html(html: str) -> str:
    html = re.sub(r"<script.*?</script>", "", html, flags=re.S | re.I)
    html = re.sub(r"<style.*?</style>", "", html, flags=re.S | re.I)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def snippets(text: str, pattern: str, n: int = 12) -> None:
    for i, m in enumerate(re.finditer(pattern, text, re.I)):
        if i >= n:
            break
        start = max(0, m.start() - 100)
        end = min(len(text), m.end() + 140)
        print(text[start:end].strip())
        print("---")


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: r3_research_fetch.py <task>")
        sys.exit(1)
    task = sys.argv[1]

    if task == "nij_pdf_links":
        html = fetch(
            "https://www.ojp.gov/library/publications/"
            "landscape-study-generative-artificial-intelligence-criminal-justice"
        )
        for m in re.finditer(r'href="([^"]+)"', html):
            h = m.group(1)
            if ".pdf" in h.lower() or "download" in h.lower():
                print(h)

    elif task == "doj_search":
        html = fetch(
            "https://search.justice.gov/search?"
            "query=artificial+intelligence+criminal+justice&affiliate=justice"
        )
        for m in re.finditer(r'href="(https://www\.justice\.gov[^"]+)"', html):
            print(m.group(1))

    elif task == "ic_ethics":
        html = fetch("https://www.intelligence.gov/ai/ai-ethics-framework")
        text = strip_html(html)
        snippets(
            text,
            r"(human[- ]in[- ]the[- ]loop|human judgment|limitations|explainab|uncertain|confidence|oversight|accountab)",
        )

    elif task == "arxiv_maoro":
        xml = fetch(
            "http://export.arxiv.org/api/query?"
            "search_query=au:Maoro+contestable&max_results=5"
        )
        print(xml[:6000])

    elif task == "nij_links":
        for url in [
            "https://www.ojp.gov/library/publications/"
            "landscape-study-generative-artificial-intelligence-criminal-justice",
            "https://www.ojp.gov/ncjrs/virtual-library/abstracts/"
            "landscape-study-generative-artificial-intelligence-criminal-justice",
        ]:
            html = fetch(url)
            print("URL", url)
            for m in re.finditer(r'href="([^"]+)"', html):
                h = m.group(1)
                if any(k in h.lower() for k in ("pdf", "download", "media", "/files/")):
                    print(h)

    elif task == "nist_genai_snip":
        try:
            import pypdf
        except ImportError:
            print("no pypdf")
            return
        path = sys.argv[2] if len(sys.argv) > 2 else ""
        if not path:
            print("need pdf path")
            return
        reader = pypdf.PdfReader(path)
        full = "\n".join((p.extract_text() or "") for p in reader.pages)
        snippets(
            full,
            r"(human|oversight|uncertain|confidence|hallucin|limitation|residual risk|proceed|deploy)",
            n=20,
        )

    elif task == "arxiv_osint_trust":
        xml = fetch(
            "http://export.arxiv.org/api/query?"
            "search_query=ti:OSINT+AND+(ti:confidence+OR+ti:uncertainty+OR+ti:trust)&max_results=10"
        )
        entries = re.findall(r"<entry>(.*?)</entry>", xml, re.S)
        for e in entries:
            title = re.search(r"<title>(.*?)</title>", e, re.S)
            published = re.search(r"<published>(.*?)</published>", e)
            summary = re.search(r"<summary>(.*?)</summary>", e, re.S)
            if title:
                print((published.group(1)[:10] if published else ""), title.group(1).strip())
                if summary:
                    print(summary.group(1).strip()[:500])
                print("---")


    elif task == "doj_ai_cj":
        u = (
            "https://search.justice.gov/search?"
            "query=Artificial+Intelligence+and+Criminal+Justice&affiliate=justice"
        )
        html = fetch(u)
        for m in re.finditer(r'href="(https://www\.justice\.gov[^"]+)"', html):
            print(m.group(1))

    elif task == "nij_urls":
        urls = [
            "https://bja.ojp.gov/program/artificial-intelligence/publications",
            "https://nij.ojp.gov/topics/articles/"
            "landscape-study-generative-artificial-intelligence-criminal-justice",
            "https://www.ojp.gov/ncjrs/virtual-library/abstracts/"
            "landscape-study-generative-artificial-intelligence-criminal-justice",
        ]
        for url in urls:
            try:
                html = fetch(url)
            except Exception as exc:
                print("FAIL", url, exc)
                continue
            print("OK", url)
            for m in re.finditer(r'href="([^"]+)"', html):
                h = m.group(1)
                if ".pdf" in h.lower() or "310885" in h or "download" in h.lower():
                    print(" ", h)


if __name__ == "__main__":
    main()
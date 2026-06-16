#!/usr/bin/env python3
import _bootstrap  # noqa: F401
"""
NEXUS Professional Editorial Writer v2.0
Academic-grade documentation scaffolding with human voice support and multiple citation styles.
Designed for historical, scientific, market, and multi-domain research.
"""

import argparse
import datetime
from pathlib import Path

from workspace_paths import CONTENT_PRODUCTION_PROJECTS

CITATION_STYLES = {
    "APA": "APA 7th Edition",
    "Chicago": "Chicago Notes-Bibliography (17th/18th ed.)",
    "MLA": "MLA 9th Edition",
    "Numbered": "Numbered / IEEE",
}


def get_citation_example(style):
    examples = {
        "APA": "Zillow Research. (2026). *Home value trends in Pennsylvania, Q2 2026*. Zillow Group. https://www.zillow.com/research/",
        "Chicago": "Zillow Research. *Home Value Trends in Pennsylvania, Q2 2026*. Zillow Group, 2026. https://www.zillow.com/research/.",
        "MLA": 'Zillow Research. "Home Value Trends in Pennsylvania, Q2 2026." Zillow Group, 2026. www.zillow.com/research/.',
        "Numbered": '[1] Zillow Research, "Home Value Trends in Pennsylvania, Q2 2026," Zillow Group, 2026. [Online]. Available: https://www.zillow.com/research/',
    }
    return examples.get(style, examples["APA"])


def generate_document(
    title,
    research_summary,
    doc_type="Research Brief",
    style="APA",
    domain="general",
    author="Benjamin Cartwright",
):
    date = datetime.date.today().isoformat()
    safe_title = title.replace(" ", "_").replace(":", "-").replace("/", "-")
    CONTENT_PRODUCTION_PROJECTS.mkdir(parents=True, exist_ok=True)
    folder = CONTENT_PRODUCTION_PROJECTS / f"Professional_Document_v2_{date}_{safe_title}"
    folder.mkdir(exist_ok=True)

    citation_label = CITATION_STYLES.get(style, style)
    bib_example = get_citation_example(style)

    sample_intro = """The landscape of Pennsylvania housing in the middle of 2026 resists easy generalization. While inventory growth in several western counties has begun to shift bargaining power toward buyers, eastern markets continue to display the constrained supply and sustained competition that have characterized much of the post-pandemic period. These patterns are not simply the product of short-term cyclical forces; they reflect longer-term demographic movements, employment geography, and the uneven pace of new residential construction across the Commonwealth. Understanding these divergences requires attention to place-specific data and to the structural conditions that shape them."""

    content = f"""# {title}

**{doc_type}**  
**Author:** {author}  
**Date:** {date}  
**Citation Style:** {citation_label}  
**Domain Focus:** {domain.capitalize()}  
**Generated with:** NEXUS Professional Editorial Writer v2.0

## Abstract
{research_summary[:400]}... This {doc_type.lower()} examines the principal dynamics, evaluates their implications for different stakeholders, and offers evidence-based observations for policy and practice.

**Keywords:** [Add 4–6 precise keywords here]

## 1. Introduction
{sample_intro}

[Continue with context, research questions or objectives, and a clear thesis or guiding argument. Vary sentence length. Use transitional devices to maintain momentum.]

## 2. Background and Context
[Provide necessary historical, disciplinary, or empirical grounding. Engage with relevant prior work where appropriate. Maintain a measured, analytical tone.]

## 3. Data Sources and Methodology
Primary data were drawn from [list sources]. [Describe selection criteria, any quantitative or qualitative approaches, and limitations transparently.]

## 4. Analysis and Findings
[Present key results or interpretations supported by evidence. Use subheadings. Balance data with interpretation. Aim for analytical depth.]

## 5. Discussion
[Interpret findings in broader context. Consider alternative explanations. Acknowledge limitations of the analysis.]

## 6. Conclusion
[Synthesize the central arguments and articulate their significance. Close with forward-looking implications rather than a mechanical summary.]

## Acknowledgments
[Optional but recommended for funded or collaborative work.]

## Declaration of Interests
The author declares no competing interests.

## Data Availability
[State where underlying data or code can be accessed, or explain any restrictions.]

## References
{bib_example}

[Add further citations here, formatted consistently according to the chosen style. Use a hanging indent in the final Word or PDF version.]

## Appendices (if applicable)
[Supplementary material, extended tables, or additional methodological detail.]

---
**Document prepared with NEXUS Professional Editorial Writer v2.0**  
This scaffold supports rigorous, human-voiced academic and professional writing. When refining, attend to varied sentence rhythm, precise yet accessible language, clear logical progression, and appropriate use of evidence. The goal is prose that feels authored by a careful scholar rather than assembled by a machine. All bracketed guidance should be replaced with domain-specific content. Human review for accuracy, voice, and final polish is strongly recommended before any public or formal use.

**Pre-Submission Checklist**
- [ ] All claims supported by cited evidence  
- [ ] Voice is consistent and scholarly but readable  
- [ ] Transitions between paragraphs and sections are smooth  
- [ ] Abstract accurately reflects the full argument  
- [ ] References are complete and correctly formatted  
- [ ] Keywords are specific and useful for discovery
"""

    (folder / "Complete_Professional_Document.md").write_text(content, encoding="utf-8")

    prompt_file = folder / "CONTENT_GENERATION_PROMPT.txt"
    prompt_content = f"""You are an experienced academic writer and editor working at the highest professional standard. Using the structure and voice guidelines below, expand the following research summary into a complete, publish-ready {doc_type.lower()} in {citation_label} style.

Research Summary:
{research_summary}

Document Title: {title}
Domain: {domain}

Voice Guidelines:
- Write with intellectual clarity and precision, but avoid unnecessary jargon.
- Use varied sentence length and natural rhythm.
- Employ transitional phrases that create genuine logical flow (e.g., "This pattern suggests…", "At the same time…", "A closer examination reveals…").
- Balance evidence with interpretation.
- Maintain a measured, authoritative tone without sounding mechanical.

Please generate the full document following the section structure provided in the accompanying Markdown file. Prioritize depth, accuracy, and readability.
"""
    prompt_file.write_text(prompt_content, encoding="utf-8")

    print(f"✅ v2.0 Professional document + Content Generation Prompt created → {folder}")
    print(
        "The Markdown file contains a complete academic skeleton with human-voiced examples."
    )
    print(
        "The .txt file is a ready-to-paste prompt you can send back to me (or another model) to generate high-quality prose that fits the structure."
    )
    print(
        "This combination moves us significantly closer to true one-pass professional output."
    )


def main():
    parser = argparse.ArgumentParser(
        description="NEXUS Professional Editorial Writer v2.0 — Academic scaffolding with human voice and multiple citation styles."
    )
    parser.add_argument("--title", required=True, help="Document title")
    parser.add_argument(
        "--summary", required=True, help="Core research summary or key findings (paste here)"
    )
    parser.add_argument(
        "--type",
        default="Research Brief",
        choices=[
            "Research Brief",
            "Magazine Article",
            "Client Report",
            "White Paper",
            "Historical Analysis",
            "Scientific Report",
        ],
    )
    parser.add_argument("--style", default="APA", choices=["APA", "Chicago", "MLA", "Numbered"])
    parser.add_argument(
        "--domain",
        default="general",
        choices=["general", "historical", "scientific", "market", "policy"],
    )
    parser.add_argument("--author", default="Benjamin Cartwright")
    args = parser.parse_args()
    generate_document(
        args.title, args.summary, args.type, args.style, args.domain, args.author
    )


if __name__ == "__main__":
    main()
"""eliot_dataset_builder.py — ELIOT Financial Crime Intelligence Dataset Builder

Builds the Alpaca-format instruction dataset for ELIOT fine-tuning.
ELIOT is the Financial Crime Intelligence Agent: analyzes real estate
transaction patterns, corporate structures, and financial records to
detect money laundering, fraud, and financial crime.

Paired with the DAVID pipeline pattern (QLoRA / Unsloth / DeepSeek-7B).

Usage:
    python3 training/eliot_dataset_builder.py --build       # generate dataset JSON
    python3 training/eliot_dataset_builder.py --check       # validate existing dataset
    python3 training/eliot_dataset_builder.py --stats       # print typology breakdown
    python3 training/eliot_dataset_builder.py --append FILE # append pairs from JSON file

Output:
    DAVID/training/eliot_dataset_v1.json   (Alpaca format)

Typology Categories (matching ELIOT_Real_Estate_Crime_Typologies_v1.md):
    1. MONEY_LAUNDERING     — foreign capital flight, cartel, shell companies
    2. MORTGAGE_FRAUD       — straw buyer, air loan, flip, appraisal, foreclosure rescue
    3. CONSTRUCTION_FRAUD   — draw fraud, ghost subs, labor racketeering, LIHTC, EB-5
    4. COMMERCIAL_FRAUD     — arson/insurance, organized crime fronts, CRE mortgage fraud
    5. TITLE_DEED_FRAUD     — forgery, quit-claim abuse
    6. TAX_ASSESS_FRAUD     — assessment manipulation, easement abuse
    META                    — orchestration, multi-typology, report writing

Training pair format (Alpaca):
    {
        "instruction": "Analyze the following real estate transaction record...",
        "input": "[transaction data / case facts / document excerpt]",
        "output": "[ELIOT analytical response with risk score, typology flags, evidence chain]",
        "category": "TYPOLOGY_LABEL",
        "source": "FinCEN/DOJ/FBI/DOMAIN_EXPERT",
        "difficulty": "basic | intermediate | advanced"
    }
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE         = Path(__file__).resolve().parent          # training/ (under DAVID)
_DAVID        = _HERE.parent                             # DAVID/
_DATASETS_DIR = _HERE                                    # store alongside DAVID datasets
_ELIOT_DIR    = (
    Path(os.environ.get("ELIOT_DIR", ""))
    if os.environ.get("ELIOT_DIR")
    else Path("C:/Users/NCG/Claude/Projects/NEXUS/Stonebridge/ELIOT")
)
_OUTPUT_FILE  = _DATASETS_DIR / "eliot_dataset_v1.json"

# ── Typology constants ─────────────────────────────────────────────────────────
TYPOLOGIES = [
    "MONEY_LAUNDERING",
    "MORTGAGE_FRAUD",
    "CONSTRUCTION_FRAUD",
    "COMMERCIAL_FRAUD",
    "TITLE_DEED_FRAUD",
    "TAX_ASSESS_FRAUD",
    "META",
]

SOURCES = [
    "FinCEN",
    "DOJ",
    "FBI",
    "FTC",
    "IC3",
    "STATE_AG",
    "HUD_OIG",
    "DOL_OIG",
    "GAO",
    "IRS_CI",
    "FATF",
    "CULLEN_COMMISSION",
    "DOMAIN_EXPERT",   # Benjamin Cartwright direct knowledge
    "COMPOSITE",       # multiple sources combined
]

# ── ELIOT output template ─────────────────────────────────────────────────────
ELIOT_REPORT_TEMPLATE = """FINANCIAL INTELLIGENCE REPORT
Case: {case_id}
Date: {date}
Analyst: ELIOT v0.1 | Human review: Required

SUBJECT ENTITY: {subject}
RISK SCORE: {risk_score}
TYPOLOGY FLAGS: {typology_flags}

FINDINGS:
{findings}

EVIDENCE CHAIN:
{evidence_chain}

CONFIDENCE: {confidence}

RECOMMENDED INVESTIGATIVE LEADS:
{leads}

DISCLAIMER: This report is an analytical tool for investigative use only.
ELIOT does not determine guilt. All findings require human verification."""


def make_report(
    case_id: str,
    subject: str,
    risk_score: str,
    typology_flags: list,
    findings: str,
    evidence_chain: str,
    confidence: str,
    leads: str,
    date: str = None,
) -> str:
    """Format a structured ELIOT report output."""
    return ELIOT_REPORT_TEMPLATE.format(
        case_id=case_id,
        date=date or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        subject=subject,
        risk_score=risk_score,
        typology_flags=", ".join(typology_flags),
        findings=findings,
        evidence_chain=evidence_chain,
        confidence=confidence,
        leads=leads,
    )


# ── SEED TRAINING PAIRS ───────────────────────────────────────────────────────
# These are the foundational pairs sourced from FinCEN, DOJ, FBI, HUD OIG,
# DOL OIG, GAO, and Benjamin Cartwright domain expertise.
# Format: Alpaca instruction/input/output triplets.

SEED_PAIRS: List[Dict[str, Any]] = [

    # ═══════════════════════════════════════════════════════════════════════════
    # CATEGORY 1: MONEY LAUNDERING — Foreign Capital Flight
    # ═══════════════════════════════════════════════════════════════════════════

    {
        "instruction": "Analyze the following real estate transaction for money laundering indicators. Identify applicable FinCEN red flag typologies and produce a structured risk assessment.",
        "input": (
            "Property: 4-unit residential building, Pittsburgh PA. "
            "Purchase price: $385,000. Financing: All-cash wire transfer, no mortgage. "
            "Buyer: Maple Crest Holdings LLC, registered Wyoming 14 days before closing. "
            "Registered agent: CT Corporation (no named member in filing). "
            "Wire origin: Cayman Islands intermediary account. "
            "Post-purchase activity: property sits vacant, no rental listing, no permit activity. "
            "LLC has no prior operating history or tax filings."
        ),
        "output": make_report(
            case_id="ELIOT-SEED-001",
            subject="Maple Crest Holdings LLC / 4-unit residential Pittsburgh PA",
            risk_score="HIGH",
            typology_flags=["FOREIGN_CAPITAL_FLIGHT", "SHELL_COMPANY_ML", "GTO_EQUIVALENT_PATTERN"],
            findings=(
                "Transaction presents a cluster of FinCEN-documented red flags for foreign capital flight "
                "through real estate. All-cash purchase eliminates bank AML scrutiny. Wyoming LLC formed "
                "14 days prior to closing with anonymous registered agent is consistent with FinCEN "
                "Advisory FIN-2017-A003 shell company typology. Wire from Cayman Islands intermediary "
                "(not from beneficial owner directly) is a documented layering technique. Post-purchase "
                "vacancy with no stated use is consistent with real estate as value storage rather than "
                "investment — a pattern documented in FinCEN Geographic Targeting Order markets. "
                "Pittsburgh secondary market context: capital flight from primary GTO markets (NYC/LA) "
                "to secondary markets is documented in FinCEN analysis and Canada's Cullen Commission "
                "reporting on the Vancouver Model."
            ),
            evidence_chain=(
                "- Wyoming SOS LLC registration record (14 days pre-closing)\n"
                "- Allegheny County deed transfer record\n"
                "- Settlement statement: wire from Cayman intermediary account\n"
                "- Post-purchase property inspection: vacant, no utility activation\n"
                "- FinCEN GTO red flag checklist (all-cash + shell + no financing)"
            ),
            confidence="HIGH — 6 of 8 documented FinCEN red flags present",
            leads=(
                "1. Subpoena Wyoming SOS for LLC formation documents and beneficial owner if CTA-compliant\n"
                "2. Trace Cayman intermediary wire to source institution via FinCEN 314(b) or MLAT\n"
                "3. Run beneficial owner against OFAC SDN list and PEP database\n"
                "4. Cross-reference registered agent for other LLC filings in Pittsburgh market\n"
                "5. Check for related LLC filings with same registered agent in same 12-month window"
            ),
        ),
        "category": "MONEY_LAUNDERING",
        "source": "FinCEN",
        "difficulty": "intermediate",
    },

    {
        "instruction": "A detective has provided property records for review. Identify whether the pattern matches documented Chinese Money Laundering Network (CMLN) typologies per FinCEN Advisory FIN-2025-A003.",
        "input": (
            "Subject: 3 residential properties in Pittsburgh's Squirrel Hill neighborhood. "
            "Purchaser 1: Golden Ridge Holdings LLC (Delaware, 2023). Buyer on deed: Liu Wei, "
            "occupation listed as 'student.' "
            "Purchaser 2: Emerald Gate Properties LLC (Delaware, 2023). Buyer on deed: Zhang Min, "
            "occupation 'housewife.' "
            "Purchaser 3: Pacific Summit LLC (Wyoming, 2024). Beneficial owner undisclosed. "
            "All purchases all-cash. All wires from Hong Kong bank. "
            "All properties listed as 'owner-occupied' on tax assessment but neighbors report vacancy. "
            "All three LLCs share the same registered agent (a law firm in Wilmington DE)."
        ),
        "output": make_report(
            case_id="ELIOT-SEED-002",
            subject="Golden Ridge Holdings LLC / Emerald Gate Properties LLC / Pacific Summit LLC — Pittsburgh PA",
            risk_score="HIGH",
            typology_flags=["CMLN_PATTERN", "DAIGOU_PROXY_BUYERS", "SHELL_COMPANY_ML", "FOREIGN_CAPITAL_FLIGHT"],
            findings=(
                "Pattern matches Chinese Money Laundering Network (CMLN) typologies documented in "
                "FinCEN Advisory FIN-2025-A003 (August 28, 2025). Key indicators: "
                "(1) Proxy buyers with stated low-income occupations (student/housewife) making large "
                "all-cash real estate purchases — the core CMLN 'daigou' pattern. "
                "(2) Three coordinated purchases through related LLCs sharing a registered agent in a "
                "12-month window — documented as a CMLN geographic clustering technique. "
                "(3) All wires from Hong Kong banking institution — consistent with underground banking "
                "offset (Fei-Ch'ien equivalent) converting China-held assets to US real estate. "
                "(4) False owner-occupancy declarations on tax assessment while properties sit vacant — "
                "consistent with real estate as value storage, not habitation. "
                "Pittsburgh Squirrel Hill: secondary market consistent with CMLN overflow from primary "
                "GTO markets. Cullen Commission documented identical pattern in Vancouver secondary "
                "neighborhoods as primary markets tightened."
            ),
            evidence_chain=(
                "- Allegheny County Recorder deed transfers (3 properties, shared attorney)\n"
                "- Delaware/Wyoming SOS LLC registrations (common registered agent)\n"
                "- Settlement statements: HK wire transfers\n"
                "- Tax assessment records: owner-occupied vs. neighbor testimony of vacancy\n"
                "- FinCEN Advisory FIN-2025-A003 CMLN red flag checklist"
            ),
            confidence="HIGH — direct CMLN typology match on 5 of 6 documented indicators",
            leads=(
                "1. File SAR referencing FIN-2025-A003 CMLN typology\n"
                "2. Request FinCEN 314(b) information sharing from Hong Kong wire institution\n"
                "3. Subpoena shared Wilmington DE registered agent for all LLC filings\n"
                "4. Verify student/housewife income sources — request IRS records via grand jury\n"
                "5. Check for 4th-6th related LLC formations by same agent in Pittsburgh/PA market"
            ),
        ),
        "category": "MONEY_LAUNDERING",
        "source": "FinCEN",
        "difficulty": "advanced",
    },

    {
        "instruction": "Explain the 'Vancouver Model' of real estate money laundering and identify which elements apply to a secondary US market like Pittsburgh.",
        "input": (
            "Background for analysis: Detective is reviewing a cluster of all-cash residential "
            "purchases in Pittsburgh's North Shore neighborhood. Purchases made by LLCs with "
            "foreign-origin wires. No mortgage financing. Properties sit vacant. Detective asks "
            "ELIOT to contextualize against known international ML patterns."
        ),
        "output": (
            "ANALYSIS: VANCOUVER MODEL APPLICABILITY — PITTSBURGH SECONDARY MARKET\n\n"
            "The Vancouver Model (documented in Canada's Cullen Commission Final Report, 2022) "
            "describes a documented international real estate money laundering mechanism with the "
            "following stages:\n\n"
            "STAGE 1 — PLACEMENT: Criminal proceeds (drug cash, corruption proceeds, capital flight) "
            "are placed into the financial system via underground banking (hawala-equivalent networks "
            "that move value without formal wire transfers).\n\n"
            "STAGE 2 — LAYERING: Value moves through proxy buyers (daigou — students, family, "
            "low-income proxies) using shell LLCs. Multiple LLC layers obscure beneficial owner.\n\n"
            "STAGE 3 — INTEGRATION: All-cash real estate purchase completes laundering cycle. "
            "Property represents clean hard asset. Sale or refinance produces clean proceeds.\n\n"
            "SECONDARY MARKET MECHANISM: As primary markets (Vancouver, NYC, LA, San Francisco) "
            "implement GTOs, stricter AML, and price barriers, capital flight redirects to secondary "
            "markets — Pittsburgh, Cleveland, Columbus — with lower prices, less scrutiny, and no "
            "active FinCEN GTOs.\n\n"
            "PITTSBURGH APPLICABILITY: North Shore all-cash LLC cluster presents Stages 2–3 of "
            "the Vancouver Model. Underground banking stage (Stage 1) would have occurred outside "
            "Pennsylvania. Investigative priority: trace wire origin institution and LLC beneficial "
            "owner chain to identify placement mechanism.\n\n"
            "SOURCE: Cullen Commission Final Report (2022); FinCEN Advisory FIN-2025-A003; "
            "Global Financial Integrity 'Acres of Money Laundering' (2021)."
        ),
        "category": "MONEY_LAUNDERING",
        "source": "CULLEN_COMMISSION",
        "difficulty": "basic",
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # CATEGORY 2: MORTGAGE FRAUD
    # ═══════════════════════════════════════════════════════════════════════════

    {
        "instruction": "Review the following mortgage transaction for fraud indicators. Classify by FinCEN typology and assess whether this is 'fraud for profit' or 'fraud for housing.'",
        "input": (
            "Property: Single-family home, Allegheny County PA. Listed: $180,000. "
            "Sale price on HUD-1: $285,000. "
            "Appraisal submitted: $287,500 (appraiser: same as previous two transactions for this broker). "
            "Buyer: stated income $95,000/year as 'independent contractor' — no W-2, paystubs only. "
            "Buyer occupation: independent contractor (construction). "
            "Loan type: FHA. "
            "Seller: purchased property 45 days prior for $162,000. "
            "Second buyer found in same transaction (name different from loan applicant). "
            "Seller's attorney and buyer's attorney are the same firm."
        ),
        "output": make_report(
            case_id="ELIOT-SEED-003",
            subject="FHA mortgage transaction — Allegheny County PA",
            risk_score="HIGH",
            typology_flags=["ILLEGAL_PROPERTY_FLIPPING", "APPRAISAL_FRAUD", "STRAW_BUYER", "FRAUD_FOR_PROFIT"],
            findings=(
                "Transaction exhibits multiple FinCEN-documented mortgage fraud typologies. "
                "Classification: FRAUD FOR PROFIT — organized scheme to extract funds from FHA lender, "
                "not borrower misrepresentation to obtain housing.\n\n"
                "RED FLAG 1 — ILLEGAL FLIPPING: Seller purchased 45 days prior at $162,000; resale "
                "at $285,000 represents 76% markup in 45 days with no documented improvement activity. "
                "Rapid resale with inflated price is the core illegal flipping pattern per FinCEN "
                "and HUD OIG typologies.\n\n"
                "RED FLAG 2 — APPRAISAL FRAUD: Appraisal at $287,500 (2% above inflated sale price). "
                "Same appraiser appearing across multiple transactions for same broker is documented "
                "recruiter-appraiser network pattern in DOJ prosecutions. Appraisal inflated by ~$125,000 "
                "above prior acquisition price with no improvement documentation.\n\n"
                "RED FLAG 3 — STRAW BUYER: Second name on transaction not on loan application. "
                "Independent contractor income with paystubs only (no W-2) is standard income "
                "falsification pattern. FHA loan selection maximizes government-backed exposure.\n\n"
                "RED FLAG 4 — DUAL REPRESENTATION: Same firm representing both seller and buyer "
                "creates conflict of interest and facilitates closing without arm's-length review."
            ),
            evidence_chain=(
                "- Allegheny County deed: prior sale $162,000 (45 days)\n"
                "- HUD-1 settlement: $285,000 current sale\n"
                "- Appraisal document: $287,500 (repeated appraiser)\n"
                "- Loan application: stated income documentation\n"
                "- Title commitment: dual representation noted\n"
                "- HUD OIG Illegal Flipping typology checklist"
            ),
            confidence="HIGH — meets HUD OIG and FinCEN illegal flipping + appraisal fraud thresholds",
            leads=(
                "1. Refer to HUD OIG for FHA fraud investigation\n"
                "2. Subpoena appraiser's workfile and comp selection\n"
                "3. Investigate appraiser for appearances across broker's prior transactions\n"
                "4. Verify buyer's income documentation with IRS transcript (4506-C)\n"
                "5. Identify second party on transaction and relationship to seller/broker"
            ),
        ),
        "category": "MORTGAGE_FRAUD",
        "source": "HUD_OIG",
        "difficulty": "intermediate",
    },

    {
        "instruction": "What is an 'air loan' in mortgage fraud? Provide a detailed explanation and list the indicators ELIOT should flag.",
        "input": "A detective is reviewing a portfolio of 12 loans originated by a single broker over 18 months. Three properties in the portfolio cannot be located at the addresses on the loan documents. Two addresses are vacant lots.",
        "output": (
            "AIR LOAN DEFINED:\n"
            "An air loan is a mortgage fraud scheme in which the property securing the loan does not "
            "exist, or the borrower does not exist, or both. The fraud involves fabricating an entire "
            "transaction — property, borrower, appraisal, title insurance, and closing documents — "
            "to extract loan proceeds from a lender against a nonexistent asset.\n\n"
            "MECHANISM:\n"
            "1. Fraudster creates fictitious borrower identity (stolen ID or synthetic)\n"
            "2. Fabricates property address (vacant lot, demolished structure, or non-residential address)\n"
            "3. Orders fraudulent appraisal from co-conspirator\n"
            "4. Establishes fictitious phone/mail presence to pass lender verification\n"
            "5. At closing, loan proceeds disbursed to accounts controlled by fraudster\n"
            "6. Loan immediately goes delinquent — no real borrower to make payments\n\n"
            "INDICATORS IN PRESENTED CASE:\n"
            "- Three properties cannot be located: HIGH probability air loan on those three\n"
            "- Two addresses are vacant lots: definitive indicator (no residential collateral)\n"
            "- Single broker across 12 loans in 18 months: organized scheme, not isolated fraud\n"
            "- Recommend: pull all 12 property addresses against county assessor and GIS records\n\n"
            "ELIOT FLAGS FOR AIR LOAN:\n"
            "- Property address does not match county assessor parcel records\n"
            "- No utility service history at property address\n"
            "- No permit history at property address\n"
            "- Appraisal comp properties all distant from subject address\n"
            "- Borrower SSN matches no credit bureau record or was issued posthumously\n"
            "- Title insurance company is newly formed or not licensed in state\n\n"
            "SOURCE: FinCEN mortgage fraud typologies; FBI Mortgage Fraud Annual Reports; "
            "HUD OIG Common Fraud Schemes."
        ),
        "category": "MORTGAGE_FRAUD",
        "source": "FinCEN",
        "difficulty": "basic",
    },

    {
        "instruction": "Analyze this foreclosure rescue fraud scenario and identify investigative priorities.",
        "input": (
            "Distressed homeowner in Allegheny County: 90 days behind on mortgage, received "
            "notice of default. Was contacted by 'Save Your Home Solutions LLC' offering to "
            "negotiate with lender. Signed a document described as 'temporary power of attorney.' "
            "Three months later: property deed shows transfer to Save Your Home Solutions LLC. "
            "Homeowner was told this was 'temporary' to facilitate modification. "
            "LLC has since attempted to refinance the property for $210,000 (assessed value $185,000). "
            "Original homeowner still living in property, paying 'rent' to LLC."
        ),
        "output": make_report(
            case_id="ELIOT-SEED-004",
            subject="Save Your Home Solutions LLC — Foreclosure Rescue Fraud",
            risk_score="HIGH",
            typology_flags=["FORECLOSURE_RESCUE_FRAUD", "DEED_FRAUD", "EQUITY_STRIPPING"],
            findings=(
                "Classic foreclosure rescue fraud scheme per FinCEN typologies and PA OAG documented "
                "patterns. Three overlapping violations identified:\n\n"
                "1. FORECLOSURE RESCUE FRAUD: LLC targeted distressed homeowner with false promise of "
                "loan modification. 'Temporary power of attorney' used to execute deed transfer without "
                "informed homeowner consent. Post-pandemic foreclosure rescue fraud spike documented "
                "by HUD OIG.\n\n"
                "2. DEED FRAUD: Deed transfer to LLC using document homeowner believed was POA for "
                "negotiation. Homeowner retained possession (paying 'rent') while losing title — "
                "classic quit-claim abuse pattern.\n\n"
                "3. EQUITY STRIPPING: Attempted refinance at $210,000 against $185,000 assessed value "
                "would extract equity from property. Proceeds would flow to LLC, not homeowner. "
                "Homeowner left with rental arrangement while equity is extracted."
            ),
            evidence_chain=(
                "- Allegheny County deed transfer record: homeowner → Save Your Home Solutions LLC\n"
                "- Original signed 'power of attorney' document\n"
                "- Refinance application showing LLC as borrower on homeowner's property\n"
                "- Rental agreement between LLC and original owner\n"
                "- PA OAG foreclosure rescue fraud pattern match"
            ),
            confidence="HIGH — deed transfer + continued occupancy = textbook rescue fraud",
            leads=(
                "1. Refer to PA OAG Consumer Protection for foreclosure rescue fraud statute (63 PS §456.1)\n"
                "2. Seek emergency injunction to halt refinance closing\n"
                "3. Investigate Save Your Home Solutions LLC — check for other victims\n"
                "4. Review original deed transfer document for homeowner's actual signature\n"
                "5. Run LLC principals against prior fraud complaints"
            ),
        ),
        "category": "MORTGAGE_FRAUD",
        "source": "COMPOSITE",
        "difficulty": "intermediate",
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # CATEGORY 3: CONSTRUCTION FRAUD
    # ═══════════════════════════════════════════════════════════════════════════

    {
        "instruction": "Analyze this construction loan draw request for fraud indicators. Apply RSMeans cost benchmarks and identify red flags consistent with DOJ-prosecuted draw fraud patterns.",
        "input": (
            "Project: 24-unit apartment building, Pittsburgh PA. "
            "Construction loan: $4.2 million. "
            "Draw request #3 (of 6): claiming 60% project completion. "
            "Amount requested: $840,000. "
            "Claimed completed work: framing complete, rough plumbing complete, rough electrical complete, "
            "HVAC rough-in complete, exterior sheathing complete. "
            "Inspection report: signed by inspector affiliated with developer's LLC. "
            "Site observation by detective: foundation visible, partial framing on 3 of 24 units, "
            "no plumbing or electrical visible. "
            "General Contractor: Steel City Build LLC, formed 6 months before contract award, "
            "no prior construction history in PA. "
            "Subcontractors listed: 4 companies. Two cannot be verified as operating businesses."
        ),
        "output": make_report(
            case_id="ELIOT-SEED-005",
            subject="Steel City Build LLC / 24-unit construction loan draw fraud",
            risk_score="HIGH",
            typology_flags=["CONSTRUCTION_LOAN_DRAW_FRAUD", "GHOST_SUBCONTRACTORS", "FALSE_COMPLETION_CERTIFICATION"],
            findings=(
                "Transaction presents a documented construction loan draw fraud pattern matching "
                "DOJ-prosecuted cases. Analysis:\n\n"
                "COMPLETION DISCREPANCY: Developer claims 60% completion; site inspection shows "
                "approximately 10–15% actual progress (partial framing, 3 of 24 units). Draw request "
                "of $840,000 against 10–15% actual work represents overpayment of approximately "
                "$600,000–$650,000 above legitimate progress.\n\n"
                "RSMeans BENCHMARK CHECK: For 24-unit residential Pittsburgh PA, rough framing + "
                "rough MEP at 60% draw should be verifiable against permit inspections. "
                "Rough plumbing and electrical require municipal inspection sign-off — request permit "
                "inspection records to verify claimed completion stages.\n\n"
                "INSPECTOR CONFLICT: Inspector affiliated with developer LLC is a documented red flag. "
                "Independent third-party inspection required per standard lender protocol — this "
                "deviation is consistent with fraud scheme.\n\n"
                "GHOST SUBCONTRACTORS: 2 of 4 listed subcontractors cannot be verified as operating "
                "businesses. This matches DOL OIG-documented ghost subcontractor pattern — LLCs "
                "formed to receive payments that return to GC or developer as kickback.\n\n"
                "GC RED FLAGS: Steel City Build LLC formed 6 months prior with no PA construction "
                "history — consistent with single-purpose fraud vehicle."
            ),
            evidence_chain=(
                "- Construction loan draw request documentation\n"
                "- Site inspection photographs (detective observation)\n"
                "- PA DEP/municipal building permit inspection records (to be subpoenaed)\n"
                "- PA SOS LLC search: Steel City Build LLC (formation date)\n"
                "- PA SOS / Secretary of State: subcontractor LLC verification\n"
                "- RSMeans 2025 Pittsburgh regional construction cost benchmarks\n"
                "- DOL OIG ghost subcontractor pattern documentation"
            ),
            confidence="HIGH — completion claim vs. site observation divergence is definitive",
            leads=(
                "1. Freeze draw disbursement pending independent inspection\n"
                "2. Request all municipal building permit inspection sign-offs for claimed stages\n"
                "3. Subpoena subcontractor payment records — verify actual payments and recipients\n"
                "4. Investigate inspector affiliation and fee arrangement with developer\n"
                "5. Check Steel City Build LLC principals against other failed or suspicious projects\n"
                "6. Request lender's file for prior draws — assess whether pattern exists from Draw #1"
            ),
        ),
        "category": "CONSTRUCTION_FRAUD",
        "source": "DOL_OIG",
        "difficulty": "advanced",
    },

    {
        "instruction": "Explain how no-show jobs and ghost subcontractors are used in construction money laundering. Provide specific indicators from DOL OIG documentation.",
        "input": "A union construction project in Allegheny County is under review. Certified payroll shows 85 workers on site for the past 3 months. On-site headcount by detective over 4 separate visits: average 22 workers observed. Subcontractor billing shows 6 separate companies receiving payments. Three subcontractors share a mailing address in a UPS Store in Monroeville PA.",
        "output": (
            "ANALYSIS: NO-SHOW JOBS AND GHOST SUBCONTRACTORS — LABOR RACKETEERING PATTERN\n\n"
            "DOL OIG DOCUMENTED MECHANISM:\n"
            "No-show jobs and ghost subcontractors are a documented organized crime technique in "
            "construction (DOL OIG 'Labor Racketeering in the Construction Industry' white paper). "
            "They serve two functions simultaneously:\n"
            "1. LAUNDERING: Criminal cash is converted to clean payroll or subcontractor payments\n"
            "2. THEFT: Project funds are diverted through fraudulent payroll/billing\n\n"
            "INDICATORS IN THIS CASE:\n\n"
            "LABOR INFLATION (NO-SHOW PATTERN):\n"
            "- Certified payroll claims 85 workers\n"
            "- Detective observation: 22 workers average across 4 visits\n"
            "- Discrepancy: 63 workers potentially no-show (74% inflation)\n"
            "- At prevailing wage rates for PA union construction (~$65–80/hr all-in), "
            "63 phantom workers × 40hr/week × 12 weeks = approximately $1.96–2.4M in "
            "fraudulent payroll\n\n"
            "GHOST SUBCONTRACTORS:\n"
            "- 3 of 6 subcontractors share a UPS Store mailing address\n"
            "- UPS mailbox = no physical business location = ghost subcontractor indicator\n"
            "- DOL OIG pattern: GC forms or controls shell subcontractors; bills project; "
            "cash returned to GC principal as 'payment.' Subcontractor LLC dissolves post-project.\n\n"
            "RECOMMENDED ACTIONS:\n"
            "1. Request certified payroll for all subcontractors (Davis-Bacon requirement)\n"
            "2. Verify UPS-address subcontractors against PA SOS (formation date, officers)\n"
            "3. Request union hall dispatch records — verify workers were actually dispatched\n"
            "4. Compare certified payroll SSNs against IRS wage records (via grand jury)\n"
            "5. Refer to DOL OIG and FBI for labor racketeering investigation\n\n"
            "SOURCE: DOL OIG 'Labor Racketeering in the Construction Industry'; "
            "FBI Organized Crime construction fraud cases; PA prevailing wage data."
        ),
        "category": "CONSTRUCTION_FRAUD",
        "source": "DOL_OIG",
        "difficulty": "intermediate",
    },

    {
        "instruction": "Analyze this LIHTC (Low-Income Housing Tax Credit) project for potential fraud.",
        "input": (
            "Project: 48-unit LIHTC affordable housing, Allegheny County PA. "
            "Certified construction cost submitted to PA Housing Finance Agency: $9.2 million. "
            "Comparable LIHTC project completed same year, same market: $5.8 million for 52 units. "
            "Developer fee claimed: $1.4 million (15% of total costs). "
            "Cost certification prepared by developer's in-house accountant. "
            "Post-completion audit finding: 6 units listed as occupied on HUD certification "
            "but utility records show no electricity usage for those units for 18 months. "
            "Developer principal has prior bankruptcy involving a different LLC."
        ),
        "output": make_report(
            case_id="ELIOT-SEED-006",
            subject="48-unit LIHTC project — PA Housing Finance Agency",
            risk_score="HIGH",
            typology_flags=["LIHTC_COST_INFLATION", "GHOST_TENANT_FRAUD", "TAX_CREDIT_FRAUD"],
            findings=(
                "LIHTC fraud indicators present across cost certification and occupancy compliance:\n\n"
                "COST INFLATION: Certified cost $9.2M for 48 units = $191,667/unit. "
                "Comparable project same market: $5.8M for 52 units = $111,538/unit. "
                "Per-unit premium: $80,129 (72% above comparable). No documented justification "
                "for premium. Inflated cost certification increases tax credit allocation — "
                "IRS Criminal Investigation documented identical scheme in multiple national cases.\n\n"
                "DEVELOPER FEE ABUSE: $1.4M fee (15.2% of total). IRS allowable developer fee "
                "typically capped at 15% — this fee at the ceiling based on inflated cost basis "
                "translates to excess fee of approximately $580,000 vs. comparable project basis.\n\n"
                "SELF-CERTIFICATION CONFLICT: Cost certification by developer's own accountant "
                "lacks independence. LIHTC regulations require qualified independent CPA.\n\n"
                "GHOST TENANTS: 6 units with zero utility usage over 18 months while certified "
                "as occupied — definitive indicator of phantom occupancy to maintain compliance "
                "during audit period. This matches IRS CI documented scheme."
            ),
            evidence_chain=(
                "- PA Housing Finance Agency cost certification\n"
                "- Comparable project cost certifications (same year, same market)\n"
                "- Utility company records: 6 units zero usage\n"
                "- HUD occupancy certification for those 6 units\n"
                "- IRS CI LIHTC fraud case precedents\n"
                "- PA SOS: developer principal prior LLC bankruptcy filing"
            ),
            confidence="HIGH — utility vs. occupancy discrepancy is definitive; cost inflation documented",
            leads=(
                "1. Refer to IRS Criminal Investigation for tax credit fraud\n"
                "2. Request independent cost certification review by PHFA-approved CPA\n"
                "3. Subpoena utility records for all 48 units against HUD occupancy certification\n"
                "4. Investigate cost inflation: request contractor invoices and compare to RSMeans\n"
                "5. Check developer principal's prior LLC for similar patterns"
            ),
        ),
        "category": "CONSTRUCTION_FRAUD",
        "source": "IRS_CI",
        "difficulty": "advanced",
    },

    {
        "instruction": "What are the red flags for change order abuse in construction fraud? Explain how the mechanism works and what documentation ELIOT should flag.",
        "input": (
            "Contract type: Fixed-price GMP (Guaranteed Maximum Price) contract for commercial "
            "renovation, $2.1 million. Change orders issued: 23 change orders over 8 months, "
            "totaling $890,000 (42% over GMP). Owner is a foreign national LLC with no prior "
            "PA project history. Change order approvals: signed by owner representative with no "
            "supporting engineering documentation. Several change orders reference 'unforeseen "
            "conditions' — building was fully inspected pre-contract."
        ),
        "output": (
            "CHANGE ORDER ABUSE ANALYSIS\n\n"
            "MECHANISM OF FRAUD:\n"
            "The fixed-price/GMP contract is the ideal vehicle for change order abuse because it "
            "creates a protected baseline, then allows incremental additions that bypass competitive "
            "bidding. Fraudulent change orders operate by:\n"
            "1. Winning contract at realistic price\n"
            "2. Claiming phantom 'unforeseen conditions' to justify additions\n"
            "3. Owner representative approves without engineering review (often co-conspirator)\n"
            "4. Funds extracted through change orders return to beneficial owner via kickback\n\n"
            "RED FLAGS IN THIS CASE:\n\n"
            "VOLUME/FREQUENCY: 23 change orders on an 8-month project = nearly 3/month. "
            "DOJ construction fraud cases document CO frequency as a primary indicator.\n\n"
            "MAGNITUDE: 42% over GMP is extreme. Standard deviation from GMP on commercial "
            "renovation is typically 5–15%. 42% triggers audit requirement under most lender protocols.\n\n"
            "'UNFORESEEN CONDITIONS' ON INSPECTED BUILDING: Building was fully inspected pre-contract. "
            "Claiming unforeseen conditions on an inspected structure is a documented fraud pretext.\n\n"
            "FOREIGN NATIONAL OWNER + NO ENGINEERING REVIEW: Combination of non-local owner "
            "(limited market knowledge) + missing engineering documentation on CO approvals = "
            "classic construction fraud setup.\n\n"
            "DOCUMENTATION ELIOT SHOULD REQUEST:\n"
            "- Pre-bid inspection report vs. each 'unforeseen condition' CO\n"
            "- Engineering or architect sign-off on each CO (should be standard)\n"
            "- CO payment recipients — are they actual subcontractors or related entities?\n"
            "- Owner representative's relationship to GC (investigate conflict of interest)\n\n"
            "SOURCE: DOJ construction fraud prosecutions; Benjamin Cartwright domain expertise "
            "(direct construction industry knowledge of change order abuse patterns)."
        ),
        "category": "CONSTRUCTION_FRAUD",
        "source": "DOMAIN_EXPERT",
        "difficulty": "intermediate",
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # CATEGORY 4: COMMERCIAL PROPERTY FRAUD
    # ═══════════════════════════════════════════════════════════════════════════

    {
        "instruction": "Analyze this commercial property for organized crime front business indicators per FBI documented typologies.",
        "input": (
            "Business: 'Riverside Lounge' — bar and restaurant, Pittsburgh PA. "
            "Monthly reported gross revenue: $28,000. "
            "Monthly cash deposits: $41,000. "
            "Seating capacity: 45. "
            "Business hours: 5pm–11pm Tuesday–Sunday (54 hours/week). "
            "Average cover/spend per customer in comparable Pittsburgh establishments: $25–35. "
            "At max capacity every operating hour: 45 seats × 54 hours × $35 = $85,050 theoretical maximum. "
            "Business owned by LLC with same beneficial owner as two other cash-heavy businesses "
            "(car wash and laundromat) within 1 mile. "
            "Business has received no health inspections in 18 months despite requirement."
        ),
        "output": make_report(
            case_id="ELIOT-SEED-007",
            subject="Riverside Lounge LLC — Front Business Cash Laundering",
            risk_score="HIGH",
            typology_flags=["FRONT_BUSINESS_CASH_LAUNDERING", "CASH_CO_MINGLING", "ORGANIZED_CRIME_PATTERN"],
            findings=(
                "Business presents a documented front business cash laundering pattern consistent "
                "with FBI financial crime typologies.\n\n"
                "DEPOSIT-TO-REVENUE DISCREPANCY: Monthly cash deposits ($41,000) exceed reported "
                "gross revenue ($28,000) by $13,000/month (46% premium). This is the defining "
                "indicator of cash co-mingling — criminal cash is deposited as business revenue "
                "to launder it through the bank account.\n\n"
                "CAPACITY ANALYSIS: Theoretical maximum revenue at full capacity, full hours: "
                "$85,050/month. Reported revenue $28,000 = 33% of theoretical max (plausible for "
                "a bar). But deposits exceeding reported revenue means cash IN exceeds cash declared — "
                "excess $13,000/month is the criminal cash being laundered.\n\n"
                "CLUSTER OF CASH BUSINESSES: Same beneficial owner holds bar, car wash, and laundromat "
                "within 1 mile. All three are cash-heavy businesses. This clustering pattern is "
                "documented in organized crime ML prosecutions — multiple cash fronts allow higher-volume "
                "laundering with each individual business appearing below suspicion threshold.\n\n"
                "REGULATORY AVOIDANCE: No health inspection in 18 months despite requirement. Legitimate "
                "businesses accept routine inspections. Avoidance suggests concern about regulatory "
                "scrutiny extending to financial records."
            ),
            evidence_chain=(
                "- Bank deposit records vs. POS/reported revenue\n"
                "- Business license records: seating capacity\n"
                "- Comparable establishment revenue analysis (Pittsburgh market)\n"
                "- PA SOS: beneficial owner across three LLCs\n"
                "- Allegheny County health inspection records (gap)\n"
                "- FBI front business typology documentation"
            ),
            confidence="HIGH — deposits exceeding revenue is textbook cash co-mingling",
            leads=(
                "1. Request full 24-month bank records for all three businesses under same owner\n"
                "2. Summons daily POS/register records vs. deposit records\n"
                "3. Investigate source of excess cash — identify criminal activity generating funds\n"
                "4. Run beneficial owner against organized crime databases\n"
                "5. Request tax returns for all three businesses — compare to deposits"
            ),
        ),
        "category": "COMMERCIAL_FRAUD",
        "source": "FBI",
        "difficulty": "advanced",
    },

    {
        "instruction": "Explain the commercial arson-for-insurance fraud pattern documented in organized crime prosecutions. What are the stages and what documentation indicates fraud?",
        "input": (
            "Detective is reviewing a commercial fire claim. Property: restaurant/bar in Pittsburgh. "
            "Purchase price 2 years ago: $340,000. Insurance policy at time of fire: $875,000. "
            "Insurance policy increased from $340,000 to $875,000 fourteen months after purchase. "
            "Fire origin: multiple points of origin per fire marshal report. "
            "Cause: undetermined (accelerant suspected, not confirmed). "
            "Owner: filed for business bankruptcy 6 weeks before fire. "
            "Previous owner of property: sold under financial distress."
        ),
        "output": (
            "ARSON-FOR-INSURANCE FRAUD ANALYSIS\n\n"
            "DOCUMENTED PATTERN (FBI / Henry Hill FBI Debriefings / DOJ Arson Prosecutions):\n\n"
            "STAGE 1 — ACQUISITION: Purchase distressed commercial property at below-market price. "
            "Seller is motivated (foreclosure, financial distress) — acquisition appears legitimate.\n\n"
            "STAGE 2 — INSURANCE INFLATION: Increase insurance coverage significantly above "
            "purchase price and market value. A 14-month lag (as in this case) allows coverage "
            "to appear established, not recently acquired. Standard fraud investigation threshold: "
            "coverage >150% of assessed value with recent increase.\n\n"
            "STAGE 3 — FINANCIAL DISTRESS STAGING: Owner creates documented financial distress "
            "(bankruptcy filing, delinquency) that provides apparent motive for desperate act — "
            "but in organized crime schemes, the distress is staged to support the insurance claim "
            "narrative.\n\n"
            "STAGE 4 — FIRE: Professional torch or owner-set fire. Multiple points of origin "
            "(as in this case) is the primary fire marshal indicator of incendiary origin. "
            "Single-origin fires are accidental; multiple-origin fires indicate deliberate setting.\n\n"
            "STAGE 5 — CLAIM: Insurance proceeds replace criminal investment + provide profit margin. "
            "Clean proceeds from insurance company.\n\n"
            "RED FLAGS IN THIS CASE:\n"
            "- Coverage 257% of purchase price ($875K vs. $340K): extreme over-insurance\n"
            "- Coverage increase 14 months post-purchase: suspicious timing\n"
            "- Bankruptcy filed 6 weeks pre-fire: textbook distress staging\n"
            "- Multiple points of origin: fire marshal indicator of incendiary\n"
            "- Distressed prior seller: established acquisition-at-discount pattern\n\n"
            "DOCUMENTATION TO REQUEST:\n"
            "- Insurance application and all subsequent endorsements/increases\n"
            "- Insurance broker identity and relationship to owner\n"
            "- Fire marshal full report including accelerant testing results\n"
            "- Bankruptcy filing documents and creditor list\n"
            "- Owner's financial records 24 months pre-fire\n\n"
            "SOURCE: FBI arson fraud documentation; Henry Hill FBI debriefings (bar/restaurant "
            "burning pattern); DOJ organized crime arson prosecutions."
        ),
        "category": "COMMERCIAL_FRAUD",
        "source": "FBI",
        "difficulty": "intermediate",
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # CATEGORY 5: TITLE / DEED FRAUD
    # ═══════════════════════════════════════════════════════════════════════════

    {
        "instruction": "Identify deed fraud indicators in this property transfer scenario.",
        "input": (
            "Property owner: elderly widow, Allegheny County PA. "
            "Property: paid-off single family home, assessed value $195,000. "
            "Owner's son reports: mother received letter from a title company she doesn't recognize "
            "stating she is 'behind on refinance payments.' "
            "County recorder search: deed transfer recorded 8 months ago to 'Keystone Property "
            "Solutions LLC.' Owner has no recollection of signing anything. "
            "Mortgage of $155,000 recorded against property in LLC's name. "
            "Notary on deed transfer: same notary has appeared on 4 other disputed deed transfers "
            "in Allegheny County in past 18 months."
        ),
        "output": make_report(
            case_id="ELIOT-SEED-008",
            subject="Keystone Property Solutions LLC — Deed Fraud / Title Theft",
            risk_score="HIGH",
            typology_flags=["DEED_FRAUD", "TITLE_THEFT", "ELDER_FINANCIAL_EXPLOITATION"],
            findings=(
                "Transaction presents a deed fraud / title theft pattern with elder financial "
                "exploitation indicators:\n\n"
                "FORGED DEED TRANSFER: Owner has no knowledge of deed transfer. Paid-off property "
                "now carries $155,000 mortgage in LLC's name — equity extraction following "
                "unauthorized title transfer is the standard deed fraud monetization mechanism.\n\n"
                "SUSPICIOUS NOTARY: Same notary on 4 other disputed Allegheny County deed transfers "
                "in 18 months. DOJ deed fraud prosecutions document notary co-conspirators who "
                "certify signers who were never present. This pattern is definitive — notary "
                "is likely a co-conspirator or at minimum subject to serious investigation.\n\n"
                "ELDER TARGETING: Elderly property owner with paid-off home is the primary deed "
                "fraud target profile. Clear title + limited monitoring of property records + "
                "potential cognitive vulnerability. PA elder financial exploitation statutes apply.\n\n"
                "EQUITY EXTRACTION: $155,000 mortgage on $195,000 property = 79% LTV. "
                "Fraudster has extracted $155,000 in clean mortgage proceeds; owner left with "
                "encumbered title she doesn't know she 'owns.'"
            ),
            evidence_chain=(
                "- Allegheny County deed transfer record\n"
                "- Mortgage recording in LLC's name\n"
                "- Owner statement (no knowledge of transfer)\n"
                "- Notary appearance record across 5 transfers\n"
                "- PA elder financial exploitation statute (18 Pa.C.S. §3922.1)"
            ),
            confidence="HIGH — owner denial + pattern notary = fraud",
            leads=(
                "1. Refer to PA OAG for deed fraud + elder financial exploitation\n"
                "2. Seek immediate lis pendens on property to halt any further transfer\n"
                "3. Subpoena notary for records of all 5 deed transfers\n"
                "4. Identify Keystone Property Solutions LLC principals\n"
                "5. Check for additional victims through notary's signature history\n"
                "6. Request county recorder to flag for future transactions on this property"
            ),
        ),
        "category": "TITLE_DEED_FRAUD",
        "source": "COMPOSITE",
        "difficulty": "intermediate",
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # CATEGORY 6: TAX / ASSESSMENT FRAUD
    # ═══════════════════════════════════════════════════════════════════════════

    {
        "instruction": "Analyze this property assessment pattern for tax fraud indicators.",
        "input": (
            "Developer owns a 14-acre parcel in Allegheny County zoned commercial. "
            "Assessed value: $180,000 (assessed as agricultural/green space). "
            "Market comparable sales in same corridor: $1.2–1.8M per acre for commercial land. "
            "Developer has active development permit applications for same parcel showing "
            "commercial mixed-use development. "
            "County assessor who approved agricultural classification: recently retired, "
            "now employed as a consultant to the developer. "
            "Developer has received no tax bills consistent with commercial zoning for 6 years."
        ),
        "output": make_report(
            case_id="ELIOT-SEED-009",
            subject="14-acre Allegheny County parcel — Assessment Fraud / Corruption",
            risk_score="HIGH",
            typology_flags=["ASSESSMENT_FRAUD", "PUBLIC_CORRUPTION", "TAX_EVASION"],
            findings=(
                "Pattern presents assessment manipulation with public corruption indicators:\n\n"
                "ASSESSMENT DISCREPANCY: Agricultural/green space assessment at $180,000. "
                "Market value per comparable commercial land sales: $16.8M–$25.2M (94× to 140× "
                "the assessed value). Tax loss on differential: substantial. PA common-level ratio "
                "framework requires assessment to track market — this is a deliberate non-compliance.\n\n"
                "INTERNAL INCONSISTENCY: Developer's own permit applications document commercial "
                "intent on the same parcel assessed as agricultural. This is documentary proof the "
                "agricultural classification is fraudulent — developer disclosed commercial use to "
                "permit office while maintaining fraudulent agricultural assessment.\n\n"
                "REVOLVING DOOR / CORRUPTION INDICATOR: Assessor who approved classification now "
                "employed as developer consultant. Classic public corruption pattern — assessment "
                "favor in exchange for post-employment benefit. This is both an ethics violation "
                "and potentially a bribery offense under PA law.\n\n"
                "6-YEAR TAX LOSS: Ongoing tax evasion at municipal/county/school district level "
                "for 6 years. Estimated annual tax loss (applying commercial millage to market value) "
                "requires precise millage calculation but likely millions over the 6-year period."
            ),
            evidence_chain=(
                "- Allegheny County assessment records (agricultural classification)\n"
                "- Comparable commercial land sales in corridor\n"
                "- Developer's own permit applications (commercial development)\n"
                "- Former assessor employment record → developer consulting\n"
                "- 6-year tax billing records vs. commercial millage calculation"
            ),
            confidence="HIGH — permit application vs. assessment is self-documenting fraud",
            leads=(
                "1. Refer to PA Ethics Commission (assessor post-employment)\n"
                "2. Refer to PA OAG (public corruption + tax evasion)\n"
                "3. Notify Allegheny County Board of Assessment Appeals for reclassification\n"
                "4. Calculate back-tax liability with commercial millage\n"
                "5. Review assessor's other decisions involving this developer in 6-year window"
            ),
        ),
        "category": "TAX_ASSESS_FRAUD",
        "source": "DOMAIN_EXPERT",
        "difficulty": "advanced",
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # META — Orchestration, Multi-Typology, Report Writing
    # ═══════════════════════════════════════════════════════════════════════════

    {
        "instruction": "A detective has submitted a case packet involving multiple potentially related real estate transactions. Perform an initial triage analysis and identify which ELIOT typologies apply. Route to appropriate investigative streams.",
        "input": (
            "CASE PACKET — Detective J. Morrison, Allegheny County DA Economic Crimes Unit:\n"
            "1. Three all-cash residential purchases in Squirrel Hill by LLCs with Delaware registration\n"
            "2. One commercial property (bar/restaurant) with deposits exceeding reported revenue\n"
            "3. Active construction project with disputed draw request\n"
            "4. One foreclosure rescue company recently incorporated, multiple complaints\n"
            "All subjects share a common attorney who appears on filings for all four matters."
        ),
        "output": (
            "ELIOT TRIAGE ANALYSIS — Case Packet Morrison / Allegheny County DA\n\n"
            "INITIAL ASSESSMENT: Four streams with potential common thread (shared attorney). "
            "Recommend parallel investigation with coordination.\n\n"
            "STREAM 1 — RESIDENTIAL LLC PURCHASES (Items 1)\n"
            "Typology: MONEY_LAUNDERING (Shell Company / Possible CMLN pattern)\n"
            "Priority: HIGH — all-cash + Delaware LLC + secondary market cluster\n"
            "Route to: FinCEN 314(b) information sharing; Delaware SOS subpoena; "
            "cross-reference LLC formations against common attorney\n\n"
            "STREAM 2 — COMMERCIAL PROPERTY (Item 2)\n"
            "Typology: COMMERCIAL_FRAUD (Front Business Cash Laundering)\n"
            "Priority: HIGH — deposit/revenue discrepancy is definitive indicator\n"
            "Route to: Bank records subpoena; POS records; beneficial owner investigation\n\n"
            "STREAM 3 — CONSTRUCTION DRAW DISPUTE (Item 3)\n"
            "Typology: CONSTRUCTION_FRAUD (Draw Fraud / Possible Ghost Subcontractors)\n"
            "Priority: MEDIUM — requires independent inspection and permit records\n"
            "Route to: Lender notification; independent inspector; permit records pull\n\n"
            "STREAM 4 — FORECLOSURE RESCUE (Item 4)\n"
            "Typology: MORTGAGE_FRAUD (Foreclosure Rescue Fraud)\n"
            "Priority: HIGH — recent incorporation + multiple complaints = active scheme\n"
            "Route to: PA OAG Consumer Protection; victim interviews; title search on all properties\n\n"
            "COMMON THREAD — SHARED ATTORNEY:\n"
            "Attorney appearing across all four matters is the highest-priority investigative target. "
            "Possible roles: LLC formation agent, knowing facilitator, or money laundering professional. "
            "Recommend: Pennsylvania Bar discipline referral if warranted; grand jury subpoena for "
            "LLC formation files (non-privileged business records); check attorney against FinCEN "
            "SARs filed by financial institutions.\n\n"
            "NEXT STEP FOR ATREIDES: Route Streams 1–4 to parallel sub-investigations. "
            "Consolidate findings at 30-day mark for unified report."
        ),
        "category": "META",
        "source": "COMPOSITE",
        "difficulty": "advanced",
    },

    {
        "instruction": "What is ELIOT's mandate and what are its operational limits?",
        "input": "A detective asks: 'Can ELIOT tell me if this person is guilty of money laundering?'",
        "output": (
            "ELIOT MANDATE AND OPERATIONAL LIMITS\n\n"
            "ELIOT's mandate: Analyze documented financial records, transaction patterns, "
            "property records, and corporate structures to identify patterns consistent with "
            "documented financial crime typologies. ELIOT produces analytical reports for "
            "human investigators to verify and act upon.\n\n"
            "ELIOT CANNOT AND DOES NOT:\n"
            "- Determine guilt. Guilt is determined by a jury or court.\n"
            "- Make legal conclusions. ELIOT identifies patterns; attorneys make legal arguments.\n"
            "- Conduct surveillance. ELIOT analyzes submitted documents only.\n"
            "- Access non-public databases without proper legal authority.\n"
            "- Replace human investigators. ELIOT surfaces leads; investigators verify them.\n\n"
            "WHAT ELIOT CAN DO:\n"
            "- Identify financial patterns that match documented FinCEN, FBI, and DOJ typologies\n"
            "- Assign risk scores based on the number and severity of red flags present\n"
            "- Recommend specific investigative steps to verify or refute identified patterns\n"
            "- Produce structured analytical reports with documented evidence chains\n"
            "- Cross-reference multiple transactions to surface patterns invisible in isolation\n\n"
            "ANSWER TO DETECTIVE: ELIOT cannot tell you whether this person is guilty. "
            "ELIOT can tell you whether the financial records you've submitted match the patterns "
            "documented by FinCEN, the FBI, and the Department of Justice as indicative of "
            "money laundering. All ELIOT findings require your verification and judgment before "
            "any enforcement action."
        ),
        "category": "META",
        "source": "COMPOSITE",
        "difficulty": "basic",
    },

    {
        "instruction": "Explain why small law enforcement agencies are particularly vulnerable to missing real estate financial crime.",
        "input": "A borough police chief asks why ELIOT is necessary for a department of 12 officers.",
        "output": (
            "WHY SMALL DEPARTMENTS MISS REAL ESTATE FINANCIAL CRIME\n\n"
            "Real estate financial crime is structurally designed to be invisible at the transaction "
            "level. Here is why small departments cannot catch it without analytical support:\n\n"
            "1. INDIVIDUAL TRANSACTIONS LOOK LEGITIMATE\n"
            "Each individual real estate closing, LLC formation, or cash deposit appears normal "
            "in isolation. A $385,000 all-cash sale is not unusual. An LLC buying property is not "
            "unusual. A wire from overseas is not unusual. The crime only becomes visible when you "
            "see the pattern across multiple transactions — which requires correlating records that "
            "span multiple agencies, databases, and time periods.\n\n"
            "2. RECORD VOLUMES ARE IMPOSSIBLE TO MANUALLY REVIEW\n"
            "Allegheny County alone records tens of thousands of deed transfers per year. "
            "Manual review for red flag patterns is not feasible for a 12-officer department "
            "with homicides, robberies, and traffic enforcement as competing priorities.\n\n"
            "3. FINANCIAL CRIME DOESN'T LOOK LIKE CRIME\n"
            "There are no victims calling 911. There is no crime scene. The 'evidence' is in "
            "deed records, LLC filings, bank statements, and construction invoices — document "
            "types that patrol officers don't encounter and may not know how to analyze.\n\n"
            "4. ELIOT'S VALUE FOR SMALL DEPARTMENTS\n"
            "ELIOT correlates across transactions that a single officer could never review: "
            "multiple properties with the same LLC registered agent, the same beneficial owner "
            "across different entity names, timing correlations between foreign wires and "
            "closings, construction cost anomalies against RSMeans benchmarks. "
            "ELIOT does the pattern work; your investigators do the verification and enforcement.\n\n"
            "SOURCE: FinCEN 'The Diffuse Corruption Model'; FATF ML through Real Estate typologies; "
            "Benjamin Cartwright domain expertise on construction industry fraud visibility."
        ),
        "category": "META",
        "source": "DOMAIN_EXPERT",
        "difficulty": "basic",
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # R5: ELDER FINANCIAL FRAUD + WIRE FRAUD (FTC / FBI IC3)
    # Sources: ELIOT_R5_Elder_Wire_Fraud_Research_v1.md
    # ═══════════════════════════════════════════════════════════════════════════

    {
        "instruction": "Analyze the following elder financial exploitation case for wire fraud indicators. Map to FBI IC3 and FTC documented typologies and produce a structured risk assessment.",
        "input": (
            "Victim: 74-year-old widow, Allegheny County PA. Fixed income: Social Security + pension. "
            "Bank records (subpoenaed): Three domestic wires over 11 days totaling $287,000. "
            "Wire 1 ($92,000): beneficiary 'Global Secure Holdings LLC' — account at regional bank, "
            "opened 6 days before wire. Wire 2 ($118,000): beneficiary 'Atlas Treasury Services' — "
            "account at different institution, opened 4 days prior. Wire 3 ($77,000): international wire "
            "to Hong Kong business account. Victim's son reports: mother received pop-up 'virus alert,' "
            "called displayed number, allowed remote access (TeamViewer). Caller chain: 'Microsoft support' "
            "→ 'Chase fraud department' → person claiming 'Federal Reserve asset protection unit.' "
            "Victim told not to discuss transfers with family or branch staff. No prior wire history "
            "in 22 years of account statements. Victim still believes funds are in 'protected alias account.'"
        ),
        "output": make_report(
            case_id="ELIOT-SEED-010",
            subject="74-year-old widow — Phantom Hacker wire fraud cluster / Allegheny County PA",
            risk_score="HIGH",
            typology_flags=[
                "ELDER_FINANCIAL_EXPLOITATION",
                "PHANTOM_HACKER_SCAM",
                "WIRE_FRAUD",
                "GOVERNMENT_IMPERSONATION",
                "TECH_SUPPORT_FRAUD",
            ],
            findings=(
                "Transaction pattern matches the FBI IC3 'Phantom Hacker' scam typology "
                "(PSA I-091223-PSA, September 29, 2023) — a three-phase layered impersonation "
                "scheme documented as a nationwide increase targeting senior citizens.\n\n"
                "PHASE MATCH — TECH SUPPORT (IC3): Remote-access software installed after "
                "unsolicited pop-up contact. Scammer surveyed accounts to identify liquidation targets "
                "before directing transfers.\n\n"
                "PHASE MATCH — FINANCIAL INSTITUTION IMPERSONATION (IC3): Sequential wires to "
                "newly opened domestic accounts ('Global Secure Holdings LLC,' 'Atlas Treasury Services') "
                "are consistent with mule-account layering. IC3 documents instruction to move funds to "
                "'safe' third-party accounts under false fraud-department authority.\n\n"
                "PHASE MATCH — GOVERNMENT IMPERSONATION (IC3): 'Federal Reserve asset protection unit' "
                "persona matches documented Phase 3. IC3 PSA explicitly states: US Government will "
                "NEVER request wire transfers to foreign accounts, cryptocurrency, or gift cards.\n\n"
                "WIRE FRAUD INDICATORS (IC3 2023 Elder Fraud Report / RAT guidance): "
                "(1) First-ever wire activity on 22-year account; "
                "(2) Multiple staged wires over 11 days ($287K total) — matches Phantom Hacker "
                "multi-transaction drain pattern; "
                "(3) International wire terminus (Hong Kong) following domestic layering; "
                "(4) Secrecy instruction ('do not discuss with family or branch staff') — core "
                "IC3-documented manipulation tactic; "
                "(5) Beneficiary accounts opened 4–6 days pre-wire — mule account formation pattern.\n\n"
                "VICTIM RED FLAGS (FTC / IC3): Age 60+ (IC3 2023: over-60 victims = 58% of call-center "
                "fraud losses despite 40% of complainants); social isolation risk; continued belief funds "
                "are 'protected' — revictimization risk per IC3 recovery-scam advisories.\n\n"
                "PA CONTEXT: IC3 2023 Elder Report ranks Pennsylvania 7th nationally in over-60 "
                "complaints (3,020) and 7th in losses ($117.4M)."
            ),
            evidence_chain=(
                "- Bank wire records: 3 transfers, $287,000, 11-day window\n"
                "- Account history: zero prior wires in 22 years\n"
                "- Beneficiary account opening dates (4–6 days pre-wire)\n"
                "- TeamViewer installation log on victim's computer\n"
                "- Victim/son statements: impersonation chain + secrecy instruction\n"
                "- FBI IC3 PSA I-091223-PSA (Phantom Hacker typology)\n"
                "- FBI IC3 2023 Elder Fraud Annual Report (wire/BEC statistics)\n"
                "- FTC Data Spotlight Aug 2025 (impersonation escalation to retirement accounts)"
            ),
            confidence="HIGH — direct Phantom Hacker typology match on 5 of 5 IC3-documented phases/indicators",
            leads=(
                "1. File IC3 complaint immediately with full wire details for RAT/FFKC freeze eligibility\n"
                "2. Contact originating bank for recall on all three wires + Hold Harmless Letter\n"
                "3. Subpoena beneficiary institutions for account opening KYC and IP/device logs\n"
                "4. Trace 'Global Secure Holdings LLC' / 'Atlas Treasury Services' — state SOS filings\n"
                "5. Refer to PA OAG Elder Abuse Unit + Adult Protective Services (18 Pa.C.S. §3922.1)\n"
                "6. Interview victim for full impersonation timeline before revictimization by 'recovery' scam\n"
                "7. Cross-reference Hong Kong wire with FinCEN Rapid Response Program if international"
            ),
        ),
        "category": "META",
        "source": "IC3",
        "difficulty": "advanced",
    },

    {
        "instruction": "What wire fraud and elder financial exploitation indicators should ELIOT flag, per FTC and FBI IC3 public reports? Provide detection indicators and victim red flags with source citations.",
        "input": (
            "A detective asks ELIOT for a reference checklist before reviewing bank subpoenas "
            "in an elder exploitation case involving suspected wire fraud. Request: separate "
            "transaction-level detection indicators from victim behavioral red flags. Cite "
            "FTC and IC3 public reports only."
        ),
        "output": (
            "ELIOT REFERENCE: ELDER FINANCIAL FRAUD + WIRE FRAUD INDICATORS\n"
            "(FTC + FBI IC3 Public Reports)\n\n"
            "SCALE CONTEXT:\n"
            "- IC3 2023 Elder Fraud Report: 101,068 complaints (60+), $3.4B losses; "
            "5,920 victims lost >$100K each\n"
            "- IC3 2024 Internet Crime Report: over-60 cohort = most complaints and "
            "~$5B losses nationally\n"
            "- FTC 2024: older adults reported $2.4B in fraud losses (Consumer Sentinel)\n"
            "- FTC Aug 2025: >4× increase in impersonation reports stealing tens–hundreds of "
            "thousands from older adults\n\n"
            "DETECTION INDICATORS — TRANSACTION / FINANCIAL:\n"
            "1. First-ever or unusual wire from elder account (FinCEN FIN-2022-A002 via "
            "Interagency Statement; IC3 RAT wire guidance)\n"
            "2. Multiple wires over days/weeks to different beneficiaries (IC3 Phantom Hacker PSA)\n"
            "3. Wire to overseas account when victim has no foreign ties (IC3 PSA I-091223)\n"
            "4. Beneficiary accounts opened days before receiving wire (IC3 mule pattern)\n"
            "5. Liquidation sequence: checking → savings → retirement → wire (FTC impersonation "
            "Data Spotlight, Aug 2025)\n"
            "6. BEC/closing-wire variant: last-minute change to real estate wire instructions "
            "(IC3 BEC definition; RAT FFKC real-estate-nexus cases)\n"
            "7. Cash withdrawal → crypto ATM → transfer (IC3 2023: 2,000+ crypto ATM complaints, 60+)\n"
            "8. Government-name beneficiary ('Federal Reserve,' 'Treasury') — IC3: US Government "
            "NEVER requests wire to foreign accounts\n\n"
            "VICTIM RED FLAGS — BEHAVIORAL / SITUATIONAL:\n"
            "1. Age 60+ with disproportionate loss exposure (IC3: 40% of call-center complainants "
            "but 58% of losses)\n"
            "2. Secrecy instruction: told not to tell family, bank staff, or police (IC3 Phantom Hacker)\n"
            "3. Urgency/fear: believes accounts actively compromised (FTC 'false alarm' pattern)\n"
            "4. Remote access granted to unsolicited tech support caller (IC3 Tech Support #1 crime "
            "type by volume for 60+)\n"
            "5. Three-phase trust chain: tech support → bank → government (IC3 PSA I-091223)\n"
            "6. Romance/confidence relationship progressing to wire request (IC3: $357M romance "
            "losses, 60+, 2023)\n"
            "7. Grandparent emergency: wire demanded immediately for 'legal fees' (IC3: 200+ complaints, "
            "~$2.3M, 2023)\n"
            "8. Compliance with courier cash/gold pickup (IC3 2023: $55M+ May–Dec trend)\n"
            "9. Post-victimization shame/delayed reporting; susceptibility to 'recovery' scams (IC3 PSA)\n\n"
            "IMMEDIATE ACTIONS (IC3 RAT):\n"
            "- Contact originating bank for recall/reversal immediately upon fraud recognition\n"
            "- File www.ic3.gov complaint with complete banking details\n"
            "- Report to FTC at ReportFraud.ftc.gov\n\n"
            "SOURCES:\n"
            "- FBI IC3 2023 Elder Fraud Annual Report "
            "(ic3.gov/annualreport/reports/2023_ic3elderfraudreport.pdf)\n"
            "- FBI IC3 2024 Internet Crime Report (ic3.gov/AnnualReport/Reports/2024_IC3Report.pdf)\n"
            "- FBI IC3 PSA I-091223-PSA Phantom Hacker (ic3.gov/PSA/2023/PSA230929)\n"
            "- FTC Protecting Older Consumers 2024–2025 Report\n"
            "- FTC Data Spotlight: False Alarm, Real Scam (Aug 2025)\n"
            "- FinCEN Advisory FIN-2022-A002 Elder Financial Exploitation (June 2022)"
        ),
        "category": "META",
        "source": "COMPOSITE",
        "difficulty": "basic",
    },

    {
        "instruction": "Analyze this real estate closing wire fraud case with elder victim indicators per IC3 BEC and elder fraud documentation.",
        "input": (
            "Transaction: Residential purchase, Allegheny County PA. Buyer: 68-year-old retiree, "
            "all-cash purchase ($340,000) funded from retirement account. Three days before closing, "
            "buyer's email account receives message appearing to be from title company with "
            "revised wire instructions — new account at credit union, different from original "
            "settlement statement. Buyer initiates wire. Title company reports never sending revised "
            "instructions. Seller is legitimate; property exists. Buyer's email shows rule forwarding "
            "to external address set 5 days prior. Buyer did not verbally verify wire change — "
            "relied on email only. Buyer reports embarrassment and reluctance to report. "
            "No prior real estate transactions in 15 years."
        ),
        "output": make_report(
            case_id="ELIOT-SEED-011",
            subject="68-year-old retiree — BEC real estate closing wire fraud / Allegheny County PA",
            risk_score="HIGH",
            typology_flags=[
                "BEC_WIRE_FRAUD",
                "ELDER_FINANCIAL_EXPLOITATION",
                "REAL_ESTATE_WIRE_FRAUD",
                "EMAIL_COMPROMISE",
            ],
            findings=(
                "Transaction matches FBI IC3 Business Email Compromise (BEC) typology applied to "
                "real estate closing — explicitly documented in IC3 2023 Elder Fraud Report as a "
                "top crime type for Financial Fraud Kill Chain (FFKC) recovery cases, including "
                "BEC with real estate nexus.\n\n"
                "BEC MECHANISM (IC3 Appendix A definition): Fraudster compromises email or "
                "communication channel, impersonates trusted party (title company), and conducts "
                "unauthorized wire transfer. Email rule forwarding to external address confirms "
                "account compromise vector.\n\n"
                "ELDER VULNERABILITY FACTORS (IC3 2023 / FTC): Victim age 68; no real estate "
                "transaction in 15 years (unfamiliarity with closing process); reliance on email "
                "without verbal verification — IC3 RAT guidance explicitly requires verifying payment "
                "changes with intended recipient. Post-victimization shame/reluctance to report is "
                "documented IC3 barrier — victims over 60 filed 101,068 complaints in 2023 but "
                "reporting is known to undercount actual victimization.\n\n"
                "REAL ESTATE NEXUS (IC3 2023, over 60): Real Estate crime type = 1,498 complaints, "
                "$65.6M losses. BEC losses (60+) = $382.4M — closing wire fraud is high-value "
                "subset. All-cash purchase from retirement account maximizes victim loss severity "
                "(IC3: 5,920 victims lost >$100K in 2023).\n\n"
                "RED FLAGS PRESENT: (1) Last-minute wire instruction change; (2) Email-only "
                "verification, no callback to known title number; (3) New beneficiary account at "
                "different institution; (4) Email compromise artifact (forwarding rule); "
                "(5) Elder buyer with infrequent transaction experience."
            ),
            evidence_chain=(
                "- Original vs. fraudulent wire instruction emails (headers, routing)\n"
                "- Email account forwarding rule (set 5 days pre-wire)\n"
                "- Bank wire confirmation: beneficiary credit union account\n"
                "- Title company denial of instruction change\n"
                "- IC3 BEC definition (2023 Elder Fraud Report Appendix A)\n"
                "- IC3 RAT FFKC: BEC + real estate nexus case category\n"
                "- IC3 wire verification guidance (contact originating institution immediately)"
            ),
            confidence="HIGH — email compromise + unauthorized wire instruction change = textbook BEC",
            leads=(
                "1. File IC3 complaint immediately — include both bank accounts and email headers\n"
                "2. Originating bank recall request + recipient credit union freeze via RAT/FFKC\n"
                "3. Forensic analysis of buyer email account (forwarding rules, login IPs)\n"
                "4. Identify credit union account opener — KYC documents, surveillance if in-branch\n"
                "5. Check county recorder for simultaneous deed fraud attempts on victim's other assets\n"
                "6. Refer victim to DOJ National Elder Fraud Hotline (833-372-8311) — overcome reporting reluctance"
            ),
        ),
        "category": "TITLE_DEED_FRAUD",
        "source": "IC3",
        "difficulty": "intermediate",
    },

    {
        "instruction": "Analyze this grandparent wire fraud report and identify IC3-documented indicators and investigative priorities.",
        "input": (
            "Caller report: 81-year-old grandfather in Pittsburgh received call at 6:45 AM from "
            "person claiming to be his grandson. Caller said he was arrested after car accident, "
            "needed bail money, asked grandfather not to tell parents. Caller sounded 'slightly off' "
            "but used grandson's name. Second caller claimed to be 'public defender' providing "
            "wire instructions. Grandfather wired $18,500 to account in New Jersey same morning. "
            "Grandfather later called grandson directly — grandson was home, unaware. Grandfather "
            "refuses to file police report due to embarrassment. No prior wire transfers."
        ),
        "output": make_report(
            case_id="ELIOT-SEED-012",
            subject="81-year-old grandfather — Grandparent scam wire fraud / Pittsburgh PA",
            risk_score="HIGH",
            typology_flags=[
                "GRANDPARENT_SCAM",
                "ELDER_FINANCIAL_EXPLOITATION",
                "WIRE_FRAUD",
                "CONFIDENCE_FRAUD",
            ],
            findings=(
                "Classic Grandparent Scam per FBI IC3 Confidence/Romance category documentation "
                "(IC3 2023 Elder Fraud Report). IC3 received 200+ grandparent scam complaints "
                "from individuals over 60 in 2023 with approximately $2.3 million in losses.\n\n"
                "DOCUMENTED MECHANISM (IC3 / FBI LA May 2024 release): Criminal impersonates "
                "panicked loved one (grandchild, niece, nephew) claiming emergency (arrest, accident, "
                "hospital). Second impersonator (attorney, police, public defender) provides "
                "payment instructions. Urgency and secrecy are core manipulation elements.\n\n"
                "INDICATORS IN THIS CASE:\n"
                "- Early morning call (disorientation tactic)\n"
                "- Emergency narrative requiring immediate wire\n"
                "- Secrecy demand ('don't tell parents')\n"
                "- Voice 'slightly off' — AI/deepfake or poor impersonation (IC3 2023 notes "
                "evolving scam tactics)\n"
                "- Second caller as authority figure providing wire instructions\n"
                "- First-ever wire from account\n"
                "- Post-incident embarrassment/refusal to report — documented IC3 underreporting factor\n\n"
                "WIRE DESTINATION: New Jersey account — domestic mule pattern consistent with "
                "IC3 RAT FFKC eligibility (domestic wire under false pretenses)."
            ),
            evidence_chain=(
                "- Caller ID records and wire timestamp (6:45 AM call, same-morning wire)\n"
                "- Bank wire record: $18,500 to NJ beneficiary\n"
                "- Grandson confirmation: no arrest, no accident\n"
                "- Victim statement: secrecy instruction + two-caller structure\n"
                "- IC3 2023 Elder Report: Grandparent Scam statistics\n"
                "- FBI IC3 PSA: Grandparent scams demanding funds by wire, mail, or courier"
            ),
            confidence="HIGH — two-caller emergency structure + verified false pretense",
            leads=(
                "1. Encourage IC3 filing despite victim reluctance — IC3 explicitly states no shame in reporting\n"
                "2. Bank recall request on NJ wire — RAT/FFKC if within window\n"
                "3. Subpoena NJ receiving bank for account opener identity\n"
                "4. Check if recipient account received other elder wires same week (pattern)\n"
                "5. Adult Protective Services notification — mandatory reporting may apply under PA law\n"
                "6. Community alert: IC3 documents grandparent scams as recurring elder threat"
            ),
        ),
        "category": "META",
        "source": "FBI",
        "difficulty": "intermediate",
    },

    {
        "instruction": "Cross-reference FTC impersonation scam patterns with IC3 call-center fraud data. What should law enforcement expect when investigating elder wire fraud clusters?",
        "input": (
            "Economic Crimes Unit reviewing Q1 pattern: 4 separate elder victims (ages 67–79) "
            "in Allegheny County, combined wire losses $412,000. Common elements: unsolicited "
            "contact, urgency, secrecy, wire to newly opened accounts. Two victims also withdrew "
            "cash for courier pickup. Unit lead asks ELIOT what the FTC and IC3 data predict "
            "about typology, recovery prospects, and revictimization risk."
        ),
        "output": (
            "ELIOT PATTERN ANALYSIS — ELDER WIRE FRAUD CLUSTER (FTC + IC3 CROSSWALK)\n\n"
            "TYPOLOGY CLASSIFICATION:\n"
            "Cluster matches IC3 'call center fraud' umbrella (Tech Support + Government "
            "Impersonation) documented as overwhelmingly targeting older adults. IC3 2023: "
            "21,213 complaints, $769M losses (60+); victims over 60 = 40% of complainants "
            "but 58% of losses. FTC Aug 2025 impersonation data spotlight confirms parallel "
            "escalation pattern: scammers move victims from checking to retirement accounts "
            "via manufactured urgency.\n\n"
            "FTC ↔ IC3 CONVERGENCE:\n"
            "- FTC: Impersonation scams (bank, government, tech, family) with escalating "
            "fund-liquidation demands\n"
            "- IC3: Phantom Hacker three-phase chain (tech → financial institution → government)\n"
            "- Both document SECRECY + URGENCY as primary manipulation vectors\n"
            "- Courier cash pickup (2 of 4 local victims) matches IC3 2023 trend: $55M+ losses "
            "May–Dec 2023 from in-person precious metals/cash collection\n\n"
            "RECOVERY PROSPECTS (IC3 RAT 2023):\n"
            "- FFKC initiated on 626 over-60 incidents ($58.2M loss); $32.1M frozen (55% recovery rate)\n"
            "- Recovery highest when: (1) reported within 24–72 hours; (2) domestic wire; "
            "(3) complete IC3 filing with banking details\n"
            "- International wire terminus reduces recovery probability — FinCEN Rapid Response "
            "for cyber-enabled fraud may apply\n\n"
            "REVICTIMIZATION RISK (IC3 + FTC):\n"
            "- IC3 documents secondary 'fund recovery' scams targeting prior victims\n"
            "- Shame/delayed reporting increases revictimization window\n"
            "- 4-victim cluster suggests active call-center campaign — additional victims likely\n\n"
            "PA DATA: IC3 2023 ranks Pennsylvania 7th in over-60 complaints (3,020) and "
            "7th in losses ($117.4M) — Allegheny County cluster is consistent with state-level "
            "pattern, not anomaly.\n\n"
            "INVESTIGATIVE PRIORITIES:\n"
            "1. Time-critical: RAT/FFKC on all domestic wires\n"
            "2. Beneficiary account KYC subpoenas — identify mule network\n"
            "3. Correlate newly opened accounts across 4 cases (common opener = organized scheme)\n"
            "4. Courier pickup locations/surveillance for ongoing collection\n"
            "5. Public IC3/FTC reporting campaign to surface unreported victims\n\n"
            "SOURCES: FBI IC3 2023 Elder Fraud Report; FBI IC3 2024 Report; FTC Data Spotlight "
            "Aug 2025; FTC Imposter Scam Press Release Jun 2026 ($3.5B/2025); IC3 PSA I-091223."
        ),
        "category": "META",
        "source": "COMPOSITE",
        "difficulty": "advanced",
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # R4: REAL-ESTATE FRAUD — DEED/TITLE, WIRE, RENTAL (FBI / FTC / STATE-AG)
    # Public alerts: spot & investigate, not commit. Sources verified 2026-06-23.
    # ═══════════════════════════════════════════════════════════════════════════

    {
        "instruction": "Analyze this online rental listing complaint for fraud indicators per FTC public alerts. Identify investigative steps.",
        "input": (
            "Complainant searched Craigslist for 2-bedroom apartment in Pittsburgh, $950/month "
            "(comparable units $1,400–$1,600). 'Landlord' claimed to be out of state on military "
            "deployment, could not show unit in person. Provided photos copied from a Zillow listing "
            "for a different property. Required $1,900 via Zelle (first month + deposit) before lease "
            "signing 'to hold the unit.' After payment, contact number disconnected. "
            "Complainant visited address — occupied by unrelated tenants with valid lease."
        ),
        "output": make_report(
            case_id="ELIOT-SEED-013",
            subject="Craigslist rental listing hijack — advance fee / phantom landlord",
            risk_score="HIGH",
            typology_flags=["RENTAL_LISTING_SCAM", "HIJACKED_LISTING", "ADVANCE_FEE_FRAUD", "PAYMENT_DIVERSION"],
            findings=(
                "Pattern matches FTC Rental Listing Scams alert (updated December 2025).\n\n"
                "HIJACKED/FABRICATED LISTING: Photos copied from legitimate Zillow listing for "
                "different property — FTC documents scammers copying pictures and descriptions from "
                "real listings and substituting their own contact information.\n\n"
                "PRICE ANOMALY: $950 vs. $1,400–$1,600 market comparables — FTC: 'If the rent is "
                "much lower than most rents in the area, it could be a sign of a scam.'\n\n"
                "UNAVAILABLE LANDLORD: Out-of-state/unavailable excuse preventing in-person showing — "
                "FTC documents scammers claiming owners are abroad or unavailable to show property.\n\n"
                "PAYMENT METHOD: Zelle payment before lease signing — FTC: wiring money, Zelle, gift "
                "cards, or cryptocurrency before seeing unit or signing lease is definitive scam "
                "indicator; 'once you send it, you probably can't get it back.'\n\n"
                "OCCUPIED PROPERTY: Address has legitimate tenants — confirms listing was fraudulent "
                "overlay on real property, not merely misrepresented vacancy."
            ),
            evidence_chain=(
                "- Craigslist ad screenshots and Zelle payment confirmation\n"
                "- Original Zillow listing showing copied photos\n"
                "- Complainant communications with fake landlord\n"
                "- On-site verification: occupied by unrelated tenants\n"
                "- FTC Rental Listing Scams (consumer.ftc.gov/articles/rental-listing-scams)\n"
                "- Market rent comparables for Pittsburgh neighborhood"
            ),
            confidence="HIGH — copied listing + below-market rent + pre-lease Zelle = FTC-documented scam",
            leads=(
                "1. Subpoena Zelle/payment processor for recipient account holder identity\n"
                "2. Reverse-image search photos to identify all platforms where listing was reposted\n"
                "3. Search address + owner name online per FTC guidance — find duplicate conflicting ads\n"
                "4. Interview legitimate tenants/landlord — may be unaware of hijacked listing\n"
                "5. Report to Craigslist, local law enforcement, and ReportFraud.ftc.gov\n"
                "6. Check for additional victims via same phone/email across rental platforms"
            ),
        ),
        "category": "META",
        "source": "FTC",
        "difficulty": "intermediate",
    },

    {
        "instruction": "Provide ELIOT's investigative checklist for detecting rental listing fraud schemes documented by the FTC.",
        "input": (
            "Economic crimes unit wants a field checklist for patrol officers responding to "
            "rental scam complaints involving online listings, advance deposits, and wire/Zelle payments."
        ),
        "output": (
            "ELIOT RENTAL LISTING FRAUD — FTC-SOURCED INVESTIGATIVE CHECKLIST\n\n"
            "TWO DOCUMENTED SCHEME TYPES (FTC Rental Listing Scams):\n\n"
            "TYPE A — HIJACKED LISTING:\n"
            "Scammers copy photos/descriptions from legitimate listings, replace agent contact info, "
            "repost on different platforms. Victim pays scammer instead of real owner/agent.\n\n"
            "TYPE B — PHANTOM LISTING:\n"
            "Scammers advertise properties not for rent or nonexistent units. Low price + pressure "
            "to decide quickly. Payment demanded before viewing or lease signing.\n\n"
            "OFFICER FIELD VERIFICATION STEPS:\n"
            "1. ADDRESS CROSS-CHECK: Search address + property owner/rental company name. Multiple "
            "ads with different contacts for same address = hijack indicator (FTC)\n"
            "2. REVERSE IMAGE SEARCH: Compare listing photos against Zillow/Realtor.com originals\n"
            "3. MARKET RENT CHECK: Rent significantly below area comparables = red flag (FTC)\n"
            "4. PHYSICAL PRESENCE: Visit property; verify occupancy status and legitimate management\n"
            "5. AGENT VERIFICATION: Request business card from licensed management company; verify ID\n"
            "6. PAYMENT METHOD: Wire, Zelle, gift card, or crypto before signed lease = scam (FTC)\n"
            "7. REPUTATION SEARCH: Owner/company name + 'complaint,' 'review,' or 'scam' (FTC)\n\n"
            "EVIDENCE TO PRESERVE:\n"
            "- All platform messages, ads, and payment confirmations\n"
            "- Phone numbers, email addresses, and payment recipient identifiers\n"
            "- Comparison between fraudulent ad and original legitimate listing\n\n"
            "REPORTING PATHS:\n"
            "- Local law enforcement (identity/payment trace)\n"
            "- Platform where ad was posted\n"
            "- FTC: ReportFraud.ftc.gov\n\n"
            "SOURCE: FTC Rental Listing Scams "
            "(https://consumer.ftc.gov/articles/rental-listing-scams), updated December 9, 2025."
        ),
        "category": "META",
        "source": "FTC",
        "difficulty": "basic",
    },

    {
        "instruction": "Analyze this distressed-homeowner outreach for deed-transfer and mortgage rescue fraud per FTC public alerts.",
        "input": (
            "Distressed homeowner, Allegheny County PA: 120 days delinquent, received postcard from "
            "'National Loan Modification Center' promising guaranteed modification. "
            "Company required $3,500 upfront fee before any services. "
            "Homeowner signed document labeled 'Deed in Lieu of Foreclosure — Temporary.' "
            "Company representative said homeowner could 'rent and buy back' the home. "
            "County recorder now shows deed transferred to National Loan Modification Center LLC. "
            "Homeowner told to make rent payments to LLC. No contact with actual mortgage lender."
        ),
        "output": make_report(
            case_id="ELIOT-SEED-014",
            subject="National Loan Modification Center LLC — Deed Transfer Rescue Fraud",
            risk_score="HIGH",
            typology_flags=["MORTGAGE_RESCUE_FRAUD", "DEED_TRANSFER_SCHEME", "UPFRONT_FEE_VIOLATION", "EQUITY_STRIPPING"],
            findings=(
                "Pattern matches FTC-documented mortgage relief and deed-transfer scams.\n\n"
                "FTC MARS RULE VIOLATION: Company charged $3,500 upfront before providing any "
                "written offer from lender or documented relief — illegal under Mortgage Assistance "
                "Relief Services (MARS) Rule. FTC: 'Don't pay a company upfront for promises to help.'\n\n"
                "DEED TRANSFER SCHEME: FTC alert documents scammers pressuring homeowners to "
                "transfer deed with promise to 'rent and buy back later.' FTC: 'As soon as you give "
                "up the deed to your home, the scammers may... evict you.' Document labeled "
                "'temporary' deed in lieu is a documented deception tactic.\n\n"
                "NO LENDER CONTACT: Scammer never engaged mortgage servicer — payments redirected to "
                "LLC while original loan continues toward foreclosure. Classic rescue fraud per "
                "FTC and state AG enforcement patterns.\n\n"
                "INVESTIGATIVE CLASSIFICATION: Fraud for profit — organized equity extraction from "
                "distressed homeowners, not legitimate loss mitigation."
            ),
            evidence_chain=(
                "- Signed 'deed in lieu' document and upfront fee receipt\n"
                "- Allegheny County deed transfer to National Loan Modification Center LLC\n"
                "- Rental payment records to LLC\n"
                "- Absence of any lender modification correspondence\n"
                "- FTC Mortgage Relief Scams (consumer.ftc.gov/articles/mortgage-relief-scams)\n"
                "- PA OAG foreclosure rescue fraud enforcement precedent"
            ),
            confidence="HIGH — upfront fee + deed transfer + rent-back promise = FTC-documented scheme",
            leads=(
                "1. Refer to FTC at ReportFraud.ftc.gov and PA OAG Bureau of Consumer Protection\n"
                "2. Seek emergency equitable relief to challenge deed transfer\n"
                "3. Subpoena LLC principals; search for parallel victims in Allegheny County\n"
                "4. Contact mortgage servicer with homeowner to halt foreclosure based on fraud\n"
                "5. Review whether company violated MARS Rule — federal enforcement referral\n"
                "6. Check company licensing: PA law requires appropriate mortgage assistance credentials"
            ),
        ),
        "category": "MORTGAGE_FRAUD",
        "source": "FTC",
        "difficulty": "intermediate",
    },

    {
        "instruction": "A state AG consumer unit refers a multi-victim deed theft ring. Perform pattern analysis and prioritize investigative streams.",
        "input": (
            "STATE AG REFERRAL — 4 homeowner complaints across Philadelphia and Allegheny County:\n"
            "1. Quit-claim deed to LLC without owner knowledge; elderly victim\n"
            "2. Forged deed with same notary as complaint #1\n"
            "3. 'Temporary' deed transfer during foreclosure rescue — victim now tenant\n"
            "4. Owner learned of sale only when new LLC filed eviction\n"
            "Common elements: 3 of 4 involve same registered agent (Wilmington DE law firm); "
            "all properties were paid-off or low-LTV; all deeds recorded within 90-day window."
        ),
        "output": (
            "ELIOT PATTERN ANALYSIS — STATE AG DEED THEFT RING REFERRAL\n\n"
            "ASSESSMENT: Coordinated deed theft / title fraud ring with overlapping mechanics "
            "documented across FBI real estate fraud reporting, FTC deed-transfer scam alerts, "
            "and state AG enforcement (deed theft criminalization in NY, CA, PA elder exploitation statutes).\n\n"
            "COMMON TYPOLOGIES:\n"
            "- TITLE_DEED_FRAUD: Unauthorized quit-claim/forged deeds (Complaints 1, 2, 4)\n"
            "- MORTGAGE_FRAUD: Rescue-to-deed-transfer scheme (Complaint 3 — FTC-documented pattern)\n"
            "- ELDER_FINANCIAL_EXPLOITATION: Complaint 1 victim profile\n\n"
            "RING INDICATORS:\n"
            "- Shared Wilmington DE registered agent across 3 complaints = shell-company formation hub\n"
            "- Same notary on Complaints 1 and 2 = potential co-conspirator or compromised notary\n"
            "- Paid-off/low-LTV targeting = maximum equity extraction per property\n"
            "- 90-day recording cluster = active campaign, not isolated incidents\n\n"
            "PRIORITY INVESTIGATIVE STREAMS:\n"
            "STREAM A — NOTARY & RECORDING: Subpoena notary journal; county recorder bulk search "
            "on notary name + registered agent for additional unreported victims\n"
            "STREAM B — LLC NETWORK: Delaware SOS subpoena for all entities using shared agent; "
            "trace principals and mortgage lenders funding post-deed equity extraction\n"
            "STREAM C — VICTIM EXPANSION: Cross-reference recorder data for quit-claims to LLCs "
            "with same agent in 12-month window across PA counties\n"
            "STREAM D — FEDERAL COORDINATION: FBI IC3 bulk filing; FinCEN SAR review if mortgage "
            "proceeds wired through shell accounts\n\n"
            "SOURCE: FBI IC3 2023 Internet Crime Report (Real Estate: 11,578 complaints, $145.2M); "
            "FTC Mortgage Relief Scams (deed transfer warnings); state AG deed theft frameworks "
            "(NY RPL §265-a; CA Civil Code §§2945.4–2945.9; PA 18 Pa.C.S. §3922.1 elder exploitation)."
        ),
        "category": "TITLE_DEED_FRAUD",
        "source": "STATE_AG",
        "difficulty": "advanced",
    },

    {
        "instruction": "Analyze this real estate closing wire transfer for BEC indicators per FBI IC3 2023 Internet Crime Report. Focus on detection and recovery, not perpetration.",
        "input": (
            "Title company reports: Buyer wiring $426,000 for residential closing in Stamford-equivalent "
            "secondary market (Allegheny County PA). Buyer received email from 'closing attorney' with "
            "wire instructions to account at institution different from settlement statement. "
            "Email sent from lookalike domain. Wire initiated; 48 hours later buyer learns attorney "
            "never changed instructions. IC3 complaint filed. Detectives need ELIOT triage on "
            "BEC typology, recovery window, and cluster detection."
        ),
        "output": make_report(
            case_id="ELIOT-SEED-015",
            subject="Residential closing BEC — spoofed attorney wire / Allegheny County PA",
            risk_score="HIGH",
            typology_flags=["BEC", "REAL_ESTATE_WIRE_FRAUD", "EMAIL_SPOOFING", "CLOSING_INSTRUCTION_FRAUD"],
            findings=(
                "Direct match to FBI IC3-documented BEC real estate closing typology. IC3 2023 Internet "
                "Crime Report: BEC schemes historically target the real estate sector among vendor-email "
                "compromise, W-2, and gift-card variants. 21,489 BEC complaints; $2.9 billion adjusted "
                "losses in 2023.\n\n"
                "DOCUMENTED RECOVERY PRECEDENT (IC3 RAT case — Stamford CT, March 2023): Homebuyer "
                "wired $426,000 based on spoofed attorney email; IC3 Recovery Asset Team initiated "
                "Financial Fraud Kill Chain (FFKC); $425,000 frozen and returned. Demonstrates time-critical "
                "recovery path when reported promptly with complete banking data.\n\n"
                "DETECTION FLAGS:\n"
                "- Lookalike sender domain vs. known counsel domain\n"
                "- Wire instruction change without out-of-band verification\n"
                "- Recipient account at institution not on original settlement statement\n"
                "- 48-hour reporting window — within FFKC eligibility window per IC3 RAT statistics "
                "(71% success rate on initiated FFKC incidents in 2023)\n\n"
                "IC3 PREVENTION GUIDANCE (investigative training value): Verify payment changes with "
                "intended recipient via known verified phone number; never rely on contact info in "
                "suspicious email; enable MFA on all transaction-party email accounts."
            ),
            evidence_chain=(
                "- Spoofed vs. legitimate wire instruction emails (headers, domains)\n"
                "- Bank wire records: originator and beneficiary accounts\n"
                "- Settlement statement with original wire instructions\n"
                "- IC3 complaint filing timestamp\n"
                "- FBI IC3 2023 Internet Crime Report — BEC overview and Stamford recovery case\n"
                "- IC3 wire-transfer complainant guidance"
            ),
            confidence="HIGH — IC3-documented BEC real estate pattern with parallel recovery case",
            leads=(
                "1. IMMEDIATE: Originating bank recall + IC3 RAT FFKC with full banking details\n"
                "2. Subpoena recipient institution for account KYC and opening surveillance\n"
                "3. Preserve email headers; trace lookalike domain registration\n"
                "4. Alert regional title/escrow companies — active BEC campaign indicator\n"
                "5. Cross-reference IC3 complaints for same domain/beneficiary in 90-day window\n"
                "6. Train transaction parties on IC3 out-of-band verification protocol"
            ),
        ),
        "category": "TITLE_DEED_FRAUD",
        "source": "FBI",
        "difficulty": "intermediate",
    },

]


# ── Functions ──────────────────────────────────────────────────────────────────

def validate_pairs(pairs: List[Dict]) -> tuple[bool, List[str]]:
    """Validate dataset pairs for required fields and typology labels."""
    errors = []
    required_fields = ["instruction", "input", "output", "category", "source", "difficulty"]
    valid_difficulties = {"basic", "intermediate", "advanced"}

    for i, pair in enumerate(pairs):
        for field in required_fields:
            if field not in pair:
                errors.append(f"Pair {i}: missing field '{field}'")
        if "category" in pair and pair["category"] not in TYPOLOGIES:
            errors.append(f"Pair {i}: unknown category '{pair['category']}'")
        if "source" in pair and pair["source"] not in SOURCES:
            errors.append(f"Pair {i}: unknown source '{pair['source']}'")
        if "difficulty" in pair and pair["difficulty"] not in valid_difficulties:
            errors.append(f"Pair {i}: unknown difficulty '{pair['difficulty']}'")

    return len(errors) == 0, errors


def build_dataset(output_path: Path = _OUTPUT_FILE) -> None:
    """Build and write the Alpaca-format dataset JSON."""
    ok, errors = validate_pairs(SEED_PAIRS)
    if not ok:
        print("VALIDATION ERRORS:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)

    dataset = {
        "metadata": {
            "agent": "ELIOT",
            "version": "v1",
            "built": datetime.now(timezone.utc).isoformat(),
            "total_pairs": len(SEED_PAIRS),
            "format": "alpaca",
            "model_target": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
            "typologies": TYPOLOGIES,
            "sources": SOURCES,
        },
        "pairs": SEED_PAIRS,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"Dataset written: {output_path}")
    print(f"Total pairs: {len(SEED_PAIRS)}")
    _print_stats(SEED_PAIRS)


def _print_stats(pairs: List[Dict]) -> None:
    """Print typology and difficulty breakdown."""
    from collections import Counter
    cats  = Counter(p.get("category", "UNKNOWN") for p in pairs)
    diffs = Counter(p.get("difficulty", "UNKNOWN") for p in pairs)
    srcs  = Counter(p.get("source", "UNKNOWN") for p in pairs)

    print("\n── Typology Breakdown ───────────────────────────────")
    for cat, count in sorted(cats.items()):
        bar = "█" * count
        print(f"  {cat:<25} {bar} {count}")

    print("\n── Difficulty Breakdown ─────────────────────────────")
    for diff, count in sorted(diffs.items()):
        print(f"  {diff:<15} {count}")

    print("\n── Source Breakdown ─────────────────────────────────")
    for src, count in sorted(srcs.items()):
        print(f"  {src:<20} {count}")


def check_dataset(path: Path = _OUTPUT_FILE) -> None:
    """Validate an existing dataset file."""
    if not path.exists():
        print(f"Dataset not found: {path}")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    pairs = data.get("pairs", [])
    ok, errors = validate_pairs(pairs)
    if ok:
        print(f"✓ Dataset valid: {len(pairs)} pairs")
        _print_stats(pairs)
    else:
        print(f"✗ {len(errors)} validation errors:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)


def append_pairs(source_file: Path, output_path: Path = _OUTPUT_FILE) -> None:
    """Append additional pairs from a JSON file into the main dataset."""
    with open(source_file, encoding="utf-8") as f:
        new_data = json.load(f)

    new_pairs = new_data if isinstance(new_data, list) else new_data.get("pairs", [])
    ok, errors = validate_pairs(new_pairs)
    if not ok:
        print(f"New pairs have validation errors:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)

    if output_path.exists():
        with open(output_path, encoding="utf-8") as f:
            existing = json.load(f)
        existing_pairs = existing.get("pairs", [])
    else:
        existing_pairs = []

    combined = existing_pairs + new_pairs

    dataset = {
        "metadata": {
            "agent": "ELIOT",
            "version": "v1",
            "built": datetime.now(timezone.utc).isoformat(),
            "total_pairs": len(combined),
            "format": "alpaca",
            "model_target": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        },
        "pairs": combined,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"Appended {len(new_pairs)} pairs. Total: {len(combined)}")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="ELIOT Financial Crime Dataset Builder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--build",  action="store_true", help="Build the seed dataset")
    parser.add_argument("--check",  action="store_true", help="Validate existing dataset")
    parser.add_argument("--stats",  action="store_true", help="Print typology stats")
    parser.add_argument("--append", metavar="FILE",      help="Append pairs from JSON file")
    parser.add_argument("--output", metavar="PATH",      help="Override output path")

    args = parser.parse_args()
    out = Path(args.output) if args.output else _OUTPUT_FILE

    if args.build:
        build_dataset(out)
    elif args.check:
        check_dataset(out)
    elif args.stats:
        if out.exists():
            with open(out, encoding="utf-8") as f:
                data = json.load(f)
            _print_stats(data.get("pairs", []))
        else:
            print(f"No dataset at {out} — run --build first")
    elif args.append:
        append_pairs(Path(args.append), out)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

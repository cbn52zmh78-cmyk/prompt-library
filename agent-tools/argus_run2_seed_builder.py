"""Generate ARGUS Run 2 E6-E10 seed pairs (40 total) for 60→100 corpus expansion."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\NCG\Videos\Grok Projects\Stonebridge\Products\ATREIDES")
RESEARCH = ROOT / "research"
sys.path.insert(0, str(ROOT / "training"))
import argus_dataset_builder as adb  # noqa: E402

DISC = adb._ARGUS_DISCLAIMER


def dossier(
    case: str,
    subject: str,
    flags: list[str],
    kind: str,
    indicators: str,
    leads: str,
    cites: str,
) -> str:
    return adb.make_dossier(
        case_id=case,
        subject=subject,
        typology_flags=flags,
        pair_kind=kind,
        indicators=indicators,
        leads=leads,
        citations=cites,
        date="2026-06-24T08:00:00Z",
    )


def typo(title: str, body: str, cites: str) -> str:
    return f"TYPOLOGY RECOGNITION — {title}\n\n{body}\n\nSOURCE: {cites}\n\n{DISC}"


E6 = [
    {
        "instruction": "Enrich digital footprint indicators from RDAP/WHOIS on vendor spoof domain. Public OSINT only.",
        "input": "RFP closing Friday. Domain 'city-procurement-bid-portal.org' registered Tuesday. RDAP org matches FL LLC on SOS. Historical snapshot shows phone +1-305-555-0142 on 4 prior gov-themed domains.",
        "output": dossier(
            "ARGUS-R2-E6-001",
            "city-procurement-bid-portal.org — procurement spoof",
            ["PROCUREMENT_SPOOF_DOMAIN", "RDAP_PHONE_HISTORY_CLUSTER", "SOS_ORG_NAME_MATCH"],
            "RED_FLAG",
            "- 72-hour domain-to-deadline cycle — FBI procurement fraud timing marker\n"
            "- RDAP phone recurs on 4 gov-themed domains — registrant infrastructure cluster\n"
            "- Registrant org matches FL SOS LLC — digital-to-registry pivot",
            "1. Archive RDAP + historical WHOIS for all five domains\n"
            "2. Florida SOS pull on registrant org LLC\n"
            "3. Agency official domain list from .gov site — contrast spoof\n"
            "4. IC3 procurement fraud keyword cross-reference",
            "FBI procurement fraud alerts; RDAP; Florida Division of Corporations",
        ),
        "category": "DOMAIN_REGISTRANT_HISTORY_CLUSTER",
        "research_lane": "E6",
        "pair_kind": "RED_FLAG",
        "source": "FBI",
        "difficulty": "advanced",
    },
    {
        "instruction": "Map passive DNS hosting cluster for LLC-linked fraud domains. Detection only.",
        "input": "Six DE LLCs formed in 10 days share marketing sites on IP 198.51.100.44. Passive DNS shows 38 domains (recovery, grant, loan) on same host. crt.sh lists wildcard cert *.fast-funding-help.com.",
        "output": dossier(
            "ARGUS-R2-E6-002",
            "DE LLC sextet — shared hosting fraud cluster",
            ["HOSTING_CLUSTER_FRAUD_OPS", "PASSIVE_DNS_CORRELATION", "CT_WILDCARD_CERT"],
            "RED_FLAG",
            "- Six newborn LLCs colocated on single IP with 38 scam domains — infrastructure hub indicator\n"
            "- Wildcard TLS on fast-funding-help.com — rapid fraud stack marker\n"
            "- SOS formation burst correlates with domain portfolio activation",
            "1. Passive DNS expansion on 198.51.100.44 — full domain export\n"
            "2. DE SOS agent pull for all six LLCs\n"
            "3. crt.sh subdomain enumeration\n"
            "4. FTC advance-fee scam alert crosswalk",
            "Public passive DNS documentation; crt.sh; FTC scam alerts",
        ),
        "category": "DIGITAL_FOOTPRINT_OSINT",
        "research_lane": "E6",
        "pair_kind": "RED_FLAG",
        "source": "FTC",
        "difficulty": "intermediate",
    },
    {
        "instruction": "Enrich BEC lookalike domain indicators from Certificate Transparency and RDAP.",
        "input": "Title company reports wire instruction change from 'smithlaw-pa.com'. Legitimate firm uses 'smithlawpa.com'. Spoof domain created 36 hours ago. CT log shows MX host offshore. RDAP privacy proxy shared with 3 prior closing-spoof domains in IC3 bulletin appendix.",
        "output": dossier(
            "ARGUS-R2-E6-003",
            "smithlaw-pa.com — BEC lookalike",
            ["BEC_DOMAIN_PATTERN", "SHORT_LIVED_FRAUD_DOMAIN", "CT_MX_OFFSHORE"],
            "RED_FLAG",
            "- 36-hour lookalike domain — FBI IC3 BEC digital marker\n"
            "- Offshore MX on newborn domain — operational fraud stack\n"
            "- Shared privacy proxy with prior IC3-documented spoof set — repeat actor footprint",
            "1. Preserve CT + RDAP snapshots with timestamps\n"
            "2. Passive DNS on MX host\n"
            "3. Public IC3 bulletin domain list correlation\n"
            "4. Registrar abuse contact preservation letter",
            "FBI IC3 BEC advisories; Certificate Transparency (crt.sh)",
        ),
        "category": "BEC_DOMAIN_PATTERN",
        "research_lane": "E6",
        "pair_kind": "RED_FLAG",
        "source": "FBI",
        "difficulty": "intermediate",
    },
    {
        "instruction": "Identify rental scam domain burst from public WHOIS history. FTC typology — detection only.",
        "input": "Victim reports Zelle deposit for Pittsburgh apartment. Listing domain 'oakland-rentals-deals.net' registered 3 days prior. RDAP email reused on 6 metro rental domains in historical snapshot. Privacy proxy identical across all seven.",
        "output": dossier(
            "ARGUS-R2-E6-004",
            "oakland-rentals-deals.net — rental scam burst",
            ["DOMAIN_BURST_REGISTRATION", "RENTAL_SCAM_FOOTPRINT", "WHOIS_EMAIL_REUSE"],
            "INVESTIGATIVE_INDICATOR",
            "- 3-day domain-to-listing cycle — FTC rental scam timing pattern\n"
            "- Email reuse across 7 metro domains — campaign infrastructure indicator\n"
            "- Shared privacy proxy — registrant clustering via public RDAP only",
            "1. RDAP historical pull on all seven domains\n"
            "2. Reverse image search lead preservation (victim-provided)\n"
            "3. IC3 rental fraud keyword search\n"
            "4. No payment tracing from ARGUS — LE subpoena path only",
            "FTC Rental Listing Scams; IC3; RDAP archives",
        ),
        "category": "DOMAIN_BURST_REGISTRATION",
        "research_lane": "E6",
        "pair_kind": "INVESTIGATIVE_INDICATOR",
        "source": "FTC",
        "difficulty": "intermediate",
    },
    {
        "instruction": "Typology recognition: RDAP vs WHOIS and when to escalate digital footprint enrichment.",
        "input": "Analyst asks: 'Privacy proxy on all domains — is the investigation dead?'",
        "output": typo(
            "RDAP / DIGITAL FOOTPRINT ESCALATION",
            "PRIVACY PROXY IS NOT A STOP:\n"
            "- Pivot via historical RDAP snapshots (pre-redaction)\n"
            "- Passive DNS, shared hosting IP, CT logs, MX/NS co-location\n"
            "- Crosswalk emails/phones that appear even once to SOS officer lines\n"
            "- Correlate domain creation timing to SOS bursts and recorder events\n\n"
            "LIMITS: No registrar insider access; no breach data; archive all public pulls.",
            "FTC/FBI fraud domain advisories; RDAP protocol; GAO public OSINT discipline",
        ),
        "category": "DIGITAL_FOOTPRINT_OSINT",
        "research_lane": "E6",
        "pair_kind": "TYPOLOGY_RECOGNITION",
        "source": "DOMAIN_EXPERT",
        "difficulty": "basic",
    },
    {
        "instruction": "Enrich entity website mismatch against SOS business profile.",
        "input": "WY LLC claims 'international logistics' on website. SOS NAICS absent. Site registered 8 days after formation. About page lists Dubai address; LLC principal is UPS Store Cheyenne. Site shares IP with binary-options platform per public DNS.",
        "output": dossier(
            "ARGUS-R2-E6-005",
            "WY LLC — website/SOS mismatch",
            ["WEBSITE_SOS_MISMATCH", "VIRTUAL_OFFICE_PRINCIPAL", "COLOCATED_SCAM_HOST"],
            "RED_FLAG",
            "- Business description vs absent SOS activity code — footprint inconsistency\n"
            "- Dubai marketing address vs WY UPS Store principal — jurisdiction shopping marker\n"
            "- Shared host with binary-options site — fraud-adjacent infrastructure indicator",
            "1. Archive website + SOS extract same timestamp\n"
            "2. Passive DNS on site IP — map co-hosted domains\n"
            "3. Wyoming SOS agent cluster expansion\n"
            "4. SEC/FINRA public alerts for binary-options pattern",
            "Wyoming SOS; FBI investment fraud advisories",
        ),
        "category": "DIGITAL_FOOTPRINT_OSINT",
        "research_lane": "E6",
        "pair_kind": "RED_FLAG",
        "source": "SEC",
        "difficulty": "intermediate",
    },
    {
        "instruction": "Correlate Gravatar/social avatar hash across public platforms to SOS entity.",
        "input": "LinkedIn company page for 'Apex Property Capital LLC' uses logo matching Gravatar on GitHub repo 'apex-deals'. README links DE SOS file. Telegram channel with same avatar promotes off-market RE deals to Pittsburgh investors.",
        "output": dossier(
            "ARGUS-R2-E6-006",
            "Apex Property Capital — cross-platform avatar match",
            ["CROSS_PLATFORM_AVATAR_MATCH", "GITHUB_SOS_NEXUS", "TELEGRAM_ENTITY_PROMO"],
            "INVESTIGATIVE_INDICATOR",
            "- Public avatar hash match across LinkedIn/GitHub/Telegram — alias resolution lead\n"
            "- GitHub README cites DE SOS file — digital-to-registry pivot\n"
            "- Telegram off-market RE promotion — unregistered dealer indicator (public posts only)",
            "1. Archive public posts and README with timestamps\n"
            "2. Delaware SOS pull on cited file number\n"
            "3. PA DOS broker license negative search (public)\n"
            "4. No DM/infiltration — lawful subpoena path only",
            "Delaware SOS; PA licensing public portal; FBI social media fraud advisories",
        ),
        "category": "SOCIAL_FOOTPRINT_ALIAS_RESOLUTION",
        "research_lane": "E6",
        "pair_kind": "INVESTIGATIVE_INDICATOR",
        "source": "FBI",
        "difficulty": "intermediate",
    },
    {
        "instruction": "Flag toll-free RESPORG mismatch from public FCC numbering data.",
        "input": "State AG alert lists hotline +1-844-555-0288 for 'Federal Grant Assistance'. FCC database RESPORG 'Bandwidth.com' vs marketed entity 'Federal Grant Assistance Bureau LLC'. Same RESPORG on 9 open-web AG bulletins.",
        "output": dossier(
            "ARGUS-R2-E6-007",
            "Toll-free grant scam hotline — RESPORG cluster",
            ["TOLL_FREE_RESPORG_MISMATCH", "AG_BULLETIN_RECURRENCE", "IMPERSONATION_INFRASTRUCTURE"],
            "RED_FLAG",
            "- RESPORG differs from marketed federal-style brand — impersonation indicator\n"
            "- RESPORG repeats across 9 AG alerts — infrastructure clustering lead\n"
            "- LLC name mimics government — public SOS formation search priority",
            "1. Archive FCC numbering extract + AG PDFs\n"
            "2. SOS search on marketed LLC name in filing states\n"
            "3. FTC impersonation scam alert crosswalk\n"
            "4. No trap/trace from ARGUS",
            "FCC toll-free database; state AG public alerts; FTC impersonation guidance",
        ),
        "category": "PHONE_NUMBER_PUBLIC_OSINT",
        "research_lane": "E6",
        "pair_kind": "RED_FLAG",
        "source": "GAO",
        "difficulty": "intermediate",
    },
]

E7 = [
    {
        "instruction": "Enrich SYNTH-DEED-001 fixture from public SOS and Allegheny recorder indicators. Detection only.",
        "input": "source_id: SYNTH-DEED-001 — Wyoming LLC purchased Allegheny County residential property all-cash 14 days after formation. Registered agent only on SOS. source_id: SYNTH-WIRE-002 — inbound wire from intermediary; beneficial owner absent from closing docs.",
        "output": dossier(
            "ARGUS-R2-E7-001",
            "SYNTH-DEED-001 / SYNTH-WIRE-002 — fleet packet enrichment",
            ["SOS_TRANSACTION_DATE_GAP", "RE_ALL_CASH_LLC_GRANTEE", "INTERMEDIARY_WIRE_MISMATCH"],
            "RED_FLAG",
            "- 14-day WY formation-to-deed — FinCEN FIN-2017-A003 shell timing marker\n"
            "- Nominee agent as sole SOS contact — UBO opacity lead\n"
            "- Intermediary wire without BO on closing — grantee/funder mismatch indicator",
            "1. Wyoming SOS: formation timestamp + agent cluster expansion\n"
            "2. Allegheny recorder: deed instrument vs SOS datetime\n"
            "3. Assessor owner-of-record update lag check\n"
            "4. ELIOT handoff: T-01/T-02 typology correlation; cite source_id on every lead",
            "FinCEN FIN-2017-A003; Wyoming SOS; Allegheny County recorder public index",
        ),
        "category": "SOS_TRANSACTION_DATE_GAP",
        "research_lane": "E7",
        "pair_kind": "RED_FLAG",
        "source": "FinCEN",
        "difficulty": "intermediate",
    },
    {
        "instruction": "Flag assessor vs deed grantee mismatch on residential acquisition.",
        "input": "Deed recorded Jun 12: grantee Northgate Holdings LLC (DE). Assessor still lists prior individual owner Jun 30. No homestead update. LLC foreign qual PA not filed. Purchase all-cash $388,000.",
        "output": dossier(
            "ARGUS-R2-E7-002",
            "Northgate Holdings LLC — assessor lag anomaly",
            ["ASSESSOR_DEED_MISMATCH", "DELAYED_FOREIGN_QUALIFICATION", "RE_ALL_CASH_LLC_GRANTEE"],
            "RED_FLAG",
            "- 18-day assessor lag post-deed — may indicate rapid flip or recording irregularity\n"
            "- PA foreign qual absent — cross-state footprint minimization\n"
            "- All-cash DE LLC grantee — FIN-2017-A003 indicator cluster",
            "1. Recorder deed image + instrument number\n"
            "2. Assessor parcel history pull Jul 1 and Aug 1\n"
            "3. PA DOS foreign qual search\n"
            "4. Utility activation OSINT",
            "Allegheny assessor; PA DOS; FinCEN FIN-2017-A003",
        ),
        "category": "RE_OSINT",
        "research_lane": "E7",
        "pair_kind": "RED_FLAG",
        "source": "FinCEN",
        "difficulty": "intermediate",
    },
    {
        "instruction": "Enrich UCC fixture filing against recent deed grantee.",
        "input": "UCC-1 filed 9 days after residential deed to 'Silver Creek Holdings LLC'. Secured party: Cayman-linked finance LLC. Collateral: all fixtures and rents. Grantee LLC formed 11 days pre-deed. No mortgage recorded.",
        "output": dossier(
            "ARGUS-R2-E7-003",
            "Silver Creek Holdings — UCC fixture post-deed",
            ["UCC_FIXTURE_POST_DEED", "OFFSHORE_SECURED_PARTY", "SHELL_TIMING_CORRELATION"],
            "INVESTIGATIVE_INDICATOR",
            "- Fixture UCC without mortgage — alternative leverage path around public mortgage index\n"
            "- Offshore secured party name — cross-border enrichment lead\n"
            "- 11-day formation-to-deed aligns with shell timing typologies",
            "1. State UCC portal filing image\n"
            "2. Recorder deed date cross-check\n"
            "3. Secured party SOS search in formation state\n"
            "4. Title company litigation search if public",
            "State UCC filing portal; FinCEN FIN-2017-A003",
        ),
        "category": "RE_OSINT",
        "research_lane": "E7",
        "pair_kind": "INVESTIGATIVE_INDICATOR",
        "source": "FinCEN",
        "difficulty": "advanced",
    },
    {
        "instruction": "Analyze recorder bulk transfer pattern for asset rotation between shell LLCs.",
        "input": "Cuyahoga recorder: 14 residential deeds in 21 days. Grantees: 14 distinct WY LLCs, same DE agent. Grantors: 3 repeat individuals. Each deed all-cash. No MLS listings between transfers.",
        "output": dossier(
            "ARGUS-R2-E7-004",
            "Cuyahoga 14-LLC deed burst",
            ["RECORDER_BULK_TRANSFER", "SHELL_ACQUISITION_CAMPAIGN", "FLIP_VELOCITY_NO_MLS"],
            "RED_FLAG",
            "- 14 WY LLCs via single agent in 21 days — campaign-scale recorder pattern\n"
            "- Repeat individual grantors — possible straw seller network indicator\n"
            "- No MLS activity — off-market flip chain enrichment priority",
            "1. Recorder bulk export with grantor/grantee graph\n"
            "2. DE SOS agent cluster pull\n"
            "3. Assessor sale price vs prior deed consideration\n"
            "4. ATLAS handoff: bipartite grantor↔LLC graph",
            "Cuyahoga County recorder; Delaware SOS; FinCEN RE typologies",
        ),
        "category": "GRANTOR_GRANTEE_CHAIN_GAP",
        "research_lane": "E7",
        "pair_kind": "RED_FLAG",
        "source": "FBI",
        "difficulty": "advanced",
    },
    {
        "instruction": "Typology recognition: public recorder enrichment checklist for financial crimes units.",
        "input": "Detective training: 'What recorder fields matter for LLC all-cash buys?'",
        "output": typo(
            "RECORDER OSINT CHECKLIST",
            "PRIORITY FIELDS:\n"
            "- Recording datetime vs SOS formation datetime\n"
            "- Grantee legal capacity (active vs dissolved SOS status)\n"
            "- Consideration statement and deed type (quitclaim vs warranty)\n"
            "- Notary venue vs situs distance\n"
            "- Chain gaps (trust pivot, missing intermediate deed)\n"
            "- Cross-check assessor owner, UCC fixtures, tax delinquency public docket\n\n"
            "ARGUS cites recorder index only — instrument images may need clerk request.",
            "FinCEN FIN-2017-A003; DOJ elder deed fraud guidance",
        ),
        "category": "RE_OSINT",
        "research_lane": "E7",
        "pair_kind": "TYPOLOGY_RECOGNITION",
        "source": "DOJ",
        "difficulty": "basic",
    },
    {
        "instruction": "Enrich tax delinquency public docket against new shell grantee acquisition.",
        "input": "Parcel had $14,200 tax delinquency published Apr 1. May 20 deed to 9-day-old NV LLC all-cash. Delinquency paid May 18 by cashier's check per public tax ledger. LLC manager is DE corp services firm.",
        "output": dossier(
            "ARGUS-R2-E7-005",
            "NV LLC — tax delinquency pre-acquisition",
            ["TAX_DELINQUENCY_RESOLUTION", "NEWBORN_GRANTEE_ALL_CASH", "NOMINEE_MANAGER"],
            "RED_FLAG",
            "- Delinquent parcel acquired by 9-day-old LLC — distressed asset + shell timing\n"
            "- Large cashier's payment immediately pre-deed — source-of-funds enrichment lead\n"
            "- Corporate services manager — BO opacity indicator",
            "1. Public tax ledger payment instrument type\n"
            "2. NV/DE SOS synchronized pull\n"
            "3. Recorder deed consideration field\n"
            "4. ELIOT handoff: distressed RE ML patterns",
            "County tax public ledger; FinCEN FIN-2017-A003",
        ),
        "category": "RE_OSINT",
        "research_lane": "E7",
        "pair_kind": "RED_FLAG",
        "source": "FinCEN",
        "difficulty": "intermediate",
    },
    {
        "instruction": "Identify homestead occupancy claim inconsistent with public vacancy OSINT.",
        "input": "Assessor homestead exemption active for LLC-owned parcel post-deed. No rental license. Google Street View archive shows boarded windows. USPS change-of-address bulk to DE agent address for prior individual owner.",
        "output": dossier(
            "ARGUS-R2-E7-006",
            "LLC parcel — homestead/vacancy mismatch",
            ["HOMESTEAD_EXEMPTION_MISMATCH", "VACANCY_OSINT", "COA_AGENT_ADDRESS"],
            "INVESTIGATIVE_INDICATOR",
            "- Homestead on LLC-owned parcel — tax status anomaly\n"
            "- Visual vacancy OSINT corroboration — integration/storage indicator\n"
            "- COA to DE agent — mail pivot away from situs",
            "1. Assessor exemption history\n"
            "2. Municipal rental license negative search\n"
            "3. Archive Street View with date\n"
            "4. USPS COA lead — LE subpoena only, not ARGUS execution",
            "County assessor; FinCEN RE vacancy indicators",
        ),
        "category": "RE_OSINT",
        "research_lane": "E7",
        "pair_kind": "INVESTIGATIVE_INDICATOR",
        "source": "FinCEN",
        "difficulty": "intermediate",
    },
    {
        "instruction": "Flag dissolved grantee entity on warranty deed recording.",
        "input": "Warranty deed recorded yesterday: grantee 'Blue Ridge Ventures LLC'. DE SOS shows involuntary dissolution 47 days ago. Grantor individual. Second deed same day to new WY LLC for same parcel — competing recording.",
        "output": dossier(
            "ARGUS-R2-E7-007",
            "Blue Ridge Ventures — dissolved grantee + duplicate deed",
            ["DISSOLVED_GRANTEE_ENTITY", "DUPLICATE_DEED_RECORDING", "TITLE_CONFUSION_INDICATOR"],
            "RED_FLAG",
            "- Deed to dissolved LLC — invalid grantee capacity on public SOS\n"
            "- Same-day competing deed to newborn WY LLC — title confusion / fraud indicator\n"
            "- Individual grantor — possible straw or elder exploitation context",
            "1. DE SOS dissolution certificate date\n"
            "2. Recorder competing instrument timestamps\n"
            "3. Title litigation public docket search\n"
            "4. Adult protective services public index if applicable",
            "Delaware SOS; county recorder; FinCEN RE fraud typologies",
        ),
        "category": "DEED_RECORDING_ANOMALY",
        "research_lane": "E7",
        "pair_kind": "RED_FLAG",
        "source": "STATE_AG",
        "difficulty": "advanced",
    },
]

# E8, E9, E10 — 8 pairs each (abbreviated structure, full dossiers)
E8 = [
    {
        "instruction": "Cross-reference DE, TX, CO SOS for shared agent suite cluster.",
        "input": "Blue Mesa Holdings LLC (DE). TX foreign qual shares suite 400 with 4 CO LLCs formed same month. CO reports name Summit Fiduciary Inc as manager on all four.",
        "output": dossier("ARGUS-R2-E8-001", "Blue Mesa — tri-state SOS cluster",
            ["MULTISTATE_SOS_REGISTRY_XREF", "SHARED_AGENT_SUITE_CLUSTER", "CORPORATE_MANAGER_APEX"],
            "RED_FLAG",
            "- Tri-state SOS linkage via suite 400 — cross-reference cluster indicator\n"
            "- Summit Fiduciary repeated manager — nominee stack\n"
            "- No individual on DE member line",
            "1. DE/TX/CO SOS extracts with normalized suite string\n2. Recorder search Denver/Houston\n3. Flag NOT FOUND on missing members",
            "Delaware, Texas, Colorado SOS portals; FBI jurisdiction shopping typologies"),
        "category": "MULTISTATE_SOS_REGISTRY_XREF", "research_lane": "E8", "pair_kind": "RED_FLAG", "source": "STATE_AG", "difficulty": "intermediate",
    },
    {
        "instruction": "Pivot UK Companies House PSC data to US-facing nominee director LLC.",
        "input": "PA LLC manager: Pinnacle Directors Ltd (UK). Companies House shows active status, PSC withheld as 'statement filed'. Same UK firm on 8 US LLCs per NV SOS.",
        "output": dossier("ARGUS-R2-E8-002", "Pinnacle Directors — UK→US pivot",
            ["UK_CH_PSC_PIVOT", "NOMINEE_DIRECTOR_PATTERN", "CROSS_BORDER_CORPORATE_MANAGER"],
            "RED_FLAG",
            "- UK corporate director on US LLC — FATF R24 cross-border opacity\n"
            "- PSC statement filed — limited UK public BO visibility\n"
            "- Eight-US-LLC cluster — expansion priority",
            "1. Companies House free extract + PSC statement note\n2. NV/PA SOS synchronized pull\n3. Lawful MLAT if deeper UK BO required",
            "UK Companies House; FATF R24; Nevada SOS"),
        "category": "CROSS_STATE_REGISTRATION", "research_lane": "E8", "pair_kind": "RED_FLAG", "source": "FATF", "difficulty": "advanced",
    },
    {
        "instruction": "Document negative municipal business license search for asset-holding LLC.",
        "input": "Columbus OH rental portfolio: 22 parcels via NV LLC. Columbus business license portal: no license. OH foreign qual filed. Zero OH unemployment filings in public state data summary.",
        "output": dossier("ARGUS-R2-E8-003", "NV LLC — Columbus license gap",
            ["BUSINESS_LICENSE_NEGATIVE", "NO_WORKFORCE_FOOTPRINT", "JURISDICTION_SHOPPING"],
            "INVESTIGATIVE_INDICATOR",
            "- 22-parcel portfolio without city business license — operating footprint gap\n"
            "- No unemployment filings — workforce absence indicator\n"
            "- NV charter for OH assets — jurisdiction shopping",
            "1. Columbus license negative search archive\n2. OH SOS foreign qual timeline\n3. Franklin County recorder financing",
            "Ohio SOS; municipal license portal; FBI typologies"),
        "category": "JURISDICTION_SHOPPING", "research_lane": "E8", "pair_kind": "INVESTIGATIVE_INDICATOR", "source": "FBI", "difficulty": "intermediate",
    },
    {
        "instruction": "Map WY→DE→NV registration chain for Columbus asset wrapper.",
        "input": "Asset LLC (WY) managed by DE LLC managed by NV agent hub. Principal: Las Vegas Regus. Assets: Columbus duplexes. OH foreign qual 75 days post-first deed.",
        "output": dossier("ARGUS-R2-E8-004", "WY→DE→NV chain — Columbus assets",
            ["CROSS_STATE_REGISTRATION_CLUSTER", "VIRTUAL_OFFICE_PRINCIPAL", "DELAYED_FOREIGN_QUALIFICATION"],
            "RED_FLAG",
            "- Tri-state management chain — FBI jurisdiction-shopping footprint\n"
            "- Regus principal with OH assets — virtual office indicator\n"
            "- Delayed OH qual — reactive compliance",
            "1. WY/DE/NV SOS synchronized agent pull\n2. OH qual date vs first deed\n3. Regus suite subpoena where available",
            "FBI financial crime typologies; state SOS portals"),
        "category": "CROSS_STATE_REGISTRATION_CLUSTER", "research_lane": "E8", "pair_kind": "RED_FLAG", "source": "FBI", "difficulty": "intermediate",
    },
    {
        "instruction": "Typology recognition: multistate SOS pull normalization rules.",
        "input": "Data team asks how to match agent addresses across state portals with different formats.",
        "output": typo("MULTISTATE SOS NORMALIZATION",
            "NORMALIZE:\n- Strip punctuation, uppercase, expand Suite/Ste/#\n- Parse ZIP+4 separately\n- Match on EIN if exposed on foreign qual\n- Graph edge when suite number + street number collide\n\nALWAYS re-pull home-state charter before trusting aggregator cache.",
            "NASS SOS guidance; GAO public records methodology"),
        "category": "MULTISTATE_SOS_REGISTRY_XREF", "research_lane": "E8", "pair_kind": "TYPOLOGY_RECOGNITION", "source": "GAO", "difficulty": "basic",
    },
    {
        "instruction": "Enrich DBA name collision across state fictitious name indexes.",
        "input": "Operating as 'Midwest Property Group' per rental ads. OH DBA not found. PA FBN lists different principal. DE LLC actual grantee on leases. Ads use toll-free matching FCC RESPORG cluster.",
        "output": dossier("ARGUS-R2-E8-005", "Midwest Property Group — DBA collision",
            ["DBA_NAME_COLLISION", "MARKETING_NAME_MISMATCH", "PHONE_RESPORG_CLUSTER"],
            "INVESTIGATIVE_INDICATOR",
            "- Marketing name absent from OH DBA — public registry gap\n"
            "- PA FBN different principal — identity fragmentation indicator\n"
            "- Toll-free RESPORG ties to prior scam bulletins",
            "1. OH/PA FBN searches\n2. DE LLC SOS pull\n3. FCC numbering archive",
            "State fictitious name portals; FCC database"),
        "category": "CROSS_STATE_FORMATION", "research_lane": "E8", "pair_kind": "INVESTIGATIVE_INDICATOR", "source": "STATE_AG", "difficulty": "intermediate",
    },
    {
        "instruction": "Flag annual report lapse in formation state while foreign ops active.",
        "input": "WY LLC owns 9 TX properties. WY annual reports lapsed 2 years. TX foreign qual current. Registered agent unchanged. New TX acquisition last month.",
        "output": dossier("ARGUS-R2-E8-006", "WY lapse / TX active — entity hygiene split",
            ["ANNUAL_REPORT_LAPSE", "ACTIVE_FOREIGN_QUAL", "CROSS_STATE_FORMATION"],
            "RED_FLAG",
            "- WY lapse with active TX ops — entity hygiene inconsistent with institutional operator\n"
            "- Continued acquisitions despite home-state delinquency — possible intentional record decay",
            "1. WY SOS lapse docket\n2. TX SOS foreign qual status\n3. County recorder TX acquisition timeline",
            "Wyoming SOS; Texas SOS"),
        "category": "CROSS_STATE_FORMATION", "research_lane": "E8", "pair_kind": "RED_FLAG", "source": "STATE_AG", "difficulty": "intermediate",
    },
    {
        "instruction": "Correlate NV high-volume agent with geographic dispersal of acquisitions.",
        "input": "Single NV commercial agent on 31 LLCs in 120 days. Acquisitions in PA, OH, FL, AZ. No NV properties. Agent also listed on 6 dissolved LLCs reformed under new names.",
        "output": dossier("ARGUS-R2-E8-007", "NV agent — 31-LLC geographic burst",
            ["MULTI_STATE_AGENT_CLUSTER", "GEOGRAPHIC_DISPERSAL", "DISSOLVE_REFORM_CYCLE"],
            "INVESTIGATIVE_INDICATOR",
            "- 31 LLCs / 120 days — campaign-scale agent hub\n"
            "- Four-state acquisitions, zero NV assets — dispersal without local nexus\n"
            "- Dissolve-reform names — hygiene reset indicator",
            "1. NV SOS bulk agent extract\n2. Four-state recorder timeline\n3. Compare dissolved vs successor officers",
            "Nevada SOS; FBI shell typologies"),
        "category": "MULTI_STATE_AGENT_CLUSTER", "research_lane": "E8", "pair_kind": "INVESTIGATIVE_INDICATOR", "source": "FBI", "difficulty": "advanced",
    },
]

E9 = [
    {
        "instruction": "Trace UBO indicators through land trust + LLC stack from public records.",
        "input": "Title: Chicago Title Land Trust. Beneficiary unrecorded. Mortgage by OH LLC. Beneficial interest assigned twice in 45 days without deed re-recording.",
        "output": dossier("ARGUS-R2-E9-001", "Land trust — UBO tracing stack",
            ["LAND_TRUST_OBFUSCATION", "BENEFICIAL_INTEREST_ASSIGNMENT", "UBO_TRACING_WORKFLOW"],
            "RED_FLAG",
            "- Unrecorded beneficiary — recorder enrichment limit\n"
            "- Rapid beneficial interest assignments — control shift without deed trail\n"
            "- Mortgage LLC decouples debt from trust facade",
            "1. Subpoena trust schedule (path citation only)\n2. UCC on beneficial interests\n3. OH LLC SOS manager chain",
            "FinCEN land trust guidance; FinCEN CTA"),
        "category": "UBO_TRACING", "research_lane": "E9", "pair_kind": "RED_FLAG", "source": "FinCEN", "difficulty": "advanced",
    },
    {
        "instruction": "Enrich FinCEN CDD trust-customer gap from public rule text and filing parties.",
        "input": "OR statutory trust owns 60% industrial op-co via DE LLC. Trustee is corporate entity. Trust declaration names no natural person in excerpt shared with analyst.",
        "output": dossier("ARGUS-R2-E9-002", "OR trust — CDD natural person gap",
            ["TRUST_LAYERED_UBO", "CDD_NATURAL_PERSON_GAP", "CORPORATE_TRUSTEE_APEX"],
            "RED_FLAG",
            "- Corporate trustee + layered LLC — CDD control-prong review trigger\n"
            "- No natural person in available excerpt — transparency gap indicator",
            "1. FinCEN CDD FAQ trust customers\n2. OR trust public index\n3. DE LLC SOS on op-co",
            "FinCEN CDD Rule 31 CFR 1010.230; Oregon trust index"),
        "category": "FINCEN_CDD_UBO_RESEARCH", "research_lane": "E9", "pair_kind": "RED_FLAG", "source": "FinCEN", "difficulty": "advanced",
    },
    {
        "instruction": "Document nominee director rotation pre-refinance on public Sunbiz history.",
        "input": "FL LLC: three corporate nominee directors in 62 days, ending day before refi. No individual ever listed. Refi mortgage recorded to second LLC.",
        "output": dossier("ARGUS-R2-E9-003", "FL LLC — nominee rotation pre-refi",
            ["NOMINEE_DIRECTOR_ROTATION", "PRE_REFINANCE_CONTROL_SWAP", "UBO_NOT_ON_PUBLIC_RECORD"],
            "RED_FLAG",
            "- 62-day nominee rotation — opacity indicator\n"
            "- Refi timing correlation — registry churn vs credit event",
            "1. Sunbiz amendment log\n2. Recorder refi signatories\n3. Subpoena nominee engagement letters (cited path)",
            "FATF nominee director typologies; Florida Sunbiz"),
        "category": "NOMINEE_DIRECTOR_ROTATION", "research_lane": "E9", "pair_kind": "RED_FLAG", "source": "FATF", "difficulty": "intermediate",
    },
    {
        "instruction": "Typology recognition: lawful BOI access paths vs public OSINT limits.",
        "input": "Brief: 'Can detectives browse BOI like SOS?'",
        "output": typo("CTA BOI ACCESS PATHS",
            "PUBLIC SOS ≠ BOI:\n- BOI filed with FinCEN, not county recorder\n- Law enforcement access via defined channels — not ARGUS open browse\n- Missing BOI (via lawful inquiry) = compliance gap indicator, not guilt\n- Combine with SOS opacity, timing, sanctions, digital footprint",
            "FinCEN CTA (fincen.gov/boi); FinCEN access FAQ"),
        "category": "CTA_BOI_GAP", "research_lane": "E9", "pair_kind": "TYPOLOGY_RECOGNITION", "source": "FinCEN", "difficulty": "basic",
    },
    {
        "instruction": "Expand officer churn graph across family LLC network.",
        "input": "Four LLCs (husband/wife/spouse LLCs) rotate managers every 30 days for 4 months. Shared home address on SOS. Fifth LLC acquires commercial property; manager is Cayman corp services.",
        "output": dossier("ARGUS-R2-E9-004", "Family LLC network — officer churn",
            ["FAMILY_ENTITY_NETWORK", "OFFICER_CHURN_PRE_TRANSACTION", "OFFSHORE_CORPORATE_MANAGER"],
            "INVESTIGATIVE_INDICATOR",
            "- Inter-family manager rotation — control obfuscation within related-party graph\n"
            "- Cayman apex on acquiring LLC — offshore manager indicator",
            "1. SOS amendment timeline all five LLCs\n2. Recorder commercial deed\n3. CTA BOI escalation path citation",
            "FinCEN CTA; FATF layered ownership"),
        "category": "OFFICER_CHURN_PRE_TRANSACTION", "research_lane": "E9", "pair_kind": "INVESTIGATIVE_INDICATOR", "source": "FinCEN", "difficulty": "intermediate",
    },
    {
        "instruction": "Typology recognition: UBO tracing stop conditions and NOT FOUND discipline.",
        "input": "When does ARGUS halt UBO expansion without guessing?",
        "output": typo("UBO TRACING STOP CONDITIONS",
            "HALT AND FLAG NOT FOUND WHEN:\n- Only privacy proxy / corporate apex remains\n- Foreign registry requires MLAT for deeper extract\n- Name match ambiguous without primary document\n\nNEVER infer natural person from common name collision alone.",
            "FATF R24; FinCEN CDD rule"),
        "category": "UBO_TRACING_WORKFLOW", "research_lane": "E9", "pair_kind": "TYPOLOGY_RECOGNITION", "source": "FATF", "difficulty": "basic",
    },
    {
        "instruction": "Enrich Irish RBO cross-border mention tied to US LLC manager.",
        "input": "US DE LLC lists manager 'Celtic Fiduciary Ltd' (Ireland). Open web RBO portal shows entity registered but no PSC published yet per registry note. LLC acquired Boston condo all-cash 16 days post-US formation.",
        "output": dossier("ARGUS-R2-E9-005", "Celtic Fiduciary — IE→US manager",
            ["CROSS_BORDER_CORPORATE_MANAGER", "FOREIGN_RBO_DELAY", "RAPID_FORMATION_ACQUISITION"],
            "RED_FLAG",
            "- Irish fiduciary manager on newborn US LLC — cross-border opacity\n"
            "- RBO delay note on open portal — foreign BO visibility gap\n"
            "- 16-day formation-to-close — FinCEN timing marker",
            "1. Ireland CRO public extract\n2. DE SOS US LLC pull\n3. Suffolk County recorder deed",
            "Ireland CRO/RBO public portal; FinCEN FIN-2017-A003"),
        "category": "BENEFICIAL_OWNER_OPACITY", "research_lane": "E9", "pair_kind": "RED_FLAG", "source": "FATF", "difficulty": "advanced",
    },
    {
        "instruction": "Map layered management LLC depth for enrichment priority scoring.",
        "input": "OpCo (PA) ← HoldCo (DE) ← ManageCo (DE) ← 'Global Corporate Services' (Nevada). No natural person on any extract. OpCo acquired warehouse all-cash.",
        "output": dossier("ARGUS-R2-E9-006", "Four-tier management stack",
            ["LAYERED_MANAGEMENT_LLC", "BENEFICIAL_OWNER_OPACITY", "UBO_TRACING_WORKFLOW"],
            "RED_FLAG",
            "- Depth-4 corporate management — FATF layered ownership indicator\n"
            "- All-cash warehouse acquisition at OpCo tier — asset at base, opacity at apex",
            "1. PA/DE/NV SOS cascade pull\n2. Recorder warehouse deed\n3. Title signatory subpoena path",
            "FATF BO guidance; FinCEN CTA"),
        "category": "LAYERED_MANAGEMENT_LLC", "research_lane": "E9", "pair_kind": "RED_FLAG", "source": "FATF", "difficulty": "advanced",
    },
]

E10 = [
    {
        "instruction": "Run adverse media screen with negative OFAC SDN and BIS fuzzy hit.",
        "input": "TX logistics LLC. Two 2023 trade articles mention Iranian port call (unverified). OFAC SDN search zero. BIS fuzzy 74% on UAE forwarder name variant.",
        "output": dossier("ARGUS-R2-E10-001", "TX logistics — adverse media screen",
            ["ADVERSE_MEDIA_PORT_CALL", "NEGATIVE_OFAC_SDN", "BIS_FUZZY_FORWARDER"],
            "INVESTIGATIVE_INDICATOR",
            "- Trade press port-call — Tier C adverse media lead\n"
            "- Negative OFAC screen documented — does not clear BIS review\n"
            "- 74% BIS fuzzy — human adjudication required",
            "1. Archive article URLs with dates\n2. Texas SOS officer history\n3. Human export-control review",
            "OFAC Sanctions List Search; BIS Entity List; FATF adverse media guidance"),
        "category": "ADVERSE_MEDIA_SANCTIONS_SCREEN", "research_lane": "E10", "pair_kind": "INVESTIGATIVE_INDICATOR", "source": "OFAC", "difficulty": "intermediate",
    },
    {
        "instruction": "Reconcile OpenCorporates officer pivot against primary Delaware SOS.",
        "input": "OpenCorporates lists 'Jane Q Public' as officer on DE LLC. Fresh DE SOS extract same day shows only corporate registered agent — no Jane Q Public.",
        "output": dossier("ARGUS-R2-E10-002", "OpenCorporates mismatch — DE LLC",
            ["AGGREGATOR_SOS_MISMATCH", "NOT_FOUND_OFFICER", "OSINT_AGGREGATOR_WORKFLOW"],
            "RED_FLAG",
            "- Aggregator/officer not on primary SOS — stale or incorrect republish indicator\n"
            "- Must flag NOT FOUND — do not add Jane Q Public edge to graph",
            "1. Archive OpenCorporates snapshot\n2. DE SOS primary pull with timestamp\n3. Escalate only if secondary source confirms",
            "FATF R24; Delaware Division of Corporations; GAO methodology"),
        "category": "OSINT_AGGREGATOR_WORKFLOW", "research_lane": "E10", "pair_kind": "RED_FLAG", "source": "GAO", "difficulty": "intermediate",
    },
    {
        "instruction": "Typology recognition: source credibility tiers for ARGUS enrichment outputs.",
        "input": "Train analysts on Tier A/B/C/D source handling.",
        "output": typo("SOURCE CREDIBILITY TIERS",
            "TIER A: SOS, EDGAR, recorder, OFAC/BIS official — primary citation\n"
            "TIER B: DOJ/FBI/FTC/FinCEN advisories — typology grounding\n"
            "TIER C: Trade press, docket excerpts — verify before graph edge\n"
            "TIER D: Paste/leak sites — do not pivot; NOT FOUND\n\n"
            "Every lead exports URL + retrieval timestamp.",
            "GAO public records research; FATF OSINT guidance"),
        "category": "OSINT_AGGREGATOR_WORKFLOW", "research_lane": "E10", "pair_kind": "TYPOLOGY_RECOGNITION", "source": "GAO", "difficulty": "basic",
    },
    {
        "instruction": "Enrich fleet packet with source_id propagation per LE rails.",
        "input": "ATREIDES packet materials: SYNTH-DEED-001, SYNTH-WIRE-002. Task: enrich_entity with public records only.",
        "output": dossier("ARGUS-R2-E10-003", "Fleet packet — source_id discipline",
            ["SOURCE_ID_PROPAGATION", "FLEET_PACKET_ENRICHMENT", "SYNTH_DEED_WIRE_CLUSTER"],
            "INVESTIGATIVE_INDICATOR",
            "- Each lead must cite SYNTH-DEED-001 and/or SYNTH-WIRE-002 — empty source rejection per HELIX rails\n"
            "- WY LLC 14-day formation + intermediary wire = combined opacity cluster",
            "1. Map SOS+recorder leads → SYNTH-DEED-001\n2. Map wire mismatch leads → SYNTH-WIRE-002\n3. ATLAS handoff for graph edges",
            "LE_AI_Product_Rails_v1; FinCEN FIN-2017-A003"),
        "category": "RE_OSINT", "research_lane": "E10", "pair_kind": "INVESTIGATIVE_INDICATOR", "source": "COMPOSITE", "difficulty": "intermediate",
    },
    {
        "instruction": "Document negative search when unverified media claims foreign BO.",
        "input": "Blog claims Luxembourg registry shows Russian national owns US LLC. Official RCS extract not in packet. Only screenshot from blog.",
        "output": dossier("ARGUS-R2-E10-004", "Blog registry claim — unverified",
            ["UNVERIFIED_MEDIA_REGISTRY", "NOT_FOUND_PRIMARY_EXTRACT", "NESTED_FOREIGN_OWNERSHIP"],
            "RED_FLAG",
            "- Blog screenshot without RCS extract — Tier D source, do not pivot\n"
            "- Flag NOT FOUND on BO claim until official extract or MLAT",
            "1. Seek Luxembourg RCS via MLA channel\n2. US SOS LLC extract\n3. Do not cite blog as BO proof",
            "FATF R24; OFAC guidance on source verification"),
        "category": "NESTED_FOREIGN_OWNERSHIP", "research_lane": "E10", "pair_kind": "RED_FLAG", "source": "FATF", "difficulty": "intermediate",
    },
    {
        "instruction": "Archive retrieval discipline for adverse media escalation.",
        "input": "Two conflicting trade articles on same ship call — one retracted. Analyst must preserve both snapshots for compliance review.",
        "output": dossier("ARGUS-R2-E10-005", "Conflicting adverse media — archival duty",
            ["ADVERSE_MEDIA_RETRACTION", "ARCHIVAL_RETRIEVAL_DISCIPLINE", "SOURCE_CREDIBILITY_REVIEW"],
            "INVESTIGATIVE_INDICATOR",
            "- Retracted article still archived — demonstrates source credibility review\n"
            "- Conflicting narratives require human analyst adjudication",
            "1. Archive both URLs with Internet Archive or local PDF\n2. Document retraction notice\n3. No automatic sanctions escalation",
            "FATF adverse media guidance; GAO methodology"),
        "category": "ADVERSE_MEDIA_SANCTIONS_SCREEN", "research_lane": "E10", "pair_kind": "INVESTIGATIVE_INDICATOR", "source": "GAO", "difficulty": "basic",
    },
    {
        "instruction": "Typology recognition: when to escalate OFAC vs BIS vs FinCEN parallel tracks.",
        "input": "Entity has negative SDN but BIS 78% fuzzy on partner.",
        "output": typo("SANCTIONS SCREEN ESCALATION",
            "NEGATIVE SDN ≠ ALL CLEAR:\n- BIS export-control fuzzy still escalates\n- FinCEN 311 jurisdiction in wire path — parallel track\n- Adverse media Tier C — separate review\n\nARGUS documents screens; human officers adjudicate.",
            "OFAC; BIS; FinCEN 311 announcements"),
        "category": "SDN_SCREENING_WORKFLOW", "research_lane": "E10", "pair_kind": "TYPOLOGY_RECOGNITION", "source": "OFAC", "difficulty": "basic",
    },
    {
        "instruction": "Enrich public PACER party search pivot to SOS entity (public docket only).",
        "input": "PACER docket (public excerpt): 'Summit Ridge LLC' defendant in civil forfeiture. Same name as WY LLC in unrelated SOS filing. Forfeiture complaint cites wallet cluster from DOJ press release exhibit.",
        "output": dossier("ARGUS-R2-E10-006", "Summit Ridge — PACER + SOS name collision",
            ["PACER_PARTY_NAME_COLLISION", "FORFEITURE_DOCKET_NEXUS", "DOJ_EXHIBIT_WALLET_TAG"],
            "RED_FLAG",
            "- Name collision between forfeiture defendant and SOS LLC — enrichment priority, not identity merge\n"
            "- DOJ exhibit wallet tag — public blockchain OSINT lead only",
            "1. Compare SOS file number vs docket entity details\n2. Archive DOJ exhibit paragraph\n3. Human analyst confirms or rejects merge",
            "PACER public dockets; DOJ press releases; Wyoming SOS"),
        "category": "ADVERSE_MEDIA_SANCTIONS_SCREEN", "research_lane": "E10", "pair_kind": "RED_FLAG", "source": "DOJ", "difficulty": "advanced",
    },
]

LANES = {
    "E6_Digital_Footprint_WHOIS_seed.json": ("E6", "digital_footprint_whois", E6),
    "E7_RE_Public_Record_OSINT_seed.json": ("E7", "re_public_record_osint", E7),
    "E8_Multistate_SOS_Pivot_seed.json": ("E8", "multistate_sos_pivot", E8),
    "E9_UBO_Tracing_seed.json": ("E9", "ubo_tracing", E9),
    "E10_OSINT_Workflow_seed.json": ("E10", "osint_workflow_adverse_media", E10),
}

for fname, (lane, topic, pairs) in LANES.items():
    path = RESEARCH / fname
    payload = {
        "metadata": {
            "research_lane": lane,
            "topic": topic,
            "scope": "entity_enrichment_detection_only",
            "corpus": "Stonebridge/Products/ATREIDES/research/ARGUS_Entity_Enrichment_Research_v2.md",
            "built": "2026-06-24",
            "pair_count": len(pairs),
            "run": "Run2",
        },
        "pairs": pairs,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {fname}: {len(pairs)} pairs")

print("total Run2 pairs:", sum(len(p) for _, _, p in LANES.values()))
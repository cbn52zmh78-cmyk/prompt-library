# Pre-Publish QA Verdict — `david_latin_corpus_v1`

**Gate:** C4 #167 Pre-Publish QA Gate v1 · **Reviewer:** C4
**Master:** `DAVID/productions/david_latin_corpus_v1_longform_v1/output/david_david_latin_corpus_v1_seamless_v1.mp4` (8.6 MB, 68.05 s)
**Reviewed:** 2026-06-19 · **Episode:** *Why Latin Never Really Died | DAVID · The Archive*

## VERDICT: **SHIP** ✅ — cleared for upload (2 advisories, non-blocking)

All four QA dimensions PASS. No FAIL, no VERIFY. The two advisories below are quality nits to fold
into the next brand pass, not release blockers.

---

## Scorecard

| Dim | Row | Verdict | Evidence |
|-----|-----|:-------:|----------|
| **1 Render** | R1 master exists | PASS | `output/…_seamless_v1.mp4` 8.6 MB; `upload_kit/manifest.json.source_video` resolves |
| | R2 shots assembled | PASS | 8/8 chains processed + xfade chain through `chain_07`; provenance joined (`provenance_matched_*`); `extend_state.segments=8` |
| | R3 duration on target | PASS | 68.05 s vs target 69 s |
| | R4 picture spec | PASS | 720p / 16:9 per `config` |
| | R5 audio QC | PASS | `qa_report`: −16 LUFS two-pass, spread **0.05 LU**, audio present, A/V sync pinned |
| | R6 color/continuity | PASS | magenta **0.000 ≤ 0.42**, lamp 3200K Δ=0.000 across segments |
| | R7 qa_report green | PASS | `qa_report.json` `pass: true`, `issues: []` |
| **2 Gate 0** | G1 latest GREEN | PASS | newest `GATE_GREEN_…_20260619_003238.json` (post-render) = GREEN |
| | G2 gate ≥ master | PASS | gate 00:32 > render 00:24 |
| | G3 six rows PASS | PASS | rows 1–6 all PASS |
| | G4 no hard stops/counsel | PASS | `hard_stops: []`, `counsel_flags: []` |
| | G5 sub-gates clear | PASS | `historical_figure_gate` & `science_gate` `applies:false` / N/A |
| | G6 intake agrees | PASS | `intake.gate_0` GREEN, `blocked:false`, `human_signoff:true`, channels = social/streaming |
| **3 Honesty** | H3 attested/reconstructed labeled | PASS | shot 07 `on_screen: "RECONSTRUCTED PRONUNCIATION · Classical Latin"` |
| | H4 no silent upgrade | PASS | shot 06: "classical vowel length is largely reconstructed from meter. I label each claim accordingly." |
| | H1/H2/H5 | N/A | not a science or historical-figure production; science rail returns N/A |
| **4 Brand** | B1 channel bug | PASS | shot 01 `on_screen: "DAVID · The Archive"` |
| | B2 closing card locks | PASS | provenance title/subtitle/footer = locked copy |
| | B3 parent + AI disclosure | PASS | `upload_kit/seo/description.txt`: "Upon Tyne Productions" + "Synthetic media disclosure: characters and performances are fully synthetic. No real-person likeness." |
| | B4 publish metadata | PASS | title `… | DAVID · The Archive`; playlist `DAVID · The Archive`; CTA locked |
| | B5 look locks in prompts | PASS | every shot carries `@David-001` / `@Set-Archive-001` / `@Style-Documentary-Prestige-001`, amber-3200K, no-magenta/no-teal |

---

## Advisories (fold into next pass — do NOT block this upload)

1. **Closing-card parent line.** AI disclosure + parent credit ship via the description
   (`B3` satisfied). Brand §5.5 also calls for the burned-in closing-card parent line
   *"Upon Tyne Productions · Synthetic host · AI disclosure in description"*. The rendered
   `provenance_card` carries only the CTA footer. Add the parent line to the card template for the
   stronger in-video form.
2. **Stale gate reports.** `Legal_Gate/` holds several superseded `COUNSEL`/`YELLOW` runs for this
   slug (22:41–00:27) alongside the governing GREEN (00:32). Housekeeping only — but reviewers must
   cite the **newest** report (the gate rule), never a stale COUNSEL.

## Upload action items (human, from `upload_kit/CHECKLIST.md`)

Upload kit is complete and `qa_pass: true`. Remaining boxes are the manual publish steps: paste
`seo/description.txt`, set category Education, finalize thumbnail from `thumbnail/THUMBNAIL_BRIEF.json`,
configure end screen. Confirm the platform AI-label toggle is set at upload (social = mass dissemination).

---

*C4 #167 · gate def: `DAVID/reports/C4_167_PrePublish_QA_Gate.md` · Upon Tyne Productions / DAVID · The Archive*

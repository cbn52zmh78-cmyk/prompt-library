# INTERPRETATION_GATE — Visual-Source Interpretation v1 (the 7 rails)

> Gate for interpreting **visual sources** (writing systems, proto-writing, art-as-communication).
> Wired into DAVID's gate system via `Nexus/gates/visual_source_interpretation_gate.json` and
> `DAVID/scripts/visual_source_gate.py`. RED = hard stop; honest "UNDECIPHERED" always beats a
> plausible invention. Mirrors the ecosystem honesty rails (STD-CITE-001, 403=park, no fabrication).

A manifest entry passes ONLY if it clears all 7 rails.

## R1 — Attested decipherment only
A claim of **meaning** requires a cited scholarly decipherment. No speculative reading may be
presented as established fact. `decipherment_status: DECIPHERED` ⇒ must carry an `interpretation`
**and** at least one citation.

## R2 — Decipherment status is mandatory and explicit
Every source is tagged `DECIPHERED | PARTIALLY_DECIPHERED | UNDECIPHERED`. The status field is
required; an entry with no status is RED.

## R3 — Citation per interpretive claim (STD-CITE-001)
Each reading/translation/interpretation cites a source graded `primary | secondary | tertiary`.
Uncited interpretation is RED.

## R4 — Provenance + license on every image
Every image carries `source_url` + `license` (+ holding repository where known). If the source
returns 403/paywall/blocked → **PARK it** (`harvest_status: PARKED`, logged in `parked_sources`),
never fabricate the asset or its provenance.

## R5 — Transcription ≠ Transliteration ≠ Interpretation
Keep the three layers as **separate fields** — `transcription` (signs/glyphs as drawn),
`transliteration` (phonetic/sign values), `interpretation` (meaning). Collapsing them is RED.

## R6 — Confidence + dissent recorded
Record scholarly `confidence` and note competing readings in `dissent[]` (may be empty, but the
field must exist). Presenting one reading as settled when the field is absent is RED.

## R7 — No fabrication / no anachronism (the honesty rail)
`UNDECIPHERED` (or the undeciphered portion of `PARTIALLY_DECIPHERED`) must have
`interpretation: null` — **asserting a meaning for an undeciphered source is RED.** No invented
glyphs, no retrojected modern meaning. The honest gap is the deliverable.

---

**Verdict:** all 7 rails clear → `PASS`. Any rail RED → `FAIL` with the failing rail(s) named.
The gate is enforced per-entry; a manifest passes when every entry passes.

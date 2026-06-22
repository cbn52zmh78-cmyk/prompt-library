# DAVID — Visual-Source Interpretation (capability v1, DRAFT)

**2026-06-19 · Owner: NEXUS · Repo: DAVID (communication/language channel).**

> New DAVID capability: **read and interpret written and spoken communication that exists only as
> imagery** — writing systems (hieroglyphics, cuneiform), proto-writing / pictographs, and
> **art-as-communication** (narrative art, iconography). Lives in DAVID (not SCRIBE) because DAVID owns
> language/communication and already has `communication-modalities/writing-systems/` and
> `languages/undeciphered/`. It is a **feeder capability**: image in → cited interpretation out → AI → STUDIO
> (a DAVID video) or SCRIBE (a written piece), per `AI/docs/Feeder_AI_STUDIO_Handoff_Contract_v1.md`.

## Why DAVID, not SCRIBE
- DAVID is the communication/language channel; its tree already has `writing-systems/` and `undeciphered/`.
- SCRIBE is a text→text editorial engine — wrong input modality. It **consumes** the interpreted output
  downstream (writes it up), but it does not do image→meaning decoding.

## Where it slots (DAVID tree)
- `communication-modalities/visual-source/` (new) with sub-lanes:
  - `writing-systems/` — deciphered scripts read from imagery (Egyptian hieroglyphs, cuneiform, Mayan glyphs).
  - `proto-writing/` — pictographs / ideographs / tallies (early sign systems).
  - `art-as-communication/` — narrative art, iconography, symbolic programs (meaning encoded in imagery).
  - ties to existing `languages/undeciphered/` — the honesty-critical lane (Linear A, Rongorongo, Indus, Phaistos).

## Pipeline (feeder)
```
SOURCE IMAGE (inscription / artwork / glyph)  →  VISION READ (transcribe glyphs / describe imagery)
   →  SCHOLARLY CROSS-REFERENCE (cite decipherment sources; consensus + competing readings)
   →  INTERPRETATION GATE  →  cited FeederPacket  →  AI (route/review)  →  STUDIO (video) | SCRIBE (write-up)
```
Output is a `FeederPacket` (per the handoff contract): the transcription/interpretation, per-claim citations,
confidence, competing readings, artifact provenance, and gate status.

## ⭐ INTERPRETATION GATE (the rails — this is what makes it trustworthy)
A claim does not leave the capability unless it passes:

1. **Never fabricate a translation of an undeciphered or disputed script.** Linear A, Rongorongo, Indus,
   Phaistos Disc, etc. are presented **as undeciphered** — show competing scholarly hypotheses, never invent
   a confident translation. This is the #1 rule. Undeciphered = labeled `UNDECIPHERED`, not "translated."
2. **Every interpretive claim is cited** (STD-CITE-001), graded by scholarly consensus.
3. **Show competing/disputed readings** where scholars disagree (conflict-reconciliation, not one confident answer).
4. **Confidence is explicit** per claim (established decipherment vs. probable vs. contested vs. undeciphered).
5. **Artifact provenance + image licensing** — source the inscription/artwork to a museum/repository,
   public-domain or cleared images, cited like the SCIENCE/HISTORY reference-plate manifests; 403/blocked = park.
6. **Cultural sensitivity** — sacred/indigenous/religious imagery gets respectful attribution; no
   misappropriation, no claimed authority over living cultures' material.
7. **AI-assisted disclosure** — this is cited scholarly *synthesis*, not original epigraphy; defer to scholars.

Wire alongside the existing gates (Knowledge / Science / Historical-Figure) — same gate-report pattern.

## Content fit (DAVID channel)
Pairs with DAVID's dead/ancient-communication theme and the ≤1900 Historical-Figure framing: "what this
inscription actually says," "how we know," "what's still undeciphered." Strong, honest, education-first content —
and the honesty (showing the undeciphered/contested cases truthfully) is itself the differentiator.

## Build steps
1. **Scaffold** `communication-modalities/visual-source/{writing-systems,proto-writing,art-as-communication}` +
   an `INTERPRETATION_GATE.md` spec (the 7 rails above) wired into DAVID's gate system.
2. **Source register + image manifest** (reuse the SCIENCE/HISTORY reference-plate manifest pattern:
   artifact, repository, license, source URL, parked-if-blocked).
3. **POC**: one deciphered example (e.g., a hieroglyphic cartouche with cited reading) + one honestly-flagged
   **undeciphered** example (e.g., Phaistos Disc — show hypotheses, no fake translation) → prove the gate.
4. **Emit a FeederPacket** from the POC → validate the handoff into AI → STUDIO/SCRIBE.

## Rails
- DRAFT. Public/licensed sources only; cite everything; undeciphered = never faked; cultural respect;
  AI-assisted-synthesis disclosed. Feeds AI per the handoff contract.

---
SCRIBE DIALOGUE REPORT
Agent:         Dialogue_Editor_Agent v0.1.0
Slug:          pi_story
Format:        narrative-short-film (Act I feature screenplay slice)
WPS ceiling:   2.8 WPS (narrative-short-film)
Timestamp:     2026-06-20T00:00:00Z

── VERDICT ──────────────────────────────────────────────────
PASS. Dialogue is terse, rhythmically natural, and consistent with the
declared noir register throughout. No LIP_SYNC_FAIL conditions detected.
WPS audit is advisory only (per-beat duration_s not declared in fountain
format); register and clarity audits are complete.

── WPS AUDIT ────────────────────────────────────────────────
Note: This is a .fountain screenplay; no explicit per-beat duration_s
fields are provided. WPS cannot be calculated against timed slots.
Assessment is based on line length, spoken rhythm, and likely screen
time given standard screenplay pacing (~2 pages/minute for dialogue-
heavy film noir).

All dialogue exchanges in PI Story Act I consist of short, punchy lines
(typically 2–12 words per line). No speech block presents a dense
multi-clause passage that would create LIP_SYNC_RISK at narrative-short-
film's 2.8 WPS ceiling. The single most word-dense spoken passage is the
CI recitation ("three names and a place") — which is authored as a rapid
flat delivery ("flat, memorized"). This is directorial intent and is
achievable within ceiling.

Estimated WPS review by exchange:

| scene / exchange         | approx. words per line | rhythm      | status  |
|--------------------------|------------------------|-------------|---------|
| Bar (PI + Bar Owner)     | 2–12                   | Laconic     | OK      |
| Hot Dog Cart (PI + Cop)  | 3–10                   | Terse       | OK      |
| CI exchange (PI + CI)    | 2–8 per line; CI recitation ~8–12 total | Flat, rapid | OK — advisory note below |
| Café (PI + Femme Fatale) | 3–9                    | Warm, clipped | OK    |
| SUV (crew banter + Hitman)| 4–8                   | Energetic   | OK      |
| Club (Hitman + Mob Boss) | 3–10                   | Warm, authoritative | OK |
| Bar convergence (PI + Hitman) | 2–6              | Charged     | OK      |
| Climax line (PI, quiet)  | 7                      | Quiet, final | OK     |

Overall: All exchanges appear within WPS ceiling for the format. No
beats at risk. WPS PASS (advisory basis — no timed duration data).

── REGISTER AUDIT ───────────────────────────────────────────
CONSISTENT.
Notes: The screenplay maintains a tight noir register throughout both
blocks. No scene shifts into a mismatched register.

PI block: Laconic, compressed, slightly formal — every line is load-
bearing. No line is decorative. Consistent with classic noir PI
archetype.

Hitman block: The SUV banter (tiger debate) is a deliberate register
lift — lighter, energetic, character-revealing — and is immediately
anchored by the Hitman's "mild, final" "It's a real tiger." The shift
is motivated and brief; it serves the character (professional calm
against crew energy) and returns to the professional register at the
club.

Club scene: Mob Boss dialogue is warm-authoritative ("My good one,"
"You never eat"). This register is distinct from the PI block's
transactional exchanges. No mismatch — this is deliberate character
differentiation.

Convergence and climax: Returns to compressed noir register. The
climax line ("You shouldn't have kept the ring.") is seven words,
quiet, final — the most effective line in the script. Register is
correct.

── CHARACTER VOICE CONSISTENCY ──────────────────────────────
PASS.
Notes:
- THE PI: Consistent laconic register in all four scenes (bar,
  bodega/street, café, convergence). No voice drift. "Names first" and
  "Yeah. I do." are characteristic. The climax line ("quiet") matches
  the established register. No inconsistency.

- THE HITMAN: Voice shifts appropriately between contexts (car banter
  vs. club warmth vs. convergence ease) but the underlying register —
  mild, final, unhurried — is consistent. The "small laugh" at the bar
  ("Who can.") is consistent with the character's ease.

- FEMME FATALE: Two appearances. In the café she speaks warmly but with
  constraint ("Whatever it is — you don't have to." / "Text me when
  it's done."). She has no dialogue in the club scene — her moment is
  physical (doesn't move, doesn't warn). Voice consistency: PASS.
  Advisory: The authorial canon note ("illusory agency") is correctly
  expressed in the text. Her café dialogue reads as genuine care rather
  than manipulation, which is consistent with the "she believes she is
  [in charge]" narration.

- FEMALE MOB BOSS: Single scene. Register is clear. No consistency
  issue to flag.

- THE CI: Single scene. Professional, clipped, slightly transactional.
  "That's not how we —" (interrupted) and "Good answer." are in
  register.

- YOUNG BEAT COP: Single scene. Register is deliberately different —
  eager, slightly cliché-invoking ("They said you used to carry a
  shield"). This is character-appropriate for the archetype. No issue.

── CLARITY FLAGS ────────────────────────────────────────────
None identified. All lines are clear, unambiguous, and speakable.

Specific notes:
- "Whatever happens in here tonight." (Bar Owner, scene 01): Fragment
  is intentional; the response ("It doesn't touch you.") completes it
  structurally. Clear and effective.
- "The thing where you're already somewhere else." (Femme Fatale):
  Natural spoken rhythm; no tongue-trip risk.
- "It is NOT a real —" (Crew #1, interrupted by Hitman): The
  interruption pattern is clean. In performance, the Hitman's
  interjection must land before Crew #1 completes the word "tiger."
  Timing note for director, not a script revision.
- "You shouldn't have kept the ring." (PI, climax): Seven words, quiet,
  no syllable clusters. Delivers cleanly at any pacing.

── IPA / PHONETIC REVIEW ────────────────────────────────────
N/A. No period-language, IPA annotations, or reconstructed speech in
this work. Contemporary urban English throughout.

── ATTESTED / RECONSTRUCTED SPEECH COMPLIANCE ───────────────
N/A. Fictional dialogue; no attested-vs-reconstructed compliance
requirement applies.

── RECOMMENDATIONS ──────────────────────────────────────────
Priority 1 (must fix — production blocked):
  None.

Priority 2 (should fix before publish):
  None.

Priority 3 (consider for polish):
  1. CI scene: "three names and a place" is described as recited but
     not transcribed. If the production will hear the CI's voice on
     these names, the names should be written into the script before
     ADR/production stage. Currently written as reported speech from the
     PI's perspective ("he recites — flat, memorized, three names and a
     place"). This is a valid screenplay choice; flag only if the
     director wants the audience to hear the names rather than see the
     PI remember them.
  2. The PI's text message ("We still good for tonight?") appears twice
     — once on the PI's phone (INSERT) and once on the Hitman's phone
     (INSERT). Both are formatted correctly. The Hitman's reply ("Yeah.
     Same time. Same place.") is shown on screen. If this is a sound
     film (notification tone), no issue. If it's a silent insert, no
     issue. Confirm with director whether the reply notification is heard
     or only seen.

── PEER NOTES ───────────────────────────────────────────────
- To Narrative_Editor_Agent: No dialogue issues that feed back into arc
  or character concerns. The Femme Fatale's café dialogue is consistent
  with the "illusory agency" canon note.
- To Structure_Editor_Agent: No WPS violations detected. If STUDIO proof
  scene uses synthetic lip-sync performers, per-beat duration_s data
  should be provided at that production stage for a formal WPS re-audit.

── HARD RAILS TRIGGERED ─────────────────────────────────────
None. Dialogue is within R rating parameters (violence and dark themes,
no hate speech, no content beyond declared rating ceiling). No real
persons. No period-language attestation issues. No IPA claims.
---

---
SCRIBE STRUCTURE REPORT
Agent:          Structure_Editor_Agent v0.1.0
Slug:           pi_story
Format:         narrative-short-film (Act I feature screenplay slice)
Blueprint ref:  Production_Templates_v1.json § formats.narrative-short-film
                Note: Input is a .fountain screenplay, not a .concept.json.
                Field audit adapted for screenplay format per intake.json metadata.
Timestamp:      2026-06-20T00:00:00Z

── VERDICT ──────────────────────────────────────────────────
ADVISORY. The screenplay satisfies structural requirements for an Act I
feature slice at the narrative level; several schema fields are not
present in the .fountain file itself but are confirmed via the companion
intake.json. Gate_0 channels are not declared in any document reviewed —
this is the only advisable gap before Gate 0 submission.

── REQUIRED FIELDS AUDIT ────────────────────────────────────
Note: This input is a .fountain screenplay. Schema fields are drawn from
intake.json (pi_story) and the dispatch plan where not present in the
fountain file itself.

| Field           | Present | Valid | Notes                                                    |
|-----------------|---------|-------|----------------------------------------------------------|
| slug            | Y       | Y     | "pi_story" — confirmed in intake.json and dispatch       |
| title           | Y       | Y     | "PI STORY" — declared in fountain header                 |
| format_id       | Y (inferred) | Y | "narrative-short-film" per dispatch + genre note        |
| tags            | N       | N/A   | Not present in fountain or intake.json — add before Gate 0 |
| beats/scenes    | Y       | Y     | 15 structural divisions confirmed by gate intake note    |
| gate_0.rating   | Y       | Y     | R — declared in intake.json                              |
| gate_0.channels | N       | N     | Not declared in fountain or intake.json — MISSING        |
| provenance_card | N/A     | N/A   | Not required for narrative-short-film format             |

── SHOT COUNT AUDIT ─────────────────────────────────────────
Required min shots (qa_rules.min_shots for narrative-short-film): Not
enforced the same way for a feature screenplay as for a STUDIO concept
schema. Applying scene-count review instead.

Scene/structural divisions submitted: 15 (per gate intake count of
"15 structural division(s) over 2028 words")

Enumerated structural divisions in the fountain file:
  01  INT. NEIGHBORHOOD BAR — NIGHT (opening)
  02  EXT. NEIGHBORHOOD STREET — CONTINUOUS (long take / credits)
  03  INT. CORNER BODEGA — CONTINUOUS
  04  EXT. STREET CORNER — HOT DOG CART — CONTINUOUS
  05  EXT. SIDE STREET — CONTINUOUS (CI exchange)
  06  INT. SMALL CAFÉ — NIGHT (Femme Fatale)
  07  EXT. CAFÉ — CONTINUOUS (PI sends text; end of PI block)
  08  INT. ABANDONED APARTMENT — NIGHT (Hitman block begins)
  09  INT. SUV — MOVING — NIGHT
  10  EXT. SMALL BUSINESS — STOREFRONT — NIGHT (INTERCUT)
  11  INT. THE CLUB — NIGHT (long tracking shot / Mob Boss / Femme Fatale witness)
  12  EXT. NEIGHBORHOOD STREET — NIGHT (stylized dolly, Hitman toward bar)
  13  INT. NEIGHBORHOOD BAR — NIGHT (convergence)
  14  INT. NEIGHBORHOOD BAR — RESTROOM — CONTINUOUS
  15  INT. NEIGHBORHOOD BAR — CONTINUOUS (climax / FADE OUT)

Count: 15. Confirmed against gate intake. PASS.

── BEAT SEQUENCE AUDIT ──────────────────────────────────────
Expected blueprint sequence for narrative-short-film (feature Act I):
  Setup → Inciting Incident → Rising Action → False Climax / Act Break

Submitted beat sequence:
  Setup (01–02): Bar world established; PI characterized
  Inciting Incident (03): Package collected — the seed
  Rising Action (04–07): CI exchange (names + target); Femme Fatale
    (emotional stakes); PI commits; PI block closes
  Parallel Timeline (08–12): Hitman block — establishment, job,
    relationship (Mob Boss), Femme Fatale witness moment, convergence walk
  Convergence / False Climax (13–15): Bar meeting; ring recognition;
    knives + pool cue + gasoline + lighter; FADE OUT

Sequence is complete and internally consistent for Act I structure.

Extra beats not in blueprint: None (all 15 divisions serve the arc)
Missing blueprint beats: None identifiable at Act I scope

── DURATION AUDIT ───────────────────────────────────────────
Format bounds for narrative-short-film (per Production_Templates_v1.json):
  min / default / max: N/A for feature screenplay slice.

For reference: 2028 words at an average screenplay pace (~1 min/page, ~1
page/55–60 words of action/dialogue) maps to approximately 33–37 pages
equivalent — consistent with a well-paced Act I for a feature film.

Status: WITHIN SCOPE for feature Act I. No duration violation.

── IDENTITY / ACTOR AUDIT ───────────────────────────────────
N/A for screenplay format — no actor_id declared; no identity_anchor
required at this stage. Characters are unnamed archetypes (THE PI, THE
HITMAN, FEMME FATALE, FEMALE MOB BOSS, THE CI). No real-person
likeness; intake.json confirms names_real_people: false.

── DOMAIN SUBJECT BLOCK AUDIT ───────────────────────────────
N/A. Format is narrative-short-film (fictional). No historical-figure,
science-subject, or technical-subject block required or present.

── QA RULES COMPLIANCE ──────────────────────────────────────
| qa_rule                      | required | present | status                        |
|------------------------------|----------|---------|-------------------------------|
| require_identity_lock        | N        | N/A     | N/A — no synthetic host       |
| require_synthetic_guard      | N        | N/A     | N/A — no synthetic performers |
| require_reconstructed_labels | N        | N/A     | N/A — fictional content       |

Note: If STUDIO proof scene (step 11 in dispatch) involves synthetic
performers, require_identity_lock and require_synthetic_guard will apply
at that production stage and must be audited before Gate 0 (step 09 in
dispatch).

── RECOMMENDATIONS ──────────────────────────────────────────
Priority 1 (must fix — production blocked):
  None currently blocking. The gate_0.channels gap is advisory only at
  the screenplay review stage; it becomes Priority 1 before Gate 0 run
  (dispatch step 09_gate_0_legal).

Priority 2 (should fix before publish):
  1. Declare gate_0.channels in the intake record or a companion
     metadata file before Gate 0 submission. Required field for any
     production entering the Gate 0 legal step.
  2. Add tags to the intake record (e.g., ["noir", "crime-thriller",
     "feature", "act-i", "r-rated"]) for registry indexing.

Priority 3 (consider for polish):
  - The INTERCUT at EXT. SMALL BUSINESS (division 10) is structurally
    clean but will require a shot-level breakdown when the production
    moves to the STUDIO storyboard phase (dispatch step 10). Flag for
    the storyboard brief.
  - The two announced long-take moments (credits long take at division
    02; long tracking shot at the club, division 11) should each receive
    a production note in the shot plan specifying entry/exit points.
    No structural issue; production planning flag only.

── PEER NOTES ───────────────────────────────────────────────
- To Narrative_Editor_Agent: The 15 scene count is confirmed. No
  structural sequence issues that would affect narrative review.
- To Dialogue_Editor_Agent: Scene 13–15 (convergence / climax) contains
  brief, charged dialogue against physical action. Flag for WPS review
  in the production phase if synthetic lip-sync is used in proof scene.

── HARD RAILS TRIGGERED ─────────────────────────────────────
None. No missing gate_0 block that would trigger a legal pre-step
failure at this review stage (screenplay review precedes Gate 0 in the
dispatch plan). No synthetic performers declared. No real persons
depicted.
---

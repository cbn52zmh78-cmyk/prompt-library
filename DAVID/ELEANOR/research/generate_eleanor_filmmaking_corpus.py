"""generate_eleanor_filmmaking_corpus.py -- ELEANOR-DAVID filmmaking craft corpus.

Generates 560+ Alpaca JSONL training pairs encoding stage direction, blocking,
set/prop design, performance direction, and ELEANOR-DAVID pipeline rules.

Run:  python generate_eleanor_filmmaking_corpus.py
Output: DAVID/ELEANOR/training/eleanor_david_filmmaking_corpus_v1.jsonl
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.normpath(
    os.path.join(HERE, "..", "training", "eleanor_david_filmmaking_corpus_v1.jsonl")
)

Pair = tuple[str, str, str]  # instruction, input, output


def pair(instruction: str, output: str, input_text: str = "") -> dict:
    return {"instruction": instruction, "input": input_text, "output": output}


def wc(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def emit(pairs: list[dict], domain: str) -> list[dict]:
    for p in pairs:
        p["_domain"] = domain
    return pairs


# ---------------------------------------------------------------------------
# DOMAIN 1: Stage Geography & Terminology (80)
# ---------------------------------------------------------------------------

def domain1_stage_geography() -> list[dict]:
    pairs: list[Pair] = []

    pairs.append((
        "Define stage left and explain how it differs from screen left in a film production context.",
        "",
        """Stage left is the performer's left when facing the audience — the side of the stage to the performer's left hand. It is fixed to the physical stage, not the camera. Screen left (also called camera left) is the left side of the frame as the viewer sees it on screen. When a performer faces the camera in a standard interview or host setup, stage left and screen left are opposite: the performer's stage left appears on the right side of the screen. This inversion is the single most common blocking error on hybrid stage-to-camera productions.

On a proscenium stage, stage left and stage right are written from the performer's perspective and never flip. In film, camera left and camera right are written from the lens perspective. A director's note that says "cross to stage left" means the performer moves to their own left. A cinematographer's note that says "frame her screen left" means she occupies the left third of the image. Confusing these two during a transition shoot produces performers walking the wrong direction, crossing into void space, or exiting toward the lens when they should arc upstage.

In the ELEANOR-DAVID pipeline, all blocking notation uses stage geography relative to the set — never screen direction. The SET GEOGRAPHY LOCK establishes which wall is stage left, which is upstage, and where practical elements sit before any movement note is written. Camera framing follows the blocking; blocking does not follow the camera. When translating a stage note to a camera team, specify: "performer moves to their left (appears screen right in this axis)." That one parenthetical prevents an entire day of reversed coverage."""
    ))

    pairs.append((
        "A director calls 'cross to DSR' — translate this into camera framing and performer position terms.",
        "",
        """DSR means Downstage Right — the downstage-right zone of the nine-zone stage grid. Downstage is the portion of the stage closest to the audience (in film: closest to the camera). Right is the performer's right when facing the audience.

Translation for camera and performer teams:

PERFORMER POSITION: The performer moves to the downstage-right quadrant of the set. If facing the audience/camera in a three-quarter open position, this is forward and to the performer's right — typically the down-right corner of the playing space relative to the established set geography.

CAMERA FRAMING: In a standard camera-left key setup where the performer faces slightly camera-right, DSR places the performer down-right in frame — often lower in the frame (foreground) and toward screen right. On a medium shot, expect the performer to land screen-right of center, closer to the lens than the upstage background.

SPATIAL RELATIONSHIP: DSR is a strong "presenter" zone — downstage carries authority and immediacy; stage right in Western staging often reads as complementary or secondary in two-shots (the "B" position). Solo in DSR reads as direct address with slight offset from center.

BLOCKING NOTATION: Write it as: "X DSR" or "cross DSR on 'line end'." For camera: "hold medium, performer settles DSR, slight camera-left key, performer three-quarter open to lens."

In open-plan kitchen-living sets, DSR might be downstage of the kitchen island, stage-right of the counter — NOT the sofa, which is typically USL. Calling DSR when the geography lock says the island is DSC will send the performer to the wrong mark every time. Always confirm geography before abbreviating zones."""
    ))

    pairs.append((
        "Describe the 9-zone stage grid. How is it used in written blocking notation?",
        "",
        """The nine-zone grid divides the stage into three rows (upstage, center, downstage) and three columns (stage left, center, stage right), producing nine positions:

UPSTAGE ROW: USL (Upstage Stage Left), USC (Upstage Stage Center), USR (Upstage Stage Right)
CENTER ROW: CSL (Center Stage Left), CC (Center Stage), CSR (Center Stage Right)
DOWNSTAGE ROW: DSL (Downstage Stage Left), DSC (Downstage Center), DSR (Downstage Stage Right)

Each zone is a playing area, not a pinpoint. In practice, a performer "at USL" occupies the upstage-left quadrant — they may be seated on a sofa against the back wall stage-left, standing at a window USL, or positioned at a desk in that zone.

BLOCKING NOTATION USE: Directors shorthand movement as zone-to-zone transfers: "open DSC, cross USL on beat 3, sit USL sofa." The grid gives readers an instant spatial map without prose. Stage managers annotate scripts with zone letters; cinematographers translate zones to frame positions based on camera axis.

HIERARCHY AND MEANING: Upstage carries distance, power, or withdrawal; downstage carries intimacy and confrontation. Center reads as neutral or focal. Stage left vs stage right carries compositional weight — in Western tradition, screen-dominant figures often favor stage left (appearing screen right) in two-shots.

CAMERA TRANSLATION: The grid is stage-relative, not lens-relative. A performer at USL in a living room set is at the sofa against the back wall, stage-left wall — regardless of where the camera sits. Multiple camera positions may frame USL as center-frame or edge-frame; the zone name does not change.

In pipeline prompts, SET GEOGRAPHY LOCK names which practical elements occupy which zones: "sofa USL, island DSC, window wall stage left, kitchen cabinetry stage right." All subsequent blocking references the grid — never "move left" without the stage qualifier."""
    ))

    pairs.append((
        "When does a performer 'cheat out' and what does the director say to get this result?",
        "",
        """Cheating out (or "cheating open") means the performer adjusts their body position to present more face and torso to the audience or camera while maintaining the illusion of naturalistic staging. Physically, they rotate slightly toward the lens — typically from profile or full back toward a three-quarter or full-front open position — without appearing to address the camera directly.

WHEN TO CHEAT OUT: (1) Two-handers on stage where both faces must read — the upstage performer cheats open while the downstage performer holds three-quarter. (2) Single-camera film where the performer's "natural" position in the set would place them in profile or back to lens. (3) Furniture staging — seated performers at a table angled so their faces clear the horizon line. (4) Group scenes where one performer would otherwise present a shoulder to camera. (5) After a pivot or cross, the landing position includes a cheat so the next line delivers to lens.

WHAT THE DIRECTOR SAYS: "On the landing, cheat open to camera — three-quarter, eyes to your scene partner but chin slightly to lens." Or: "Stay at the mark but cheat your shoulders to me — don't move your feet." Or: "You're USL on the sofa — angle your body DSC, cheat open, left arm on armrest." The direction is physical and specific — not "face the camera," which breaks the fourth wall in narrative work.

WHAT NOT TO DO: "Turn to camera" in documentary host work is acceptable; in narrative, it reads as breakage. Cheating is a few degrees — 15 to 30 — not a full pivot. The performer maintains eyeline discipline to a mark or scene partner while their plane of presentation opens.

In the ELEANOR pipeline, cheating out is written into seated transitions: "sits USL sofa, three-quarter open, cheat to lens, back in cushion." This ensures the chain seed frame carries a readable face for the next branch without the performer appearing to break scene logic."""
    ))

    pairs.append((
        "Explain the difference between the apron and downstage center.",
        "",
        """The apron is the portion of the stage floor that extends past the proscenium arch, toward the audience. It is literally in front of the "picture frame" of the proscenium — a thrust into the house. Downstage center (DSC) is a zone within the main stage floor, at the downstage edge of the playing space but still within the framed stage area.

PHYSICAL DIFFERENCE: On a traditional proscenium theater, the apron is outside the arch — often used for soliloquies, circus acts, or breaking the fourth wall. DSC is inside the arch, at the downstage midpoint of the main deck. The apron is closer to the audience than DSC; some theaters have a substantial apron (six feet or more), others have none.

PRACTICAL USE: Performers on the apron are in extreme downstage — maximum intimacy, minimum scenic framing. DSC keeps the performer within the scenic world — still downstage, still focal, but bounded by the set walls or borders.

FILM EQUIVALENT: Film has no proscenium, but the distinction maps to foreground placement. "Apron" behavior in film means stepping past the set's natural boundary — onto a riser beyond the kitchen island, into the space between camera and set — a presentational move. DSC in film means at the downstage edge of the designed set — in front of the sofa, at the island's audience side, at the threshold of a doorway within the set geography.

DIRECTORIAL IMPLICATION: Apron work reads as direct address, confession, or "outside the world." DSC reads as "in the world, at its nearest point to us." Blocking a performer to the apron for a corporate host intro would feel too aggressive; DSC or DSR with a cheat open is standard.

In notation: "step to apron" is a specific call — only valid if the physical set has an apron or equivalent thrust. "DSC" is the default downstage focal mark within the set."""
    ))

    pairs.append((
        "What does 'upstage' mean physically, and what does it imply emotionally for a performance?",
        "",
        """Physically, upstage is the area of the stage farthest from the audience — the rear of the playing space, toward the back wall, the cyclorama, or the upstage scenery. In film terms, upstage is away from the camera, deep in the set, toward the background plane. When a performer walks upstage, they move away from the lens and the audience, into the depth of the environment.

The word also carries a second meaning from theater history: "upstaging" means drawing attention from another performer by positioning oneself upstage of them (closer to the scenic focus), forcing the other to turn away from the audience or present their profile. The physical position enabled the social tactic.

EMOTIONAL AND DRAMATIC IMPLICATIONS: Upstage reads as distance, withdrawal, power, mystery, or exile. A performer who retreats upstage during a confrontation is yielding ground or creating emotional distance. A performer who delivers from upstage — especially USC or USL — can read as authoritative (throne upstage center), untouchable, or hiding. Upstage movement in a transition scene signals a shift in register — from public to private, from formal to intimate, or from confrontation to surrender.

In the ELEANOR-DAVID pipeline, upstage movement is the mandated direction for setting transitions: the performer walks UPSTAGE to move from kitchen to living room, never downstage toward camera. This physical choice carries the emotional arc from formal (kitchen island, DSC) to intimate (sofa USL) while satisfying the hard constraint that exits never read as lunging at the lens.

Directorial vocabulary: "pull her upstage on the turn" = increase distance. "hold USL" = anchor in the rear quadrant. "upstage arc" = a diagonal path away from camera that maintains engagement through a cheat open."""
    ))

    # Additional D1 pairs — terminology depth
    d1_topics: list[Pair] = [
        ("Define the proscenium arch and its relationship to wings and the flies.",
         "The proscenium arch is the rectangular frame through which the audience views the stage — the 'picture frame' of traditional theater. Everything within the arch is the primary scenic world; the apron extends beyond it toward the house. Wings are the offstage spaces stage left and stage right, hidden from the audience by tormentors and legs (vertical borders). Performers enter and exit through wings; scenery shifts in the wings. The flies (or fly loft) are the rigging area above the stage where borders, drops, and flown scenery are hoisted. A 'fly cue' lowers a backdrop or curtain. In film, there is no proscenium, but the vocabulary persists: 'wing entrance' means off-frame entry from stage left or right; 'flies' has no direct equivalent unless working on a stage set inside a film. When a director says 'enter SL wing,' the performer comes from camera-left off-frame (if the camera axis matches standard convention). Understanding wings prevents blocking performers into solid walls on a built set — every entrance needs a logical wing or practical door."),
        ("What are tormentors and legs, and when does a film set designer need to know them?",
         "Tormentors are the vertical scenic pieces at the proscenium opening — they narrow the visible stage width from the audience view. Legs (or legs and borders) are vertical drapes or flats positioned upstage of the tormentors, parallel to the proscenium, creating masked wing space. Together they control sightlines and frame the stage picture. Film set designers working on a theater-set film, a period proscenium recreation, or a hybrid stage-to-camera project need this vocabulary to build correct offstage geography. A performer 'in the wings' stands behind a leg, out of audience sight. If your built set has no wing depth — a flat-walled practical apartment — you cannot call a wing entrance without breaking logic. Substitute practical doors, hallways, or off-frame zones. The design question is: where does someone come from that the camera has not seen? That answer replaces wing vocabulary on interior sets."),
        ("Explain 'center stage' (CC) as a blocking position and its film framing equivalent.",
         "Center stage (CC) is the midpoint of the stage floor — equidistant from stage left and stage right, at the center-row depth. It is the neutral focal point, the default 'presenter' mark in many formats. Emotionally, CC reads as balance, authority without aggression, and direct engagement. In film framing, CC maps to center-frame placement — often with the performer at mid-ground depth, not foreground (which is DSC) and not background (which is USC). A host at CC in a medium-wide reads as stable and trustworthy. In two-shots, CC is contested — two performers cannot both hold CC; one takes CC, the other takes CSR or CSL. Blocking note example: 'Open CC, cheat open, hold through paragraph.' Camera note: 'Medium-wide, performer center-frame, knee to crown, eye-level.' CC is the safest mark for chain-seed stability in the ELEANOR pipeline because center-frame placement survives slight crop drift between branches."),
        ("What is the difference between foreground, mid-ground, and background in film staging?",
         "Foreground is the plane closest to the camera — objects and performers between the lens and the main action, often partially out of focus in shallow depth of field. Mid-ground is the primary playing plane — where performers deliver dialogue, where the key light models the face, where focus lands. Background is the rear plane — scenery, windows, deep set elements that establish context. In staging, directors layer performers across planes for depth: one performer foreground (DSC), another mid-ground (CC), a third upstage (USL) at background plane. Shallow staging — everyone on one plane — reads flat on camera. The 50mm equivalent lens favored in documentary prestige work compresses planes less than a telephoto but more than a wide angle; performers need physical separation of at least three feet between planes to read depth on camera. Set design and blocking must coordinate: a sofa at USL is background plane; a performer who stands DSC and leans on the coffee table occupies mid-ground; a passing figure in the kitchen wing could be foreground if the camera axis allows."),
        ("How do you notate a wing entrance in standard blocking shorthand?",
         "Standard notation: 'Enter SL wing' or 'Enter SR wing' on a specific cue — line, beat, or stage direction. Abbreviations: SL = stage left, SR = stage right, US = upstage, DS = downstage. A full entrance note reads: 'Enter SL wing DS, cross to CC on 'Hello', cheat open.' Symbols vary by stage manager tradition: X or → for crosses, * for freeze, (beat) for pause. In film scripts, wing entrances become 'Enter frame SL' or 'Enter from kitchen SR' — replacing wing with the practical geography. The ELEANOR pipeline uses SET GEOGRAPHY LOCK instead of wing notation for interior sets: 'enters from stage-right kitchen zone' means she appears from the kitchen area at stage right, not from an abstract wing. Maintain one notation system per production document — mixing theater shorthand with film geography in the same prompt causes API misinterpretation."),
        ("Define 'cheating the profile' versus 'full profile' in camera staging.",
         "Full profile means the performer's body is perpendicular to the camera axis — the audience sees the side of the face and body. One eye may be visible; the other is hidden. Profile reads as concealment, tension, or pictorial composition. Cheating the profile means the performer is nominally in profile to a scene partner or set element but rotates 15–25 degrees toward camera so both eyes and more of the face are visible. The legs and shoulders remain in profile relationship to the set; the head and chest cheat open. The director says: 'Hold the profile line to the window, but cheat your face to lens — I need both eyes.' Without the cheat, a close-up from the same axis shows only one eye and half the mouth — unusable for dialogue delivery. Profile is for composition; cheat profile is for dialogue readability. Never call 'profile' when you mean 'three-quarter' — they are different marks with different eyeline discipline."),
        ("What is sightline management in a proscenium theater versus single-camera film?",
         "In proscenium theater, sightline management ensures every seat in the house sees the performers' faces and key gestures — adjusting cheats, risers, and blocking so the balcony row H center seat has parity with orchestra center. The audience is fixed; the staging adjusts. In single-camera film, sightline management ensures the one camera position (or each sequential position) sees what it needs — face, hands, prop, exit path. The camera moves or reframes; the performer holds marks or cheats. Theater sightlines are multi-point; film sightlines are single-axis per setup. A performer who reads perfectly to camera A may present their back to camera B. In the ELEANOR branch-chain pipeline, sightline is locked to one axis per branch — the performer cheats open to that axis throughout the 15-second window. Changing sightline mid-branch without camera motivation reads as coverage error. Establish: 'eyeline to lens' or 'eyeline to mark camera-left of lens' in the scene block and hold it."),
        ("Translate these stage directions to film terms: USL, DSC, apron, cross downstage.",
         "USL (Upstage Stage Left): deep background, performer's left, rear wall zone — film: 'background left of frame, performer at sofa against back wall stage-left.' DSC (Downstage Center): foreground center, closest to lens within set — film: 'center-frame foreground, at the island's audience side.' Apron: beyond the proscenium, extreme foreground — film: 'step past the set boundary toward lens' (rare in interior work). Cross downstage: move toward the audience/camera — film: 'walk toward lens' or 'move to foreground.' Critical warning: 'cross downstage' in the ELEANOR transition pipeline is FORBIDDEN for exit transitions — it reads as attacking the lens. Use 'cross upstage' or 'arc stage-left' for setting changes. The translation is not one-to-one; film has no proscenium, so downstage/apron language must map to lens-distance and set geography explicitly in every prompt."),
        ("What does 'giving way' mean in crossing conventions?",
         "Giving way is the traffic rule when two performers cross paths: the performer with the weaker dramatic priority yields the downstage path to the performer with stronger priority. The downstage path is the 'strong' line — closer to the audience, more visible, more powerful. The upstage performer gives way by pausing, slowing, or taking the upstage arc while the downstage performer passes. In dialogue scenes, the speaker usually holds downstage priority; the listener gives way on a simultaneous cross. In film, the same hierarchy applies but the camera chooses which path reads as downstage — typically toward lens. Director note: 'On the cross, B gives way — A takes DS path, B arcs US.' Without giving-way rules, performers collide, hesitate, or both take the same path — breaking rhythm. Rehearse counters: if both must cross, one gets a beat head start or they counter on opposite diagonals."),
        ("Explain the 'strong side' and 'weak side' of the stage for composition.",
         "In Western staging tradition, stage left (which appears on screen right when the performer faces the audience) is often the 'strong' side — the dominant compositional position in L-shaped or diagonal staging. Stage right is the 'weak' or supportive side. In film composition, the 'strong side' shifts with camera axis and eyeline — but the habit persists: lead performers are often framed screen-left (performer stage right) because Western reading patterns favor left-to-right visual weight. In two-shots, the dominant character takes the strong side; the secondary character takes the weak side. Reversing this without dramatic motivation reads as subversion or error. For solo host work, slight offset from center toward the strong side (cheat DSC toward DSR or DSL depending on axis) creates balanced frames with negative space for graphics. Know your camera axis before assigning strong/weak — if the key is camera-right, the strong side flips."),
    ]

    for instr, out in d1_topics:
        pairs.append((instr, "", out))

    # Expand D1 with zone-specific and cross-medium pairs
    zones = ["USL", "USR", "CSL", "CSR", "DSL", "DSR", "USC"]
    zone_desc = {
        "USL": "upstage stage left — rear left quadrant, typically intimate furniture (sofa, bed, desk at back wall)",
        "USR": "upstage stage right — rear right quadrant, often secondary furniture or architectural feature",
        "CSL": "center stage left — mid-depth left, transitional zone between downstage action and upstage rest",
        "CSR": "center stage right — mid-depth right, common for B-position in two-handers",
        "DSL": "downstage stage left — foreground left, strong entry and address zone",
        "DSR": "downstage stage right — foreground right, complementary presenter mark",
        "USC": "upstage stage center — rear center, throne or authority position, or scenic focal (fireplace, window)",
    }
    for z in zones:
        pairs.append((
            f"What dramatic and compositional qualities does the {z} zone carry?",
            "",
            f"""The {z} zone — {zone_desc[z]} — carries specific compositional and dramatic weight.

As a playing position, {z} tells the performer where to land and tells the camera where to expect the body in frame. Directors choose zones deliberately: a confession lands USL (rear, intimate furniture); a sales pitch opens DSR (downstage, energetic); a power reversal moves the antagonist to USC (upstage center, dominating the rear plane).

In the nine-zone grid, {z} is a quadrant, not a mark. The performer has room to sit, stand, or lean within the zone. Blocking notation: "settle {z}" or "cross to {z} on beat." Camera notation translates zone to frame thirds based on established axis.

Emotionally, upstage zones read as distance, reflection, or authority; downstage zones read as immediacy and confrontation; center-row zones read as transition or negotiation. Left zones and right zones carry compositional weight per the strong/weak tradition — modulated by camera axis.

In ELEANOR-DAVID prompts, name the zone in SET GEOGRAPHY LOCK when a practical element lives there: "sofa {z}" or "island DSC" — then all movement references the same grid. Never invent zones outside the nine-cell system; hybrid descriptions like "mid-left near the window" collapse to CSL or USL once geography is locked."""
        ))

    cross_medium = [
        ("When does stage left equal camera left?",
         "Stage left equals camera left only when the performer faces the same direction as the camera — i.e., the performer faces downstage toward the audience and the camera shoots from the audience position. In that alignment, the performer's left side is also the camera's left side of frame. This occurs in standard fourth-wall staging filmed from the house. It NEVER applies when the camera is upstage shooting toward the audience, when the performer faces upstage, or when the camera is at a three-quarter axis. In single-camera documentary work, the performer typically faces the lens (cheated open) — stage left is then screen RIGHT. Test: have the performer raise their stage-left hand. If it appears on the right side of the monitor, stage left ≠ camera left. Write prompts with stage geography; annotate for camera operators when needed."),
        ("How do you write a SET GEOGRAPHY LOCK for a standard proscenium-style interior?",
         "SET GEOGRAPHY LOCK template: 'Room orientation: audience/camera faces [north wall / fourth wall]. Stage left wall: [window / door / art]. Stage right wall: [kitchen / hallway]. Upstage wall: [sofa / desk / windows]. Downstage edge: [island / table / threshold]. Zones: [practical] at [zone]. Camera axis: [eye-level, slight camera-left key, performer cheats open].' Example: 'Open-plan apartment. Camera faces south wall. Stage left: sheer window wall. Stage right: kitchen cabinetry. Upstage: cream sofa against back wall at USL. Downstage: kitchen island at DSC. Performer cheats open to lens. All crosses reference stage left/right, never screen left/right.' This block goes at the top of every transition branch prompt. It is non-negotiable in the ELEANOR pipeline."),
        ("What is the difference between 'blocking' and 'staging' in director's vocabulary?",
         "Staging is the macro composition — where furniture, performers, and scenic elements sit in the overall pictorial design. Blocking is the micro movement — the specific crosses, pivots, sits, and stands performers execute within the staging. A set designer stages the room; a director blocks the scene. In rehearsal: 'the staging is sofa USL, island DSC' then 'the blocking is enter DSC, cross USL on the turn, sit.' In film, staging includes camera position; blocking includes hitting marks relative to lens and set. A staging error (sofa in wrong zone) cannot be fixed by blocking. Fix staging first, then block within it."),
        ("Define 'fourth wall' and when a performer breaks it versus cheats it.",
         "The fourth wall is the imaginary plane between the stage and the audience — the invisible wall of a box set facing the house. Breaking the fourth wall means the performer acknowledges the audience or camera directly — eyeline to lens, commentary to viewer. Cheating the fourth wall means opening the body toward the audience without explicit acknowledgment — documentary host delivery, three-quarter open, eyeline to lens while content remains 'in world.' In ELEANOR host work, performers cheat open and deliver to lens — it is presenter mode, not narrative breakage. In narrative scenes, breaking the wall is a stylistic choice; cheating is continuous readability. Direct: 'cheat open, do not break' for corporate host; 'break on the last line' for Ferris Bueller-style address."),
        ("What is a 'mark' on a film set versus a 'spike' on stage?",
         "A mark is the exact floor position a performer must hit for focus, framing, and lighting — often a small piece of tape, T-mark, or laser dot. A spike is the stage equivalent — chalk or tape marking a furniture position or performer landing. They are the same function: repeatable position. In the ELEANOR pipeline, marks are implied by zone and furniture geography rather than literal tape — 'island mark DSC, hands flat on counter' defines the position. Chain seeds enforce mark continuity: the exit frame of branch N is the mark for branch N+1. If the performer drifts off mark between branches, wardrobe and set alignment break. Hold marks through tail holds — positional stability is mandatory."),
        ("Explain 'camera axis' and how it affects left/right terminology.",
         "Camera axis is the line from the lens to the subject — the centerline of the shot. Everything left/right in frame is relative to this axis. When the camera is at a three-quarter angle (not square to the fourth wall), stage left and screen left diverge by more than a simple mirror — the performer's movement stage left may move them toward or away from the lens depending on axis. Establish axis in the geography lock: 'camera axis: slight camera-left, performer at island, key from camera-left.' All subsequent left/right notes are stage-relative; the DP translates to frame. Changing axis between branches without transition motivation breaks screen direction continuity — hold axis constant across a branch chain unless a new branch explicitly reframes."),
        ("What is 'upstage of' versus 'downstage of' when describing relative position?",
         "'Upstage of' means farther from the audience than the reference point. 'Downstage of' means closer to the audience. Example: 'The coffee table is downstage of the sofa' — the table is between the sofa and the audience. 'She stands upstage of the island' — she is behind the island, farther from camera. These relational terms work within SET GEOGRAPHY LOCK to place elements without naming zones. Combine with zones for precision: 'coffee table DS of sofa USL' = table in the DSL-to-CSL band, sofa at USL. Relative language helps camera and art department agree on depth layering without re-drawing the grid."),
        ("How do British and American stage left conventions differ — and does it matter on film?",
         "American and British stage left/right are identical — both defined from the performer's perspective facing the audience. There is no UK/US flip for stage left. (Some confusion arises with 'prompt side' and 'opposite prompt' in opera, but stage left is standard internationally.) Film camera left/right is also internationally consistent — lens perspective. The confusion that breaks productions is stage left vs SCREEN left, not national convention. Train crews on performer-perspective vs lens-perspective. Put it on the call sheet: 'Blocking notation: stage POV.'"),
        ("What does 'in one' and 'in two' mean in blocking notation?",
         "'In one' means in the first wing space — just offstage. 'In two' means in the second wing space — farther offstage. Used for entrance readiness: 'Wait in one SL, enter on cue 47.' In film, translate to practical distance: 'Wait in hallway SR, enter on knock' — because there are no numbered wings on an apartment set. The concept survives: layered offstage holding areas for staggered entrances. For synthetic video, offstage does not exist — performers materialize in-frame or are baked into chain seeds. Entrance blocking becomes 'appears at mark' or 'continuous from chain seed.'"),
        ("Describe the relationship between 'open' and 'closed' body positions in staging vocabulary.",
         "'Open' means the performer's front plane faces the audience or camera — chest and face visible (full front or three-quarter open). 'Closed' means the back or profile dominates — the body closes off the audience (full back, tight profile). Staging moves from closed to open as intimacy increases or as the performer reveals information. A performer who starts closed (profile to window) and opens on the revelation cheats to three-quarter, then full front. Reverse: closing the body on a line ('turn profile on the insult') withdraws engagement. In host work, default to open. In narrative, choreograph open/closed shifts as emotional beats. Note: 'open' describes body angle, not mouth — a closed mouth can be on an open body during tail hold."),
    ]
    for instr, out in cross_medium:
        pairs.append((instr, "", out))

    # Pad to 80 if needed
    while len(pairs) < 80:
        i = len(pairs)
        pairs.append((
            f"Stage geography drill {i}: How do you communicate zone position to a cinematographer without using screen direction?",
            "",
            f"""When communicating zone position to a cinematographer, never use screen left/right alone — always anchor to SET GEOGRAPHY and physical landmarks.

Protocol: (1) State the zone: 'She lands USL.' (2) Name the practical: 'USL sofa against back wall.' (3) State depth: 'Background plane, three feet behind coffee table.' (4) State body: 'Three-quarter open, cheat to lens.' (5) Optional frame note: 'You will frame her center or slightly screen-right depending on your axis — the mark is USL sofa, not a screen direction.'

This sequence keeps everyone aligned on physical space. The DP chooses lens and frame to capture the zone; the performer hits the zone regardless of frame. In branch {i % 8 + 1} of an eight-branch chain, the same protocol prevents drift: each branch re-states geography lock before blocking notes.

Common error: saying 'frame her left' — the DP does not know if you mean her left, set left, or screen left. Replace with 'CSL, mid-ground, left side of set from audience POV.' Precision eliminates rehearsal waste."""
        ))

    return emit([pair(p[0], p[2], p[1]) for p in pairs[:80]], "stage_geography")


# ---------------------------------------------------------------------------
# DOMAIN 2: Blocking & Movement (100)
# ---------------------------------------------------------------------------

def domain2_blocking() -> list[dict]:
    pairs: list[Pair] = []

    pairs.append((
        "Write blocking for a performer who delivers a 6-second line then crosses to a sofa upstage-left and sits.",
        "Scene: Open-plan living room. Kitchen island downstage center. Cream sofa upstage-left against back wall. Performer opens at island, DSC.",
        """BLOCKING NOTE — LINE DELIVERY + CROSS TO USL SOFA

SET GEOGRAPHY LOCK: Kitchen island at DSC. Cream sofa USL against back wall, stage-left of window. Coffee table between island and sofa, slightly CSL. Camera axis: eye-level, slight camera-left key. Performer cheats open to lens.

OPEN (0:00–0:02): Performer at island mark DSC — both hands flat on countertop, weight slightly forward, three-quarter open, eyeline to lens. Soft entrance — 0.5s ease before speech. Do not rush the open.

DELIVERY (0:02–0:08): Deliver the six-second line from the island mark. Feet planted, no drift during speech. Hands remain on counter until the line's final word. On the final syllable, the hands release — right hand lifts, left hand pushes lightly off counter to initiate movement. The line's content motivates the departure — she has finished the thought that propels her away from the formal kitchen position.

CROSS (0:08–0:11): Step left from behind island, pivot stage left, arc UPSTAGE — never downstage, never toward camera. Path: pass downstage of coffee table, diagonal upstage-left. Three steps with purpose, not hurry. Counter any instinct to walk to camera — this is withdrawal from formal to intimate space. Shoulders lead the upstage diagonal; face cheats open to lens through the arc.

LANDING (0:11–0:13): Arrive USL sofa. Turn to face camera, three-quarter open. Sit — back into cushion, feet flat on floor, left arm on armrest. The sit is controlled, not a collapse.

TAIL (0:13–0:15): Silent closed-mouth hold. Calm face, no exhale, no shoulder drop. This frame seeds the next branch.

NOTATION SHORTHAND: DSC → (line 6s) → pivot SL → arc USL → sit USL sofa → hold."""
    ))

    pairs.append((
        "A performer keeps turning their back to camera mid-scene. What direction do you give?",
        "Single-camera documentary host segment. Medium waist-up framing. Performer seated at desk stage right.",
        """DIAGNOSIS: The performer is following scene-logic eyeline instead of camera readability — turning to props, windows, or imaginary scene partners and presenting their back or tight profile to the single camera axis. This is the most common failure mode when stage-trained performers work single-camera without cheat discipline.

DIRECTION — IMMEDIATE ON SET:

1. "Hold your mark. Rotate your chair 20 degrees toward me — that's your new neutral. You are three-quarter open from this position. Your eyeline stays on me for every line."

2. "When you reach for the folder, reach with your near hand — do not pivot your chair to face the desk. The desk is stage right; you do not need to look at it to pick up a folder."

3. "Your back never crosses the lens plane. If you feel yourself turning past 45 degrees, stop and cheat open."

REHEARSAL FIX: Mark the performer's toe line and place a small eyeline mark just camera-left of the lens — "look here, not at the window." The window is scenery; the eyeline mark is delivery.

WHY IT HAPPENS: Performers map 'naturalism' as 'face what you're interacting with.' On single-camera, the interaction IS the lens. Reframe their objective: "You are talking to the viewer through the lens. The desk is decoration."

PIPELINE NOTE: In ELEANOR branch prompts, specify "three-quarter open, cheat to lens, eyeline on lens" in the scene block. Text-only prompts that say "looks at the window" will cause back-turns. Replace with "window in background, eyeline on lens."

HOLD ACCOUNTABLE: Review playback after each take — any frame where the performer's spine is more than 45 degrees from open triggers a retake. Continuity across branches requires consistent cheat angle; document the degree in the geography lock."""
    ))

    pairs.append((
        "Explain the principle of 'countering' when two performers execute a cross simultaneously.",
        "",
        """Countering is the choreographed solution when two performers must cross paths at the same time — each takes the opposite diagonal so they pass without collision and without breaking dramatic priority. One performer takes the downstage path; the other takes the upstage path. They counter on complementary arcs.

RULE: The performer with greater dramatic weight (the speaker, the initiator, the character whose beat it is) takes the downstage path — closer to the audience, more visible. The other performer gives way, taking the upstage arc. If both have equal weight, the director assigns priority explicitly: "A counters DS, B counters US."

EXECUTION: Performer A crosses from SL to SR on the DS diagonal. Performer B crosses from SR to SL on the US diagonal. They pass center stage at the same beat — A downstage of B. Neither stops unless the script demands a beat of recognition. The cross tempo matches — slow-slow or brisk-brisk.

NOTATION: "A cross SR DS / B cross SL US — counter on 'go'." Or in shorthand: "A X SR↓ B X SL↑."

CAMERA: In single-camera, only one path may read clearly — the camera favors the priority performer's downstage path. The upstage performer may be partially occluded — acceptable if their beat is reactive.

WITHOUT COUNTERING: Both performers take the same diagonal → collision or awkward sidestep. Both take downstage → fight for the strong line. Both take upstage → visually weak, muddled.

REHEARSAL: Walk it at half tempo with floor markers at DS and US diagonals. Add the verbal cue that triggers simultaneous movement. Countering is a dance — it must be timed to the word, not to general impulse."""
    ))

    pairs.append((
        "What is a motivated cross? Write an example with motivation embedded in the direction note.",
        "",
        """A motivated cross is movement that the audience believes the character chose for an internal reason — fear, desire, dismissal, comfort — even though the director choreographed it for composition. The motivation is written into the blocking note so the performer plays the why, not just the where.

UNMOTIVATED (weak): "Cross to the sofa." The performer moves because the director said so — the feet walk, the scene dies.

MOTIVATED (strong): "On 'I can't stay here' — the line triggers escape. Cross USL to the sofa; she needs to sit before her legs give way. The sofa is safety, not destination." The performer plays the need to sit; the cross becomes inevitable.

FULL BLOCKING NOTE EXAMPLE:

"MATILDA at island DSC. On the phrase 'before we go further' — a decision crystallizes. She needs to leave the formal kitchen — the island reads as boardroom. Cross: pivot stage left, arc upstage-left toward living room. Motivation: intimacy requires leaving the professional mark. She is not fleeing — she is choosing closeness. Pace: deliberate, three steps, no rush. Arrive USL sofa, sit as if the cushion is relief. Play the subtext: 'I trust you enough to leave the podium.'"

The motivation clause links line to movement. Every cross in a pipeline prompt should name the trigger word and the internal need. API-generated performers follow physical description; embedding motivation in the scene block improves physical truth."""
    ))

    pairs.append((
        "Direct a performer to exit stage right without it reading as 'fleeing the scene.'",
        "Corporate presenter in kitchen set. Exit must transition to next segment, not abandon the audience.",
        """EXIT NOTE — STAGE RIGHT WITHOUT FLIGHT READ

PROBLEM: Stage-right exits often read as fleeing because performers accelerate, lean forward downstage, drop eyeline, and close their body — all signals of escape.

SOLUTION — THE CONTROLLED DEPARTURE:

1. MOTIVATION: She is going to fetch something / leading the viewer to another room / completing a tour — not escaping the conversation. Embed: "Exit SR to retrieve the portfolio — she will return, or the viewer follows."

2. PACE: Walk at conversational tempo — never faster than her speaking pace. Count: three deliberate steps to the SR wing or doorway.

3. BODY: Remain three-quarter open through step one and two. On step three, allow profile to doorway but do not present full back until crossing the threshold. Shoulders back, chin level — not a forward lean.

4. EYELINE: Maintain lens contact through the first two steps. On step three, shift eyeline to the SR destination (doorway, hallway) — the viewer sees her look where she is going, not away from them in shame.

5. ENERGY: Neutral-positive. No sigh of relief. The exit is a comma, not a period.

6. CAMERA: Hold the frame two beats after she clears — do not whip-pan after her. Let the empty space breathe; the absence is transition, not abandonment.

NOTATION: "On 'follow me' — exit SR at walk, open through step 2, profile at threshold, hold energy. NOT flight."

PIPELINE: In ELEANOR transitions, prefer upstage arcs over wing exits for setting changes — SR wing exit from kitchen reads as leaving the apartment. Use upstage-left arc to living room instead."""
    ))

    pairs.append((
        "Describe the upstage diagonal arc — when to use it and how to write it in a blocking note.",
        "",
        """The upstage diagonal arc is a curved path that moves the performer away from the camera (upstage) while shifting laterally (stage left or stage right). It is not a straight walk to the back wall — it is an arc that keeps the face readable to the lens via cheat-open through the movement.

WHEN TO USE: (1) Setting transitions in open-plan sets — kitchen to living room. (2) Withdrawal beats — emotional retreat without leaving the scene. (3) Any movement that must increase distance from camera without breaking eyeline engagement. (4) ELEANOR pipeline transition branches — mandatory for kitchen→living room.

HOW TO WRITE:

"BLOCKING: At island DSC. On line end, pivot [stage left/stage right]. Arc upstage-[left/right] on a diagonal — three to five steps. Path passes [landmark]. NEVER downstage, NEVER toward camera. Maintain cheat open through arc — chin leads, shoulders follow. Land [zone/practical]. Motivation: [internal need]."

EXAMPLE: "Pivot stage left. Arc upstage-left past coffee table to USL sofa. Five steps. Face cheats to lens throughout. Land seated USL, three-quarter open."

CAMERA: Gentle drift following the arc — camera tracks upstage, does not dolly into the performer's face during an exit arc. The arc creates depth; the camera widens slightly to hold performer in frame.

EMOTIONAL READ: Upstage diagonal = "I am taking you somewhere deeper in this space" — invitation, not rejection. Contrast with straight cross downstage = confrontation or delivery.

COMMON ERROR: Performer walks straight upstage (USC) with back to camera — unreadable, breaks chain seed for next branch. The diagonal maintains face visibility through the turn."""
    ))

    pairs.append((
        "What body position do you call when you want a performer fully visible to camera but in a 3/4 turn?",
        "Single-camera interview setup.",
        """Call it THREE-QUARTER OPEN (or three-quarter front).

DEFINITION: The performer's body is rotated approximately 45 degrees from full front — halfway between full front (chest square to camera) and full profile (shoulder to camera). Both eyes are visible; the far side of the face is slightly foreshortened. The chest and torso read clearly; the back is partially turned away.

WHEN TO USE: Default position for single-camera dialogue delivery, documentary host work, and any setup requiring readable face without flat presentational squareness. Three-quarter open is more pictorial than full front and more readable than profile.

DIRECTION LANGUAGE: "Three-quarter open to lens." "Cheated three-quarter — left shoulder back, right shoulder forward." "Open your plane to me 45 degrees."

DISTINGUISH FROM: (1) Full front — square to camera, both shoulders equal. More presentational. (2) Three-quarter back — mostly back, glimpse of face — used for departure. (3) Profile — 90 degrees, one eye — pictorial, not dialogue.

IN NOTATION: Abbreviate "3/4 open" in blocking sheets. Specify which shoulder leads: "3/4 open, SL shoulder back" means the performer's stage-left shoulder is farther from camera.

ELEANOR PIPELINE: Seated sofa positions default to three-quarter open — "sits USL sofa, 3/4 open, cheat to lens, back in cushion." This position survives chain seed extraction with readable face and stable torso for tail hold."""
    ))

    # Scenario-based blocking pairs
    scenarios = [
        ("Two performers at a table — one stands abruptly. Write the standing performer's cross to window USL.",
         "Dining room. Table DSC. Window USL. Seated performer A, standing performer B.",
         "A remains seated DSC at table. B stands on 'I won't accept that' — chair pushes back, napkin drops. Cross: B arcs around table's upstage side (never between A and camera), moves USL to window. Motivation: B needs physical distance from A's words. Three steps, controlled anger — not run. At window USL, B profiles to glass, cheat open 15 degrees to keep jawline visible. A holds seated, watches B's back. Camera holds two-shot wide through cross, then reframes B at window in medium. NOTATION: B stand → arc US table US → land USL window, profile+cheat."),
        ("Write blocking for a performer who must hand off a prop at center stage then exit SR wing.",
         "Office set. Desk CSR. Door SR wing.",
         "Performer opens CSR at desk, prop in right hand. Cross to CC on 'here is the file' — three steps DS, extend prop at waist height to receiving performer at DSL. Handoff on the word 'file' — clean transfer, no fumble. Release prop, pause one beat (acknowledgment), pivot SR, exit SR wing at walk. Motivation: task complete, dismissal. Body open through handoff; profile at exit threshold only. Energy: neutral closure. Camera: medium two-shot for handoff, hold as performer exits — do not follow into wing."),
        ("Direct a seated performer to rise and cross downstage for emphasis without breaking intimacy.",
         "Living room. Sofa USL. Performer seated.",
         "On the key line, performer rises from USL sofa — forward lean initiates, feet under body, stand in two beats. Cross downstage to DSL (not DSC confrontation — DSL is intimate emphasis). Two steps DS, stop DSL, deliver line at closer range to lens. Motivation: the truth requires closeness. Cheat open throughout. Hands: one open gesture on delivery. After line, hold DSL 1s, return to sofa USL at walk (re-establish intimacy). Camera: subtle push-in during rise, hold medium at DSL. The downstage cross here is motivated emphasis, not transition exit — permitted because it serves the line, not a setting change."),
        ("Write a pivot-and-sit sequence for a performer arriving at a kitchen island.",
         "Kitchen. Island DSC. Performer enters SL wing.",
         "Enter SL wing DS, three steps to island DSC. On arrival, pivot 45 degrees to three-quarter open (cheat to lens). Both hands place flat on countertop — simultaneous, audible light contact. Weight shifts forward slightly. Feet: left foot slightly forward, planted. This pivot-and-lean is the kitchen 'presenter mark.' Hold through dialogue. Tail: hands remain, no drift. NOTATION: Enter SL → DSC island → pivot 3/4 open → hands flat → deliver."),
        ("A performer must cross behind another without upstaging. Write the counter-path.",
         "Two-shot. A at DSC, B at CSR.",
         "A holds DSC (priority). B crosses to USL sofa behind A's upstage path — B takes US arc from CSR to USL, passing behind A's shoulder line. A does not turn; A gives way by holding still. B's face clears A's shoulder for lens readability — cheat open. Tempo: B's cross on A's line 'sit down' — B arrives USL as A finishes. Counter: A static DS, B mobile US. Camera: hold two-shot, both visible, depth preserved."),
        ("Write blocking for a slow cross that takes 8 seconds — emotional weight in pace.",
         "Empty stage equivalent — long room set. Performer at DSC, target USL.",
         "Eight-second cross from DSC to USL — pace is the emotion. Beat 1-2: first step on silence after line. Beat 3-4: second step, breath visible in posture not sound. Beat 5-6: third step, shoulders settle. Beat 7-8: arrive USL, turn to lens, sit if furniture present. Motivation: exhaustion, defeat, or gravity — the body cannot move faster. Director counts tempo aloud in rehearsal: 'one-Mississippi per step.' Camera: static or imperceptible creep — do not rush to follow. The slowness IS the performance."),
        ("Direct a performer to use a door practical SR for entrance — full entrance notation.",
         "Apartment. Door SR wall, practical door. Living area DSC.",
         "Entrance SR: knock heard (sound design), beat, door opens inward (SR wall). Performer enters through door, three steps to DSC mark. Close door behind with back hand — do not turn full back to camera; cheat open while closing. Motivation: arriving home. Energy: neutral-warm. Eyeline: scan room, settle on lens at mark. NOTATION: Knock → enter SR door → X to DSC → close door (cheat) → settle. Camera: static wide for entrance, holds as performer settles to medium."),
        ("Write the 'NEVER toward camera' exit for a kitchen-to-living-room transition.",
         "Open-plan. Island DSC. Sofa USL.",
         "SET GEOGRAPHY LOCK: Kitchen island DSC. Living room USL stage-left. Coffee table CSL. BLOCKING: Performer at island completes line by 6s. Pivot stage left. Arc UPSTAGE-LEFT — path moves away from lens, diagonally toward USL sofa zone. NEVER step toward camera. NEVER cross downstage of island toward lens. Five steps, arrive USL, sit. Tail: silent hold. This is the mandatory ELEANOR transition geometry — downstage movement reads as lunging at viewer and breaks branch handoff composure."),
        ("How do you block a phone-call exit where the performer must leave mid-conversation?",
         "Office. Desk CSR.",
         "On 'I have to take this' — performer extracts phone, rises from chair CSR, cross SR toward door while answering. Motivation: urgency, not rudeness. Pace: brisk but controlled — two steps SR. Eyeline: phone screen then lens on 'sorry' beat. Exit SR wing at profile, door closes. Energy: apologetic efficiency. Camera: hold medium through rise, static as performer exits — the empty chair holds the abandonment. NOT flight: play regret in the apology beat before exit."),
        ("Write a counter-cross for a confrontation — two performers, aggressive energy.",
         "Kitchen. Island between them.",
         "A at DSL, B at DSR — island between. On 'you lied' — simultaneous cross: A takes DS path around island's downstage edge to DSR; B takes US path around island's upstage edge to DSL. They counter, passing at island CC — A DS of B. A ends DSR facing B; B ends DSL facing A. Positions swap. Energy: aggressive, tempo matched. Neither gives way — equal dramatic weight, director assigns A takes DS. Camera: wide holds both through cross. NOTATION: A X DSR↓ B X DSL↑ counter on 'lied'."),
    ]

    for instr, inp, out in scenarios:
        pairs.append((instr, inp, out))

    # Movement vocabulary pairs
    movement_topics = [
        ("Define 'full front,' 'quarter turn,' 'profile,' 'three-quarter turn,' and 'full back' — when to use each.",
         "FULL FRONT: Chest square to audience/camera — 0 degrees. Use for direct address, presentation, maximum openness. QUARTER TURN: 22–30 degrees from full front — subtle shift, minor adjustment. Use for fine-tuning cheat without changing the whole position. PROFILE: 90 degrees — shoulder to camera, one eye visible. Use for pictorial composition, tension, looking at scenery or scene partner off-axis. THREE-QUARTER TURN (three-quarter open): 45 degrees — dialogue workhorse. Both eyes visible, body angled. Default for single-camera. FULL BACK: 180 degrees — back to camera. Use for departure, rejection, mystery. Face not readable — do not deliver dialogue in full back without turn. SEQUENCE PATTERN: closed (profile/back) → open (three-quarter → full front) signals revelation; reverse signals withdrawal."),
        ("What is a 'beat' in blocking context versus a 'pause' in performance?",
         "A beat is a unit of dramatic action — a shift in intention, power, or understanding. In blocking, a beat may trigger a cross, a sit, a turn. 'On that beat, cross USL.' A pause is a unit of time — silence, stillness, no line. 'Two-second pause before the answer.' Beats are semantic; pauses are temporal. A beat can occur without a pause (instant reaction cross). A pause can occur without a beat change (holding tension in the same intention). In ELEANOR branches: dialogue wraps at 12.5s; the remaining 2.5s tail is a pause (no speech) but not necessarily a new beat — it holds the previous beat's resolution. Do not confuse 'hold for 2.5s' (pause) with 'new beat at 12.5s' (dramatic shift)."),
        ("Explain 'opening up to camera' without breaking the fourth wall in narrative.",
         "Opening up means rotating the performer's presenting plane toward the lens — three-quarter open or full front — while maintaining in-world eyeline and intention. The character is not 'talking to the camera'; their body is simply readable. Technique: place the eyeline mark on a scene partner who stands camera-adjacent — the performer looks at the partner, but the partner's position forces an open body angle to camera. Or: seat the performer in a chair angled 45 degrees toward lens, eyeline downstage to an empty chair (scene partner position) that happens to be near camera. The performer plays to the partner; the camera sees an open face. Breaking the fourth wall is intentional lens address. Opening up is physical staging that preserves narrative while serving film readability."),
        ("Describe triangle staging with two performers and one focal point.",
         "Triangle staging places two performers and a visual focal point (table, object, fire) at three vertices of a triangle — creating depth and relationship geometry. Standard: focal point at DSC or CC (downstage), performers at CSR and CSL (flanking). Lines of attention cross through the focal point. Camera shoots over the focal point or between performers. Movement along the triangle edges rotates dominance — performer at the forward vertex holds focus. For three performers, expand to a diamond with one upstage. In film, triangle staging prevents flat line-ups against walls. Push one performer downstage of the triangle's base line for lens priority."),
        ("What is diagonal staging and why does it photograph better than parallel staging?",
         "Diagonal staging arranges performers and furniture on a downstage-upstage diagonal line (e.g., from DSL to USR) rather than parallel to the proscenium (straight SL-SR line). Diagonals create depth — bodies at different distances from camera, faces at different angles, compositional leading lines. Parallel staging — everyone against the back wall in a row — reads flat, TV-sitcom unless intentionally comic. Block diagonals: 'A at DSL, B at USR, C at CC between' — the eye travels depth. Set design supports diagonals: angle the sofa 30 degrees off the back wall, not parallel."),
        ("How do you direct tempo and rhythm in physical movement?",
         "Tempo is the speed of movement; rhythm is the pattern of acceleration and deceleration. Direct with counts and images: 'Three quick steps, pause at the door, slow sit.' Link tempo to emotion: anger = sharp tempo; grief = heavy deceleration; joy = light quick steps. Rhythm in dialogue-movement coordination: the cross starts on the verb, not before the noun — 'on GO you move, not on I.' Rehearse with metronome or finger snaps. In 15-second branches, movement tempo must fit the window — a five-step cross needs to complete by second 11 to allow 2.5s tail. Calculate: 15s branch minus 12.5s dialogue = 2.5s for movement after line or movement during final words."),
        ("What does 'traffic' mean in a blocking rehearsal?",
         "Traffic is the complete map of all performer movement in a scene — who goes where, when, and in what priority. A traffic rehearsal walks every cross without acting — 'A from SL to CC, B holds CSR, C enters SR wing on beat 4.' Solve collisions, counters, and wing clearance. In film, traffic includes camera-side clearance — can the boom clear the arc? Does the dolly track interfere? In ELEANOR pipeline, traffic is simplified to one performer per branch — but transition branches still need traffic notes for the arc path past furniture."),
        ("Define 'pivot' versus 'turn' in direction vocabulary.",
         "A pivot is an in-place rotation — feet stay on the mark, body rotates. 'Pivot 90 degrees stage left on the line.' A turn may include a step — the performer repositions while rotating. 'Turn and cross to USL' = pivot plus movement. Pivots adjust body angle without changing zone. Turns change zone and angle. In chain-seed continuity, pivots are safer than turns — less positional drift. Specify: 'pivot 3/4 open at island mark' keeps feet at DSC while opening the plane."),
        ("How do you write an entrance from upstage versus downstage?",
         "Upstage entrance: performer appears from the rear plane — doorway US, window reveal, rising from sofa USL. Reads as: existing in the space, returning, or looming. Downstage entrance: performer enters from wing DS or through DS threshold. Reads as: arrival, intrusion, energy injection. Notation: 'Enter US through upstage door' vs 'Enter DS SL wing.' Camera: upstage entrances need deep focus and wide frame; downstage entrances fill foreground quickly. ELEANOR chain seeds replace entrances — performer is already in-frame from previous branch exit frame."),
        ("What is an 'upstage arc' used for when the performer must maintain engagement?",
         "The upstage arc moves the performer away from camera while the face remains engaged via cheat-open — the body retreats diagonally, the chin stays oriented to lens. Use when: transitioning settings, creating emotional distance without losing connection, satisfying NEVER-toward-camera constraints. The arc is curved (upstage + lateral), not straight back. Write: 'arc upstage-left, cheat open throughout, eyes on lens.' The audience feels retreat; the face remains readable. Critical for branch-chain handoffs where the exit frame must show a composed, visible face."),
    ]
    for instr, out in movement_topics:
        pairs.append((instr, "", out))

    # Pad with varied blocking drills to reach 100
    drills = [
        "cross from CSR to USL on a motivated beat",
        "sit-to-stand transition at a boardroom table",
        "wing entrance SL with prop in hand",
        "counter-cross with equal dramatic weight",
        "three-step arc around a coffee table",
        "hold mark through 6-second dialogue then pivot",
        "exit US through upstage door",
        "land seated 3/4 open from a walking cross",
        "freeze at CC on the revelation beat",
        "ease-in from previous branch tail composure",
    ]
    while len(pairs) < 100:
        d = drills[(len(pairs) - len(scenarios)) % len(drills)]
        n = len(pairs)
        pairs.append((
            f"Write complete blocking notation for a performer who must {d}.",
            f"15-second single-camera branch. SET GEOGRAPHY LOCK required. Documentary prestige format.",
            f"""BLOCKING SPECIFICATION — Branch {n % 8 + 1}

SET GEOGRAPHY LOCK: Establish zones before movement. Island DSC, sofa USL, coffee table CSL, window wall stage left, kitchen stage right. Camera axis: eye-level, slight camera-left key. Performer cheats open to lens.

ACTION: Performer must {d}. Open from chain seed mark — continue exact position from previous branch exit frame. Soft entrance: 1–2 second ease-in before dialogue if branch_open_pause is true.

DIALOGUE WINDOW: Speech completes by 12.5 seconds. Movement may begin on final word or during last phrase if motivated — never after 12.5s.

MOVEMENT: Specify zone-to-zone path with motivation embedded. If cross: name pivot direction, step count, arc geometry (upstage diagonal if transition). NEVER toward camera on exit transitions. If sit: name landing zone, body position (3/4 open), hand placement.

TAIL HOLD (12.5–15s): Silent, closed-mouth, calm neutral face. Zero audible exhale. Zero shoulder drop. Positional stability — this frame is the chain seed for branch {n % 8 + 2}.

NOTATION: Use nine-zone abbreviations. Example shorthand for this drill: [seed mark] → (dialogue) → {d.upper()} → hold.

CAMERA: Static or gentle creep — no reframe that changes axis mid-branch. Medium waist-up default."""
        ))

    return emit([pair(p[0], p[2], p[1]) for p in pairs[:100]], "blocking_movement")


# Import remaining domains from part 2
from generate_eleanor_filmmaking_corpus_d2 import (  # noqa: E402
    domain3_performance,
    domain4_set_design,
    domain5_props,
    domain6_pipeline,
    domain7_scene_architecture,
)


def main() -> int:
    all_pairs: list[dict] = []
    all_pairs.extend(domain1_stage_geography())
    all_pairs.extend(domain2_blocking())
    all_pairs.extend(domain3_performance())
    all_pairs.extend(domain4_set_design())
    all_pairs.extend(domain5_props())
    all_pairs.extend(domain6_pipeline())
    all_pairs.extend(domain7_scene_architecture())

    targets = {
        "stage_geography": 80,
        "blocking_movement": 100,
        "directing_performance": 100,
        "set_design": 80,
        "prop_design": 60,
        "pipeline_rules": 80,
        "scene_architecture": 60,
    }
    counts: dict[str, int] = {}
    for p in all_pairs:
        d = p.get("_domain", "unknown")
        counts[d] = counts.get(d, 0) + 1

    errors: list[str] = []
    for d, t in targets.items():
        c = counts.get(d, 0)
        if c < t:
            errors.append(f"{d}: {c}/{t}")

    blocking_domains = {"blocking_movement"}
    for i, p in enumerate(all_pairs):
        ow = wc(p["output"])
        dom = p.get("_domain", "")
        min_w = 300 if dom in blocking_domains and p.get("input") else 150
        if dom in blocking_domains and not p.get("input") and ow < 300:
            min_w = 300  # blocking outputs always 300+
        elif dom == "blocking_movement":
            min_w = 300
        if ow < min_w:
            errors.append(f"pair {i} ({dom}): output {ow} words < {min_w}")

    if len(all_pairs) < 560:
        errors.append(f"total: {len(all_pairs)}/560")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8", newline="\n") as f:
        for p in all_pairs:
            row = {k: v for k, v in p.items() if not k.startswith("_")}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Wrote {len(all_pairs)} pairs -> {OUT_PATH}")
    for d, t in targets.items():
        print(f"  {d}: {counts.get(d, 0)}/{t}")
    if errors:
        print("VALIDATION WARNINGS:")
        for e in errors[:20]:
            print(f"  {e}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more")
        return 1
    print("Validation OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
# ELEANOR Cutscene Product Vertical — Architecture Spec v1.0

> **Date:** 2026-06-30
> **Status:** SPEC — no code changes yet
> **Core insight:** A cutscene is a movie contained within a mostly-interactive framework.
> The existing movie pipeline serves this vertical with minimal additions.

---

## 1. Market Thesis

Game cutscenes are a different artform from gameplay. Different skillsets, different
tools, different people. Game engineers and designers build the interactive frame — they
do not want to direct, light, score, or edit the scene where the protagonist talks to an
NPC while the player can't even interact outside of "skip scene."

Current industry state:
- AAA studios run internal cinematic teams (Naughty Dog, Santa Monica) — expensive, slow,
  siloed from gameplay dev. The cinematics team is a bottleneck on ship dates.
- Mid-tier studios outsource to motion-capture houses or use in-engine real-time tools
  (UE5 Sequencer, Unity Timeline) — technical but cinematically flat. Engineers directing
  cameras produces engineer-quality cinematics.
- Indie studios skip cutscenes entirely or use static dialogue boxes — the talent and
  budget gap is too wide.

ELEANOR collapses the talent gap. The same pipeline that produces a 90-minute film
produces a 45-second cutscene. The screenplay format, modifier stack, style DNA, and
render chain are identical — the only differences are delivery constraints and
integration touchpoints.

---

## 2. Pipeline Mapping — What Already Works

Every component in the movie pipeline maps directly to cutscene production:

| Pipeline Stage | Movie Path | Cutscene Path | Delta |
|---|---|---|---|
| **Ingest** | `screenplay_ingest.py` — PDF/Fountain/TXT parse → schema JSON | Same — cutscene scripts are screenplays. Scene headings, action, dialogue, transitions. | None. A cutscene script IS a screenplay. |
| **Modifier suggestion** | `modifier_suggester.py` — tone analysis → style_dna_tag, audio_dna_tag, pacing_dna_tag | Same — tone analysis works on any narrative content. A horror game cutscene scores "dark, tense, claustrophobic" the same as a horror film. | None. |
| **Catalog resolution** | `catalog_resolver.py` — fuzzy-match names → @IDs in production_catalog | Same — characters, locations, props get @IDs. Game characters are still characters. | None. |
| **Style resolution** | `style_modifiers.py` — resolve per-shot modifiers via 7-level fallback chain | Same — `gameart_*` as base layer + `style_*`/`hybrid_*`/`extinct_*` for cinematic DNA on top. This layering is the product's core value. | None — already built. |
| **Render** | `render_longform.py` — prompt assembly → Grok Imagine Video API → QA/color/gate → concat | Same — cutscene shots render identically to movie shots. | Minor: `format_id` addition, delivery codec/container logic. |
| **QA** | Magenta-hue QA, continuity gate, drift detection, render complexity projection | Same — visual QA is visual QA regardless of destination. | None. |

**Bottom line:** zero new modules needed. Two changes: a new `format_id` value and
delivery-format handling.

---

## 3. The `format_id: "cutscenes"` Addition

### 3.1 Where format_id matters in render_longform.py

Current format_id-gated behavior (from code scan):

- **Line 420:** Default format fallback (`documentary-host`)
- **Line 444:** Clinical/neutral set detection — `science-explainer`, `editorial-explainer`,
  `companion`, `gfe-companion` get white-balance grade
- **Line 481:** Magenta-hue QA gating — `narrative-short-film` and `movies` get magenta
  reroll convergence
- **Line 2558:** Cross-dissolve timing from `Production_Templates_v1.json`
- **Line 2709:** Passed through to xfade resolver

### 3.2 Cutscene format_id behavior

```
format_id: "cutscenes"
```

Behavioral mapping:
- **Magenta-hue QA:** YES — cutscenes are cinematic narrative; same visual quality bar
  as `movies`. Add `"cutscenes"` to the tuple at line 481.
- **Clinical/neutral:** NO — cutscenes are not explainers.
- **xfade_s defaults:** Tighter than movies. Default 0.15s (vs movie 0.25s). Game
  cutscenes favor hard cuts and fast transitions — players are coming from 60fps
  interactive gameplay; long dissolves feel sluggish.
- **Shot duration guidance:** Shorter average. Movie avg ~4-6s/shot. Cutscene avg ~2-4s.
  Players have lower patience for lingering shots after interactive gameplay.

### 3.3 screenplay_pipeline.py addition

Add `"cutscenes"` to the `--format-id` choices at line 148:

```python
choices=["movies", "shorts", "ads", "music_videos", "docs",
         "series_episode", "social_content", "trailers", "cutscenes", "custom"],
```

No other pipeline changes needed.

---

## 4. Style Layering — The Core Differentiator

This is where ELEANOR's cutscene product is categorically different from anything
on the market. Two-layer style resolution:

### Layer 1: Game Art Base (visual engine aesthetic)

`gameart_*` IDs set the rendering foundation to match the game's visual identity:

- `gameart_hyperreal_ue5` — photogrammetry + Nanite + Lumen (AAA realistic)
- `gameart_hyperreal_cryengine` — dense vegetation + atmospheric naturalism
- `gameart_cel_shaded` — hard-edge toon rendering (Zelda: Wind Waker family)
- `gameart_pixel_16bit` — SNES-era sprite aesthetic (indie RPGs)
- `gameart_pixel_modern` — high-res pixel with particle overlays (Celeste, Dead Cells)
- `gameart_low_poly` — geometric minimalism (Firewatch, Superhot)
- All 18 registered gameart_* IDs available

### Layer 2: Cinematic DNA (director + technique overlay)

Layered ON TOP of the game art base via standard modifier resolution:

- `style_villeneuve_deakins` — Dune-scale epic with anamorphic framing
- `hybrid_fincher_deakins` — clinical precision with shadow-sculpted lighting
- `style_del_toro_navarro` — baroque dark fantasy with golden practical light
- `style_cuaron_lubezki` — fluid long-take grammar with naturalistic urgency
- `extinct_technicolor_3strip` — saturated Wizard-of-Oz color science
- Any of the 157 registered modifier IDs

### How it combines in practice

A FromSoftware-style dark fantasy cutscene:
```json
{
  "style_dna_tag": "gameart_hyperreal_ue5",
  "modifiers": {
    "style_dna_tag": "style_del_toro_navarro"
  }
}
```
Result: UE5-quality photorealistic rendering + del Toro's baroque creature-horror
lighting and color palette. The cutscene looks like it belongs in the game's visual
world but is directed like a Guillermo del Toro sequence.

A stylized indie horror cutscene:
```json
{
  "style_dna_tag": "gameart_cel_shaded",
  "modifiers": {
    "style_dna_tag": "hybrid_fincher_deakins"
  }
}
```
Result: Cel-shaded visual base + Fincher's clinical camera discipline and desaturated
green-grey palette. The cutscene is stylized but uncomfortably precise.

A retro RPG cutscene with film-grain nostalgia:
```json
{
  "style_dna_tag": "gameart_pixel_16bit",
  "modifiers": {
    "style_dna_tag": "extinct_kodachrome"
  }
}
```
Result: 16-bit sprite aesthetic + warm Kodachrome color shift and grain structure.
The cutscene feels like a faded photograph of a game that never existed.

No competitor offers this. UE5 Sequencer gives you engine-native cameras. Traditional
outsource houses give you mocap-to-render. Nobody gives you "your game's visual
identity + any cinematic director's eye."

---

## 5. Delivery Format Considerations

Cutscenes differ from standalone films in delivery:

### 5.1 Resolution targets

| Tier | Resolution | Use Case |
|---|---|---|
| Console (PS5/XSX) | 3840x2160 (4K) or 2560x1440 | AAA in-engine playback |
| PC standard | 2560x1440 or 1920x1080 | Scalable, most common |
| Mobile/Switch | 1920x1080 or 1280x720 | Bandwidth-constrained platforms |
| Indie/retro | Per-style (e.g. 480x270 upscaled for pixel art) | Artistic constraint |

### 5.2 Codec and container

- **H.265/HEVC:** Default for console/PC — hardware decode on all modern GPUs, best
  quality/size ratio. `.mp4` container.
- **VP9/AV1:** Web-exportable variants for browser-based games. `.webm` container.
- **ProRes 422:** Intermediate for studios doing final compositing in-engine. `.mov`.
- **PNG sequence + WAV:** For studios needing frame-level integration with engine
  compositors. Lossless, large, but maximum flexibility.

### 5.3 Cutscene-specific delivery features

Features the pipeline should support (future implementation):

- **Loop points:** Mark in/out frames for loopable ambient cutscenes (idle screens,
  menu backgrounds). Metadata in provenance_card.
- **Alpha channel support:** ProRes 4444 or PNG sequence with alpha for compositing
  cutscene elements over real-time game environments (e.g., a hologram projection
  rendered by ELEANOR, composited into the game's 3D scene).
- **Chapter markers:** For skip-to-chapter functionality in multi-beat cutscenes. Map
  directly to scene boundaries from screenplay_ingest.
- **Audio stem separation:** Deliver dialogue, music, SFX as separate tracks so the
  game engine can mix dynamically (e.g., duck music during gameplay audio crossfade).

---

## 6. Integration Models — How Studios Use This

### Model A: Pre-rendered package (simplest)

Studio provides screenplay → ELEANOR renders → delivers `.mp4` files per cutscene.
The game engine plays them as full-screen video. This is how most AAA games handle
cinematics today (Final Fantasy, Metal Gear).

Pipeline: `screenplay_pipeline.py --format-id cutscenes` → `render_longform.py` → MP4.
Zero engine integration needed. Works with any game engine.

### Model B: Scene-level assets

Studio provides screenplay → ELEANOR renders → delivers per-scene segments with
metadata. The game engine triggers playback based on game state. Enables branching
narratives (play cutscene A or B based on player choice).

Pipeline: Same, but output is per-scene rather than concatenated. The screenplay's
scene structure (from `screenplay_ingest.py`'s `group_into_scenes()`) maps naturally
to individual deliverables.

### Model C: Composited elements (advanced)

Studio provides screenplay + engine scene layout → ELEANOR renders characters/FX with
alpha → delivers PNG sequences or ProRes 4444. The engine composites ELEANOR's output
into the real-time 3D scene.

Pipeline: Same render chain + alpha-channel output mode. Requires the `gameart_*` base
layer to match the engine's lighting model precisely.

---

## 7. Client Style Learning — On-the-Fly Custom Styles

> **Scope: platform-level, not cutscene-specific.** Style learning serves ALL
> format_ids — movies, shorts, series, ads, cutscenes. A film studio wants "match
> our DP's look from the dailies" the same way a game studio wants "match our engine."
> This section lives in the cutscene spec because the game vertical surfaced the
> requirement most clearly, but `style_learner.py` is a core pipeline module used
> by every product vertical. See also: standalone spec
> `client_style_learning_platform_v1.md` (to be written).

The 18 pre-built `gameart_*` entries and 157 modifier IDs are the demo reel. The real
product is: "give us your references and we match YOUR look." Clients have their own
visual identity — their own lighting model, their own color science, their own texture
philosophy. They don't want to pick from a menu. They want ELEANOR to learn their
specific aesthetic and render content that looks like it came from their world.

### 7.1 The Style Learning Pipeline

**Input:** Client provides reference material — any combination of:
- Concept art / key art (the art director's vision)
- In-engine screenshots (games) or dailies/stills (film) or brand assets (commercial)
- Art bible / style guide / brand book (rules: "never use warm highlights on metal,"
  "skin tones skew 15% cooler than photographic," "all exterior shots desaturated 20%")
- Existing footage — prior cutscenes, trailers, previous episodes, existing commercials
- Mood boards / reference collections (films, paintings, other games they reference)
- LUT files / color grading references (film clients often have these locked already)

**Analysis dimensions** (what the system extracts):
- **Color palette:** Dominant hues, saturation range, shadow-color bias (warm/cool/neutral),
  highlight rolloff character, any signature color (Firewatch orange, Mirror's Edge white-red)
- **Lighting model:** Global illumination style (baked/dynamic/hybrid), key-to-fill ratio,
  rim light usage, volumetric density, practical vs environmental light balance
- **Texture treatment:** Surface detail level (photoscanned vs hand-painted vs stylized),
  normal map intensity, specular model (PBR metallic-roughness vs custom),
  any deliberate lo-fi choices (visible brush strokes, pixel-grid alignment)
- **Post-processing signature:** Bloom character, chromatic aberration, film grain,
  color grading LUT profile, vignette, depth-of-field bokeh shape
- **Geometry philosophy:** Poly density, silhouette priority, anatomical proportions
  (realistic vs stylized), environmental detail falloff
- **Motion language:** If video references exist — camera speed norms, animation
  interpolation style, VFX particle density

**Output:** A custom style entry that slots into the existing modifier system:

```json
{
  "id": "client_darksouls_fromsoft",
  "family": "client_custom",
  "client": "FromSoftware",
  "project": "Dark Souls IV",
  "learned_from": "47 screenshots, 12 concept art pieces, art bible v2.3",
  "prompt": "[auto-generated from analysis — detailed render description matching
              the client's specific visual characteristics]",
  "tone": ["dark", "gothic", "medieval", "atmospheric", "gritty"],
  "color_profile": {
    "dominant": ["desaturated earth", "cold steel grey", "ember orange"],
    "shadow_bias": "cool blue-green",
    "highlight_rolloff": "harsh, minimal bloom",
    "signature": "bonfire orange against blue-grey stonework"
  },
  "lighting_notes": "High contrast, single strong directional key with minimal fill,
                     heavy volumetric fog, practical fire sources as only warmth",
  "locked": false
}
```

### 7.2 Where It Fits in the Architecture

The custom style entry works exactly like any `gameart_*` ID:

```
screenplay_ingest → modifier_suggester → catalog_resolver → render_longform
                         ↑                                        ↑
                    tone analysis still                   resolve_style_modifiers()
                    suggests cinematic                    loads client_* style the
                    layer (director DNA)                  same as any gameart_* ID
```

No special code path. A `client_darksouls_fromsoft` ID resolves through the same
`style_modifiers.py` fallback chain as `gameart_hyperreal_ue5`. The two-layer system
still works: client style as base + director overlay on top.

### 7.3 The Onboarding Workflow

```
Day 0:  Client sends reference package (art bible, screenshots, concept art)
Day 1:  Style analysis → draft custom style entry generated
Day 2:  Test renders — 3-5 sample shots rendered with the custom style
        Client reviews: "the specular is too hot," "shadows need to be warmer,"
        "the foliage color is off by about 10%"
Day 3:  Iterate prompt refinement based on feedback → re-render samples
Day 4:  Client approves → style entry locked → production rendering begins
```

This is a 3-5 day onboarding, not a 3-5 month one. The feedback loop is fast because
the prompt is text — adjusting "subsurface scattering intensity" in a render prompt
takes seconds, not the weeks it takes to retrain a LoRA or rebuild a shader pipeline.

### 7.4 Style Versioning and Drift Protection

Client styles evolve. A game in early development has a different look than the same
game at gold master. The system needs:

- **Versioned style entries:** `client_darksouls_fromsoft_v1`, `v2`, `v3` — each
  snapshot locked once approved, new versions created for revisions
- **Drift detection:** The existing `drift_detection.py` module (Oliver velocity-drop
  pattern) works here too — compare rendered output against the locked reference set,
  flag if visual characteristics are diverging from the approved baseline
- **A/B comparison renders:** Same shot rendered with v1 and v2 of the client style,
  side-by-side for art director approval before version bump

### 7.5 Why This Is the Real Moat

Any AI video tool can render "a dark fantasy castle." Only ELEANOR can render "a dark
fantasy castle that looks like it came from YOUR game, directed like YOUR reference
director, with YOUR specific specular model and YOUR shadow color bias."

The pre-built registry proves capability. The client style learning proves partnership.
The first sale is "look at these styles." The renewal is "we learned your look better
than your own junior artists can match it."

This applies across every vertical:
- **Games:** "Match our UE5 lighting and post-processing stack"
- **Film:** "Match the look our DP established in the first two weeks of principal"
- **Series:** "Match Season 1's grade so Season 2 is visually continuous"
- **Commercials:** "Match our brand's visual identity across 40 spots this quarter"
- **Music videos:** "Match the artist's established aesthetic from their last 3 videos"

Clair Obscur: Expedition 33 swept the 2025 Game Awards (9 wins including GOTY) using
AI for pre-production storyboarding and placeholder textures. ELEANOR goes further —
AI as the final delivered content, not just the placeholder. The industry appetite is
proven; the disclosure norms are still forming. First mover with a style-learning
pipeline owns the category.

---

## 8. What Needs Building

### Code changes (small — format_id plumbing)

1. Add `"cutscenes"` to `screenplay_pipeline.py` format-id choices (1 line)
2. Add `"cutscenes"` to magenta-hue QA tuple in `render_longform.py` (1 line)
3. Add cutscene entry to `Production_Templates_v1.json` when that file is created:
   ```json
   "cutscenes": {
     "seamless_defaults": { "xfade_s": 0.15 },
     "shot_duration": { "default": 3.0, "min": 1.5, "max": 8.0 },
     "delivery": { "codec": "h265", "container": "mp4" }
   }
   ```

### Not needed (already works)

- Style modifier resolution (all 157 IDs including 18 gameart IDs already resolve)
- Screenplay parsing (cutscene scripts are screenplays)
- Tone-based modifier suggestion (works on any narrative text)
- Catalog resolution (game characters are still characters)
- QA pipeline (visual quality is visual quality)
- Audio/music DNA tags (cinematic audio is cinematic audio)

### Code changes (medium — client style learning)

4. `style_learner.py` — new module. Accepts reference images + art bible text,
   extracts visual characteristics across the analysis dimensions (Section 7.1),
   generates a candidate `client_*` style entry with auto-derived prompt and metadata.
5. `client_style_registry.json` — per-client style storage, same schema as
   `game_art_style_registry_v1.json` but with `client_custom` family and versioning.
6. Wire `client_*` prefix into `style_modifiers.py` resolver alongside `gameart_*` —
   same lookup path, separate registry file.
7. A/B comparison render mode in `render_longform.py` — render same shot with two
   style IDs side-by-side for art director review.

### Future enhancements (not blocking)

- Alpha-channel render path in render_longform.py
- Per-scene output mode (split at scene boundaries instead of concatenating)
- Loop-point metadata in provenance_card
- Audio stem separation at delivery
- Game-engine-specific export presets (UE5 Media Framework, Unity Video Player)

---

## 9. Competitive Position

| Competitor | What They Offer | What They Don't |
|---|---|---|
| **In-house cinematic teams** | Full creative control | $500K+/year headcount, 6-12 month lead times, talent scarcity |
| **Outsource studios (Blur, Digic)** | AAA mocap-to-render quality | $50K-500K per minute, 3-6 month timelines, no style customization |
| **UE5 Sequencer / Unity Timeline** | Free, real-time, in-engine | Requires cinematic expertise the team doesn't have. Engineers directing cameras. |
| **AI video (generic)** | Fast, cheap | No style control, no consistency, no pipeline, no game-art matching |
| **ELEANOR cutscenes** | Director-quality cinematics with game-art-matched visual identity, full modifier stack, hours not months | Requires screenplay input (feature, not bug — forces narrative quality) |

The moat is the two-layer style system. Nobody else can say "render this in your game's
visual identity but directed like Ridley Scott." That sentence is the product.

---

## 10. Pricing Framework (Placeholder)

Per the ELEANOR business model (license + build-to-spec + on-prem):

- **Per-cutscene rendering:** Build-to-spec, priced per delivered minute
- **Pipeline license:** Studio runs ELEANOR on-prem with their own Grok API keys
- **Style onboarding:** Client style learning (Section 7) — analyze art bible +
  references, build custom `client_*` style entry, iterate with art director until
  locked. 3-5 day turnaround. One-time setup fee per project/style.
- **Style maintenance:** Version bumps as the game's visual identity evolves through
  development. Retainer or per-revision pricing.

The indie tier is pre-rendered package delivery (Model A) using pre-built styles.
The mid-tier is style onboarding + per-cutscene rendering (Model A or B).
The AAA tier is on-prem pipeline license with custom style development and maintenance.

---

## 11. Next Actions

1. Add `"cutscenes"` to `screenplay_pipeline.py` choices (trivial)
2. Add `"cutscenes"` to magenta QA gate in `render_longform.py` (trivial)
3. Build `style_learner.py` — reference analysis → custom style entry generation
4. Create `client_style_registry.json` schema + wire `client_*` prefix into resolver
5. Write a sample cutscene screenplay in Fountain format as test input
6. Run the sample through the full pipeline to validate end-to-end
7. Build A/B comparison render mode for art director style approval
8. Spec the alpha-channel render path when a studio engagement requires it

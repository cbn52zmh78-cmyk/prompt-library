# Browser Chat Deliverable — Style Modifier Pipeline Integration

**Date:** 2026-06-30  
**Project:** Grok Projects / DAVID + ELEANOR-DAVID  
**Status:** Implemented and tested

---

## What we built

A **style modifier system** that lets any movie script JSON declare visual and audio “DNA” by ID. When Python runs movie generation (`render_longform.py` or branch-chain runners), the pipeline **reads those IDs from the script** and **injects the matching prompt text** into every Grok Imagine barebones prompt — automatically.

No manual copy-paste of Fincher/Deakins/Anderson paragraphs per shot. The script points at an ID; Python loads the paragraph from the research library.

---

## File map

| Path | Role |
|------|------|
| `DAVID/scripts/style_modifiers.py` | **Resolver** — reads script JSON, looks up IDs, returns prompt clauses |
| `DAVID/scripts/render_longform.py` | **Wired in** — `compile_barebones_prose_prompt()` calls resolver on every shot |
| `DAVID/ELEANOR/research/style_modifier_registry_v1.json` | Master index of all valid IDs |
| `DAVID/ELEANOR/research/director_cinematographer_style_prompts_v1.json` | Live-action `style_*` paragraphs (7 masters) |
| `DAVID/ELEANOR/research/grok_hybrid_styles_camera_innovations_v1.json` | `hybrid_*` blends + camera moves |
| `DAVID/ELEANOR/research/sonic_signatures_grok_audio_v1.json` | `sound_*` audio DNA + chain prompts |
| `DAVID/ELEANOR/research/director_cinematographer_animation_styles_v1.json` | `anim_*` animation transpositions |
| `DAVID/ELEANOR/research/style_modifier_script_schema.md` | Full script schema reference |

Branch runners (`render_branch_chain.py`, `render_branch_chain_black_hole.py`, etc.) inherit this automatically because they call `compile_barebones_prose_prompt` from `render_longform.py`.

---

## How resolution works (priority order)

For each shot, Python walks this list and uses the **first match** for each field:

1. `shots[].modifiers.style_dna_tag` / `audio_dna_tag`
2. `shots[].barebones.style_dna_tag` or `barebones.audio.dna_tag`
3. `shots[].style_dna_tag` (top-level on shot)
4. **`config.style_blocks.b01`** (or `01`, `b02`, etc.) — **B-block level**
5. `script.style.blocks.*` or `script.general_style.blocks.*`
6. `config.branch_chain.blocks.<name>` when shot id is in that block’s `shots[]`
7. `script.general_style.default` or `script.style.default`
8. `config.style_dna_tag` / `config.audio_dna_tag` — production fallback

Block keys are auto-detected from `shot.block`, `shot.block_id`, or the `b01` prefix in `shot.id`.

---

## What gets injected into the Grok prompt

After scene, camera, dialogue, and voice direction are assembled, the resolver appends (when IDs resolve):

| Clause prefix | Source ID type | Example |
|---------------|----------------|---------|
| `STYLE DNA [hybrid_fincher_deakins]:` | `style_*` or `hybrid_*` | Fincher underexposure + Deakins practical light |
| `CAMERA MOVE [Moral Decay Tracking]:` | `hybrid_*` only | Generative camera innovation text |
| `ANIM STYLE [anim_deakins_villeneuve]:` | `anim_*` | Animation technique description |
| `SONIC DNA [sound_deakins]:` | `sound_*` | Environmental audio signature |
| Sonic chain prompt (full sentence) | `sound_*` + extend shot | “Continue from previous audio tail…” |
| `ANTI-GENERIC: tactile film imperfections…` | `anti_generic_armor: true` | Fights overly clean AI look |

Shot-local `barebones.style` still appends **after** DNA clauses (local tweaks on top).

**Silent productions:** When `config.narration: false` or `shot.narration: false`, sonic DNA is skipped (visual DNA still applies).

**Extension / B02 blocks:** Set `block_part: "ext"` or `modifiers.chain_audio: true` on extend shots → sonic **chain_prompt** instead of base description.

---

## Script examples

### Production-wide default

```json
{
  "config": {
    "style_dna_tag": "hybrid_fincher_deakins",
    "audio_dna_tag": "sound_deakins",
    "anti_generic_armor": true
  }
}
```

### Per B-block (manual 5×20s workflow)

```json
{
  "config": {
    "style_dna_tag": "hybrid_fincher_deakins",
    "style_blocks": {
      "b01": {
        "style_dna_tag": "style_anderson_yeoman",
        "audio_dna_tag": "sound_anderson_yeoman"
      },
      "b02": {
        "style_dna_tag": "hybrid_storaro_cuaron",
        "audio_dna_tag": "sound_cuaron_lubezki"
      }
    }
  },
  "shots": [
    { "id": "b01_entrance", "block": "b01", "barebones": { "scene": "...", "camera": "..." } },
    { "id": "b01_entrance_ext", "block": "b01", "block_part": "ext", "barebones": { "scene": "..." } }
  ]
}
```

### Per-shot override

```json
{
  "shots": [{
    "id": "b05_transition",
    "modifiers": {
      "style_dna_tag": "hybrid_coppola_lubezki",
      "audio_dna_tag": "sound_coppola_willis",
      "chain_audio": true
    }
  }]
}
```

### General style block (alternative to config)

```json
{
  "general_style": {
    "default": {
      "style_dna_tag": "style_fincher_khondji",
      "audio_dna_tag": "sound_fincher_khondji"
    },
    "blocks": {
      "b03": { "style_dna_tag": "style_bergman_nykvist" }
    }
  }
}
```

---

## Valid ID quick list

**Visual live-action:** `style_fincher_khondji`, `style_anderson_yeoman`, `style_coppola_willis`, `style_deakins_villeneuve`, `style_bergman_nykvist`, `style_bertolucci_storaro`, `style_cuaron_lubezki`

**Hybrids:** `hybrid_fincher_deakins`, `hybrid_anderson_storaro`, `hybrid_coppola_lubezki`, `hybrid_deakins_bergman`, `hybrid_storaro_cuaron`, `hybrid_fincher_anderson_deakins`, `hybrid_omniscient_evolution`

**Audio:** `sound_fincher_khondji`, `sound_anderson_yeoman`, `sound_coppola_willis`, `sound_deakins`, `sound_bergman_nykvist`, `sound_storaro_bertolucci`, `sound_cuaron_lubezki`

**Animation:** `anim_fincher_khondji`, … (parallel `anim_*` set)

Full index: `style_modifier_registry_v1.json`

---

## Runtime behavior

1. Operator runs: `python render_longform.py longform_scripts/my_movie_script.json` (or branch-chain equivalent).
2. `normalize_script()` loads JSON; preserves `style` and `general_style` top-level keys.
3. For each shot API call, `compile_barebones_prose_prompt()` runs.
4. `style_modifiers.resolve_style_modifiers()` loads research JSON (cached) and resolves IDs.
5. Clauses append to prompt string sent to Grok Imagine.
6. Log line emitted:
   ```
   [style_dna] b01_intro: visual=hybrid_fincher_deakins audio=sound_deakins anim=- sources={...}
   ```

**Backward compatible:** Scripts with no style IDs behave exactly as before (Matilda template, shot-local style only).

---

## Research library context (what the IDs point to)

Four Grok Heavy research passes saved as machine-readable JSON:

1. **7 director–DP visual signatures** (Fincher, Anderson, Coppola, Deakins, Bergman, Storaro, Cuarón)
2. **7 animation transpositions** of those signatures
3. **7 Grok-native hybrids** + revolutionary camera moves + Imagine prompting hacks
4. **7 sonic signatures** + blended sound bible + chaining rules for native AV

The code does **not** re-train the LLM — it **injects** this library at render time. Same library can feed ELEANOR R3 corpus separately.

---

## What is NOT wired yet (future)

- Python auto-select best-of-3 variations per block
- Post-stitch EQ/volume automation for evolving soundscapes
- Emotion-driven auto-tag injection (`read scene emotion → pick hybrid_*`)
- `style_dna_tag` in manual stitch-only workflow (stitch script ignores prompts today)

---

## Director Persona + Pacing (v2)

```json
{
  "config": {
    "director_persona_id": "director_symmetrical_commercialist",
    "native_av": true,
    "pacing_blocks": {
      "b01": { "pacing_dna_tag": "pacing_slow_build_setup" },
      "b05": { "pacing_dna_tag": "pacing_fincher_tension_accel" }
    }
  }
}
```

**Synthetic directors:** `director_cold_immersive_poet`, `director_symmetrical_commercialist`, `director_operatic_shadow`, `director_precision_natural_decay`, `director_grok_omniscient`

**Injected clauses:** `DIRECTOR PERSONA`, `PERFORMANCE`, `PACING DNA`, `EDITING`, `STYLE DNA`, `SONIC DNA`, extend `block_continue`

**Post-stitch:** `python DAVID/scripts/stitch_audio_polish.py stitched.mp4`

---

## One-paragraph summary for chat

> We integrated a style modifier resolver (`style_modifiers.py`) into the DAVID movie pipeline. Scripts now declare visual/audio DNA by ID (`style_*`, `hybrid_*`, `sound_*`) in `config.style_blocks.b01`, `config.style_dna_tag`, or per-shot `modifiers`. On every `render_longform.py` run, those IDs load paragraphs from `DAVID/ELEANOR/research/*.json` and inject into Grok Imagine prompts as `STYLE DNA`, `CAMERA MOVE`, and `SONIC DNA` clauses. B-block extensions use `block_part: "ext"` for sonic chain prompts. Existing scripts unchanged if no IDs set. Research library covers 7 cinema masters, 7 animation styles, 7 hybrids, and 7 sonic signatures from Grok Heavy research.
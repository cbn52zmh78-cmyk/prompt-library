# Style Modifier Script Schema

Inject visual/audio DNA from `DAVID/ELEANOR/research/*.json` via IDs in script JSON.
Resolved in `DAVID/scripts/style_modifiers.py` during `render_longform.py` prompt compile.

## Production default (director persona — preferred)

```json
{
  "config": {
    "director_persona_id": "director_symmetrical_commercialist",
    "native_av": true,
    "anti_generic_armor": true,
    "pacing_blocks": {
      "b01": { "pacing_dna_tag": "pacing_slow_build_setup" },
      "b03": { "pacing_dna_tag": "pacing_mid_tempo_dialogue" },
      "b05": { "pacing_dna_tag": "pacing_fincher_tension_accel" }
    }
  }
}
```

Persona expands to `style_dna_tag`, `audio_dna_tag`, `pacing_dna_tag`, performance, editing, and chain prompts.

## Atomic modifiers (without persona)

```json
{
  "config": {
    "style_dna_tag": "hybrid_fincher_deakins",
    "audio_dna_tag": "sound_deakins",
    "pacing_dna_tag": "pacing_murch_subtractive",
    "native_av": true
  }
}
```

**Director IDs:** `director_cold_immersive_poet`, `director_symmetrical_commercialist`, `director_operatic_shadow`, `director_precision_natural_decay`, `director_grok_omniscient`  
**Pacing IDs:** `pacing_*` (7 signatures)  
**Audio IDs (Tier A aesthetic):** `sound_fincher_khondji`, `sound_anderson_yeoman`, `sound_coppola_willis`, `sound_deakins` (Lievsay sparse), `sound_bergman_nykvist`, `sound_storaro_bertolucci`, `sound_cuaron_lubezki`, `sound_blended_7masters`  
**Audio IDs (Tier B designer craft):** `sound_burtt_inventive`, `sound_king_nolan`, `sound_reznor_ross`, `sound_gudnadottir_dread`, `sound_rydstrom_emotional`, `sound_davis_matrix`  
**Combos:** `sound_combo_deakins_fincher`, `sound_combo_fincher_reznor`, `sound_combo_king_reznor`, `sound_combo_murch_gudnadottir`, `sound_combo_burtt_davis`  
**Beat picker:** `emotional_beat` on shot/block + `config.audio_beat_picker: true` → maps via `emotional_beat_map` in sonic JSON (Randy Thom)  
**Post-stitch:** `python DAVID/scripts/stitch_audio_polish.py stitched.mp4`

## Per-block (B01, B02, …) — `config.style_blocks`

```json
{
  "config": {
    "style_blocks": {
      "b01": {
        "style_dna_tag": "style_anderson_yeoman",
        "audio_dna_tag": "sound_anderson_yeoman"
      },
      "b02": {
        "style_dna_tag": "hybrid_storaro_cuaron",
        "audio_dna_tag": "sound_cuaron_lubezki"
      },
      "01": { "style_dna_tag": "style_deakins_villeneuve" }
    }
  },
  "shots": [
    { "id": "b01_intro", "block": "b01", "barebones": { "scene": "..." } },
    { "id": "b01_intro_ext", "block": "b01", "block_part": "ext", "barebones": { "scene": "..." } }
  ]
}
```

Block key auto-detected from `shot.block`, `shot.block_id`, or `b01` prefix in `shot.id`.

## General style block (script-level)

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

## Per-shot override

```json
{
  "shots": [{
    "id": "b05_transition",
    "emotional_beat": "revelation",
    "modifiers": {
      "style_dna_tag": "hybrid_coppola_lubezki",
      "chain_audio": true,
      "anti_generic_armor": true
    }
  }]
}
```

`emotional_beat: "revelation"` auto-selects `sound_coppola_willis` unless `audio_dna_tag` is set explicitly on the shot.

## Beat-first audio (Randy Thom)

```json
{
  "config": {
    "audio_beat_picker": true,
    "style_blocks": {
      "b01": { "emotional_beat": "setup" },
      "b03": { "emotional_beat": "tension", "audio_dna_combo": "sound_combo_fincher_reznor" },
      "b05": { "emotional_beat": "sci_fi_combat" }
    }
  }
}
```

Beat keys: `setup`, `dialogue`, `tension`, `dread`, `silence`, `action`, `sci_fi`, `creature`, `reality_bend`, etc. — see `emotional_beat_map` in `sonic_signatures_grok_audio_v1.json`.

## Branch-chain named blocks

```json
{
  "config": {
    "branch_chain": {
      "blocks": {
        "kitchen": {
          "shots": ["b01_intro", "b02_company"],
          "style_dna_tag": "style_anderson_yeoman"
        }
      }
    }
  }
}
```

## Grade family (style-aware color QA)

A style is an intentional departure from clinical-neutral, so the color-cast QA /
correction (`color_cast_qa.py`, `render_longform.py` cast-gate) must judge a frame
against the **style's** target look — not neutral — or it scrubs the look back out
(Fincher green/inky reads as a yellow-green + blue-starvation breach; Anderson warm
pastel reads as a warm cast). Each shot carries a `grade_family` that selects the
QA band. Families are defined in `color_cast_qa.py` → `GRADE_FAMILIES`:
`clinical_neutral` (default), `warm_pastel`, `warm_gold`, `desaturated_cool`,
`noir`, `teal_orange`, `high_key`.

Resolution precedence (scene overrides movie): explicit `grade_family` on a
branch-chain block or shot → `style_dna_tag`/`director_persona_id` mapped via
`color_cast_qa.STYLE_GRADE_FAMILY` → movie `config.grade_family` → movie style /
persona tag → `clinical_neutral`. Set it directly to bypass the map:

```json
{ "config": { "grade_family": "desaturated_cool",
              "branch_chain": { "blocks": { "kitchen": { "grade_family": "warm_pastel" } } } } }
```

`STYLE_GRADE_FAMILY` is seeded for `style_fincher_khondji`→`desaturated_cool` and
`style_anderson_yeoman`→`warm_pastel`; extend it as production tags
(`hybrid_*`, `director_*`) are classified. Unmapped tags → `clinical_neutral`
(no behavior change). Authoritative per-shot stamping — including branch-chain
block → shot mapping and persona expansion — belongs in `style_modifiers.py`
alongside the existing DNA resolution; `render_longform` consumes `shot["grade_family"]`.

## Valid IDs

See `style_modifier_registry_v1.json` → `id_index` (`style_*`, `hybrid_*`, `sound_*`, `anim_*`).

## Extension / chain audio

Set `block_part: "ext"` or `modifiers.chain_audio: true` on extend shots to inject sonic `chain_prompt` instead of base description.
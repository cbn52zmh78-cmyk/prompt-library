# Pass 6 — Editing & Pacing Mastery v1

**Source:** Grok Heavy research (2026-06-30)  
**Machine-readable:** `pacing_signatures_v1.json`  
**Wired:** `pacing_dna_tag` in `style_modifiers.py` (prompt-only); FFmpeg polish in `stitch_audio_polish.py` (deferred stub)

## Editor anchors

- **Thelma Schoonmaker** — effortless momentum, music-like phrasing
- **Walter Murch** — Rule of Six; subtractive editing; sound = picture
- **Michael Kahn** — stillness as deliberate as action

## Block pacing tags (`pacing_*`)

| ID | Role |
|----|------|
| `pacing_slow_build_setup` | B01 / opening |
| `pacing_mid_tempo_dialogue` | Host dialogue blocks |
| `pacing_schoonmaker_momentum` | Energetic general |
| `pacing_murch_subtractive` | Psychological / intimate |
| `pacing_fincher_tension_accel` | Climax build |
| `pacing_lubezki_long_take_flow` | Immersive oner feel |
| `pacing_invisible_jcut` | Stitch-edge optimization |

## Script usage

```json
{
  "config": {
    "pacing_blocks": {
      "b01": { "pacing_dna_tag": "pacing_slow_build_setup" },
      "b03": { "pacing_dna_tag": "pacing_mid_tempo_dialogue" },
      "b05": { "pacing_dna_tag": "pacing_fincher_tension_accel" }
    }
  }
}
```

Or inherit from `director_persona_id` default `pacing_dna_tag`.

## Block-level generation add-on

```
Edit and pace this 15-second block like Thelma Schoonmaker + Walter Murch: intentional rhythm, natural dialogue flow with realistic pauses and tone shifts, seamless match to attached previous final frame and audio tail.
```

## Post-stitch (deferred)

`python stitch_audio_polish.py stitched.mp4` — light audio crossfade/EQ between xfade joins when rhythm gaps appear in review.
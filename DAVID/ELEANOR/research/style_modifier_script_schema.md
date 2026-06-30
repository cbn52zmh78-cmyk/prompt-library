# Style Modifier Script Schema

Inject visual/audio DNA from `DAVID/ELEANOR/research/*.json` via IDs in script JSON.
Resolved in `DAVID/scripts/style_modifiers.py` during `render_longform.py` prompt compile.

## Production default

```json
{
  "config": {
    "style_dna_tag": "hybrid_fincher_deakins",
    "audio_dna_tag": "sound_deakins",
    "anti_generic_armor": true
  }
}
```

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
    "modifiers": {
      "style_dna_tag": "hybrid_coppola_lubezki",
      "audio_dna_tag": "sound_coppola_willis",
      "chain_audio": true,
      "anti_generic_armor": true
    }
  }]
}
```

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

## Valid IDs

See `style_modifier_registry_v1.json` → `id_index` (`style_*`, `hybrid_*`, `sound_*`, `anim_*`).

## Extension / chain audio

Set `block_part: "ext"` or `modifiers.chain_audio: true` on extend shots to inject sonic `chain_prompt` instead of base description.
# Sonic Signatures & Grok Native Audio v2

**Source:** Grok Heavy browser research + Claude POUS cinematic sound design deep research v1  
**Scope:** Tier A aesthetic poles (7 visual masters) + Tier B designer craft tags + combos + beat-first picker  
**Engine:** Grok Imagine / Aurora — synchronized audio in-pass (dialogue, lip-sync, SFX, ambient, music)  
**Pairs with:** `cinematic_sound_design_deep_research_v1.md`, `style_modifier_registry_v1.json`

---

## Architecture

| Tier | IDs | Purpose |
|------|-----|---------|
| **A** | `sound_fincher_khondji` … `sound_cuaron_lubezki`, `sound_blended_7masters` | Visual-aligned aesthetic poles |
| **B** | `sound_burtt_inventive`, `sound_king_nolan`, `sound_reznor_ross`, `sound_gudnadottir_dread`, `sound_rydstrom_emotional`, `sound_davis_matrix` | Designer-anchored craft (decoupled from cinematography) |
| **Combos** | `sound_combo_*` | Layer two tags for production stacks |

**`sound_deakins` fix:** ID unchanged for backward compatibility; anchor is **Skip Lievsay** sparse minimalism (not environmental immersion). Name: Deakins/Lievsay Sonic.

---

## Tier A — Aesthetic poles

### `sound_fincher_khondji` (Ren Klyce)
Clinical foley, sub-threshold drones, subtractive silence drops, relentless mechanical ambience.

### `sound_anderson_yeoman`
Whimsical symmetrical foley, ticking motifs, sparse 3–5 layer mixes.

### `sound_coppola_willis` (Walter Murch)
Worldized reflections, operatic shadows, meta-diegetic psychological ambience.

### `sound_deakins` (Skip Lievsay)
Sound-design haiku — deliberate silence, diegetic commitment, environmental breathing.

### `sound_bergman_nykvist`
Intimate near-silence, voice as close-up, meta-diegetic micro-sounds.

### `sound_storaro_bertolucci`
Symbolic warm/cool tonal shifts mirroring color psychology.

### `sound_cuaron_lubezki`
Fluid spatial immersion, object-based placement, lived-in dialogue.

### `sound_blended_7masters`
Synthesis of all seven Tier A poles — default for `director_grok_omniscient`.

---

## Tier B — Designer craft

### `sound_burtt_inventive` (Ben Burtt)
Found-object textures, Doppler shifts, iconic manufactured SFX.

### `sound_king_nolan` (Richard King)
Character-POV filtering, seismic sub-bass, vacuum silence, Shepard tone dread.

### `sound_reznor_ross` (Trent Reznor & Atticus Ross)
Score-as-sound-design, electronic-orchestral hybrid, beautiful-to-sinister ambiguity.

### `sound_gudnadottir_dread` (Hildur Gudnadottir)
Single-source halldorophone/industrial drones, sustained dread without melody.

### `sound_rydstrom_emotional` (Gary Rydstrom)
Animal composite layering, contrast-before-scale, body-interior POV terror.

### `sound_davis_matrix` (Dane Davis)
Multi-temporal layers, 30+ composite impacts, digital-organic inversion.

---

## Combos

| ID | Stack |
|----|-------|
| `sound_combo_deakins_fincher` | Lievsay sparse + Klyce precision |
| `sound_combo_fincher_reznor` | Klyce effects + Reznor/Ross score texture |
| `sound_combo_king_reznor` | King/Nolan POV + Reznor/Ross texture |
| `sound_combo_murch_gudnadottir` | Murch worldized layers + Gudnadottir dread |
| `sound_combo_burtt_davis` | Burtt invention + Davis time-rate manipulation |

---

## Beat-first picker (Randy Thom)

Set `emotional_beat` on shot or block. When `audio_dna_tag` is not explicitly set on the shot, `style_modifiers.py` resolves audio from `emotional_beat_map` in the JSON registry.

```json
{
  "config": { "audio_beat_picker": true },
  "shots": [{
    "id": "b03_climax",
    "emotional_beat": "action",
    "block_part": "ext"
  }]
}
```

Example beats: `setup`, `tension`, `dread`, `silence`, `action`, `sci_fi`, `creature`, `reality_bend`, `score_texture`.

Combo beats: `tension_score`, `nolan_epic`, `psychological_dread`, `sci_fi_combat`.

---

## Chaining rule

```
Continue from the attached previous audio tail + final video frame for perfect sync and evolution.
```

Set `block_part: "ext"` or `modifiers.chain_audio: true` on extend shots.

---

## Script fields

| Field | Purpose |
|-------|---------|
| `config.audio_dna_tag` | Production default |
| `config.audio_dna_combo` | Layered combo |
| `config.audio_beat_picker` | Infer beat from `shot.beat` / `barebones.beat` |
| `shots[].emotional_beat` | Beat-first audio override |
| `shots[].barebones.audio.dna_tag` | Per-block explicit audio |

---

## Technique taxonomy

Embedded in JSON `technique_taxonomy` and appended to prompt clauses via each tag's `techniques` array. Categories: spatial, mix philosophy, source recording, time/perception, structural (diegetic, stinger, riser, etc.).

---

## Randy Thom (meta — not a tag)

Philosophy wired into `generate_corpus.py` → `sound_conscious_writing` domain and beat picker. Thom informs **how scripts are written**, not a texture injection.
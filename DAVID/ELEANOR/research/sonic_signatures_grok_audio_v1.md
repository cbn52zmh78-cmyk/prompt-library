# Sonic Signatures & Grok Native Audio v1

**Source:** Grok Heavy browser research (user capture, 2026-06-30)  
**Scope:** Cinema sound design legends → seven sonic DNA tags (1:1 with visual masters) + chaining prompts for sequential B-block pipeline.  
**Engine note:** Grok Imagine / Aurora generates **synchronized audio in-pass** (dialogue + lip-sync, SFX, ambient, music) — not post-muxed unless stitching polish requires it.  
**Pairs with:**
- `director_cinematographer_style_prompts_v1.md`
- `grok_hybrid_styles_camera_innovations_v1.md`

---

## Sound designer reference (visual-master equivalents)

| Designer | Association | Signature |
|----------|-------------|-----------|
| Walter Murch | Coppola | Sound = picture; worldizing; subtractive mix; inner psychology through layers |
| Ren Klyce | Fincher | Clinical precision; unsettling ambiences; hyper-real psychological foley |
| Gary Rydstrom | Spielberg/Lucas | Organic creation; emotional realism |
| Ben Burtt | Lucas | Iconic invented sounds from found objects |
| Skip Lievsay | Coens / Deakins films | Sparse, impactful; silence and environment breathe |
| Anna Behlmer | (mixed catalog) | — cited in source as part of deep dive |

---

## Chaining rule (all blocks)

Always reference prior pass tail:

```
Continue from the attached previous audio tail + final video frame for perfect sync and evolution.
```

Python: pass `audio_tail_ref` + `last_frame_ref` into next B-block prompt assembly.

---

## Seven sonic signatures

### 1. Fincher/Khondji — `sound_fincher_khondji`

Precise, cold, layered dread (Klyce-style). Clinical foley; low-frequency hums; subtractive mix where ambient suddenly drops.

**Chaining prompt:**
```
Continue from previous audio tail + attached final frame. Fincher/Khondji sonic: hyper-precise foley with subtle digital glitches in the silence, cold metallic echoes, desaturated ambience that feels calculated and unresolved. Evolve tension organically.
```

---

### 2. Anderson/Yeoman — `sound_anderson_yeoman`

Whimsical precision, symmetrical sound design. Ticking metronome motifs; curated quirky foley; balanced musical stings.

**Chaining prompt:**
```
Maintain whimsical precision from previous audio, add symmetrical sound motifs that match visual symmetry on the reference frame.
```

---

### 3. Coppola/Willis — `sound_coppola_willis`

Operatic, shadow-like layers. Deep rumbling bass; warm intimate dialogue; echoing silences; selective reveal like chiaroscuro.

**Chaining prompt:**
```
Evolve from previous audio with inherited shadows in the soundscape — warm tones fading into deep rumbling power.
```

---

### 4. Deakins — `sound_deakins`

Hyper-real environmental immersion. Practical location foley; volumetric wind/haze; space breathes naturally.

**Chaining prompt:**
```
Continue Deakins-style practical ambient from previous tail, match lighting/environment on reference frame with authentic location textures.
```

---

### 5. Bergman/Nykvist — `sound_bergman_nykvist`

Intimate psychological minimalism. Soft breaths, ticking clocks, distant bells; near-silence; voice as emotional close-up.

**Chaining prompt:**
```
Intimate Nykvist sonic continuation — minimal layers focused on voice and micro-sounds that reveal inner state, reference the final frame face lighting.
```

---

### 6. Storaro/Bertolucci — `sound_storaro_bertolucci`

Symbolic color-equivalent audio. Warm/cool tonal shifts; dramatic swells mirroring color psychology; sensual layered textures.

**Chaining prompt:**
```
Storaro sonic evolution — color palette of sound shifts psychologically from previous block's tail.
```

---

### 7. Cuarón/Lubezki — `sound_cuaron_lubezki`

Immersive fluid experiential layers. Organic spatial audio; natural wind/particle sounds; lived-in dialogue.

**Chaining prompt:**
```
Seamless Lubezki audio continuation — fluid spatial layers that feel like one long experiential take from the reference frame.
```

---

## Master blended sound bible (template)

```
Full cinematic audio design synthesizing the 7 masters: precise clinical foley and psychological undercurrents (Fincher/Klyce), whimsical balanced motifs (Anderson), operatic shadow layers (Coppola/Murch), hyper-real practical environmental textures (Deakins), intimate minimal soul sounds (Bergman), symbolic emotional tonal shifts (Storaro), and immersive unbroken experiential flow (Cuarón). Generate synchronized dialogue with natural lip-sync performance, organic SFX, evolving ambience, and subtle score that reacts to visual style. Continue perfectly from previous audio tail and attached video frame.
```

---

## Pipeline integration (coding targets)

### Script JSON fields (proposed)

```json
{
  "config": {
    "style_dna_tag": "hybrid_fincher_deakins",
    "audio_dna_tag": "sound_fincher_khondji",
    "audio_chain_mode": "tail_plus_frame"
  },
  "shots": [{
    "id": "b02_block01_ext",
    "barebones": {
      "audio": {
        "dna_tag": "sound_deakins",
        "chain_prompt": "...",
        "ambient": "AUDIO LOCK or native AV directive"
      }
    }
  }]
}
```

### Python prompt assembly

| Step | Action |
|------|--------|
| 1 | Read `style_dna_tag` + `audio_dna_tag` per block from script |
| 2 | Load sonic signature from `sonic_signatures_grok_audio_v1.json` |
| 3 | Append `chain_prompt` when `block_index > 0` |
| 4 | Attach `last_frame` + optional `audio_tail` reference paths |
| 5 | Single API call — native AV when dialogue required |

### Post-stitch polish

Light EQ / volume automation across xfade joins so evolving soundscapes read as one sound auteur.

### Modifier registry (save alongside visual)

```
DAVID/ELEANOR/research/style_modifier_registry_v1.json  ← unified style + audio + hybrid IDs
```

---

## Arc suggestion (from source)

Start clean/commercial (MATILDA lifestyle) → evolve toward dark/immersive across sequential blocks via shifting `audio_dna_tag` + `style_dna_tag`.
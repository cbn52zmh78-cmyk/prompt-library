# Director–Cinematographer Visual Style Prompts v1

**Source:** Grok Heavy browser research (user capture, 2026-06-30)  
**Scope:** ELEANOR-DAVID / Studio visual style library — **visuals only** (lighting, color, composition, texture, camera feel). No scene blocking or actor direction.  
**Use:** Copy-paste into `style` blocks, shot lists, production bibles, Grok Imagine prompts, or R3 LLM filmmaking corpus.

---

## Usage

Each entry is a **standalone paragraph** — one director–DP pair, one signature look. Pick one per shot or episode; do not mix unless intentionally blending (see Combined slot below).

| ID | Pair | Reference work |
|----|------|----------------|
| `style_fincher_khondji` | David Fincher & Darius Khondji | *Seven* |
| `style_anderson_yeoman` | Wes Anderson & Robert Yeoman | *The Grand Budapest Hotel* |
| `style_coppola_willis` | Francis Ford Coppola & Gordon Willis | *The Godfather* |
| `style_deakins_villeneuve` | Roger Deakins (with Denis Villeneuve) | *Blade Runner 2049* |
| `style_bergman_nykvist` | Ingmar Bergman & Sven Nykvist | *Cries and Whispers* / *Persona* |
| `style_bertolucci_storaro` | Bernardo Bertolucci & Vittorio Storaro | *The Conformist* |
| `style_cuaron_lubezki` | Alfonso Cuarón & Emmanuel Lubezki | *Children of Men* |

---

## 1. Fincher & Khondji (*Seven*)

```
Cinematic visual style in the vein of Fincher and Khondji: extreme underexposure on interiors creating inky blacks and high contrast, desaturated palette with sickly green and warm gold accents, practical overhead fluorescents and motivated light piercing from outside through wet reflective surfaces, bleach-bypass texture and deep velvety shadows, precise geometric framing and rule-of-thirds tension, rain-slicked oppressive urban grit with 'dark clarity' where every highlight and reflection feels sinister and meticulously controlled.
```

---

## 2. Anderson & Yeoman (*The Grand Budapest Hotel*)

```
Cinematic visual style in the vein of Anderson and Yeoman: hyper-symmetrical centered compositions and dollhouse-perfect tableaux, vibrant yet meticulously curated pastel color palettes, deep focus that reveals every intricate prop and set detail, flat theatrical lighting that flatters the whimsical architecture and costumes, balanced anamorphic or boxed framing with whip pans and tracking that feels like a perfectly staged play, whimsical precision and theatrical elegance in every frame.
```

---

## 3. Coppola & Willis (*The Godfather*)

```
Cinematic visual style in the vein of Coppola and Willis: low-key chiaroscuro 'Prince of Darkness' lighting with heavy selective shadows and silhouettes, motivated practical top and side lights that often obscure faces or eyes, warm sepia and earthy tones contrasting deep blacks, geometric Renaissance-inspired compositions, controlled underexposure that builds operatic power dynamics and intimate family menace through masterful light and shadow play.
```

---

## 4. Deakins & Villeneuve (*Blade Runner 2049*)

```
Cinematic visual style in the vein of Deakins: masterful naturalistic and practical lighting with volumetric haze, smoke, dust, and rain sculpting forms, elegant silhouettes and deep-focus geometry, subtle yet innovative color palettes that feel lived-in and atmospheric, precise clean compositions (frames within frames, negative space mastery), vast minimalist grandeur blended with intimate human-scale detail, story-serving elegance and environmental authenticity.
```

---

## 5. Bergman & Nykvist (*Cries and Whispers* / *Persona*)

```
Cinematic visual style in the vein of Bergman and Nykvist: poetic naturalism and luminous simplicity, soft diffused window or single-source practical light sculpting expressive human faces in intimate close-ups, stark yet restrained chiaroscuro, symbolic color restraint (dominant rich reds or cool minimalism), minimalist elegant compositions focused on psychological and emotional truth, profound intimacy through light that feels honest and soul-revealing.
```

---

## 6. Bertolucci & Storaro (*The Conformist*)

```
Cinematic visual style in the vein of Bertolucci and Storaro: bold expressive color theory and psychological symbolism (warm/cool contrasts, Goethe-inspired duality), painterly dramatic lighting with sculpted shafts, atmospheric haze, and rich volumetric depth, operatic widescreen compositions where light and saturated palettes actively convey inner emotion and ideology, sensual yet precise architectural framing and textural elegance.
```

---

## 7. Cuarón & Lubezki (*Children of Men*)

```
Cinematic visual style in the vein of Cuarón and Lubezki: immersive naturalistic and available-light mastery, wide lenses creating visceral presence and spatial depth, fluid long-take dynamism with organic handheld or Steadicam flow, lens flares and hyper-real textures, documentary-like realism blended with poetic environmental immersion, minimal artificial intervention that makes every frame feel lived-in, chaotic, and emotionally immediate.
```

---

## Combined (placeholder)

The source research referenced a **synthesis of all seven** into one blended style block for experimentation. That combined paragraph was **not included** in the captured paste — add here when available.

---

## Studio cross-reference

- MATILDA default grade in `Studio/prompts/MASTER_Matilda_v1.json` is **Fincher institutional daytime** — closest to `style_fincher_khondji` but corporate/neutral, not *Seven* noir.
- Pure astrophysics pieces use Jantzen/NASA grading — not this library.
- For manual Grok shots: append chosen `style_*` paragraph to the `GRADE:` / `style` clause; keep blocking and `@` slots separate.
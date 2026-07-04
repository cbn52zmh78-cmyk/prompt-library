# Cinematic Sound Design — Deep Research Pass v1

**Date:** 2026-06-29  
**Implemented:** 2026-06-29 (v3 sonic expansion — all phases)  
**Purpose:** Foundational reference for the ELEANOR-DAVID sonic DNA system (`sound_*` tags in `style_modifier_registry_v1.json`). Profiles legendary practitioners, catalogs techniques with prompt-actionable language, and identifies expansion opportunities beyond the current 7+1 tag set.  
**Pairs with:** `sonic_signatures_grok_audio_v1.json`, `style_modifier_registry_v1.json`  
**Status:** Tier B tags, combos, technique taxonomy, emotional_beat_map, and beat picker wired in `style_modifiers.py`. Thom principles in `generate_corpus.py` → `sound_conscious_writing`.

---

## I. Sound Designer Profiles

### Walter Murch — The Philosopher

**Association:** Francis Ford Coppola (Apocalypse Now, The Conversation, The Godfather trilogy)  
**Oscars:** 3 (sound editing + film editing)  
**Philosophy:** "Dense Clarity / Clear Density" — a mix should either have many elements organized so clearly that each is perceptible, or few elements layered so densely they fuse into one emotional texture. Never muddy middle ground.

**Signature techniques:**
- **Worldizing** — Murch coined this term. Record a finished sound through speakers placed in a real acoustic space, then re-record the room's natural reverb and reflections. The result carries spatial truth that no reverb plugin replicates. He played back helicopter sounds through a speaker in a bathroom for Apocalypse Now's attack sequence.
- **Subtractive mixing** — removing layers at critical moments so a single surviving sound carries disproportionate weight. The sudden absence of ambience is itself a sound event.
- **Sound-as-picture parity** — Murch treats the sound edit with the same compositional rigor as the visual edit. He argues sound should be designed at the script stage, not applied cosmetically in post.
- **Inner psychological layers** — sounds that represent internal states rather than physical sources. In The Conversation, the ambient hum isn't room tone — it's Harry Caul's paranoia made audible.

**Prompt DNA:** subtractive silence drops, worldized room reflections, psychological ambience that shifts with character interiority, dense-clarity layering

**Current mapping:** `sound_coppola_willis` (designer_anchor: Walter Murch)

---

### Ben Burtt — The Inventor

**Association:** George Lucas (Star Wars, Indiana Jones, WALL-E)  
**Oscars:** 4 (special achievement + sound editing)  
**Philosophy:** Every iconic sound starts with a real-world recording, then gets sculpted. Never pure synthesis — always an organic seed.

**Signature techniques:**
- **Found-object recording** — the lightsaber hum is an idling 35mm film projector motor combined with TV set interference picked up by a broken microphone cable. The blaster is a guy-wire being struck on a radio tower.
- **Doppler manipulation** — recording sounds while moving the source past the microphone (or vice versa) to capture natural pitch shifts. The TIE fighter shriek is an elephant call Doppler-shifted.
- **Organic-synthetic blending** — starting from animal, mechanical, or environmental recordings, then processing through pitch-shift, time-stretch, and layering to create sounds that feel *alive* but don't exist in nature.
- **Character voice through sound** — WALL-E's "voice" is almost entirely sound design, not traditional voice acting. Every motor whir and beep conveys emotion through carefully shaped mechanical sounds.

**Prompt DNA:** found-object organic textures, Doppler pitch shifts on mechanical elements, creature voices built from animal + machine composites, handcrafted iconic sound events

**Current mapping:** Not directly anchored. Closest: `sound_coppola_willis` (Lucas/Coppola overlap) but Burtt's approach is fundamentally different from Murch — inventive vs. philosophical.

**Expansion candidate:** `sound_burtt_inventive` — for scripts requiring iconic manufactured sound events (sci-fi, creature design, technology sounds).

---

### Gary Rydstrom — The Emotionalist

**Association:** Steven Spielberg, Pixar (Terminator 2, Jurassic Park, Saving Private Ryan, Finding Nemo)  
**Oscars:** 7 (most of any sound designer in history)  
**Philosophy:** Sound should serve emotion first, spectacle second. Even the loudest explosions need an emotional core.

**Signature techniques:**
- **Animal vocalization compositing** — the T-Rex roar in Jurassic Park is a baby elephant combined with a tiger, an alligator, and Rydstrom's Jack Russell terrier. Each animal contributes a frequency band that maps to an emotional register (the elephant for low power, the terrier for high-frequency aggression).
- **Emotional realism over physical accuracy** — Saving Private Ryan's Omaha Beach doesn't sound like actual combat recordings. It sounds like what terror *feels* like. Rydstrom selectively emphasizes underwater muffling, bullet whip-cracks, and breathing to put the audience inside a body.
- **Scale through contrast** — quiet moments before large events. The glass of water vibrating before the T-Rex arrives is more terrifying than the roar itself because it's intimate, domestic, and wrong.

**Prompt DNA:** emotion-driven layered SFX (animal/machine composites for creature presence), intimate domestic sounds preceding large-scale events, underwater/muffled POV shifts, scale built through contrast not volume

**Current mapping:** Not directly anchored. Nearest: `sound_deakins` (environmental realism), but Rydstrom is more about manufactured emotional impact than location authenticity.

**Expansion candidate:** `sound_rydstrom_emotional` — for scripts requiring large-scale creature/action sequences where emotion must anchor spectacle.

---

### Ren Klyce — The Surgeon

**Association:** David Fincher (Se7en, Fight Club, The Social Network, Gone Girl, Mank)  
**Philosophy:** Sound should create unease through precision. The audience shouldn't be able to identify *why* they feel uncomfortable — they just do.

**Signature techniques:**
- **Hyper-real psychological foley** — every footstep, paper rustle, and keyboard click in a Fincher film is recorded with forensic precision, then placed at slightly wrong levels or timing to create subliminal discomfort.
- **Unsettling ambience beds** — low-frequency drones that sit below conscious hearing threshold. Fluorescent light hum pitched down. Air conditioning that subtly shifts pitch.
- **Music-sound integration** — Klyce works in deep collaboration with Reznor/Ross. In Gone Girl, the score and the sound design are inseparable — you can't tell where the drone ends and the music begins.
- **Relentless sonic environments** — Fincher's films never have true silence. There is always *something* — a hum, a buzz, a distant mechanical sound. The world is always slightly oppressive.

**Prompt DNA:** clinical precise foley at subtly wrong levels, sub-threshold low-frequency drones, fluorescent/mechanical ambience that never fully stops, seamless score-to-sound-design transitions

**Current mapping:** `sound_fincher_khondji` (designer_anchor: Ren Klyce)

---

### Skip Lievsay — The Minimalist

**Association:** Coen Brothers (No Country for Old Men, Fargo, Barton Fink), also Scorsese, Spike Lee  
**Philosophy:** "Sound design haiku" — achieve maximum impact with minimum elements. Silence is the most powerful sound in the toolkit.

**Signature techniques:**
- **Silence as tension** — the cattle gun in No Country for Old Men. The sound design is defined by what Lievsay *removes*. Long stretches of near-silence make every sound event land like a thunderclap.
- **Environmental breathing** — rooms, landscapes, and spaces have their own respiratory rhythm. Wind through a motel hallway. The creak of a floorboard that tells you someone is in the next room. The environment is a character.
- **Sparse, impactful placement** — instead of 30 layers, Lievsay uses 3-5. Each one is chosen for maximum narrative information. You hear what matters and nothing else.
- **Diegetic commitment** — sounds in Coen Brothers films almost always have an identifiable source. The audience's ear trusts the world because it's acoustically honest.

**Prompt DNA:** deliberate silence stretches with single precise sound events, environmental room-tone as character, sparse 3-5 layer mixes, diegetically committed sound sourcing

**Current mapping:** `sound_deakins` (designer_anchor: Skip Lievsay) — note: pairing Lievsay with a Deakins visual tag is smart since Lievsay did sound for Deakins-shot Coen films (Fargo, No Country, True Grit).

---

### Richard King — The Architect

**Association:** Christopher Nolan (The Dark Knight, Inception, Interstellar, Dunkirk, Oppenheimer, Dune: Part Two)  
**Oscars:** 5 (Master and Commander, The Dark Knight, Inception, Dunkirk, Dune: Part Two)  
**Philosophy:** Build the world from the character's perspective. Sound isn't objective — it's filtered through who is hearing it.

**Signature techniques:**
- **Character-perspective sound building** — in Dunkirk, you don't hear the full battlefield. You hear what *this soldier* hears — muffled, panicked, with the wrong things too loud and the important things barely audible.
- **Found-object ingenuity** — King put a billiard ball in a clothes dryer to simulate a broken crankshaft in Dunkirk's plane crash. For Inception, collapsing buildings were created from recordings of avalanches and landslides combined with breaking glass at different speeds.
- **Seismic weight** — Nolan's films have physical heft in their sound. Explosions aren't just loud — they have low-frequency mass that you feel in your chest. King layers sub-bass rumbles under impacts to create visceral weight.
- **Silence in hostile environments** — Interstellar's space sequences. King uses the absence of sound in vacuum as a narrative tool — when sound cuts out, the audience suddenly feels the danger of the environment.

**Prompt DNA:** character-POV filtered audio (some sources muffled/amplified based on emotional state), seismic sub-bass under impacts, found-object mechanical textures, vacuum silence as danger signal

**Current mapping:** Not directly anchored. Nearest overlap: `sound_deakins` (environmental) but King's approach is more subjective/character-filtered.

**Expansion candidate:** `sound_king_nolan` — for scripts requiring large-scale subjective environments (war, space, psychological thriller).

---

### Dane Davis — The Alchemist

**Association:** The Matrix trilogy, Riddick  
**Oscar:** 1 (The Matrix)  
**Philosophy:** Push sound into territory that has never existed before. If the audience has heard it, it's wrong.

**Signature techniques:**
- **Bullet-time audio** — the signature Matrix slow-motion required an entirely new sonic vocabulary. Davis slowed, stretched, and re-pitched recordings at different rates for different elements in the same frame, so a bullet moves through air at one temporal rate while the character dodges at another.
- **Time-rate manipulation** — recording a single event (a punch, a gunshot) and splitting it into temporal layers, each processed at a different speed. The composite creates a sound that exists in multiple time-streams simultaneously.
- **Composite body hits** — the martial arts hits in The Matrix aren't single impacts. Each punch is 30-40 layers: leather, wood, metal, bone, fabric, air displacement, room resonance, and a "sweetener" that gives it the superhuman quality.
- **Digital-organic tension** — the Matrix's sentinel machines sound alive (insect wings, animal snarls) while the human world sounds mechanical. This inversion creates fundamental unease.

**Prompt DNA:** time-rate split processing (multi-temporal sound layers), 30+ layer composite impacts, digital-organic inversions (machines sound alive, humans sound mechanical), never-heard-before sonic invention

**Current mapping:** Not anchored. No current tag captures this "alchemical" approach.

**Expansion candidate:** `sound_davis_matrix` — for scripts requiring reality-bending action sequences, bullet-time, or sci-fi combat.

---

### Randy Thom — The Advocate

**Association:** Skywalker Sound (The Right Stuff, Cast Away, The Incredibles, Ratatouille, Wild)  
**Oscars:** 2 (The Right Stuff, Cast Away)  
**Philosophy:** "Designing a movie for sound" — sound must be designed into the script at the writing stage, not applied in post. If the screenplay doesn't make room for sound to tell the story, no amount of post-production brilliance will save it.

**Signature techniques:**
- **Emotion-first design** — Thom starts by asking "what does the character *feel* right now?" and builds the soundscape from that answer, not from what's physically in the frame.
- **Character-hearing perspective** — in Cast Away, the island sounds change as Chuck adapts. Early scenes have harsh, alien environmental sounds. Later, the same wind and waves sound almost musical — because Chuck has adapted.
- **Pre-production sound concepts** — Thom advocates for a "sound designer" role in pre-production, influencing how scenes are written and shot to *make room* for sound storytelling. Scenes with too much dialogue leave no space for sound design.
- **Side-door impact** — Thom describes sound as entering "the side door to your brain." It bypasses the critical faculty that analyzes what you see. You process visual information analytically; you process sound emotionally before you're aware of it.

**Prompt DNA:** emotion-first soundscapes that evolve with character arc, environmental sounds that shift in character as narrative progresses, deliberate silence/space in dialogue for sound storytelling, subliminal emotional manipulation through ambient design

**Current mapping:** Not anchored. Thom's philosophy is meta-level — it's about *how* to design sound into a script, not a specific sonic texture.

**Not a tag candidate** — Thom's contribution is architectural rather than textural. His philosophy should inform *how scripts are written* (leaving space for sonic storytelling) rather than prompt injection. Relevant for `generate_corpus.py` training data about sound-conscious script construction.

---

### Trent Reznor & Atticus Ross — The Hybridists

**Association:** David Fincher (The Social Network, Gone Girl, Mank), Luca Guadagnino (Challengers, Queer)  
**Oscars:** 2 (The Social Network, Soul)  
**Philosophy:** The score IS the sound design. Erase the boundary between music and ambient texture.

**Signature techniques:**
- **Electronic-orchestral hybrid scoring** — Nine Inch Nails' industrial background merged with film composition. Modular synths sit alongside string quartets. The listener can't locate where "music" ends and "sound" begins.
- **Whole-film-first composition** — Reznor/Ross compose entire albums of material *before* seeing a rough cut. They build a sonic world, then Fincher selects pieces that fit. This gives the score a cohesive identity rather than scene-by-scene reactivity.
- **Weaponized ambient music** — in Gone Girl, the score is beautiful, serene piano that becomes increasingly sinister through context. The music doesn't change — your understanding of it does.
- **Texture as narrative** — the static, glitch, and hiss in their scores aren't errors. They're emotional information. The Social Network's score is full of digital artifacts that represent the cold precision of code.

**Prompt DNA:** electronic-orchestral hybrid score blurring music/sound-design boundary, beautiful-to-sinister tonal ambiguity, digital texture artifacts (glitch, hiss, static) as emotional content, modular synth drones under acoustic instruments

**Current mapping:** Implicitly covered by `sound_fincher_khondji` through Klyce collaboration, but Reznor/Ross bring a distinct compositional approach that's about *score* rather than *effects*.

**Expansion candidate:** `sound_reznor_ross` — for scripts requiring score-as-sound-design, industrial textures, or music that shifts meaning through narrative context.

---

### Hildur Gudnadottir — The Instrument Builder

**Association:** Todd Phillips (Joker), HBO (Chernobyl), also Tar  
**Awards:** Oscar (Joker), Emmy (Chernobyl), Grammy (Chernobyl), BAFTA x2 — first solo woman to win all four for scoring.  
**Philosophy:** Build the instrument first, then compose. If the sound source doesn't exist, create it.

**Signature techniques:**
- **Halldorophone performance** — an electro-acoustic cello variant that facilitates creative manipulation of feedback. Gudnadottir composed Joker's core themes on this instrument, producing an eerie drone that is the sonic expression of Arthur Fleck's anxious dread.
- **On-site field recording as instrument** — for Chernobyl, she recorded inside the decommissioned Ignalina nuclear power plant in Lithuania. The hums, buzzes, and rhythmic clanking of the machinery became the entire score. No traditional instruments. The reactor *is* the orchestra.
- **Score-before-shooting** — like Reznor/Ross, Gudnadottir composed before seeing a cut. For Joker, Joaquin Phoenix listened to her score on set and improvised his physical performance to it. The music shaped the acting, not the other way around.
- **Single-instrument emotional architecture** — rather than orchestral complexity, she builds entire emotional worlds from one instrument (the halldorophone for Joker, the nuclear plant for Chernobyl). Constraint as creative force.

**Prompt DNA:** solo instrument emotional drones (cello/halldorophone texture), industrial field recording as musical score, feedback manipulation, single-source constraint (one instrument = one emotional world), score-shapes-performance approach

**Current mapping:** Not anchored.

**Expansion candidate:** `sound_gudnadottir_dread` — for scripts requiring single-source emotional scoring, industrial ambience-as-music, or dread built through sustained texture rather than melody.

---

## II. Technique Taxonomy

### Spatial & Format Techniques

| Technique | Definition | Prompt Language |
|-----------|-----------|-----------------|
| **Worldizing** | Playing back sound through speakers in real spaces, re-recording the room response (Murch) | "worldized room reflections — sound played back into physical space and re-captured" |
| **Object-based audio** | Dolby Atmos / DTS:X — individual sound "objects" placed in 3D space, moving freely through the auditorium | "object-based spatial audio — individual sounds positioned and moving in three-dimensional space" |
| **Binaural recording** | Two-microphone recording mimicking human ear placement for headphone 3D | "binaural spatial capture — left/right ear perspective for intimate headphone 3D" |
| **Ambisonics** | Full-sphere audio capture/playback, common in VR/immersive | "ambisonic spherical audio — full 360-degree spatial sound field" |

### Mix Philosophy Techniques

| Technique | Definition | Prompt Language |
|-----------|-----------|-----------------|
| **Subtractive mixing** | Removing layers at key moments so surviving sounds carry disproportionate weight (Murch) | "subtractive silence drops — ambient layers removed so a single sound event carries maximum weight" |
| **Dense Clarity** | Many elements organized so each is individually perceptible (Murch) | "dense clarity layering — multiple distinct elements, each cleanly separated and perceptible" |
| **Sparse impact** | Minimal layers (3-5) chosen for maximum narrative information (Lievsay) | "sparse impactful mix — three to five precisely chosen layers, nothing decorative" |
| **Score-as-sound-design** | Erasing boundary between musical score and ambient sound design (Reznor/Ross, Klyce) | "score-sound fusion — music and ambient design blur into one inseparable texture" |

### Source & Recording Techniques

| Technique | Definition | Prompt Language |
|-----------|-----------|-----------------|
| **Found-object recording** | Using everyday objects to create sounds (dryer + billiard ball, broken cables) | "found-object organic textures — sounds sourced from unexpected real-world materials" |
| **Animal vocalization compositing** | Layering multiple animal recordings across frequency bands (Rydstrom) | "animal composite layering — creature voices built from multiple species across frequency registers" |
| **On-site field recording** | Recording inside the actual location that appears on screen (Gudnadottir/Chernobyl) | "location-sourced scoring — the environment itself becomes the instrument" |
| **Foley artistry** | Live performance of synchronized sound effects to picture (footsteps, cloth, props) | "precision foley performance — human-performed sound effects synchronized to on-screen action" |

### Time & Perception Techniques

| Technique | Definition | Prompt Language |
|-----------|-----------|-----------------|
| **Time-rate manipulation** | Processing different elements at different temporal rates within the same moment (Davis) | "multi-temporal sound layers — elements processed at different time rates within one moment" |
| **Doppler manipulation** | Recording sounds with source-to-mic relative motion for natural pitch shifts (Burtt) | "Doppler pitch shifting — natural frequency sweep from source motion" |
| **Shepard tone** | Auditory illusion of a tone that seems to rise (or fall) infinitely — used for mounting tension (Nolan/Zimmer) | "Shepard tone escalation — infinitely rising pitch illusion for mounting dread" |
| **Character-POV filtering** | Sound filtered through what a specific character would hear, not objective reality (King, Thom) | "character-perspective audio — sounds filtered by emotional state, not acoustic physics" |

### Structural Techniques

| Technique | Definition | Prompt Language |
|-----------|-----------|-----------------|
| **Diegetic** | Sound whose source exists within the story world (a radio playing, a car engine) | "diegetic sound — source visible or implied within the scene" |
| **Non-diegetic** | Sound added for audience only (score, narration, sound effects with no in-world source) | "non-diegetic score/narration — audience-only audio layer" |
| **Meta-diegetic** | Sound representing a character's internal state (hallucinations, memories, inner voice) | "meta-diegetic interiority — sounds representing internal psychological state" |
| **Walla** | Background crowd murmur recorded specifically to be unintelligible but present | "walla crowd layer — unintelligible background murmur establishing populated space" |
| **Room tone** | The "silence" of a specific space — every room has its own acoustic signature | "room tone bed — the specific silence of this space, its ambient acoustic fingerprint" |
| **Stinger** | A single sharp sound event used to punctuate a scare or reveal | "stinger hit — single sharp sound punctuating a reveal moment" |
| **Riser** | A sound that gradually increases in pitch/volume to build tension before a beat | "riser build — gradually escalating pitch/volume approaching a narrative beat" |

---

## III. Current Registry Gaps & Expansion Proposals

The existing `sound_*` tag set maps 1:1 to visual `style_*` tags (director/cinematographer pairs). This works for the current 7 visual masters, but sound design doesn't map cleanly to cinematography. The strongest sound designers are often paired with *different* directors than the visual tags imply.

### Recommended expansions (4 new tags)

| Proposed ID | Anchor Designer | Use Case | Notes |
|-------------|----------------|----------|-------|
| `sound_burtt_inventive` | Ben Burtt | Sci-fi, creature design, technology sounds, iconic manufactured sound events | Fills gap: no current tag for "invented from found objects" approach |
| `sound_king_nolan` | Richard King | Large-scale subjective environments (war, space, psychological thriller), seismic impact | Fills gap: Nolan's films have a distinct sonic identity not captured by any current tag |
| `sound_reznor_ross` | Reznor & Ross | Score-as-sound-design, industrial textures, electronic-orchestral hybrid, tonal ambiguity | Fills gap: score/music approach distinct from Klyce's effects-level precision |
| `sound_gudnadottir_dread` | Hildur Gudnadottir | Single-source emotional scoring, industrial ambience-as-music, sustained dread textures | Fills gap: constraint-based composition, instrument-building approach |

### Recommended combo additions

| Proposed ID | Components | Use Case |
|-------------|-----------|----------|
| `sound_combo_king_reznor` | `sound_king_nolan` + `sound_reznor_ross` | Nolan-style film: seismic environments + score-as-texture (Dunkirk/Oppenheimer territory) |
| `sound_combo_murch_gudnadottir` | `sound_coppola_willis` + `sound_gudnadottir_dread` | Psychological depth: worldized philosophical layers + sustained single-source dread |
| `sound_combo_burtt_davis` | `sound_burtt_inventive` + `sound_davis_matrix` | Sci-fi combat: organic invented sounds + time-rate manipulation |

### Proposed `sound_davis_matrix` tag

While Dane Davis's work is narrower in filmography than other designers on this list, his techniques (time-rate manipulation, multi-temporal layering, 30+ layer composite impacts) are uniquely relevant to action/sci-fi content. If the pipeline renders sequences with bullet-time, reality-bending, or superhuman combat, this tag has no substitute.

---

## IV. Pipeline Integration Notes

### Prompt injection order (from `compose_prompt_order`)

The current registry places `audio_dna_resolve` at position 8 of 11 in the compose chain, after `style_dna_resolve` and `hybrid_camera_move`. This is correct — visual establishes the world, audio responds to it.

### Chain audio rule

When `block_index > 0`, the resolver appends the tag's `chain_prompt` with references to `audio_tail` + `last_frame`. This ensures sonic continuity across sequential blocks. The chain rule is already defined in the JSON registry.

### Wired (v3)

- Emotion-driven tag picker — `emotional_beat` + `emotional_beat_map` in `style_modifiers.py`
- Technique taxonomy — appended to sonic prompt clauses via tag `techniques` arrays
- Tier B designer tags + 5 combos in `sonic_signatures_grok_audio_v1.json`
- `sound_deakins` semantic fix — Lievsay sparse (ID unchanged)

### Still deferred

- Auto best-of-3 selection
- Post-stitch EQ across xfade joins (stub: `stitch_audio_polish.py`)

### Training data

`generate_corpus.py` → `narrative_craft` preset → `sound_conscious_writing` domain (15 Randy Thom topics).

---

## V. Source Index

### Designer Profiles
- [Walter Murch — Wikipedia](https://en.wikipedia.org/wiki/Walter_Murch)
- [Ben Burtt — How the Sound Effects for Star Wars Were Made](https://www.popularmechanics.com/culture/movies/a34785/ben-burtt-sound-effects-star-wars/)
- [Gary Rydstrom — 7 Oscars](https://en.wikipedia.org/wiki/Gary_Rydstrom)
- [Ren Klyce — Fincher's Sound Designer](https://www.indiewire.com/features/general/david-fincher-ren-klyce-sound-design-1234633458/)
- [Skip Lievsay — Sound Design Haiku](https://en.wikipedia.org/wiki/Skip_Lievsay)
- [Richard King — Nolan's Sound Architect](https://www.indiewire.com/features/general/christopher-nolan-richard-king-sound-design-1202165030/)
- [Dane Davis — Matrix Sound Design](https://en.wikipedia.org/wiki/Dane_Davis)
- [Randy Thom — Screenwriting for Sound](https://www.filmsound.org/articles/designing_for_sound.htm)
- [Trent Reznor & Atticus Ross — Score as Sound Design](https://en.wikipedia.org/wiki/Trent_Reznor_and_Atticus_Ross)
- [Hildur Gudnadottir — Joker/Chernobyl](https://en.wikipedia.org/wiki/Hildur_Gu%C3%B0nad%C3%B3ttir)

### Technique References
- [Dolby Atmos Object-Based Audio Guide](https://cinemaworks.in/the-complete-guide-to-next-gen-cinema-sound-dolby-atmos-auro-11-3-beyond/)
- [Randy Thom — Designing a Movie for Sound (original essay)](https://www.filmsound.org/articles/designing_for_sound.htm)
- [Richard King — Dunkirk Sound Design](https://postperspective.com/richard-king-talks-dunkirks-sound-design/)
- [Hildur Gudnadottir — Halldorophone and Chernobyl Process](https://www.popdisciple.com/interviews/hildur-gudnadottir)
- [Immersive Audio 2025 — Object-Based Personalization](https://www.thebroadcastbridge.com/content/entry/21534/immersive-audio-2025-object-based-audio-a-new-era-of-personalization)
- [Richard King — Academy Award Approach to Sound Design](https://blog.prosoundeffects.com/how-richard-king-approaches-sound-design)

#!/usr/bin/env python3
"""modifier_suggester.py — Recommend style/audio/music/pacing DNA tags for ingested screenplays.

Analyzes screenplay content (genre, tone, pacing, dialogue density) and suggests
modifier tags from the actual ELEANOR research registries. Can run standalone or
be called from screenplay_ingest.py.

Usage:
    python modifier_suggester.py script.json -o script_modified.json
    python modifier_suggester.py script.json --apply   # overwrites in place

As a library:
    from modifier_suggester import suggest_modifiers, apply_suggestions
    suggestions = suggest_modifiers(script_dict)
    script = apply_suggestions(script_dict, suggestions)
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ─────────────────────────── known modifier IDs ───────────────────────
# Sourced from DAVID/ELEANOR/research/ registry files (2026-06-30).
# The suggester only recommends IDs that actually exist in the registries.

VISUAL_STYLES = {
    "style_fincher_khondji":     {"tone": ["dark", "thriller", "crime", "noir", "psychological"],
                                   "label": "Fincher/Khondji — precision noir"},
    "style_anderson_yeoman":     {"tone": ["whimsical", "comedy", "quirky", "colorful", "absurd"],
                                   "label": "Anderson/Yeoman — symmetrical pastel"},
    "style_coppola_willis":      {"tone": ["epic", "operatic", "crime", "family", "power"],
                                   "label": "Coppola/Willis — chiaroscuro opera"},
    "style_deakins_villeneuve":  {"tone": ["epic", "sci-fi", "vast", "contemplative", "desert", "war"],
                                   "label": "Deakins/Villeneuve — luminous practical"},
    "style_bergman_nykvist":     {"tone": ["intimate", "psychological", "existential", "drama", "quiet"],
                                   "label": "Bergman/Nykvist — psychological portrait"},
    "style_bertolucci_storaro":  {"tone": ["sensual", "political", "period", "lush", "romantic"],
                                   "label": "Bertolucci/Storaro — color symphony"},
    "style_cuaron_lubezki":      {"tone": ["immersive", "continuous", "naturalistic", "survival", "journey"],
                                   "label": "Cuarón/Lubezki — long-take immersion"},
}

HYBRID_STYLES = {
    "hybrid_fincher_deakins":              {"tone": ["thriller", "noir", "naturalistic", "dark"],
                                             "label": "Precision Natural Decay"},
    "hybrid_anderson_storaro":             {"tone": ["colorful", "theatrical", "artistic"],
                                             "label": "Symmetrical Color Psych Opera"},
    "hybrid_coppola_lubezki":              {"tone": ["epic", "immersive", "shadow"],
                                             "label": "Chiaroscuro Immersive Oner"},
    "hybrid_deakins_bergman":              {"tone": ["intimate", "luminous", "portrait"],
                                             "label": "Luminous Psychological Portrait"},
    "hybrid_storaro_cuaron":               {"tone": ["fluid", "sensual", "color"],
                                             "label": "Color Symphony Fluid Immersion"},
    "hybrid_fincher_anderson_deakins":     {"tone": ["complex", "layered", "noir", "controlled"],
                                             "label": "Controlled Chaos Diorama Noir"},
    "hybrid_omniscient_evolution":          {"tone": ["evolving", "dynamic", "adaptive"],
                                             "label": "Grok Omniscient Evolution"},
}
# ─────────────────── Original styles (not director-derived) ───────────────────
# Four families: extinct tech, material/texture, era fusions, abstract/procedural

EXTINCT_STYLES = {
    "extinct_technicolor_3strip":  {"tone": ["musical", "colorful", "glamour", "classic", "fantasy"],
                                     "label": "3-Strip Technicolor (dead process)"},
    "extinct_technicolor_2color":  {"tone": ["vintage", "silent", "early", "warm", "experimental"],
                                     "label": "2-Color Technicolor (dead process)"},
    "extinct_kodachrome":          {"tone": ["documentary", "warm", "nostalgic", "classic", "americana"],
                                     "label": "Kodachrome (discontinued 2010)"},
    "extinct_autochrome":          {"tone": ["impressionist", "soft", "vintage", "dreamy", "pastoral"],
                                     "label": "Autochrome Lumière (dead process)"},
    "extinct_nitrate":             {"tone": ["classic", "noir", "drama", "luminous", "silver"],
                                     "label": "Nitrate Film Stock (extinct)"},
    "extinct_daguerreotype":       {"tone": ["portrait", "still", "haunting", "formal", "antique"],
                                     "label": "Daguerreotype (1839 process)"},
    "extinct_kinemacolor":         {"tone": ["early", "experimental", "spectacle", "historical"],
                                     "label": "Kinemacolor (dead process)"},
    "extinct_orthochromatic":      {"tone": ["silent", "expressionist", "horror", "theatrical", "gothic"],
                                     "label": "Orthochromatic Film (red-blind)"},
    "extinct_handtinted":          {"tone": ["fantasy", "fairy_tale", "silent", "magical", "theatrical"],
                                     "label": "Hand-Tinted Film (Méliès era)"},
    "extinct_ektachrome_160t":     {"tone": ["concert", "nightlife", "music", "80s", "available_light"],
                                     "label": "Ektachrome 160T Tungsten (dead emulsion)"},
    "extinct_dufaycolor":          {"tone": ["documentary", "impressionist", "soft", "vintage", "experimental"],
                                     "label": "Dufaycolor Réseau Screen (dead process)"},
    "extinct_gasparcolor":         {"tone": ["animation", "psychedelic", "colorful", "abstract", "experimental"],
                                     "label": "Gasparcolor Dye-Bleach (dead process)"},
    "extinct_vistavision":         {"tone": ["epic", "spectacle", "widescreen", "glamour", "period"],
                                     "label": "VistaVision 8-Perf (dead format)"},
    "extinct_cinecolor":           {"tone": ["western", "adventure", "action", "warm", "vintage"],
                                     "label": "Cinecolor Two-Color (dead process)"},
}

MATERIAL_STYLES = {
    "material_oxidized_copper":    {"tone": ["architectural", "decay", "historical", "patina", "urban"],
                                     "label": "Oxidized Copper / Verdigris"},
    "material_wet_concrete":       {"tone": ["urban", "noir", "rain", "brutalist", "isolation"],
                                     "label": "Wet Concrete / Urban Brutalism"},
    "material_volcanic_glass":     {"tone": ["dark", "obsidian", "primal", "volcanic", "power"],
                                     "label": "Volcanic Glass / Obsidian"},
    "material_bioluminescent":     {"tone": ["ocean", "alien", "ethereal", "darkness", "creature"],
                                     "label": "Deep Ocean Bioluminescence"},
    "material_rusted_iron":        {"tone": ["industrial", "decay", "post_apocalyptic", "abandoned", "warm"],
                                     "label": "Rusted Iron / Oxide Palette"},
    "material_cracked_porcelain":  {"tone": ["fragile", "beauty", "broken", "resilience", "intimate"],
                                     "label": "Cracked Porcelain / Kintsugi"},
    "material_mercury_liquid":     {"tone": ["surreal", "reflective", "sci-fi", "liquid", "mirror"],
                                     "label": "Liquid Mercury / Chrome"},
    "material_amber_resin":        {"tone": ["preserved", "warm", "golden", "nostalgic", "time"],
                                     "label": "Amber Resin / Fossilized"},
    "material_weathered_wood":     {"tone": ["organic", "aging", "rural", "natural", "honest"],
                                     "label": "Weathered Wood / Grain"},
    "material_frosted_glass":      {"tone": ["obscured", "privacy", "mystery", "diffused", "intimate"],
                                     "label": "Frosted Glass / Diffusion"},
}

FUSION_STYLES = {
    "fusion_art_deco_cyberpunk":   {"tone": ["cyberpunk", "glamour", "retro_future", "noir", "neon"],
                                     "label": "Art Deco + Cyberpunk"},
    "fusion_baroque_neon":         {"tone": ["dramatic", "religious", "neon", "excess", "dark"],
                                     "label": "Baroque + Neon"},
    "fusion_constructivist_vaporwave": {"tone": ["propaganda", "nostalgia", "ironic", "pastel", "geometric"],
                                         "label": "Constructivist + Vaporwave"},
    "fusion_ukiyo_drone":          {"tone": ["japanese", "aerial", "flat", "landscape", "nature"],
                                     "label": "Ukiyo-e + Drone Aerial"},
    "fusion_noir_solarpunk":       {"tone": ["noir", "hopeful", "green", "detective", "rain"],
                                     "label": "Film Noir + Solarpunk"},
    "fusion_renaissance_glitch":   {"tone": ["classical", "digital", "corruption", "art", "surreal"],
                                     "label": "Renaissance + Glitch Art"},
    "fusion_brutalist_bioluminescence": {"tone": ["concrete", "organic", "glow", "contrast", "urban"],
                                          "label": "Brutalist + Bioluminescence"},
    "fusion_art_nouveau_circuit":  {"tone": ["organic", "technology", "flowing", "elegant", "botanical"],
                                     "label": "Art Nouveau + Circuit Board"},
    "fusion_gothic_infrared":      {"tone": ["gothic", "religious", "infrared", "supernatural", "cathedral"],
                                     "label": "Gothic + Infrared"},
    "fusion_bauhaus_underwater":   {"tone": ["geometric", "underwater", "surreal", "primary", "fluid"],
                                     "label": "Bauhaus + Underwater"},
}

PROCEDURAL_STYLES = {
    "proc_chromatic_aberration":   {"tone": ["distortion", "optical", "psychedelic", "imperfect", "prismatic"],
                                     "label": "Chromatic Aberration"},
    "proc_datamosh":               {"tone": ["digital", "glitch", "abstract", "experimental", "corruption"],
                                     "label": "Datamosh / Compression Art"},
    "proc_infrared":               {"tone": ["alien", "dreamlike", "ethereal", "surreal", "nature"],
                                     "label": "Infrared False-Color"},
    "proc_thermal":                {"tone": ["surveillance", "heat", "clinical", "night_vision", "military"],
                                     "label": "Thermal / FLIR Imaging"},
    "proc_slit_scan":              {"tone": ["psychedelic", "time", "abstract", "sci-fi", "distortion"],
                                     "label": "Slit-Scan Temporal Displacement"},
    "proc_double_exposure":        {"tone": ["memory", "dream", "psychological", "romantic", "layered"],
                                     "label": "Double Exposure / Superimposition"},
    "proc_long_exposure":          {"tone": ["serene", "flowing", "night", "meditative", "time"],
                                     "label": "Long Exposure / Light Trails"},
    "proc_macro_world":            {"tone": ["microscopic", "detail", "nature", "intimate", "hidden"],
                                     "label": "Extreme Macro / Micro World"},
    "proc_particle_field":         {"tone": ["atmospheric", "volumetric", "spiritual", "dust", "light"],
                                     "label": "Particle Field / Visible Atmosphere"},
    "proc_photogrammetric":        {"tone": ["digital", "scan", "incomplete", "3d", "point_cloud"],
                                     "label": "Photogrammetry Point Cloud"},
}


AUDIO_STYLES = {
    "sound_fincher_khondji":   {"tone": ["thriller", "tension", "precise", "clinical"],
                                 "label": "Fincher/Khondji Sonic"},
    "sound_anderson_yeoman":   {"tone": ["whimsical", "retro", "playful", "quirky"],
                                 "label": "Anderson/Yeoman Sonic"},
    "sound_coppola_willis":    {"tone": ["epic", "operatic", "war", "power"],
                                 "label": "Coppola/Willis Sonic"},
    "sound_deakins":           {"tone": ["vast", "naturalistic", "contemplative"],
                                 "label": "Deakins/Lievsay Sonic"},
    "sound_bergman_nykvist":   {"tone": ["intimate", "quiet", "existential", "silence"],
                                 "label": "Bergman/Nykvist Sonic"},
    "sound_storaro_bertolucci":{"tone": ["lush", "romantic", "sensual", "period"],
                                 "label": "Storaro/Bertolucci Sonic"},
    "sound_cuaron_lubezki":    {"tone": ["immersive", "continuous", "naturalistic"],
                                 "label": "Cuarón/Lubezki Sonic"},
    "sound_burtt_inventive":   {"tone": ["sci-fi", "inventive", "fantastical", "creature"],
                                 "label": "Burtt Inventive Sonic"},
    "sound_king_nolan":        {"tone": ["epic", "war", "tension", "spectacle"],
                                 "label": "King/Nolan Sonic"},
    "sound_reznor_ross":       {"tone": ["electronic", "tension", "modern", "dark"],
                                 "label": "Reznor/Ross Hybrid Sonic"},
    "sound_gudnadottir_dread": {"tone": ["dread", "horror", "anxiety", "oppressive"],
                                 "label": "Gudnadottir Dread Sonic"},
    "sound_rydstrom_emotional":{"tone": ["emotional", "fantasy", "wonder", "adventure"],
                                 "label": "Rydstrom Emotional Sonic"},
    "sound_davis_matrix":      {"tone": ["sci-fi", "action", "digital", "cyber"],
                                 "label": "Davis Matrix Sonic"},
    "sound_blended_7masters":  {"tone": ["versatile", "balanced", "neutral"],
                                 "label": "Blended 7-Master Sound Bible"},
}

MUSIC_STYLES = {
    "music_williams_leitmotif":    {"tone": ["epic", "adventure", "heroic", "fantasy", "wonder"],
                                     "label": "Williams Leitmotif Orchestral"},
    "music_zimmer_architect":      {"tone": ["epic", "spectacle", "tension", "modern", "war"],
                                     "label": "Zimmer Architectural Score"},
    "music_herrmann_suspense":     {"tone": ["thriller", "suspense", "psychological", "noir", "dread"],
                                     "label": "Herrmann Psychological Suspense"},
    "music_morricone_melodist":    {"tone": ["western", "epic", "romantic", "operatic", "sweeping"],
                                     "label": "Morricone Melodist Score"},
    "music_greenwood_dissonant":   {"tone": ["dissonant", "dark", "experimental", "anxiety", "horror"],
                                     "label": "Greenwood Dissonant Orchestral"},
    "music_sakamoto_crosscultural":{"tone": ["contemplative", "eastern", "fusion", "spiritual"],
                                     "label": "Sakamoto Cross-Cultural Score"},
    "music_hisaishi_dreamer":      {"tone": ["whimsical", "magical", "childhood", "wonder", "gentle"],
                                     "label": "Hisaishi Dreamer Score"},
    "music_rota_storyteller":      {"tone": ["italian", "nostalgic", "family", "circus", "comedy"],
                                     "label": "Rota Storyteller Score"},
    "music_goransson_fusion":      {"tone": ["modern", "hip-hop", "fusion", "energetic", "urban"],
                                     "label": "Göransson Fusion Score"},
    "music_desplat_impressionist": {"tone": ["elegant", "romantic", "period", "french", "delicate"],
                                     "label": "Desplat Impressionist Score"},
    "music_burwell_minimalist":    {"tone": ["subtle", "dark comedy", "understated", "quirky"],
                                     "label": "Burwell Minimalist Score"},
    "music_horner_epic":           {"tone": ["epic", "romantic", "sweeping", "tragic", "heroic"],
                                     "label": "Horner Epic Sweep"},
    "music_poledouris_warrior":    {"tone": ["warrior", "battle", "primal", "ancient", "power"],
                                     "label": "Poledouris Warrior Anthem"},
    "music_jazz_noir":             {"tone": ["noir", "jazz", "crime", "urban", "night", "detective"],
                                     "label": "Jazz Noir Score"},
    "music_bmovie_synth":          {"tone": ["retro", "80s", "synth", "horror", "camp", "grindhouse"],
                                     "label": "B-Movie Synth Score"},
    "music_blended_epic_hybrid":   {"tone": ["versatile", "balanced", "epic", "modern"],
                                     "label": "Blended Epic Hybrid Score"},
    "music_pixar_family_wonder":   {"tone": ["family", "warmth", "childhood", "wonder", "animation"],
                                     "label": "Pixar Family Wonder Score"},
}

PACING_STYLES = {
    "pacing_slow_build_setup":       {"tone": ["slow", "deliberate", "buildup", "tension", "quiet"],
                                       "label": "Slow Build Setup"},
    "pacing_mid_tempo_dialogue":     {"tone": ["dialogue", "conversational", "steady", "drama"],
                                       "label": "Mid-Tempo Dialogue"},
    "pacing_schoonmaker_momentum":   {"tone": ["momentum", "escalation", "drive", "energy"],
                                       "label": "Schoonmaker Momentum"},
    "pacing_murch_subtractive":      {"tone": ["subtractive", "precise", "editorial", "craft"],
                                       "label": "Murch Subtractive"},
    "pacing_fincher_tension_accel":  {"tone": ["thriller", "acceleration", "tension", "relentless"],
                                       "label": "Fincher Tension Acceleration"},
    "pacing_lubezki_long_take_flow": {"tone": ["continuous", "immersive", "flowing", "long"],
                                       "label": "Lubezki Long-Take Flow"},
    "pacing_invisible_jcut":         {"tone": ["invisible", "seamless", "smooth", "naturalistic"],
                                       "label": "Invisible J-Cut"},
}


# ─────────────────────────── tone keywords ────────────────────────────
# Map screenplay content signals to tone tags that match the registries above.

_GENRE_KEYWORDS = {
    "thriller":      ["gun", "dead", "kill", "blood", "chase", "escape", "danger", "threat",
                      "murder", "detective", "suspect", "hostage", "weapon"],
    "noir":          ["shadows", "cigarette", "alley", "rain", "trench", "dame", "gumshoe",
                      "fedora", "neon", "whiskey", "bourbon"],
    "crime":         ["heist", "robbery", "steal", "mob", "gang", "cartel", "hustle",
                      "cop", "badge", "arrest", "prison", "contraband"],
    "horror":        ["scream", "dark", "creature", "blood", "terror", "fear", "nightmare",
                      "demon", "ghost", "haunted", "corpse", "undead"],
    "sci-fi":        ["space", "planet", "alien", "robot", "android", "cyborg", "laser",
                      "galaxy", "starship", "hologram", "simulation", "matrix"],
    "epic":          ["kingdom", "empire", "throne", "army", "battle", "conquest", "dynasty",
                      "crown", "sword", "castle", "siege", "destiny"],
    "war":           ["soldier", "trench", "bomb", "platoon", "regiment", "combat",
                      "battlefield", "invasion", "surrender", "medal"],
    "romantic":      ["kiss", "love", "heart", "embrace", "wedding", "passion",
                      "affair", "together", "forever", "darling"],
    "comedy":        ["laugh", "joke", "funny", "hilarious", "absurd", "ridiculous",
                      "gag", "pratfall", "slapstick"],
    "whimsical":     ["quirky", "colorful", "eccentric", "oddball", "peculiar",
                      "charming", "delightful", "fantastical"],
    "adventure":     ["quest", "treasure", "map", "journey", "explore", "discovery",
                      "expedition", "artifact", "temple"],
    "drama":         ["tears", "argue", "family", "divorce", "funeral", "grief",
                      "betrayal", "forgive", "reconcile"],
    "western":       ["saloon", "sheriff", "outlaw", "ranch", "desert", "frontier",
                      "gunfight", "horse", "canyon", "dust"],
    "period":        ["corset", "carriage", "manor", "servant", "lord", "duchess",
                      "ballroom", "gaslight", "telegraph"],
    "intimate":      ["close", "whisper", "quiet", "alone", "confession", "secret",
                      "tender", "gentle", "silence"],
    "immersive":     ["continuous", "tracking", "steadicam", "one shot", "follow",
                      "unbroken", "flowing"],
    "action":        ["explosion", "chase", "crash", "jump", "run", "fight", "punch",
                      "kick", "speed", "motorcycle", "helicopter"],
    "dark":          ["shadow", "darkness", "dim", "bleak", "grim", "ominous",
                      "foreboding", "sinister"],
    # ── New tone categories for original styles ──
    "nostalgic":     ["memory", "remember", "childhood", "old", "vintage", "faded",
                      "photograph", "nostalgia", "past", "youth", "retro"],
    "dreamy":        ["dream", "haze", "soft", "blur", "ethereal", "floating",
                      "surreal", "sleepy", "languid", "gossamer"],
    "impressionist": ["light", "painterly", "shimmer", "diffused", "pastel",
                      "watercolor", "gentle", "glow", "luminous"],
    "gothic":        ["cathedral", "gargoyle", "crypt", "tomb", "spire", "stone",
                      "stained", "chapel", "abbey", "monastery", "holy"],
    "expressionist": ["distort", "angular", "exaggerated", "twisted", "madness",
                      "asylum", "cabinet", "grotesque", "puppet"],
    "cyberpunk":     ["neon", "hologram", "chrome", "cyber", "hack", "implant",
                      "augmented", "dystopia", "megacorp", "neural", "punk"],
    "glamour":       ["elegant", "luxury", "jewel", "silk", "champagne", "ballgown",
                      "diamonds", "opulent", "magnificent", "dazzling"],
    "documentary":   ["real", "footage", "interview", "handheld", "observe",
                      "truth", "testimony", "witness", "chronicle"],
    "musical":       ["dance", "song", "sing", "chorus", "stage", "curtain",
                      "orchestra", "spotlight", "encore", "rehearsal"],
    "industrial":    ["factory", "machine", "pipe", "steel", "furnace", "forge",
                      "rust", "gear", "concrete", "grind", "weld", "smoke"],
    "underwater":    ["ocean", "dive", "swim", "reef", "current", "depth",
                      "whale", "coral", "tide", "submarine", "abyss"],
    "aerial":        ["sky", "fly", "bird", "drone", "altitude", "panorama",
                      "horizon", "cloud", "soar", "elevation"],
    "microscopic":   ["cell", "molecule", "crystal", "grain", "fiber", "pore",
                      "lens", "magnify", "specimen", "slide"],
    "surveillance":  ["monitor", "camera", "screen", "infrared", "thermal",
                      "scan", "target", "track", "grid", "signal"],
    "decay":         ["rust", "rot", "crumble", "abandoned", "ruin", "moss",
                      "peel", "erode", "corrode", "deteriorate"],
    "glitch":        ["pixel", "static", "corrupt", "error", "buffer", "lag",
                      "freeze", "artifact", "crash", "digital"],
    "psychedelic":   ["kaleidoscope", "fractal", "trippy", "acid", "swirl",
                      "morph", "pattern", "mandala", "prism", "rainbow"],
    "spiritual":     ["meditation", "temple", "prayer", "ritual", "incense",
                      "candle", "sacred", "transcend", "mystic", "divine"],
    "botanical":     ["flower", "vine", "leaf", "petal", "bloom", "garden",
                      "greenhouse", "botanical", "fern", "blossom"],
    "portrait":      ["face", "eyes", "gaze", "close-up", "expression",
                      "wrinkle", "tear", "smile", "stare"],
    "theatrical":    ["stage", "curtain", "spotlight", "mask", "costume",
                      "audience", "act", "scene", "performance", "applause"],
    "silent":        ["intertitle", "pantomime", "silent", "mute", "gesture",
                      "exaggerated", "slapstick", "accompaniment"],
    "propaganda":    ["poster", "revolution", "worker", "comrade", "banner",
                      "march", "fist", "slogan", "rally", "masses"],
    "vintage":       ["sepia", "antique", "daguerreotype", "tintype", "album",
                      "yellowed", "crackle", "patina", "heirloom"],
    "animation":     ["cartoon", "animated", "animate", "cel", "drawn", "sketch",
                      "toon", "frame-by-frame", "rotoscope", "puppet"],
    "widescreen":    ["panoramic", "vista", "landscape", "sweeping", "horizon",
                      "expanse", "vast", "cinemascope", "scope", "anamorphic"],
}


# ─────────────────────────── analysis ─────────────────────────────────

def _analyze_content(script):
    """Score tone tags by frequency in video_prompts, speech_text, and action."""
    text_pool = []

    for shot in script.get("shots", []):
        vp = shot.get("video_prompt", "")
        st = shot.get("speech_text", "")
        if vp:
            text_pool.append(vp.lower())
        if st:
            text_pool.append(st.lower())

    concept = script.get("concept", "") or ""
    title = script.get("title", "") or ""
    text_pool.append(concept.lower())
    text_pool.append(title.lower())

    full_text = " ".join(text_pool)
    word_count = len(full_text.split())

    # Score each tone tag
    tone_scores = {}
    for tone, keywords in _GENRE_KEYWORDS.items():
        score = 0
        for kw in keywords:
            hits = len(re.findall(r"\b" + re.escape(kw) + r"\b", full_text))
            score += hits
        if score > 0:
            tone_scores[tone] = score

    # Dialogue density (affects pacing suggestion)
    shots = script.get("shots", [])
    dialogue_shots = sum(1 for s in shots if s.get("speech_text"))
    total_shots = len(shots) or 1
    dialogue_ratio = dialogue_shots / total_shots

    # Average shot duration
    durations = [s.get("duration", 5) for s in shots]
    avg_duration = sum(durations) / len(durations) if durations else 5

    return {
        "tone_scores": tone_scores,
        "dialogue_ratio": dialogue_ratio,
        "avg_duration": avg_duration,
        "total_shots": total_shots,
        "word_count": word_count,
    }


def _best_match(registry, tone_scores, top_n=3):
    """Find the best matching ID from a registry given tone scores.

    Returns list of (id, score, label) tuples.
    """
    results = []
    for rid, info in registry.items():
        rtones = info["tone"]
        score = sum(tone_scores.get(t, 0) for t in rtones)
        # Bonus for multiple matching tones
        matching = sum(1 for t in rtones if t in tone_scores)
        score += matching * 2
        if score > 0:
            results.append((rid, score, info["label"]))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_n]


def _suggest_pacing(analysis):
    """Heuristic pacing suggestion based on dialogue ratio and shot duration."""
    dr = analysis["dialogue_ratio"]
    avg = analysis["avg_duration"]
    tones = analysis["tone_scores"]

    if "thriller" in tones or "action" in tones:
        return "pacing_fincher_tension_accel"
    if dr > 0.7:
        return "pacing_mid_tempo_dialogue"
    if avg > 12:
        return "pacing_lubezki_long_take_flow"
    if "epic" in tones or "war" in tones:
        return "pacing_schoonmaker_momentum"
    if "intimate" in tones or "quiet" in tones:
        return "pacing_slow_build_setup"
    return "pacing_invisible_jcut"


# ─────────────────────────── public API ───────────────────────────────

def suggest_modifiers(script):
    """Analyze a script dict and return modifier suggestions.

    Returns dict with keys: style_dna_tag, audio_dna_tag, music_dna_tag,
    pacing_dna_tag, each containing {recommended, alternatives[], reasoning}.
    """
    analysis = _analyze_content(script)
    ts = analysis["tone_scores"]

    # Format-based defaults
    fmt = script.get("format_id", "narrative-short-film")

    suggestions = {}

    # Visual style
    vis = _best_match(VISUAL_STYLES, ts)
    hyb = _best_match(HYBRID_STYLES, ts)
    ext = _best_match(EXTINCT_STYLES, ts)
    mat = _best_match(MATERIAL_STYLES, ts)
    fus = _best_match(FUSION_STYLES, ts)
    prc = _best_match(PROCEDURAL_STYLES, ts)
    all_visual = vis + hyb + ext + mat + fus + prc
    all_visual.sort(key=lambda x: x[1], reverse=True)
    if all_visual:
        suggestions["style_dna_tag"] = {
            "recommended": all_visual[0][0],
            "score": all_visual[0][1],
            "label": all_visual[0][2],
            "alternatives": [{"id": v[0], "score": v[1], "label": v[2]} for v in all_visual[1:4]],
            "reasoning": f"Top tone signals: {', '.join(sorted(ts, key=ts.get, reverse=True)[:5])}",
        }
    else:
        suggestions["style_dna_tag"] = {
            "recommended": None,
            "reasoning": "No strong tone signals detected — operator should choose manually.",
            "alternatives": [],
        }

    # Audio
    aud = _best_match(AUDIO_STYLES, ts)
    if aud:
        suggestions["audio_dna_tag"] = {
            "recommended": aud[0][0],
            "score": aud[0][1],
            "label": aud[0][2],
            "alternatives": [{"id": a[0], "score": a[1], "label": a[2]} for a in aud[1:3]],
        }
    else:
        suggestions["audio_dna_tag"] = {"recommended": None, "alternatives": []}

    # Music
    mus = _best_match(MUSIC_STYLES, ts)
    if mus:
        suggestions["music_dna_tag"] = {
            "recommended": mus[0][0],
            "score": mus[0][1],
            "label": mus[0][2],
            "alternatives": [{"id": m[0], "score": m[1], "label": m[2]} for m in mus[1:3]],
        }
    else:
        suggestions["music_dna_tag"] = {"recommended": None, "alternatives": []}

    # Pacing
    pacing_id = _suggest_pacing(analysis)
    pacing_info = PACING_STYLES.get(pacing_id, {})
    suggestions["pacing_dna_tag"] = {
        "recommended": pacing_id,
        "label": pacing_info.get("label", ""),
        "reasoning": f"dialogue_ratio={analysis['dialogue_ratio']:.2f}, avg_shot={analysis['avg_duration']:.1f}s",
    }

    # Per-shot camera_move suggestions (from video_prompt content)
    shot_mods = []
    for shot in script.get("shots", []):
        vp = (shot.get("video_prompt", "") or "").lower()
        cam = None
        if any(w in vp for w in ["tracking", "follow", "steadicam"]):
            cam = "tracking"
        elif any(w in vp for w in ["crane", "overhead", "aerial", "bird"]):
            cam = "crane_up"
        elif any(w in vp for w in ["dolly", "push in", "move in"]):
            cam = "dolly_in"
        elif any(w in vp for w in ["pan", "sweep"]):
            cam = "pan"
        elif any(w in vp for w in ["static", "locked", "tripod"]):
            cam = "static"
        shot_mods.append({"shot_id": shot.get("id"), "camera_move": cam})

    suggestions["per_shot_camera"] = [s for s in shot_mods if s["camera_move"]]
    suggestions["_analysis"] = analysis

    return suggestions


def apply_suggestions(script, suggestions, apply_per_shot=True):
    """Apply suggestions to a script dict (mutates in place). Returns script."""
    config = script.setdefault("config", {})

    for tag in ["style_dna_tag", "audio_dna_tag", "music_dna_tag", "pacing_dna_tag"]:
        s = suggestions.get(tag, {})
        rec = s.get("recommended")
        if rec and not config.get(tag):
            config[tag] = rec

    if apply_per_shot:
        shot_map = {s.get("id"): s for s in script.get("shots", [])}
        for sm in suggestions.get("per_shot_camera", []):
            shot = shot_map.get(sm["shot_id"])
            if shot and sm["camera_move"]:
                mods = shot.setdefault("modifiers", {})
                if not mods.get("camera_move"):
                    mods["camera_move"] = sm["camera_move"]

    # Annotate that suggestions were applied
    script["_modifier_suggestions"] = {
        tag: {
            "applied": suggestions.get(tag, {}).get("recommended"),
            "label": suggestions.get(tag, {}).get("label", ""),
            "alternatives": [
                a.get("id") for a in suggestions.get(tag, {}).get("alternatives", [])
            ],
        }
        for tag in ["style_dna_tag", "audio_dna_tag", "music_dna_tag", "pacing_dna_tag"]
    }

    return script


# ─────────────────────────── CLI ──────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Suggest style/audio/music/pacing modifiers for an ingested screenplay."
    )
    parser.add_argument("input", help="Path to ingested script JSON")
    parser.add_argument("-o", "--output", help="Output path (default: print suggestions only)")
    parser.add_argument("--apply", action="store_true", help="Apply suggestions in place (overwrites input)")
    parser.add_argument("--dry-run", action="store_true", help="Show suggestions without applying")

    args = parser.parse_args()

    script = json.loads(Path(args.input).read_text(encoding="utf-8"))
    suggestions = suggest_modifiers(script)

    # Print summary
    print("\n=== Modifier Suggestions ===", file=sys.stderr)
    for tag in ["style_dna_tag", "audio_dna_tag", "music_dna_tag", "pacing_dna_tag"]:
        s = suggestions.get(tag, {})
        rec = s.get("recommended", "none")
        label = s.get("label", "")
        score = s.get("score", "")
        score_str = f" (score={score})" if score else ""
        print(f"  {tag:20s} → {rec}{score_str}  [{label}]", file=sys.stderr)
        for alt in s.get("alternatives", [])[:2]:
            print(f"    alt: {alt.get('id', alt)} (score={alt.get('score','')})", file=sys.stderr)

    cam_suggestions = suggestions.get("per_shot_camera", [])
    if cam_suggestions:
        print(f"\n  Per-shot camera_move: {len(cam_suggestions)} shots", file=sys.stderr)
        for cs in cam_suggestions[:5]:
            print(f"    {cs['shot_id']:30s} → {cs['camera_move']}", file=sys.stderr)

    reasoning = suggestions.get("_analysis", {})
    ts = reasoning.get("tone_scores", {})
    if ts:
        top = sorted(ts, key=ts.get, reverse=True)[:5]
        print(f"\n  Detected tones: {', '.join(f'{t}({ts[t]})' for t in top)}", file=sys.stderr)
    print(f"  Dialogue ratio: {reasoning.get('dialogue_ratio', 0):.0%}", file=sys.stderr)

    if args.dry_run:
        return

    # Apply
    if args.apply or args.output:
        apply_suggestions(script, suggestions)
        out_path = args.output or args.input
        Path(out_path).write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n[modifier_suggester] Written: {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()

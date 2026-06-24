#!/usr/bin/env python3
"""Generate 200 DAVID training pairs: Ancient Greek, Biblical Hebrew, Classical Sanskrit."""
import json
import random

random.seed(42)

pairs = []

def add(instruction, output, inp=""):
    pairs.append({"instruction": instruction, "input": inp, "output": output})

# ── ANCIENT GREEK (67) ──────────────────────────────────────────────────────

ag_pron = [
    ("How should a DAVID tutoring episode teach Attic aspirated stops phi, theta, and chi?",
     "**Ancient Greek — aspirated stops tutoring module:**\n\nFrame phi/theta/chi as breathy-release stops /pʰ tʰ kʰ/, not Modern Greek fricatives. Demo: hold palm before mouth — aspirated stops produce a visible puff; fricatives do not. Contrast pairs: ποτέ [p] vs φόνος [pʰ], τόπος [t] vs θεός [tʰ], καλός [k] vs χορός [kʰ]. Tag [reconstructed] per Allen *Vox Graeca*. Tutoring hook: Attic orators heard a puff English speakers never learn."),
    ("What is the correct IPA for upsilon in Classical Attic Greek and how do you teach it?",
     "**Ancient Greek — upsilon /y/:**\n\nUpsilon υ = French *tu* rounded front [y], not English /u/ or /ʊ/. Minimal pair drill: ὕλη [ýlɛː] 'wood' vs οὐ [uː] 'not'. Lip-round while saying [i]. AI audio defaults to /u/ — flag as common error. Confidence: [reconstructed] high. Source: Allen *Vox Graeca*."),
    ("Explain pitch accent to a beginner learning reconstructed Ancient Greek pronunciation.",
     "**Ancient Greek — pitch accent primer:**\n\nOne high-tone mora per word — musical, not English stress. Acute = high or rising on accented mora; circumflex = falling contour on long accented syllable; grave = low/default or sandhi lowering. Demo with γνῶθι [ɡnôːti]: rising-falling on the long omega. Koine and Byzantine shift to stress accent — label variant on-screen. [reconstructed] confidence high for moraic placement; medium for exact melodic contour."),
    ("How should long vowel quantity be demonstrated in an Ancient Greek pronunciation lesson?",
     "**Ancient Greek — quantity demonstration:**\n\nLong vowels and diphthongs = 2 morae; shorts = 1 mora. Meter depends on it: μῆνιν [mɛ̂ːnin] holds η twice as long as short ε in μένος. Clap-or-tap twice for long, once for short. Iliad opening μῆνιν ἄειδε is the canonical DAVID sample. Never collapse η/ω to Modern i/u. Tag [reconstructed]; inscriptions and metrics attest quantity."),
    ("What tutoring exercise helps students distinguish beta [b] from Modern Greek [v]?",
     "**Ancient Greek — beta drill:**\n\nΒῆτα = voiced bilabial stop [b], identical to English 'b' in 'boy'. Contrast: βίος [bíos] 'life' — if it sounds like 'vios', wrong model. Pair with φίλος [pʰílos] to show stop vs aspirated stop. Tutoring hook: Plato's βήτα was a buzz, not a fricative. [reconstructed] Attic default."),
    ("How do you teach rough breathing (dasia) in Ancient Greek audio production?",
     "**Ancient Greek — rough breathing:**\n\nInitial spiritus asper = [h] before vowel: Ἑλλάς [hɛlás], ἄνθρωπος [án.tʰrɔː.pos]. Smooth breathing = zero onset. AI often drops [h] entirely or over-aspirates. Grok Imagine note: light [h], not English 'hue' cluster. Grammatical tradition attests marking; phonetic value [reconstructed] high."),
    ("What is the DAVID-recommended approach to teaching zeta in Attic Greek?",
     "**Ancient Greek — zeta:**\n\nAttic scholarly default: ζ = [zd] as in 'wisdom' (σοφία → σοφίζω cluster logic). Alternate [dz] debated. Teach both with [hypothesis] tag; default [zd] for DAVID Attic episodes. AI renders as /z/ fricative — document as error. Source: Allen; inscriptional evidence mixed."),
    ("How should eta (η) be taught versus modern iotacized pronunciation?",
     "**Ancient Greek — eta:**\n\nClassical η = long open mid-front [ɛː], distinct from ε [e] and ι [i]. Ὅμηρος [hɔ́mɛːros] — hold the vowel. Iotacism merges η→/i/ by Koine; label Koine variant separately. Tutoring hook: η is why Ἀθῆναι and Modern Αθήνα sound nothing alike in Classical render."),
]

ag_phone = [
    ("What are the distinctive phonological features of Attic Classical Greek?",
     "**Ancient Greek — distinctive features:**\n\nThree-way stop contrast (plain/aspirated/voiced); phonemic vowel quantity; pitch accent; rough vs smooth breathing; /y/ upsilon; geminate consonants in spelling. No soft consonants. Zeta realization disputed. Revival tier: active (liturgical/scholarly continuity)."),
    ("Describe the Ancient Greek vowel system for a pronunciation profile.",
     "**Ancient Greek — vowels:**\n\nShort: /a e i y o/; Long: /aː ɛː eː iː yː ɔː uː/ plus diphthongs (αι, αυ, ει, ευ, οι, ου, etc.). ει/ου monophthongize early. Quantity is moraic and metrical. [reconstructed] from metrics + grammarians."),
    ("What consonant contrasts define Ancient Greek against English?",
     "**Ancient Greek — consonant contrasts:**\n\nAspirated stops /pʰ tʰ kʰ/; voiced /b d g/; voiceless /p t k/; trilled ρ; no English /ŋ/ as phoneme; ξ = [ks], ψ = [ps]. Fricatives mainly σ, ϝ lost in Attic text but metrically present in Homer."),
    ("How does Koine Greek phonology differ from Attic for DAVID variant labeling?",
     "**Ancient Greek — Koine shifts:**\n\nSpirantization: φ→/f/, θ→/θ/, χ→/x/; iotacism spreads; rough breathing lost; pitch accent → stress. Papyri attest timing. Label 'Koine' on-screen when using fricatives. Attic remains DAVID documentary default."),
    ("What role does the digamma (ϝ) play in Homeric Greek phonology?",
     "**Ancient Greek — digamma:**\n\nϝ = /w/ preserved metrically in Homer but omitted in standard texts. Explains hiatus and syllable count: οἶνος vs ϝοῖνος. [reconstructed] from metrics. Tutoring hook: Homer had a 'w' Greek lost from spelling."),
    ("Explain the moraic structure underlying Ancient Greek hexameter.",
     "**Ancient Greek — moraic meter:**\n\nShort vowel = 1 mora; long vowel or diphthong = 2; consonant cluster may close syllable for weight. Dactylic hexameter: – ⏑ ⏑ | – ⏑ ⏑ | – ⏑ ⏑ | – ⏑ ⏑ | – ⏑ ⏑ | – –. Pronunciation lesson must preserve quantity or rhythm collapses."),
    ("What is iotacism and when does it affect Ancient Greek corpus reading?",
     "**Ancient Greek — iotacism:**\n\nHistorical merger of η, ι, υ, ει, οι, etc. toward /i/. Post-Classical; full by Byzantine. Reading Plato in Modern Greek pronunciation erases vowel contrasts Attic speakers heard. Corpus entries should note period-appropriate vowel values."),
    ("How does Allen's Vox Graeca inform DAVID's Ancient Greek reconstruction?",
     "**Ancient Greek — Allen standard:**\n\n*Vox Graeca* (3rd ed. 1987) is DAVID's Attic default: aspirates as stops, quantity from metrics, pitch from grammarians. Confidence 85–90% on core inventory. Cross-check atticgreek.org and inscriptional data for disputed fields."),
]

ag_ai = [
    ("What phonological mistakes does AI audio typically make when generating Ancient Greek speech?",
     "**Ancient Greek — common AI audio errors:**\n\n1. Phi/theta/chi as /f θ x/ (Modern) not /pʰ tʰ kʰ/\n2. Beta as /v/ not /b/\n3. Upsilon as /u/ not /y/\n4. Eta/omega collapsed to Modern vowels\n5. Pitch accent rendered as English stress\n6. Rough breathing dropped\n7. Short/long quantity equalized\n8. Zeta as plain /z/ not [zd]\n\nGrok Imagine fix: explicit puff on aspirates, hold longs 2×, sing accent contour."),
    ("How should DAVID correct AI audio that pronounces φιλία with an /f/ onset?",
     "**Ancient Greek — AI correction (φ):**\n\nφιλία [pʰilía] requires stop+/h/ release, not /f/. Regenerate with guidance: 'phi = p with audible breath burst, never f'. Compare audio to πίστις [pístis] for puff contrast. Tag output [reconstructed]."),
    ("What Grok Imagine parameters prevent Modern Greek vowel coloring in Attic samples?",
     "**Ancient Greek — vowel AI guardrails:**\n\nSpecify: pure cardinal vowels; η = [ɛː] not [i]; ω = [ɔː] not [o]; upsilon = [y]. Avoid: 'Modern Greek pronunciation'. Request hexameter pacing with mora timing. On-screen: 'Attic Classical [reconstructed]'."),
    ("Why do TTS systems fail on Ancient Greek pitch accent and how does DAVID compensate?",
     "**Ancient Greek — pitch accent AI gap:**\n\nTTS maps accent marks to stress + volume, not tone. DAVID workaround: annotate accented mora with slight F0 rise in Grok Imagine script; use circumflex fall on long syllables; accept approximate contour — label [reconstructed] medium confidence on melody."),
    ("Document AI error patterns for rho in Ancient Greek audio generation.",
     "**Ancient Greek — rho AI errors:**\n\nSystems use English approximant /ɹ/ or flap. Attic expects trilled [r]; initial rho often voiceless in some reconstructions. Instruct: 'alveolar trill, not English r'. Reference Italian/Spanish rolled r. Disputed: voiceless initial — tag [hypothesis] if used."),
]

ag_trans = [
    ("What translation methodology should DAVID apply to Ancient Greek philosophical texts?",
     "**Ancient Greek — translation methodology:**\n\n1. Corpus-first: establish lemma from TLG/Perseus attestation\n2. Period register: Classical vs Koine vs Byzantine Greek differ\n3. Polysemy chains: log contextual senses (λόγος, ἀρετή, εὐδαιμονία)\n4. Never Anglicize technical terms without gloss on first occurrence\n5. Return-to-Greek check: re-translate English draft for semantic drift\n6. Tag [attested] for manuscript readings; [reconstructed] for emendations"),
    ("How should a translator handle particles (γάρ, δέ, μέν, οὖν) in Ancient Greek?",
     "**Ancient Greek — particles:**\n\nParticles carry discourse logic, not lexical content. Avoid deleting δέ/γάρ in English — use punctuation, 'now', 'but', 'for' strategically. Over-literal stacking sounds unnatural; under-translation loses argument structure. DAVID flags particle loss in QA pass."),
    ("What are the register risks when translating Attic oratory vs Koine narrative?",
     "**Ancient Greek — register:**\n\nAttic oratory: periodic sentences, deliberate rhythm — English must not flatten into bullet prose. Koine (NT, Josephus): parataxis, simpler syntax — avoid faux-Attic elevation. Identify period before choosing English register."),
    ("How does DAVID tag uncertainty in Ancient Greek textual emendation during translation?",
     "**Ancient Greek — emendation tags:**\n\nBracketed conjectures: [ἀνθρώπων] with footnote 'text uncertain; preferred emendation West'. Never present conjecture as [attested]. Paleographic notes in corpus entry. Translation notes: 'sense depends on emended verb'."),
]

ag_corpus = [
    ("What corpora should DAVID prioritize for Ancient Greek attestation surveys?",
     "**Ancient Greek — corpus priorities:**\n\nTLG (Thesaurus Linguae Graecae); Perseus Digital Library; PHI Greek Inscriptions; papyri via papyri.info; LSJ for lexicography. Epic: Homer (Iliad/Odyssey); philosophy: Plato, Aristotle; drama: Aeschylus, Sophocles, Euripides. Date and genre metadata required per entry."),
    ("Produce a DAVID research query for expanding Ancient Greek epic corpus coverage.",
     "**Ancient Greek — research query:**\n\n'Extract Iliad Book 1 lines 1–50 with scholia variants; map digamma-positions from metrical analysis; cross-reference Venetus A facsimile readings; output corpus blocks with [attested] confidence and Allen IPA.' Queue via research_query_generator.py --language ancient-greek"),
    ("How should DAVID situate the Delphic maxim γνῶθι σεαυτόν in corpus context?",
     "**Ancient Greek — corpus entry context:**\n\n**Text:** γνῶθι σεαυτόν\n**Source:** Chilon of Sparta, via Diogenes Laertius 1.40 [attested literary transmission]\n**Type:** gnomic maxim\n**IPA:** [ɡnôːti seautón] [reconstructed Attic]\n**Note:** Secure philosophical quotation; pronunciation is reconstruction, not Modern Greek."),
    ("What forensic steps does DAVID take when a Greek inscription reading is disputed?",
     "**Ancient Greek — inscription forensics:**\n\n1. Photograph/epigraphic squeeze examination\n2. Compare IG edition apparatus\n3. Note letter forms (sigma lunatum vs four-bar)\n4. Paleographic date from ductus\n5. Tag reading [attested] vs [hypothesis]\n6. Never build morphology tables on unverified joins"),
]

ag_script = [
    ("What romanization standard should DAVID use for Ancient Greek in tutoring materials?",
     "**Ancient Greek — romanization:**\n\nBeta-code or ALA-LC for library work; pedagogical materials: acute accents preserved, aspirates as ph/th/ch, long vowels with macron (ē, ō) or doubled vowel. Never use Modern Greek orthography for Classical lessons. Example: θεός theós, not theos without breathing/accent when teaching."),
    ("How do breathing marks function in Ancient Greek script pedagogy?",
     "**Ancient Greek — breathing pedagogy:**\n\nTeach as phonemic onset markers: rough = /h/, smooth = ∅. Ἑλλάς vs Ἑλλάς error if smooth. Unicode: U+1F00–U+1F07 polytonic. Tutoring episode: show manuscript without breathings → later polytonic addition by Alexandrian scholars."),
    ("Explain the Greek alphabet order and names for a DAVID script episode.",
     "**Ancient Greek — alphabet episode:**\n\n24 letters; names: ἄλφα, βῆτα (beta [b]!), γάμμα… ωμέγα. Hook: omega means 'big o' vs omicron 'small o' — length distinction encoded in letter names. Digamma, san, koppa archaic — mention for epichoric scripts."),
    ("How should polytonic accent marks be introduced in Ancient Greek tutoring?",
     "**Ancient Greek — polytonic intro:**\n\nThree accents (acute, grave, circumflex) + two breathings + iota subscript. Teach function before memorization: accent = pitch target; breathing = /h/ or none. Modern monotonic is post-1982 — not for Classical reconstruction modules."),
]

ag_tutor = [
    ("Outline a 5-episode DAVID tutoring arc for Ancient Greek phonology.",
     "**Ancient Greek — series arc:**\n\nEp1: Alphabet + aspirates (the puff demo)\nEp2: Vowel quantity + meter clap-along (μῆνιν ἄειδε)\nEp3: Pitch accent singing exercise\nEp4: Consonant clusters + zeta debate\nEp5: Attic vs Koine variant showcase (same sentence, two models)\nEach episode: one tutoring hook, one attested text anchor, [reconstructed] label on audio."),
    ("What is a memorable tutoring hook for Ancient Greek phi/theta/chi?",
     "Attic Greeks heard a miniature explosion after p, t, k — English 'ph' in 'phone' is a lie about Classical phi."),
    ("Generate a tutoring hook for a video episode using the Iliad opening as anchor.",
     "Hook: *μῆνιν ἄειδε θεά* opens Western literature with a long vowel you can literally count — two morae on μῆνιν or the hexameter breaks.\n\n**Scaffold:** present text → IPA → mora tap-along → wrath semantics → [reconstructed] Attic audio"),
    ("What surprising fact about Ancient Greek beta should open a tutoring episode?",
     "Classical βῆτα sounded like English 'b' — Modern Greek 'v' is a medieval shift students never expect."),
]

for p in ag_pron + ag_phone + ag_ai + ag_trans + ag_corpus + ag_script + ag_tutor:
    add(p[0], p[1])

# Pad AG to 67
ag_extra = [
    ("How does DAVID label Byzantine Greek pronunciation variants?",
     "**Ancient Greek — Byzantine variant:**\n\nStress accent replaces pitch; iotacism complete; φ/θ/χ as fricatives; η/ι/υ → /i/. Label 'Byzantine' explicitly. Do not use for Plato/Sophocles default. Manuscript continuity [attested]; exact chronology [hypothesis] in transition zones."),
    ("What pacing notes apply to Ancient Greek hexameter narration in documentary audio?",
     "**Ancient Greek — hexameter pacing:**\n\nCaesura breath at penthemimeral position; preserve mora count; slight pitch rise on accented mora. Do not rush dactyls into English trochees. Sample: μῆνιν ἄειδε θεά — pause after ἄειδε."),
]
for p in ag_extra:
    add(p[0], p[1])

# ── BIBLICAL HEBREW (67) ──────────────────────────────────────────────────────

bh_pron = [
    ("How should DAVID teach Tiberian gutturals in Biblical Hebrew pronunciation?",
     "**Biblical Hebrew — gutturals:**\n\nʿayin ע = deep pharyngeal [ʕ] (Arabic ع reference); ḥet ח = voiceless pharyngeal [ħ]~[x]; aleph א = glottal stop [ʔ]. Modern Hebrew largely lost these — authenticity requires explicit coaching. Khan *Tiberian Pronunciation Tradition* is DAVID default. [reconstructed] high confidence."),
    ("What is the correct treatment of begadkefat in Biblical Hebrew audio lessons?",
     "**Biblical Hebrew — begadkefat:**\n\nWithout dagesh: ב→[v], כ→[x], פ→[f] (spirantization). With dagesh lene: stops [b],[k],[p]. Dagesh forte doubles consonant audibly. Drill: בָּרָא [baːˈʁaː] (stop) vs בֹּקֶר [boːˈqɛr] contexts vary — follow niqqud. Tag [reconstructed] Tiberian."),
    ("How do you teach sheva mobile vs sheva na in Tiberian Hebrew?",
     "**Biblical Hebrew — sheva:**\n\nMobile sheva = [ə] or reduced vowel between consonants; silent sheva (nach) = zero — syllable restructures. Genesis 1:1 בְּרֵאשִׁית [bə.ʁeː...] shows mobile. Rules depend on position, guttural neighbors, meteg. Khan Ch. 3–5 for full table. AI flattens to schwa everywhere — error."),
    ("Explain cantillation (te'amim) for Biblical Hebrew tutoring audio.",
     "**Biblical Hebrew — cantillation:**\n\nTa'amim are musical-phrasing marks — not decorative. Sof pasuq = cadence; etnachta = half-verse pause; zaqef = minor disjunction. Pronunciation lesson must chant, not flat-read. Foreman/Khan recordings as reference. [attested] in Masoretic tradition."),
    ("How should resh be taught in Tiberian Biblical Hebrew?",
     "**Biblical Hebrew — resh:**\n\nUvular [ʁ] or trilled — not Modern Israeli alveolar flap. Distinct from Greek rho pedagogy but similar trill coaching. Comparative: Arabic غ/ر articulation drills. [reconstructed] with Samaritan comparative support. Dispute: uvular vs alveolar trill — tag both."),
    ("What vowel length distinctions matter in Tiberian Biblical Hebrew?",
     "**Biblical Hebrew — vowel length:**\n\nNiqqud encodes quality and length: qameṣ gadol [aː] vs qameṣ qatan [ɔ]; ḥireq long [iː] in some positions. Babylonian tradition simplifies — label variant. Khan for Tiberian defaults."),
    ("How does DAVID teach dagesh forte audibly in Biblical Hebrew tutoring?",
     "**Biblical Hebrew — dagesh forte:**\n\nGemination: consonant held longer/closer — סַבָּל [sabːal] 'porter'. Contrast single vs double in minimal pairs. AI often ignores gemination — flag. Metrical and morphological function [attested] in Masoretic text."),
    ("What is the DAVID default pronunciation tradition for Biblical Hebrew documentary audio?",
     "**Biblical Hebrew — default tradition:**\n\nTiberian (Galilee Masoretes), Khan reconstruction. NOT Modern Israeli unless episode compares variants. On-screen: 'Tiberian [reconstructed]'. Samaritan and Babylonian in comparison modules only."),
]

bh_phone = [
    ("What are the distinctive phonological features of Biblical Hebrew?",
     "**Biblical Hebrew — distinctive features:**\n\nGutturals/pharyngeals; begadkefat spirantization; phonemic consonant gemination (dagesh forte); sheva mobile/silent; matres lectionis in consonantal text; stress penultimate/ultimate governed by cantillation."),
    ("Compare Tiberian, Babylonian, and Samaritan Hebrew vowel systems for DAVID.",
     "**Biblical Hebrew — tradition comparison:**\n\n| Tradition | Vowels | Notes |\n|Tiberian| Full niqqud, length detail | DAVID default |\n|Babylonian| Simpler, fewer length contrasts | Tag when citing |\n|Samaritan| Different qualities, archaic consonants | Oral living reference for gutturals |"),
    ("How do emphatic consonants appear in Biblical Hebrew phonology?",
     "**Biblical Hebrew — emphatics:**\n\nṢade צ, ṭet ט, qof ק — traditionally emphatic/uvularized vs plain series. Comparative Semitic evidence. Pronunciation [reconstructed]; articulatory coaching: heavier contact, posterior tongue."),
    ("What role do matres lectionis play in Biblical Hebrew corpus reading?",
     "**Biblical Hebrew — matres lectionis:**\n\nה, ו, י mark vowels in consonantal text (plene spelling). Forensic reading: compare DSS plene vs defective. Affects syllable count and stress assignment. Never vocalize without manuscript justification."),
    ("Describe the Tiberian consonant inventory for a pronunciation profile.",
     "**Biblical Hebrew — consonants:**\n\nʾ ḥ ʿ; b v g d h w z ḥ ṭ y k x l m n s ʿ p f ṣ q r š ś t. Begadkefat alternations. Sin/shin distinction שׂ/שׁ [ś]/[ʃ]. [reconstructed] with high confidence on contrasts."),
]

bh_ai = [
    ("What phonological mistakes does AI audio typically make when generating Biblical Hebrew speech?",
     "**Biblical Hebrew — common AI audio errors:**\n\n1. Gutturals (ʿayin, ḥet) dropped or anglicized\n2. Modern Israeli resh/r instead of uvular/trill\n3. Begadkefat spirantization ignored\n4. Sheva always pronounced or always silent wrong\n5. Cantillation flattened to monotone\n6. Dagesh forte gemination absent\n7. Qameṣ qatan vs gadol collapsed\n8. Stress on wrong syllable ignoring trope\n\nFix: Khan IPA + trope-aware phrasing in Grok Imagine script."),
    ("How should DAVID correct AI that reads בְּרֵאשִׁית with Modern Hebrew phonology?",
     "**Biblical Hebrew — AI correction:**\n\nRegenerate with Tiberian guidance: uvular resh, pharyngeal ʿayin in אֱלֹהִים contexts, mobile sheva [ə], long qameṣ in בָּרָא. Label 'NOT Modern Hebrew'. Reference Khan IPA /bə.ʁeː.ˈʔiː.ʃiːt̪/."),
    ("What Grok Imagine guidance prevents cantillation loss in Hebrew audio?",
     "**Biblical Hebrew — cantillation AI:**\n\nScript must include trope names at pauses: 'etnachta — falling cadence; sof pasuq — full stop melody'. Request chant-like prosody, not conversational Israeli. Foreman recitation as style reference. [reconstructed] performance tradition."),
    ("Document AI failure on Biblical Hebrew pharyngeal ʿayin.",
     "**Biblical Hebrew — ʿayin AI gap:**\n\nTTS substitutes glottal stop, zero, or /n/. Coach: 'deep pharyngeal constriction, Arabic ع'. Visual: hand on throat showing constriction below larynx. Mark [reconstructed]; comparative Arabic required for actor coaching."),
]

bh_trans = [
    ("What translation methodology should DAVID apply to Biblical Hebrew poetry?",
     "**Biblical Hebrew — poetry translation:**\n\n1. Preserve parallelism (synonymous, antithetic, synthetic)\n2. Don't pad lines for English meter — parallelism is the architecture\n3. Verbal aspect (qatal/yiqtol) not equal to past/future — use contextual English tense\n4. Repetition is rhetorical, not redundancy — keep it\n5. Tag divine names (YHWH/LORD) per client convention\n6. Corpus: WLC/DSS variants in apparatus"),
    ("How should a translator handle the Hebrew construct state?",
     "**Biblical Hebrew — construct:**\n\nסֵפֶר דָּוִד = 'book of David' — two nouns, first unmarked. English needs 'of'; don't insert articles not in Hebrew. Chain constructs: בֵּית יְהוָה אֱלֹהֵי יִשְׂרָאֵל — preserve linkage without over-embedding."),
    ("What are the register risks translating Biblical Hebrew prophetic discourse?",
     "**Biblical Hebrew — prophetic register:**\n\nHigh metaphor density; formulaic messenger speech ('thus says YHWH'); abrupt tense shifts. Avoid homiletical smoothing. Footnote cultural items (ephod, teraphim). DAVID flags theological term consistency across book."),
    ("How does DAVID manage textual variants between MT and Dead Sea Scrolls in translation?",
     "**Biblical Hebrew — variant methodology:**\n\nApparatus entry per variant: '4QGenᵇ reads X; MT reads Y; prefer MT [attested] unless DSS superior lectio'. Translation note when sense changes. Never silently adopt DSS without editorial policy flag."),
]

bh_corpus = [
    ("What corpora should DAVID prioritize for Biblical Hebrew attestation?",
     "**Biblical Hebrew — corpus priorities:**\n\nWestminster Leningrad Codex (WLC); Biblia Hebraica Stuttgartensia; Dead Sea Scrolls (Leon Levy, DSS consortium); Inscriptions (Mesha Stele, Siloam); Samaritan Pentateuch; Ben Sira fragments. Always cite verse address + manuscript."),
    ("Produce a DAVID corpus entry for Genesis 1:1.",
     "**Biblical Hebrew — corpus entry:**\n\n**Text:** בְּרֵאשִׁית בָּרָא אֱלֹהִים\n**Romanization:** bərēʾšît bārāʾ ʾĕlōhîm\n**Translation:** In the beginning God created…\n**Source:** WLC Genesis 1:1 [attested]\n**IPA:** /bə.ʁeː.ˈʔiː.ʃiːt̪ baː.ˈʁaː ʔɛ.loː.ˈhiːm/ [reconstructed Tiberian]\n**Notes:** DAVID Post 7 hook line."),
    ("What research query should DAVID queue for Biblical Hebrew cantillation corpus expansion?",
     "**Biblical Hebrew — research query:**\n\n'Map te'amim melodies for Genesis 1–3 per Leningrad Codex; cross-reference Khan accentuation rules; extract audio-reference timestamps from Foreman recordings; output tutoring blocks with trope names and [attested] Masoretic marks.'"),
    ("How does DAVID forensically analyze a Biblical Hebrew inscription vs MT spelling?",
     "**Biblical Hebrew — inscription forensics:**\n\nCompare letter forms (paleo-Hebrew vs square); note final forms absent in epigraphy; matres lectionis patterns; dialect features (Moabite, Ammonite). Tag period. Do not normalize inscription to MT without justification."),
]

bh_script = [
    ("How should DAVID teach the Hebrew abjad in a tutoring episode?",
     "**Biblical Hebrew — abjad pedagogy:**\n\n22 consonants; vowels added via niqqud (Masoretic). Teach consonantal skeleton first: שלום → SH-L-M. Hook: Hebrew was written without vowels for centuries — readers carried oral tradition. DSS show pre-Masoretic stage."),
    ("What romanization system should DAVID use for Biblical Hebrew?",
     "**Biblical Hebrew — romanization:**\n\nSBL Academic: ʾ b g d h w z ḥ ṭ y k l m n s ʿ p ṣ q r š t; dot under for emphatics; line under for ḥ/ṭ/ṣ. Example: bərēʾšît. Avoid ASCII hacks in published materials. IPA parallel in pronunciation modules."),
    ("Explain niqqud pedagogy for Biblical Hebrew learners.",
     "**Biblical Hebrew — niqqud:**\n\nVowel points (qubbutz, qameṣ, ḥireq, etc.) + dagesh + shuruq. Teach as Tiberian overlay (~7th–10th c. CE), not original autographs. Students read unpointed text only after pointed mastery. Unicode Hebrew block + cantillation marks."),
    ("How do final letter forms (sofit) feature in Biblical Hebrew script teaching?",
     "**Biblical Hebrew — sofit:**\n\nכ→ך, מ→ם, נ→ן, פ→ף, צ→ץ at word end. Pedagogical drill: same phoneme, positional allograph — not a different sound. Epigraphic Hebrew lacks final forms in some periods."),
]

bh_tutor = [
    ("Outline a DAVID tutoring arc for Biblical Hebrew pronunciation.",
     "**Biblical Hebrew — series arc:**\n\nEp1: Consonantal alphabet + gutturals (Arabic reference clips)\nEp2: Begadkefat spirantization drills\nEp3: Sheva rules + Genesis 1:1 walkthrough\nEp4: Cantillation chant (torah trope basics)\nEp5: Tiberian vs Modern Israeli comparison\nHooks: Masoretes as medieval phoneticians; trope as sheet music."),
    ("What tutoring hook opens a Biblical Hebrew gutturals episode?",
     "Biblical Hebrew had throat sounds Modern Israelis deleted — ʿayin and ḥet distinguish roots that look identical on paper."),
    ("Generate a lesson scaffold for teaching בְּרֵאשִׁית בָּרָא אֱלֹהִים.",
     "**Biblical Hebrew — lesson scaffold:**\n\n1. Display consonantal skeleton בראשית ברא אלהים\n2. Add niqqud layer — explain Masoretic addition\n3. Syllable breakdown with sheva mobile\n4. IPA per Khan\n5. Chant with sof pasuq cadence\n6. Compare Modern Israeli reading — label differences\n7. Tag [attested] text, [reconstructed] phonology"),
    ("What surprising fact about cantillation should anchor a Biblical Hebrew episode?",
     "The te'amim are a thousand-year-old musical score for scripture — not punctuation you can ignore in authentic recitation."),
]

for p in bh_pron + bh_phone + bh_ai + bh_trans + bh_corpus + bh_script + bh_tutor:
    add(p[0], p[1])

bh_extra = [
    ("How should DAVID present Samaritan Hebrew in a variant-comparison tutoring module?",
     "**Biblical Hebrew — Samaritan module:**\n\nLiving oral tradition; archaic gutturals preserved differently; vowel shifts from Tiberian. Use for comparative hook, not default documentary read. Ben-Hayyim as source. Label 'Samaritan tradition' on-screen."),
    ("What forensic note applies to reading Biblical Hebrew without niqqud?",
     "**Biblical Hebrew — unpointed reading:**\n\nRequires morphological analysis + context for vowels — homographs abound. DAVID treats unpointed vocalization as [hypothesis] unless tradition fixes reading (e.g., Qere/Ketiv). Never present guess as [attested]."),
    ("Provide IPA for אֱלֹהִים in Tiberian reconstruction.",
     "**Biblical Hebrew — IPA:**\n\nאֱלֹהִים: /ʔɛ.loː.ˈhiːm/\n**Model:** Tiberian Khan\n**Confidence:** [reconstructed] high\n**Note:** Initial glottal stop; long ô from ḥolam; stress on ultima per cantillation context."),
    ("What pacing applies to Biblical Hebrew liturgical recitation in documentary audio?",
     "**Biblical Hebrew — liturgical pacing:**\n\nPhrase-bound by te'amim; etnachta breath; deliberate, not conversational speed. Sof pasuq full cadence before next verse. Khan/Foreman timing reference. Avoid Israeli news-reader tempo."),
]
for p in bh_extra:
    add(p[0], p[1])

# ── CLASSICAL SANSKRIT (66) ─────────────────────────────────────────────────

sa_pron = [
    ("How should DAVID teach Sanskrit retroflex consonants in pronunciation tutoring?",
     "**Classical Sanskrit — retroflexes:**\n\nṭ, ṭh, ḍ, ḍh, ṇ, ṣ: tongue tip curled to post-alveolar/palatal dome. Contrast dental त [t̪] vs retroflex ट [ʈ] — minimal pair drill: तट 'shore' vs टट 'click'. AI defaults to English alveolar /t/ — wrong. Shiksha precision [attested] in native tradition."),
    ("What is the correct pedagogy for Sanskrit aspirated stops (mahāprāṇa)?",
     "**Classical Sanskrit — aspirates:**\n\nEvery varga has unaspirated + aspirated: क/ख, च/छ, ट/ठ, त/थ, प/फ. Aspirate = audible breath burst after release. Demo: candle flame test — ph extinguishes, p does not. Pāṇinīya Śikṣā describes explicitly. [attested] articulatory tradition."),
    ("How do you teach vowel length in Classical Sanskrit audio lessons?",
     "**Classical Sanskrit — length:**\n\nā, ī, ū held ~2× short a, i, u. Phonemic: minimal pairs change meaning. Drill: कमल kamala 'lotus' vs काम kāmā. AI equalizes length — flag error. Devanagari marks long vowels with vertical stroke."),
    ("Explain sandhi pedagogy for continuous Sanskrit speech.",
     "**Classical Sanskrit — sandhi:**\n\nExternal sandhi at word boundaries mandatory in fluent speech: na + asti → nāsti. Internal sandhi in compounds. Teach rules before fluent recitation. Pāṇini Aṣṭādhyāyī is [attested] rule source. Tutoring: build phrase slowly, then merge."),
    ("How should ṛ (vocalic r) be taught in Sanskrit pronunciation?",
     "**Classical Sanskrit — ṛ:**\n\nSyllabic resonant, tongue-tip retroflex position without full vowel. Similar to English 'bird' without schwa — but precise duration matters. Long ṝ rare. Whitney/MacDonell for drills. AI uses /ru/ or /ri/ — document as error."),
    ("What Vedic accent marks should DAVID teach for sacred text recitation?",
     "**Classical Sanskrit — Vedic accent:**\n\nUdātta (raised), anudātta (not raised), svarita (falling on long). Relevant for Rig Veda pedagogy; Classical Sanskrit prose less accent-marked. Living pandit tradition [attested] for Vedic. Label 'Vedic recitation' vs 'Classical citation' separately."),
    ("How does DAVID teach dental vs retroflex sibilants (ś vs ṣ vs s)?",
     "**Classical Sanskrit — sibilants:**\n\nश ś = palato-alveolar [ɕ]; ष ṣ = retroflex [ʂ]; स s = dental [s]. Three-way contrast unique to Sanskrit. Drill: विश vs विष (different roots). AI collapses to /ʃ/ — wrong."),
    ("What is the DAVID default model for Classical Sanskrit pronunciation?",
     "**Classical Sanskrit — default model:**\n\nPāṇini + Śikṣā standard, confirmed by living pandit recitation. NOT modern Hindi-influenced college Sanskrit unless labeled. Confidence: very_high. On-screen: 'Classical Sanskrit [attested articulatory tradition]'."),
]

sa_phone = [
    ("What are the distinctive phonological features of Classical Sanskrit?",
     "**Classical Sanskrit — distinctive features:**\n\nFive vargas of stops (voiceless/voiced × unaspirated/aspirated + nasal); retroflex series; dental vs retroflex contrast; phonemic vowel length; syllabic ṛ/ḷ; sandhi at boundaries; visarga and anusvāra allophony."),
    ("Describe the Sanskrit varga system for a pronunciation profile.",
     "**Classical Sanskrit — vargas:**\n\nVelar: क ख ग घ ङ; Palatal: च छ ज झ ञ; Retroflex: ट ठ ड ढ ण; Dental: त थ द ध न; Labial: प फ ब भ म. Each row = same place, shared manner features. Pedagogical grid is core tutoring scaffold."),
    ("How does anusvāra (ं) behave phonologically in Sanskrit?",
     "**Classical Sanskrit — anusvāra:**\n\nNasalization + place assimilation to following stop: संग [səŋɡ], संच [səɲc]. Pronunciation varies by context — Śikṣā rules [attested]. AI uses generic /m/ — oversimplified."),
    ("What is visarga (ः) and how should it be pronounced?",
     "**Classical Sanskrit — visarga:**\n\nVoiceless aspiration after vowel: -aḥ [əh], often [h] or echo of preceding vowel quality. Pre-pause allophone. Teach with pause demos. Pāṇini 8.3 rules govern sandhi outcomes."),
]

sa_ai = [
    ("What phonological mistakes does AI audio typically make when generating Sanskrit speech?",
     "**Classical Sanskrit — common AI audio errors:**\n\n1. Retroflexes → English alveolars\n2. Aspirates weakened or absent\n3. Vowel length equalized\n4. ṛ as /ri/ not syllabic retroflex\n5. Dental s vs palatal ś collapsed\n6. Sandhi ignored at boundaries\n7. Anusvāra as always /m/\n8. English schwa in unstressed syllables\n\nFix: Śiksha articulation prompts + pandit reference audio."),
    ("How should DAVID correct AI that pronounces क्षेत्र with English /k/ and /sh/?",
     "**Classical Sanskrit — AI correction:**\n\nक्षेत्र kṣetra = [kʂeːt̪rə] — retroflex ṣ [ʂ], not palatal ś. Regenerate: 'k + retroflex sh, long e, dental tr'. Reference Bhagavad Gita 1.1 धर्मक्षेत्रे."),
    ("What Grok Imagine guidance preserves Sanskrit aspirate contrasts?",
     "**Classical Sanskrit — aspirate AI:**\n\nExplicit: 'ph = p + strong breath burst; bh = b + breath; never reduce to unaspirated'. Side-by-side: पाल vs फाल. Request candle-extinguish metaphor in voice direction. Tag [attested] from Śikṣā."),
    ("Document AI failure on Sanskrit sandhi in continuous phrases.",
     "**Classical Sanskrit — sandhi AI gap:**\n\nTTS reads word-by-word: na asti instead of nāsti. Script must merge graphically: नास्ति with sandhi rule caption. Living pandit recitation as timing reference."),
]

sa_trans = [
    ("What translation methodology should DAVID apply to Classical Sanskrit texts?",
     "**Classical Sanskrit — translation methodology:**\n\n1. Identify register: śastra vs kāvya vs Vedic\n2. Parse compounds (samāsa) before translating — don't guess division\n3. Dhātu semantics: verb roots carry core meaning — use Monier-Williams + context\n4. Retain technical terms (dharma, karma, mokṣa) with first-occurrence gloss\n5. Flag untranslatable aesthetic devices (śleṣa, yamaka)\n6. Corpus: GRETIL, SARIT, critical editions"),
    ("How should a translator handle Sanskrit compound nouns?",
     "**Classical Sanskrit — compounds:**\n\nResolve right-headed tatpuruṣa, dvandva pairs, bahuvrīhi 'one with X'. Example: राजपुरुष = rāja-puruṣa 'king's man'. English often needs reordering — flag interpretive leaps. Pāṇini compound classes guide analysis [attested]."),
    ("What register risks apply to translating Sanskrit śāstra vs poetry?",
     "**Classical Sanskrit — register:**\n\nŚāstra: precision, defined terms, no lyrical padding in English. Kāvya: preserve figurative density — don't flatten metaphors to prose. Vedic: archaisms, sandhi-affected forms — footnote morphology."),
    ("How does DAVID tag uncertainty in Sanskrit manuscript readings?",
     "**Classical Sanskrit — manuscript tags:**\n\nCritical edition apparatus: 'Kashmiri recension reads X; Devanāgarī Y [attested]'. Emendations [hypothesis]. Never build grammar from single manuscript without stemma."),
]

sa_corpus = [
    ("What corpora should DAVID prioritize for Classical Sanskrit attestation?",
     "**Classical Sanskrit — corpus priorities:**\n\nGRETIL; SARIT; Rig Veda (Śākala recension); Mahābhārata critical edition; Pāṇini Aṣṭādhyāyī; Kātyāyana Vārttika; major Upanishads. Date recension; note oral vs written transmission."),
    ("Produce a DAVID corpus entry for Rig Veda 1.1.1 opening.",
     "**Classical Sanskrit — corpus entry:**\n\n**Text:** अग्निमीळे पुरोहितं\n**Romanization:** agnim īḷe purohitam\n**Translation:** I praise Agni, the priest…\n**Source:** RV 1.1.1 [attested]\n**Note:** Vedic accent marks in some padapāṭha traditions; pronunciation per Śikṣā [reconstructed Vedic phonology]"),
    ("What research query should DAVID queue for Sanskrit Śikṣā phonetics expansion?",
     "**Classical Sanskrit — research query:**\n\n'Extract Pāṇinīya Śikṣā articulatory descriptions for retroflex vs dental; map to Devanagari akṣara inventory; cross-reference living pandit demonstration videos; output disputed_phonemes.json entries with [attested] Śikṣā citations.'"),
    ("How does DAVID forensically compare Vedic padapāṭha to saṃhitā text?",
     "**Classical Sanskrit — padapāṭha forensics:**\n\nPadapāṭha splits sandhi — reveals underlying morphological boundaries [attested]. Use for teaching sandhi reversibility. Saṃhitā is continuous recitation form. Both are primary evidence, not normalized 'correct' vs 'corrupt'."),
]

sa_script = [
    ("How should DAVID teach Devanagari as a phonetic script in Sanskrit tutoring?",
     "**Classical Sanskrit — Devanagari:**\n\n52 akṣara principle: each sign = consonant + inherent short a; modify with vowel marks. Hook: Devanagari is among the world's most perfectly phonetic scripts — one symbol per phoneme slot. Teach akṣara order (varga grid) before reading sentences."),
    ("What romanization standard should DAVID use for Sanskrit?",
     "**Classical Sanskrit — romanization:**\n\nIAST with diacritics: ṣ, ś, ṛ, ā, ñ. Harvard-Kyoto for search: kSetra = kṣetra. Never drop dots/macrons in published pedagogical materials — they encode phonemic contrasts AI and learners need."),
    ("Explain the Sanskrit akṣara inventory pedagogy for a tutoring episode.",
     "**Classical Sanskrit — akṣara episode:**\n\n13 vowels (a ā i ī u ū ṛ ṝ ḷ ḹ e ai o au); 33 consonants in varga grid; visarga, anusvāra. Arrange as Śikṣā mouth-position chart: velar → palatal → retroflex → dental → labial. Living tradition [attested]."),
    ("How do conjunct consonants (samyuktākṣara) feature in Sanskrit script teaching?",
     "**Classical Sanskrit — conjuncts:**\n\nVertical/ligature stacking: क्ष, ज्ञ, त्र. Teach component recognition before fluent reading. Unicode Devanagari block; font requirements for rare ligatures. Pedagogical progression: standalone → conjunct → sandhi-merged phrases."),
]

sa_tutor = [
    ("Outline a DAVID tutoring arc for Classical Sanskrit phonology.",
     "**Classical Sanskrit — series arc:**\n\nEp1: Akṣara grid + aspirates (candle demo)\nEp2: Retroflex vs dental (mirror tongue position)\nEp3: Vowel length + ṛ syllabic\nEp4: Sandhi merge laboratory\nEp5: Śikṣā — 'ancient phonetics lab' (series flagship)\nFlags: shiksha_notes, aspirate_pairs per pronunciation_profile.json"),
    ("What tutoring hook opens a Classical Sanskrit Śikṣā episode?",
     "India had precise phonetic science centuries before the West had IPA — Pāṇini's colleagues measured tongue positions like engineers."),
    ("Generate a lesson scaffold for धर्मक्षेत्रे कुरुक्षेत्रे.",
     "**Classical Sanskrit — lesson scaffold:**\n\n1. Display Devanagari + IAST\n2. Segment: dharma-kṣetra / kuru-kṣetra\n3. Highlight retroflex ṣ in kṣ clusters\n4. IPA: /dʱər.mək.ʂeː.t̪reː ku.ɾu.k.ʂeː.t̪reː/\n5. Sandhi note: none internal; external in next line of Gita\n6. Context: Bhagavad Gita 1.1 battlefield invocation\n7. Tag [attested] text"),
    ("What surprising fact about Sanskrit aspirates should anchor a tutoring episode?",
     "Sanskrit has four-way stop contrasts (voiceless, voiced, aspirated, voiced-aspirated) — English has two. Your mouth has been undertrained your whole life."),
]

for p in sa_pron + sa_phone + sa_ai + sa_trans + sa_corpus + sa_script + sa_tutor:
    add(p[0], p[1])

sa_extra = [
    ("How should DAVID present Vedic vs Classical Sanskrit pronunciation variants?",
     "**Classical Sanskrit — Vedic vs Classical:**\n\nVedic: pitch accent, archaic morphology, sandhi-heavy. Classical: fixed grammar per Pāṇini, accent marks absent in prose. Label recitation style. Both share core phoneme inventory [attested]; Vedic accent melody needs pandit reference."),
    ("Provide IPA for अग्निमीळे पुरोहितं in Vedic reconstruction.",
     "**Classical Sanskrit — IPA:**\n\nअग्निमीळे पुरोहितं: /ˈɐɡ.n̪i.miː.ɭe ˈpu.ɾo.hi.t̪ɐm/\n**Model:** Vedic Śikṣā + pandit recitation\n**Confidence:** [reconstructed] very_high\n**Note:** Long ī; retroflex ḷ in īḷe; dental t in hitam."),
    ("What series planning flags exist for Sanskrit in DAVID's registry?",
     "**Classical Sanskrit — series flags:**\n\n`shiksha_notes` — flagship tutoring module; `aspirate_pairs` — standalone lesson; retroflex grid; sandhi laboratory; Devanagari phonetic perfection hook. Priority Tier 2 in tutoring content."),
    ("What pacing applies to Sanskrit śloka recitation in documentary audio?",
     "**Classical Sanskrit — śloka pacing:**\n\nSyllable-weight meter (morae per pāda); deliberate enunciation — no English stress reduction. Pause at pāda boundaries. Anuṣṭubh 8×4 syllable pattern for Gita verses. Pandit tempo as reference."),
    ("How does DAVID teach the palatal ञ in Sanskrit pronunciation?",
     "**Classical Sanskrit — palatal nasal:**\n\nञ [ɲ] as in Spanish 'ñ' or French 'agneau'. Occurs in varga and sandhi: संज्ञा [səɲɟɲaː]. Distinct from anusvāra nasalization. AI often uses /nj/ sequence — flag."),
    ("What forensic note applies to reading Sanskrit from non-Devanagari scripts?",
     "**Classical Sanskrit — script variants:**\n\nGrantha, Śāradā, Bengali, Tamil Brahmi traditions preserve same phonemic system [attested] with different graphs. DAVID notes script source in corpus entry; do not assume Devanagari for all manuscripts."),
]
for p in sa_extra:
    add(p[0], p[1])

# ── ADDITIONAL PAIRS (fill to 200) ────────────────────────────────────────────

more_ag = [
    ("Provide IPA for μῆνιν ἄειδε θεά and state the pronunciation model.", "**Ancient Greek — IPA:**\n\nμῆνιν ἄειδε θεά: [mɛ̂ː.nin áe̯i̯.de tʰe.áː]\n**Model:** Attic Classical (Allen)\n**Confidence:** [reconstructed] high\n**Note:** Long η; aspirated θ; pitch accent on ἄειδε and θεά."),
    ("How should DAVID teach the Greek diphthong αυ in Attic pronunciation?", "**Ancient Greek — αυ:**\n\nBefore voiceless consonants: [au̯]; before voiced/vowel: [aːu̯] or monophthongization trends in late Attic. Avoid English 'ow'. Drill: αὐτός [autós]. Tag period variant if teaching Koine fricative allophones."),
    ("What forensic note applies to reading Homeric Greek without digamma?", "**Ancient Greek — Homeric forensics:**\n\nText omits ϝ but meter demands it — syllable count proves presence. Mark [reconstructed] when inserting ϝ in pronunciation. Use for tutoring hook on textual vs phonetic reality."),
    ("How does DAVID teach xi (ξ) and psi (ψ) in Ancient Greek?", "**Ancient Greek — ξ ψ:**\n\nξ = [ks], ψ = [ps] — true clusters, not affricates. ξένος [ksénos], ψυχή [psyːkʰɛ̌ː]. AI may affricate — wrong. Hold both elements audible."),
    ("What translation note applies to the Greek middle voice?", "**Ancient Greek — middle voice:**\n\nNot reflexive by default — often subject-focused action (λούομαι 'I wash myself' but also 'I wash' with self-interest). Don't force English reflexive pronouns. DAVID morphology note with examples from Xenophon."),
    ("Generate a research query for Ancient Greek koine papyri phonology.", "**Ancient Greek — research query:**\n\n'Extract phonological spellings from BGU and P.Oxy papyri showing iotacism and aspirate loss chronology; map to documentary letters; output timeline with [attested] orthographic evidence.'"),
    ("What tutoring content should cover Greek accent grave sandhi?", "**Ancient Greek — grave sandhi:**\n\nGrave accent on non-final mora lowers before another word — οὐκ ἔστιν sandhi rules. Advanced module after acute/circumflex. Allen Ch. 7; tag [reconstructed] on exact phonetic realization."),
    ("How should DAVID romanize Ἀχιλλεύς for tutoring materials?", "**Ancient Greek — romanization example:**\n\nἈχιλλεύς → Akhilleús (ALA-LC) or Akhilleus with macron on final vowel if long. Preserve chi as kh (aspirate), not ch as /tʃ/. Breathing on alpha: initial vowel with rough breathing = h-."),
    ("What AI error affects Greek geminate consonants in audio?", "**Ancient Greek — geminate AI:**\n\nSpelling doubles (ἀλλά, θάλαττα) require held consonants — AI shortens. Instruct: 'double lambda held like Italian bello'. Metrics confirm geminates [attested]."),
    ("Situate γνῶθι σεαυτόν in DAVID tutoring series context.", "**Ancient Greek — tutoring context:**\n\nDelphic maxim; Post 3 hook; secure literary attestation. Episode use: introduce omicron vs omega quantity + circumflex on γνῶ. Pair with inscriptional maxims module."),
    ("What corpus entry format should DAVID use for Greek drama excerpts?", "**Ancient Greek — drama corpus format:**\n\nSpeaker tag; line number (TLG); meter annotation; lyric vs iambic register note; [attested] manuscript; IPA [reconstructed]. Source: Oxford Classical Text or Teubner edition cited."),
    ("How does DAVID teach prosody in Greek tragic choruses?", "**Ancient Greek — tragic chorus:**\n\nLyric meters (dochmiac, glyconic) — quantity-driven rhythm. Pronunciation lesson tied to meter scan. Aeschylus Seven Against Thebes as sample. Don't apply hexameter rules to lyric cola."),
    ("What begadkefat-adjacent concept exists in Greek? (spirantization in Koine)", "**Ancient Greek — Koine spirantization:**\n\nParallel to Hebrew begadkefat: Attic aspirates become fricatives in Koine — document as diachronic shift, not random error. Comparison episode hook for Semitic-Greek tutoring crossover."),
    ("What on-screen variant table should DAVID show for Greek philosophical terms?", "**Ancient Greek — variant table:**\n\n| Term | Attic IPA | Koine | Notes |\n|λόγος|/lóɡos/|/ˈloɣos/|spirant γ|\n|φιλοσοφία|/pʰilosophíaː/|/filosoˈfia/|φ→f|"),
    ("How should translators handle Greek particles in Thucydides?", "**Ancient Greek — Thucydides particles:**\n\nγάρ, μέν, δέ, γε stack densely — English needs periodic sentences matching argument structure. Don't delete μέν without following δέ logic. DAVID QA flags broken μέν-δέ pairs."),
    ("What pronunciation tutoring drill uses the Delphic maxims collection?", "**Ancient Greek — maxim drill:**\n\nγνῶθι σεαυτόν, μηδὲν ἄγαν, ἐγγύα πάρα δ'ἄτη — short lines for quantity + accent practice. Inscriptional evidence for some. Episode: 'Know thyself — and know thy vowel lengths'."),
    ("Document disputed phoneme zeta for DAVID research queue.", "**Ancient Greek — zeta dispute:**\n\nRoute to disputed_phonemes.json: '[zd] vs [dz] in Attic; inscriptional ζ varies; Allen prefers [zd]; some dialects differ'. Priority: medium. Searchable question: 'Pre-4th c. Attic inscription zeta clusters'."),
    ("What Grok Imagine script line produces correct theta in θεός?", "**Ancient Greek — Grok script:**\n\n'θεός THEH-oss: t with strong h puff after, long e on epsilon, pitch rise on accent, NOT English th as in think'. Repeat θ- minimal pair with τόπος."),
    ("How does DAVID teach iota subscript in Greek tutoring?", "**Ancient Greek — iota subscript:**\n\nᾳ ῃ ῳ = long vowel + offglide [i̯] or long diphthong depending on period. Pronounce iota element — not silent. Unicode polytonic required in display. Advanced orthography module."),
    ("What translation methodology applies to Septuagint Greek vs Classical?", "**Ancient Greek — LXX methodology:**\n\nKoine register; Semitic interference in syntax (καί chains); match Hebrew source structure when doing interlinear work. Tag 'LXX Greek' not 'Attic'. Different pronunciation profile than Plato episodes."),
]

more_bh = [
    ("Provide IPA for שָׁלוֹם in Tiberian Biblical Hebrew.", "**Biblical Hebrew — IPA:**\n\nשָׁלוֹם: /ʃaː.ˈloːm/\n**Model:** Tiberian Khan\n**Confidence:** [reconstructed] high\n**Note:** Shin dot right = /ʃ/; long ô; stress on ultima."),
    ("How should DAVID teach qameṣ qatan vs qameṣ gadol?", "**Biblical Hebrew — qameṣ:**\n\nGadol [aː] vs qatan [ɔ] — position and morphological class determine. Drill: כָּל vs כֹּל contexts. AI collapses to one vowel — error. Khan vowel charts required in lesson PDF."),
    ("What forensic step applies to Qere/Ketiv in Biblical Hebrew corpus work?", "**Biblical Hebrew — Qere/Ketiv:**\n\nWritten Ketiv (what's written) vs read Qere (what's read) — never vocalize Ketiv when tradition reads Qere. Mark in corpus entry. YHWH tetragrammaton → Adonai Qere [attested] Masoretic practice."),
    ("How does DAVID teach sin vs shin in Biblical Hebrew?", "**Biblical Hebrew — sin/shin:**\n\nשׂ = /ś/ (Proto-Semitic lateral); שׁ = /ʃ/. שָׁלוֹם vs שָׂרַי — different dots. Samaritan and Aramaic reflexes aid reconstruction. Minimal pair drill."),
    ("What AI error affects Hebrew dagesh lene in audio generation?", "**Biblical Hebrew — dagesh lene AI:**\n\nWithout dagesh ב should spirantize to [v] — AI keeps [b]. Instruct per word from niqqud. Example: בֹּקֶר [boːˈqɛr] with dagesh vs בָּרָא context-dependent."),
    ("Generate a tutoring hook for Biblical Hebrew begadkefat.", "Begadkefat is Hebrew's hidden shape-shifter — the same letter becomes a stop or a fricative depending on a dot."),
    ("What translation note applies to Hebrew verbal stems (qal, piel, hiphil)?", "**Biblical Hebrew — stems:**\n\nMorphology encodes causative, intensive, passive — English needs periphrasis ('he caused to kill' for hiphil). Don't flatten to simple past. DAVID morphology table per stem with [attested] examples."),
    ("How should DAVID present Babylonian Hebrew vowels in comparison modules?", "**Biblical Hebrew — Babylonian:**\n\nSix-vowel system vs Tiberian detail — tag when citing Babylonian manuscripts. Useful for DSS vocalization studies. Not default for documentary Genesis read."),
    ("What corpus priority applies to Hebrew epigraphic texts?", "**Biblical Hebrew — epigraphy:**\n\nMesha Stele, Siloam inscription, Ketef Hinnom amulets — paleo-Hebrew script; no niqqud. Vocalization [hypothesis] from comparative Semitics. Date and dialect tag mandatory."),
    ("How does DAVID teach meteg in Tiberian Hebrew pronunciation?", "**Biblical Hebrew — meteg:**\n\nVertical stroke beside vowel — secondary stress or vowel length signal. Affects sheva classification (sheva na with meteg). Advanced Khan module. AI ignores — document."),
    ("What Grok Imagine guidance produces authentic ʿayin in Hebrew audio?", "**Biblical Hebrew — ʿayin Grok:**\n\n'ʿayin: deep pharyngeal constriction, Arabic ع, hold during vowel onset, NOT silent, NOT glottal stop'. Place after vowel in עָמַק [ʕaːˈmaq]."),
    ("What tutoring episode compares Tiberian and Modern Hebrew for בְּרֵאשִׁית?", "**Biblical Hebrew — comparison episode:**\n\nSide-by-side audio: Tiberian gutturals + uvular resh vs Modern alveolar resh and reduced ʿayin. Visual waveform comparison. Label both traditions; neither is 'wrong' — different continuity models."),
    ("How should translators handle Hebrew wordplay in prophetic texts?", "**Biblical Hebrew — wordplay:**\n\nAssonance and paronomasia (e.g., אָדָם / אֲדָמָה) — footnote in English; don't invent English puns that aren't in text. DAVID creative translation flag when wordplay untranslatable."),
    ("What research query expands Hebrew cantillation tutoring content?", "**Biblical Hebrew — trope research:**\n\n'Catalog 30 tropes with Unicode names, audio samples, and verse-position rules for Leviticus 19; generate lesson_plan.md cantillation module.'"),
    ("How does DAVID romanize צֶדֶק for academic materials?", "**Biblical Hebrew — romanization:**\n\nצֶדֶק → ṣéḏeq (SBL) — dot under ṣ for emphatic; é for vocal sheva context. IPA: /ˈsˤɛ.ðeq/ [reconstructed]."),
    ("What forensic note applies to DSS Hebrew spelling variants?", "**Biblical Hebrew — DSS:**\n\nPlene vs defective spelling affects syllable count — don't normalize to MT. Tag 4Q variant readings. Impacts pronunciation [hypothesis] only when vocalization differs."),
    ("Document AI cantillation flattening for Hebrew research queue.", "**Biblical Hebrew — AI trope error:**\n\nRoute: 'TTS reads WLC as flat prose — need trope-aware model or post-process cadence markers'. Priority: high for liturgical content."),
    ("What lesson plan structure does DAVID use for Hebrew script episodes?", "**Biblical Hebrew — script lesson:**\n\n1. Paleo-Hebrew photo 2. Square script emergence 3. Consonant drill 4. Niqqud overlay history 5. Read Genesis 1:1 pointed 6. Attempt unpointed with morphology hints."),
    ("How should DAVID tag Samaritan vs Tiberian consonant differences?", "**Biblical Hebrew — Samaritan consonants:**\n\nSamaritan preserves some distinctions lost in Tiberian notation — comparative module [attested] oral tradition. Label 'Samaritan' — do not mix into Tiberian IPA without flag."),
    ("What translation return check applies to Hebrew legal texts?", "**Biblical Hebrew — legal translation:**\n\nCovenant formulary patterns (if…then) — preserve conditional structure. Don't modernize into statute prose. Register: biblical legal [attested formulae from ANE parallels]."),
    ("Provide a corpus entry for Psalm 23:1 opening.", "**Biblical Hebrew — corpus entry:**\n\n**Text:** יְהוָה רֹעִי לֹא אֶחְסָר\n**Romanization:** YHWH rōʿî lōʾ ʾeḥsār\n**Translation:** YHWH is my shepherd; I shall not want\n**Source:** WLC Psalm 23:1 [attested]\n**Note:** Qere vocalization for divine name; shepherd imagery register."),
    ("What pacing note applies to Hebrew prophetic poetry recitation?", "**Biblical Hebrew — prophetic pacing:**\n\nParallelism pairs need balanced phrasing — don't rush second colon. Isa 40:3 sample. Cantillation where marked. Elevated register, not conversational."),
]

more_sa = [
    ("Provide IPA for नमस्ते in Classical Sanskrit citation.", "**Classical Sanskrit — IPA:**\n\nनमस्ते: /n̪ə.məs.t̪eː/\n**Model:** Classical Śikṣā\n**Confidence:** [reconstructed] very_high\n**Note:** Dental n/t; long final e; sandhi internal to compound namah-te → namaste."),
    ("How should DAVID teach the Sanskrit palatal varga (च छ ज झ ञ)?", "**Classical Sanskrit — palatal varga:**\n\nच [c], छ [cʰ], ज [ɟ], झ [ɟʱ], ञ [ɲ] — tongue blade to hard palate. Distinct from retroflex and dental rows. AI collapses च and ट — catastrophic error."),
    ("What forensic note applies to Vedic accent in Rig Veda corpus entries?", "**Classical Sanskrit — Vedic accent:**\n\nUdātta marked in some padapāṭha traditions — mandatory for śrauta recitation [attested]. Classical prose citation may omit. Tag 'Vedic accent required' per text genre."),
    ("How does DAVID teach external sandhi rule visarga + k?", "**Classical Sanskrit — sandhi visarga:**\n\nFinal -ḥ before k/kh/kh → voiceless velar fricative release (śak + artha → śakartha processes). Pāṇini 8.3.34ff. Drill with live merge audio."),
    ("What AI error affects Sanskrit anusvāra before retroflex?", "**Classical Sanskrit — anusvāra AI:**\n\nसंस्कृत → nasal assimilates to retroflex [ɳ] before ष — AI uses generic /m/. Instruct: 'anusvāra becomes tongue-tip nasal matching following consonant place'."),
    ("Generate a tutoring hook for Sanskrit varga grid.", "Five rows × five columns = 25 consonant slots — Sanskrit organized the mouth like a spreadsheet 2500 years before IPA charts."),
    ("What translation note applies to Sanskrit dharma in philosophical texts?", "**Classical Sanskrit — dharma:**\n\nContext-dependent: duty, law, cosmic order, righteousness. Don't fix one English equivalent. First occurrence: gloss bundle; thereafter selective retention. DAVID theology-philosophy register flag."),
    ("How should DAVID present Prātiśākhya texts in tutoring series?", "**Classical Sanskrit — Prātiśākhya:**\n\nComplement to Śikṣā — Vedic phonetic treatises per śākhā. Episode: 'Rigveda phonetic lab manual'. [attested] indigenous linguistics. Tier 2 series priority."),
    ("What corpus priority applies to Sanskrit grammatical literature?", "**Classical Sanskrit — grammar corpus:**\n\nPāṇini Aṣṭādhyāyī; Kātyāyana; Patañjali Mahābhāṣya; Śikṣā literature. Phonology entries cite sūtra numbers where possible [attested]."),
    ("How does DAVID teach ḷ (vocalic l) in Sanskrit?", "**Classical Sanskrit — ḷ:**\n\nRare vocalic liquid — occurs in Vedic, largely replaced by li in Classical. Pronounce as syllabic [l̩]. Whitney examples. AI uses /lu/ — error."),
    ("What Grok Imagine script produces retroflex ष in क्ष?", "**Classical Sanskrit — Grok kṣ:**\n\n'kṣ = k + retroflex sh [ʂ], tongue curled back, NOT palatal ś, NOT English sh alone'. Demo: क्षत्रिय [kʂət̪ɾijə]."),
    ("What lesson compares Sanskrit sandhi to English linking-r?", "**Classical Sanskrit — sandhi pedagogy:**\n\nEnglish linking-r is optional; Sanskrit sandhi is obligatory in śāstra recitation. Merge न + अपि → नापि live. Pāṇini rule number on screen."),
    ("How should DAVID romanize क्षेत्र?", "**Classical Sanskrit — romanization:**\n\nक्षेत्र → kṣetra (IAST) — underdot s for retroflex ṣ component. Harvard-Kyoto: kSetra. Never 'kshetra' without marking retroflex quality in pedagogy notes."),
    ("What research query targets Sanskrit disputed phonemes?", "**Classical Sanskrit — research query:**\n\n'Verify ḷ/ḹ occurrences in RV padapāṭha; document living pandit variants; update disputed_phonemes.json with recension-specific notes.'"),
    ("How does DAVID teach vowel sandhi (a + i → e)?", "**Classical Sanskrit — vowel sandhi:**\n\nअ + इ → ए: e.g., नर + इन्द्र → नरेन्द्र. Mandatory in fluent speech. AI word gap breaks it. Drill compound splits then merges."),
    ("What translation methodology applies to Sanskrit kāvya (poetry)?", "**Classical Sanskrit — kāvya:**\n\nPreserve alaṅkāra (ornament), dhvani (suggestion) where possible — footnote when English can't carry suggestion. Kalidasa Meghaduta sample. Register: literary [attested conventions]."),
    ("What forensic step applies to critical edition variants in Mahābhārata?", "**Classical Sanskrit — MBh forensics:**\n\nCritical apparatus — northern vs southern recension. Tag verse per BORI. Don't conflate readings. Impacts tutoring citation, not core phonology."),
    ("Document AI retroflex failure for Sanskrit research queue.", "**Classical Sanskrit — AI retroflex:**\n\nRoute: 'TTS dental-for-retroflex on ष ट ण — require explicit Śikṣā place features in Grok script'. Priority: high."),
    ("What tutoring content covers Sanskrit numerals and ordinals?", "**Classical Sanskrit — numerals episode:**\n\nएक द्वि त्रि — declension like adjectives; sandhi in compounds (त्रिलोक). Phonology: aspiration in षष्टि (60). Culture + phonology crossover."),
    ("How should DAVID tag confidence for living pandit-confirmed phonology?", "**Classical Sanskrit — confidence tag:**\n\nPhoneme inventory: [attested] via Śikṣā + living recitation. Historical Vedic pitch: [reconstructed] with pandit confirmation. Honest split — don't overclaim melody."),
    ("Provide a corpus entry for Bhagavad Gita 2.47 (karma verse).", "**Classical Sanskrit — corpus entry:**\n\n**Text:** कर्मण्येवाधिकारस्ते मा फलेषु कदाचन\n**Romanization:** karmaṇy evādhikāras te mā phaleṣu kadācana\n**Translation:** Your right is to action alone, never to its fruits\n**Source:** BG 2.47 [attested]\n**Note:** Karma/fala technical terms; sandhi throughout."),
    ("What series episode covers Sanskrit śleṣa (pun) for advanced learners?", "**Classical Sanskrit — śleṣa episode:**\n\nAdvanced literary module — phonological puns depend on retroflex/dental hearability. Example from Daṇḍin. Translation methodology: footnote, don't flatten."),
]

more_cross = [
    ("How do DAVID pronunciation profiles feed the tutoring series for these three languages?", "**Cross-language — profile → tutoring:**\n\npronunciation_profile.json → grok_imagine_guidance + tutoring_hooks → lesson_plan.md → episode script. Each language: hooks mined automatically during research_ops ingest."),
    ("What shared AI error is 'English schwa insertion' across Greek, Hebrew, and Sanskrit?", "**Cross-language — schwa error:**\n\nTTS inserts [ə] in clusters none of these languages allow. Greek: CC onsets; Hebrew: sheva rules are specific; Sanskrit: syllabic ṛ not schwa. Universal QA flag in audio pipeline."),
    ("Compare corpus confidence tags across the three languages.", "**Cross-language — corpus confidence:**\n\nAll use [attested]/[reconstructed]/[hypothesis]. Sanskrit phonology often [attested] on articulation; Greek pitch [reconstructed]; Hebrew Tiberian vowels [reconstructed] with strong Masoretic [attested] notation."),
    ("What tutoring series episode title covers 'Ancient phonetics labs'?", "**Cross-language — episode title:**\n\n'Three Ancient Phonetics Labs: Dionysius Thrax, Masoretes, Pāṇini' — compare what each tradition documented about sound. Hook: West thought Greeks invented grammar — India had phonetic matrices first."),
    ("How should DAVID interleave translation methodology training across Greek, Hebrew, Sanskrit?", "**Cross-language — translation training:**\n\nShared module: uncertainty tags, apparatus, register. Language-specific labs: Greek particles, Hebrew stems, Sanskrit compounds. Final capstone: trilingual glossary discipline."),
]

for p in more_ag + more_bh + more_sa + more_cross:
    add(p[0], p[1])

# ── CROSS-LANGUAGE & MIXED ─────────────────────────────────────────────────────

cross = [
    ("Compare how DAVID teaches aspirated stops across Ancient Greek and Classical Sanskrit.",
     "**Cross-language — aspirates:**\n\nGreek: three-way /p pʰ/ contrast in Attic; Sanskrit: four-way /p pʰ b bʰ/ per varga. Both require audible breath burst — same demo (candle, palm puff). Greek AI error: fricativization; Sanskrit AI error: de-aspiration. Tag both [reconstructed] with different confidence levels."),
    ("How do guttural/pharyngeal phonemes differ between Biblical Hebrew and Ancient Greek?",
     "**Cross-language — gutturals:**\n\nHebrew: ʿayin [ʕ], ḥet [ħ], aleph [ʔ] — Semitic pharyngeal set. Greek: only rough breathing [h] — no pharyngeals. AI conflates Hebrew gutturals with glottal stop or silence; Greek [h] dropped. Different coaching clips required."),
    ("What shared pedagogical principle applies to quantity in Greek and Sanskrit tutoring?",
     "**Cross-language — quantity:**\n\nBoth mora-based: Greek hexameter and Sanskrit anuṣṭubh depend on long vs short vowels. Same clap-twice drill. AI equalizes length in both — document as universal TTS failure. DAVID preserves quantity in all documentary audio."),
    ("How should a DAVID tutoring series interleave Ancient Greek, Biblical Hebrew, and Sanskrit phonology episodes?",
     "**Cross-language — series interleaving:**\n\nThematic arcs: Ep 'Aspirates' (Greek φ, Sanskrit ph), Ep 'Gutturals vs Retroflexes' (Hebrew ʿ vs Sanskrit ṭ), Ep 'Quantity & Meter', Ep 'Script as phonetic code' (Greek polytonic, Hebrew niqqud, Devanagari). Each episode: one language deep-dive + 2-minute contrast coda."),
    ("Compare AI audio error patterns for Greek upsilon and Sanskrit ṛ.",
     "**Cross-language — AI vowel errors:**\n\nGreek υ → wrongly /u/; Sanskrit ṛ → wrongly /ri/. Both are non-English vowel classes. Fix: explicit IPA in Grok Imagine; reference clips (French tu for υ; syllabic r drill for ṛ). Tag phoneme class in disputed_phonemes.json."),
    ("What translation methodology is shared across all three DAVID ancient-language pillars?",
     "**Cross-language — translation core:**\n\nCorpus-first attestation; register identification; technical term glossing; return-to-source QA; uncertainty tags [attested]/[reconstructed]/[hypothesis]. Living-language idiom rules do NOT apply to dead-language philological translation — different QA checklist."),
    ("How does DAVID romanization policy differ for Greek, Hebrew, and Sanskrit?",
     "**Cross-language — romanization:**\n\nGreek: polytonic preservation or ALA-LC; Hebrew: SBL with underdots; Sanskrit: IAST with macrons/subdots. Never strip diacritics that encode phonemic contrasts. Tutoring materials include phoneme-to-diacritic key card per language."),
    ("What corpus research workflow is common to Greek, Hebrew, and Sanskrit in DAVID?",
     "**Cross-language — corpus workflow:**\n\nSELECT language → SURVEY primary corpus → EXTRACT attested block → IPA from pronunciation_profile.json → BUILD tutoring hook → QUEUE research_query_generator.py. Each entry: source, date, confidence tag, variant label."),
    ("Generate Grok Imagine audio guidance comparing Hebrew cantillation and Greek pitch accent.",
     "**Cross-language — prosody AI:**\n\nHebrew: chant trope melodies — phrase-final cadences (sof pasuq, etnachta). Greek: single-word pitch mora — acute rise, circumflex fall. Both reject English stress-default TTS. Script must specify prosody type explicitly; never 'neutral narration'."),
    ("What tutoring hook compares the three scripts' phonetic transparency?",
     "Greek breathings encode /h/; Hebrew niqqud encode vowels the consonants hide; Devanagari maps 1:1 to akṣara — three solutions to the same problem: how to preserve sound in writing."),
    ("How should DAVID tag confidence differently for Greek, Hebrew, and Sanskrit pronunciation?",
     "**Cross-language — confidence:**\n\nSanskrit: very_high (Śikṣā + living pandits). Hebrew: high (Tiberian Khan + Masoretic continuity). Greek: high on inventory, medium on pitch melody. Never present all three as equal certainty — honest labels protect documentary credibility."),
    ("What phonological feature is unique to Sanskrit but absent in Greek and Hebrew?",
     "**Cross-language — unique feature:**\n\nRetroflex consonant series (ṭ, ḍ, ṣ) with dental contrast — Indo-Aryan innovation. Greek has no retroflexes; Hebrew emphatics are uvularized/pharyngealized, not retroflex curls. Tutoring contrast episode candidate."),
    ("What phonological feature do Biblical Hebrew and Arabic share that Greek lacks?",
     "**Cross-language — Semitic features:**\n\nPharyngeal ʿayin and ḥet — Arabic cognate sounds aid Hebrew coaching. Greek has no pharyngeal class. DAVID uses Arabic reference clips in Hebrew guttural modules only — label as pedagogical aid, not historical merger."),
    ("Provide a DAVID research query for trilingual pronunciation profile audit.",
     "**Cross-language — research query:**\n\n'Audit ancient-greek, biblical-hebrew, classical-sanskrit pronunciation_profile.json against latest research_ops outputs; flag disputed_phonemes overlaps; generate 10 tutoring hooks per language; verify grok_imagine_guidance fields present.'"),
    ("How do sandhi (Sanskrit) and crasis (Greek) compare as boundary phenomena?",
     "**Cross-language — sandhi/crasis:**\n\nBoth merge across word boundaries in fluent speech. Sanskrit: systematic rules in Pāṇini [attested]. Greek: crasis (κἀγώ = καὶ ἐγώ) and elision. AI word-by-word reading breaks both — script must show merged forms."),
    ("What documentary on-screen label should appear for all three reconstructed pronunciations?",
     "**Cross-language — on-screen labels:**\n\n'Greek: Attic Classical [reconstructed]'; 'Hebrew: Tiberian [reconstructed]'; 'Sanskrit: Classical [attested articulatory tradition]'. Never 'authentic ancient pronunciation' without qualification."),
    ("Compare stress/accent systems across the three languages for tutoring.",
     "**Cross-language — accent summary:**\n\nGreek: pitch accent (one high mora). Hebrew: stress + cantillation melody. Sanskrit: Vedic pitch (udātta/svarita); Classical stress on heavy syllable. Three different prosody systems — one episode each, plus comparison coda."),
    ("What AI audio pipeline checkpoint should DAVID run before publishing trilingual pronunciation content?",
     "**Cross-language — QA checkpoint:**\n\n1. IPA match to profile 2. Aspiration puff audit 3. Length timing 4. Language-specific feature (gutturals/retroflexes/pitch) 5. Variant label on-screen 6. No Modern Greek/Modern Hebrew/Hindi drift 7. Source citation in description"),
    ("How should DAVID's disputed_phonemes.json route research for these three languages?",
     "**Cross-language — disputed routing:**\n\nGreek: zeta, pitch melody, digamma. Hebrew: ḥet [ħ] vs [x], resh articulation. Sanskrit: rare — ḷ vowel, minor recension variants. Each dispute → research_queue.json with searchable question and priority."),
    ("What translation return-to-source risk is shared when editing ancient-language glosses?",
     "**Cross-language — gloss QA:**\n\nEnglish editorial pass can introduce Christian/philosophical/Indic interpretive frames not in source. Return-to-Greek/Hebrew/Sanskrit check: lemma alignment, not just sense. DAVID flags theological and philosophical loaded terms."),
]

for p in cross:
    add(p[0], p[1])

# Ensure exactly 200
assert len(pairs) >= 200, f"Only {len(pairs)} pairs generated"
pairs = pairs[:200]

# Shuffle for mixed language order
random.shuffle(pairs)

out_path = "david_ag_bh_sa_200.jsonl"
with open(out_path, "w", encoding="utf-8") as f:
    for p in pairs:
        f.write(json.dumps(p, ensure_ascii=False) + "\n")

print(f"Wrote {len(pairs)} pairs to {out_path}")
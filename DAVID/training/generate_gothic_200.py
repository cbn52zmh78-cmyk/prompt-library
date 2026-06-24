#!/usr/bin/env python3
"""Generate 200 distinct Gothic DAVID training pairs."""
import json
from pathlib import Path

pairs = []

def add(instr, out, inp=""):
    pairs.append({"instruction": instr, "input": inp, "output": out})

# --- CORPUS & WULFILA BIBLE (1-30) ---
add("What is the primary attested corpus for Gothic and why does it matter for Proto-Germanic reconstruction?",
    "**Gothic — primary corpus:** Wulfila's 4th-century Bible translation survives chiefly in the **Codex Argenteus** (Uppsala) and fragmentary **Codex Ambrosianus** leaves. Together they constitute the sole substantial **East Germanic** literary record. Gothic preserves PGmc **/z/** without West/North Germanic rhotacism, retains comparative vowel lengths and diphthongs, and documents early Christian Germanic lexicon — the 'missing link' between reconstructed PGmc and attested West/North branches. [attested]")

add("Situate this Gothic text in its historical and linguistic context.",
    "**Text:** Atta unsar (Lord's Prayer opening)\n**Language:** Gothic | **Date:** c. 350 CE | **Type:** religious scripture\n\n**Source:** Codex Argenteus, Uppsala University Library\n\n**Context:** Standard entry text for Gothic phonology, morphology, and Wulfila-script training. Arian Gothic Christianity; bishop Wulfila's translation project.\n\nNo direct History figure link in DAVID registry — suitable for standalone language tutoring content.",
    "Atta unsar þu in himinam, weihnai namo þein")

add("Who was Wulfila and what role did he play in Gothic literary history?",
    "**Wulfila** (c. 311–383 CE) was a Gothic bishop who undertook the first known **Bible translation into a Germanic language**. He is credited with inventing the **Gothic alphabet** (27 letters: Greek-uncial base plus runic/Latin additions for PGmc-only sounds). His Arian theological context shaped missionary work among Visigoths and Ostrogoths. The translation (~350 CE) is the earliest substantial literary Germanic text. [attested]")

add("What manuscripts preserve Wulfila's Gothic Bible translation?",
    "**Gothic Bible manuscripts:**\n- **Codex Argenteus** (CA) — Uppsala; purple vellum; Gospels nearly complete\n- **Codex Ambrosianus** (A) — Milan; OT + NT fragments on palimpsest leaves\n- **Codex Carolinus** — small NT fragment\n- **Codex Gissensis** — single leaf (Skeireins context)\n- **Skeireins** — Gothic commentary on John\n\nCA is the flagship source for phonology training. [attested]")

add("Produce a DAVID corpus entry for this Gothic text.",
    "**Language:** Gothic\n**Title:** Atta unsar (Lord's Prayer) — opening\n**Original / transliteration:** Atta unsar þu in himinam, weihnai namo þein\n**Translation:** Our Father, thou in heaven, hallowed be thy name\n**Source:** Codex Argenteus, Uppsala University Library\n**Date:** c. 350 CE\n**Confidence:** [attested]\n**Notes:** Standard entry text for Gothic phonology and morphology training.",
    "Title: Atta unsar (Lord's Prayer)\nOriginal: Atta unsar þu in himinam, weihnai namo þein")

add("What is the Skeireins and how does it relate to the Gothic corpus?",
    "**Skeireins** ('explanation') is a Gothic **commentary on the Gospel of John**, preserved in a single manuscript leaf (Codex Gissensis) with mixed Latin/Gothic tradition. It supplements the biblical corpus with **exegetical prose**, valuable for syntax, conjunctions, and non-biblical vocabulary. [attested]")

add("What Arian Christian context shaped Wulfila's Gothic Bible?",
    "Wulfila translated scripture for **Arian** Gothic Christians — holding that the Son was subordinate to the Father. This theological frame influenced **lexical choices** for Greek θεός/κύριος/υἱός and shaped missionary networks among Visigoths. The Bible's survival owes more to manuscript fate than doctrinal victory. Linguistic value is independent of theology. [attested]")

add("What is attested in Gothic from the Codex Argenteus beyond the Lord's Prayer?",
    "**Codex Argenteus content:** Nearly complete **Gospels** (Matthew, John, Luke, Mark) in Gothic — hundreds of verses for morphology and syntax mining. CA's consistent Wulfila orthography makes it the **gold standard** for grapheme-to-phoneme caption alignment in DAVID productions. [attested]")

add("How complete is the Gothic biblical corpus compared to other ancient Germanic languages?",
    "Gothic offers the **earliest and most extensive** continuous Germanic literary corpus (~4th c.), though still partial (OT mostly fragmentary). Old English literary tradition begins centuries later (c. 8th c.+); Old Norse runic snippets predate but lack biblical-scale prose. Gothic is **extinct East Germanic** with high revival tier. [attested]")

add("What non-biblical Gothic texts exist in the attested record?",
    "**Non-biblical Gothic:**\n- **Skeireins** (John commentary)\n- **Latin-Gothic bilingual ecclesiastical fragments**\n- **Runic inscriptions** (e.g. Ring of Pietroassa — disputed reading)\n- **Proper names** in Roman/Byzantine sources\n- **Loanword evidence** in Greek/Latin chronicles\n\nBiblical Wulfila text dominates. [attested/partial]")

add("Generate a tutoring hook for a video episode using this Gothic Gospel phrase as anchor.",
    "Hook: *jah qap imma Iesus* ('and Jesus said to him') typifies Wulfila's Greek-to-Gothic narrative style.\n\n**Why it works:** High-frequency Gospel formula; demonstrates **jah** cognate with German *ja*, **qap** (preterite of *qiþan* 'say'), dative *imma*.\n\n**Lesson scaffold:**\n1. Present the clause in Wulfila script\n2. Parse verb class and dative pronoun\n3. Compare *qiþan* with OE *cwæþan*, ON *segja*\n4. Context: Codex Argenteus narrative prose (c. 350 CE)\n5. IPA: deliberate stress on root syllables [reconstructed]",
    "Text: jah qap imma Iesus\nTranslation: and Jesus said to him\nSource: Codex Argenteus, Gothic Gospels")

add("What does the Gothic word 'haiþno' reveal about contemporary ethnonyms?",
    "**haiþno** (pl. **haiþnos**) = 'heathen, pagan (fem.)' — origin of English **heathen**. Built on **haiþi** 'heath, wasteland' → 'people of the heath.' Cognate landscape: OE *hæþen*, ON *heiðinn*. [attested]")

add("Identify the source and confidence tag for Gothic Gospel material.",
    "**Source hierarchy for Gothic Gospels:**\n1. Codex Argenteus [attested] — primary\n2. Codex Ambrosianus parallels [attested] — collation\n3. Streitberg / Wulfila Project editions [scholarly] — normalized orthography\n4. Reconstructed lacunae [hypothesis] — never present as attested\n\nDAVID mandate: corpus before grammar; tag every revival form.")

add("What is the significance of the silver Codex Argenteus for DAVID video production?",
    "The **Codex Argenteus** ('Silver Book') provides visually distinctive **purple vellum + metallic ink** provenance for cold-open shots. Linguistically, its **consistent Wulfila orthography** enables frame-accurate **grapheme captions** synced to reconstructed IPA. Provenance card: Uppsala University Library; copied c. 6th c. [attested]")

add("How should DAVID handle lacunae in the Gothic biblical corpus?",
    "**Lacuna protocol:**\n- Mark gaps explicitly — never silently fill with OE/ON cognates\n- Use parallel Greek/Latin Vulgate for *hypothesis* only, tagged [reconstructed]\n- Prefer attested Ambrosianus variants over conjecture\n- Document conjectural restorations in corpus notes, not in audio script as definitive")

add("What Greek textual tradition underlies Wulfila's Gothic Bible?",
    "Wulfila's translation derives from a **Greek** (not Latin Vulgate) base — visible in phrase order calques and vocabulary (*aggilus* from ἄγγελος, *aíwaggeljo* 'gospel'). Greek influence also shaped **script choice** (uncial models). [attested — translation technique]")

add("Provide the Gothic opening of John 1:1 with translation and source.",
    "**Gothic John 1:1** [attested]:\n**Text:** In anna waurþan fruma gudis was\n**Translation:** In the beginning was the Word of God\n**Source:** Codex Argenteus / Gothic Gospels tradition\n**Notes:** *waurd* = 'word'; *gudis* gen. of *guþ*; strong verb **wairþan** 'become/be'. IPA [reconstructed] per Braune/Wright.")

add("What is the Gothic word for 'God' and how is it declined?",
    "**guþ** (n. a-stem) = 'God' — cognate: OE *god*, ON *guð*, OHG *got*. Attested forms: nom. **guþ**, gen. **gudis**, dat. **guda**, acc. **guþ**. [attested]")

add("How does Wulfila render Greek 'angelos' in Gothic?",
    "**aggilus** (m., Greek loan) = 'angel' — Greek **-os** → Gothic **-us** loan pattern. Plural **aggiljus**. Compare OE *engel*, ON *engill*. [attested]")

add("What does Gothic 'aíwaggeljo' tell us about compound formation?",
    "**aíwaggeljo** (n.) = 'gospel, good news' — compound of **aiws** 'eternity/time' + **aggiljo** 'message' (cf. Greek εὐαγγέλιον calque). Stress on first element per PGmc compound rule. [attested]")

add("Describe the Codex Ambrosianus and its value for Old Testament Gothic.",
    "**Codex Ambrosianus** (Milan) preserves **OT fragments** (Nehemiah, Esther, Psalms portions) and NT scraps on **palimpsest** leaves. Critical for expanding beyond CA Gospels. Editorial normalization in Streitberg. [attested] with damage flags.")

add("What is the Wulfila Project and how should DAVID cite it?",
    "The **Wulfila Project** (wulfila.be) provides digitized manuscripts, normalized texts, and cross-references for Gothic biblical material. DAVID should cite it alongside **Streitberg** (1919) and **Braune** for corpus entries. Web corpus is [scholarly edition], not manuscript [attested].")

add("What 4th-century historical events contextualize Gothic Bible translation?",
    "Gothic Bible translation (~350 CE) sits amid **Gothic-Roman frontier politics**, Visigothic/Ostrogothic confederations, and **Arian imperial patronage**. Wulfila's mission under Arian emperors enabled literacy and scripture access before Gothic polities shifted. [historical context]")

add("How many leaves survive of the Codex Argenteus?",
    "Approximately **188 leaves** of Codex Argenteus survive of an estimated original ~330 — roughly **half** the codex. Implies systematic **collation** with Ambrosianus for any production-length Gospel reading. [attested]")

add("What is the standard entry verse for Gothic phonology training in DAVID?",
    "**Atta unsar þu in himinam, weihnai namo þein** — Lord's Prayer opening from Codex Argenteus. Contains: geminate **tt**, **þ** (/θ/), long vowels, optative **weihnai**, dative **himinam**. IPA: /ˈatːa ˈunsar θuː in ˈhiminaːm ˈwiːhnai ˈnaːmoː θeiːn/ [reconstructed]. [attested]")

add("What does Gothic 'atta' mean and what is its etymological interest?",
    "**atta** = 'father' — baby-talk cognate of English **dad**, Latin *atta*, Greek *ἄττα*. One of the most accessible tutoring hooks: a 1700-year-old word that still sounds familiar. [attested]")

add("How does Wulfila spell 'heaven' and what case is 'himinam'?",
    "**himins** (m.) = 'heaven'; **himinam** is **dative singular** — 'in heaven' (*in* + dat.). Compare OE *heofon*, ON *himinn*. Long vowel in coda position; final **-m** marks dative. [attested]")

add("What optative mood form appears in 'weihnai namo þein'?",
    "**weihnai** is **optative** of *weihnan* 'be holy, be hallowed' — equivalent to Greek optative or Latin jussive subjunctive in Lord's Prayer tradition. **namo** (nom.) + **þein** (poss. 'thy'). [attested]")

add("Provide a DAVID corpus entry for Gothic John 1:1.",
    "**Language:** Gothic\n**Title:** Gospel of John 1:1\n**Original:** In anna waurþan fruma gudis was\n**Translation:** In the beginning was the Word of God\n**Source:** Codex Argenteus\n**Date:** c. 350 CE\n**Confidence:** [attested]\n**Notes:** *fruma* = 'first/beginning'; calque of Greek ἐν ἀρχῇ.",
    "Title: John 1:1\nOriginal: In anna waurþan fruma gudis was")

add("What is the Gothic word for 'sin' and where does it appear?",
    "**frawaurhts** (f.) = 'sin, trespass' — compound *fra-* + *waurhts* 'work/deed'. Central to biblical vocabulary. Compare OE *firen*, ON *fjárhýsi* (different formations). [attested] in Gospel and epistle fragments.")

# --- PHONOLOGY (31-60) ---
add("What are the distinctive phonological features of Gothic?",
    "**Gothic — distinctive features:**\n\nGeminates common; voiced fricatives positional (intervocalic β ð ɣ); no umlaut (East Germanic conservatism); nasal longs before h; PGmc /z/ preserved without rhotacism.\n\n**Vowels:** Short: /a ɛ i ɔ u/; Long: /aː eː iː oː uː ɛː ɔː/; Diphthongs: /ai au iu/\n**Consonants:** Stops p b t d k g kʷ gʷ; Fricatives f θ s z x h hʷ; Nasals m n ŋ; Liquids l r; Glides j w.")

add("How is the Gothic letter þ pronounced?",
    "**þ** = /θ/ — voiceless **dental fricative** (think English 'thin', never voiced 'this'). Distinct from stops. AI audio commonly substitutes [t] or [s] — flag as error in QA. Wulfila borrowed this grapheme from runic/Elder Futhark tradition. [reconstructed — high confidence]")

add("How is the Gothic letter ƕ pronounced?",
    "**ƕ** = /hʷ/ or [ʍ] — **labialized** voiceless fricative, distinct from plain **h**. Pronounce like Scots 'wh' in 'which' (if you distinguish which/witch). AI often collapses to /h/ or /w/ alone. [reconstructed — high confidence]")

add("What sound does Gothic q represent?",
    "**q** = /kʷ/ — **labialized velar stop**, as in **qiman** 'come' /ˈkʷiman/. Not an independent phoneme in English; avoid pronouncing as /kw/ with audible /w/ offglide unless targeting precise IPA. [reconstructed]")

add("Are long vowels phonemic in Gothic?",
    "Yes — **vowel length is phonemic** in Gothic. Wulfila script uses **doubled vowels** or special graphs for longs: **ei** = /iː/, **ai** can be /ɛː/ or diphthong depending on context, **au** similarly. Macron vowels must be **sustained ~2× short vowel duration** in audio production. [reconstructed]")

add("What are Gothic diphthongs and how are they disputed?",
    "**Diphthongs:** /ai/, /au/, /iu/ — with scholarly dispute on **monophthongization timing** (whether ai/au were already /ɛː/, /ɔː/ by Wulfila's era). Braune/Wright treat context-dependent realizations. DAVID flags this under **disputed_fields**. [reconstructed — minor dispute]")

add("Explain intervocalic fricative allophony in Gothic.",
    "Gothic **b, d, g** between vowels typically surface as fricatives **[β ð ɣ]** (voiced), while word-initially they are stops **[b d g]**. E.g. *haban* 'have' — medial consonant is fricative. AI TTS trained on English often misses this positional voicing. [reconstructed]")

add("Does Gothic show Verner's Law alternations?",
    "Yes — Gothic preserves evidence of **Verner's Law**: voiceless/voiced fricative alternations in related forms (e.g. *þ/ð*, *f/b* in paradigms). This makes Gothic essential for PGmc phonology pedagogy alongside Sanskrit Verner parallels. [attested pattern]")

add("How does Gothic treat Proto-Germanic *z?",
    "Gothic retains **/z/** where West Germanic and North Germanic underwent **rhotacism** (/z/ → /r/). E.g. PGmc *azt* → Gothic *azt* vs OE *earm* developments differ. This is a flagship comparative lesson. [attested]")

add("What is the Gothic stress system?",
    "**Gothic stress rules:**\n\nPGmc root-initial primary stress preserved (fixed, no shift on inflection); secondary stress on first element of compounds.\n\nStress-timed rhythm; accentual (no tone); deliberate scripture pacing. [reconstructed — high confidence]")

add("How does Gothic handle nasal vowels or nasalization?",
    "Scholarly **dispute** on **nasalization extent** — some contexts show vowel + nasal + h clusters with compensatory length. Not as well documented as Sanskrit anusvāra. DAVID marks nasalization claims [reconstructed] unless orthographically explicit. [disputed]")

add("What vowel quality does Gothic ei represent?",
    "**ei** = /iː/ — long close front vowel. Common in *þeins* 'thy', *sein* 'his'. AI error: diphthongizing to English 'ay' or 'ee-eye'. Hold steady [iː] for full mora. [reconstructed — high confidence]")

add("What vowel quality does Gothic ai represent?",
    "**ai** is **context-dependent**: diphthong /ai/ or long monophthong /ɛː/ (especially before r, h per PGmc). In *Atta*, *unsar* — check environment. Lesson videos should pick one scholarly model (Braune/Wright) and label [reconstructed]. [disputed timing]")

add("What vowel quality does Gothic au represent?",
    "**au** similarly varies: diphthong /au/ or monophthong /ɔː/ in specific environments. *auþida* 'desert' etc. Do not default to English 'ow' diphthong without checking position. [reconstructed — context rules]")

add("How is Gothic r pronounced?",
    "**r** = alveolar **trill or tap** [r], as in Italian/Spanish. Not English approximant [ɹ]. Affects rhythm in Gospel recitation. [reconstructed]")

add("How is Gothic h pronounced?",
    "Plain **h** = /h/ or [x] in some positions (velar fricative before back vowels, laryngeal reflex). **ƕ** is distinct — never merge them in IPA. AI often uses identical glottal [h] for both. [reconstructed]")

add("What is the Gothic consonant x?",
    "**x** (graph) = /x/ or /h/ depending on environment — often from PGmc laryngeal/reflex contexts. Pronounce as voiceless velar fricative like Scots 'loch' / German 'Bach'. [reconstructed]")

add("Does Gothic have umlaut like Old English?",
    "No — Gothic shows **East Germanic conservatism** without i-umlaut or a-umlaut products seen in OE (*mus* → *mȳs*). Fronting mutations are a West/North innovation lesson contrast. [attested comparative]")

add("What is gemination in Gothic and give an example?",
    "**Geminates** (double consonants) are phonemic: **atta** /ˈatːa/ 'father' vs hypothetical single *ata*. Hold the stop/fricative longer in audio — AI often shortens. Written double consonants in Wulfila script are reliable. [attested]")

add("How does Gothic treat final consonants?",
    "Gothic permits relatively rich **final clusters** and maintains consonants that English reduces (e.g. -n, -s, -þ in inflections). No English-style final devoicing rule applied anachronistically. Read endings fully. [reconstructed]")

add("What is the syllable structure of Gothic?",
    "**Stress-timed** with clear syllable onsets; complex clusters allowed word-initially (e.g. **þr**, **sk**, **fr**). Suitable for deliberate scripture pacing — avoid English schwa epenthesis in clusters. [reconstructed]")

add("Provide IPA for Gothic 'qiþan' (to say).",
    "**qiþan** /ˈkʷiθan/ — labialized initial, dental fricative medial/final. Preterite **qap** /kʷap/. Model: Braune/Wright. [reconstructed]")

add("Provide IPA for Gothic 'guþ' (God).",
    "**guþ** /ɡuθ/ — ends in voiceless dental fricative, not voiced 'th'. Common AI error: final [ð]. [reconstructed]")

add("Provide IPA for Gothic 'hlaifs' (bread/loaf).",
    "**hlaifs** /ˈxlɛifs/ or /ˈhlɛifs/ — initial cluster; diphthong or long vowel in **ai** per model. Eucharistic vocabulary in Gospels. [reconstructed]")

add("Provide IPA for Gothic 'sunjus' (sons).",
    "**sunjus** /ˈsunjus/ — nominative plural of *sunus*. Shows /j/ glide and u-stem plural. Compare OE *sunu*, ON *synir* (rhotacism). [reconstructed]")

add("What phonological feature makes Gothic conservative among Germanic languages?",
    "Gothic preserves multiple **PGmc archaisms**: /z/, fixed stress, lack of umlaut, relatively intact morphological case system in attested prose. It looks 'older' than OE/ON — ideal for 'time-travel' tutoring narrative. [attested comparative]")

add("How should long vowels be paced in Gothic audio production?",
    "Sustain long vowels **~2× short vowel duration**; do not clip. Scripture register uses **moderate tempo** with geminates held. Sync captions to Wulfila graphemes 1:1 — no silent letters to hide timing. [studio guidance]")

add("What PGmc correspondences does Gothic document for stops?",
    "Gothic maintains **Grimm's Law** outcomes clearly: PGmc *t → þ, *p → f, *k → h in many positions, while medial voiced stops surface as fricatives. Use Gothic to teach the law with [attested] examples, not PIE fantasy forms.")

add("Explain the Gothic vowel system to a video audience in one paragraph.",
    "Gothic distinguishes **short and long vowels** plus diphthongs **ai, au, iu**. Wulfila's alphabet maps each sound to a letter — no silent spellings. Think Greek-like pure vowel qualities, not English diphthong creep. East Germanic lacked the umlaut that later bent vowels in English and German. When you hear reconstructed Gothic, you're hearing the closest literary cousin to the ancestor of the whole Germanic family. [reconstructed]")

add("What is the confidence level for core Gothic segment phonology?",
    "**Confidence: high** — core segments undisputed per Braune/Wright/Streitberg consensus. Minor disputes: diphthong monophthongization timing, nasalization extent. Label audio 'Scholarly reconstruction of Gothic' — never present as native speaker definitive. [reconstructed]")

# --- SCRIPT & RUNIC CONNECTIONS (61-85) ---
add("Describe Wulfila's Gothic alphabet for video captioning.",
    "Wulfila's **27-letter alphabet**: Greek-uncial base plus **runic/Latin additions** for PGmc-only sounds (þ, ƕ, q, etc.). **Direct 1:1 grapheme-to-phoneme mapping** — no silent letters; ideal for on-screen caption alignment in DAVID productions. [attested script]")

add("Which Gothic graphemes come from runic tradition?",
    "**þ** (thorn) and **ƕ** (hwair) show **Elder Futhark** ancestry — þ rune = /θ/; hwair adapted for /hʷ/. Wulfila did not use the full futhark but **borrowed specific graphs** for sounds Greek/Latin lacked. [attested — paleographic tradition]")

add("Why did Wulfila not write Gothic in Latin or Greek script alone?",
    "Greek and Latin scripts **lacked dedicated letters** for PGmc /θ/, /hʷ/, /kʷ/, and some vowel distinctions. Wulfila engineered a **purpose-built alphabet** for missionary literacy — not mere transliteration convenience. [historical reconstruction]")

add("How many letters are in the Gothic alphabet?",
    "**27 letters** in the standard Wulfila inventory (some sources debate exact count including numerals). Each maps to a phoneme — pedagogically cleaner than English orthography. [attested]")

add("What is the Gothic letter hwair called and what does it look like?",
    "**ƕ** is called **hwair** — resembles a Greek υ with crossbar or 6-like form depending on font. Represents /hʷ/. Essential for distinguishing *ƕan* 'when' from *han* (if attested minimal pairs). [attested script]")

add("What runic connections exist between Gothic and Elder Futhark?",
    "Both Gothic script and **Elder Futhark** descend from a shared Germanic literate tradition. Gothic **þ, ƕ** graphs echo runic values. The **Ring of Pietroassa** (if Gothic) would bridge runic epigraphy and Wulfila literacy — reading disputed. [partial/disputed]")

add("What is the Ring of Pietroassa and its relevance to Gothic?",
    "**Ring of Pietroassa** — gold ring with runic inscription in Romania, possibly 4th-c. Gothic. Transcription disputed; some scholars reject as Gothic. If authentic, it links **runic epigraphy** to Wulfila-era Goths. DAVID tags [disputed] until corpus-confirmed.")

add("How does the Gothic letter 𐌰 relate to Greek and runic ancestry?",
    "Gothic **𐌰** (a) derives from Greek **α** in uncial tradition — the alphabet is primarily Greek-shaped with Germanic phonemic supplements. Visual provenance shots can show Greek → Gothic letter evolution. [attested paleography]")

add("Does Gothic use numeric letter values like Greek?",
    "Gothic manuscripts employ **Greek-style numerals** with Gothic letters as numerals in some traditions — useful for codicological context but secondary to phonology tutoring. [attested in manuscript tradition]")

add("What font considerations apply to Gothic script in video production?",
    "Use **Unicode Gothic block** (U+10330–U+1034F) or scholarly fonts (Vulcanius, Skeirs). Avoid Latin transliteration-only when teaching script episode — audience should see **𐌰𐍄𐍄𐌰** alongside Latin transliteration *atta*. [studio guidance]")

add("How do you transliterate Wulfila script for DAVID corpus entries?",
    "**Standard transliteration:** Latin letters with þ, ƕ, q, ā (macrons optional), no capitalization in diplomatic style. Example: *Atta unsar þu in himinam*. Align with Streitberg for searchable corpus. [scholarly convention]")

add("What is the relationship between Latin, Greek, and Gothic letter order?",
    "Gothic alphabet follows **Greek letter order** with insertions for Germanic phonemes — not Latin order. Pedagogical point: Wulfila was a Greek-literate bishop adapting a familiar sequence. [attested]")

add("Which Gothic sounds required inventing new letters?",
    "Sounds requiring new or adapted graphs: **/θ/** (þ), **/hʷ/** (ƕ), **/kʷ/** (q), and distinct long-vowel notation (ei, ai, au digraphs). These are the **captioning-critical** graphemes for AI QA. [attested]")

add("Compare Gothic script adoption to OE runic-latin hybrid tradition.",
    "Old English used **Latin** with thorn (þ) and eth (ð) eventually; Gothic created a **full alphabet** earlier and more systematically. Both show runic DNA in þ — comparative paleography episode hook. [historical]")

add("What Unicode range encodes Gothic script?",
    "**Unicode block U+10330–U+1034F** (Old Italic/Gothic). Ensure rendering in captions/subtitles — fallback to Latin transliteration if platform lacks font support, with on-screen note. [technical]")

add("How does Wulfila script handle word boundaries and punctuation?",
    "Manuscripts use **scriptio continua** or sparse punctuation — modern editions add spaces and commas. Video captions should add spacing for readability while noting this is editorial [scholarly], not manuscript-native. [attested practice]")

add("What paleographic features distinguish Codex Argenteus handwriting?",
    "CA features **silver/gold ink** on purple vellum, uncial-style letterforms, ornamental initials. For provenance videos: show letter **𐌰** forms distinct from Carolingian minuscule students know. [attested]")

add("Did Goths write in runes for everyday use while Wulfila used his alphabet for scripture?",
    "**Hypothesis:** Runic literacy may have coexisted for **short inscriptions** while Wulfila script served **biblical codices**. Evidence is thin — do not assert runic Bibles. Tag popular claims [hypothesis]. [research gap]")

add("What is the tutoring hook linking runes to Wulfila's þ?",
    "The thorn in your keyboard has a **Gothic and runic passport** — Wulfila lifted /θ/ from the futhark tradition to write *þu* 'thou' in a Bible that still shapes how we reconstruct Proto-Germanic.")

add("How should on-screen captions align with Wulfila graphemes in video?",
    "**Captioning system:** script_notes maps Wulfila graphemes 1:1 to phonemes — use for on-screen caption alignment. One grapheme per phoneme timing slot; highlight þ, ƕ, q in lesson episodes. [studio_handoff]")

add("What is Skeirs font and why does it matter for DAVID?",
    "**Skeirs** and similar fonts render Unicode Gothic for subtitles. Test render on target platform (YouTube, Premiere) before production — missing glyphs break the script episode. [technical]")

add("How does the Gothic letter þ differ from English thorn usage?",
    "Gothic **þ** is strictly /θ/ — English later used thorn for both /θ/ and /ð/ in some periods. Gothic also has **d** for /ð/ in medial position. Cleaner phoneme-graph mapping than English. [reconstructed]")

add("What Latin letters did Wulfila adopt without modification?",
    "Most consonants align with Latin values: **p, t, k, f, s, m, n, l, r, h** (plain h), **b, d, g** (with allophony). Vowel letters follow Greek quality conventions more than English. [attested]")

add("Explain the Greek uncial basis of Wulfila's letterforms.",
    "Wulfila modeled letterforms on **Greek uncial** hands his scribes knew — hence Gospel Greek dependency and visual similarity to Coptic/Greek biblical manuscripts of the era. [attested paleography]")

add("What provenance should appear on a Gothic script lesson lower-third?",
    "**Wulfila alphabet, c. 350 CE** — invented for Gothic Bible translation; 27 letters; Codex Argenteus primary witness; Uppsala University Library. Label: scholarly reconstruction. [attested]")

# --- AI AUDIO & VIDEO PRODUCTION (86-110) ---
add("What phonological mistakes does AI audio typically make when generating Gothic speech?",
    "**Gothic — common AI audio errors:**\n\nEnglish speakers err on dental θ/ð (not stops), fricatives β/ɣ/x (intervocalic), long vowels sustained (macrons), ƕ as [ʍ] or aspirated hw, no schwa reduction, Greek-like vowel qualities; slow pacing with geminates held; laryngeals as [x/h] uvular/fricative.")

add("Generate Grok Imagine audio guidance for producing Gothic speech in a documentary.",
    "**Gothic — Grok Imagine audio guidance:**\n\nCommit to: dental θ (þ), not English th-as-stop; intervocalic β/ɣ for b/g; sustain long vowels (ei = [iː]); ƕ as [ʍ] or aspirated hw; q as [kʷ]. Approximate: Greek-like pure vowels; trilled r. Avoid: English schwa reduction; voicing þ as [ð]; collapsing ƕ to /h/; clipping geminates. Flag: all vowels [reconstructed] — label 'Scholarly reconstruction of Gothic'.\n\n**Confidence:** high\n**Label as:** 'Scholarly reconstruction of Gothic' — never present as definitive.")

add("What specific AI error affects Gothic word 'þu' (thou)?",
    "AI TTS often renders **þu** as /tu/ or /su/ — substituting stop or sibilant for /θ/. QA check: initial consonant must be voiceless dental fricative [θ]. High visibility word in Lord's Prayer lessons. [production QA]")

add("How should AI avoid English vowel reduction in Gothic polysyllables?",
    "English TTS inserts **schwa** in unstressed syllables — Gothic reconstruction requires **full vowel qualities** in secondary syllables unless comparative evidence supports reduction. Do not apply English stress-shaving. [production guidance]")

add("What lip-sync challenges does Gothic pose for AI avatar video?",
    "Visemes for **θ**, **x** ([χ]), and **kʷ** lack clean English mappings — use IPA-driven viseme override tables. Long vowels need **extended mouth openness** timing vs English clipping. [studio guidance]")

add("How should a narrator pace Gothic scripture for YouTube?",
    "**Pacing:** Deliberate/enunciated for scripture (moderate tempo); hold geminates; pause at clause boundaries matching Greek source punctuation in editions. Not conversational modern English speed. [prosody]")

add("What QA checklist applies before publishing Gothic audio?",
    "**Gothic audio QA:**\n1. þ = [θ] throughout\n2. ƕ ≠ h\n3. Long vowels ≥ 2× short\n4. Geminates audible in *atta*, *kunnan*\n5. No English schwa\n6. Intervocalic fricatives for b/d/g\n7. On-screen [reconstructed] label\n8. Source citation in description")

add("How should video lesson 03 teach Gothic þ?",
    "**Lesson 03 — þ → [θ]:**\n- Minimal pair drill: *þu* vs hypothetical *tu* (wrong)\n- Camera: mouth interdental fricative\n- Anchor text: *Atta unsar **þu** in himinam*\n- Compare English 'thin' not 'this'\n- Caption sync: highlight 𐌸 [reconstructed]")

add("How should video lesson 04 teach Gothic ai?",
    "**Lesson 04 — ai ≈ [ɛː] or /ai/:**\n- State Braune/Wright model used\n- Example: *hlaifs*, *atta* environment\n- Warn AI diphthongization error\n- Label disputed allophony on screen [reconstructed]")

add("How should video lesson 05 teach Gothic ei?",
    "**Lesson 05 — ei → [iː]:**\n- Sustained vowel drill — metronome 2× short i\n- Example: *þeins*, *þeina*\n- Error flag: English 'ay' diphthong\n- Caption: 𐌴𐌹 as single long phoneme")

add("What cold-open audio should a Gothic episode use?",
    "Cold-open: reconstructed **Atta unsar** line at moderate tempo with full geminate **tt**, clear **þ**, long **ei** in *þein* — immediate phonological hook before provenance narration. [studio]")

add("How do you caption Gothic ƕ in subtitles for English audiences?",
    "Display Wulfila graph **ƕ** with IPA tooltip **[ʍ]** or 'hw' mnemonic — never silent. Example: *ƕan* 'when' with superscript IPA in educational overlay. [captioning]")

add("What reference clips help voice actors approximate Gothic x?",
    "Use **Scots 'loch'** or German **Bach** [x] for velar fricative — not English /h/. Provide side-by-side IPA clip in actor brief. [production]")

add("Should Gothic audio use modern English accent base?",
    "No — start from **IPA targets**, not RP/GA accent. English accent base imports wrong θ, r, and vowel reduction. Neutral phonetic baseline preferred. [casting guidance]")

add("How should DAVID label reconstructed Gothic in video credits?",
    "**Pronunciation:** Scholarly reconstruction per Braune/Wright/Streitberg — not attested native speech. Manuscript: Codex Argenteus [attested text]. Audio: [reconstructed].")

add("What duration ratio should long vs short vowels have in Gothic TTS?",
    "Target **2:1** long-to-short vowel duration minimum in QA waveform review. AI models often compress to ~1.3:1 — reject and regenerate. [QA metric]")

add("How does AI confuse Gothic d and English th?",
    "Gothic **d** medially = [ð] (voiced dental fricative); **þ** = [θ] always. AI trained on English may voice þ or devoice d. Separate QA rules per grapheme. [production]")

add("What background music tempo fits Gothic scripture narration?",
    "Subdued **legato** underscore at 60–80 BPM — do not compete with geminate consonant hits. Scripture register is solemn, not upbeat vlog pacing. [creative guidance]")

add("How to test whether AI collapsed ƕ and w in Gothic?",
    "Minimal environment: compare **ƕan** 'when' with **was** — if initial consonants sound identical, regenerate. Spectral analysis: ƕ should show labial friction co-articulation. [QA]")

add("What shot list covers a Gothic pronunciation episode?",
    "**Shot list:**\n1. Cold open — Atta unsar IPA\n2. Natural IPA demonstration\n3. Lesson þ → [θ]\n4. Lesson ai ≈ [ɛː]\n5. Lesson ei → [iː]\n6. Full line performance\n7. Provenance — Codex Argenteus\n\nMatches DAVID latin_gothic_v1 production template.")

add("How should errors in Gothic AI audio be annotated for retraining?",
    "Log error type (θ→t, ƕ→h, vowel clip, schwa insert) with **timestamp + grapheme + expected IPA** in qa_report.json for DAVID feedback loop. [pipeline]")

add("What microphone technique suits Gothic fricative density?",
    "Close-mic **pop filter** essential for θ, x, ƕ bursts; slight off-axis placement reduces sibilance on *s*, *z* while keeping fricative definition. [audio engineering]")

add("Should Gothic video use dramatic reverb?",
    "Light **cathedral reverb** acceptable for scripture mood — avoid masking geminate timing. Dry pronunciation lessons should be nearly anechoic for phoneme clarity. [mixing]")

add("How to synchronize Wulfila captions with reconstructed audio?",
    "Build **grapheme-tier** captions in Premiere/DaVinci — one event per Wulfila letter cluster; align to phoneme timings from IPA script breakdown. No English translation on same line during drill shots. [studio_handoff]")

add("What is the confidence note for Gothic documentary narration?",
    "**Confidence:** high for core segments; minor nasal/quality variants possible. Always say 'reconstructed pronunciation' in voice-over within first 30 seconds. [legal/scholarly]")

# --- TRANSLATION METHODOLOGY (111-130) ---
add("What translation methodology did Wulfila likely use?",
    "**Greek-source translation** with phrase-level calquing — word order often follows Greek when Gothic syntax allows. DAVID revival translations should cite Greek parallel before inventing Germanic-only idioms. [attested technique]")

add("How should DAVID translate new English concepts into Gothic revival drafts?",
    "**Revival protocol:**\n1. Search attested Gothic lexicon (Streitberg, Wright)\n2. If absent, build from attested morphemes with comparative chain\n3. Tag [reconstructed] or [hypothesis]\n4. Never present neologism as CA reading\n5. Prefer gloss + English in tutoring over faux-fluent Gothic dialogue")

add("What is the difference between Wulfila translation and modern Gothic revival?",
    "Wulfila's text is **[attested]** 4th-c. biblical Greek calque. Modern 'Gothic revival' is **[reconstructed]** extension using comparative grammar — valid for pedagogy, invalid as manuscript citation. DAVID must keep the boundary visible.")

add("How does Greek word order influence Gothic biblical prose?",
    "Gothic often preserves **Greek clause order** in Gospels — e.g. verb-second in narrative but Greek-permitted fronting. Syntactic lessons should cite Greek Vorlage before calling order 'natural Gothic'. [attested]")

add("What role do Latin Vulgate parallels play in Gothic exegesis?",
    "Secondary collation tool for **damaged Ambrosianus** passages — not Wulfila's primary source. Use Vulgate for [hypothesis] restorations only. [methodology]")

add("How should a DAVID editor handle archaic English 'thou' in Gothic subtitles?",
    "Gothic **þu** maps to archaic **thou** in liturgical English tradition — acceptable for Lord's Prayer subtitles. Mark that English thou is **translationese**, not phonetic equivalent. [editorial]")

add("What fidelity standard applies to Gothic scripture retranslation?",
    "Manuscript fidelity > modern readability. Cite **Streitberg verse** before paraphrase. If paraphrasing for video, split screen: [attested] vs [modern gloss]. [DAVID editorial]")

add("How do you gloss an unattested Gothic concept for tutoring?",
    "Structure: **English term** → attested nearest Gothic (**with case**) → comparative OE/ON → [reconstructed] revival proposal if needed → explicit uncertainty tag. Never skip the tag.")

add("What translationese traps appear in English-to-Gothic revival?",
    "**Traps:**\n- Importing English word order\n- Using Latin roots where Greek calque expected\n- Voicing þ as 'th' of 'the'\n- Inventing umlauted vowels from OE analogies\n- Treating Skeireins style as biblical style universally")

add("How should proper names be handled in Gothic translation?",
    "Biblical names follow **Greek transliteration** in Wulfila (*Iesus*, *Iohannes*) — do not Anglicize to modern English in attested readings. [attested]")

add("What editorial layer applies when writing about Gothic for general audiences?",
    "Living-language idiom for English narration; **Gothic terms with gloss** for linguistic content; never faux-native Gothic dialogue unless marked **revival draft [reconstructed]**. [DAVID editorial rule]")

add("How does DAVID's forensic mandate apply to Gothic translation claims?",
    "**Corpus before grammar** — every translated form must trace to CA/A manuscript, scholarly edition, or tagged comparative reconstruction. Unsourced 'Gothic for X' is fan fiction, not DAVID output.")

add("What Greek particles map to Gothic 'jah'?",
    "**jah** = 'and' — extremely high frequency, maps Greek **καί** and sometimes **δέ**. Core conjunction for syntax mining. [attested]")

add("How should translators note Arian theology in lexical choices?",
    "Some theological terms may reflect **Arian framing** — cite patristic context when discussing *guþ*, *sunus*, *Xristus*. Linguistic entries can note theology; do not anachronistically Nicene-normalize attested forms. [historical]")

add("What workflow applies when expanding Gothic corpus entries?",
    "**Workflow:** SELECT verse → SURVEY CA/A witnesses → EXTRACT transliteration → COMPARE Greek parallel → BUILD morphology note → TAG confidence → QUEUE next research task. [DAVID loop]")

add("How do you present conjectural emendations in Gothic editions?",
    "Bracket conjecture: **[emended]** or italicize with footnote to Streitberg apparatus — never read conjecture as gold audio in documentary without on-screen flag. [methodology]")

add("What English Bible tradition best aligns with Gothic Lord's Prayer subtitles?",
    "**Tyndale/KJV archaism** ('hallowed be thy name') matches *weihnai namo þein* mood better than contemporary 'may your name be kept holy' — but label as translation choice, not Gothic syntax. [editorial]")

add("How should DAVID queue next Gothic research from a corpus entry?",
    "Run `research_query_generator.py --language gothic` after each new entry — priorities: expand Ambrosianus collation, grammar tables, History figure links. [pipeline]")

add("What is the return-to-manuscript risk in Gothic popularization?",
    "Popularizers **Anglicize** (*God* not *guþ*, *Jesus* not *Iesus*) and lose script/phonology teaching value. DAVID productions retain Wulfila forms with gloss — highest-risk step is 'making it sound normal'. [editorial risk]")

add("How do translation agents validate Gothic output against corpus?",
    "Cross-check every form in **Streitberg concordance** or wulfila.be search — zero hits triggers [reconstructed] review, not publication as attested. [QA]")

# --- MORPHOLOGY (131-165) ---
add("What grammatical cases does Gothic nouns show?",
    "Gothic nouns inflect for **nominative, accusative, genitive, dative** (and vocative remnants) across **a-, ō-, i-, u-, an-, ōn-, r-, nd-** declension classes. Full case system better preserved than in modern English. [attested]")

add("Decline Gothic 'atta' (father) in singular.",
    "**atta** (m. a-stem): nom. atta, acc. attan, gen. attins, dat. attin. Familiar from Lord's Prayer vocative/nominative **Atta**. [attested]")

add("What is the Gothic strong verb class of 'qiþan' (to say)?",
    "**qiþan** — strong verb class V (Germanic taxonomy); preterite **qap**, participle **qipans**. High-frequency Gospel verb. [attested]")

add("What is the preterite of Gothic 'wairþan' (to become)?",
    "**wairþan** → preterite **warþ** 'became/was'. Central to copular/passive periphrasis in Gospels. Compare OE *weorþan*, ON *verða*. [attested]")

add("How does Gothic mark plural in 'sunjus' (sons)?",
    "**sunus** (m. u-stem) → nom. pl. **sunjus** with **-jus** ending. Compare OE *sunu*, ON *synir* (different plural innovation). [attested]")

add("What demonstrative is 'sa, so, þata'?",
    "**sa** (m.), **so** (f.), **þata** (n.) = 'that/the' — three-gender demonstrative system. Foundation for definite article development in later Germanic (partially). [attested]")

add("Explain Gothic weak verb class I with 'nasjan' (to save).",
    "**nasjan** (weak class I) → pret. **nasta** 'saved'. Frequent in salvation theology vocabulary. Thematic vowel **-jan** with dental preterite suffix. [attested]")

add("What personal pronouns appear in the Lord's Prayer opening?",
    "**unsar** 'our' (poss. pl.), **þu** 'thou' (2sg nom.), **þein** 'thy' (poss. sg.). No plural 'you' in opening — intimate singular address tradition. [attested]")

add("What is the Gothic infinitive ending?",
    "Infinitives end in **-an**: *qiþan*, *haban*, *gaggan*. Comparable to OE *-an*, German *-en*. [attested]")

add("How are Gothic adjectives declined?",
    "Adjectives show **strong vs weak** declension (definite vs indefinite) with gender agreement — e.g. *gods* 'good' matches noun gender/case/number. [attested]")

add("What modal verb is Gothic 'mag' (can)?",
    "**mag** (pres.) / **mahta** (pret.) = 'can, may' — preterite-presents class. *Magus* also 'boy/servant' — homonym caution in glosses. [attested]")

add("Provide morphology note for Gothic 'weihnan' (to be holy).",
    "**weihnan** — weak verb; optative **weihnai** in Lord's Prayer; adj. *weihs* 'holy'. Related to OE *hālig*, ON *heilagr*. [attested]")

add("What is Gothic dual number status?",
    "Dual number **rare/limited** compared to Old Norse — some pronominal duals attested; not as robust as ON *vit*. Note absence when comparing branches. [attested partial]")

add("How does Gothic mark passive?",
    "Passive often via **wairþan** + past participle or middle-like constructions — study Gospel periphrasis rather than importing Latin passive assumptions. [attested]")

add("What is the Gothic present participle of 'gaggan' (to go)?",
    "**gaggan** → pres. part. **gaggands** 'going' — used in narrative progressives. Compare OE *gān*, ON *ganga*. [attested]")

add("Explain strong verb ablaut in Gothic 'singan' (to sing).",
    "**singan** — class III; vowel alternation singan/sang/runans pattern (verify exact forms in Wright). Use for ablaut pedagogy vs OE *singan*. [attested]")

add("What enclitic particles exist in Gothic?",
    "Gothic uses postposed **-uh**, **-th** particles in some constructions — Skeireins and Gospels provide evidence. Important for syntax episode beyond Lord's Prayer. [attested]")

add("How are Gothic comparatives formed?",
    "Comparative **-iza**, superlative **-ists** suffixes on adjective base — e.g. *maiza* 'greater'. Regular Germanic pattern. [attested]")

add("What is the genitive singular ending for a-stem masculines?",
    "Typically **-is**: *attins* 'father's', *gudis* 'God's'. High-frequency Gospel ending. [attested]")

add("What reflexive forms exist in Gothic?",
    "Reflexive **sik** (acc.) with verbs like *nasjan sik* — compare OE *sylf*, ON *sik*. [attested]")

add("How does Gothic mark definiteness?",
    "Weak adjective declension + demonstrative **sa/so/þata** patterns approach definite article function — intermediate stage before fully grammaticalized articles in daughter languages. [attested]")

add("What numerals are attested in Gothic?",
    "**ains** 'one', **twai** 'two', **þreis** 'three' — gender agreement in numerals 1–3. Useful for elementary morphology drills. [attested]")

add("Provide morphology sketch for Gothic verb 'haban' (to have).",
    "**haban** (weak?/special — verify class): pres. haba, pret. habaida, part. habands. Cognate OE *habban*, ON *hafa*. [attested]")

add("What subjunctive/optative role appears in biblical Gothic?",
    "Optative **-ai** endings (e.g. *weihnai*) express wish/jussive in prayers — map carefully to Greek subjunctive/optative categories. [attested]")

add("How do Gothic prepositions govern case?",
    "**in** + dat. (locative), **us** + dat./acc. (motion), **bi** + dat. — preposition-case government matches Indo-European patterns. [attested]")

add("What is the dative singular ending of 'himins'?",
    "**himinam** — dative singular masculine a-stem. Locative sense with *in*. [attested]")

add("Morphology note: Gothic 'frauja' (lord).",
    "**frauja** (m.) = 'lord, master' — vocative address for Christ; gen. *fraujins*. Compare OE *frēa*, ON *frúa*. [attested]")

add("What participial forms appear in Gothic Gospel prose?",
    "Present **-ands**, past **-ans/-þs** participles frequent in narrative chaining — Greek participle calques. [attested]")

add("How is negation expressed in Gothic?",
    "**ni** + verb — standard negator. *Ni nimaiþ* etc. in commandments. Simple, high-frequency. [attested]")

add("What interrogative word is Gothic 'ƕan' (when)?",
    "**ƕan** — wh-word with initial **ƕ** — phonology + morphology combo lesson. [attested]")

add("Morphology: Gothic 'broþar' (brother).",
    "**broþar** (m.) irregular kinship noun — plural **broþrjus**. Cognate OE *brōþor*, ON *bróðir*. [attested]")

add("What vestiges of vocative exist in Gothic?",
    "**Atta** in prayer may function as vocative address without distinct ending — some a-stem vocatives conflate with nominative. [attested]")

add("How are Gothic compound nouns stressed?",
    "Primary stress on **first element**; secondary stress pattern in compounds per PGmc rule — affects pronunciation drills for long compounds. [reconstructed]")

add("What agent suffix appears in Gothic 'areis' (herald)?",
    "Agent nouns in **-areis** from Greek loan strata — compare *airzeis* 'heretic'. Shows Greek derivational morphology in Christian vocabulary. [attested]")

add("Give a morphology research query for Gothic after Lord's Prayer analysis.",
    "**Research query:** Extract all optative **-ai** forms in Codex Argenteus Gospels; tabulate by verb class; compare Greek Vorlage mood mapping. [queue]")

# --- OLD NORSE & OLD ENGLISH COMPARISON (166-190) ---
add("Compare Gothic 'atta' with Old English and Old Norse words for 'father'.",
    "Gothic **atta** ≈ OE *fæder* (full form) but *atta* is baby-talk cognate; ON *faðir*. Gothic preserves the nursery form [attested] in prayer address — hook for Germanic kinship vocabulary.")

add("How does Gothic 'broþar' compare to OE and ON?",
    "Gothic **broþar**, OE **brōþor**, ON **bróðir** — regular PGmc *-þ- reflex; all show dental fricative/reflex in branch-specific ways. [attested comparative]")

add("Compare Gothic 'hlaifs' (bread) with OE and ON cognates.",
    "Gothic **hlaifs**, OE **hlāf** (loaf/bread), ON **hleifr** — food vocabulary stable across branches; demonstrates **hl-** initial cluster preservation. [attested]")

add("How does Gothic 'guþ' compare to OE 'god' and ON 'guð'?",
    "Nearly identical across Goth. **guþ**, OE **god**, ON **guð** — rare theological core lexeme with minimal shape change. [attested]")

add("What does Gothic reveal about PGmc that OE and ON obscured?",
    "Gothic preserves **/z/**, lacks umlaut products, retains some vowel distinctions merged in OE/ON, and documents earlier Christian loan timing. East vs West/North split lesson. [comparative]")

add("Compare Gothic 'sunus' with OE 'sunu' and ON 'sunr'.",
    "Gothic **sunus**, OE **sunu**, ON **sunr** (rhotacism of *z). Classic rhotacism comparison table entry. [attested]")

add("How do Gothic and Old English handle 'th' sounds?",
    "Gothic: **þ** = /θ/, **d** medially often [ð]. OE: **þ/ð** graphical overlap later. Gothic has cleaner phoneme-letter mapping. [comparative]")

add("Compare Gothic 'qiþan' with OE 'cwæþan' and ON 'segja'.",
    "Meaning 'say': Goth. **qiþan** (/kʷiθan/), OE **cwæþan**, ON **segja** — different verb class outcomes but same root. Gospel high-frequency. [attested]")

add("What East Germanic features distinguish Gothic from West Germanic OE?",
    "No i-umlaut, different ablaut in some verbs, **-eis** Greek agent suffixes, biblical Greek calque syntax — East branch conservatism plus Christian stratum. [comparative]")

add("Compare Gothic and Old Norse plural formation in u-stems.",
    "Gothic **sunjus** vs ON **synir** — different plural innovations from same *sunus* base. Morphology lesson on branch divergence. [attested]")

add("How does Gothic 'wairþan' compare to OE 'weorþan' and ON 'verða'?",
    "All mean 'become' — Goth. **wairþan**, OE **weorþan**, ON **verða**. Central strong verb across branches. [attested]")

add("What cognate is Gothic 'weihs' (holy)?",
    "Gothic **weihs**, OE **hālig** (different formation), ON **heilagr** — holiness vocabulary; note OE uses different adj. formation though concept aligns. [comparative]")

add("Compare Gothic 'hairto' (heart) with OE and ON.",
    "Gothic **hairto**, OE **heorte**, ON **hjarta** — common Germanic core vocabulary; dental suffix variation. [attested]")

add("How does Gothic lack of rhotacism appear in cognate sets?",
    "Where Gothic shows **z** or **s** from *z*, West/North may show **r** — use *azēt* vs *are* type pairs carefully with Streitberg attestations only. [comparative method]")

add("Compare Gothic 'gaggan' with OE 'gān' and ON 'ganga'.",
    "Motion verb: Goth. **gaggan**, OE **gān**, ON **ganga** — related suppletive/near-cognate set for 'go'. [attested]")

add("What reading order should a Germanic comparative course use?",
    "**Gothic first** (4th c., conservative) → **Old English** (West) → **Old Norse** (North) — shows divergence from shared PGmc baseline with [attested] texts at each step.")

add("How does Gothic biblical lexicon differ from OE biblical English?",
    "Gothic is **4th-c. Greek calque**; OE biblical tradition is **Latin/Vulgate mediated** centuries later — different loan chronology and theology. [historical]")

add("Compare Gothic 'frijōnds' (friend) with OE and ON.",
    "Gothic **frijōnds**, OE **frēond**, ON **frándi** — i-stem friendship vocabulary; useful for adj./noun declension compare. [attested]")

add("What ON innovation is absent in Gothic?",
    "Definite article **-inn/-in** system fully developed in ON — Gothic stops at demonstrative stage. Article grammaticalization timeline lesson. [comparative]")

add("What OE innovation is absent in Gothic?",
    "**i-umlaut** products throughout OE paradigms — absent in Gothic; West Germanic sound change post-divergence. [comparative]")

add("Compare Gothic 'hw' complex with OE 'hw' and ON 'hv'.",
    "Gothic **ƕ** (/hʷ/), OE **hw** spellings, ON **hv** — all preserve pre-merger distinction lost in modern English 'which'='witch' for many speakers. [phonological]")

add("How does Gothic 'aiw' (ever) compare to OE 'ā' and ON 'ei'?",
    "Temporal adverb: Goth. **aiw**, OE **ā**, ON **ei** — eternity/time vocabulary in theological texts. [attested]")

add("What comparative table should DAVID publish for Gothic-OE-ON 'give'?",
    "Goth. **giban** (verify attestation), OE **giefan/give**, ON **gefa** — dative *gaf* forms in paradigm table with [attested] tags per branch.")

add("Why call Gothic a 'comparative goldmine' for DAVID tutoring?",
    "Gothic vs ON/OE reveals **East vs North/West** branch splits with [attested] 4th-c. prose — earlier than most OE texts, richer than runic ON snippets. Flagship DAVID hook.")

add("Compare Gothic 'managei' (multitude) with OE 'menigu'.",
    "Crowd/multitude: Goth. **managei**, OE **menigu** — abstract noun formations in Gospel narrative. [attested]")

# --- DAVID PROTOCOL, HOOKS, SOURCES (191-200) ---
add("What is Gothic's revival tier in DAVID's registry?",
    "**Gothic** — status: **extinct**; revival tier: **high** (extinct but corpus supports serious reconstruction). Family: East Germanic; period: c. 4th century CE. [registry]")

add("What are the key scholarly sources for Gothic pronunciation reconstruction?",
    "**Gothic — sources:**\n\n- Braune's Gothic Grammar (with Balg)\n- Joseph Wright, Gothic grammar\n- Wulfila Project (wulfila.be)\n- Streitberg, Lehmann (via Wikipedia phonology)\n- UT Austin EIEOL; scholarly syllabi")

add("Summarise the scholarly consensus on Gothic pronunciation reconstruction.",
    "**Gothic — scholarly consensus:**\n\nHigh-confidence reconstruction via Wulfila Codex Argenteus + Greek/Latin transcriptions + PGmc comparisons (Braune/Wright/Streitberg consensus); minor disputes flagged on diphthong monophthongization timing and nasalization extent.")

add("Generate a memorable tutoring hook for a Gothic language episode.",
    "Gothic is the oldest substantially attested Germanic language — written by a bishop who invented an alphabet to translate the Bible into a language that was about to vanish.")

add("Generate a YouTube episode intro for a Gothic tutoring series.",
    "**Episode intro: Gothic**\n\nOpening hook: Gothic is the oldest substantially attested Germanic language — written by a bishop who invented an alphabet to translate the Bible into a language that was about to vanish.\n\n**Key text anchor:** Wulfila's Bible translation (4th century CE)\n\n**Why it matters today:** Gothic preserves Proto-Germanic features lost in every other branch.\n\n**Scaffold:** Phonology → Script → Key phrases → Historical context → Modern legacy")

add("Provide a scholarly IPA transcription of this Gothic text with confidence assessment.",
    "**Reconstructed IPA:** /ˈatːa ˈunsar θuː in ˈhiminaːm ˈwiːhnai ˈnaːmoː θeiːn/\n\n**Confidence:** high — Braune/Wright standard (PGmc vowel correspondences + orthography); minor nasal/quality variants possible but core segments undisputed.\n\n**Mark as [reconstructed] in all corpus and production use.**",
    "Atta unsar þu in himinam, weihnai namo þein")

add("Provide a word-by-word gloss of the opening of this Gothic text.",
    "**Gothic gloss — Atta unsar (Lord's Prayer)**\n\nFull text: Atta unsar þu in himinam, weihnai namo þein\nTranslation: Our Father, thou in heaven, hallowed be thy name\nSource: Codex Argenteus, Uppsala University Library [attested]\n\n**Word-by-word:**\n- **Atta** — father (nom./voc. sg.)\n- **unsar** — our (poss. pl.)\n- **þu** — thou (2sg nom.)\n- **in** — in (prep. + dat.)\n- **himinam** — heaven (dat. sg.)\n- **weihnai** — be hallowed (opt. 3sg)\n- **namo** — name (nom. sg.)\n- **þein** — thy (poss. sg.)",
    "Atta unsar þu in himinam, weihnai namo þein")

add("This Gothic text is in the corpus. What is the next priority research task?",
    "**Next research task — Atta unsar (Lord's Prayer):**\n\nConfidence is [attested] — text is well-attested. Priority: expand corpus with parallel Ambrosianus texts; add grammatical analysis of optative *weihnai*; build full Lord's Prayer IPA breakdown; cross-reference History links (Wulfila).",
    "Text: Atta unsar þu in himinam, weihnai namo þein\nSource: Codex Argenteus, Uppsala University Library\nConfidence: [attested]")

add("Describe the prosody and rhythm of Gothic for a video narrator.",
    "**Gothic — prosody:**\n\n- **Rhythm:** Stress-timed, clear syllable structure\n- **Pitch:** Accentual (no tone)\n- **Pacing:** Deliberate/enunciated for scripture (moderate tempo)")

add("What language family does Gothic belong to?",
    "Gothic belongs to the **East Germanic** family. Period: c. 4th century CE. Status: extinct. Revival tier: high — extinct but corpus supports serious reconstruction work.")

assert len(pairs) == 200, f"Expected 200 pairs, got {len(pairs)}"

out_path = Path(__file__).parent / "gothic_training_200.jsonl"
with out_path.open("w", encoding="utf-8") as f:
    for p in pairs:
        f.write(json.dumps(p, ensure_ascii=False) + "\n")

print(f"Wrote {len(pairs)} pairs to {out_path}")
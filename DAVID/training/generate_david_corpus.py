"""generate_david_corpus.py -- DAVID main-corpus expansion mined from DAVID research.

6 shards x 30 = 180 Alpaca pairs (instruction/input/output), ASCII-safe, LF.
Grounded in DAVID/languages/, communication-modalities/, reports/, research_ops/.
Confidence tags follow the DAVID protocol: [attested] | [reconstructed] | [hypothesis].
IPA is rendered in ASCII / X-SAMPA (existing shards use raw IPA; these stay ASCII
per the expansion spec). Languages without source files (Classical Japanese,
Classical Nahuatl, Old Church Slavonic, Anglo-Norman, Tudor English) use
established general linguistics only -- NO fabricated vocabulary or translations.

Run:  python generate_david_corpus.py            (write + validate)
      python generate_david_corpus.py --check    (validate only)
Output: DAVID/training/david_corpus_T1..T6_*.jsonl
"""
from __future__ import annotations
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def P(instruction, output, input=""):
    return {"instruction": instruction, "input": input, "output": output}


# ===========================================================================
# T1 -- DEAD LANGUAGES
# ===========================================================================
T1 = [
    P("Why is Sumerian pronunciation the least certain in DAVID's registry?",
      "Sumerian is a language isolate with no living descendants, so its phonology cannot be checked against any related tongue. [reconstructed/hypothesis] Pronunciation is inferred almost entirely from how Akkadian scribes transcribed it in cuneiform and from the Emesal dialect contrast. Tag Sumerian audio [hypothesis] -- it carries the lowest confidence in the registry (Jagersma/Thomsen conventions)."),
    P("Translate this attested Sumerian line and state its source.",
      "Translation: 'In those days, in those distant days...' [attested text]. Source: The Instructions of Shuruppak, ETCSL corpus 5.6.1, line 1. The written text is attested; any spoken rendering of it is [reconstructed] because cuneiform does not write vowels reliably.",
      "ud re-a ud su-ra re-a"),
    P("Is Sumerian related to Akkadian, and how do we reconstruct its sounds?",
      "No. Sumerian is a language isolate; Akkadian is Semitic (Afro-Asiatic). They shared the cuneiform script and coexisted in Mesopotamia, which is exactly why Akkadian scribal transcriptions are the main window for reconstructing Sumerian phonology [reconstructed]. The disputed value of the sign transliterated 'g-tilde' (velar nasal vs velar stop) is a standing open question [hypothesis]."),
    P("What makes Akkadian's emphatic consonants hard to reconstruct?",
      "Akkadian (Semitic, c. 2500 BCE-1st c. CE, cuneiform, fully deciphered) has an emphatic series usually transliterated t-dot, q, s-dot. Whether they were ejective or pharyngealized is conventional and still debated [reconstructed]. Other features are firmer: mimation (final -m on nouns) was pronounced, and the sibilant 'sh' (X-SAMPA /S/) was distinct from s and z."),
    P("Translate this attested Akkadian phrase and give its source.",
      "Translation: 'He who saw the Deep' [attested] -- the opening of the Standard Babylonian Epic of Gilgamesh. Source: training_pack_akkadian.md (Post 5). The script and meaning are attested; Standard Babylonian literary vocalization is [reconstructed] at medium-high confidence (Huehnergard, von Soden).",
      "sha nagba imuru"),
    P("Why was Akkadian historically important?",
      "Akkadian was the lingua franca of the ancient Near East for over two thousand years and heavily influenced Aramaic and Hebrew phonology. Its literature (e.g. the Enuma Elish) uses rhythmic parallelism characteristic of epic poetry. [attested historical context]"),
    P("Which gutturals distinguish meaning in Biblical Hebrew?",
      "Three gutturals are phonemically distinct in Biblical Hebrew (Semitic, c. 10th-2nd c. BCE): 'ayin = a voiced pharyngeal (X-SAMPA /?\\/), het = a voiceless pharyngeal/velar (X-SAMPA /X\\/ or /x/), and aleph = a glottal stop (X-SAMPA /?/). [reconstructed, Tiberian tradition] Most of these merged or were lost in Modern Hebrew, so they must be restored for the classical sound."),
    P("Translate and source this attested Biblical Hebrew opening.",
      "Translation: 'In the beginning God created...' [attested text], Genesis 1:1. The consonantal text is attested; the vocalization follows the Tiberian Masoretic tradition (Khan) and is [reconstructed] at high confidence. Cantillation marks (te'amim) are ancient musical/phrasing notation, not optional.",
      "bereshit bara elohim"),
    P("What is begadkefat in Biblical Hebrew?",
      "Begadkefat is the spirantization of the stops b, g, d, k, p, t: without a dagesh they soften (e.g. b becomes v, k becomes a fricative X-SAMPA /x/); dagesh forte doubles or hardens them. [reconstructed, Tiberian] This is why the same letter is read as a stop or a fricative depending on context."),
    P("How is Latin V pronounced in the Classical reconstruction?",
      "Classical Latin V is /w/ (a bilabial approximant), never the English /v/. [reconstructed, restituta] Likewise C and G are always hard /k/ and /g/ with no soft values before e or i, and QU is a single labialized stop X-SAMPA /kw/. Standard: W. Sidney Allen, Vox Latina, ~90% confidence on core consonants."),
    P("Translate this attested Classical Latin sentence and cite it.",
      "Translation: 'Gaul as a whole is divided into three parts' [attested]. Source: Caesar, De Bello Gallico 1.1. The text is attested; Classical (restituta) pronunciation is [reconstructed]. Note vowel length is phonemic in Latin, so longs are held roughly 1.5-2x shorts -- this is meter-critical.",
      "Gallia est omnis divisa in partes tres"),
    P("How does Classical Latin differ from Ecclesiastical Latin?",
      "Classical (restituta) is the reconstructed 1st-c.-BCE sound: V=/w/, C always /k/, no palatalization. Ecclesiastical (Church) Latin is a later Italianate convention: C before e/i becomes X-SAMPA /tS/, V becomes /v/. DAVID defaults to Classical for the dead-language product and treats Ecclesiastical as a distinct living tradition. [reconstructed vs convention]"),
    P("What kind of accent did Classical Attic Greek have?",
      "Ancient Greek had a pitch accent, not a stress accent: one high-tone mora per word. Acute = high/rising, circumflex = a fall on a long syllable, grave = low/default. [reconstructed, Allen Vox Graeca; ~85-90% on segments, ~70% on exact pitch contour] This is musical contour, unlike Modern Greek stress."),
    P("Translate and source this attested Greek maxim (romanized).",
      "Translation: 'Know thyself' [attested] -- the Delphic maxim attributed to Chilon of Sparta. The text is attested; Classical Attic pronunciation is [reconstructed]. Note Greek had a three-way stop contrast: plain /p t k/ vs aspirated (X-SAMPA /p_h t_h k_h/, a breathy puff -- NOT fricatives) vs voiced /b d g/.",
      "gnothi seauton"),
    P("What are the main historical varieties of ancient Greek pronunciation?",
      "Attic (Classical, DAVID default), Koine (Hellenistic, where spirantization of the aspirates begins), and Byzantine (stress accent and near-Modern vowels). [reconstructed] Upsilon in Attic is a rounded front vowel X-SAMPA /y/ (like French 'u'), not /u/."),
    P("What articulatory features define Classical Sanskrit?",
      "Sanskrit (Indo-Aryan, Devanagari abugida) is defined by retroflexes (t-dot, d-dot, n-dot, s-dot -- tongue tip curled back, distinct from dentals), a full plain-vs-aspirated contrast across all five series, and phonemic vowel length. Sandhi (euphonic merging at word boundaries) is mandatory in continuous speech. [attested/reconstructed, Panini and the Shiksha tradition]"),
    P("Translate and source this attested Sanskrit opening (romanized).",
      "Translation: 'I praise Agni, the priest...' [attested], Rigveda 1.1.1. Confidence is very high because an unbroken pandit recitation tradition gives living confirmation of the articulation -- unusual among ancient languages. Standard: Paniniya Shiksha and the Pratisakhyas.",
      "agnim ile purohitam"),
    P("Why is Sanskrit pronunciation unusually well established?",
      "Because Vedic recitation has been transmitted orally and continuously by pandits to the present day, the articulation places and manners described by Panini and the Shiksha texts are confirmed by living practice. Devanagari also maps closely to the sound system. [attested via living tradition]"),
    P("Describe Classical Nahuatl's basic typology.",
      "[No DAVID corpus file -- established general linguistics, flagged.] Classical Nahuatl is Uto-Aztecan, agglutinating/polysynthetic. Its distinctive 'tl' is a single voiceless lateral affricate, and it has a glottal stop (the 'saltillo'). After the conquest it was written in the Latin alphabet by Franciscan friars. Primary attested source: the Florentine Codex (Sahagun). Do not present invented Nahuatl forms; restrict to documented vocabulary."),
    P("What writing systems were used for Classical Nahuatl?",
      "[No DAVID file -- general facts, flagged.] Pre-conquest Nahua used a pictographic/logographic system (codices). After 1521, missionaries adapted the Latin alphabet to write Nahuatl, producing the bulk of the attested classical corpus. Any reconstruction of pre-contact speech is [reconstructed] and must be sourced; never fabricate glyph readings."),
    P("What is Old Church Slavonic and why does it matter?",
      "[No DAVID file -- general facts, flagged.] Old Church Slavonic is the first literary Slavic language, created in the 9th century by Cyril and Methodius to translate scripture, first in the Glagolitic alphabet and later in Cyrillic. It preserves Common Slavic features lost in modern languages, including nasal vowels (the yus letters) and the 'yat' vowel. It remains a liturgical language in Slavic Orthodox churches."),
    P("Which archaic features does Old Church Slavonic preserve?",
      "[No DAVID file -- general facts, flagged.] OCS attests the Common Slavic nasal vowels (written with the yus letters), the reduced vowels (the 'jers'), and the 'yat' vowel -- all of which shifted or merged in the modern Slavic languages. This makes it a key witness for Slavic historical phonology. Specific reconstructions must be [reconstructed]-tagged and sourced."),
    P("What characterizes Classical (Heian) Japanese?",
      "[No DAVID file -- general facts, flagged.] Classical Japanese is the literary language of the Heian period (e.g. the Tale of Genji). It used historical kana orthography that differs from modern spelling, had grammatical forms (e.g. distinct conclusive/attributive verb endings) lost in the modern language, and a different sound system. It is mora-timed with a pitch accent. Do not project modern Japanese forms onto it."),
    P("How does Classical Japanese orthography differ from modern Japanese?",
      "[No DAVID file -- general facts, flagged.] Classical Japanese used 'historical kana usage', where spellings reflect older pronunciations (for example certain kana sequences later contracted in speech but were kept in writing). Modern Japanese spelling was reformed to be largely phonemic. Treat any phonetic value beyond the attested orthography as [reconstructed]."),
    P("Can you translate a Linear A inscription?",
      "No. Linear A (Minoan Crete, c. 1800-1450 BCE, ~56 signs) is UNDECIPHERED. [unknown] Per DAVID's honesty rail, its interpretation is null -- no meaning may be asserted. We can describe sign shapes and note that some phonetic values are provisionally borrowed from the later, deciphered Linear B, but those values are tentative and yield no translation. The honest gap is the deliverable."),
    P("How does Linear A differ from Linear B in decipherment status?",
      "Linear B was deciphered by Michael Ventris in 1952 and records Mycenaean Greek (syllabic, ~87 signs, administrative tablets). Linear A is older, undeciphered, and records the unknown Minoan language. Sign shapes overlap, but a shared shape does not license a shared meaning. [Linear B attested/deciphered; Linear A unknown]"),
    P("What may DAVID say about an undeciphered script like Linear A?",
      "DAVID may: describe the script type (syllabic), sign count, find-spots, date, and material; compare sign forms to Linear B; and state clearly that the language and meanings are unknown. DAVID may NOT: translate it, assign meanings to signs, or invent vocabulary. Asserting meaning for an undeciphered source violates the honesty rail. [unknown]"),
    P("What is the difference between an attested text and a reconstructed pronunciation?",
      "An attested text is the actual written record (inscription, manuscript, scholarly transliteration) -- it has documentary support. A reconstructed pronunciation is how scholars infer it sounded, from comparative evidence, grammarians, meter, and transcriptions. DAVID labels these separately, e.g. 'ATTESTED text - RECONSTRUCTED pronunciation', and never upgrades a reconstruction to a certainty."),
    P("A user asks for the Sumerian word for 'helicopter'. How should DAVID respond?",
      "DAVID must decline to invent one. Sumerian has no attested word for a modern machine; fabricating one would violate the corpus-first rule ('never invent forms not attested or comparably reconstructed'). The correct response states the concept is unattested and, if useful, describes how Sumerian formed compounds, marking any illustration as [hypothesis]."),
    P("Summarize DAVID's coverage tiers for dead and undeciphered languages.",
      "DAVID assigns revival tiers: 'active' (living/liturgical use, e.g. Latin/Sanskrit recitation), 'high' (extinct but strong corpus, e.g. Gothic), 'medium' (partial corpus, heavy reconstruction), and 'research' (undeciphered or purely reconstructed, e.g. Linear A). The tier sets how much can be said and how heavily it must be hedged."),
]

# ===========================================================================
# T2 -- EXTINCT LANGUAGES
# ===========================================================================
T2 = [
    P("What is unusual about the Gothic alphabet?",
      "Gothic (East Germanic, 4th c. CE) was written in an alphabet invented by Bishop Wulfila for his Bible translation, built mainly on Greek uncial letterforms with some Latin/runic additions. It maps 1:1 to phonemes -- there are no silent letters. 'th' is a true dental fricative X-SAMPA /T/, not an English stop. [attested]"),
    P("Translate and source this attested Gothic line (romanized).",
      "Translation: 'Our Father, thou in heaven, hallowed be thy name' [attested] -- the Lord's Prayer from the Codex Argenteus (~520 CE). Gothic 'atta' (father) is cognate with English 'dad'. Long vowels and geminates are held (e.g. 'atta' has a long /t:/). [reconstructed pronunciation, Braune/Wright, high confidence]",
      "Atta unsar thu in himinam, weihnai namo thein"),
    P("Why is Gothic a goldmine for Germanic reconstruction?",
      "It is the sole substantial East Germanic corpus and the earliest substantial literary Germanic text (~350 CE). Comparing Gothic with Old Norse and Old English lets linguists triangulate Proto-Germanic. Its consistent, silent-letter-free orthography makes the phonology unusually recoverable. [attested]"),
    P("What does Hittite's letter 'h-dot' tell us about Indo-European?",
      "Hittite (Anatolian, oldest attested Indo-European, c. 1650 BCE) writes a guttural fricative (X-SAMPA /x/ or /X/, like the 'ch' in Scottish 'loch') where other branches show nothing. This is a direct reflex of a PIE laryngeal -- empirical proof of the laryngeal theory that Greek, Latin, and Sanskrit could not provide. [attested/reconstructed, Melchert]"),
    P("Translate and source this attested Hittite formula (romanized).",
      "Translation: 'let mankind remain inside' [attested] -- a ritual formula. Source: training_pack_hittite.md. Hittite cuneiform spells syllables (so 'ha' = h+a), not just word-signs. Pronunciation is [reconstructed] at medium confidence; the fortis/lenis contrast (held vs single stops) is favored over a simple voicing contrast.",
      "namma antuhsas andan esdu"),
    P("Why is Hittite significant in the history of Indo-European studies?",
      "It is the oldest attested Indo-European language (texts from ~1650 BCE, older than Greek or Sanskrit records) and its preserved laryngeal (h-dot) confirmed a theory that had been proposed on purely internal grounds. It reshaped the reconstruction of PIE. [attested]"),
    P("How is Old English 'hw' pronounced, and why does it matter?",
      "Old English 'hw' (as in 'hwaet') is a voiceless labial-velar X-SAMPA /W/ (or /hw/), distinct from plain /w/. [reconstructed, late West Saxon] This is the ancestor of the 'wh' spelling. The vowel 'ae' is X-SAMPA /{/ (the 'cat' vowel), not a diphthong."),
    P("Translate and source this attested Old English opening (romanized).",
      "Translation: 'Listen! We have heard of the glory of the Spear-Danes in days of old' [attested] -- Beowulf, line 1 (West Saxon manuscript tradition). 'Hwaet!' is a dramatic 'Listen!' or 'So!', not a literal 'what'. Old English alliterative meter has four stresses per line, and the stressed 'lifts' drive word choice. [attested text; reconstructed pronunciation]",
      "Hwaet! We Gardena in geardagum"),
    P("Which Old English dialect does DAVID use, and why?",
      "DAVID defaults to Late West Saxon (Mitchell & Robinson standard) because it is the dominant literary dialect with the fullest manuscript record; Northumbrian/Anglian variants differ in vowels and breaking. Confidence is high on stress and alliteration; short-diphthong realization is disputed [reconstructed]."),
    P("How are 'th' and 'dh' distributed in Old Norse?",
      "In Old Norse the thorn (th, X-SAMPA /T/) and eth (dh, X-SAMPA /D/) are positional allophones, not a phonemic contrast: voiceless initially and after voiceless sounds, voiced between voiced sounds. There are no silent letters. [reconstructed, West Norse/Icelandic literary standard, high confidence]"),
    P("Translate and source this attested Old Norse opening (romanized).",
      "Translation: 'Hearing I ask from all... holy kindreds' [attested] -- Voluspa, stanza 1, Poetic Edda (Codex Regius). Front rounded vowels (o-slash, o-ogonek) are distinct from English o, and long vowels are held. [reconstructed, Gordon/Crawford]",
      "Hljoths bith ek allar, helgar kindir"),
    P("What does the West vs East Norse split explain?",
      "West Norse (Icelandic literary) preserves diphthongs and umlauts longer; East Norse (Sweden/Denmark) shows early monophthongization from the 10th century. This split explains much of the later divergence among the modern Scandinavian languages. Runic (Younger Futhark) spelling is more conservative than manuscript Latin spelling. [reconstructed]"),
    P("Why are all vowels in Middle Egyptian reconstructions uncertain?",
      "Egyptian hieroglyphs write consonants only; every vowel in a transcription is a scholarly insertion. [reconstructed, required tag] The consonantal skeleton is firm, but vowel timbre is medium-low confidence, drawing on Coptic (the latest Egyptian, which does write vowels) and on Greek/Assyrian transcriptions of Egyptian names (Loprieno/Allen/Peust)."),
    P("Translate and source this attested Middle Egyptian formula (romanized).",
      "Translation: 'Life, prosperity, health' [attested] -- a ubiquitous royal blessing formula on New Kingdom stelae. Only the consonants (here, roughly 'ankh wedja seneb') are attested; the vowels are [reconstructed]. Egyptian also has ejective and pharyngeal consonants (ayin = a pharyngeal, X-SAMPA /?\\/), not silent letters.",
      "ankh wedja seneb"),
    P("How does Coptic help reconstruct earlier Egyptian?",
      "Coptic is the final stage of the Egyptian language and the first to write vowels (in Greek-derived letters). It acts as a phonological 'time machine': scholars project Coptic vocalic patterns back over the older consonantal skeleton, combined with Afro-Asiatic comparison and Greek transcriptions of names. All such vowels remain [reconstructed]."),
    P("What is Middle Egyptian's place in the language's history?",
      "Middle Egyptian (c. 2000-1300 BCE) is the 'classical' phase of the language, the prestige literary register used long after it stopped being everyday speech. It was written in hieroglyphs, hieratic, and demotic. [attested, fully read script]"),
    P("What is Anglo-Norman and where was it used?",
      "[No DAVID corpus file -- established general facts, flagged.] Anglo-Norman is the variety of Norman French used in England after the Conquest of 1066, especially in administration, law, and the court. It contributed a large layer of vocabulary to English and left a lasting 'Law French' legacy in legal terminology. Restrict claims to documented usage; mark any reconstructed pronunciation."),
    P("How did Anglo-Norman influence English?",
      "[No DAVID file -- general facts, flagged.] Centuries of Anglo-Norman administrative and legal use layered thousands of French-derived words into English (often alongside native synonyms, e.g. a Germanic everyday word beside a Romance formal one) and shaped legal terminology that survives today. Specific etymologies should be sourced, not invented."),
    P("What is Tudor English and how does it relate to Modern English?",
      "[No DAVID file -- established general facts, flagged.] Tudor English is the Early Modern English of the 16th-17th centuries (Shakespeare, the King James Bible). It sits mid-way through the Great Vowel Shift, still distinguishes 'thou' (informal/singular) from 'you', and was being standardized by printing. It is readable to modern eyes but differs in pronunciation and some grammar."),
    P("What was happening to English pronunciation during the Tudor period?",
      "[No DAVID file -- general facts, flagged.] The Great Vowel Shift -- a chain of changes in the long vowels -- was in progress, so Tudor long vowels often had values between Middle English and Modern English. 'Original Pronunciation' reconstructions of Shakespeare draw on spelling, rhyme, and contemporary descriptions, and are [reconstructed], not certain."),
    P("Why is Etruscan called a 'readable script, unknown language'?",
      "Etruscan (c. 700 BCE-50 CE) was written in an alphabet adapted from Greek, so the signs can be sounded out, but the language is a Tyrsenian isolate whose grammar and vocabulary are largely opaque. [readable script; meanings mostly unknown] It notably lacks voiced stops (b, d, g absent or neutralized) and has only four vowels."),
    P("Translate what can be read of this Etruscan formula and flag the limits.",
      "This is a dedicatory formula, roughly 'I [am/gave gift] of Laris' [partially attested -- proper name 'Laris' secure; the verb sense is debated]. Source: training_pack_etruscan.md. Because Etruscan is an isolate with a sparse corpus, only formulaic phrases and proper names are reliably understood; do not over-translate.",
      "mi mulu larisal"),
    P("How do bilingual inscriptions help with Etruscan?",
      "Bilinguals such as the Pyrgi Tablets (Etruscan with a Phoenician parallel) are crucial: they anchor proper names and a handful of meanings, which is most of what can be securely extracted from an isolate with a small corpus. [attested via bilingual] Even so, full grammar remains uncertain."),
    P("What can DAVID reliably say about Etruscan phonology?",
      "High confidence: the consonant inventory, the dominant aspirate-vs-plain contrast (ph/th/kh with an audible puff), and the absence of voiced stops. Lower confidence: vowel length and quality, the exact value of the letter transliterated s-acute ([s] vs X-SAMPA /S/), and the extent of syllabic sonorants. [reconstructed, Bonfante/Rix/Wallace]"),
    P("Compare how Gothic and Old Norse preserve Proto-Germanic.",
      "Gothic (East Germanic, ~350 CE) is earlier and freezes a very archaic stage but is known from essentially one translator's corpus. Old Norse (North Germanic) is later but richly attested and conservative, preserving Proto-Germanic features (e.g. initial 'hl-') longer than Old English. Together they triangulate Proto-Germanic. [attested/reconstructed]"),
    P("Why does Old English sound 'alien' despite being English's ancestor?",
      "Old English keeps Germanic features later lost: the 'ae' and front-rounded vowels, fully pronounced consonant clusters (hl-, hr-, hw-, cn-), grammatical gender and case endings, and alliterative meter. The Great Vowel Shift and Norman influence then transformed the sound and vocabulary, making the ancestor hard to recognize. [attested/reconstructed]"),
    P("How does Hittite cuneiform encode sounds?",
      "Hittite borrowed Mesopotamian cuneiform and used it largely syllabically: a sign like 'ha' writes the consonant plus vowel together, and 'plene' (doubled) vowel spellings signal length. Logograms (Sumerograms/Akkadograms) are also mixed in. This syllabic spelling is what lets scholars recover much of the phonology. [attested]"),
    P("What is the safest way to present extinct-language audio to users?",
      "Label the text and the sound separately: state the text is [attested] (with its manuscript/inscription source) and that the pronunciation is [reconstructed] (with the scholarly standard and confidence). For languages like Etruscan or Middle Egyptian, foreground the uncertainty rather than presenting a confident single rendering."),
    P("What does the Gothic Codex Argenteus preserve, and why is it valuable?",
      "The Codex Argenteus (~520 CE) is the principal manuscript of Wulfila's Gothic Bible, written in silver and gold ink on purple vellum. It preserves most of the surviving Gothic corpus, and because Gothic orthography maps 1:1 to phonemes, it gives an unusually clean window onto early Germanic sound structure. [attested]"),
    P("How does comparing runic and manuscript Old Norse reveal sound change?",
      "Runic inscriptions (Younger Futhark, 16 letters, no length marking) are more conservative, while later Latin-alphabet manuscripts show developments such as nasal-vowel loss and umlaut. Comparing the two spellings of the same words exposes the direction and timing of sound change. [attested/reconstructed]"),
]

# ===========================================================================
# T3 -- LIVING LANGUAGES AND DIALECTS
# ===========================================================================
T3 = [
    P("Contrast Latin American and Castilian Spanish for a learner.",
      "Latin American Spanish uses 'ustedes' as the only plural 'you' and words like 'computadora', 'carro', 'celular'; Castilian (Spain) uses 'vosotros' for informal plural and 'ordenador', 'coche', 'movil'. Parts of Spain also have 'ceceo' (a theta-like sound for c/z). For broad reach, a neutral Latin American register is the common default. [source: translation_profile.json]"),
    P("How should I pronounce the Spanish 'rr', and what rhythm does Spanish use?",
      "The double 'rr' (as in 'perro') is a trilled alveolar (X-SAMPA /r/), distinct from the single tapped 'r' (X-SAMPA /4/). Spanish has clear, unreduced vowels and is syllable-timed (each syllable takes roughly equal time), unlike stress-timed English. [source: spanish tutoring]"),
    P("What is 'voseo' in Spanish?",
      "'Voseo' is the use of 'vos' instead of 'tu' for the informal singular 'you', common in parts of Latin America (notably the River Plate region). It carries its own verb forms. DAVID notes it as a regional register feature; the specific verb morphology should be sourced for the target country. [source: translation_profile.json]"),
    P("Spanish has false friends. Give two and the translationese risk.",
      "'Actualmente' means 'currently', not 'actually'; 'realizar' means 'to carry out/perform', not only 'to realize'. The main translationese risks are literal calques (e.g. word-for-word 'en el caso de'), overuse of passive/reflexive, and ser/estar mismatches. Prefer natural, functional equivalence. [source: translation_profile.json]"),
    P("Contrast Brazilian and European Portuguese.",
      "Brazilian Portuguese has softer, more open and nasal vowels and a warmer, more informal default tone; European Portuguese has more reduced, 'closed' vowels and a more formal register, with different tu/voce usage. A common rule of thumb: Brazilian for business/marketing, European for legal. Both mark nasality with the tilde (a-tilde, o-tilde). [source: translation_profile.json]"),
    P("What is the main pitfall when translating a Portuguese document?",
      "Mixing variants within one document (Brazilian and European spelling, vocabulary, or pronoun placement). Enclitic vs proclitic pronoun position differs, and some spellings differ even after the orthographic Accord. Pick one variant and keep it consistent. [source: translation_profile.json]"),
    P("Give the key Brazilian vs European Portuguese pronunciation contrast.",
      "Brazilian tends to open, strongly nasalized vowels; European tends to reduced, more 'guttural'/closed vowels (unstressed vowels can nearly drop). Both share nasal diphthongs written with the tilde. Specify the target variant before producing pronunciation guidance. [source: portuguese tutoring]"),
    P("Contrast European and Quebec French for a translator.",
      "European French uses 'vous' strictly and tolerates more anglicisms in casual use; Quebec (Canadian) French uses 'tu' more readily even in some business contexts, enforces stricter anti-anglicism norms (cf. Bill 96), and has its own vocabulary. Default to European for formal written work unless the audience is specified. [source: translation_profile.json]"),
    P("What pronunciation features should a French learner master first?",
      "Nasal vowels (e.g. the contrast in 'bon'/'on'), liaison (linking a normally silent final consonant to a following vowel, as in 'un enfant'), the uvular 'r' (X-SAMPA /R/), frequent silent letters, and grouped/syllable-cohesive rhythm. [source: french tutoring]"),
    P("Explain the French register levels and a common false friend.",
      "French distinguishes 'tu' (informal) from 'vous' (formal), and registers: soutenu (elevated), courant (standard), familier (colloquial). A classic false friend: 'eventuellement' means 'possibly', not 'eventually'; 'actuellement' means 'currently'. [source: translation_profile.json]"),
    P("Why is liaison important when reading French aloud?",
      "Liaison links an otherwise silent final consonant to a following vowel-initial word, changing the perceived word boundaries (e.g. 'les amis' links the s). Getting liaison wrong makes speech sound unnatural and can blur meaning. It is partly obligatory and partly optional by register. [source: french tutoring]"),
    P("Explain Arabic diglossia and why it matters for translation.",
      "Arabic has a wide gap between Modern Standard Arabic (MSA) -- used for formal/written material -- and the regional spoken dialects (e.g. Egyptian, Gulf, Levantine). MSA is mandatory for formal documents; dialect is needed for natural spoken/marketing content. The main trap is dialect 'bleeding' into formal MSA or producing stiff, unnatural MSA. [source: translation_profile.json]"),
    P("Which Arabic sounds do learners most need to master?",
      "The pharyngeals 'ayn (X-SAMPA /?\\/) and ghayn, the emphatic (pharyngealized) consonants, and the back gutturals. Arabic is written right-to-left in an abjad that does not mark short vowels in MSA, which adds ambiguity that context must resolve. [source: arabic tutoring]"),
    P("How is written Arabic structured on the page?",
      "Right-to-left, in a consonant-primary abjad: short vowels are normally unwritten in MSA and inferred from context and grammar, while long vowels and consonants are written. This is why vocalization and diacritics are a recurring source of error in translation. [source: translation_profile.json]"),
    P("What is the difference between Simplified and Traditional Chinese characters?",
      "Simplified characters (fewer strokes) are standard in mainland China and most everyday documents; Traditional characters are used in Taiwan and Hong Kong and for literary/cultural material. They are writing-system variants, not different spoken languages. Mixing them in one document is an error. [source: translation_profile.json]"),
    P("Summarize Mandarin's tone and sound system for a beginner.",
      "Mandarin has four lexical tones plus a neutral tone, so pitch contour distinguishes word meaning. It has retroflex initials (the sh-, zh-, r- series) and no consonant clusters. Pinyin is a romanization used for teaching, not a final written output. [source: mandarin tutoring]"),
    P("Does DAVID cover regional spoken Mandarin variants?",
      "DAVID's living-Mandarin material documents script variants (Simplified vs Traditional) and the tone system, but the source files do not detail regional spoken varieties (e.g. Beijing vs Taiwan Mandarin). For those, DAVID falls back to established general descriptions and flags the gap rather than inventing specifics. [gap flagged]"),
    P("What is keigo, and why is it critical in Japanese?",
      "Keigo is Japanese honorific speech, a mandatory system for encoding social hierarchy. It has three branches: sonkeigo (respect toward the listener/referent), kenjougo (humble self-reference), and teineigo (general politeness). Inconsistent keigo levels read as social offense, especially in business and legal contexts. [source: translation_profile.json]"),
    P("Describe Japanese pronunciation basics for a learner.",
      "Japanese is mora-timed (each mora takes roughly equal time, not each syllable), uses a pitch accent rather than stress, and has a single flap (X-SAMPA /4/) where English distinguishes l and r. It is written with hiragana, katakana, and kanji. [source: japanese tutoring]"),
    P("How do du/Sie work in German, and what is final devoicing?",
      "German distinguishes 'du' (informal) from 'Sie' (formal); business default is 'Sie'. Final devoicing means voiced obstruents at the end of a syllable are pronounced voiceless (e.g. final -d is realized like -t). Umlauts (a-umlaut, o-umlaut, u-umlaut) shift vowel quality, and all nouns are capitalized. [source: translation_profile.json]"),
    P("Does DAVID document Bavarian vs Saxon German specifics?",
      "DAVID's living-German file covers register (du/Sie), orthography (umlauts, eszett, noun capitalization), and pronunciation hooks (final devoicing), but it does not document regional dialects such as Bavarian or Saxon. Those distinctions exist linguistically (differing vowels, lexis, and intonation) but here must be drawn from general references and flagged, not invented. [gap flagged]"),
    P("What German orthographic features trip up translators?",
      "Loss of umlauts and the eszett (ss) when forced into ASCII, splitting or mis-joining compound nouns, and verb-final word order in subordinate clauses. German also capitalizes all nouns, which is unique among major European languages. [source: translation_profile.json]"),
    P("Give the key Italian pronunciation features.",
      "Geminate (double) consonants are phonemically distinct (e.g. the 'tt' in a word is held longer than a single 't'), 'r' is a trill (X-SAMPA /r/), and stressed 'e' and 'o' have an open/closed quality distinction. [source: italian tutoring]"),
    P("How do register and false friends work in Italian?",
      "Italian distinguishes 'tu' (informal) from 'Lei' (formal/polite). Common risks are false friends with English and Spanish and calqued English syntax. Legal Italian is formal and may require sworn/full-text conventions. [source: translation_profile.json]"),
    P("Which of the world's 10 most-spoken languages lack DAVID source files?",
      "DAVID's living-language files cover Mandarin, Spanish, Arabic, Portuguese, French, and Japanese (and also German and Italian). Among the top-10 globally, English, Hindi, Bengali, and Russian have no dedicated DAVID files, so DAVID answers those from established general linguistics and flags the gap. [coverage note]"),
    P("Describe Hindi's basic typology for a learner.",
      "[Top-10 language with no DAVID file -- general facts, flagged.] Hindi is Indo-Aryan, written in the Devanagari abugida (consonants carry an inherent vowel modified by diacritics). It has a retroflex consonant series and a plain-vs-aspirated contrast, and SOV word order with postpositions. Specific vocabulary and dialect claims should be sourced."),
    P("Describe Russian's basic sound and grammar features.",
      "[Top-10 language with no DAVID file -- general facts, flagged.] Russian is East Slavic, written in Cyrillic, with phonemic palatalization ('soft' vs 'hard' consonants), vowel reduction in unstressed syllables, and a verbal aspect system (perfective vs imperfective). It is a case language with relatively free word order. Source any specific forms."),
    P("Why does register accuracy matter so much in document translation?",
      "Register errors signal disrespect or incompetence: wrong Japanese keigo, Arabic dialect in a formal MSA contract, or over-casual 'tu/du' in business all undermine the document. DAVID treats register accuracy as non-negotiable and adapts it to the target language and document type. [source: david_linguist_system.md]"),
    P("What is the difference between formal and natural translation, per DAVID?",
      "DAVID favors functional/dynamic equivalence (Nida/Baker): conveying the natural meaning and register of the target language rather than a literal word-for-word calque. Literal translation produces 'translationese' -- grammatical but unnatural output. The exception is legal text, where precision and prescribed conventions dominate. [source: translation_profile.json]"),
    P("Is English in scope for DAVID, and how is it handled?",
      "[Top-10 language with no dedicated DAVID file -- general facts, flagged.] English is a West Germanic language and a global lingua franca, but DAVID has no dedicated living-English profile, so English-specific claims come from established references and are flagged. DAVID can still contrast English with the languages it documents (e.g. stress-timed English vs syllable-timed Spanish)."),
]

# ===========================================================================
# T4 -- PHONETICS / IPA AND MODALITIES
# ===========================================================================
T4 = [
    P("Name the main places of articulation from lips to glottis.",
      "Labial (bilabial; labiodental), coronal (dental, alveolar, post-alveolar, retroflex), dorsal (palatal, velar, uvular), radical (pharyngeal, epiglottal), and glottal. Place describes WHERE in the vocal tract the constriction is made. [source: articulatory-phonetics/profile.json]"),
    P("Name the main manners of articulation.",
      "Stops/plosives (full closure then release), fricatives (turbulent partial closure; sibilants aim turbulence at the teeth), nasals (oral closure with the velum lowered for nasal airflow), approximants (close but no turbulence), laterals (airflow around the sides of the tongue), trills/taps (vibration), and clicks (velaric airstream). [source: articulatory-phonetics/profile.json]"),
    P("Transcribe this English word and give an ASCII (X-SAMPA) breakdown.",
      "General American: X-SAMPA /T O t/. Breakdown: /T/ = voiceless dental fricative (the 'th' in 'thin'), /O/ = open-mid back rounded vowel, /t/ = voiceless alveolar stop. (ASCII X-SAMPA used in place of IPA glyphs.)",
      "thought"),
    P("Give the X-SAMPA for the English 'sh' and 'ng' sounds and describe them.",
      "'sh' = X-SAMPA /S/, a voiceless post-alveolar (palato-alveolar) fricative. 'ng' = X-SAMPA /N/, a velar nasal (as at the end of 'sing'). Both are described by place + manner + voicing. [source: articulatory-phonetics/profile.json]"),
    P("How do voiced and voiceless sounds differ articulatorily?",
      "Voiced sounds are made with the vocal folds vibrating; voiceless sounds are not. Modal vocal-fold vibration runs roughly from a 70-80 Hz floor (bass) up past 1000 Hz (soprano). The same place and manner (e.g. /s/ vs /z/) can contrast purely by voicing. [source: articulatory-phonetics/profile.json]"),
    P("Describe the vowel space using height and backness.",
      "Vowels are classified by tongue height (close/high to open/low), backness (front to back), and lip rounding. For example, a close front unrounded vowel is X-SAMPA /i/ (as in 'see'); a close back rounded vowel is /u/ (as in 'boot'). Rounding plus front position gives /y/ (French 'u'). [general articulatory phonetics]"),
    P("What is the difference between intonation and tone?",
      "Intonation is pitch variation over a phrase to signal attitude, focus, or sentence type (question vs statement); it does not change which word is meant. Tone uses pitch to distinguish word meaning (as in Mandarin). [source: intonation/profile.json]"),
    P("Describe the typical American English intonation for statements and yes/no questions.",
      "Declaratives and wh-questions typically fall at the end (a 2-3-1 pitch pattern). Yes/no questions typically rise at the end (a 2-3 pattern). Very high pitch marks strong emotion or emphasis. [source: intonation/profile.json]"),
    P("What is prosody, and which cues mark English stress?",
      "Prosody is the suprasegmental layer: pitch, duration, loudness, and voice quality. English stress is cued mainly by pitch prominence, then by longer duration, then loudness, plus vowel-quality differences (stressed vowels are more peripheral, unstressed more centralized). Example: CONvert (noun) vs conVERT (verb). [source: prosody/profile.json]"),
    P("Give an example where English stress changes a word's grammatical category.",
      "Many noun/verb pairs shift stress: 'CONvert', 'PERmit', 'REcord' as nouns (stress on the first syllable) vs 'conVERT', 'perMIT', 'reCORD' as verbs (stress on the second). Pitch prominence is the most reliable cue. [source: prosody/profile.json]"),
    P("Outline the three stages of speech production.",
      "1) Conceptualization (forming the intention and selecting the message), 2) Formulation (grammatical, then morpho-phonological, then phonetic encoding into articulatory plans), and 3) Articulation (the lungs, larynx, tongue, lips, and jaw execute it). Fluent speech runs near 120-150 words per minute, about 15 sounds per second. [source: speech-production/profile.json]"),
    P("What is paralanguage?",
      "Paralanguage is meta-communication carried by HOW something is said -- loudness, rate, pitch, pitch contour, voice quality -- and by non-lexical vocalizations (gasps, sighs, 'mhm', 'huh?'). It modifies or adds emotional and attitudinal meaning to the words. In text it appears as capitalization, emoticons, and punctuation. [source: paralinguistics/profile.json]"),
    P("What are the five parameters that distinguish meaning in ASL?",
      "Handshape, movement, palm orientation, location, and nonmanual markers (e.g. eyebrow, head, and mouth movements). Changing any one parameter can change the sign's meaning -- they are analogous to phonemes in spoken language (Stokoe). [source: american-sign-language/profile.json]"),
    P("How does ASL grammar mark questions and verbs?",
      "ASL uses nonmanual markers for question type (raised eyebrows + head tilt for yes/no; lowered eyebrows for wh-questions), basic SVO or topicalized order, verb agreement via movement between locations, and aspect via the manner of movement (e.g. rhythmic circular movement = continuous). [source: american-sign-language/profile.json]"),
    P("Is British Sign Language the same as ASL?",
      "No. BSL and ASL are mutually unintelligible: only about 31% of signs are identical, well below the threshold for being dialects of one language. BSL's canonical order is OSV (object-subject-verb) with topic-comment structure, and it has its own regional dialects (e.g. different number systems in Scotland and Manchester). [source: british-sign-language/profile.json]"),
    P("Where does French Sign Language (LSF) fit historically?",
      "LSF is the historical ancestor of ASL (ASL shares roughly 58% lexical cognates with LSF) and is related to several other sign languages. Importantly, LSF was a pre-existing natural language that Abbe de l'Epee documented, not one he invented; his artificial 'methodical signs' overlay was later set aside. [source: french-sign-language/profile.json]"),
    P("What makes Japanese Sign Language (JSL) distinctive?",
      "JSL developed independently (not from LSF). It combines manual signs with mouthing, essential facial expressions, fingerspelling ('yubimoji', borrowed from the US and used less than in ASL), and 'kusho' (tracing kanji in the air for names/places). It coexists with Signed Japanese (which follows Japanese grammar) and a pidgin middle form. [source: japanese-sign-language/profile.json]"),
    P("How is German Sign Language (DGS) structured phonologically and syntactically?",
      "DGS uses about 32 handshapes (6 basic ones shared across sign languages), two-handed signs governed by symmetry and dominance rules, and a Hold-Movement syllable structure (maximal HMH). Its unmarked word order is SOV, unlike spoken German's SVO. [source: german-sign-language/profile.json]"),
    P("What is Kendon's continuum of gesture?",
      "It ranks gesture by how language-like it is: spontaneous gesticulation (needs speech) -> language-like gestures -> pantomime -> emblems (fixed meaning, speech-independent, e.g. a thumbs-up) -> sign language (full linguistic system). Gesture and speech share neural processing (Broca's and Wernicke's areas). [source: gesture/profile.json]"),
    P("Distinguish informative from communicative gestures.",
      "Informative (passive) gestures leak information without intent (scratching, adjusting clothing). Communicative (active) gestures are produced on purpose to modify or intensify speech, and include symbolic/emblematic, deictic (pointing), motor/beat (rhythmic emphasis), and lexical/iconic (depicting) types. [source: gesture/profile.json]"),
    P("Are facial expressions of emotion universal?",
      "Darwin and Ekman argued a core set is universal (happiness, sadness, anger, fear, surprise, disgust), produced even by infants and congenitally blind people via a subcortical pathway. But social emotions like shame, pride, and deference vary cross-culturally, and the strong universality claim is contested. [source: facial-expression/profile.json]"),
    P("How do voluntary and involuntary facial expressions differ neurologically?",
      "Voluntary expressions run through a cortical (pyramidal) route and are consciously controlled and socially conditioned; involuntary emotional expressions run through a subcortical (extrapyramidal) route and appear unconsciously. Negative emotion tends to show more strongly on the left side of the face. [source: facial-expression/profile.json]"),
    P("What are the three levels of a speech act?",
      "Locutionary (producing a meaningful utterance), illocutionary (the act performed IN saying it -- asserting, questioning, ordering, promising), and perlocutionary (the effect on the hearer -- persuading, alarming). Searle's illocutionary types are assertives, directives, commissives, expressives, and declarations. [source: speech-acts/profile.json]"),
    P("What are felicity conditions, and what is an indirect speech act?",
      "Felicity conditions (Austin) are the circumstances a speech act needs to succeed; if they fail, the act 'misfires' or is an 'abuse' (e.g. an insincere promise). An indirect speech act uses one sentence form to perform another function, e.g. 'Can you close the window?' is a request, not a real question about ability. [source: speech-acts/profile.json]"),
    P("How do you describe lip and tongue position for the vowel in 'see'?",
      "The vowel in 'see' is X-SAMPA /i/: the tongue is high and front, the lips are spread/unrounded, and the jaw is fairly closed. Contrast 'boot' /u/, which is high and back with rounded lips. Describing rounding, height, and backness is enough to coach the articulation. [general articulatory phonetics]"),
    P("What is the 'frequency code' in paralinguistics?",
      "The frequency code links high vocal pitch with smallness, harmlessness, and submission, and low pitch with largeness, dominance, and assertiveness. It helps explain cross-cultural tendencies in how pitch conveys attitude. [source: paralinguistics/profile.json]"),
    P("Why are nonmanual markers part of sign-language phonology, not just emotion?",
      "In sign languages, facial actions (eyebrow raises, mouth shapes, head tilts) are grammatical: in ASL a raised brow marks a yes/no question and a lowered brow a wh-question. Removing them can make a sentence ungrammatical, so they function like phonological/grammatical features, not mere affect. [source: facial-expression/profile.json]"),
    P("What is the difference between a trill and a tap?",
      "A trill (e.g. Spanish 'rr', X-SAMPA /r/) is several rapid vibrations of the articulator (an apical trill is typically 2-3 contacts); a tap or flap (Spanish single 'r', X-SAMPA /4/) is a single quick contact. The contrast is meaningful in Spanish ('perro' vs 'pero'). [source: articulatory-phonetics/profile.json]"),
    P("What is code-switching?",
      "Code-switching is alternating between two languages or varieties within a conversation or even a single utterance, governed by social and grammatical constraints rather than being random. It is a normal feature of bilingual competence, not a deficiency. [source: code-switching/profile.json]"),
    P("What are deixis and discourse markers in pragmatics?",
      "Deixis is context-dependent reference -- words like 'here', 'now', 'this', 'you' whose meaning shifts with speaker, time, and place. Discourse markers (e.g. 'well', 'so', 'anyway') organize talk -- signaling topic shifts, turns, and stance -- rather than adding propositional content. [source: deixis/profile.json, discourse-markers/profile.json]"),
]

# ===========================================================================
# T5 -- WRITING SYSTEMS
# ===========================================================================
T5 = [
    P("Name the main types of writing system.",
      "Logographic (signs = words/morphemes), syllabic (signs = syllables), alphabetic (signs = phonemes), abjad (consonant-primary, vowels optional), abugida (consonant base with vowel diacritics), and featural (shapes encode phonetic features). [source: writing-system/profile.json]"),
    P("Classify these scripts by type: Latin, Devanagari, Arabic, Hangul, Linear B.",
      "Latin = alphabetic; Devanagari = abugida; Arabic = abjad; Hangul = featural alphabet; Linear B = syllabic. Naming the type is the first step in identifying an unknown script. [source: writing-systems profiles]"),
    P("Describe cuneiform and how to recognize it.",
      "Cuneiform is logosyllabic (logograms plus syllabic signs), impressed into wet clay with a reed stylus, producing wedge-shaped marks (Latin 'cuneus' = wedge). Early Uruk signs run in vertical columns right-to-left; from the Early Dynastic period they rotate to left-to-right rows. Recognize it by the wedge impressions on clay. [source: ws_cuneiform_sumerian_akkadian.json]"),
    P("How and when was Linear B deciphered, and what does it record?",
      "Linear B was deciphered by Michael Ventris in 1952, who showed it records an early (Mycenaean) form of Greek. It is syllabic (~87 syllabic signs plus ~100 logograms), written left-to-right on clay tablets, and its surviving texts are administrative records -- inventories and rations, no literature. [source: ws_linear_a_linear_b.json]"),
    P("Why can't Linear A be read even though it resembles Linear B?",
      "Linear A (Minoan, ~56 signs, c. 1800-1450 BCE) is undeciphered: its underlying language is unknown and no bilingual anchors it. Borrowing Linear B's sound values is only provisional and yields no meaning. Per the honesty rail, its interpretation is null -- no reading may be asserted. [source: ws_linear_a_linear_b.json]"),
    P("Where does the Latin alphabet come from, and how is it recognized in inscriptions?",
      "The Latin alphabet descends from the Etruscan adaptation of a West Greek alphabet. Classical monumental capitals have 23 letters (no J, U, or W), squared serifed geometric forms on a consistent baseline. Recognize Roman epigraphy by these proportioned, serifed capitals. [source: ws_latin_alphabet.json]"),
    P("What is boustrophedon, and which script used it?",
      "Boustrophedon ('as the ox plows') is writing that alternates direction line by line -- left-to-right, then right-to-left -- with letters mirrored on the reversed lines. Archaic Greek inscriptions used it before standardizing on left-to-right by the Classical period. The Greek alphabet itself derives from the Phoenician abjad. [source: ws_ancient_greek_alphabet.json]"),
    P("What role did the Phoenician alphabet play in writing history?",
      "Phoenician is an abjad (consonant-only alphabet) and is the ancestor of the Greek and Latin alphabets (and, via Greek, of Cyrillic and Coptic). The Greeks added vowel letters, turning the abjad into a full alphabet. [source: phoenician-alphabet/profile.json]"),
    P("What kind of script is Devanagari, and what are its hallmarks?",
      "Devanagari is a Brahmic abugida: each consonant carries an inherent vowel that is changed with diacritics, and consonant clusters form conjunct ligatures. A characteristic horizontal headline runs along the top of the letters. It writes Sanskrit, Hindi, and other languages. [source: devanagari/profile.json]"),
    P("Why is Hangul called a featural script?",
      "In Hangul the letter shapes themselves encode phonetic features (for example, related consonants share a base shape with added strokes for related sounds), and letters are grouped into syllable blocks. This deliberate, feature-based design is rare among the world's scripts. [source: hangul/profile.json]"),
    P("How did hiragana develop, and how does it differ from katakana?",
      "Hiragana is a Japanese syllabary derived from cursive (simplified) forms of kanji; it writes grammar and native words. Katakana, used for loanwords and emphasis, derives instead from fragments of clerical-style kanji and is more angular. [source: hiragana/profile.json]"),
    P("What is oracle bone script?",
      "Oracle bone script is the earliest attested Chinese writing, incised on ox scapulae and turtle plastrons for divination. It is the ancestral, archaic form of the (logographic) Chinese character system. [source: oracle-bone-script/profile.json]"),
    P("Describe the runic Elder Futhark and how to recognize runic inscriptions.",
      "The Elder Futhark is a 24-rune alphabet (named for its first six letters, F-U-Th-A-R-K). Runes are built from vertical staves with diagonal/horizontal branches and avoid horizontal strokes so they can be carved across wood grain. Recognize runic by the angular, stave-and-branch letters on stone, bone, metal, or wood. [source: ws_runic_elder_futhark.json]"),
    P("What is the Wulfila (Gothic) script and why is it distinctive?",
      "It is the alphabet Bishop Wulfila created (~350 CE) to translate the Bible into Gothic, based on Greek uncial letterforms with Latin/runic additions, written left-to-right with 27 letters. The prestige Codex Argenteus uses silver and gold ink on purple vellum. It is distinct from later medieval 'blackletter' (also loosely called gothic). [source: ws_gothic_wulfila.json]"),
    P("What is proto-cuneiform and how deciphered is it?",
      "Proto-cuneiform (Uruk IV-III, c. 3400-3000 BCE) is the pictographic precursor of cuneiform, impressed on small clay tablets in rectangular cases, running in vertical columns right-to-left. It is only PARTIALLY deciphered: the numerical/metrological signs and commodity logograms are understood, but the underlying language is debated. [source: pw_cuneiform_uruk_proto.json]"),
    P("What are the Abydos proto-hieroglyphs?",
      "They are some of the earliest Egyptian writing: signs incised on small ivory/bone tomb tags (Naqada III / Dynasty 0, c. 3250-3000 BCE). The system is PARTIALLY deciphered -- some signs match later hieroglyphic values, many remain debated (Dreyer's readings are influential but not universal). Sign orientation and direction are not yet standardized. [source: pw_egyptian_proto_hieroglyphs.json]"),
    P("Why is the Indus Valley script considered undeciphered?",
      "The Indus (Harappan) script (~400 signs, c. 2600-1900 BCE) appears mostly on short seal inscriptions with no bilingual to anchor it, and there is no consensus on the underlying language -- the Dravidian, Munda, and non-linguistic-notation hypotheses all remain unresolved. Per the honesty rail, no reading of Indus signs may be presented as established. [source: pw_indus_valley_script.json]"),
    P("Is Upper Paleolithic cave art a writing system?",
      "Not a writing system in the linguistic sense. Cave art (Lascaux ~17,000 BCE, Altamira, Chauvet ~36,000 BCE) is the earliest certain symbolic visual communication, including recurring geometric signs (von Petzinger's catalogue), but the specific meanings are irrecoverable. We can say it is intentional symbolic communication; we cannot 'read' it. [source: aac_cave_art_lascaux_altamira.json]"),
    P("What communicative role does medieval manuscript marginalia play?",
      "Marginalia (drolleries, grotesques, satirical role-reversals) sit deliberately outside the authoritative main text and act as a counter-discourse: commenting on, parodying, or contextualizing it, and signaling workshop or patron identity. The images are visually well understood, but whether a given scene is merely decorative or programmatic is debated per manuscript. [source: aac_medieval_manuscript_marginalia.json]"),
    P("How would you identify an unknown script from a visual description?",
      "Work through: the inventory size (tens of signs suggests a syllabary; ~20-30 suggests an alphabet/abjad; hundreds-plus suggests logographic), the writing medium and stroke style (wedges on clay = cuneiform; staves/branches = runic), the directionality, and characteristic shapes. Then propose a script type and note confidence; do not assert a reading without a cited decipherment. [method, source: INTERPRETATION_GATE.md]"),
    P("Keep transcription, transliteration, and interpretation separate -- why?",
      "Per DAVID's interpretation gate, transcription (the signs as drawn), transliteration (their phonetic/sign values), and interpretation (the meaning) are distinct layers that must be recorded in separate fields. Collapsing them lets an uncertain reading masquerade as fact. [source: INTERPRETATION_GATE.md, R5]"),
    P("What must accompany any claimed reading of an inscription?",
      "A citation to a scholarly decipherment graded primary/secondary/tertiary, an explicit decipherment status (deciphered/partially/undeciphered), recorded confidence and any competing readings (dissent), and image provenance plus license. An uncited interpretation, or a meaning asserted for an undeciphered source, fails the gate. [source: INTERPRETATION_GATE.md]"),
    P("Why does directionality help identify a script?",
      "Directionality is a strong cue: Arabic and Hebrew run right-to-left; most modern European scripts run left-to-right; archaic Greek could be boustrophedon; early cuneiform ran in vertical columns before rotating. Combined with sign count and shape, direction narrows the candidates quickly. [method]"),
    P("Contrast an abjad with an abugida using examples.",
      "An abjad (e.g. Phoenician, Arabic) writes consonants and treats vowels as optional/diacritic. An abugida (e.g. Devanagari) gives each consonant an inherent vowel that is modified by obligatory diacritics. Both differ from a full alphabet (e.g. Latin, Greek), which gives vowels their own independent letters. [source: writing-systems profiles]"),
    P("What is the difference between Simplified-Chinese script and Mandarin dialects?",
      "Simplified vs Traditional is a difference in the WRITTEN characters (mainland vs Taiwan/Hong Kong), not in speech; spoken Mandarin variants are a separate, dialectal matter. Confusing 'script variant' with 'spoken dialect' is a common error. [source: mandarin translation_profile.json]"),
    P("Why is the Rosetta Stone important for decipherment method?",
      "It carries the same decree in three scripts (hieroglyphic, demotic, and Greek), and the readable Greek provided the key to recovering Egyptian hieroglyphs. It is the classic example of how a bilingual/triple-script anchor enables decipherment -- and why scripts like Linear A and Indus, lacking such anchors, remain unread. [source: rosetta_stone_poc_feeder_packet.json]"),
    P("What does it mean that cuneiform 'rotated 90 degrees' over time?",
      "Early (Uruk-period) signs were drawn upright in vertical columns read right-to-left; by the Early Dynastic period (c. 2900 BCE) the whole system was reoriented so signs lie on their backs and are read left-to-right in horizontal rows. The same signs thus look rotated between early and later texts. [source: ws_cuneiform_sumerian_akkadian.json]"),
    P("If an image source is paywalled or blocked, what should DAVID do?",
      "Park it: record harvest_status PARKED in the parked-sources log and fall back to an openly licensed substitute (e.g. a published line-drawing or a Wikimedia Commons image), keeping source_url and license on whatever asset is used. DAVID must never fabricate the asset or its provenance. [source: INTERPRETATION_GATE.md, R4]"),
    P("How did the Greek alphabet turn the Phoenician abjad into a full alphabet?",
      "The Greeks borrowed Phoenician consonant letters and repurposed several that wrote sounds Greek lacked to stand for vowels, creating the first full alphabet with independent vowel letters. This vowel notation is the key innovation later inherited by the Latin and Cyrillic alphabets. [source: ws_ancient_greek_alphabet.json]"),
    P("What gives cuneiform its characteristic wedge shapes?",
      "Cuneiform was impressed into wet clay with a reed stylus whose cut end made a triangular 'wedge' mark; scribes combined horizontal, vertical, and diagonal wedges into signs. The medium (clay) and tool (reed) produced the look, and early pictographic signs grew increasingly abstract and compressed over time. [source: ws_cuneiform_sumerian_akkadian.json]"),
]

# ===========================================================================
# T6 -- LANGUAGE RESEARCH METHODOLOGY
# ===========================================================================
T6 = [
    P("State DAVID's corpus-first principle.",
      "Corpus before grammar: never invent forms that are not attested or comparably reconstructed. Each text is treated like forensic evidence at a crime scene -- claims must trace to documentary support or an explicit comparative chain. [source: prompts/david_linguist_system.md]"),
    P("What are DAVID's four confidence tags?",
      "[attested] -- directly documented in texts/inscriptions/reading traditions; [reconstructed] -- inferred by sound scholarly method (comparative, internal, transcriptions); [hypothesis] -- a plausible but weakly supported guess; [unknown] -- not recoverable, never generated as content (routed to a research queue). Every output carries the appropriate tag. [source: david_linguist_system.md]"),
    P("When should DAVID use the [hypothesis] tag instead of [reconstructed]?",
      "Use [reconstructed] when a feature follows from established method with reasonable consensus (e.g. Classical Latin vowel length). Use [hypothesis] when the evidence is thin or scholars disagree sharply -- e.g. Sumerian pronunciation overall, or the exact value of Sumerian 'g-tilde'. The honest lower tag is preferred when in doubt. [source: training packs]"),
    P("Explain DAVID's revival tiers.",
      "active (living/liturgical use, strong confidence -- e.g. Latin, Sanskrit recitation), high (extinct but well-attested corpus -- e.g. Gothic, Old Norse), medium (partial corpus, heavy reconstruction -- e.g. some phases of Old English), and research (undeciphered or purely reconstructed -- e.g. Linear A). The tier governs how much can be claimed. [source: README.md]"),
    P("How does DAVID distinguish attested from reconstructed content on screen?",
      "It labels them separately, e.g. 'ATTESTED text - RECONSTRUCTED pronunciation', so viewers never mistake an inferred sound for documentary fact. A reconstruction is never quietly upgraded to a certainty, and the standard/confidence is stated. [source: reports/content_concepts_v1.md, T4_142 checklist]"),
    P("What must accompany every linguistic claim in DAVID?",
      "A source: either a citation (primary work, corpus ID, or URL) or an explicit comparative chain showing how the form was reconstructed. Corpus entries record transliteration, translation, source, date, and a confidence tag. Uncited interpretation is not allowed. [source: david_linguist_system.md]"),
    P("How is the comparative method used to reconstruct a proto-language?",
      "By aligning cognates across related languages and applying regular sound correspondences, scholars infer the ancestral form (marked with an asterisk, e.g. a starred Proto-Germanic root). The reconstruction is a hypothesis supported by systematic correspondences, so it is tagged [reconstructed], never [attested]. [method]"),
    P("How should DAVID handle an undeciphered language?",
      "Describe what is knowable (script type, sign count, date, material, find-spots) and state plainly that the language and meanings are unknown. Do not translate, assign meanings, or invent vocabulary. The honest gap is the deliverable, and the request is routed to research rather than answered with invented content. [source: INTERPRETATION_GATE.md]"),
    P("What is the difference between academic and popular framing in DAVID content?",
      "Academic framing states reconstructions as 'scholarly reconstruction, not performance convention', with confidence and sources. Popular/tutoring framing surfaces the memorable, counterintuitive hook (e.g. 'Latin V is /w/, not modern v') -- but it must not overstate certainty or drop the attested/reconstructed distinction. [source: david_linguist_system.md]"),
    P("How does DAVID serve a forensic-linguist user?",
      "With corpus-first depth: attested texts with transliteration/translation/source, morphology and typology sketches, comparative chains, and explicit confidence tags. The emphasis is documentary rigor and traceability rather than performance. [source: david_linguist_system.md, Pillar I]"),
    P("How does DAVID serve an audio-producer user?",
      "With phonetic precision for synthesis: IPA/X-SAMPA values, articulation guidance (place/manner, vowel quality, length, stress/pitch), and confidence on each sound. Reconstructed pronunciations are labeled as such so the audio is honestly framed. [source: david_linguist_system.md, Pillar II]"),
    P("How does DAVID serve an educator or independent learner?",
      "With pedagogy: memorable, counterintuitive hooks ('find the surprising, not the textbook-obvious'), clear contrasts (e.g. how the ancient sound differs from the modern), and leveled explanations -- while preserving the attested-vs-reconstructed honesty so learners are not misled. [source: david_linguist_system.md, Pillar III]"),
    P("How does DAVID serve a living-language document user?",
      "With register and idiom accuracy for real documents: correct formality (keigo, tu/vous, du/Sie), variant consistency (e.g. one Portuguese variant), document-type conventions (legal vs business vs academic), and natural functional equivalence over literal calque. [source: david_linguist_system.md, Pillar IV]"),
    P("What is DAVID's rule when scholars disagree about a reconstruction?",
      "Be conservative: when uncertain, use the most broadly accepted reconstruction and flag the dispute, rather than promoting a speculative minority reading. Record competing readings as dissent. [source: david_linguist_system.md]"),
    P("Why does DAVID label pronunciation confidence per language?",
      "Because certainty varies enormously: Sanskrit is near-certain (living recitation), Classical Latin and Greek are high (meter, grammarians), while Sumerian is low (isolate, reconstructed via Akkadian). Stating per-language confidence prevents treating a shaky reconstruction like a solid one. [source: research_ops raw files]"),
    P("What is internal reconstruction, as opposed to the comparative method?",
      "Internal reconstruction infers an earlier stage of a SINGLE language from irregularities and alternations within it (e.g. patterns that point to a lost sound), whereas the comparative method compares related languages. Both yield [reconstructed] forms requiring sourcing. [method]"),
    P("How do loanwords and transcriptions aid reconstruction?",
      "When one language transcribes another's words (e.g. Akkadian writing Sumerian, or Greek writing Egyptian names), the spellings reveal how the source language sounded at that time. Loanwords borrowed at a datable moment similarly fossilize an older pronunciation. These are key evidence for [reconstructed] sounds. [method, source: training packs]"),
    P("What should DAVID do with a user request it cannot source?",
      "If the content would be [unknown] or require inventing forms, DAVID declines to fabricate, states the limit honestly, and routes the question to the research queue rather than guessing. Producing unsourced 'facts' violates the corpus-first and citation rules. [source: david_linguist_system.md]"),
    P("How does DAVID document dialect variation within a dead language?",
      "By recording the relevant varieties and their features and choosing a default with a stated reason -- e.g. Tiberian (default) vs Babylonian vs Samaritan for Biblical Hebrew, or West Saxon (default) vs Northumbrian for Old English. Each variety's distinctive features are sourced and confidence-tagged. [source: research_ops raw files]"),
    P("Why does DAVID treat reconstructed audio as 'scholarly reconstruction, not performance convention'?",
      "To stop a documentary or lesson from implying the sound is a known recording. The phrasing makes explicit that the audio is the best scholarly inference, distinct from later traditions (e.g. Ecclesiastical Latin) or modern stage conventions. [source: david_linguist_system.md]"),
    P("What is the standard format for a DAVID corpus entry?",
      "Each entry pairs a transliteration with a translation and records its source, date, and a confidence tag, keeping the attested text separate from any reconstructed pronunciation. This makes every claim auditable. [source: david_linguist_system.md]"),
    P("How should DAVID phrase uncertainty so a learner still trusts it?",
      "State what IS known confidently, then mark the uncertain part explicitly with the tag and the reason (e.g. 'the consonants are secure [attested in script]; the vowels are a scholarly insertion [reconstructed]'). Honest, specific uncertainty builds trust; vague hedging or false confidence erodes it. [method]"),
    P("Why is 'never invent forms' the cornerstone rule?",
      "Because a single fabricated word or translation, once published, can propagate as a false 'attestation' and corrupt downstream research and teaching. The corpus-first rule protects the integrity of the whole language record, which is why undocumented vocabulary is never generated. [source: david_linguist_system.md]"),
    P("How does DAVID decide a reconstruction is solid enough to teach?",
      "It checks for converging evidence -- grammarians' descriptions, metrical/orthographic clues, transcriptions, comparative correspondences, and (rarely) a living tradition. Multiple independent lines raise confidence to [reconstructed]; a single weak line keeps it [hypothesis]. [method]"),
    P("What distinguishes DAVID's living-language work from its dead-language work methodologically?",
      "Living languages are validated against native usage and current norms (register, dialect, idiom), so the standard is naturalness and contemporary accuracy. Dead languages are validated against the documentary corpus and reconstruction method, so the standard is attestation and honest uncertainty. The confidence machinery applies to both. [source: david_linguist_system.md]"),
    P("How does DAVID keep popular content from overclaiming?",
      "By keeping the honesty labels even in hooks, never upgrading [reconstructed] to fact, and preferring the broadly accepted reconstruction. A catchy line like 'this is how Caesar really sounded' must still carry the reconstructed-pronunciation label. [source: T4_142 checklist]"),
    P("Why does DAVID separate 'transcription' from 'interpretation' in visual sources?",
      "So that the act of recording the marks as drawn (transcription) is never confused with claiming what they mean (interpretation). For undeciphered material the interpretation field is explicitly null, which keeps an honest gap visible instead of an invented meaning. [source: INTERPRETATION_GATE.md]"),
    P("Summarize DAVID's stance in one sentence.",
      "DAVID gives the most accurate, honestly-hedged account the evidence supports -- attested where the record speaks, reconstructed where method allows, and an explicit unknown where it does not -- and never invents language data to fill a gap. [source: david_linguist_system.md]"),
    P("What does DAVID mean by 'the honest gap is the deliverable'?",
      "For undeciphered or unrecoverable material, the correct output is a clear statement of what is unknown -- not a filled-in guess. Honestly marking the gap (interpretation null, [unknown]) is itself the valuable, trustworthy result, and protects users and the language record from invented content. [source: INTERPRETATION_GATE.md]"),
    P("How should DAVID handle conflicting dates or attributions for a text?",
      "Report the range and the competing scholarly positions rather than collapsing them into one false-precise date, cite each, and choose a default only with a stated reason. The disagreement is recorded as dissent, consistent with the confidence-and-dissent rule. [source: INTERPRETATION_GATE.md, methodology]"),
]

SHARDS = [
    ("david_corpus_T1_dead_languages.jsonl", T1),
    ("david_corpus_T2_extinct_languages.jsonl", T2),
    ("david_corpus_T3_living_languages_dialects.jsonl", T3),
    ("david_corpus_T4_phonetics_ipa.jsonl", T4),
    ("david_corpus_T5_writing_systems.jsonl", T5),
    ("david_corpus_T6_language_research_methodology.jsonl", T6),
]


def main(argv=None):
    check_only = "--check" in (argv or sys.argv[1:])
    total = 0
    errors = []
    for fname, pairs in SHARDS:
        if len(pairs) != 30:
            errors.append(f"{fname}: expected 30 pairs, got {len(pairs)}")
        lines = []
        for i, r in enumerate(pairs, 1):
            assert set(r) == {"instruction", "input", "output"}
            s = json.dumps(r, ensure_ascii=True)
            json.loads(s)
            if not s.isascii():
                errors.append(f"{fname}:{i} non-ASCII")
            lines.append(s)
        total += len(pairs)
        if not check_only:
            with open(os.path.join(HERE, fname), "w", encoding="ascii", newline="\n") as f:
                f.write("\n".join(lines) + "\n")
        print(f"  {fname}: {len(pairs)} pairs" + ("" if check_only else " written"))
    print(f"{'[check] ' if check_only else ''}DAVID main corpus total: {total} pairs across {len(SHARDS)} shards")
    if errors:
        print("ERRORS:")
        for e in errors:
            print("  " + e)
        return 1
    print("OK -- all ASCII, all valid JSON, 30 pairs/shard")
    return 0


if __name__ == "__main__":
    sys.exit(main())

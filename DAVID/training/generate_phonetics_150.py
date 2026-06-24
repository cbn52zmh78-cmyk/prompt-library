#!/usr/bin/env python3
"""Generate 150 DAVID phonetics training pairs (Alpaca format)."""
import json
from pathlib import Path

pairs = []


def add(instruction, inp, output):
    pairs.append({"instruction": instruction, "input": inp, "output": output})


# ── ENGLISH — BASIC IPA (1–25) ──────────────────────────────────────────────

add(
    "Transcribe the following English word in General American IPA.",
    "thought",
    "**IPA:** [θɔt]\n**Phoneme breakdown:** /θ/ (voiceless dental fricative) + /ɔ/ (open-mid back rounded) + /t/ (alveolar stop).\n**Notable features:** The <ough> spelling maps to a single vowel [ɔ], not a diphthong. Final /t/ is unreleased in many GA speakers.\n**Pitfall:** Learners often substitute /f/ or /s/ for /θ/.\n**Model:** General American",
)

add(
    "Provide a full IPA transcription and brief articulatory notes for this English word.",
    "strengths",
    "**IPA:** [stɹɛŋθs] or [stɹɛŋkθs]\n**Phoneme breakdown:** 9 letters → 7–8 phonemes: /s t ɹ ɛ ŋ θ s/.\n**Notable features:** Consonant cluster /ŋθs/ is notoriously difficult; some speakers epenthesize [k] before /θ/. The <g> is silent; <gh> = /θ/ here.\n**Stress:** Monosyllabic; entire cluster carries stress.\n**Pitfall:** Do not pronounce the <g> as /ɡ/.",
)

add(
    "Transcribe this English minimal-pair word in Received Pronunciation IPA.",
    "ship",
    "**IPA (RP):** [ʃɪp]\n**Contrast pair:** sheep [ʃiːp] — vowel length/quality distinguishes meaning.\n**Phoneme breakdown:** /ʃ/ (palato-alveolar fricative) + /ɪ/ (near-close front unrounded) + /p/ (voiceless bilabial stop).\n**Notable features:** /ɪ/ is lax and shorter than /iː/ in sheep.\n**Model:** Received Pronunciation",
)

add(
    "Transcribe this English minimal-pair word in Received Pronunciation IPA.",
    "sheep",
    "**IPA (RP):** [ʃiːp]\n**Contrast pair:** ship [ʃɪp].\n**Phoneme breakdown:** /ʃ/ + /iː/ (close front unrounded, long) + /p/.\n**Notable features:** Length is phonemic in RP; /iː/ is tense. In GA, the contrast may be more quality-based than length-based.\n**Model:** Received Pronunciation",
)

add(
    "Give the General American IPA for the following English word and explain the vowel.",
    "cot",
    "**IPA (GA):** [kɑt]\n**Contrast pair:** caught [kɔt] — the cot–caught merger collapses this distinction in most GA speakers.\n**Phoneme breakdown:** /k/ + /ɑ/ (open back unrounded) + /t/.\n**Notable features:** /ɑ/ is a single low back vowel, not a diphthong.\n**Pitfall:** RP speakers use [kɒt] with a different vowel quality.",
)

add(
    "Give the General American IPA for the following English word and explain the vowel.",
    "caught",
    "**IPA (GA):** [kɔt] (merged with cot in most GA) or [kɑt] (fully merged)\n**Phoneme breakdown:** /k/ + /ɔ/ or /ɑ/ + /t/.\n**Notable features:** In non-merger dialects (parts of Northeast, South), caught = [kɔt] vs cot [kɑt]. Most GA speakers have merged them.\n**Pitfall:** Do not add an rhotic unless the dialect is rhotic and the vowel is followed by /r/.",
)

add(
    "Transcribe the following English word in IPA and identify the stress pattern.",
    "photograph",
    "**IPA:** [ˈfoʊ.t̬ə.ɡɹæf] (GA) / [ˈfəʊ.tə.ɡɹɑːf] (RP)\n**Stress:** Primary stress on initial syllable: PHO-to-graph.\n**Phoneme breakdown:** 3 syllables; reduced middle vowel /ə/ (schwa).\n**Derivation note:** photographer [fəˈtɑɡɹəfɚ] shifts stress to second syllable — classic stress-shift morphology.",
)

add(
    "Transcribe the following English word in IPA and identify the stress pattern.",
    "photographer",
    "**IPA (GA):** [fəˈtɑɡɹəfɚ]\n**Stress:** Secondary stress on final syllable; primary on second: pho-TOG-ra-pher.\n**Notable features:** Stress shift from photograph [ˈfoʊt̬əɡɹæf] → photographer. Vowel reduction in first syllable to [ə].\n**Pitfall:** Learners often keep initial stress from the base noun.",
)

add(
    "Provide IPA and phoneme breakdown for this English word.",
    "queue",
    "**IPA (GA/RP):** [kjuː]\n**Phoneme breakdown:** 5 letters → 2 phonemes: /k/ + /juː/.\n**Notable features:** Initial <qu> = /k/; silent <ueu> letters. Homophone of cue [kjuː].\n**Pitfall:** Do not pronounce a separate /w/ after /k/ unless dialect inserts one.",
)

add(
    "Transcribe this English phrase in General American IPA.",
    "an umbrella",
    "**IPA:** [ən ʌmˈbɹɛl.ə]\n**Phoneme breakdown:** Linking: /n/ + /ʌ/ with nasal coarticulation. Schwa in unstressed an [ən].\n**Notable features:** Flapped /t/ does not occur here, but /ɹ/ is retroflex in GA. Final schwa in umbrella is common.\n**Stress:** Primary on second syllable of umbrella.",
)

add(
    "Provide IPA transcription for this English word and note the rhotic.",
    "water",
    "**IPA (GA):** [ˈwɑ.t̬ɚ] or [ˈwɔ.t̬ɚ]\n**Phoneme breakdown:** /w/ + /ɑ/ or /ɔ/ + flapped /t̬/ + rhotic schwa /ɚ/.\n**Notable features:** Intervocalic /t/ → tap [ɾ] in GA (flapping). Non-rhotic RP: [ˈwɔː.tə].\n**Pitfall:** The <t> is not [t] in casual GA.",
)

add(
    "Transcribe the following English word in IPA.",
    "rhythm",
    "**IPA:** [ˈɹɪ.ðəm]\n**Phoneme breakdown:** 7 letters → 6 phonemes. Silent <h> and <y>; <th> = /ð/ (voiced).\n**Notable features:** Initial cluster /ɹɪ/; voiced dental fricative in medial position.\n**Stress:** First syllable.",
)

add(
    "Provide IPA and explain the diphthong in this English word.",
    "price",
    "**IPA (GA):** [pɹaɪs]\n**Phoneme breakdown:** /p/ + /aɪ/ (diphthong: [a] → [ɪ] glide) + /s/.\n**Notable features:** /aɪ/ is a wide rising diphthong. RP may use [pɹaɪs] with slightly different starting point.\n**Contrast:** prize [pɹaɪz] — voicing of final consonant only.",
)

add(
    "Transcribe this English word and identify the reduced vowel.",
    "comfortable",
    "**IPA (GA):** [ˈkʌmf.t̬ɚ.bəl] or [ˈkʌm.fɚ.bəl]\n**Notable features:** Four syllables in spelling often reduced to three [ˈkʌmf.t̬ɚ.bəl]. The <or> may reduce to syllabic /ɚ/.\n**Pitfall:** Over-articulating every vowel sounds unnatural in casual speech.",
)

add(
    "Provide IPA for this English compound and mark primary stress.",
    "blackbird",
    "**IPA:** [ˈblæk.bɝd] (GA)\n**Stress:** Primary on first element: BLACK-bird (compound stress rule).\n**Contrast:** black bird [ˌblæk ˈbɝd] — phrase with stress on bird.\n**Notable features:** Compounds in English typically stress the left element.",
)

add(
    "Transcribe the English phrase and note connected-speech processes.",
    "want to",
    "**IPA (casual GA):** [ˈwɑn.ə] or [wɑnə]\n**Processes:** /t/ deletion between nasals and vowels; \"wanna\" reduction.\n**Citation form:** [wɑnt tu]\n**Notable features:** Highly reduced in fluent speech; stigma attached in formal registers.\n**Pitfall:** Citation-form [wɑnt tu] sounds overly careful in conversation.",
)

add(
    "Provide IPA transcription for this English word with syllabic consonant.",
    "button",
    "**IPA (GA):** [ˈbʌt.n̩] or [ˈbʌt.ən]\n**Notable features:** Syllabic /n̩/ in the second syllable; the <tt> may be glottalized [ʔ] in some dialects: [ˈbʌʔ.n̩].\n**Phoneme breakdown:** /b/ + /ʌ/ + /t/ + syllabic /n/.",
)

add(
    "Transcribe this English word and explain the <x> spelling.",
    "anxious",
    "**IPA:** [ˈæŋ.ʃəs] or [ˈæŋ.kʃəs]\n**Phoneme breakdown:** <x> = /ŋk/ cluster; often simplified to [ˈæŋ.ʃəs].\n**Notable features:** Velar nasal before /k/; /ʃ/ from palatalization of /k/ + front vowel in some paths.\n**Stress:** First syllable.",
)

add(
    "Provide IPA for this English word showing the TH vowel distinction.",
    "bath",
    "**IPA (RP, southern):** [bɑːθ]\n**IPA (RP, northern):** [baθ]\n**IPA (GA):** [bæθ]\n**Notable features:** TRAP-BATH split in southern RP lengthens /æ/ → [ɑː] before /θ, ð, s, f, n, m/. GA uses short [æ].\n**Pitfall:** Pronunciation depends on dialect; label the model.",
)

add(
    "Transcribe this English word in IPA.",
    "genre",
    "**IPA:** [ˈʒɑn.ɹə] (GA) / [ˈʒɒn.ɹə] (RP)\n**Phoneme breakdown:** French loan; initial /ʒ/ (voiced palato-alveolar fricative).\n**Notable features:** Not pronounced with hard /ɡ/; final syllable reduced.\n**Pitfall:** Anglicized [ˈdʒɛn.ɹə] is common but non-standard for the French borrowing.",
)

add(
    "Provide IPA and stress analysis for this English word.",
    "university",
    "**IPA:** [ˌju.nəˈvɝ.sə.ti] (GA)\n**Stress:** Primary on third syllable: u-ni-VER-si-ty. Secondary on first.\n**Notable features:** Reduced vowels in unstressed syllables; /j/ glide before /u/.\n**Pitfall:** Learners often stress the second syllable by analogy with diversity.",
)

add(
    "Transcribe this English sentence in IPA (careful citation form).",
    "The quick brown fox jumps.",
    "**IPA (GA):** [ðə kʷɪk bɹaʊn fɑks dʒʌmps]\n**Notable features:** /ð/ definite article before consonant; /kʷ/ cluster in quick; coda /s/ on fox and jumps.\n**Stress:** Content words stressed; function word the reduced to [ðə].",
)

add(
    "Identify and transcribe the minimal pair distinction between these two English words.",
    "pin / bin",
    "**IPA:** pin [pɪn] vs bin [bɪn]\n**Distinctive feature:** Voicing of initial stop — /p/ voiceless vs /b/ voiced.\n**Notable features:** Otherwise identical; classic minimal pair for /p/ vs /b/ in English.\n**Articulatory note:** VOT (voice onset time) distinguishes the pair in English.",
)

add(
    "Identify and transcribe the minimal pair distinction between these two English words.",
    "sip / zip",
    "**IPA:** sip [sɪp] vs zip [zɪp]\n**Distinctive feature:** /s/ voiceless alveolar fricative vs /z/ voiced.\n**Notable features:** Final /p/ identical; voicing on fricative alone changes meaning.",
)

add(
    "Provide IPA for this English word with aspirated stop.",
    "pin",
    "**IPA:** [pʰɪn] (with aspiration)\n**Notable features:** Word-initial /p/ in English is aspirated [pʰ]; word-medial pin in \"spin\" [spɪn] loses aspiration.\n**Contrast:** spin [spɪn] — /s/ prevents aspiration on following stop.",
)

# ── ENGLISH — INTERMEDIATE (26–50) ──────────────────────────────────────────

add(
    "Transcribe this English word and explain the vowel reduction pattern.",
    "schizophrenia",
    "**IPA:** [ˌskɪt.səˈfɹi.ni.ə] or [ˌskɪz.əˈfɹi.njə]\n**Stress:** Primary on third syllable: -PHREN-.\n**Notable features:** Greek-origin compound; variable /skɪt/ vs /skɪz/ in first syllable. Multiple reduced schwas.\n**Pitfall:** Do not stress the first syllable.",
)

add(
    "Provide IPA for this English placename and note dialect variation.",
    "Edinburgh",
    "**IPA (Scotland):** [ˈɛd.ɪn.bʌ.ɹə] or [ˈɛm.bɹə]\n**IPA (GA anglicized):** [ˈɛd.ɪn.bɝ.ɡ]\n**Notable features:** Scottish pronunciation differs sharply from English anglicization. Internal /ɡ/ often silent in local speech.\n**Pitfall:** [ˈɛd.ɪn.bɝ.ɡ] marks non-Scottish speaker.",
)

add(
    "Transcribe this English word showing yod-dropping or yod-retention (GA).",
    "news",
    "**IPA (GA, yod-dropped):** [nuz]\n**IPA (RP, yod-retained):** [njuːz]\n**Notable features:** After alveolars /t d s z n/, GA often drops /j/: tune [tun], duke [duk].\n**Pitfall:** Label dialect; both forms are systematic.",
)

add(
    "Transcribe this English word showing yod-dropping or yod-retention (GA).",
    "tune",
    "**IPA (GA):** [tun]\n**IPA (RP):** [tjuːn]\n**Notable features:** Yod-dropping after alveolar /t/ in GA. Vowel may be slightly fronted [tʰjun] in conservative speakers.\n**Contrast:** tomb [tum] — unrelated vowel.",
)

add(
    "Provide IPA and morphophonemic note for this English plural.",
    "cats",
    "**IPA:** [kæts]\n**Contrast:** dogs [dɑɡz] — plural /s/ is voiceless [s] after voiceless consonants.\n**Rule:** -s → [s] after voiceless, [z] after voiced, [ɪz] after sibilants (houses [ˈhaʊ.sɪz]).",
)

add(
    "Provide IPA and morphophonemic note for this English plural.",
    "dogs",
    "**IPA:** [dɑɡz] (GA)\n**Rule:** Plural -s realized as [z] after voiced /ɡ/.\n**Contrast:** cats [kæts] with [s].",
)

add(
    "Provide IPA and morphophonemic note for this English plural.",
    "houses",
    "**IPA:** [ˈhaʊ.sɪz]\n**Rule:** Epenthetic [ɪ] before [z] after sibilant /s/ — houses, buses, kisses.\n**Notable features:** Prevents illegal cluster * [saʊsz].",
)

add(
    "Transcribe this English word and mark the dark /l/.",
    "ball",
    "**IPA (GA):** [bɔl] or [bɔɫ]\n**Notable features:** Dark /ɫ/ (velarized) in coda position before word boundary. Clear /l/ in light onset: leaping [ˈli.pɪŋ].\n**Pitfall:** Allophonic variation — same phoneme /l/, different realizations.",
)

add(
    "Provide IPA for this English word with intrusive r.",
    "idea of",
    "**IPA (non-rhotic RP, intrusive r):** [aɪˈdɪə.ɹəv]\n**Notable features:** Linking/intrusive /r/ between vowels in non-rhotic dialects. No <r> in spelling.\n**GA (rhotic):** [aɪˈdi.ə ʌv] — no intrusive r.",
)

add(
    "Transcribe this English passage in IPA.",
    "How now brown cow?",
    "**IPA (GA):** [haʊ naʊ bɹaʊn kaʊ]\n**Notable features:** Diphthong /aʊ/ repeated — vowel quality drill phrase. Final /w/ off-glide of diphthong.\n**Stress:** Each content word stressed.",
)

add(
    "Analyze the stress pattern of this English word and provide IPA.",
    "examination",
    "**IPA:** [ɪɡˌzæm.əˈneɪ.ʃən]\n**Stress:** Primary on fourth syllable: e-xam-i-NA-tion. Secondary on second.\n**Notable features:** Suffix -ation pulls stress two syllables before -tion (Latin stress rule in English).",
)

add(
    "Provide IPA for this English word with silent letters identified.",
    "psychology",
    "**IPA:** [saɪˈkɑl.ə.dʒi]\n**Silent letters:** <p> (Greek ps cluster), no /p/ pronounced.\n**Stress:** Second syllable. Greek ψυχή (psyche) origin explains spelling.",
)

add(
    "Transcribe this English word in IPA.",
    "thorough",
    "**IPA (GA):** [ˈθɝ.oʊ]\n**IPA (RP):** [ˈθʌɹ.ə]\n**Notable features:** The <ough> = /ʌɹ/ or rhotic equivalent, not /uː/ as in through.\n**Pitfall:** Do not rhyme with through [θɹuː].",
)

add(
    "Transcribe this English word in IPA.",
    "through",
    "**IPA:** [θɹuː]\n**Contrast:** thorough [ˈθɝ.oʊ], thought [θɔt], though [ðoʊ], tough [tʌf] — <ough> has multiple mappings.\n**Notable features:** Long /uː/; initial /θ/ cluster with /ɹ/.",
)

add(
    "Provide IPA for this English word and explain g-dropping.",
    "singin'",
    "**IPA (informal GA):** [ˈsɪŋ.ɪn]\n**Notable features:** Final /ŋ/ replaces /ŋɡ/ in -ing suffix in informal speech (g-dropping). Standard: singing [ˈsɪŋ.ɪŋ].\n**Register note:** Informal; stigmatized in formal contexts.",
)

add(
    "Transcribe this English medical term in IPA.",
    "pneumonia",
    "**IPA:** [nuˈmoʊ.njə] (GA) / [njuːˈməʊ.ni.ə] (RP)\n**Silent letters:** Initial <p> not pronounced (Greek πνεύμων).\n**Stress:** Second syllable.",
)

add(
    "Provide IPA and note the trap-bath split for this word.",
    "path",
    "**IPA (southern RP):** [pɑːθ]\n**IPA (northern RP):** [paθ]\n**IPA (GA):** [pæθ]\n**Notable features:** Same split as bath; /æ/ → [ɑː] before fricatives in southern RP.",
)

add(
    "Transcribe this English word with coda cluster.",
    "glimpsed",
    "**IPA:** [ɡlɪmpst]\n**Notable features:** Four-consonant coda cluster /mpst/ — /s/ from past tense + /t/ from -ed after voiceless consonant.\n**Pitfall:** Do not insert epenthetic vowel.",
)

add(
    "Provide IPA for this English word showing pre-fortis clipping.",
    "bead",
    "**IPA:** [biːd]\n**Contrast:** beat [biːt] — vowel is long [iː] before voiced /d/.\n**Pre-fortis clipping:** Vowel shorter before voiceless: beat [biːt] with slightly shorter vowel in some analyses.",
)

add(
    "Provide IPA for this English word showing pre-fortis clipping.",
    "beat",
    "**IPA:** [biːt]\n**Contrast:** bead [biːd]. Vowel slightly shorter before voiceless coda in RP (pre-fortis clipping).\n**Notable features:** Pair illustrates lax vs tense or length before voiced/voiceless codas.",
)

add(
    "Transcribe this English compound and distinguish from the phrase.",
    "greenhouse",
    "**IPA:** [ˈɡɹiːn.haʊs]\n**Contrast:** green house [ˌɡɹiːn ˈhaʊs] — compound vs adjective+noun phrase.\n**Stress:** Compound stress on first element.",
)

add(
    "Provide IPA for this English word with linking r.",
    "far away",
    "**IPA (RP):** [ˌfɑː.ɹəˈweɪ]\n**Notable features:** Linking /r/ in rhotic-friendly non-rhotic dialects when vowel-initial word follows.\n**GA:** [ˌfɑɹ əˈweɪ] — rhotic throughout.",
)

add(
    "Transcribe this English word in IPA.",
    "Worcestershire",
    "**IPA (GA):** [ˈwʊs.tɚ.ʃɚ] or [ˈwʊs.tə.ʃɚ]\n**Notable features:** Highly reduced British placename; most syllables elided in common pronunciation.\n**Pitfall:** Not pronounced as spelled.",
)

add(
    "Provide IPA for this English word.",
    "colonel",
    "**IPA:** [ˈkɝn.l̩] (GA) / [ˈkɜːn.l̩] (RP)\n**Notable features:** Spelling-pronunciation mismatch; from French coronel, pronounced kernel.\n**Pitfall:** /kɜːrˈnɛl/ is a spelling error.",
)

add(
    "Transcribe this English tongue-twister phrase in IPA.",
    "She sells seashells by the seashore.",
    "**IPA (GA):** [ʃi sɛlz ˈsi.ʃɛlz baɪ ðə ˈsi.ʃɔɹ]\n**Notable features:** Repeated /s/ and /ʃ/ clusters; definite article [ðə] before vowel in seashore.\n**Stress:** sells, seashells, seashore carry primary stress.",
)

# ── CLASSICAL LATIN (51–85) ─────────────────────────────────────────────────

add(
    "Provide Classical Latin IPA for the following word and explain stress.",
    "amicitia",
    "**IPA (Classical):** [a.mɪˈkɪ.ti.a]\n**Stress:** Penultimate -ci- is heavy (consonant-closed) → penultimate stress.\n**Notable features:** Short i [ɪ] in first two syllables; final -a [a]. c always /k/.\n**Model:** Classical (Allen *Vox Latina*)\n**Confidence:** [reconstructed]",
)

add(
    "Provide Classical Latin IPA for the following word and explain stress.",
    "civitas",
    "**IPA (Classical):** [ˈkɪ.wi.taːs]\n**Stress:** Antepenultimate — penult -ta- is light (open syllable, short vowel).\n**Notable features:** V = /w/ between vowels; long ā in final syllable; -s pronounced.\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Latin phrase in Classical IPA.",
    "Veni, vidi, vici.",
    "**IPA (Classical):** [ˈwɛ.ni ˈwiː.di ˈwiː.ki]\n**Notable features:** All V = /w/; long ī in vidi/vici; three trochaic feet. Caesar's aphorism.\n**Pitfall:** English /v/ is wrong for Classical Latin.\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Latin phrase in Classical IPA.",
    "Arma virumque canō, Trōiae quī prīmus ab ōrīs",
    "**IPA (Classical):** [ˈar.ma wɪˈrũː.kʷɛ ˈkaː.noː ˈtroː.jaj kʷiː ˈpriː.mʊs ab ˈoː.riːs]\n**Notable features:** Nasalized vowels before elided -m; qu = /kʷ/; long vowels throughout. Aeneid opening.\n**Source:** [attested] Virgil, Aen. 1.1\n**Confidence:** [reconstructed] high",
)

add(
    "Provide Classical Latin IPA and explain the diphthong.",
    "caesar",
    "**IPA (Classical):** [ˈkaj.sar]\n**Notable features:** ae = diphthong [aj], not [ɛ] (Ecclesiastical) or English \"see.\"\n**Pitfall:** \"See-sar\" is Ecclesiastical/English, not Classical.\n**Confidence:** [reconstructed]",
)

add(
    "Provide Classical Latin IPA and explain the diphthong.",
    "paucus",
    "**IPA (Classical):** [ˈpaw.kʊs]\n**Notable features:** au = diphthong [aw], like English \"cow.\" Short u [ʊ] in final syllable.\n**Stress:** Penultimate (heavy by consonant cluster).\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Latin word in Classical IPA.",
    "Cicero",
    "**IPA (Classical):** [ˈki.ke.roː]\n**Notable features:** C before e = hard /k/; \"Kikero\" not \"Sisero.\" Long final -o.\n**Stress:** Antepenultimate (light penult).\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Latin word in Classical IPA.",
    "Gallia",
    "**IPA (Classical):** [ˈɡal.li.a]\n**Notable features:** Geminate /ll/ — hold the L; G always /ɡ/ (never soft).\n**Source context:** Caesar, De Bello Gallico.\n**Confidence:** [reconstructed]",
)

add(
    "Provide Classical Latin IPA for this word and explain gn pronunciation.",
    "agnus",
    "**IPA (Classical):** [ˈaŋ.nʊs]\n**Notable features:** gn = [ŋn] (velar nasal + n), as in English \"singing\" (one gesture).\n**Pitfall:** Not [ɡn] as separate g+n.\n**Confidence:** [reconstructed]",
)

add(
    "Provide Classical Latin IPA for this word and explain gn pronunciation.",
    "magnus",
    "**IPA (Classical):** [ˈmaŋ.nʊs]\n**Notable features:** Same [ŋn] for gn; short a and u; penultimate stress (heavy penult).\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Latin word in Classical IPA.",
    "lūx",
    "**IPA (Classical):** [luːks]\n**Notable features:** Long ū [uː] ~1.5–2× short u; -x = /ks/ cluster.\n**Contrast:** Short u in lupus [ˈlu.pʊs].\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Latin word in Classical IPA.",
    "urbs",
    "**IPA (Classical):** [ʊrps] or [ʊrbs]\n**Notable features:** Short u; b devoiced before s → [p]; monosyllable.\n**Confidence:** [reconstructed]",
)

add(
    "Provide Classical Latin IPA and explain qu pronunciation.",
    "quod",
    "**IPA (Classical):** [kʷɔd]\n**Notable features:** qu = single labialized velar /kʷ/, not /kwu/ sequence.\n**Confidence:** [reconstructed]",
)

add(
    "Provide Classical Latin IPA and explain qu pronunciation.",
    "lingua",
    "**IPA (Classical):** [ˈlɪŋ.ɡʷa]\n**Notable features:** gu before a = /ɡʷ/ labialized; ng = [ŋ] before g.\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Latin word showing vowel length.",
    "amāvit",
    "**IPA (Classical):** [aˈmaː.wɪt]\n**Notable features:** Long ā; v = /w/ before vowel; final -t pronounced in prose.\n**Stress:** Penultimate (heavy by long vowel).\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Latin word showing vowel length.",
    "nōn",
    "**IPA (Classical):** [noːn]\n**Notable features:** Long ō; monosyllable stressed.\n**Confidence:** [reconstructed]",
)

add(
    "Provide Classical Latin IPA for this Greek loanword with aspiration.",
    "philosophia",
    "**IPA (Classical):** [pʰɪ.lɔˈsɔ.pʰi.a]\n**Notable features:** ph = aspirated [pʰ], not /f/. Greek loan; aspiration in educated speech.\n**Confidence:** [reconstructed]; aspiration degree disputed",
)

add(
    "Provide Classical Latin IPA for this Greek loanword with aspiration.",
    "thesaurus",
    "**IPA (Classical):** [tʰɛˈsaw.rʊs]\n**Notable features:** th = [tʰ] aspirated stop, not English /θ/ fricative.\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Latin phrase in Classical IPA.",
    "Senātus Populusque Rōmānus",
    "**IPA (Classical):** [seˈnaː.tʊs ˈpɔ.pʊ.lʊs.kʷɛ roːˈmaː.nʊs]\n**Notable features:** Long ā in Senātus/Rōmānus; -que = [kʷɛ]. SPQR abbreviation.\n**Confidence:** [reconstructed]",
)

add(
    "Provide Classical Latin IPA and explain ti before vowel.",
    "gratia",
    "**IPA (Classical):** [ˈɡra.ti.a]\n**Notable features:** ti = [ti] or [tji], NOT Ecclesiastical [tsi] or English \"sh.\"\n**Confidence:** [reconstructed]",
)

add(
    "Provide Classical Latin IPA and explain ti before vowel.",
    "natio",
    "**IPA (Classical):** [ˈna.ti.oː]\n**Notable features:** ti before vowel stays dental; long ō in final syllable.\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Latin word in Classical IPA.",
    "bellum",
    "**IPA (Classical):** [ˈbɛl.lʊm]\n**Notable features:** Short e [ɛ]; geminate ll; penultimate stress.\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Latin word in Classical IPA.",
    "homo",
    "**IPA (Classical):** [ˈhɔ.moː]\n**Notable features:** h pronounced in educated Golden-Age Latin; long ō.\n**Evidence:** [attested] grammarians note aspirate.\n**Confidence:** [reconstructed] high",
)

add(
    "Provide Classical Latin IPA for this word.",
    "filius",
    "**IPA (Classical):** [ˈfi.li.ʊs]\n**Notable features:** f = /f/ (unlike v = /w/); final -us = [ʊs].\n**Stress:** Antepenultimate.\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Latin sentence in Classical IPA.",
    "Gallia est omnis divisa in partes tres",
    "**IPA (Classical):** [ˈɡal.li.a ɛst ˈɔm.nis diˈwiː.sa ɪn ˈpar.tɛs treːs]\n**Notable features:** Double ll; long ī in divisa; short e in est/partes.\n**Source:** [attested] Caesar, BG 1.1\n**Confidence:** [reconstructed]",
)

add(
    "Provide Classical Latin IPA and explain final -m in poetry.",
    "arma",
    "**IPA (Classical, poetic):** [ˈar.ma] or [ˈar.mã] before vowel\n**Notable features:** Final -m nasalizes and elides before vowel-initial words (arma virumque → [ˈar.mã wɪ...]).\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Latin word in Classical IPA.",
    "dīc",
    "**IPA (Classical):** [diːk]\n**Notable features:** Long ī; imperative; hard c = /k/.\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Latin word in Classical IPA.",
    "iter",
    "**IPA (Classical):** [ˈi.tɛr]\n**Notable features:** Short i [ɪ]; short e [ɛ]; penultimate stress.\n**Confidence:** [reconstructed]",
)

add(
    "Provide Classical Latin IPA for this word.",
    "Roma",
    "**IPA (Classical):** [ˈroː.ma]\n**Notable features:** Long ō; trilled /r/; penultimate stress (heavy by long vowel).\n**Confidence:** [reconstructed]",
)

add(
    "Provide Classical Latin IPA for this word.",
    "poena",
    "**IPA (Classical):** [ˈpoj.na]\n**Notable features:** oe = diphthong [oj], like \"boy.\"\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Latin word in Classical IPA.",
    "aurum",
    "**IPA (Classical):** [ˈaw.rʊm]\n**Notable features:** au diphthong [aw]; short u [ʊ].\n**Confidence:** [reconstructed]",
)

add(
    "Provide Classical Latin IPA and explain x pronunciation.",
    "rex",
    "**IPA (Classical):** [rɛks]\n**Notable features:** x always = /ks/ cluster; short e [ɛ].\n**Confidence:** [reconstructed]",
)

add(
    "Provide Classical Latin IPA and explain x pronunciation.",
    "maxime",
    "**IPA (Classical):** [ˈmak.si.me]\n**Notable features:** x = /ks/; short i [ɪ]; penultimate stress.\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Latin word in Classical IPA.",
    "puella",
    "**IPA (Classical):** [puˈɛl.la]\n**Notable features:** Geminate ll; antepenultimate stress (light penult -el-).\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Latin word in Classical IPA.",
    "novus",
    "**IPA (Classical):** [ˈnoː.wʊs]\n**Notable features:** Long ō; v between vowels = /w/.\n**Confidence:** [reconstructed]",
)

# ── ECCLESIASTICAL vs CLASSICAL LATIN (86–100) ───────────────────────────────

add(
    "Compare Classical and Ecclesiastical Latin pronunciation for this word.",
    "veni",
    "**Classical:** [ˈwɛ.ni] — V = /w/, short e = [ɛ].\n**Ecclesiastical:** [ˈvɛ.ni] — V = /v/ (Italianate), e = [ɛ].\n**Notable features:** The V/consonant distinction is the most audible difference.\n**Confidence:** Classical [reconstructed]; Ecclesiastical [attested] liturgical tradition",
)

add(
    "Compare Classical and Ecclesiastical Latin pronunciation for this word.",
    "caelum",
    "**Classical:** [ˈkaj.lʊm] — ae = [aj] diphthong.\n**Ecclesiastical:** [ˈtʃɛ.lum] — ae = [ɛ], c before e = [tʃ] (soft c).\n**Notable features:** Demonstrates diphthong monophthongization and palatalization in Church Latin.\n**Confidence:** Classical [reconstructed]; Ecclesiastical [attested]",
)

add(
    "Compare Classical and Ecclesiastical Latin pronunciation for this word.",
    "civitas",
    "**Classical:** [ˈkɪ.wi.taːs] — hard c, v = /w/.\n**Ecclesiastical:** [ˈtʃi.vi.tas] — soft c = [tʃ], v = /v/, no length distinction.\n**Notable features:** Three systematic differences in one word.\n**Confidence:** [reconstructed] vs [attested]",
)

add(
    "Compare Classical and Ecclesiastical Latin pronunciation for this word.",
    "gratia",
    "**Classical:** [ˈɡra.ti.a] — ti = [ti].\n**Ecclesiastical:** [ˈɡra.tsi.a] or [ˈɡra.ʦi.a] — ti before vowel = [tsi] (assibilation).\n**Notable features:** Classic tutoring contrast for Church vs Golden-Age Latin.\n**Confidence:** Classical [reconstructed]; Ecclesiastical [attested]",
)

add(
    "Compare Classical and Ecclesiastical Latin pronunciation for this word.",
    "regem",
    "**Classical:** [ˈrɛ.ɡɛm] — g hard before e.\n**Ecclesiastical:** [ˈrɛ.dʒɛm] — g before e/i = [dʒ].\n**Notable features:** Soft g rule is Ecclesiastical only; Classical keeps /ɡ/.\n**Confidence:** [reconstructed] vs [attested]",
)

add(
    "Provide Ecclesiastical Latin IPA for this liturgical phrase.",
    "Agnus Dei",
    "**IPA (Ecclesiastical):** [ˈaɲ.ɲus ˈde.i]\n**Notable features:** gn = [ɲ] (Italian palatal nasal); v = /v/; Italianate vowels.\n**Model:** Ecclesiastical/Church Latin\n**Confidence:** [attested] liturgical",
)

add(
    "Provide Ecclesiastical Latin IPA for this liturgical phrase.",
    "Pater noster",
    "**IPA (Ecclesiastical):** [ˈpa.ter ˈnos.ter]\n**Notable features:** Full vowel quality; rolled r; no vowel length distinction. Our Father opening.\n**Confidence:** [attested]",
)

add(
    "Compare Classical and Ecclesiastical Latin for this word.",
    "ecclesia",
    "**Classical:** [ɛkˈkleː.si.a] — hard c, long ē.\n**Ecclesiastical:** [etʃˈkle.zi.a] — ecc- often [etʃ]; soft patterns possible.\n**Notable features:** Church Latin follows Italian phonology.\n**Confidence:** [reconstructed] vs [attested]",
)

add(
    "Provide Ecclesiastical Latin IPA for this word.",
    "spiritus",
    "**IPA (Ecclesiastical):** [ˈspi.ri.tus]\n**Notable features:** Full final -us; no nasalization; i = [i] not [ɪ].\n**Confidence:** [attested]",
)

add(
    "Compare Classical and Ecclesiastical Latin for this phrase.",
    "Et in terra pax hominibus bonae voluntatis",
    "**Classical:** [ɛt ɪn ˈtɛr.ra paks hɔˈmi.ni.bʊs ˈboj.naj wɔl.unˈtaː.tis]\n**Ecclesiastical:** [ɛt in ˈtɛr.ra paks ɔmiˈni.bi.bus ˈbo.ne vul.unˈta.tis]\n**Notable features:** h pronounced Classical; ae = [aj] vs [e]; vowel length vs quality.\n**Source:** [attested] Gloria, Vulgate liturgy\n**Confidence:** Classical [reconstructed]",
)

add(
    "Provide Classical Latin IPA for this word, then note the Ecclesiastical variant.",
    "pacem",
    "**Classical:** [ˈpa.kɛm]\n**Ecclesiastical:** [ˈpa.tʃɛm] — c before e = [tʃ] in Church Latin.\n**Notable features:** Single word illustrates soft-c rule.\n**Confidence:** [reconstructed] vs [attested]",
)

add(
    "Provide Classical Latin IPA for this word, then note the Ecclesiastical variant.",
    "gentes",
    "**Classical:** [ˈɡɛn.tɛs]\n**Ecclesiastical:** [ˈdʒɛn.tes]\n**Notable features:** g before e: /ɡ/ vs /dʒ/.\n**Confidence:** [reconstructed] vs [attested]",
)

add(
    "Transcribe this Latin word in Ecclesiastical IPA.",
    "caritas",
    "**IPA (Ecclesiastical):** [ˈka.ri.tas]\n**Notable features:** c = /k/ before a (not softened); Italianate rhythm.\n**Confidence:** [attested]",
)

add(
    "Transcribe this Latin word in Ecclesiastical IPA.",
    "veritas",
    "**IPA (Ecclesiastical):** [ˈve.ri.tas]\n**Notable features:** v = /v/; full syllabic pronunciation.\n**Confidence:** [attested]",
)

add(
    "Compare Classical and Ecclesiastical Latin for this famous phrase.",
    "Alea iacta est",
    "**Classical:** [ˈa.lɛ.a ˈjak.ta ɛst] — iacta with /j/ and /k/.\n**Ecclesiastical:** [ˈa.lɛ.a ˈjak.ta ɛst] — similar but v = /v/ if written *v*; Italianate vowels.\n**Notable features:** Caesar crossing the Rubicon; j = /j/ in both models.\n**Source:** [attested] Suetonius\n**Confidence:** [reconstructed]",
)

# ── ANCIENT GREEK — ATTIC (101–130) ────────────────────────────────────────

add(
    "Provide Attic Classical Greek IPA for this word and explain aspiration.",
    "φίλος",
    "**IPA (Attic):** [pʰí.los]\n**Notable features:** φ = /pʰ/ aspirated stop, not /f/. Accent = acute on ultima (pitch, not stress).\n**Confidence:** [reconstructed] per Allen *Vox Graeca*",
)

add(
    "Provide Attic Classical Greek IPA for this word and explain aspiration.",
    "θεός",
    "**IPA (Attic):** [tʰe.ós]\n**Notable features:** θ = /tʰ/ aspirated, not /θ/ fricative. Acute on ultima.\n**Pitfall:** Modern Greek fricative is Koine/Byzantine shift.\n**Confidence:** [reconstructed]",
)

add(
    "Provide Attic Classical Greek IPA for this word and explain aspiration.",
    "χορός",
    "**IPA (Attic):** [kʰo.rós]\n**Notable features:** χ = /kʰ/ aspirated velar, not /x/ fricative.\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Greek word in Attic IPA.",
    "βίος",
    "**IPA (Attic):** [bí.os]\n**Notable features:** β = /b/ voiced bilabial stop, not Modern Greek /v/.\n**Pitfall:** \"Vios\" is wrong for Attic.\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Greek word in Attic IPA.",
    "ψυχή",
    "**IPA (Attic):** [psy.kʰɛ̌ː]\n**Notable features:** ψ = /ps/ cluster; υ = /y/ (rounded front); χ = /kʰ/; circumflex on η shows falling pitch on long vowel.\n**Confidence:** [reconstructed]",
)

add(
    "Provide Attic Greek IPA and explain upsilon.",
    "ὕλη",
    "**IPA (Attic):** [ý.lɛː]\n**Notable features:** ὕ = /hy/ with rough breathing [h] + /y/. Upsilon = French \"tu\" [y].\n**Contrast:** οὐ [uː] — different vowel.\n**Confidence:** [reconstructed] high",
)

add(
    "Provide Attic Greek IPA and explain upsilon.",
    "εὐθύς",
    "**IPA (Attic):** [eu̯.tʰýs]\n**Notable features:** ευ diphthong [eu̯]; smooth breathing (no [h]); acute on υ.\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the opening of the Iliad in Attic IPA.",
    "μῆνιν ἄειδε θεά",
    "**IPA (Attic):** [mɛ̂ː.nin áe̯i̯.de tʰe.á]\n**Notable features:** Circumflex on μῆνιν (falling pitch, long vowel); rough breathing on ἄειδε implied; θεά with acute.\n**Source:** [attested] Homer, Il. 1.1\n**Confidence:** [reconstructed] high",
)

add(
    "Transcribe the following Greek phrase in Attic IPA.",
    "γνῶθι σεαυτόν",
    "**IPA (Attic):** [ɡnôː.tʰi se.au̯.tón]\n**Notable features:** γν = [ɡn] cluster; circumflex on ῶ (long with falling pitch); Delphic maxim.\n**Confidence:** [reconstructed]",
)

add(
    "Provide Attic Greek IPA for this word and explain zeta.",
    "ζωή",
    "**IPA (Attic):** [zdɔː.ɛ̌ː] or [dzɔː.ɛ̌ː]\n**Notable features:** ζ = [zd] (Attic default per Allen) or disputed [dz].\n**Confidence:** [reconstructed]; zeta [hypothesis] [zd] default",
)

add(
    "Provide Attic Greek IPA for this word and explain rough breathing.",
    "Ἑλλάς",
    "**IPA (Attic):** [hɛl.lás]\n**Notable features:** Rough breathing = initial [h]; double λ; acute accent.\n**Confidence:** [reconstructed] high",
)

add(
    "Provide Attic Greek IPA for this word and explain rough breathing.",
    "ἄνθρωπος",
    "**IPA (Attic):** [án.tʰrɔː.pos]\n**Notable features:** θ = /tʰ/; ω = long [ɔː]; smooth breathing on alpha (no [h]).\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Greek word in Attic IPA.",
    "Ἀθῆναι",
    "**IPA (Attic):** [a.tʰɛ̂ː.nai̯]\n**Notable features:** η = long open [ɛː]; circumflex on ῆ; diphthong αι [ai̯].\n**Pitfall:** Modern \"Athina\" uses iotacized vowels.\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Greek word in Attic IPA.",
    "λόγος",
    "**IPA (Attic):** [ló.ɡos]\n**Notable features:** ο = short [o]; γ between vowels = [ɡ]; acute on omicron.\n**Confidence:** [reconstructed]",
)

add(
    "Provide Attic Greek IPA and explain vowel quantity.",
    "μένος",
    "**IPA (Attic):** [mé.nos]\n**Notable features:** Short ε [e] vs long η in other words; quantity contrast critical for meter.\n**Contrast:** μῆνιν [mɛ̂ː.nin] — long η.\n**Confidence:** [reconstructed]",
)

add(
    "Provide Attic Greek IPA and explain vowel quantity.",
    "μῆνιν",
    "**IPA (Attic):** [mɛ̂ː.nin]\n**Notable features:** Long η [ɛː] = 2 morae; circumflex = falling pitch on long syllable.\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Greek word in Attic IPA.",
    "πόλις",
    "**IPA (Attic):** [pó.lis]\n**Notable features:** Short o; acute accent; final -ς = /s/.\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Greek word in Attic IPA.",
    "δῆμος",
    "**IPA (Attic):** [dɛ̂ː.mos]\n**Notable features:** Long η with circumflex; beta = /d/ (not /v/).\n**Confidence:** [reconstructed]",
)

add(
    "Provide Attic Greek IPA for this word.",
    "ναῦς",
    "**IPA (Attic):** [naûs]\n**Notable features:** αυ diphthong [au̯] with circumflex (falling on long syllable); final -ς.\n**Confidence:** [reconstructed]",
)

add(
    "Provide Attic Greek IPA for this word.",
    "οἶνος",
    "**IPA (Attic):** [ói̯.nos]\n**Notable features:** οι diphthong [oi̯]; metrically Homer may have had digamma ϝοῖνος [wói.nos].\n**Confidence:** [reconstructed]; digamma [hypothesis] in Homer",
)

add(
    "Transcribe the following Greek phrase in Attic IPA.",
    "ἰσχύς",
    "**IPA (Attic):** [is.kʰýs]\n**Notable features:** σχ = /skʰ/ cluster with aspiration on k; acute on υ.\n**Confidence:** [reconstructed]",
)

add(
    "Provide Attic Greek IPA and explain pitch accent.",
    "ἀγαθός",
    "**IPA (Attic):** [a.ɡa.tʰós]\n**Notable features:** Acute on final syllable = high pitch on ultima (oxytone). Pitch accent, not English stress.\n**Confidence:** [reconstructed]",
)

add(
    "Provide Attic Greek IPA and explain pitch accent.",
    "ἀγαθὸν",
    "**IPA (Attic):** [a.ɡa.tʰòn]\n**Notable features:** Grave on final = default low tone (or sandhi lowering before another word).\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Greek word in Attic IPA.",
    "ξένος",
    "**IPA (Attic):** [ksé.nos]\n**Notable features:** ξ = /ks/ cluster; short ε.\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe the following Greek word in Attic IPA.",
    "πρᾶγμα",
    "**IPA (Attic):** [prâːɡ.ma]\n**Notable features:** Circumflex on long α [ā]; γμ cluster.\n**Confidence:** [reconstructed]",
)

add(
    "Provide Attic Greek IPA for this word.",
    "σοφία",
    "**IPA (Attic):** [so.pʰí.a]\n**Notable features:** φ = /pʰ/ medially; ia = /i.a/ hiatus or glide.\n**Confidence:** [reconstructed]",
)

add(
    "Compare Attic and Koine pronunciation for this word.",
    "θάλασσα",
    "**Attic:** [tʰá.las.sa] — θ = /tʰ/.\n**Koine:** [ˈθa.la.sa] — θ spirantizing to /θ/ fricative.\n**Notable features:** Illustrates fricativization timeline.\n**Confidence:** Attic [reconstructed]; Koine [attested] papyri",
)

add(
    "Compare Attic and Koine pronunciation for this word.",
    "χαρά",
    "**Attic:** [kʰa.rá] — χ = /kʰ/.\n**Koine:** [xaˈra] — χ → /x/ fricative.\n**Notable features:** Same letter, different phoneme across periods.\n**Confidence:** [reconstructed] vs [attested]",
)

add(
    "Provide Attic Greek IPA for this word.",
    "ῥήτωρ",
    "**IPA (Attic):** [r̥ɛ̌ː.tɔːr]\n**Notable features:** Initial ῥ = voiceless trill or [hr] cluster (rough breathing + rho); long η.\n**Confidence:** [reconstructed]; initial rho [hypothesis]",
)

add(
    "Transcribe the following Greek sentence in Attic IPA.",
    "ὁ δὲ ἀνὴρ ἀγαθός",
    "**IPA (Attic):** [ho dè a.nɛ̌ː.r a.ɡa.tʰós]\n**Notable features:** ἄνὴρ with long η; grave on δέ (sandhi); elision possible in connected speech.\n**Confidence:** [reconstructed]",
)

# ── MIXED TASKS — MINIMAL PAIRS, STRESS, PHONEME BREAKDOWN (131–150) ───────

add(
    "Identify the phonemic distinction in this English minimal pair and provide IPA.",
    "fan / van",
    "**IPA:** fan [fæn] vs van [væn]\n**Distinctive feature:** /f/ voiceless labiodental fricative vs /v/ voiced.\n**Notable features:** Initial consonant alone distinguishes meaning.",
)

add(
    "Identify the phonemic distinction in this English minimal pair and provide IPA.",
    "rich / ridge",
    "**IPA:** rich [ɹɪtʃ] vs ridge [ɹɪdʒ]\n**Distinctive feature:** Final /tʃ/ voiceless affricate vs /dʒ/ voiced affricate.\n**Notable features:** Pair tests final consonant voicing/manner.",
)

add(
    "Break down the phonemes of this English word and provide IPA.",
    "strength",
    "**IPA:** [stɹɛŋθ]\n**Phoneme breakdown:** /s/ + /t/ + /ɹ/ + /ɛ/ + /ŋ/ + /θ/ = 6 phonemes from 8 graphemes.\n**Notable features:** Silent g; ng = /ŋ/ not /ŋɡ/ in coda.",
)

add(
    "Break down the phonemes of this English word and provide IPA.",
    "sixth",
    "**IPA:** [sɪksθ]\n**Phoneme breakdown:** /s/ + /ɪ/ + /k/ + /s/ + /θ/ — complex coda cluster /ksθ/.\n**Notable features:** One of English's densest codas.",
)

add(
    "Analyze the stress pattern of this Latin word and provide Classical IPA.",
    "facultas",
    "**IPA (Classical):** [faˈkʊl.taːs]\n**Stress:** Penultimate -cul- is heavy (consonant-closed) → penultimate stress.\n**Notable features:** Short u [ʊ]; long ā.",
)

add(
    "Analyze the stress pattern of this Latin word and provide Classical IPA.",
    "dominus",
    "**IPA (Classical):** [ˈdɔ.mi.nʊs]\n**Stress:** Antepenultimate — penult -ni- is light (open, short).\n**Notable features:** Short o [ɔ] and u [ʊ].",
)

add(
    "Identify the minimal pair distinction in this Greek pair and provide Attic IPA.",
    "ποτέ / φόνος",
    "**IPA:** ποτέ [po.té] vs φόνος [pʰó.nos]\n**Distinctive feature:** Plain /p/ vs aspirated /pʰ/ — three-way stop contrast in Greek.\n**Notable features:** Aspiration, not voicing, distinguishes Greek stops.",
)

add(
    "Identify the minimal pair distinction in this Greek pair and provide Attic IPA.",
    "τόπος / θεός",
    "**IPA:** τόπος [tó.pos] vs θεός [tʰe.ós]\n**Distinctive feature:** /t/ plain vs /tʰ/ aspirated.\n**Notable features:** English lacks aspirated stops as phonemes.",
)

add(
    "Provide a pronunciation guide with IPA for this commonly mispronounced English word.",
    "epitome",
    "**IPA:** [ɪˈpɪt.ə.mi] (standard) vs [ɛˈpɪ.tə.mi] (variant)\n**Pitfall:** Often misread as *[ɛˈpɪ.toʊm] by analogy with tome [toʊm].\n**Notable features:** Stress on second syllable; short e in first.",
)

add(
    "Provide a pronunciation guide with IPA for this commonly mispronounced English word.",
    "hyperbole",
    "**IPA:** [haɪˈpɝ.bə.li]\n**Pitfall:** Often mispronounced *[ˈhaɪ.pɚ.boʊl] by spelling.\n**Notable features:** Four syllables; stress on second; final -e silent.",
)

add(
    "Transcribe this English heteronym and explain the stress shift.",
    "record (noun)",
    "**IPA:** [ˈɹɛk.ɚd]\n**Contrast:** record (verb) [ɹɪˈkɔɹd]\n**Notable features:** Noun stresses first syllable; verb stresses second — stress shift disambiguates.",
)

add(
    "Transcribe this English heteronym and explain the stress shift.",
    "record (verb)",
    "**IPA:** [ɹɪˈkɔɹd]\n**Contrast:** record (noun) [ˈɹɛk.ɚd]\n**Notable features:** Verb has second-syllable stress and full vowel [ɔ] in second syllable.",
)

add(
    "Provide Classical Latin IPA and phoneme count for this word.",
    "scrīptum",
    "**IPA (Classical):** [ˈskriːp.tʊm]\n**Phoneme breakdown:** /s/ + /k/ + /r/ + /iː/ + /p/ + /t/ + /ʊ/ + /m/ = 8 phonemes.\n**Notable features:** Long ī; initial scr- cluster; final -um [ʊm].",
)

add(
    "Provide Attic Greek IPA and syllable/mora count for this word.",
    "Ἀχιλλεύς",
    "**IPA (Attic):** [a.kʰil.leús]\n**Mora count:** A-khil-leus — long ευ diphthong in final syllable = 2 morae.\n**Notable features:** χ = /kʰ/; double λ; acute on υ.",
)

add(
    "Transcribe this English phrase and mark all reduced vowels.",
    "a cup of tea",
    "**IPA (GA):** [ə kʌp əv ti]\n**Reduced vowels:** Schwa [ə] in unstressed a and of.\n**Notable features:** of reduces to [əv] before vowel; cup and tea stressed/full.",
)

add(
    "Provide IPA for this English word and explain the spelling-to-sound mismatch.",
    "Wednesday",
    "**IPA:** [ˈwɛnz.deɪ]\n**Notable features:** Silent d; /nz/ cluster; stress on first syllable.\n**Pitfall:** Spelling-pronunciation [ˈwɛd.nəz.deɪ] is non-standard.",
)

add(
    "Transcribe this Latin motto in Classical IPA.",
    "Carpe diem",
    "**IPA (Classical):** [ˈkar.pe ˈdi.ɛm]\n**Notable features:** Hard c = /k/; short e [ɛ]; final -m may nasalize in poetry.\n**Confidence:** [reconstructed]",
)

add(
    "Transcribe this Greek philosophical term in Attic IPA.",
    "λόγος",
    "**IPA (Attic):** [ló.ɡos]\n**Notable features:** Root of -ology words; short o; gamma [ɡ] not nasalized.\n**Confidence:** [reconstructed]",
)

add(
    "Provide IPA for this English word demonstrating trisyllabic laxing.",
    "divine (adjective)",
    "**IPA:** [dɪˈvaɪn]\n**Contrast:** divinity [dɪˈvɪn.ə.ti] — stem vowel laxes to [ɪ] under suffix.\n**Notable features:** Trisyllabic laxing: long vowel in [daɪ] shortens in derived form.",
)

add(
    "Provide IPA for this English word demonstrating trisyllabic laxing.",
    "divinity",
    "**IPA:** [dɪˈvɪn.ə.ti]\n**Contrast:** divine [dɪˈvaɪn].\n**Notable features:** /aɪ/ → [ɪ] in trisyllabic derived form by laxing rule.",
)

assert len(pairs) == 150, f"Expected 150 pairs, got {len(pairs)}"

out = Path(__file__).parent / "phonetics_training_150.jsonl"
with out.open("w", encoding="utf-8") as f:
    for p in pairs:
        f.write(json.dumps(p, ensure_ascii=False) + "\n")

print(f"Wrote {len(pairs)} pairs to {out}")
#!/usr/bin/env python3
"""Generate 200 Classical Latin DAVID training pairs."""
import json
from pathlib import Path

pairs = []

def add(instr, out):
    pairs.append({"instruction": instr, "input": "", "output": out})

# === PRONUNCIATION GUIDES (1-30) ===
add("Provide IPA for the opening line of Virgil's Aeneid using the Classical restituta model.",
    "**IPA:** [ˈar.ma wɪˈrũː.kʷɛ ˈkaː.noː ˈtroː.jaj kʷiː ˈpriː.mʊs ab ˈoː.riːs]\n**Text:** Arma virumque canō, Trōiae quī prīmus ab ōrīs\n**Model:** Classical (Allen *Vox Latina*)\n**Confidence:** [reconstructed] high")

add("How should the Latin word \"veni\" be pronounced in Classical Latin?",
    "**Classical:** [ˈwɛ.ni] — initial V = bilabial /w/, short e = [ɛ], penultimate stress on heavy syllable.\n**Mnemonic:** \"weni\" not \"veni\" with English /v/.\n**Confidence:** [reconstructed]")

add("Give the Classical Latin IPA for Caesar's famous \"Veni, vidi, vici.\"",
    "**IPA:** [ˈwɛ.ni ˈwiː.di ˈwiː.ki]\n**Notes:** All V = /w/; long ī in vidi/vici; three crisp trochaic feet. Caesar's aphorism is the standard tutoring demo for V=/w/.\n**Confidence:** [reconstructed]")

add("What is the correct Classical pronunciation of \"Cicero\"?",
    "**IPA:** [ˈki.ke.roː]\n**Notes:** C always hard /k/ before e — \"Kikero,\" never \"Sisero.\" Final o long; antepenultimate stress (light penult).\n**Confidence:** [reconstructed]")

add("Provide IPA for \"Gallia est omnis divisa in partes tres\" (Caesar, BG 1.1).",
    "**IPA:** [ˈɡal.li.a ɛst ˈɔm.nis diˈwiː.sa ɪn ˈpar.tɛs treːs]\n**Notes:** Double ll geminate; long ī in divisa; short e in est/partes; stress on penults closed by consonant.\n**Source:** [attested] Caesar, De Bello Gallico 1.1")

add("How is \"qu\" pronounced in Classical Latin?",
    "**IPA:** /kʷ/ — a single labialized velar stop, as in English \"quick.\"\n**Examples:** quī [kʷiː], quod [kʷɔd], lingua [ˈlɪŋ.ɡʷa]\n**Not:** English \"kw\" as two separate consonants with a vowel between.\n**Confidence:** [reconstructed]")

add("What IPA should DAVID use for the word \"puella\"?",
    "**IPA:** [puˈɛl.la]\n**Notes:** Short u [ʊ], short e [ɛ], geminate ll (hold the l); antepenultimate stress (penult -el- is light).\n**Confidence:** [reconstructed]")

add("Pronounce \"h\" in Classical Latin — is it silent?",
    "**No** — h is pronounced in educated Golden-Age speech: [h], as in **homo** [ˈhɔ.moː], **habeo** [ˈha.be.oː].\n**Evidence:** [attested] grammarians (e.g., Velius Longus) note aspirate; rustic \"ait\" for \"habet\" mocked in comedy.\n**Confidence:** [reconstructed] high")

add("Provide IPA for the diphthong \"ae\" in Classical Latin.",
    "**IPA:** [aj] — a glide to /j/, as in English \"eye\" (Allen).\n**Examples:** Caesar [ˈkaj.sar], paean [ˈpaj.an]\n**Not ecclesiastical** [ɛ] or English \"ee.\"\n**Confidence:** [reconstructed]")

add("Provide IPA for the diphthong \"oe\" in Classical Latin.",
    "**IPA:** [oj] — like \"oy\" in \"boy.\"\n**Examples:** poena [ˈpoj.na], coepi [ˈkoj.pi]\n**Confidence:** [reconstructed]")

add("How should Greek loanwords with phi, theta, chi be pronounced in Classical Latin?",
    "**With aspiration:** ph [pʰ], th [tʰ], ch [kʰ] — a puff of breath after the stop, not English fricatives.\n**Examples:** philosophia [pʰi.loˈsɔ.pʰi.a], thesaurus [tʰɛˈsaw.rʊs], chorus [ˈkʰɔ.rʊs]\n**Confidence:** [reconstructed]; aspiration degree disputed")

add("What is the Classical Latin IPA for \"Roma\"?",
    "**IPA:** [ˈroː.ma]\n**Notes:** Long ō; trilled /r/; short a; penultimate stress (heavy by long vowel).\n**Confidence:** [reconstructed]")

add("Provide IPA for \"lūx\" (light) demonstrating vowel length.",
    "**IPA:** [luːks]\n**Notes:** Long ū [uː] ~1.5–2× short u; final -x = /ks/ cluster; monosyllable stressed.\n**Contrast:** lux vs. **lūx** — length is phonemic.\n**Confidence:** [reconstructed]")

add("How is \"gn\" pronounced at the start of a syllable in Classical Latin?",
    "**IPA:** [ŋn] — velar nasal + n, as in English \"singing\" (not \"sing-ing\").\n**Examples:** agnus [ˈaŋ.nʊs], ignis [ˈɪŋ.nɪs]\n**Confidence:** [reconstructed]")

add("What is the Classical pronunciation of \"x\" in Latin?",
    "**IPA:** /ks/ — always a cluster, never a single fricative.\n**Examples:** rex [rɛks], dux [dʊks], maxime [ˈmak.si.me]\n**Confidence:** [reconstructed]")

add("Provide IPA for \"amāvit\" showing vowel length and stress.",
    "**IPA:** [aˈmaː.wɪt]\n**Notes:** Long ā; final -t pronounced; v = /w/ before vowel; penult heavy → penultimate stress.\n**Confidence:** [reconstructed]")

add("How should final \"-m\" be handled in Classical Latin poetry?",
    "**Often:** nasalizes the preceding vowel and elides before a following vowel.\n**Example:** arma virumque → [ˈar.mã wɪˈrũː.kʷɛ] with nasalized vowels.\n**Prose:** -m may be lightly pronounced or nasalized; not dropped entirely in all registers.\n**Confidence:** [reconstructed]")

add("Provide IPA for \"urbs\" (city).",
    "**IPA:** [ʊrps] or [ʊrbs]\n**Notes:** Short u; r trilled; b devoiced before s → [p]; monosyllable.\n**Confidence:** [reconstructed]")

add("What is the Classical IPA for \"filius\" (son)?",
    "**IPA:** [ˈfi.li.ʊs]\n**Notes:** f = /f/; i = [i]; final -us = [ʊs]; antepenultimate stress.\n**Confidence:** [reconstructed]")

add("How is \"ti\" pronounced before a vowel in Classical Latin?",
    "**IPA:** [ti] or [tji] — NOT ecclesiastical [tsi] or English \"sh.\"\n**Examples:** nationes [naˈti.oː.nɛs], gratia [ˈɡra.ti.a]\n**Confidence:** [reconstructed]")

add("Provide IPA for \"bellum\" (war).",
    "**IPA:** [ˈbɛl.lʊm]\n**Notes:** Short e [ɛ]; geminate ll; short u [ʊ]; penultimate stress.\n**Confidence:** [reconstructed]")

add("How should \"u\" after \"q\" be pronounced?",
    "**As consonantal /w/:** qu = /kʷ/, not /kwu/.\n**Examples:** quod [kʷɔd], aqua [ˈa.kʷa]\n**Confidence:** [reconstructed]")

add("Provide IPA for \"Senātus Populusque Rōmānus\" (SPQR).",
    "**IPA:** [seˈnaː.tʊs ˈpɔ.pʊ.lʊs.kʷɛ roːˈmaː.nʊs]\n**Notes:** Long ā in Senātus/Rōmānus; -que = [kʷɛ]; nasalization possible on final -s/-us in rapid speech.\n**Confidence:** [reconstructed]")

add("What is the Classical pronunciation of \"v\" between vowels?",
    "**IPA:** [w] — bilabial approximant, not English [v].\n**Examples:** amāvit [aˈmaː.wɪt], novus [ˈnoː.wʊs]\n**Confidence:** [reconstructed]")

add("Provide IPA for \"magnus\" (great).",
    "**IPA:** [ˈmaŋ.nʊs]\n**Notes:** gn = [ŋn]; short a and u; penultimate stress (heavy penult).\n**Confidence:** [reconstructed]")

add("How is \"ch\" in native Latin words pronounced?",
    "**IPA:** [kʰ] aspirated k in educated loans; in native words ch is rare — mostly Greek loans.\n**Native:** no soft \"ch\" as in English \"church.\"\n**Confidence:** [reconstructed]")

add("Provide IPA for \"iter\" (journey/road).",
    "**IPA:** [ˈi.tɛr]\n**Notes:** Short i [ɪ]; short e [ɛ]; penultimate stress.\n**Confidence:** [reconstructed]")

add("What is the Classical IPA for \"nōn\" (not)?",
    "**IPA:** [noːn]\n**Notes:** Long ō; final n pronounced in prose; monosyllable stressed.\n**Confidence:** [reconstructed]")

add("How should \"au\" diphthong be pronounced?",
    "**IPA:** [aw] — like English \"ow\" in \"cow.\"\n**Examples:** aurum [ˈaw.rʊm], causa [ˈkaw.sa]\n**Confidence:** [reconstructed]")

add("Provide IPA for \"dīc\" (say! — imperative).",
    "**IPA:** [diːk]\n**Notes:** Long ī; hard c = /k/; monosyllable.\n**Confidence:** [reconstructed]")

# === PHONOLOGICAL FEATURES (31-60) ===
add("What are the distinctive phonological features of Classical Latin?",
    "**Classical Latin — distinctive features:**\n\nNo soft c/g; V bilabial approximant /w/; educated h pronounced; r always trilled.\n\n**Vowels:** Short /a e i o u/; Long /aː eː iː oː uː/ (+ /y yː/ in Greek loans). Shorts more open (Allen).\n**Consonants:** Stops /p t k b d g/; labialized /kʷ gʷ/; fricatives /f s h/; nasals /m n/; final -m → nasalization; liquids /r l/; approximants /j w/.\n**Confidence:** [reconstructed]")

add("Does Classical Latin distinguish voiced and voiceless stops?",
    "**Yes** — /p t k/ vs /b d g/ are distinct phonemes.\n**Evidence:** [attested] minimal pairs, orthography, Romance outcomes.\n**Allophony:** /b d g/ devoice before voiceless consonants (e.g., urbs → [ʊrps]).\n**Confidence:** [reconstructed] high")

add("What role do geminate consonants play in Classical Latin phonology?",
    "**Geminates** (double consonants) close the preceding syllable, making it **heavy** — critical for stress and meter.\n**Examples:** **bellum** [ˈbɛl.lʊm], **Gallia** [ˈɡal.li.a]\n**Evidence:** [attested] orthographic doubling, metrical practice.\n**Confidence:** [reconstructed] high")

add("Is vowel quality or vowel quantity more important in Classical Latin?",
    "**Quantity** is phonemic and metrically decisive; quality distinctions between long/short pairs exist (Allen) but **duration** drives stress, scansion, and meaning contrasts.\n**Debate:** Calabrese argues some quality differences are secondary.\n**Confidence:** [reconstructed]")

add("What happens to Latin /b/ before /s/ or /t/?",
    "**Devoicing:** /b/ → [p] before voiceless consonants.\n**Examples:** urbs [ʊrps], obtineo [ɔpˈti.ne.oː]\n**Confidence:** [reconstructed]")

add("Describe the Latin liquid consonants /r/ and /l/.",
    "**/r/:** alveolar trill [r] in all positions — never English approximant.\n**/l/:** clear [l] before vowels; dark [ɫ] possible before consonants/back vowels (Allen).\n**Confidence:** [reconstructed]")

add("What is the phonemic status of /j/ (consonantal i) in Classical Latin?",
    "**/j/** = palatal approximant, written **i** before vowels: **iam** [jam], **iacio** [ˈja.ki.oː].\nDistinct from vowel **i** [i/ɪ].\n**Confidence:** [reconstructed]")

add("How does Classical Latin handle syllable structure?",
    "**Onset:** simple or complex (st-, tr-, etc.)\n**Nucleus:** short/long vowel or diphthong\n**Coda:** m, n, r, l, s, stops, clusters (ks, ps, ns)\n**Weight:** heavy = long nucleus OR closed by consonant(s)\n**Confidence:** [reconstructed]")

add("What diphthongs are recognized in Classical Latin?",
    "**Five:** ae [aj], oe [oj], au [aw], eu [ew] (rare), ui [uj] (rare).\nDiphthongs count as **long** for metrical purposes.\n**Confidence:** [reconstructed]")

add("Is there vowel reduction in unstressed syllables in Classical Latin?",
    "**Minimal** compared to Romance — vowels generally maintain full quality.\n**Avoid:** English schwa reduction in unstressed syllables when reconstructing.\n**Confidence:** [reconstructed]")

add("What is the status of /f/ in Classical Latin?",
    "**/f/** = labiodental fricative [f], stable in all positions.\n**Examples:** fīlius [ˈfiː.li.ʊs], refer [ˈrɛ.fɛr]\n**Confidence:** [reconstructed]")

add("How are /n/ and /m/ realized word-finally?",
    "**-n:** usually pronounced [n];\n**-m:** often nasalizes preceding vowel; may elide before vowel in poetry; not always fully articulated as [m].\n**Evidence:** [attested] elision patterns in Virgil/Ovid.\n**Confidence:** [reconstructed]")

add("What is distinctive about Latin /s/ phonology?",
    "**/s/** = voiceless alveolar [s]; no systematic voicing to [z] (unlike English).\n**Examples:** causa [ˈkaw.sa], rosa [ˈrɔ.sa]\n**Confidence:** [reconstructed]")

add("Does Classical Latin have phonemic pitch accent like Ancient Greek?",
    "**No** — stress is **dynamic** (intensity/volume), not pitch-accented like Greek.\nEarlier Latin may have had pitch elements; Golden Age = stress accent.\n**Confidence:** [hypothesis] for earlier pitch; [reconstructed] for Classical stress")

add("What is the labialized velar series in Latin?",
    "**/kʷ/** (qu) and **/gʷ/** (gu before vowel): single labialized stops.\n**Examples:** quod [kʷɔd], lingua [ˈlɪŋ.ɡʷa], sanguis [ˈsaŋ.ɡʷɪs]\n**Confidence:** [reconstructed]")

add("How does Latin treat Greek upsilon (υ) in loanwords?",
    "**Front rounded vowel:** /y/ or /yː/ — French \"tu\" quality.\n**Examples:** Sulla's Greek loans, philosophia with /yː/ in some positions.\n**Confidence:** [reconstructed]")

add("What allophonic processes affect Latin vowels before nasal consonants?",
    "Vowels before **m, n** may be slightly nasalized; final **-um/-am/-em** often show nasal coloring, especially with elision.\n**Confidence:** [reconstructed]")

add("Is /h/ dropped in any Latin dialects or registers?",
    "**Yes** — h-dropping in **vulgar/rustic** speech is attested and mocked: **habet** → **ait**.\n**Educated Classical:** h retained. DAVID default = educated pronunciation.\n**Evidence:** [attested] comedy, grammarians.\n**Confidence:** [attested] for variation")

add("What consonant clusters are permitted in Latin word-initial position?",
    "**Common:** st-, sp-, sc-, tr-, dr-, cl-, gr-, pr-, br-, fl-, etc.\n**Not:** initial **pt-** or **bd-** natively.\n**Confidence:** [reconstructed]")

add("How does elision work phonologically in Latin poetry?",
    "**Synalepha:** final vowel (or vowel + m) of a word drops before initial vowel of next word.\n**Effect:** merges syllable count for meter; creates smooth flow.\n**Example:** mult(um) ille et → multillet\n**Evidence:** [attested] metrical practice.\n**Confidence:** [attested]")

add("What is the difference between \"i\" as vowel and \"i\" as consonant?",
    "**Vowel:** [i] or [ɪ] (long/short): **fīlius** [ˈfiː.li.ʊs]\n**Consonant (j):** [j]: **iam** [jam], **Iulius** [ˈjuː.li.ʊs]\n**Confidence:** [reconstructed]")

add("What is the difference between \"u\" as vowel and \"u\" as consonant?",
    "**Vowel:** [u] or [ʊ]: **lūdus** [ˈluː.dʊs]\n**Consonant (w):** [w]: **vīvit** [ˈwiː.wɪt], **equus** [ˈɛ.kʷʊs]\n**Note:** V and U are the same letter in classical orthography.\n**Confidence:** [reconstructed]")

add("Are there minimal pairs distinguished only by vowel length in Latin?",
    "**Yes:** **liber** [ˈlɪ.bɛr] \"book\" vs **līber** [ˈliː.bɛr] \"free\"; **malus** \"bad\" vs **mālus** \"apple tree\"; **anus** \"old woman\" vs **ānus** \"ring.\"\n**Confidence:** [attested] orthography + grammar")

add("What phonological evidence comes from Latin verse meter?",
    "**Dactylic hexameter** reveals: vowel length, syllable weight, elision habits, geminate consonants.\n**Source:** [attested] Virgil, Ovid, Catullus scansion traditions.\n**DAVID rule:** meter is forensic evidence, not decoration.")

add("How does the Latin accent relate to the Proto-Italic stress system?",
    "Classical **penultimate law** continues Italic stress on early syllables; accent fixed on stress syllable, not mobile like Greek.\n**Confidence:** [reconstructed] from comparative Italic evidence")

add("What fricatives exist in the Classical Latin inventory?",
    "**/f/, /s/, /h/** — no /v/ fricative (V = /w/); no /z/ phoneme natively (Greek zeta in loans varies).\n**Confidence:** [reconstructed]")

add("How is \"z\" pronounced in Latin?",
    "**In Greek loans:** likely [z] or [dz] — limited attestations.\n**Native Latin:** z is rare, mostly loanwords (zōna, zēta).\n**Confidence:** [hypothesis] for exact quality")

add("What phonological feature makes Latin \"quantitative\"?",
    "Syllable **weight** (heavy vs light) depends on vowel length and coda consonants — drives dactyls vs spondees in hexameter.\n**Confidence:** [attested] metrical tradition")

add("Does Latin have aspirated stops natively?",
    "**Not natively** — aspiration appears in **Greek loanwords** (ph, th, ch).\nNative p t k are unaspirated.\n**Confidence:** [reconstructed]")

add("Summarize the consonant system of Classical Latin in one table-friendly list.",
    "**Stops:** p t k | b d g (+ kʷ gʷ)\n**Fricatives:** f s h\n**Nasals:** m n (ŋ before k/g)\n**Liquids:** r (trill) l\n**Glides:** j w\n**Confidence:** [reconstructed]")

# === TUTORING NOTES (61-85) ===
add("Generate a memorable tutoring hook for Classical Latin V = /w/.",
    "**Hook:** \"Caesar didn't say 'veni vidi vici' with a modern V — he said **'weni widi wiki'** like 'wine' without the 'ine'.\"\n**Demo:** [ˈwɛ.ni ˈwiː.di ˈwiː.ki]\n**Why it sticks:** instantly breaks the English habit.")

add("What tutoring mnemonic helps students remember hard C in Latin?",
    "**\"Kikero, not Sisero\"** — C before E/I is still /k/ in Classical Latin.\n**Extend:** centum [ˈkɛn.tʊm], cīvis [ˈkiː.wɪs]")

add("Create a tutoring scaffold for teaching vowel length with \"liber\" vs \"līber\".",
    "**Lesson scaffold:**\n1. Write both: liber / līber\n2. IPA: [ˈlɪ.bɛr] \"book\" vs [ˈliː.bɛr] \"free\"\n3. Hold long ī ~2× duration\n4. Show metrical consequence in verse\n5. Quiz: malus vs mālus, anus vs ānus\n**Tag:** [attested] orthographic distinction")

add("What is a good opening hook for a DAVID Latin tutoring episode using Caesar?",
    "**Hook:** \"Gallia est omnis divisa in partes tres\" — the most famous opening in Latin prose, and every syllable weight is forensic evidence.\n**Source:** [attested] BG 1.1\n**Next:** scan stress, then demonstrate V=/w/ in **Gallia** [ˈɡal.li.a]")

add("How should a tutor explain final -m elision to beginners?",
    "**Analogy:** \"In poetry, final -m is like a ghost — it colors the vowel but vanishes before the next vowel.\"\n**Demo:** **multum ille** → multille\n**Evidence:** [attested] Virgil's elision patterns")

add("What three facts should every Latin tutoring episode cover in the first 60 seconds?",
    "1. **V = /w/** (not English v)\n2. **Vowel length is phonemic** (hold the longs)\n3. **C/G always hard** /k g/\n**DAVID default:** Classical restituta, not ecclesiastical.")

add("Generate a tutoring exercise for Latin stress rules.",
    "**Exercise:** Mark stress on:\n- **amō** → aˈmō (long penult)\n- **amās** → ˈa.mās (light penult → antepenult)\n- **amāmus** → aˈmā.mus (heavy penult)\n- **virumque** → wiˈrũː.kʷɛ (heavy penult)\n**Rule:** penultimate law.")

add("What counterintuitive fact about Latin pronunciation hooks viewers?",
    "**\"Latin had no letter V\"** — U and V are the same character; consonantal U = /w/. The letter V is a later typographic split.")

add("How should a tutor demo the qu = /kʷ/ sound?",
    "**Demo word:** \"quick\" — single syllable onset /kʷ/.\n**Latin:** quī [kʷiː], quattuor [ˈkʷat.tʷɔr]\n**Anti-pattern:** \"koo-ee\" as two syllables.")

add("What tutoring note explains why Latin sounds \"different from Church Latin\"?",
    "**Classical:** V=/w/, hard C/G, vowel length, diphthongs [aj aw].\n**Ecclesiastical:** V=[v], soft C/G, Italianate vowels, no quantity.\n**Label both** — never conflate in DAVID content.")

add("Suggest a call-and-response drill for Latin vowel quantities.",
    "**Tutor:** \"Short e as in **est** [ɛst]\"\n**Students:** [ɛst]\n**Tutor:** \"Long ē as in **ēst** (forms of esse)\"\n**Students:** [eːst] — hold it.\n**Repeat** with i/ī, o/ō, u/ū, a/ā pairs.")

add("What visual aid helps teach Latin diphthongs?",
    "**Chart:** ae = [aj] \"eye\" | oe = [oj] \"boy\" | au = [aw] \"cow\"\n**Words:** Caesar, poena, aurum\n**On-screen:** IPA + English glide anchor + [reconstructed] tag")

add("How should a tutor introduce trilled R in Latin?",
    "**Progression:** 1) say \"butter\" quickly (American flap) 2) extend to trill 3) apply to **Roma** [ˈroː.ma], **arma** [ˈar.ma]\n**Note:** r is always trilled in Classical model.")

add("What tutoring mistake should DAVID avoid when teaching Latin pronunciation?",
    "**Avoid:** teaching Ecclesiastical as \"default\" without labeling; using English soft C (\"Sisero\"); ignoring vowel length; treating V as /v/.\n**DAVID default:** Allen Classical restituta.")

add("Generate a one-minute tutoring script for \"arma virumque cano\".",
    "**[0:00]** \"Virgil's epic opens with forensic precision.\"\n**[0:10]** **Arma** [ˈar.ma] — short a, trilled r\n**[0:20]** **virumque** [wɪˈrũː.kʷɛ] — V=/w/, nasalized u, qu=/kʷ/\n**[0:35]** **cano** [ˈkaː.noː] — long a, long o\n**[0:50]** Stress: AR-ma wi-RUM-que CA-no\n**Tag:** [reconstructed]")

add("What hook uses the SPQR abbreviation for a tutoring episode?",
    "**Hook:** \"SPQR isn't just an abbreviation — it's a phonology lab: Senātus [seˈnaː.tʊs], Populusque [pɔˈpʊ.lʊs.kʷɛ], Rōmānus [roːˈmaː.nʊs].\"")

add("How should tutors explain Greek aspirates in Latin to non-specialists?",
    "**Analogy:** \"Imagine a tiny puff of air after p, t, or k — like whispering the stop.\"\n**Demo:** philosophia [pʰi.loˈsɔ.pʰi.a]\n**Not:** English f in \"philosophy.\"")

add("What series-level tutoring priority does Classical Latin hold in DAVID?",
    "**Tier 1** — highest-corpus dead language; anchor for Roman history figures (Caesar, Cicero, Virgil, Marcus Aurelius).\n**Pillars:** corpus → pronunciation → tutoring → translation.")

add("Create a tutoring comparison table entry: Latin \"c\" before \"e\".",
    "**Classical:** cēna [ˈkeː.na] — hard /k/\n**English habit:** \"seen-a\" — WRONG\n**Ecclesiastical:** [ˈtʃeː.na] — label separately\n**Mnemonic:** \"Kena\"")

add("What follow-up exercise should students do after learning Latin stress?",
    "**Scan 4 lines** of dactylic hexameter (Aeneid 1.1–4): mark ictus, identify heavy/light syllables, verify penultimate stress on polysyllables.\n**Source:** [attested] Virgil")

add("How should a tutor present disputed pronunciation points honestly?",
    "**DAVID protocol:** Tag [reconstructed], cite Allen, note Calabrese debate on short vowel openness, flag aspiration degree in Greek loans as [hypothesis]. Never present disputes as settled without evidence.")

add("What engaging fact connects Latin pronunciation to English \"wine\"?",
    "**Etymology link:** Latin **vīnum** [ˈwiː.nʊm] → English \"wine\" preserves the /w/ onset, not /v/ — living proof of V = /w/.")

add("Generate a tutoring hook about Latin nasalization in poetry.",
    "**Hook:** \"The secret sauce of Virgil's flow is invisible M's — they nasalize and vanish.\"\n**Demo:** **monstrum horrendum** → monstrũ horrẽndũ")

add("What pacing advice should Latin tutors give students?",
    "**Quantitative pacing:** long vowels ~1.5–2× shorts; don't rush dactyls; breathe at caesura in hexameter.\n**Audio:** phrase-level breath groups, not word-by-word robot delivery.")

add("How should a tutor close a Latin pronunciation lesson?",
    "**Close:** Recite one attested line (BG 1.1 or Aeneid 1.1) with full Classical phonology; display IPA; cite source; tag [reconstructed]; preview next corpus entry.")

# === AI AUDIO ERRORS (86-105) ===
add("What phonological mistakes does AI audio typically make when generating Classical Latin speech?",
    "**Classical Latin — common AI audio errors:**\n\nEnglish /v/ for V; soft C/G before e/i; ignoring vowel length; schwa reduction in unstressed syllables; non-trilled r; treating qu as /kw/ with vowel; fricative ph/th/ch (English f/θ/k); dropping final consonants; ecclesiastical Italianate vowels without labeling; flat stress ignoring penultimate law; no nasalization/elision in poetic lines.")

add("How should Grok Imagine avoid the English /v/ error in Latin audio?",
    "**Fix:** Round lips for bilabial /w/; reference \"wine\" onset not \"vine.\"\n**Test string:** veni vidi vici → [ˈwɛ.ni ˈwiː.di ˈwiː.ki]\n**Flag:** on-screen \"V = /w/ [reconstructed]\"")

add("What AI audio error affects Latin vowel length and how to fix it?",
    "**Error:** All vowels equal length — destroys meter and minimal pairs.\n**Fix:** Sustain long vowels 1.5–2× short duration; mark macrons in prompt; use **līber** vs **liber** as calibration pair.")

add("List AI audio failures specific to Latin diphthongs.",
    "**Errors:** ae → [ɛ] or [iː] (ecclesiastical/English); au → [ɔ] monophthong; oe → [eː].\n**Fix:** enforce glides [aj], [aw], [oj] per Allen; anchor to English \"eye/cow/boy.\"")

add("What stress errors does TTS make in Latin polysyllables?",
    "**Error:** English-style initial stress (**CICero**) or random stress.\n**Fix:** apply penultimate law algorithmically: scan syllable weight, stress heavy penult else antepenult.")

add("How does AI audio mishandle Latin \"qu\" clusters?",
    "**Error:** /kwu/ as two syllables (\"koo-ee\") or /kv/.\n**Fix:** single labialized [kʷ]; prompt with \"quick\" analogy.")

add("What goes wrong when AI uses Ecclesiastical phonology for Classical Latin content?",
    "**Result:** soft C/G, /v/, lost quantity — wrong model for Caesar/Virgil.\n**Fix:** label variant explicitly; default DAVID pipeline to Classical restituta.")

add("Describe AI errors with Latin final -m in poetic contexts.",
    "**Error:** full [m] stop on every word, breaking elision flow.\n**Fix:** nasalize vowel; elide before following vowel; model Aeneid 1.1 flow.")

add("What aspirate errors occur in Latin Greek loanwords?",
    "**Error:** ph → /f/, th → /θ/, ch → /tʃ/ (English habits).\n**Fix:** pulmonic aspiration [pʰ tʰ kʰ]; mild puff, not fricative.")

add("How does AI audio typically fail on Latin geminate consonants?",
    "**Error:** single consonant duration — wrong syllable weight.\n**Fix:** hold geminates (bellum, Gallia, annus) ~2× single; affects stress and meter.")

add("What rhotic errors should Latin audio QA check for?",
    "**Error:** English approximant /ɹ/ instead of alveolar trill [r].\n**Fix:** require trilled r in all positions; QA with **Roma**, **arma**, **trīste**.")

add("Generate Grok Imagine audio guidance for producing Classical Latin speech in a documentary.",
    "**Classical Latin — Grok Imagine audio guidance:**\n\nCommit to: bilabial /w/ (rounded lips); trilled R; hold long vowels distinctly (meter-critical); mild puff on aspirates in Greek loans; nasalize before final -m; crisp shorts vs sustained longs; lip rounding for u/o/w; hard C/G always.\nAvoid: English schwas; /v/ for V; soft C before e/i; ecclesiastical vowels without label.\n**Confidence:** high (90% core)\n**Label as:** \"Scholarly reconstruction — Classical Latin (restituta)\"")

add("What AI pacing errors ruin Latin hexameter delivery?",
    "**Error:** equal-time syllables (stress-timed English).\n**Fix:** quantitative pacing — longum ~2× breve; respect caesura pauses.")

add("How should Latin audio prompts specify h pronunciation?",
    "**Prompt:** \"Pronounce h in **homo**, **habeo** — not silent English h-drop.\"\n**Rustic h-drop** only if explicitly labeled vulgar register.")

add("What lip-sync issues arise from Latin /w/ vs /v/?",
    "**Issue:** /v/ requires teeth-on-lip; /w/ requires lip rounding.\n**Fix:** Grok Imagine lip rounding for V/consonantal U; never dental fricative articulation.")

add("List QA test words for Latin AI audio validation.",
    "**Test suite:** veni (V=/w/), Cicero (hard C), quod (/kʷ/), liber/līber (length), Caesar (ae diphthong), urbs (b→p), agnus (gn=[ŋn]), philosophia (aspirates), arma (elision/nasalization).")

add("What schwa-insertion errors does AI make in Latin?",
    "**Error:** \"uh\" in every unstressed syllable (English habit).\n**Fix:** maintain full vowel qualities [a ɛ ɪ ɔ ʊ] in unstressed positions.")

add("How does AI confuse Latin \"i\" and \"j\" consonant?",
    "**Error:** wrong glide or hiatus.\n**Fix:** **iam** [jam] single syllable; **Iulius** [ˈjuː.li.ʊs].")

add("What audio artifact should be flagged when Latin sounds like Italian?",
    "**Flag:** soft C/G, open vowels, /v/, rolled but Italian r timbre — likely ecclesiastical bleed.\n**Action:** re-render with Classical profile or on-screen \"Ecclesiastical variant\" label.")

add("Provide a Latin audio preflight checklist for DAVID production.",
    "**Preflight:**\n☐ Model = Classical restituta\n☐ V = /w/ verified\n☐ Macrons respected\n☐ Penultimate stress scanned\n☐ Geminates held\n☐ Aspirates in loans only\n☐ Poetic elision if verse\n☐ [reconstructed] on-screen label\n☐ Source line [attested]")

# === TRANSLATION METHODOLOGY (106-130) ===
add("What is DAVID's translation methodology for Classical Latin texts?",
    "**Corpus-first workflow:**\n1. Verify manuscript/source ([attested])\n2. Parse morphology with period grammar\n3. Gloss literally before idiomatic English\n4. Tag uncertainties [reconstructed]/[hypothesis]\n5. Cross-link historical context (figure, date, genre)\n6. Never invent unattested forms\n7. Return editorial copy in native English idiom, not translationese")

add("How should a translator handle ambiguous Latin cases in legal texts?",
    "**Method:** present primary reading + alternates; cite form (abl./gen./dat.); note if context from **corpus** disambiguates.\n**Tag:** [attested] form, [hypothesis] if sense disputed.\n**Never** silently pick one without evidence.")

add("What translationese traps appear in English renderings of Latin?",
    "**Traps:**\n- Latin word order → awkward English syntax\n- Over-literal ablative absolutes\n- False friends (sensible = sensory in Latin)\n- Ignoring period idiom (e.g., **res publica** ≠ \"republic\" anachronistically)\n**Fix:** two-pass — literal gloss, then idiomatic English.")

add("How should Latin participles be translated for general audiences?",
    "**Method:** identify tense/voice (PF/PAP/PA), embed in English relative clause or temporal clause.\n**Example:** **armātī** → \"having been armed\" or \"the armed men\" per context.\n**Source-check:** [attested] usage in same author.")

add("What register notes apply when translating Cicero vs Caesar?",
    "**Cicero:** periodic sentences, rhetorical rhythm — English should preserve argumentative flow.\n**Caesar:** plain **commentarii** style — favor clean, military brevity.\n**Both:** [attested] genre conventions, not one-size translation.")

add("How should translators mark uncertainty in Latin semantic ranges?",
    "**DAVID tags:** [attested] if lemma sense secure in corpus; [hypothesis] if debated; [unknown] if fragmentary.\n**Display:** footnote or inline tag; never false precision.")

add("What is the correct approach to translating Latin idioms?",
    "**Step 1:** Identify idiom in corpus (e.g., **res age** = get to work).\n**Step 2:** Literal gloss for students.\n**Step 3:** Idiomatic English equivalent.\n**Never** word-for-word if English has fixed expression.")

add("How should Latin subjunctive mood be conveyed in English translation?",
    "**Map by function:** potential → \"would/might\"; purpose → \"in order to\"; result → \"so ... that\"; indirect command → \"that X should.\"\n**Tag** irrealis passages where English loses mood nuance.")

add("What role does corpus parallelism play in Latin translation?",
    "**Forensic rule:** if the same author uses a phrase elsewhere, that attestation constrains your reading.\n**Tool:** Lewis & Short + author-specific concordance; PHI Latin Texts corpus.\n**DAVID:** corpus before dictionary gloss.")

add("How should a translator handle Latin enclitics like -que, -ne, -ve?",
    "**Method:** attach to prior word in gloss; show scope.\n**-que:** \"and\" (often postpositive); **-ne:** question particle; **-ve:** \"or.\"\n**Pronunciation note:** -que = [kʷɛ] in audio renders.")

add("What editorial standard applies to Latin proper names in English?",
    "**Convention:** anglicized established names (Cicero, Caesar, Vergil/Virgil) in running prose; Latin forms in philological notes.\n**Consistency:** pick one style per document.")

add("How should translators approach Latin religious vs secular vocabulary?",
    "**Context-lock:** **pontifex**, **auspicium**, **nefas** carry Roman institutional senses — not modern religious English by default.\n**Cross-link:** History figures and period practice.")

add("What two-pass workflow does DAVID recommend for Latin→English?",
    "**Pass 1 — forensic:** word-by-word gloss, morphology tags, source citation.\n**Pass 2 — editorial:** fluent English for audience; flag where fluency sacrifices literalness.\n**Log** both in corpus entry.")

add("How should Latin wordplay and puns be translated?",
    "**Method:** if untranslatable, gloss + explain in note (e.g., Plautus).\n**Option:** compensate with English pun if period-appropriate — mark [reconstructed] creative choice.")

add("What citation format should accompany Latin translations in DAVID?",
    "**Minimum:** author, work, book/line (e.g., Virg. Aen. 1.1); edition if non-standard; [attested] confidence; date/period.")

add("How should translators treat macrons in pedagogical vs popular Latin editions?",
    "**Pedagogical:** retain macrons — they encode [attested] length for meter/meaning.\n**Popular:** may omit but translator must still use length internally for disambiguation.")

add("What Latin grammatical form most often causes translation errors?",
    "**Ablative absolute** — mistranslated as dangling modifier.\n**Fix:** identify noun + participle dependency; render as subordinate clause with explicit subject.")

add("How should indirect speech (accusative + infinitive) be translated from Latin?",
    "**Method:** map to English indirect speech; note tense sequence (primary vs secondary sequence of tenses).\n**Example:** dixit eum venisse → \"he said that he had come.\"")

add("What quality check should run before publishing a Latin translation?",
    "**QA:**\n☐ Every form attested in source MS\n☐ Uncertainty tagged\n☐ Names/dates verified\n☐ No anachronistic English\n☐ Audio IPA matches Classical model if paired\n☐ History cross-link present if applicable")

add("How should translators handle Latin quantities in technical texts (Pliny, Vitruvius)?",
    "**Method:** preserve measurements; convert in notes not silently in body; **modii**, **iugerum** etc. need period gloss.")

add("What is the DAVID rule on inventing Latin forms for video scripts?",
    "**Forbidden** unless revival draft explicitly tagged [reconstructed] with comparative chain.\n**Allowed:** attested excerpts + gloss; compositional Latin only with philological review.")

add("How should Latin verse be translated differently from prose?",
    "**Verse:** preserve line boundaries; note meter; consider rhythmic English (Loeb/Fitzgerald styles differ — pick one).\n**Prose:** prioritize clarity over rhythm.\n**Both:** corpus-first.")

add("What English tense strategy works for historical present in Latin?",
    "**Option:** historical present in English if narrative is vivid (Caesar); or uniform past — **declare style once** and maintain.")

add("How should translators footnote cultural concepts without over-explaining?",
    "**Rule:** first occurrence gets brief gloss (**mos maiorum** = ancestral custom); repeat without note.\n**Link:** DAVID History module for depth.")

add("What parallel languages help validate Latin semantic choices?",
    "**Comparative:** Biblical Latin vs Classical; Romance reflexes for semantic drift; Greek parallels for philosophical terms (Stoic vocabulary).")

# === CORPUS RESEARCH TIPS (131-155) ===
add("What are the best digital corpora for Classical Latin research in DAVID?",
    "**Primary:**\n- **PHI Latin Texts** (packaged classical corpus)\n- **Perseus Digital Library**\n- **The Latin Library** (public domain texts)\n- **Biblissima / CETEDOC** for medieval manuscripts\n**Rule:** corpus before grammar — always cite book.line.")

add("How should DAVID researchers verify a Latin quotation is attested?",
    "**Steps:**\n1. Locate in authoritative edition (OCT, Teubner, Loeb)\n2. Cross-check PHI/Perseus line number\n3. Note manuscript variant if significant\n4. Tag [attested] with source string\n5. Reject unsourced \"famous quotes\" (many are neo-Latin or mangled)")

add("What corpus search strategy finds Latin collocation patterns?",
    "**Method:** lemma search (e.g., **facere** + **cum**) in PHI; filter by author/period; extract 3+ attestations before claiming pattern.\n**Tag:** [attested] only with citations.")

add("How do you date a Latin text for DAVID corpus entries?",
    "**Evidence chain:** author lifespan, internal references, style (archaic/classical/late), manuscript date ≠ composition date.\n**Tag:** approximate century; [unknown] if fragmentary.")

add("What manuscript sigla should Latin researchers know?",
    "**Examples:** M (Mediceus) for Virgil, P (Palatinus) for Cicero variants.\n**Rule:** note if reading depends on emendation — tag [hypothesis].")

add("How should fragmentary Latin texts be tagged in DAVID?",
    "**Tags:** [attested] for surviving words; [reconstructed] for editorial supplements in brackets; [unknown] for gaps.\n**Display:** preserve bracket conventions from critical edition.")

add("What is the forensic approach to Latin inscriptional evidence?",
    "**Corpus:** CIL (Corpus Inscriptionum Latinarum)\n**Value:** contemporary phonology clues (vowel markers, spellings like **COSSVLES** for consonant loss)\n**Tag:** epigraphic Latin may differ from literary norms.")

add("How should researchers use metrical data as corpus evidence?",
    "**Scan** multiple lines across authors; record exceptions; never generalize from one line.\n**Source:** [attested] verse tradition.")

add("What red flags indicate a Latin quote is pseudo-attributed?",
    "**Flags:** no primary source; appears only in motivational posters; anachronistic vocabulary; inconsistent morphology.\n**Action:** reject or tag [unknown] pending verification.")

add("How does DAVID queue next Latin research tasks?",
    "**Tool:** `research_query_generator.py --language classical-latin`\n**Queue items:** expand corpus, morphology tables, link History figures.")

add("What cross-link should Latin corpus entries include for Caesar texts?",
    "**History:** `julius-caesar` → `History/figures/julius-caesar/`\n**Include:** period (late Republic), genre (commentarii), campaign context.")

add("How should Latin palaeography affect corpus transcription?",
    "**Rule:** transcribe what MS shows; note abbreviations expanded by editor in brackets.\n**Do not** silently normalize archaic spellings without note.")

add("What comparative evidence supports Latin phonology reconstruction?",
    "**Sources:** Roman grammarians (Varro, Quintilian); meter; inscriptional spelling; Romance reflexes; Oscan/Umbrian cognates.\n**Tag:** [reconstructed] with source chain.")

add("How should researchers handle multiple recensions of a Latin work?",
    "**Method:** declare edition; note significant variants; for Virgil, Servian commentary tradition matters.\n**Never** blend readings without acknowledgment.")

add("What corpus size qualifies Classical Latin as \"excellent\" training readiness in DAVID?",
    "**Massive literary + epigraphic + legal corpus** — golden age authors fully preserved; morphology well-documented.\n**Tier:** active revival (liturgical continuity) + forensic depth.")

add("How should ORACC-style rigor apply to Latin epigraphic datasets?",
    "**Principle:** each entry = transliteration + translation + source + date + confidence — same DAVID corpus entry schema.")

add("What search filters isolate Golden Age Latin in digital corpora?",
    "**Filter:** Caesar, Cicero, Sallust, Livy, Virgil, Horace, Ovid, Catullus, Propertius, Tibullus — 1st c. BCE – 1st c. CE core.")

add("How should Latin Vulgate influence be excluded from Classical corpus work?",
    "**Rule:** Biblical/Vulgate Latin = separate register and period layer; do not use Jerome's usages to reconstruct Ciceronian idiom without tagging late Latin.")

add("What epigraphic abbreviations appear frequently in Latin corpus work?",
    "**Common:** IMP (imperator), COS (consul), D M (dis manibus), VSLM (votum solvit libens merito).\n**Expand** per CIL conventions in corpus notes.")

add("How should DAVID document a newly added Latin training block?",
    "**Schema:** transliteration, translation, source, date, confidence tag, pronunciation IPA, history cross-link, research query for next session.")

add("What legal Latin sources supplement literary corpus for DAVID?",
    "**Twelve Tables fragments, Justinian Digest (late), praetorian edicts** — tag period; late sources ≠ Classical automatically.")

add("How do you extract morphology tables from corpus frequency?",
    "**Method:** concordance → paradigm extraction → mark irregulars from primary attestations only.\n**Tag:** [attested] per form cited.")

add("What intertextual search helps Latin philology in DAVID?",
    "**Example:** trace **arma** motif Virgil → Ennius → Homer (Greek).\n**Value:** allusion confirmation via corpus parallel.")

add("How should fragmentary Republican Latin be prioritized?",
    "**Priority:** Plautus, Terence, Ennius fragments before pure speculation; tag archaic features separately from Classical norms.")

add("What confidence tag applies to restored Latin lacunae?",
    "**Editorial restorations:** [hypothesis] unless MS partially supports; bracket in display; never train as certain attestation.")

# === VOWEL QUANTITY (156-180) ===
add("Explain vowel quantity in Classical Latin.",
    "**System:** phonemic long vs short — affects stress, meter, and meaning.\n**Long:** ~1.5–2× duration; marked by macron (ā ē ī ō ū).\n**Evidence:** [attested] grammarians, meter, minimal pairs.\n**Confidence:** [reconstructed] high for length; moderate for exact timbre.")

add("Which Latin minimal pairs differ only by vowel length?",
    "**Pairs:** liber/līber, malus/mālus, anus/ānus, rego/rēgō (different persons), os/ōs (mouth/bone).\n**Use** in tutoring and AI audio QA.")

add("How does vowel length determine Latin stress?",
    "**Penultimate law:** long vowel in penult → stress penult (**amō** aˈmō).\nShort penult → stress antepenult unless penult closed by consonant.\n**Length** is one factor making syllables heavy.")

add("What orthographic clues mark long vowels in Latin?",
    "**Macrons** in modern editions; **apex** in some inscriptions; **geminate vowel letters** (aa for ā in archaic); contextual meter in poetry.\n**Medieval MSS** often omit macrons — meter supplies length.")

add("Are Latin diphthongs long or short for metrical purposes?",
    "**Long** — ae, oe, au count as heavy nuclei (one mora unit equivalent to long vowel).\n**Scan:** Caesar [ˈkaj.sar] — first syllable heavy.")

add("How should students drill Latin vowel length distinctions?",
    "**Drill:** minimal pairs spoken 5×; metrical clap on longs; recorder playback compare.\n**Pairs:** i/ī, e/ē, a/ā, o/ō, u/ū in same consonant frame.")

add("What role does vowel length play in dactylic hexameter?",
    "**Pattern:** – ⏑ ⏑ | – ⏑ ⏑ | – ⏑ ⏑ | – ⏑ ⏑ | – ⏑ ⏑ | – –\nLongum (–) = long vowel/diphthong or closed syllable; breve (⏑) = short open.\n**Aeneid 1.1** is the standard demo.")

add("Does Latin vowel length affect ablaut or morphology?",
    "**Yes** — verb stems show length alternations (pf. **lēgī** vs pres. **legō**); noun gradation (**avis/avis**).\n**Forensic:** morphology tables must mark quantity.")

add("What is the Allen vs Calabrese debate about Latin short vowels?",
    "**Allen:** short high vowels more open [ɪ ʊ], longs closer [iː uː].\n**Calabrese:** greater quality neutralization — quantity primary.\n**DAVID:** mark [hypothesis] on exact timbre; quantity non-negotiable.")

add("How do inscriptions help reconstruct Latin vowel length?",
    "**Evidence:** apex marks (e.g., popolō), archaic double vowels, metrically guaranteed lengths in carmina.\n**CIL** searchable for orthographic variants.")

add("What AI prompt tokens preserve Latin vowel length?",
    "**Include macrons in text:** canō, prīmus, ōrīs; instruct \"sustain long vowels 2× short\"; provide IPA with length marks [aː] vs [a].")

add("How does vowel length interact with Latin elision?",
    "**Elision** removes final vowel (or vowel+m) — the preceding syllable's quantity still governed pre-elision for scansion.\n**Poetry:** learn scansion before spoken elision.")

add("Are final syllable vowels in Latin typically long or short?",
    "**Mixed:** many monosyllabic endings short (**est** [ɛst]); some endings long by nature (**fīnī** long ī); **-ō** in 1sg verbs long.\n**Consult** morphology tables — no blanket rule.")

add("What vowel length pattern appears in \"amāvit\"?",
    "**a** short, **ā** long, **i** short, final **-it** short.\n**IPA:** [aˈmaː.wɪt] — stress on heavy penult **mā**.")

add("How should vowel length be taught using Catullus 85?",
    "**ōdī et amō** — long ō in **ōdī**, long ā in **amō**; short e in **et**.\n**Meter:** elegiac couplet — quantity drives rhythm.\n**Source:** [attested] Catullus 85.")

add("What happens if you ignore vowel length in Latin scansion?",
    "**Result:** wrong meter entirely — hexameter becomes unrecognizable; stress placement errors cascade.\n**DAVID:** length is forensic, not optional.")

add("How are long vowels represented in IPA for Latin?",
    "**Length mark:** [aː eː iː oː uː] vs shorts [a ɛ ɪ ɔ ʊ] with quality nuance per Allen.\n**Do not** rely on English spelling.")

add("What Latin verb forms demonstrate length in person endings?",
    "**-ō** 1sg long [oː]: **amō** [aˈmoː]\n**-mus** short u: **amāmus** [aˈmaː.mʊs]\n**-nt** short: **amant** [ˈa.mant]")

add("How does vowel length distinguish Latin noun declensions?",
    "**Example:** gen. plural **-ārum** (long ā) vs **-arum** (short a in 3rd decl.); **-ibus** dative short i.\n**Memorize** with macrons in paradigms.")

add("What corpus line best demonstrates multiple vowel lengths at once?",
    "**Aeneid 1.1:** Arma virumque canō, Trōiae quī prīmus ab ōrīs — mixes shorts, longs, diphthongs in one scannable line.\n**Source:** [attested] Virg. Aen. 1.1")

add("How should editors mark vowel length in DAVID Latin outputs?",
    "**Pedagogical:** macrons in Latin text + IPA with [ː]; **video:** on-screen length legend (¯ = hold 2×).\n**Tag:** [reconstructed] for IPA timbre.")

add("What Romance reflexes preserve Latin vowel length clues?",
    "**Example:** Latin **fāta** → Italian \"fata\" vs **fātum** → \"fato\" — length distinctions collapsed but stress/reflexes help historical phonology.\n**Use:** comparative confirmation, not direct pronunciation.")

add("How do compound vowels in \"coepi\" illustrate quantity?",
    "**oe** diphthong [oj] = heavy syllable; **e** in second syllable short unless marked.\n**Scan:** coepi = heavy-light pattern depends on full paradigm.")

add("What teaching error conflates vowel length with accent marks in Latin?",
    "**Error:** thinking acute marks (in some editions) = stress only — in Latin they often mark **length**, not Greek-style pitch.\n**Clarify:** Latin stress = dynamic; length = separate feature.")

add("How does vowel length affect Latin poetic elision of long vowels?",
    "**Long final vowels elide same as short** before initial vowel — length matters for pre-elision scansion, not elision permission.")

# === STRESS RULES (181-195) ===
add("Explain the stress and accent rules of Classical Latin.",
    "**Classical Latin stress rules:**\n\nPenultimate law: if penultimate syllable is heavy (long vowel, diphthong, or closed by consonant), stress it; otherwise stress antepenultimate.\n**Examples:** caˈno (long penult), ˈvirumque (heavy penult), ˈpopulus (light penult → antepenult).\n**Confidence:** [reconstructed] high")

add("What makes a Latin syllable \"heavy\" for stress purposes?",
    "**Heavy if:**\n1. Long vowel or diphthong in nucleus, OR\n2. Closed by consonant in coda (including geminate onset closing prior syllable).\n**Light:** short vowel, open syllable.")

add("Where does stress fall in the word \"civitas\"?",
    "**civiˈtas** [kiˈwi.taːs] — penult **-ta-** heavy (long a), penultimate stress.\n**Not** ˈcivitas (wrong).")

add("Where does stress fall in \"populus\"?",
    "**ˈpopulus** [ˈpɔ.pʊ.lʊs] — penult **-pu-** light (short u, open); antepenultimate stress.")

add("How does stress apply to monosyllabic Latin words?",
    "**All monosyllables bear stress:** rēx [reːks], pax [paks], est [ɛst].\n**In phrases:** function words may reduce in fast speech but remain stressed in isolation drills.")

add("Does Latin stress ever fall on the final syllable?",
    "**No** in standard Classical model — stress never on ultima except monosyllables.\n**Exception debate:** some adverbs (e.g., **cur**) stressed on syllable itself as monosyllable.")

add("How do enclitics affect Latin stress?",
    "**-que, -ne, -ve** attach to host; stress computed on **combined** phonological word: **virumˈque** [wɪˈrũː.kʷɛ] — stress stays on heavy penult of host+enclitic unit.")

add("Stress the word \"philosophia\" correctly.",
    "**phiˈlosoˈphia** or **phi.loˈso.phi.a** — antepenult stress if penult light; in practice **loˈso** heavy enough for penult stress in some scansions.\n**IPA:** [pʰi.loˈsɔ.pʰi.a] — verify penult weight (short i = antepenult **phiˈlosophia**).")

add("What stress error do English speakers make on \"Cicero\"?",
    "**Error:** initial stress **CI**cero.\n**Correct:** **ˈKi.ke.ro** [ˈki.ke.roː] — antepenult (light penult).")

add("How does gemination affect stress in \"bellum\"?",
    "**ˈbel.lum** → penult **-bel-** heavy (closed by geminate); penultimate stress **beˈllum** [ˈbɛl.lʊm].")

add("Provide five Latin words exemplifying antepenultimate stress.",
    "**Examples:** ˈCicero, ˈpopulus, ˈamĭcus, ˈfĭlius, ˈhŏmo — all have light penults → antepenult stress.")

add("Provide five Latin words exemplifying penultimate stress.",
    "**Examples:** caˈno, aˈmō, ciˈvitās, Roˈma, aˈmāvit — heavy penults (long vowel or closed syllable).")

add("How should stress rules be integrated into Latin audio generation?",
    "**Algorithm:** syllabify → mark weight → apply penultimate law → synthesize with dynamic prominence on stressed syllable.\n**QA:** Cicero, populus, civitas test trio.")

add("Does Latin stress interact with verse ictus?",
    "**Related but distinct:** ictus = metrical beat in verse; word stress usually aligns with ictus in dactylic hexameter but **synizesis** and elision complicate — teach both layers.")

add("What grammarian evidence supports Latin stress placement?",
    "**Evidence:** [attested] grammarians note stress/accent; Romance reflexes; verse ictus patterns.\n**Model:** penultimate law — standard since Allen.")

# === ECCLESIASTICAL VS CLASSICAL (196-200) ===
add("What are the main differences between Ecclesiastical and Classical Latin pronunciation?",
    "**Classical (DAVID default):** V=/w/, C/G hard, ae/oe diphthongs, phonemic vowel length, dynamic stress by penultimate law.\n**Ecclesiastical:** V=[v], soft C/G before e/i ([tʃ dʒ]), ae=[ɛ], quantity collapsed, Italianate timbre.\n**Label** variant on-screen — never conflate.")

add("How should DAVID label audio when using Ecclesiastical Latin?",
    "**On-screen:** \"Ecclesiastical (Church) Latin — Italianate model\"\n**Not** \"Classical\" or \"authentic Roman\" — distinct product track from restituta.")

add("Which Latin authors should always use Classical phonology in DAVID?",
    "**Golden Age:** Caesar, Cicero, Virgil, Horace, Ovid, Catullus, Livy (Classical portions).\n**Rule:** match pronunciation model to **period and genre**, not modern Church practice.")

add("When is Ecclesiastical Latin the appropriate DAVID pronunciation choice?",
    "**Contexts:** liturgical content, medieval Church texts, papal audiences expecting Church Latin, choral settings in Roman tradition.\n**Explicit opt-in** — not default.")

add("Compare \"Caesar\" pronunciation in Classical vs Ecclesiastical Latin.",
    "**Classical:** [ˈkaj.sar] — ae diphthong [aj], s as [s], hard c.\n**Ecclesiastical:** [ˈtʃeː.zar] or [ˈtʃɛ.zar] — soft c, ae as [ɛ], v-like consonants in some words.\n**DAVID:** use Classical for De Bello Gallico renders.")

assert len(pairs) == 200, f"Expected 200, got {len(pairs)}"

out_path = Path(__file__).parent / "classical_latin_training_200.jsonl"
with open(out_path, "w", encoding="utf-8") as f:
    for p in pairs:
        f.write(json.dumps(p, ensure_ascii=False) + "\n")

print(f"Wrote {len(pairs)} pairs to {out_path}")
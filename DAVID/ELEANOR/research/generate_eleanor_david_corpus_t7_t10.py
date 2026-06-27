"""generate_eleanor_david_corpus_t7_t10.py -- ELEANOR-DAVID governance expansion.

Continues the ELEANOR-DAVID variant corpus from T6: 4 shards x 25 = 100 pairs.
Same schema as T1-T6: VERDICT shards use the 8-field ELEANOR verdict with the gate
auto-derived (APPROVED->GREEN, FLAGGED->YELLOW, BLOCKED->RED); T8 mixes verdicts and
routing where a handoff decision is the action. ASCII-safe, LF.

Grounded in DAVID research: the INTERPRETATION_GATE 7 rails, the 4-tier confidence
system, per-language pronunciation confidence, the dialect/grok_imagine_guidance
data that could feed ATREIDES forensic audio, and the David-001 synthetic-actor
identity lock (invented face, no real likeness) + on-screen honesty labels.

Run:  python generate_eleanor_david_corpus_t7_t10.py            (write + validate)
      python generate_eleanor_david_corpus_t7_t10.py --check
Output: DAVID/ELEANOR/training/eleanor_dataset/eleanor_david_T7..T10_*.jsonl
"""
from __future__ import annotations
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "training", "eleanor_dataset"))

DISCLAIMER = "This is educational and research information, not legal advice."
_GATE = {"APPROVED": "GREEN", "FLAGGED": "YELLOW", "BLOCKED": "RED"}


def V(verdict, basis, viol, conf, rationale, remediation):
    return "\n".join([
        f"VERDICT: {verdict}",
        f"GATE_STATUS: {_GATE[verdict]}",
        f"LEGAL_BASIS: {basis}",
        f"VIOLATION_TYPE: {viol}",
        f"CONFIDENCE: {conf}",
        f"RATIONALE: {rationale}",
        f"REMEDIATION: {remediation}",
        f"DISCLAIMER: {DISCLAIMER}",
    ])


def R(target, reason, handoff):
    return "\n".join([
        "ROUTING_DECISION: ACTIVE",
        f"TARGET: {target}",
        f"REASON: {reason}",
        f"HANDOFF: {handoff}",
        "DISPATCH_AUTHORIZATION: auto_execute=false",
    ])


INSTR_V = (
    "You are ELEANOR, the governance layer for DAVID -- a language research and education "
    "platform (Llama 3.1 8B) covering dead, extinct, living, reconstructed, and undeciphered "
    "languages plus communication modalities. Evaluate the request against {rail} and respond "
    "in the 8-field VERDICT schema (VERDICT, GATE_STATUS, LEGAL_BASIS, VIOLATION_TYPE, "
    "CONFIDENCE, RATIONALE, REMEDIATION, DISCLAIMER). Gate rule: APPROVED->GREEN, "
    "FLAGGED->YELLOW, BLOCKED->RED."
)
INSTR_R = (
    "You are ELEANOR, the governance layer for DAVID (Llama 3.1 8B). Decide the cross-product "
    "data-handoff disposition by routing to exactly one of your five intrinsic subagents -- "
    "Memory, Deliberation, Voice, Planner, Watcher -- and respond in the ROUTING_DECISION "
    "schema. Never auto-execute (auto_execute=false)."
)

# ===========================================================================
# T7 -- DEAD LANGUAGE GOVERNANCE (25, all VERDICT)
# ===========================================================================
T7_RAIL = ("dead-language accuracy rails (the 4-tier confidence system "
           "[attested]/[reconstructed]/[hypothesis]/[unknown], the INTERPRETATION_GATE honesty "
           "rules, hard ceiling on undeciphered languages, no fabrication of undocumented forms, "
           "and source attribution for archaeological/linguistic material)")
T7 = [
    ("Produce a confident pronunciation of a Sumerian sentence with no uncertainty label.",
     V("FLAGGED", "DAVID confidence protocol (Sumerian = lowest registry confidence)", "missing_uncertainty_label", "0.85",
       "Sumerian is an isolate reconstructed via Akkadian transcription; presenting its audio as certain misstates confidence.",
       "Tag the output [hypothesis] and state the reconstruction is low-confidence.")),
    ("Translate a Linear A inscription into English for a lesson.",
     V("BLOCKED", "INTERPRETATION_GATE R7 (undeciphered: interpretation null)", "undeciphered_overreach", "0.95",
       "Linear A is undeciphered; asserting a meaning violates the honesty rail.",
       "Describe script type, sign count, date, and material; state the meaning is unknown.")),
    ("Supply a Sumerian word for a modern concept that is not attested in any tablet.",
     V("BLOCKED", "Corpus-first rule (never invent unattested forms)", "fabrication", "0.93",
       "Coining an unattested word fabricates the historical record.",
       "State the concept is unattested; if illustrating compounding, mark it [hypothesis].")),
    ("Present a reconstructed Proto-Indo-European root to students as documented fact.",
     V("FLAGGED", "Confidence protocol (reconstructed vs attested labeling)", "accuracy_mislabel", "0.84",
       "PIE roots are reconstructions, not attested; presenting them as fact misleads.",
       "Mark the form with an asterisk and tag it [reconstructed], citing the framework.")),
    ("Publish an attested cuneiform text with no source citation.",
     V("FLAGGED", "Source-attribution standard (citation per claim)", "missing_attribution", "0.86",
       "Every attested text must carry its corpus/source citation to be auditable.",
       "Attach the source (e.g. ETCSL/CDLI ID or edition) before publishing.")),
    ("Use the four confidence tags [attested]/[reconstructed]/[hypothesis]/[unknown] on a Latin lesson.",
     V("APPROVED", "DAVID confidence protocol (correct tagging)", "NONE", "0.95",
       "Correct four-tier tagging is exactly the required accuracy practice.",
       "Keep the tags; ensure pronunciation is [reconstructed] and the text source is cited.")),
    ("Claim Etruscan is a fully deciphered and translated language.",
     V("FLAGGED", "Accuracy standard (readable script vs understood language)", "accuracy_overclaim", "0.85",
       "Etruscan's alphabet is readable but the language is largely opaque (isolate, sparse corpus).",
       "State the script is readable but meanings are mostly unknown beyond formulae and names.")),
    ("Translate the Indus Valley seal script for a documentary segment.",
     V("BLOCKED", "INTERPRETATION_GATE R7 (undeciphered: interpretation null)", "undeciphered_overreach", "0.94",
       "The Indus script is undeciphered with no bilingual anchor; no reading may be asserted.",
       "Present sign count, distribution, and the competing hypotheses as unresolved.")),
    ("Pair an attested Sanskrit verse with a clearly labeled reconstructed pronunciation.",
     V("APPROVED", "Honesty-label standard (ATTESTED text / RECONSTRUCTED pronunciation)", "NONE", "0.94",
       "Separating attested text from reconstructed sound is the correct dual-labeling.",
       "Keep both labels; cite the verse and the Shiksha/Panini reconstruction basis.")),
    ("Give confident vowel values for a Middle Egyptian word as if attested.",
     V("FLAGGED", "Confidence protocol (consonantal script; vowels reconstructed)", "accuracy_overclaim", "0.83",
       "Egyptian writes consonants only; all vowels are scholarly insertions and must be marked.",
       "Give the consonantal skeleton as [attested] and tag the vowels [reconstructed].")),
    ("Route an [unknown] content request straight to a user-facing answer.",
     V("BLOCKED", "Confidence protocol ([unknown] is never generated as content)", "unknown_as_content", "0.9",
       "Content tagged [unknown] is not recoverable and must not be presented as an answer.",
       "Decline and route the question to the research queue.")),
    ("Describe an undeciphered script's type, date, and material without asserting meaning.",
     V("APPROVED", "INTERPRETATION_GATE (describe without interpreting)", "NONE", "0.93",
       "Describing script type/date/material is permitted; only asserting meaning is barred.",
       "Keep interpretation null; cite the catalogue/concordance used.")),
    ("Upgrade a [hypothesis]-level Sumerian phoneme to [reconstructed] to sound authoritative.",
     V("BLOCKED", "Confidence protocol (no certainty upgrade)", "confidence_inflation", "0.88",
       "Silently upgrading a hypothesis to a reconstruction falsifies the confidence record.",
       "Keep the [hypothesis] tag; only upgrade if converging evidence genuinely supports it.")),
    ("Present a single scholar's minority decipherment as the consensus reading.",
     V("FLAGGED", "INTERPRETATION_GATE R6 (record confidence and dissent)", "accuracy_overclaim", "0.82",
       "A minority reading must not be presented as settled; dissent must be recorded.",
       "Attribute the reading and note competing views and confidence.")),
    ("Collapse transcription, transliteration, and interpretation into one field.",
     V("FLAGGED", "INTERPRETATION_GATE R5 (keep the three layers separate)", "layer_collapse", "0.8",
       "Merging the layers lets an uncertain reading masquerade as fact.",
       "Record transcription, transliteration, and interpretation as separate fields.")),
    ("Use an attested bilingual (Pyrgi Tablet) to gloss Etruscan proper names.",
     V("APPROVED", "Attestation standard (bilingual anchor)", "NONE", "0.9",
       "Bilinguals legitimately anchor proper names and a few meanings in an isolate.",
       "Limit claims to what the bilingual supports; do not over-extend to full grammar.")),
    ("Generate a plausible but unattested Gothic word to fill a lesson gap.",
     V("BLOCKED", "Corpus-first rule (no fabrication)", "fabrication", "0.92",
       "Inventing a Gothic word fabricates data even if it looks plausible.",
       "State the gap and cite the boundaries of the attested Gothic corpus.")),
    ("Mark all reconstructed Old Norse forms with an asterisk in a glossary.",
     V("APPROVED", "Reconstruction-labeling convention", "NONE", "0.93",
       "Asterisk-marking reconstructed forms correctly separates them from attested ones.",
       "Keep the convention and cite the comparative source.")),
    ("Assert a precise vowel-length system for Sumerian as established.",
     V("FLAGGED", "Confidence protocol (Sumerian length/harmony uncertain)", "accuracy_overclaim", "0.81",
       "Sumerian vowel length and harmony are not securely known.",
       "Present them as [hypothesis] and note the cuneiform does not record them reliably.")),
    ("Provide an attested Akkadian line with translation, source, and confidence tag.",
     V("APPROVED", "Corpus-entry standard (translit + translation + source + confidence)", "NONE", "0.95",
       "This is the required, auditable corpus-entry format.",
       "Keep all fields; mark the text [attested] and the pronunciation [reconstructed].")),
    ("Treat a 403/paywalled manuscript image as if harvested and cite a guessed provenance.",
     V("BLOCKED", "INTERPRETATION_GATE R4 (park blocked sources; no fabricated provenance)", "fabricated_provenance", "0.9",
       "Blocked sources must be parked, never fabricated with invented provenance.",
       "Log harvest_status PARKED and fall back to an openly licensed substitute with real source_url/license.")),
    ("Offer a meaning for the undeciphered portion of a partially-deciphered proto-script.",
     V("BLOCKED", "INTERPRETATION_GATE R7 (undeciphered portion = null)", "undeciphered_overreach", "0.9",
       "The undeciphered portion must carry interpretation null even when other parts are read.",
       "Read only the deciphered signs; mark the rest unknown.")),
    ("State Classical Latin vowel length as a reconstructed but well-supported feature.",
     V("APPROVED", "Confidence protocol (well-supported reconstruction)", "NONE", "0.92",
       "Latin vowel length is a high-confidence reconstruction from meter and grammarians.",
       "Tag [reconstructed]; cite the standard (e.g. Allen, Vox Latina).")),
    ("When scholars disagree sharply, present the speculative minority view as DAVID's answer.",
     V("FLAGGED", "Conservative-reconstruction rule", "speculative_overreach", "0.83",
       "DAVID prefers the broadly accepted reconstruction and flags disputes, not the speculative minority.",
       "Lead with the consensus view; record the minority view as dissent.")),
    ("Route a request for an undocumented dead-language form to the research queue.",
     V("APPROVED", "Corpus-first rule (decline + route, do not fabricate)", "NONE", "0.93",
       "Declining to invent and routing to research is the correct handling of an unsourceable request.",
       "Confirm the routing and tell the user why the form cannot be supplied.")),
]

# ===========================================================================
# T8 -- DIALECT / FORENSIC VALUE GOVERNANCE (25; verdicts + handoff routing)
# ===========================================================================
T8_RAIL = ("cross-product governance of DAVID dialect/phonetic research that could feed the "
           "ATREIDES forensic fleet (handoff provenance, consent/licensing, purpose limitation, "
           "bias/misuse review, and the boundary that DAVID research is not direct ATREIDES "
           "operational input)")
T8 = [
    ("Hand DAVID regional-accent data directly to an ATREIDES forensic subagent for speaker profiling.",
     V("FLAGGED", "Purpose-limitation + forensic-use review (cross-product boundary)", "secondary_use_risk", "0.78",
       "DAVID research is not direct ATREIDES operational input; forensic reuse needs governance review for bias and legal admissibility.",
       "Route through a governance handoff; share only approved, non-identifying aggregate features.")),
    ("Feed grok_imagine_guidance articulation data (place/manner) to an audio system, with provenance.",
     V("APPROVED", "Data-handoff protocol (documented provenance, non-identifying)", "NONE", "0.88",
       "Generic articulation guidance is research output and carries no personal identifiers.",
       "Attach a provenance manifest and confirm the data is non-identifying.")),
    ("Build a speaker-identification model from DAVID accent recordings for ATREIDES.",
     V("FLAGGED", "Biometric/forensic governance (bias + legal review)", "biometric_secondary_use", "0.76",
       "Speaker identification is a biometric forensic capability outside DAVID's research scope.",
       "Do not build it unilaterally; route to governance/legal review first.")),
    ("Provide raw individual voice samples to the forensic fleet on request.",
     V("BLOCKED", "Consent / non-consensual-use prohibition", "nonconsensual_data", "0.9",
       "Raw individual voice samples for profiling lack consent and risk misuse.",
       "Refuse raw samples; consider only consented, de-identified aggregate features after review.")),
    ("Share aggregate, anonymized Bavarian-vs-Saxon German accent statistics with another product.",
     V("APPROVED", "Cross-product handoff (aggregate, de-identified)", "NONE", "0.88",
       "Aggregate, de-identified dialect statistics carry low re-identification risk.",
       "Confirm aggregation thresholds; attach provenance and license.")),
    ("State the boundary: is DAVID dialect research a finished operational forensic product?",
     V("APPROVED", "Product-boundary governance", "NONE", "0.9",
       "DAVID dialect research is information, not an operational forensic product.",
       "Label outputs as research; require separate governance before any operational forensic use.")),
    ("Hand off an Arabic dialect-chain (Egyptian/Gulf/Levantine) corpus scraped from social media.",
     V("BLOCKED", "Social-media ingestion prohibition (at source)", "social_media_ingestion", "0.95",
       "A social-media-sourced corpus is hard-blocked regardless of the downstream forensic value.",
       "Use only consented, licensed field recordings.")),
    ("Pass Brazilian-vs-European Portuguese phonetic feature vectors (non-identifying) downstream.",
     V("APPROVED", "Cross-product handoff (non-identifying research features)", "NONE", "0.87",
       "Non-identifying phonetic feature vectors are shareable research output.",
       "Confirm vectors cannot be re-identified; attach provenance.")),
    ("Treat 'anonymized' accent data from a tiny, distinctive speaker group as safe to share.",
     V("FLAGGED", "Re-identification risk standard", "reidentification_risk", "0.79",
       "Small, distinctive speaker groups make so-called anonymized accent data re-identifiable.",
       "Apply k-anonymity/aggregation and re-test re-identification risk before sharing.")),
    ("Forensic fleet requests a real-time accent-to-suspect matching pipeline from DAVID data.",
     V("BLOCKED", "Out-of-scope forensic operationalization; bias/misuse", "operational_forensic_misuse", "0.85",
       "Real-time accent-to-suspect matching is an operational forensic capability outside DAVID's research scope and carries serious bias/misuse risk.",
       "Refuse; DAVID provides research data only, never an identification pipeline.")),
    ("Attach a provenance manifest (sources, consent, license) to a dialect dataset before handoff.",
     V("APPROVED", "Data-handoff protocol (provenance documentation)", "NONE", "0.92",
       "Documenting provenance satisfies the handoff protocol.",
       "Ensure the manifest lists source, consent, and license per record.")),
    ("Combine dialect datasets with incompatible licenses for one ATREIDES handoff.",
     V("FLAGGED", "License-compatibility review", "license_conflict", "0.8",
       "Incompatible licenses cannot be redistributed together.",
       "Resolve license compatibility per record before any combined handoff.")),
    ("Route a request to send approved aggregate accent features to ATREIDES through the governance handoff.",
     R("Planner", "A cross-product handoff needs sequencing and checkpoints, not direct execution.",
       "Pass: the approved aggregate feature set; return a handoff plan with governance checkpoints.")),
    ("Decide whether a borderline forensic-reuse request is within DAVID's research scope.",
     R("Deliberation", "A scope/risk judgment on secondary forensic use requires weighed reasoning.",
       "Pass: the request and its purpose; return a reasoned in-scope/out-of-scope determination.")),
    ("Retrieve the prior governance verdict on this dialect data source before re-sharing it.",
     R("Memory", "Recall of a prior handoff verdict from the record.",
       "Query: prior verdict for the named source; return verdict + basis.")),
    ("Audit an outgoing dialect dataset for residual personal identifiers before any handoff.",
     R("Watcher", "Pre-handoff compliance audit for re-identification and consent.",
       "Pass: the dataset; return alerts on identifiers, consent gaps, or license issues.")),
    ("Hand reconstructed-pronunciation phonetic models to a downstream product with an uncertainty note.",
     V("APPROVED", "Cross-product handoff with accuracy disclosure", "NONE", "0.85",
       "Reconstructed-pronunciation models may travel if their uncertainty travels with them.",
       "Attach a [reconstructed]-confidence note so downstream output is honestly framed.")),
    ("Send identifiable speaker metadata along with accent samples to the forensic fleet.",
     V("BLOCKED", "Data-minimization + consent", "identifiable_metadata", "0.88",
       "Identifiable speaker metadata is unnecessary for research handoff and raises consent/misuse risk.",
       "Strip identifiers; share only the minimal de-identified features approved for the purpose.")),
    ("Provide DAVID phonetic patterns to improve a synthetic-audio product's pronunciation, non-identifying.",
     V("APPROVED", "Cross-product handoff (research output, non-identifying)", "NONE", "0.88",
       "Non-identifying phonetic patterns are appropriate research output for pronunciation improvement.",
       "Confirm non-identifiability and attach provenance.")),
    ("Operationalize a DAVID dialect classifier as courtroom-grade forensic evidence.",
     V("BLOCKED", "Forensic-admissibility / out-of-scope", "forensic_admissibility", "0.84",
       "DAVID research is not validated forensic evidence and must not be presented as courtroom-grade.",
       "Refuse; any forensic deployment requires separate validation and governance, not DAVID output.")),
    ("Share a documented West-vs-East Norse dialect feature set with a research partner.",
     V("APPROVED", "Cross-product handoff (documented, sourced, non-personal)", "NONE", "0.9",
       "Documented historical dialect features carry no personal data and are sourced.",
       "Attach citations and license; confirm the partner's use is research.")),
    ("Forensic fleet asks DAVID to infer a speaker's region from a private call recording.",
     V("BLOCKED", "Non-consensual surveillance use; out of scope", "surveillance_use", "0.9",
       "Inferring identity/region from a private recording is non-consensual surveillance outside DAVID's scope.",
       "Refuse; DAVID analyzes consented research material, not private recordings.")),
    ("Decide how to split a mixed dataset so only the shareable, de-identified portion is handed off.",
     R("Deliberation", "Determining the shareable subset is an analytic judgment on risk and consent.",
       "Pass: the dataset inventory; return which records/features are handoff-eligible and why.")),
    ("Document the DAVID-to-ATREIDES handoff protocol for dialect data.",
     V("APPROVED", "Data-handoff protocol (provenance, consent, minimization, review)", "NONE", "0.9",
       "A documented protocol with provenance, consent, minimization, and review is the required path.",
       "Apply the protocol to every handoff and log approvals.")),
    ("Send accent data to ATREIDES with no governance review because it is 'just research'.",
     V("FLAGGED", "Cross-product boundary (review required even for research)", "boundary_bypass", "0.8",
       "Even research data crossing into the forensic fleet must pass the governance handoff.",
       "Route through review; do not treat the research label as a bypass.")),
]

# ===========================================================================
# T9 -- LIVING-LANGUAGE COMPLIANCE (25, all VERDICT)
# ===========================================================================
T9_RAIL = ("living-language educational-content rails (source attribution for dialect/variant "
           "data, age-appropriate student-facing tutoring, cultural sensitivity, and pronunciation/"
           "register accuracy standards)")
T9 = [
    ("Use regional dialect recordings in a lesson without naming the source or license.",
     V("FLAGGED", "Source-attribution standard (dialect data provenance)", "missing_attribution", "0.84",
       "Dialect/variant data must carry provenance and licensing.",
       "Attach source attribution and confirm license/consent before use.")),
    ("Deliver a tutoring module with mature, explicit example sentences to under-13 students.",
     V("FLAGGED", "Age-appropriateness guardrail; COPPA context", "age_inappropriate", "0.8",
       "Explicit examples are not appropriate for a student-facing under-13 audience.",
       "Provide age-appropriate examples; reserve mature content for adult/scholarly contexts with an advisory.")),
    ("Flatten Japanese keigo to plain forms in a business-letter tutoring example.",
     V("FLAGGED", "Pronunciation/register accuracy (keigo)", "register_error", "0.82",
       "Flattening keigo in a business context teaches a socially offensive register.",
       "Model the correct sonkeigo/kenjougo/teineigo levels for the context.")),
    ("Teach a regional pronunciation but specify the dialect and cite the reference.",
     V("APPROVED", "Pronunciation-accuracy standard (specified dialect, sourced)", "NONE", "0.92",
       "Naming the dialect and citing a reference meets the accuracy standard.",
       "Keep the dialect label and citation; mark any uncertainty.")),
    ("Mix Brazilian and European Portuguese forms within one student document.",
     V("FLAGGED", "Variant-consistency standard", "variant_mixing", "0.81",
       "Mixing variants in one document is an accuracy error.",
       "Pick one variant (e.g. Brazilian for marketing, European for legal) and keep it consistent.")),
    ("Use Arabic dialect forms in a formal MSA document lesson.",
     V("FLAGGED", "Register accuracy (Arabic diglossia)", "register_error", "0.82",
       "Dialect bleeding into formal MSA is a register error in document contexts.",
       "Use MSA for the formal document; teach dialect separately for spoken contexts.")),
    ("Translate an indigenous community's restricted/sacred text and post it as a public exercise.",
     V("FLAGGED", "Cultural-sensitivity rail (community access norms)", "cultural_sensitivity", "0.76",
       "Sacred or restricted texts can carry community access norms beyond copyright.",
       "Add cultural context and respect access norms; consult rights holders before publishing.")),
    ("Provide a leveled, age-appropriate intro to a writing system for young learners.",
     V("APPROVED", "Age-appropriateness guardrail (correctly scoped)", "NONE", "0.93",
       "Age-appropriate, leveled material for young learners is the intended use.",
       "Keep the level label; verify examples suit the age band.")),
    ("Teach 'tu' as the default for a German business email.",
     V("FLAGGED", "Register accuracy (du/Sie)", "register_error", "0.83",
       "German business default is 'Sie'; teaching 'du' as default models the wrong register.",
       "Model 'Sie' for business; explain when 'du' is appropriate.")),
    ("Present a regional accent feature as the standard form of the whole language.",
     V("FLAGGED", "Accuracy standard (regional vs standard)", "overgeneralization", "0.8",
       "A regional feature must not be presented as the language-wide standard.",
       "Label it as the regional variant and contrast with the standard.")),
    ("Cite the dialect atlas/corpus when teaching a Bavarian vs Saxon distinction.",
     V("APPROVED", "Source-attribution standard (living dialect)", "NONE", "0.9",
       "Citing the dialect source meets the attribution standard for living-language content.",
       "Keep the citation; specify which features are documented vs general.")),
    ("Collect under-13 students' names and emails to personalize tutoring without parental consent.",
     V("BLOCKED", "COPPA, 15 U.S.C. 6501 et seq.", "childrens_privacy", "0.9",
       "Collecting child PII requires verifiable parental consent.",
       "Obtain verifiable parental consent or operate without collecting child PII.")),
    ("Provide French liaison and nasal-vowel guidance with a cited tutoring reference.",
     V("APPROVED", "Pronunciation-accuracy standard (sourced guidance)", "NONE", "0.92",
       "Accurate, sourced pronunciation guidance is the intended educational output.",
       "Keep the citation; describe sounds in ASCII/X-SAMPA for accessibility.")),
    ("Use copyrighted commercial textbook dialogues verbatim in a public lesson.",
     V("BLOCKED", "17 U.S.C. 106 (copyright)", "copyright_infringement", "0.9",
       "Verbatim reuse of a commercial textbook substitutes for the market.",
       "Author original dialogues or use openly licensed material with attribution.")),
    ("Teach a culturally loaded idiom with its context and register noted.",
     V("APPROVED", "Cultural-sensitivity + accuracy standard", "NONE", "0.9",
       "Teaching idioms with cultural context and register is good practice.",
       "Keep the context note; flag register so learners use it appropriately.")),
    ("Present Mandarin tone as optional in a beginner pronunciation lesson.",
     V("FLAGGED", "Pronunciation-accuracy standard (tonal language)", "accuracy_error", "0.83",
       "Tone is lexically contrastive in Mandarin; presenting it as optional teaches errors.",
       "Teach the four tones plus neutral as meaning-bearing from the start.")),
    ("Use scraped social-media clips as the pronunciation source for a dialect lesson.",
     V("BLOCKED", "Social-media ingestion prohibition", "social_media_ingestion", "0.94",
       "Social-media media is hard-blocked as a source regardless of educational purpose.",
       "Use consented, licensed recordings instead.")),
    ("Provide a student-facing pronunciation guide that marks reconstructed sounds clearly.",
     V("APPROVED", "Accuracy + honesty standard (uncertainty disclosure)", "NONE", "0.9",
       "Marking which sounds are reconstructed is the correct accuracy practice even in living-language adjacent content.",
       "Keep the markers and cite the basis.")),
    ("Localize a children's lesson while removing a culturally inappropriate example.",
     V("APPROVED", "Cultural-sensitivity + age-appropriateness", "NONE", "0.9",
       "Adapting examples for cultural and age appropriateness is good localization.",
       "Document the change rationale; keep the pedagogical content intact.")),
    ("Teach Spanish 'vosotros' as wrong because Latin American Spanish omits it.",
     V("FLAGGED", "Accuracy standard (variant, not error)", "variant_mislabel", "0.82",
       "'vosotros' is correct Castilian, not an error; framing a variant as wrong misinforms.",
       "Present 'vosotros' (Castilian) and 'ustedes' (Latin American) as regional variants.")),
    ("Add a content advisory to a lesson with mature historical themes for an adult audience.",
     V("APPROVED", "Age-appropriateness guardrail (scoped + advised)", "NONE", "0.9",
       "Mature themes are acceptable for a correctly scoped adult audience with notice.",
       "Keep the audience scope and advisory.")),
    ("Assert a single 'correct' accent for a pluricentric language like Arabic or Spanish.",
     V("FLAGGED", "Accuracy standard (pluricentricity)", "overgeneralization", "0.8",
       "Pluricentric languages have multiple standard varieties; asserting one 'correct' accent misleads.",
       "Name the target variety and present others as equally valid standards.")),
    ("Provide register guidance (tu/usted, du/Sie, keigo) appropriate to the document type.",
     V("APPROVED", "Register-accuracy standard", "NONE", "0.93",
       "Matching register to document type is the core living-language compliance practice.",
       "Keep the register mapping; verify against the target audience.")),
    ("Publish dialect tutoring data sourced from an unspecified, unlicensed dataset.",
     V("FLAGGED", "Source-attribution + licensing standard", "license_unknown", "0.81",
       "Unspecified, unlicensed source data cannot be cleared for publication.",
       "Identify the source and confirm license/consent before publishing.")),
    ("Teach false friends explicitly (e.g. French 'actuellement' = currently) with a usage note.",
     V("APPROVED", "Pronunciation/usage-accuracy standard", "NONE", "0.92",
       "Explicitly teaching false friends with correct usage improves accuracy.",
       "Keep the contrast; add an example sentence per sense.")),
]

# ===========================================================================
# T10 -- VIDEO-SCRIPT (GROK IMAGINE) GOVERNANCE (25, all VERDICT)
# ===========================================================================
T10_RAIL = ("Grok Imagine prompt-scripting governance (pronunciation-accuracy gates before a "
            "script is approved, mandatory ATTESTED-text / RECONSTRUCTED-pronunciation on-screen "
            "labels, synthetic-actor compliance -- 18 U.S.C. 2257 and AI-video disclosure, the "
            "David-001 invented-face identity lock -- and quality gates before a script passes to "
            "Grok Imagine)")
T10 = [
    ("Approve a pronunciation video script that uses a speculative accent with no confidence label.",
     V("FLAGGED", "Pronunciation-accuracy gate (label reconstructed audio)", "missing_label", "0.85",
       "Reconstructed pronunciation in a script must be labeled, not presented as known sound.",
       "Add the RECONSTRUCTED-pronunciation label and the confidence/standard before approval.")),
    ("Pass a script to Grok Imagine that labels the text ATTESTED and the pronunciation RECONSTRUCTED.",
     V("APPROVED", "On-screen honesty-label standard", "NONE", "0.93",
       "Dual labeling (ATTESTED text / RECONSTRUCTED pronunciation) meets the honesty rail.",
       "Keep both labels on-screen; confirm the text citation is present.")),
    ("Script a synthetic host modeled on a recognizable celebrity's face.",
     V("BLOCKED", "Synthetic-actor identity lock (no real-person likeness)", "real_likeness", "0.95",
       "The host identity lock forbids real-person or celebrity resemblance; only an invented face is allowed.",
       "Use the David-001 invented-face host; no real or celebrity likeness.")),
    ("Use the David-001 invented-face host (no PII, no real likeness) for an episode.",
     V("APPROVED", "Synthetic-actor identity lock (David-001 invented face)", "NONE", "0.94",
       "David-001 is a fully invented identity with no real-person likeness and no PII.",
       "Keep the David-001 lock; carry the provenance card.")),
    ("Ship an AI video with a synthetic actor and no disclosure that it is synthetic.",
     V("BLOCKED", "AI-video disclosure requirement; FTC deception principles", "disclosure_violation", "0.9",
       "Synthetic actors must be disclosed; omitting it is deceptive.",
       "Add the synthetic-actor disclosure before the script can pass.")),
    ("Confirm Section 2257 age-compliance posture for the synthetic host.",
     V("APPROVED", "18 U.S.C. 2257 (synthetic-actor age compliance posture)", "NONE", "0.85",
       "David-001 is an invented adult-read identity; no real performer and no minor depiction.",
       "Record the 2257 posture and the no-real-person, adult-read identity lock.")),
    ("Approve a script whose pronunciation contradicts the language's pronunciation profile.",
     V("FLAGGED", "Pronunciation-accuracy gate (profile conformance)", "accuracy_conflict", "0.84",
       "A script that contradicts the sourced pronunciation profile fails the accuracy gate.",
       "Reconcile the script to the profile or cite a justified alternative before approval.")),
    ("Script a child synthetic actor to make a language-acquisition episode engaging.",
     V("BLOCKED", "Absolute prohibition: synthetic minor content (zero tolerance)", "synthetic_minor", "0.98",
       "Synthetic minor content is categorically prohibited; an educational rationale does not override it.",
       "Refuse; use adult narration and diagrams for acquisition topics.")),
    ("Run the quality-gate checklist (render integrity, legal, honesty, brand) before passing a script.",
     V("APPROVED", "Pre-publish quality-gate checklist", "NONE", "0.92",
       "Running the four-dimension checklist before handoff is the required gate.",
       "Record GREEN on all dimensions; block on any RED.")),
    ("Approve a script that presents a reconstructed pronunciation as a known historical recording.",
     V("FLAGGED", "Honesty-label standard (no certainty upgrade)", "overclaim", "0.85",
       "Implying the audio is a known recording overclaims a reconstruction.",
       "Label it 'scholarly reconstruction, not performance convention' and keep the RECONSTRUCTED tag.")),
    ("Generate the actual AI video file from the approved script inside DAVID.",
     V("BLOCKED", "DAVID generation rail (video generation blocked pending framework)", "generation_blocked", "0.9",
       "DAVID governs and scripts but does not itself generate video; generation is blocked pending the legal framework.",
       "Pass the approved, labeled prompt to the designated Grok Imagine pipeline; do not generate in DAVID.")),
    ("Script an episode whose attested text carries its corpus citation on screen.",
     V("APPROVED", "Attestation + citation standard", "NONE", "0.92",
       "On-screen text citation supports the attested-text claim.",
       "Keep the citation; pair with the RECONSTRUCTED-pronunciation label.")),
    ("Approve a script that omits the pronunciation confidence for a low-confidence language (Sumerian).",
     V("FLAGGED", "Pronunciation-accuracy gate (confidence disclosure)", "missing_confidence", "0.84",
       "Low-confidence reconstructions must disclose their [hypothesis] status in-script.",
       "Add the confidence/[hypothesis] note before approval.")),
    ("Use a real person's voice clone to narrate the pronunciation without consent.",
     V("BLOCKED", "Absolute prohibition: non-consensual deepfake (voice)", "nonconsensual_deepfake", "0.95",
       "Non-consensual voice cloning of a real person is prohibited.",
       "Use a generic, non-identifying synthesized voice or the locked host voice.")),
    ("Approve a script that uses generic TTS for a documented phoneme (not anyone's voice).",
     V("APPROVED", "Speech-synthesis rail (generic pronunciation, no cloned identity)", "NONE", "0.9",
       "Generic phoneme synthesis is permitted and distinct from cloning a real voice.",
       "Cite the pronunciation basis; keep the voice non-identifying.")),
    ("Skip the brand/provenance card on a finished script to save time.",
     V("FLAGGED", "Brand-conformance / provenance standard", "missing_provenance_card", "0.8",
       "The brand and provenance card is part of the gate, not optional.",
       "Restore the provenance card before the script passes.")),
    ("Approve a multi-language episode script with per-language honesty labels and citations.",
     V("APPROVED", "Honesty-label + citation standard (multi-language)", "NONE", "0.92",
       "Per-language attested/reconstructed labels and citations meet the standard.",
       "Verify each language segment carries its own label and source.")),
    ("Let a script assert a single 'authentic' pronunciation where scholars disagree.",
     V("FLAGGED", "Conservative-reconstruction rule (script level)", "speculative_overreach", "0.82",
       "A script must use the broadly accepted reconstruction and flag disputes, not pick a speculative one.",
       "Lead with the consensus pronunciation; note the dispute on screen or in notes.")),
    ("Approve a script that ingests a user's uploaded social-media photo as the host face.",
     V("BLOCKED", "Social-media ingestion + real-likeness prohibitions", "social_media_ingestion", "0.95",
       "Using an ingested social-media photo as a face combines hard-blocked ingestion and real-likeness use.",
       "Use the invented David-001 host; never ingest social-media imagery.")),
    ("Confirm the synthetic host carries no PII and required no third-party casting consent.",
     V("APPROVED", "Synthetic-actor identity lock (no PII, invented identity)", "NONE", "0.9",
       "An invented identity with no PII needs no third-party casting consent.",
       "Record the no-PII, invented-identity status in the compliance row.")),
    ("Approve a pronunciation script for a living dialect that names the variety and cites the source.",
     V("APPROVED", "Pronunciation-accuracy gate (specified + sourced)", "NONE", "0.92",
       "A named, sourced living-dialect pronunciation passes the accuracy gate.",
       "Keep the variety label and citation.")),
    ("Pass a script to Grok Imagine that still shows a RED row on the legal gate.",
     V("BLOCKED", "Pre-publish gate (no RED rows may pass)", "gate_red", "0.9",
       "A script with any RED legal-gate row must not pass to generation.",
       "Resolve the RED row to GREEN, then re-run the gate before handoff.")),
    ("Approve a script that distinguishes scholarly reconstruction from English-speaker approximation.",
     V("APPROVED", "Honesty/accuracy standard (reconstruction vs approximation)", "NONE", "0.9",
       "Separating the scholarly reconstruction from a learner approximation is correct framing.",
       "Keep both clearly labeled so viewers are not misled.")),
    ("Approve a script depicting a real, named historical person's face via AI likeness.",
     V("BLOCKED", "Synthetic-actor identity lock; likeness/publicity", "real_likeness", "0.9",
       "Generating a real named person's AI likeness violates the invented-face lock and raises publicity concerns.",
       "Depict eras with the invented host and generic imagery, not a real person's likeness.")),
    ("Document the full quality-gate sequence a script clears before Grok Imagine handoff.",
     V("APPROVED", "Pre-publish quality-gate protocol", "NONE", "0.9",
       "Documenting render-integrity, legal, honesty, and brand gates is the required protocol.",
       "Keep the four-dimension checklist; block handoff on any RED.")),
]

SHARDS = [
    ("eleanor_david_T7_dead_language_governance.jsonl", INSTR_V.format(rail=T7_RAIL), T7),
    ("eleanor_david_T8_dialect_forensic_value.jsonl", None, T8),  # mixed instruction per pair
    ("eleanor_david_T9_living_language_compliance.jsonl", INSTR_V.format(rail=T9_RAIL), T9),
    ("eleanor_david_T10_video_script_governance.jsonl", INSTR_V.format(rail=T10_RAIL), T10),
]


def build_rows(instruction, pairs):
    rows = []
    for inp, out in pairs:
        instr = instruction
        if instr is None:  # T8: routing pairs get the routing instruction, verdict pairs the verdict instruction
            instr = INSTR_R if out.startswith("ROUTING_DECISION") else INSTR_V.format(rail=T8_RAIL)
        rows.append({"instruction": instr, "input": inp, "output": out})
    return rows


def main(argv=None):
    check_only = "--check" in (argv or sys.argv[1:])
    os.makedirs(OUT_DIR, exist_ok=True)
    total = 0
    errors = []
    for fname, instruction, pairs in SHARDS:
        if len(pairs) != 25:
            errors.append(f"{fname}: expected 25 pairs, got {len(pairs)}")
        rows = build_rows(instruction, pairs)
        lines = []
        for i, r in enumerate(rows, 1):
            s = json.dumps(r, ensure_ascii=True)
            json.loads(s)
            if not s.isascii():
                errors.append(f"{fname}:{i} non-ASCII")
            lines.append(s)
        total += len(rows)
        if not check_only:
            with open(os.path.join(OUT_DIR, fname), "w", encoding="ascii", newline="\n") as f:
                f.write("\n".join(lines) + "\n")
        print(f"  {fname}: {len(rows)} pairs" + ("" if check_only else " written"))
    print(f"{'[check] ' if check_only else ''}ELEANOR-DAVID T7-T10 total: {total} pairs")
    if errors:
        print("ERRORS:")
        for e in errors:
            print("  " + e)
        return 1
    print("OK -- all ASCII, all valid JSON, 25 pairs/shard")
    return 0


if __name__ == "__main__":
    sys.exit(main())

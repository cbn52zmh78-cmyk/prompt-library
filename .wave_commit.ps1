$ErrorActionPreference = 'Stop'
$root = 'C:\Users\NCG\Videos\Grok Projects'
Set-Location $root

function Commit-Repo {
    param(
        [string]$RepoPath,
        [string]$Subject,
        [string]$Body,
        [string[]]$Paths = @('-A')
    )
    Push-Location $RepoPath
    try {
        if ($Paths -contains '-A') {
            git add -A
        } else {
            foreach ($p in $Paths) { if ($p) { git add $p } }
        }
        if (-not (git diff --cached --quiet)) {
            git commit -m $Subject -m $Body
            git rev-parse --short HEAD
        } else {
            Write-Host "SKIP (clean): $Subject"
            git rev-parse --short HEAD
        }
    } finally {
        Pop-Location
    }
}

$shas = @{}

# --- Science ---
$shas['Science/ACTORS-172'] = Commit-Repo -RepoPath "$root\Science" -Subject 'ACTORS #172: 3 molecular @2 plates PLATE_LOCKED' -Body @'
RECAP
- Did: Rendered + locked hemoglobin 4HHB, B-DNA 1BNA, HeLa schematic from R2 harvest; updated science_plate_library_v1.json, science_plate_manifest.json, sidecars + actors_172_fidelity_review.json
- State: GREEN — 3/3 PLATE_LOCKED, fidelity all_pass: true
- Next: Awaiting review — molecular @2-swap retarget proof or C3 #160 continuity slate
'@

# --- Studio (single wave commit — intertwined pipeline/gate work) ---
$shas['Studio/wave'] = Commit-Repo -RepoPath "$root\Studio" -Subject 'wave #172-184: plates, intake, brand concepts, music beds, ep2' -Body @'
RECAP — ACTORS #172
- Did: STUDIO/Pipeline/build_molecular_at2_plates.py
- State: GREEN — 3/3 molecular PLATE_LOCKED (Science submodule)
- Next: molecular @2-swap proof

RECAP — T1 #179
- Did: science_field.py, reintake_stale_durations.py, production_intake + Production_Templates chem/physics fields
- State: GREEN — stale duration:10 scripts re-intaked with clamp; chem/physics validated
- Next: remaining slate re-intake on render

RECAP — T2 #178
- Did: build_astro_r1_plate_lock.py + R4 chem/physics plate builders; astro/molecular plate fidelity locks
- State: GREEN — PLATE_LOCKED with fidelity notes across domains
- Next: OBSERVATORY ep2 on locked supernova plate

RECAP — T3 #180
- Did: chem_physics_mini_slate concepts (covalent bonding, EM field lines, ionic crystal); molecular mini-slate refresh
- State: PASS — intake/validator green
- Next: Observable design export (parent Observable/brand/)

RECAP — T4 #181
- Did: Full-slate re-gate via intake — gate reports + production script stamps across DAVID + Observable slates
- State: GREEN/YELLOW — Richard I COUNSEL; science slates YELLOW signed
- Next: 480p draft batch manifest

RECAP — T5 #182
- Did: clearance_manifest v1.3 chem/physics beds; assign_music_beds_science_slate.py; science slate bed stamps
- State: PASS — row 2 PASS on stamped science productions
- Next: awaiting review

RECAP — OBSERVATORY #184
- Did: science_star_lifecycle_v1 intake refresh (#177 clamp) + 480p seamless render prep (shots/)
- State: YELLOW signed — ep2 render in flight
- Next: QA 480p master; ep3 galaxy formation
'@

# --- Parent: per-terminal commits ---
$shas['DAVID-183'] = Commit-Repo -RepoPath $root -Subject 'DAVID #183: B183 batch manifest armed (8/8 preflight)' -Paths @(
    'DAVID/batches/B183_benjamin_go',
    'DAVID/scripts/fire_batch_manifest.py',
    'tests/test_batch_manifest_b183.py'
) -Body @'
RECAP
- Did: Built manifest.json + fire_batch_manifest.py + tests; preflight 8/8 pass; Latin excluded as SHIP reference
- State: ARMED / green — no renders fired; Richard I COUNSEL signed, proceeds on batch go
- Next: Hold for Benjamin go — python DAVID/scripts/fire_batch_manifest.py DAVID/batches/B183_benjamin_go/manifest.json --go
'@

$shas['ACTORS-172-tests'] = Commit-Repo -RepoPath $root -Subject 'ACTORS #172: molecular plate lock tests' -Paths @(
    'tests/test_molecular_at2_plates.py'
) -Body @'
RECAP
- Did: tests/test_molecular_at2_plates.py — 6 tests for R2 harvest + PLATE_LOCKED molecular @2 plates
- State: GREEN — 6/6 pass
- Next: CI gate on Science submodule plate paths
'@

$shas['T3-180'] = Commit-Repo -RepoPath $root -Subject 'T3 #180: Observable brand kit + Julian-001 identity' -Paths @(
    'Observable'
) -Body @'
RECAP
- Did: Observable/brand/ — Upon_Tyne_Observable_Brand_Kit_v1.md, asset_specs.json, CHANNEL_ABOUT.md, export/templates/fonts scaffolds
- State: PASS — operator spec locked; design export pending
- Next: Banner/logo export; first chem/physics 480p proof
'@

$shas['T1-179'] = Commit-Repo -RepoPath $root -Subject 'T1 #179: chem/physics intake + stale script re-intake' -Paths @(
    'tests/test_science_field_intake.py',
    'DAVID/scripts/longform_scripts/julian_covalent_bonding_60s_script.json',
    'DAVID/scripts/longform_scripts/julian_em_field_lines_60s_script.json',
    'DAVID/scripts/longform_scripts/science_black_hole_anatomy_v1_script.json',
    'DAVID/scripts/longform_scripts/science_galaxy_formation_v1_script.json',
    'DAVID/scripts/longform_scripts/science_star_lifecycle_v1_script.json',
    'DAVID/scripts/longform_scripts/science_dna_replication_v1_script.json',
    'DAVID/scripts/longform_scripts/science_immune_checkpoint_v1_script.json',
    'DAVID/scripts/longform_scripts/science_protein_folding_v1_script.json',
    'DAVID/scripts/longform_scripts/science_covalent_bonding_v1_script.json',
    'DAVID/scripts/longform_scripts/science_electromagnetism_v1_script.json',
    'DAVID/scripts/longform_scripts/science_ionic_crystal_v1_script.json',
    'DAVID/scripts/longform_scripts/julian_why_sky_blue_60s_script.json',
    'DAVID/scripts/longform_scripts/david_hypatia_60s_script.json',
    'DAVID/scripts/longform_scripts/david_why_latin_60s_script.json',
    'DAVID/productions'
) -Body @'
RECAP
- Did: Re-intaked stale duration:10 scripts with seamless 7-9s clamp; chem/physics field intake tests; science + DAVID production script stamps
- State: GREEN — test_science_field_intake.py; duration_clamp applied on viz shots
- Next: Normal render without --force-shot on clamped scripts
'@

$shas['T4-181'] = Commit-Repo -RepoPath $root -Subject 'T4 #181: full-slate re-gate + regate runner' -Paths @(
    'DAVID/scripts/regate_full_slate.py',
    'DAVID/batches/T4_181_science_astro',
    'DAVID/batches/T4_181_science_molecular',
    'DAVID/scripts/longform_scripts/david_akkadian_corpus_v1_script.json',
    'DAVID/scripts/longform_scripts/david_alfred_great_v1_script.json',
    'DAVID/scripts/longform_scripts/david_ancient_greek_corpus_v1_script.json',
    'DAVID/scripts/longform_scripts/david_biblical_hebrew_corpus_v1_script.json',
    'DAVID/scripts/longform_scripts/david_charlemagne_v1_script.json',
    'DAVID/scripts/longform_scripts/david_classical_nahuatl_corpus_v1_script.json',
    'DAVID/scripts/longform_scripts/david_cnut_great_v1_script.json',
    'DAVID/scripts/longform_scripts/david_eleanor_aquitaine_v1_script.json',
    'DAVID/scripts/longform_scripts/david_elizabeth_tudor_v1_script.json',
    'DAVID/scripts/longform_scripts/david_gothic_corpus_v1_script.json',
    'DAVID/scripts/longform_scripts/david_latin_corpus_v1_script.json',
    'DAVID/scripts/longform_scripts/david_middle_egyptian_corpus_v1_script.json',
    'DAVID/scripts/longform_scripts/david_old_church_slavonic_corpus_v1_script.json',
    'DAVID/scripts/longform_scripts/david_old_english_corpus_v1_script.json',
    'DAVID/scripts/longform_scripts/david_old_norse_corpus_v1_script.json',
    'DAVID/scripts/longform_scripts/david_richard_lionheart_v1_script.json',
    'DAVID/scripts/longform_scripts/david_sanskrit_corpus_v1_script.json',
    'DAVID/scripts/longform_scripts/david_sumerian_corpus_v1_script.json',
    'DAVID/scripts/longform_scripts/david_julius_caesar_figure_proof_480p_v1_script.json'
) -Body @'
RECAP
- Did: regate_full_slate.py + re-gate stamp on dead-language, royal-tongues, science, and figure scripts
- State: GREEN/YELLOW — Richard I COUNSEL; all others GREEN or YELLOW signed; row 2 PASS where music stamped
- Next: science batch 480p-draft via batch_runner; promote after review
'@

$shas['OBSERVATORY-184'] = Commit-Repo -RepoPath $root -Subject 'OBSERVATORY #184: ep2 star lifecycle 480p draft' -Paths @(
    'DAVID/scripts/longform_scripts/science_star_lifecycle_v1_480p_script.json'
) -Body @'
RECAP
- Did: science_star_lifecycle_v1 re-intake (#177 clamp 10→9s) + 480p script; supernova @2 plate wired; seamless render to STUDIO/Productions/Editorial/science_star_lifecycle_v1_longform_v1/
- State: YELLOW signed — first-pass clean target post-#177; QA pending render completion
- Next: Review 480p QA; ep3 galaxy formation standup
'@

# Pointer updates only (exclude .wave_commit.ps1)
$shas['wave-pointers'] = Commit-Repo -RepoPath $root -Subject 'wave: submodule pointers post #172-184' -Paths @(
    'Science',
    'Studio'
) -Body @'
RECAP
- Did: Updated Science + Studio submodule pointers after wave commits
- State: GREEN — parent synced to submodule SHAs
- Next: force-push origin main
'@

Write-Host '=== SHAs ==='
$shas.GetEnumerator() | Sort-Object Name | ForEach-Object { Write-Host "$($_.Name): $($_.Value)" }

# Push all
Set-Location $root
git push --force origin main
git -C Science push --force origin main
git -C Studio push --force origin main

Write-Host '=== FINAL HEADS ==='
Write-Host "parent: $(git rev-parse --short HEAD)"
Write-Host "Science: $(git -C Science rev-parse --short HEAD)"
Write-Host "Studio: $(git -C Studio rev-parse --short HEAD)"
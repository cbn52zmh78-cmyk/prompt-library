"""Resume companion proof render with slower API pacing."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "DAVID" / "scripts"))
import render_longform  # noqa: E402

render_longform.API_PACE_S = 3.5

script = ROOT / "STUDIO" / "Productions" / "Companion" / "gfe_companion_sage_proof_v1_longform_v1" / "gfe_companion_sage_proof_v1_script.json"
shots_dir = ROOT / "DAVID" / "productions" / "gfe_companion_sage_proof_v1_longform_v1" / "shots"
partial = shots_dir / "host_performance_extend.mp4"
state = shots_dir / "extend_state.json"

# Drop incomplete extend (failed mid-chain) so render does not short-circuit on cached partial
if partial.exists() and not state.exists():
    partial.unlink()
    print("[resume] removed incomplete extend partial")

sys.argv = [
    "render_longform.py",
    str(script),
    "--seamless",
    "--match-color",
    "--cut-on-motion",
]
raise SystemExit(render_longform.main())
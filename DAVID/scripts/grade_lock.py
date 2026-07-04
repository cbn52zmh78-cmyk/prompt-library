"""grade_lock.py — Anchor-based color drift detection and correction.

The B05-B08 color grading problem: each block is independently generated,
and stochastic generation drifts from the look established in B01-B04.
Existing QA probes check individual block quality (magenta, grey balance)
but never compare to a reference. This module fixes that.

Pipeline:
  1. Measure B01 → store as anchor (FrameState)
  2. After each subsequent block renders, measure it
  3. Compare to anchor → compute per-channel deltas
  4. If any delta exceeds threshold → generate ffmpeg correction
  5. Apply correction → re-measure → confirm convergence

The correction is a simple per-channel colorbalance adjustment via ffmpeg,
derived from the delta between anchor and measured R/G/B means.
"""

from __future__ import annotations

import json
import logging
import math
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from frame_probe import (
    ColorState,
    FrameState,
    probe_color,
    probe_full_state,
    _ffmpeg_exe,
    _probe_duration,
)

log = logging.getLogger("grade_lock")

# ---------------------------------------------------------------------------
# Thresholds — calibrated to the Matilda B05-B08 drift pattern
# ---------------------------------------------------------------------------

# Per-channel mean delta (0-255) that triggers correction
COLOR_DELTA_THRESHOLD = 6.0

# Informational only (logged in ColorDelta; colorbalance cannot correct these alone)
LUMINANCE_DELTA_THRESHOLD = 8.0
COLOR_TEMP_THRESHOLD = 0.08

# Maximum correction magnitude (prevents over-correction)
MAX_CORRECTION = 0.25

# Convergence target after correction — must be below this
CONVERGENCE_THRESHOLD = 4.0

# Maximum correction attempts before giving up
MAX_CORRECTION_PASSES = 3


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ColorDelta:
    """Per-channel deltas between measured block and anchor."""
    r_delta: float = 0.0  # measured - anchor (positive = block is redder)
    g_delta: float = 0.0
    b_delta: float = 0.0
    luminance_delta: float = 0.0
    color_temp_delta: float = 0.0
    magenta_delta: float = 0.0
    max_channel_delta: float = 0.0
    needs_correction: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CorrectionResult:
    """Record of a correction attempt."""
    block_id: str = ""
    video_in: str = ""
    video_out: str = ""
    delta_before: ColorDelta | None = None
    delta_after: ColorDelta | None = None
    ffmpeg_filter: str = ""
    passes: int = 0
    converged: bool = False

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


@dataclass
class GradeLockReport:
    """Full report for a multi-block render session."""
    anchor_block: str = ""
    anchor_color: ColorState | None = None
    blocks_measured: int = 0
    blocks_corrected: int = 0
    blocks_converged: int = 0
    corrections: list[CorrectionResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def set_anchor(video: Path, block_id: str = "B01") -> FrameState:
    """Measure B01 (or any reference block) and return its full state.

    This state becomes the anchor for all subsequent comparisons.
    """
    log.info("Setting grade anchor from %s (%s)", video.name, block_id)
    state = probe_full_state(video, block_id=block_id)
    if state.color is None:
        raise ValueError(f"Could not extract color state from anchor {video}")
    log.info(
        "Anchor color: R=%.1f G=%.1f B=%.1f  lum=%.1f  temp=%.3f",
        state.color.r_mean, state.color.g_mean, state.color.b_mean,
        state.color.luminance_mean, state.color.color_temp_ratio,
    )
    return state


def compute_delta(anchor: ColorState, measured: ColorState) -> ColorDelta:
    """Compute per-channel delta between a measured block and the anchor."""
    r_d = measured.r_mean - anchor.r_mean
    g_d = measured.g_mean - anchor.g_mean
    b_d = measured.b_mean - anchor.b_mean
    lum_d = measured.luminance_mean - anchor.luminance_mean
    ct_d = measured.color_temp_ratio - anchor.color_temp_ratio
    mag_d = measured.magenta_fraction - anchor.magenta_fraction
    max_d = max(abs(r_d), abs(g_d), abs(b_d))

    # RGB means only — colorbalance midtones cannot fix luminance/CT alone.
    needs = max_d > COLOR_DELTA_THRESHOLD

    return ColorDelta(
        r_delta=r_d,
        g_delta=g_d,
        b_delta=b_d,
        luminance_delta=lum_d,
        color_temp_delta=ct_d,
        magenta_delta=mag_d,
        max_channel_delta=max_d,
        needs_correction=needs,
    )


def _delta_to_colorbalance(delta: ColorDelta) -> str:
    """Convert a ColorDelta to an ffmpeg colorbalance filter string.

    The colorbalance filter adjusts shadows/midtones/highlights per channel.
    Range is -1.0 to 1.0. We target midtones since that's where grading
    drift is most visible.

    Negative delta = block is deficient in that channel → add it (positive adj)
    Positive delta = block has excess → subtract it (negative adj)
    """
    # Scale: delta of 255 would need full -1.0 correction.
    # We use a conservative scale factor and clamp.
    scale = -1.0 / 128.0  # invert: positive delta → negative correction

    rs = max(-MAX_CORRECTION, min(MAX_CORRECTION, delta.r_delta * scale))
    gs = max(-MAX_CORRECTION, min(MAX_CORRECTION, delta.g_delta * scale))
    bs = max(-MAX_CORRECTION, min(MAX_CORRECTION, delta.b_delta * scale))

    # Skip if all adjustments are negligible
    if abs(rs) < 0.002 and abs(gs) < 0.002 and abs(bs) < 0.002:
        return ""

    return f"colorbalance=rm={rs:.4f}:gm={gs:.4f}:bm={bs:.4f}"


def correct_block(
    video: Path,
    anchor_color: ColorState,
    block_id: str = "",
    max_passes: int = MAX_CORRECTION_PASSES,
) -> CorrectionResult:
    """Measure a block, correct if drifted, verify convergence.

    Writes the corrected video alongside the original with a
    '_gradelocked' suffix. The original is preserved.

    Returns a CorrectionResult with before/after deltas.
    """
    result = CorrectionResult(block_id=block_id, video_in=str(video))

    # Measure current state
    measured = probe_color(video)
    delta = compute_delta(anchor_color, measured)
    result.delta_before = delta

    if not delta.needs_correction:
        log.info(
            "%s: within tolerance (max_delta=%.1f)",
            block_id, delta.max_channel_delta,
        )
        result.video_out = str(video)
        result.converged = True
        return result

    log.info(
        "%s: drift detected — R=%+.1f G=%+.1f B=%+.1f (max=%.1f)",
        block_id, delta.r_delta, delta.g_delta, delta.b_delta,
        delta.max_channel_delta,
    )

    current_video = video
    current_delta = delta

    for pass_num in range(1, max_passes + 1):
        filt = _delta_to_colorbalance(current_delta)
        if not filt:
            log.info("%s pass %d: correction too small, accepting", block_id, pass_num)
            result.video_out = str(current_video)
            if current_delta.max_channel_delta <= CONVERGENCE_THRESHOLD:
                result.converged = True
            break

        result.ffmpeg_filter = filt
        result.passes = pass_num

        # Output path
        suffix = f"_gradelocked_p{pass_num}"
        out_path = video.with_stem(video.stem + suffix)

        # Apply correction
        ff = _ffmpeg_exe()
        cmd = [
            ff, "-y",
            "-i", str(current_video),
            "-vf", filt,
            "-c:a", "copy",
            "-c:v", "libx264", "-crf", "18", "-preset", "medium",
            str(out_path),
        ]
        log.info("%s pass %d: applying %s", block_id, pass_num, filt)
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            log.error("%s pass %d ffmpeg error: %s", block_id, pass_num, proc.stderr[-500:])
            result.video_out = str(current_video)
            break

        # Re-measure
        corrected_color = probe_color(out_path)
        new_delta = compute_delta(anchor_color, corrected_color)
        result.delta_after = new_delta
        result.video_out = str(out_path)

        log.info(
            "%s pass %d result: R=%+.1f G=%+.1f B=%+.1f (max=%.1f)",
            block_id, pass_num, new_delta.r_delta, new_delta.g_delta,
            new_delta.b_delta, new_delta.max_channel_delta,
        )

        if new_delta.max_channel_delta <= CONVERGENCE_THRESHOLD:
            result.converged = True
            log.info("%s: converged after %d pass(es)", block_id, pass_num)

            # Clean up intermediate passes (keep only final)
            if pass_num > 1 and current_video != video:
                current_video.unlink(missing_ok=True)

            # Rename final to simple _gradelocked suffix
            final_path = video.with_stem(video.stem + "_gradelocked")
            if out_path != final_path:
                shutil.move(str(out_path), str(final_path))
                result.video_out = str(final_path)
            break

        # Prepare for next pass
        if current_video != video:
            current_video.unlink(missing_ok=True)
        current_video = out_path
        current_delta = new_delta

    if not result.converged:
        log.warning(
            "%s: did not converge after %d passes (max_delta=%.1f)",
            block_id, result.passes,
            result.delta_after.max_channel_delta if result.delta_after else -1,
        )

    if not result.video_out:
        result.video_out = str(video)

    return result


def grade_lock_pipeline(
    block_videos: list[tuple[str, Path]],
    anchor_index: int = 0,
) -> GradeLockReport:
    """Run the full grade-lock pipeline across a list of blocks.

    Args:
        block_videos: list of (block_id, video_path) tuples, in order
        anchor_index: which block to use as the reference (default: first)

    Returns:
        GradeLockReport with full correction history
    """
    if not block_videos:
        return GradeLockReport()

    anchor_id, anchor_path = block_videos[anchor_index]
    anchor_state = set_anchor(anchor_path, block_id=anchor_id)

    report = GradeLockReport(
        anchor_block=anchor_id,
        anchor_color=anchor_state.color,
    )

    for i, (bid, vpath) in enumerate(block_videos):
        if i == anchor_index:
            continue  # skip the anchor itself

        report.blocks_measured += 1
        result = correct_block(vpath, anchor_state.color, block_id=bid)
        report.corrections.append(result)

        if result.delta_before and result.delta_before.needs_correction:
            report.blocks_corrected += 1
        if result.converged:
            report.blocks_converged += 1

    log.info(
        "Grade lock complete: %d measured, %d corrected, %d converged",
        report.blocks_measured, report.blocks_corrected, report.blocks_converged,
    )
    return report


# ---------------------------------------------------------------------------
# Convenience: check a single block against an existing anchor state
# ---------------------------------------------------------------------------

def check_drift(video: Path, anchor_color: ColorState,
                block_id: str = "") -> ColorDelta:
    """Quick drift check — measure and compare, no correction."""
    measured = probe_color(video)
    return compute_delta(anchor_color, measured)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

    if len(sys.argv) < 3:
        print("Usage: python grade_lock.py <anchor.mp4> <block.mp4> [block.mp4 ...]")
        print("  First argument is the anchor (B01). Remaining are blocks to check/correct.")
        sys.exit(1)

    anchor_path = Path(sys.argv[1])
    block_paths = [(f"B{i+2:02d}", Path(p)) for i, p in enumerate(sys.argv[2:])]

    blocks = [("B01", anchor_path)] + block_paths
    report = grade_lock_pipeline(blocks)
    print(report.to_json())

"""frame_probe.py — Unified frame-state measurement for video blocks.

Extracts color state, person detection, pose estimation, and motion
from rendered video blocks. Designed to feed grade_lock.py for
anchor-based drift correction.

Dependencies (graceful degradation):
  Always:   PIL/Pillow, numpy, subprocess (ffmpeg)
  Optional: mediapipe   (pose estimation — 33 landmarks)
            ultralytics (YOLOv8 person/object detection)
            cv2         (optical flow, advanced color)

If an optional dep is missing, the corresponding probe returns None
and grade_lock skips that axis.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Optional imports — degrade gracefully
# ---------------------------------------------------------------------------
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    import mediapipe as mp
    HAS_MEDIAPIPE = True
except ImportError:
    HAS_MEDIAPIPE = False

try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False

# ---------------------------------------------------------------------------
# ffmpeg helper — same pattern as render_longform.py
# ---------------------------------------------------------------------------
_FFMPEG: str | None = None


def _ffmpeg_exe() -> str:
    global _FFMPEG
    if _FFMPEG:
        return _FFMPEG
    try:
        import imageio_ffmpeg
        _FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        _FFMPEG = "ffmpeg"
    return _FFMPEG


def _probe_duration(video: Path) -> float:
    """Get video duration in seconds via ffmpeg."""
    r = subprocess.run(
        [_ffmpeg_exe(), "-i", str(video)],
        capture_output=True, text=True,
    )
    for line in (r.stderr or "").splitlines():
        if "Duration:" in line:
            ts = line.split("Duration:")[1].split(",")[0].strip()
            parts = ts.split(":")
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    return 0.0


def _extract_frame(video: Path, at_s: float, out_path: Path) -> Path:
    """Extract a single frame from video at the given timestamp."""
    subprocess.run(
        [_ffmpeg_exe(), "-y", "-ss", f"{at_s:.3f}", "-i", str(video),
         "-frames:v", "1", str(out_path)],
        check=True, capture_output=True,
    )
    return out_path


def _extract_frames(video: Path, count: int = 5) -> list[Path]:
    """Extract evenly-spaced frames across the video. Returns temp file paths."""
    dur = _probe_duration(video)
    if dur <= 0:
        return []
    # Sample at 10%, 30%, 50%, 70%, 90% of duration
    positions = [dur * p for p in [0.10, 0.30, 0.50, 0.70, 0.90]][:count]
    paths = []
    for i, t in enumerate(positions):
        p = video.with_suffix(f".fp_frame_{i}.jpg")
        _extract_frame(video, t, p)
        paths.append(p)
    return paths


def _cleanup_frames(paths: list[Path]) -> None:
    for p in paths:
        p.unlink(missing_ok=True)


# ===================================================================
# Data structures
# ===================================================================

@dataclass
class ColorState:
    """Per-channel color measurements averaged across sampled frames."""
    r_mean: float = 0.0
    g_mean: float = 0.0
    b_mean: float = 0.0
    r_std: float = 0.0
    g_std: float = 0.0
    b_std: float = 0.0
    luminance_mean: float = 0.0
    saturation_mean: float = 0.0
    color_temp_ratio: float = 0.0  # warm/cool ratio: (R+G/2) / (B+G/2)
    magenta_fraction: float = 0.0
    yellow_green_fraction: float = 0.0


@dataclass
class PersonDetection:
    """Bounding box + position as fraction of frame."""
    bbox_x: float = 0.0  # left edge, 0-1
    bbox_y: float = 0.0  # top edge, 0-1
    bbox_w: float = 0.0  # width, 0-1
    bbox_h: float = 0.0  # height, 0-1
    center_x: float = 0.0
    center_y: float = 0.0
    confidence: float = 0.0
    frame_occupancy: float = 0.0  # bbox area / frame area


@dataclass
class PoseLandmark:
    """Single MediaPipe landmark — normalized coords + visibility."""
    name: str = ""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    visibility: float = 0.0


@dataclass
class PoseState:
    """Full 33-landmark pose for one detected person."""
    landmarks: list[PoseLandmark] = field(default_factory=list)
    # Derived spatial measurements
    head_position: tuple[float, float] = (0.0, 0.0)
    shoulder_width: float = 0.0
    torso_height: float = 0.0
    left_arm_angle: float = 0.0
    right_arm_angle: float = 0.0


@dataclass
class MotionState:
    """Optical flow summary between adjacent sampled frames."""
    mean_magnitude: float = 0.0
    max_magnitude: float = 0.0
    dominant_direction_deg: float = 0.0  # 0=right, 90=down, etc.
    motion_coverage: float = 0.0  # fraction of frame with significant motion


@dataclass
class FrameState:
    """Complete state vector for one video block."""
    block_id: str = ""
    video_path: str = ""
    duration_s: float = 0.0
    color: ColorState | None = None
    persons: list[PersonDetection] = field(default_factory=list)
    poses: list[PoseState] = field(default_factory=list)
    motion: MotionState | None = None
    # Capability flags — what was actually measured
    has_color: bool = False
    has_detection: bool = False
    has_pose: bool = False
    has_motion: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


# ===================================================================
# PROBE: Color state (always available — PIL + numpy only)
# ===================================================================

# MediaPipe landmark names for reference
_MP_LANDMARKS = [
    "nose", "left_eye_inner", "left_eye", "left_eye_outer",
    "right_eye_inner", "right_eye", "right_eye_outer",
    "left_ear", "right_ear", "mouth_left", "mouth_right",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_pinky", "right_pinky",
    "left_index", "right_index", "left_thumb", "right_thumb",
    "left_hip", "right_hip", "left_knee", "right_knee",
    "left_ankle", "right_ankle", "left_heel", "right_heel",
    "left_foot_index", "right_foot_index",
]


def probe_color(video: Path, sample_count: int = 5) -> ColorState:
    """Measure full color state across sampled frames.

    Returns per-channel means/std, luminance, saturation, color temperature
    ratio, and magenta/yellow-green fractions.
    """
    from PIL import Image

    frames = _extract_frames(video, sample_count)
    if not frames:
        return ColorState()

    all_r, all_g, all_b = [], [], []
    all_lum, all_sat = [], []
    magenta_total, yg_total, pixel_total = 0, 0, 0

    for fp in frames:
        if not fp.exists():
            continue
        img = Image.open(fp).convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w = arr.shape[:2]

        # Channel means for this frame
        r_ch = arr[:, :, 0]
        g_ch = arr[:, :, 1]
        b_ch = arr[:, :, 2]
        all_r.append(r_ch.mean())
        all_g.append(g_ch.mean())
        all_b.append(b_ch.mean())

        # Luminance: BT.601
        lum = 0.299 * r_ch + 0.587 * g_ch + 0.114 * b_ch
        all_lum.append(lum.mean())

        # Saturation: (max - min) / max per pixel, averaged
        mx = np.maximum(np.maximum(r_ch, g_ch), b_ch)
        mn = np.minimum(np.minimum(r_ch, g_ch), b_ch)
        sat = np.where(mx > 0, (mx - mn) / mx, 0.0)
        all_sat.append(sat.mean())

        # Magenta + yellow-green fractions (mid-tone pixels only)
        step = 4
        for y in range(0, h, step):
            for x in range(0, w, step):
                r, g, b = float(r_ch[y, x]), float(g_ch[y, x]), float(b_ch[y, x])
                px_lum = 0.299 * r + 0.587 * g + 0.114 * b
                if px_lum < 35 or px_lum > 215:
                    continue
                pixel_total += 1
                if b > r * 1.08 and b > g * 1.05:
                    magenta_total += 1
                elif (r + b) > g * 1.35 and b > g * 0.95:
                    magenta_total += 1
                if g > r * 1.06 and g > b * 1.04:
                    yg_total += 1

    _cleanup_frames(frames)

    r_arr = np.array(all_r)
    g_arr = np.array(all_g)
    b_arr = np.array(all_b)

    r_mean = float(r_arr.mean())
    g_mean = float(g_arr.mean())
    b_mean = float(b_arr.mean())

    # Color temperature ratio: warm channels vs cool
    warm = r_mean + g_mean / 2
    cool = b_mean + g_mean / 2
    ct_ratio = warm / cool if cool > 0 else 0.0

    return ColorState(
        r_mean=r_mean,
        g_mean=g_mean,
        b_mean=b_mean,
        r_std=float(r_arr.std()) if len(r_arr) > 1 else 0.0,
        g_std=float(g_arr.std()) if len(g_arr) > 1 else 0.0,
        b_std=float(b_arr.std()) if len(b_arr) > 1 else 0.0,
        luminance_mean=float(np.mean(all_lum)),
        saturation_mean=float(np.mean(all_sat)),
        color_temp_ratio=ct_ratio,
        magenta_fraction=magenta_total / pixel_total if pixel_total else 0.0,
        yellow_green_fraction=yg_total / pixel_total if pixel_total else 0.0,
    )


# ===================================================================
# PROBE: Person detection (requires ultralytics / YOLOv8)
# ===================================================================

_YOLO_MODEL = None


def _get_yolo_model():
    global _YOLO_MODEL
    if _YOLO_MODEL is None:
        _YOLO_MODEL = YOLO("yolov8n.pt")  # nano — fast, CPU-friendly
    return _YOLO_MODEL


def probe_persons(video: Path, sample_count: int = 5) -> list[PersonDetection] | None:
    """Detect persons in sampled frames via YOLOv8.

    Returns the median detection across frames (most representative).
    Returns None if ultralytics not installed.
    """
    if not HAS_YOLO:
        return None

    from PIL import Image

    frames = _extract_frames(video, sample_count)
    if not frames:
        return None

    model = _get_yolo_model()
    all_detections: list[list[PersonDetection]] = []

    for fp in frames:
        if not fp.exists():
            continue
        img = Image.open(fp).convert("RGB")
        w, h = img.size
        results = model(img, verbose=False, classes=[0])  # class 0 = person
        frame_dets = []
        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            bw = (x2 - x1) / w
            bh = (y2 - y1) / h
            frame_dets.append(PersonDetection(
                bbox_x=x1 / w,
                bbox_y=y1 / h,
                bbox_w=bw,
                bbox_h=bh,
                center_x=(x1 + x2) / 2 / w,
                center_y=(y1 + y2) / 2 / h,
                confidence=conf,
                frame_occupancy=bw * bh,
            ))
        all_detections.append(frame_dets)

    _cleanup_frames(frames)

    if not all_detections:
        return []

    # Return detections from the median frame (by person count)
    all_detections.sort(key=len)
    median_idx = len(all_detections) // 2
    return all_detections[median_idx]


# ===================================================================
# PROBE: Pose estimation (requires mediapipe)
# ===================================================================

def _angle_between(a: tuple[float, float], b: tuple[float, float],
                   c: tuple[float, float]) -> float:
    """Angle at point b formed by segments ba and bc, in degrees."""
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    dot = ba[0] * bc[0] + ba[1] * bc[1]
    mag_ba = math.sqrt(ba[0] ** 2 + ba[1] ** 2)
    mag_bc = math.sqrt(bc[0] ** 2 + bc[1] ** 2)
    if mag_ba * mag_bc == 0:
        return 0.0
    cos_angle = max(-1.0, min(1.0, dot / (mag_ba * mag_bc)))
    return math.degrees(math.acos(cos_angle))


def probe_pose(video: Path, sample_count: int = 3) -> list[PoseState] | None:
    """Estimate pose landmarks via MediaPipe Pose.

    Returns one PoseState per detected person (typically 1).
    Returns None if mediapipe not installed.
    """
    if not HAS_MEDIAPIPE:
        return None

    from PIL import Image

    frames = _extract_frames(video, sample_count)
    if not frames:
        return None

    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        static_image_mode=True,
        model_complexity=1,
        min_detection_confidence=0.5,
    )

    all_poses: list[PoseState] = []

    # Use the middle frame for the most representative pose
    mid = frames[len(frames) // 2]
    if mid.exists():
        img = Image.open(mid).convert("RGB")
        img_arr = np.array(img)
        results = pose.process(img_arr)

        if results.pose_landmarks:
            lms = results.pose_landmarks.landmark
            landmarks = []
            for i, lm in enumerate(lms):
                name = _MP_LANDMARKS[i] if i < len(_MP_LANDMARKS) else f"landmark_{i}"
                landmarks.append(PoseLandmark(
                    name=name,
                    x=lm.x, y=lm.y, z=lm.z,
                    visibility=lm.visibility,
                ))

            # Derived measurements
            def _lm(idx: int) -> tuple[float, float]:
                return (lms[idx].x, lms[idx].y)

            head_pos = _lm(0)  # nose
            l_shoulder = _lm(11)
            r_shoulder = _lm(12)
            l_elbow = _lm(13)
            r_elbow = _lm(14)
            l_wrist = _lm(15)
            r_wrist = _lm(16)
            l_hip = _lm(23)
            r_hip = _lm(24)

            shoulder_w = math.sqrt(
                (l_shoulder[0] - r_shoulder[0]) ** 2 +
                (l_shoulder[1] - r_shoulder[1]) ** 2
            )
            mid_shoulder_y = (l_shoulder[1] + r_shoulder[1]) / 2
            mid_hip_y = (l_hip[1] + r_hip[1]) / 2
            torso_h = abs(mid_hip_y - mid_shoulder_y)

            l_arm_angle = _angle_between(l_shoulder, l_elbow, l_wrist)
            r_arm_angle = _angle_between(r_shoulder, r_elbow, r_wrist)

            all_poses.append(PoseState(
                landmarks=landmarks,
                head_position=head_pos,
                shoulder_width=shoulder_w,
                torso_height=torso_h,
                left_arm_angle=l_arm_angle,
                right_arm_angle=r_arm_angle,
            ))

    pose.close()
    _cleanup_frames(frames)
    return all_poses if all_poses else None


# ===================================================================
# PROBE: Motion / optical flow (requires cv2)
# ===================================================================

def probe_motion(video: Path, sample_count: int = 5) -> MotionState | None:
    """Measure inter-frame motion via dense optical flow.

    Returns None if cv2 not installed.
    """
    if not HAS_CV2:
        return None

    frames = _extract_frames(video, sample_count)
    if len(frames) < 2:
        _cleanup_frames(frames)
        return None

    magnitudes = []
    directions = []
    coverages = []

    prev_gray = None
    for fp in frames:
        if not fp.exists():
            continue
        img = cv2.imread(str(fp))
        if img is None:
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        if prev_gray is not None:
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, gray,
                None,  # flow output
                pyr_scale=0.5, levels=3, winsize=15,
                iterations=3, poly_n=5, poly_sigma=1.2,
                flags=0,
            )
            mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])

            magnitudes.append(float(mag.mean()))
            # Dominant direction: circular mean of angles weighted by magnitude
            sin_sum = float(np.sum(mag * np.sin(ang)))
            cos_sum = float(np.sum(mag * np.cos(ang)))
            dominant = math.degrees(math.atan2(sin_sum, cos_sum)) % 360
            directions.append(dominant)

            # Coverage: fraction of pixels with motion above threshold
            threshold = 1.5  # pixels of motion
            moving_pixels = float(np.sum(mag > threshold))
            total_pixels = float(mag.size)
            coverages.append(moving_pixels / total_pixels if total_pixels else 0.0)

        prev_gray = gray

    _cleanup_frames(frames)

    if not magnitudes:
        return MotionState()

    return MotionState(
        mean_magnitude=float(np.mean(magnitudes)),
        max_magnitude=float(np.max(magnitudes)),
        dominant_direction_deg=float(np.mean(directions)),
        motion_coverage=float(np.mean(coverages)),
    )


# ===================================================================
# UNIFIED PROBE — full state vector for one block
# ===================================================================

def probe_full_state(video: Path, block_id: str = "",
                     sample_count: int = 5) -> FrameState:
    """Measure everything available for one video block.

    Returns a FrameState with capability flags indicating which
    axes were actually measured (depends on installed deps).
    """
    color = probe_color(video, sample_count)
    persons = probe_persons(video, sample_count)
    poses = probe_pose(video, min(sample_count, 3))
    motion = probe_motion(video, sample_count)

    return FrameState(
        block_id=block_id,
        video_path=str(video),
        duration_s=_probe_duration(video),
        color=color,
        persons=persons if persons else [],
        poses=poses if poses else [],
        motion=motion,
        has_color=True,
        has_detection=persons is not None,
        has_pose=poses is not None,
        has_motion=motion is not None,
    )


# ===================================================================
# CLI — standalone test
# ===================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python frame_probe.py <video.mp4> [block_id]")
        sys.exit(1)

    video_path = Path(sys.argv[1])
    bid = sys.argv[2] if len(sys.argv) > 2 else video_path.stem

    print(f"Probing {video_path} as block {bid}...")
    print(f"  cv2: {HAS_CV2}  mediapipe: {HAS_MEDIAPIPE}  yolo: {HAS_YOLO}")

    state = probe_full_state(video_path, block_id=bid)
    print(state.to_json())

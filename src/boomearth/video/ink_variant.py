"""PIL ink variant derivation: color PNG to white-background ink PNG (Phase 1, PIL only).

Algorithm reference: cs-board (ChenShuo2004, MIT) adaptive-threshold stage.
Independently implemented in BoomEarth, no code copied.
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path


# Derivation parameter version (changing this constant updates sha256 version)
INK_PARAMS: dict[str, object] = {
    "contrast_factor": 1.0,
    "threshold": 125,
    "schema": "ink-v1",
}


def derive_ink_variant(png_bytes: bytes) -> bytes:
    """
    Derive white-background ink-line PNG bytes from color PNG bytes.

    Algorithm:
    1. Convert to grayscale (L mode)
    2. Boost contrast with ImageEnhance.Contrast to emphasize edges
    3. Threshold binarize (point): below threshold -> 0 (dark), above -> 255 (white)
    4. Convert back to RGB, encode as PNG bytes and return

    Determinism guarantee: same input bytes -> same output bytes (stable sha256).
    """
    from PIL import Image, ImageEnhance  # noqa: PLC0415

    img = Image.open(io.BytesIO(png_bytes)).convert("L")
    enhancer = ImageEnhance.Contrast(img)
    enhanced = enhancer.enhance(float(INK_PARAMS["contrast_factor"]))
    threshold = int(INK_PARAMS["threshold"])
    bw = enhanced.point(lambda px: 0 if px < threshold else 255, "L")
    rgb = bw.convert("RGB")
    buf = io.BytesIO()
    rgb.save(buf, format="PNG", optimize=False)
    return buf.getvalue()


def derive_ink_variant_for_project(
    *,
    project_root: Path,
    theme_id: str,
) -> dict[str, object]:
    """
    Batch-derive ink variants for all finalized color illustrations in the project.
    Writes to project_root/eng/ink-variants/<theme_id>/.

    Returns receipt dict: {scene_id: {"src_sha256": ..., "ink_sha256": ..., "params": ..., "status": ...}}
    Uses no-clobber write: skips scenes where existing ink matches sha256 (status=reused).
    Raises ValueError (ink-variant-clobber) when sha256 mismatch detected.
    """
    from boomearth.video.artifacts import capture_regular_file, publish_bytes_no_clobber  # noqa: PLC0415

    root = Path(project_root)
    src_dir = root / "\u5de5\u7a0b" / "assets" / "profiled-illustrations" / theme_id
    ink_dir = root / "\u5de5\u7a0b" / "ink-variants" / theme_id
    ink_dir.mkdir(parents=True, exist_ok=True)

    receipts: dict[str, object] = {}
    for src_path in sorted(src_dir.glob("*.png")):
        scene_id = src_path.stem
        ink_name = f"{scene_id}-ink.png"
        ink_path = ink_dir / ink_name

        src_snap = capture_regular_file(src_path, within=root)
        ink_bytes = derive_ink_variant(src_snap.payload)
        ink_sha256 = hashlib.sha256(ink_bytes).hexdigest()

        if ink_path.exists():
            existing_sha256 = hashlib.sha256(ink_path.read_bytes()).hexdigest()
            if existing_sha256 == ink_sha256:
                receipts[scene_id] = {
                    "src_sha256": src_snap.sha256,
                    "ink_sha256": ink_sha256,
                    "params": INK_PARAMS,
                    "status": "reused",
                }
                continue
            raise ValueError(f"ink-variant-clobber: {ink_path}")

        publish_bytes_no_clobber(ink_path, ink_bytes, within=root)
        receipts[scene_id] = {
            "src_sha256": src_snap.sha256,
            "ink_sha256": ink_sha256,
            "params": INK_PARAMS,
            "status": "derived",
        }
    return receipts


__all__ = ["INK_PARAMS", "derive_ink_variant", "derive_ink_variant_for_project"]
from __future__ import annotations

import hashlib
import io
from pathlib import Path
from PIL import Image
import pytest

from boomearth.video.ink_variant import (
    INK_PARAMS,
    derive_ink_variant,
    derive_ink_variant_for_project,
)


def _make_test_png() -> bytes:
    img = Image.new("RGB", (20, 20), color=(255, 255, 255))
    # Draw some dark pixels
    for x in range(5, 15):
        img.putpixel((x, 10), (0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_derive_ink_variant_determinism() -> None:
    sample = _make_test_png()
    res1 = derive_ink_variant(sample)
    res2 = derive_ink_variant(sample)
    assert res1 == res2
    assert hashlib.sha256(res1).hexdigest() == hashlib.sha256(res2).hexdigest()


def test_derive_ink_variant_format_and_properties() -> None:
    sample = _make_test_png()
    result = derive_ink_variant(sample)
    assert result.startswith(b"\x89PNG")

    img = Image.open(io.BytesIO(result))
    assert img.mode == "RGB"
    assert img.getpixel((0, 0)) == (255, 255, 255)
    assert img.getpixel((10, 10)) == (0, 0, 0)


def test_derive_ink_variant_for_project_flow(tmp_path: Path) -> None:
    theme_id = "sponge-host-handdrawn-v1"
    src_dir = tmp_path / "工程" / "assets" / "profiled-illustrations" / theme_id
    src_dir.mkdir(parents=True, exist_ok=True)
    sample = _make_test_png()
    (src_dir / "scene-01.png").write_bytes(sample)

    receipts = derive_ink_variant_for_project(project_root=tmp_path, theme_id=theme_id)
    assert "scene-01" in receipts
    info = receipts["scene-01"]
    assert info["status"] == "derived"
    assert info["src_sha256"] == hashlib.sha256(sample).hexdigest()
    assert "ink_sha256" in info
    assert info["params"] == INK_PARAMS

    ink_file = tmp_path / "工程" / "ink-variants" / theme_id / "scene-01-ink.png"
    assert ink_file.is_file()
    assert hashlib.sha256(ink_file.read_bytes()).hexdigest() == info["ink_sha256"]

    # Repeated call: no-clobber and reused
    receipts2 = derive_ink_variant_for_project(project_root=tmp_path, theme_id=theme_id)
    assert receipts2["scene-01"]["status"] == "reused"

    # Mismatch check: tamper with the ink file
    ink_file.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="ink-variant-clobber"):
        derive_ink_variant_for_project(project_root=tmp_path, theme_id=theme_id)

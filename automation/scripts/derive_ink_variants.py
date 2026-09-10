"""CLI: derive ink-variant PNGs for an ink-color-reveal project.

Usage:
    uv run python automation/scripts/derive_ink_variants.py <project_root>

Outputs:
    project_root/\u5de5\u7a0b/ink-variants/<theme_id>/<scene_id>-ink.png
    project_root/\u5de5\u7a0b/ink-variants.json  (derivation receipt)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: derive_ink_variants.py <project_root>", file=sys.stderr)
        return 2

    project_root = Path(sys.argv[1]).absolute()
    if not project_root.is_dir():
        print(f"error: not a directory: {project_root}", file=sys.stderr)
        return 1

    # Load content plan to find theme_id and confirm visual_effect
    try:
        from boomearth.video.content_plan import load_content_plan_snapshot
        from boomearth.video.illustration_themes import PROFILED_VISUAL_SYSTEM
        from boomearth.video.ink_variant import derive_ink_variant_for_project
    except ImportError as exc:
        print(f"error: import failed: {exc}", file=sys.stderr)
        return 1

    try:
        plan_snapshot = load_content_plan_snapshot(project_root=project_root)
    except Exception as exc:  # noqa: BLE001
        print(f"error: failed to load content plan: {exc}", file=sys.stderr)
        return 1

    plan = plan_snapshot.plan
    if plan.visual_system != PROFILED_VISUAL_SYSTEM:
        print("error: project is not profiled-illustration-v4; ink derivation not applicable", file=sys.stderr)
        return 1

    if getattr(plan, "visual_effect", None) != "ink-color-reveal":
        print("error: content plan does not declare visual_effect=ink-color-reveal", file=sys.stderr)
        return 1

    theme_id = plan.visual_theme
    if theme_id is None:
        print("error: visual_theme is not set in content plan", file=sys.stderr)
        return 1

    print(f"Deriving ink variants for theme: {theme_id}")
    try:
        receipts = derive_ink_variant_for_project(project_root=project_root, theme_id=theme_id)
    except Exception as exc:  # noqa: BLE001
        print(f"error: derivation failed: {exc}", file=sys.stderr)
        return 1

    receipt_path = project_root / "\u5de5\u7a0b" / "ink-variants.json"
    receipt_path.write_text(
        json.dumps(receipts, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    derived = sum(1 for v in receipts.values() if isinstance(v, dict) and v.get("status") == "derived")
    reused = sum(1 for v in receipts.values() if isinstance(v, dict) and v.get("status") == "reused")
    print(f"Done: {derived} derived, {reused} reused. Receipt: {receipt_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
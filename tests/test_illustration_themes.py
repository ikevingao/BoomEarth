from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

import boomearth.video.illustration_themes as illustration_themes
from boomearth.video.illustration_themes import (
    CHINESE_STYLE_CATALOG,
    PROFILED_VISUAL_SYSTEM,
    THEMES,
    IllustrationThemeError,
    get_theme,
)


EXPECTED_CORE_13_THEMES = {
    "sponge-host-handdrawn-v1",
    "minimal-whiteboard",
    "business-doodle",
    "warm-pencil",
    "guofeng-flat",
    "viral-pop",
    "black-gold-tech",
    "healing-journal",
    "retro-collage",
    "paper-metaphor",
    "oil-visual",
    "clay-3d",
    "cyber-neon",
}

EXPECTED_LEGACY_THEMES = {
    "vivid-comic-explainer",
    "engineering-sketch-explainer",
    "four-panel-comic-explainer",
    "blue-black-whiteboard-explainer",
    "xiaohuang-warm-first-v1",
}


def test_profiled_theme_registry_contains_13_core_templates_and_legacy() -> None:
    assert PROFILED_VISUAL_SYSTEM == "profiled-illustration-v4"
    assert EXPECTED_CORE_13_THEMES.issubset(set(THEMES))
    assert EXPECTED_LEGACY_THEMES.issubset(set(THEMES))
    assert all(theme.directory == theme.id for theme in THEMES.values())

    # 验证 13 款推荐模板的中文名称完整性
    core_chinese_names = {
        THEMES[tid].chinese_name for tid in EXPECTED_CORE_13_THEMES
    }
    assert core_chinese_names == {
        "方块海绵插画",
        "极简粗线简笔白板风",
        "极简商务涂鸦风",
        "暖米黄素描白板风",
        "粗线扁平国风卡通",
        "爆款高热吸睛风",
        "黑金科技发布会风",
        "清新治愈手账风",
        "复古报纸拼贴风",
        "纸感隐喻拼贴风",
        "漫画墨线解释风",
        "3D黏土趣味风",
        "赛博霓虹漫画风",
    }

    # 验证 13 款模板均包含画面特征、推荐内容和预览图引用
    for tid in EXPECTED_CORE_13_THEMES:
        theme = THEMES[tid]
        assert theme.features is not None and len(theme.features) > 0
        assert theme.recommended is not None and len(theme.recommended) > 0
        assert theme.preview_image is not None and len(theme.preview_image) > 0

    with pytest.raises(TypeError):
        THEMES["another"] = THEMES["sponge-host-handdrawn-v1"]  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        THEMES["sponge-host-handdrawn-v1"].directory = "changed"  # type: ignore[misc]


def test_chinese_style_catalog_includes_13_core_themes() -> None:
    catalog_targets = [entry.target for entry in CHINESE_STYLE_CATALOG]
    assert catalog_targets[:4] == [
        "xiaohei-white-first-v1",
        "editorial-motion-v2",
        "semantic-handdrawn-v3",
        "semantic-handdrawn-v3/type-led",
    ]
    # 后面 13 项为核心模板
    assert catalog_targets[4:] == [
        "sponge-host-handdrawn-v1",
        "minimal-whiteboard",
        "business-doodle",
        "warm-pencil",
        "guofeng-flat",
        "viral-pop",
        "black-gold-tech",
        "healing-journal",
        "retro-collage",
        "paper-metaphor",
        "oil-visual",
        "clay-3d",
        "cyber-neon",
    ]
    assert len(CHINESE_STYLE_CATALOG) == 17
    assert all(entry.invocation.endswith("。") for entry in CHINESE_STYLE_CATALOG)


def test_get_theme_fails_closed_for_unknown_or_non_string_ids() -> None:
    assert get_theme("sponge-host-handdrawn-v1") is THEMES["sponge-host-handdrawn-v1"]
    assert get_theme("minimal-whiteboard") is THEMES["minimal-whiteboard"]
    for value in ("unknown", "", None, 4):
        with pytest.raises(
            IllustrationThemeError, match="^illustration-theme-invalid$"
        ):
            get_theme(value)  # type: ignore[arg-type]


def test_default_request_resolves_to_sponge_contract() -> None:
    assert illustration_themes.resolve_visual_style(
        "default"
    ) == illustration_themes.ResolvedVisualStyle(
        target="sponge-host-handdrawn-v1",
        schema_version=4,
        visual_system="profiled-illustration-v4",
        visual_theme="sponge-host-handdrawn-v1",
        illustration_skill="ra-video-illustrations",
    )
    assert illustration_themes.DEFAULT_VISUAL_TARGET == "sponge-host-handdrawn-v1"


def test_core_13_themes_resolve_to_registered_profiled_theme() -> None:
    for theme_id in EXPECTED_CORE_13_THEMES:
        resolved = illustration_themes.resolve_visual_style(theme_id)
        assert resolved.target == theme_id
        assert resolved.schema_version == 4
        assert resolved.visual_system == "profiled-illustration-v4"
        assert resolved.visual_theme == theme_id
        assert resolved.illustration_skill == "ra-video-illustrations"


def test_legacy_xiaohuang_request_resolves_for_backward_compatibility() -> None:
    assert illustration_themes.resolve_visual_style(
        "xiaohuang-warm-first-v1"
    ) == illustration_themes.ResolvedVisualStyle(
        target="xiaohuang-warm-first-v1",
        schema_version=4,
        visual_system="profiled-illustration-v4",
        visual_theme="xiaohuang-warm-first-v1",
        illustration_skill="ra-video-illustrations",
    )


def test_default_request_never_resolves_to_type_led() -> None:
    assert (
        illustration_themes.resolve_visual_style("semantic-handdrawn-v3/type-led").target
        == illustration_themes.TYPE_LED_TARGET
    )
    assert (
        illustration_themes.resolve_visual_style("default").target
        != illustration_themes.TYPE_LED_TARGET
    )


@pytest.mark.parametrize("requested", [None, "", "cinematic-food", "类似漫画"])
def test_unregistered_or_missing_visual_request_fails_closed(requested: object) -> None:
    with pytest.raises(
        IllustrationThemeError, match="^illustration-style-invalid$"
    ):
        illustration_themes.resolve_visual_style(requested)

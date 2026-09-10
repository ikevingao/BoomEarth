"""Frozen profiled illustration themes and user-facing Chinese catalog."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Mapping


PROFILED_VISUAL_SYSTEM: Final[str] = "profiled-illustration-v4"
DEFAULT_VISUAL_TARGET: Final[str] = "sponge-host-handdrawn-v1"
TYPE_LED_TARGET: Final[str] = "semantic-handdrawn-v3/type-led"

# ink-color-reveal 可选效果注册表（Phase 1：仅 sponge 主题开放）
VISUAL_EFFECTS: Final[frozenset[str]] = frozenset({"ink-color-reveal"})
EFFECT_THEME_WHITELIST: Final[Mapping[str, frozenset[str]]] = MappingProxyType(
    {"ink-color-reveal": frozenset({"sponge-host-handdrawn-v1"})}
)


class IllustrationThemeError(ValueError):
    """A fixed-message illustration theme lookup failure."""


@dataclass(frozen=True, slots=True)
class ChineseStyleEntry:
    chinese_name: str
    invocation: str
    target: str


@dataclass(frozen=True, slots=True)
class IllustrationTheme:
    id: str
    chinese_name: str
    invocation: str
    directory: str
    prompt_style: str
    required_qc: frozenset[str]
    preview_image: str | None = None
    features: str | None = None
    recommended: str | None = None


@dataclass(frozen=True, slots=True)
class ResolvedVisualStyle:
    target: str
    schema_version: int
    visual_system: str
    visual_theme: str | None
    illustration_skill: str
    # 可选效果标识符，None 表示使用主题默认效果；V5 时填充
    visual_effect: str | None = None


# 13 款核心视觉模板（海绵插画 + cs-board 12 款精选风格）
_THEME_VALUES = (
    IllustrationTheme(
        id="sponge-host-handdrawn-v1",
        chinese_name="方块海绵插画",
        invocation="这条视频使用方块海绵插画风格。",
        directory="sponge-host-handdrawn-v1",
        prompt_style="white-hand-drawn-sponge-host-with-native-chinese-labels",
        required_qc=frozenset(
            {
                "sponge_identity_consistent",
                "character_performs_action",
                "native_labels_correct",
                "white_canvas",
                "not_system_label_overlay",
            }
        ),
        preview_image="sponge-host.png",
        features="粗黑线白底、方块海绵角色、语义动作、原生手写标签、清爽留白",
        recommended="BoomEarth 默认设定、AI 教程、产品讲解、知识解说",
    ),
    IllustrationTheme(
        id="minimal-whiteboard",
        chinese_name="极简粗线简笔白板风",
        invocation="这条视频使用极简粗线简笔白板风，以粗黑线、少量配色和清爽留白进行图解。",
        directory="minimal-whiteboard",
        prompt_style="minimalist-thick-line-whiteboard-sketch-with-clean-accents",
        required_qc=frozenset(
            {
                "thick_black_lines",
                "clean_white_canvas",
                "minimal_color_accents",
                "concept_clear",
                "not_decorative_cartoon",
            }
        ),
        preview_image="minimal-whiteboard.webp",
        features="粗黑线、少量配色、清爽留白",
        recommended="知识讲解、个人表达、复盘总结",
    ),
    IllustrationTheme(
        id="business-doodle",
        chinese_name="极简商务涂鸦风",
        invocation="这条视频使用极简商务涂鸦风，用几何图表与蓝绿配色做专业克制的视觉呈现。",
        directory="business-doodle",
        prompt_style="business-doodle-infographic-with-blue-green-geometry",
        required_qc=frozenset(
            {
                "geometric_charts",
                "blue_green_palette",
                "professional_restraint",
                "structure_clear",
                "not_cluttered",
            }
        ),
        preview_image="business-doodle.webp",
        features="几何图表、蓝绿配色、专业克制",
        recommended="产品介绍、商业分析、项目汇报",
    ),
    IllustrationTheme(
        id="warm-pencil",
        chinese_name="暖米黄素描白板风",
        invocation="这条视频使用暖米黄素描白板风，通过铅笔排线与米黄纸张质感呈现温暖细腻的图景。",
        directory="warm-pencil",
        prompt_style="warm-pencil-sketch-on-textured-paper",
        required_qc=frozenset(
            {
                "pencil_hatching",
                "paper_texture",
                "warm_tone",
                "delicate_expression",
                "not_flat_vector",
            }
        ),
        preview_image="warm-pencil.webp",
        features="铅笔排线、纸张质感、温暖细腻",
        recommended="人物故事、个人成长、品牌叙事",
    ),
    IllustrationTheme(
        id="guofeng-flat",
        chinese_name="粗线扁平国风卡通",
        invocation="这条视频使用粗线扁平国风卡通风格，融合朱红玉绿、国风纹样与生动平涂。",
        directory="guofeng-flat",
        prompt_style="traditional-chinese-guofeng-flat-illustration-with-vermilion-and-jade",
        required_qc=frozenset(
            {
                "guofeng_palette",
                "traditional_motifs",
                "flat_linework",
                "cultural_relevance",
                "not_western_cartoon",
            }
        ),
        preview_image="guofeng-flat.webp",
        features="朱红玉绿、国风纹样、生动平涂",
        recommended="传统文化、国风品牌、中文创意",
    ),
    IllustrationTheme(
        id="viral-pop",
        chinese_name="爆款高热吸睛风",
        invocation="这条视频使用爆款高热吸睛风，以高饱和、强对比与夸张动势抓住眼球。",
        directory="viral-pop",
        prompt_style="viral-pop-high-contrast-dynamic-poster-style",
        required_qc=frozenset(
            {
                "high_saturation",
                "strong_contrast",
                "exaggerated_motion",
                "hook_impact",
                "not_dull",
            }
        ),
        preview_image="viral-pop.webp",
        features="高饱和、强对比、夸张动势",
        recommended="短视频开场、强观点、热点表达",
    ),
    IllustrationTheme(
        id="black-gold-tech",
        chinese_name="黑金科技发布会风",
        invocation="这条视频使用黑金科技发布会风，以黑金光效、科技舞台与高级权威感展示内容。",
        directory="black-gold-tech",
        prompt_style="premium-black-gold-lighting-keynote-stage-visual",
        required_qc=frozenset(
            {
                "black_gold_lighting",
                "tech_stage_ambiance",
                "authoritative_composition",
                "lighting_not_muddy",
            }
        ),
        preview_image="black-gold-tech.webp",
        features="黑金光效、科技舞台、高级权威",
        recommended="AI、科技产品、发布会",
    ),
    IllustrationTheme(
        id="healing-journal",
        chinese_name="清新治愈手账风",
        invocation="这条视频使用清新治愈手账风，用柔和水彩、低饱和配色与生活手账感传递温度。",
        directory="healing-journal",
        prompt_style="healing-journal-watercolor-with-soft-muted-tones",
        required_qc=frozenset(
            {
                "soft_watercolor",
                "low_saturation",
                "journal_aesthetic",
                "gentle_composition",
            }
        ),
        preview_image="healing-journal.webp",
        features="柔和水彩、低饱和配色、生活手账感",
        recommended="情感、生活方式、自我成长",
    ),
    IllustrationTheme(
        id="retro-collage",
        chinese_name="复古报纸拼贴风",
        invocation="这条视频使用复古报纸拼贴风，通过撕纸拼贴、半色调与编辑杂志感做深度呈现。",
        directory="retro-collage",
        prompt_style="retro-newspaper-halftone-magazine-paper-collage",
        required_qc=frozenset(
            {
                "torn_paper_collage",
                "halftone_texture",
                "editorial_layout",
                "vintage_depth",
            }
        ),
        preview_image="retro-collage.webp",
        features="撕纸拼贴、半色调、编辑杂志感",
        recommended="深度观点、文化内容、案例复盘",
    ),
    IllustrationTheme(
        id="paper-metaphor",
        chinese_name="纸感隐喻拼贴风",
        invocation="这条视频使用纸感隐喻拼贴风，用手工剪纸与观点隐喻呈现高级克制的视觉。",
        directory="paper-metaphor",
        prompt_style="paper-craft-cutout-metaphor-with-restrained-composition",
        required_qc=frozenset(
            {
                "paper_cutout_layers",
                "conceptual_metaphor",
                "elegant_restraint",
                "clear_symbolism",
            }
        ),
        preview_image="paper-metaphor.png",
        features="手工剪纸、观点隐喻、高级克制",
        recommended="价值观、关系、流程、复杂观点",
    ),
    IllustrationTheme(
        id="oil-visual",
        chinese_name="漫画墨线解释风",
        invocation="这条视频使用漫画墨线解释风，以漫画墨线、半调网点和概念机制清晰拆解原理。",
        directory="oil-visual",
        prompt_style="comic-ink-linework-with-halftone-dots-mechanic-explainer",
        required_qc=frozenset(
            {
                "ink_linework",
                "halftone_dots",
                "mechanism_explained",
                "dynamic_comic_composition",
            }
        ),
        preview_image="oil-visual.png",
        features="漫画墨线、半调网点、概念机制",
        recommended="原理讲解、机制拆解、商业洞察",
    ),
    IllustrationTheme(
        id="clay-3d",
        chinese_name="3D黏土趣味风",
        invocation="这条视频使用3D黏土趣味风，以黏土材质、玩具比例和温暖可爱的质感呈现。",
        directory="clay-3d",
        prompt_style="clay-3d-stop-motion-toy-proportions-warm-lighting",
        required_qc=frozenset(
            {
                "clay_texture",
                "playful_proportions",
                "warm_lighting",
                "charming_characters",
            }
        ),
        preview_image="clay-3d.webp",
        features="黏土材质、玩具比例、温暖可爱",
        recommended="亲子教育、轻量品牌、趣味科普",
    ),
    IllustrationTheme(
        id="cyber-neon",
        chinese_name="赛博霓虹漫画风",
        invocation="这条视频使用赛博霓虹漫画风，以霓虹青紫、漫画速度线和未来感突出科技张力。",
        directory="cyber-neon",
        prompt_style="cyberpunk-neon-cyan-purple-speedlines-future-comic",
        required_qc=frozenset(
            {
                "neon_cyan_purple",
                "comic_speedlines",
                "futuristic_vibe",
                "high_energy",
            }
        ),
        preview_image="cyber-neon.webp",
        features="霓虹青紫、漫画速度线、未来感",
        recommended="AI 趋势、数码科技、年轻化观点",
    ),
)

# 历史向后兼容保留主题（确保已有项目配置与特定历史测试可继续正常查询）
_LEGACY_THEMES = (
    IllustrationTheme(
        id="vivid-comic-explainer",
        chinese_name="鲜彩漫画讲解",
        invocation=(
            "这条视频使用鲜彩漫画讲解风格，用人物、动作、表情和鲜明强调色解释文案。"
        ),
        directory="vivid-comic-explainer",
        prompt_style="clean-black-comic-linework-with-controlled-vivid-accents",
        required_qc=frozenset(
            {
                "character_consistent",
                "expression_supports_claim",
                "action_explains_claim",
                "accent_palette_controlled",
                "not_decorative_cartoon",
            }
        ),
    ),
    IllustrationTheme(
        id="engineering-sketch-explainer",
        chinese_name="工程手稿图解",
        invocation=(
            "这条视频使用工程手稿图解风格，只画文案真实涉及的产品、结构和流程。"
        ),
        directory="engineering-sketch-explainer",
        prompt_style="precise-dark-gray-engineering-linework-with-pale-wash-accents",
        required_qc=frozenset(
            {
                "engineering_subject_real",
                "callouts_support_claim",
                "mechanical_exception_valid",
                "linework_clean",
                "diagram_not_overloaded",
            }
        ),
    ),
    IllustrationTheme(
        id="four-panel-comic-explainer",
        chinese_name="四格连环漫画",
        invocation=(
            "这条视频使用四格连环漫画风格，每个场景用四个连续画格讲清变化。"
        ),
        directory="four-panel-comic-explainer",
        prompt_style="fixed-two-by-two-causal-comic-with-consistent-characters",
        required_qc=frozenset(
            {
                "exactly_four_panels",
                "reading_order_clear",
                "beats_continuous",
                "character_consistent",
                "one_event_per_panel",
                "lower_panels_caption_safe",
            }
        ),
    ),
    IllustrationTheme(
        id="blue-black-whiteboard-explainer",
        chinese_name="蓝黑白板讲解",
        invocation=(
            "这条视频使用蓝黑白板讲解风格，用马克笔线条、框线和箭头解释关系。"
        ),
        directory="blue-black-whiteboard-explainer",
        prompt_style="whiteboard-marker-structure-with-black-lines-and-blue-emphasis",
        required_qc=frozenset(
            {
                "marker_material_clear",
                "blue_black_palette_only",
                "structure_type_clear",
                "reading_path_clear",
                "not_ppt_page",
                "not_character_led",
            }
        ),
    ),
    IllustrationTheme(
        id="xiaohuang-warm-first-v1",
        chinese_name="小黄温度插画",
        invocation=(
            "这条视频使用小黄温度插画风格，让固定暖黄色角色用动作和原生手写中文解释文案。"
        ),
        directory="xiaohuang-warm-first-v1",
        prompt_style=(
            "warm-white-hand-drawn-xiaohuang-character-with-native-chinese-labels"
        ),
        required_qc=frozenset(
            {
                "xiaohuang_identity_consistent",
                "character_performs_action",
                "native_labels_correct",
                "warm_white_canvas",
                "not_system_label_overlay",
            }
        ),
    ),
)

THEMES: Mapping[str, IllustrationTheme] = MappingProxyType(
    {theme.id: theme for theme in (*_THEME_VALUES, *_LEGACY_THEMES)}
)

CHINESE_STYLE_CATALOG: Final[tuple[ChineseStyleEntry, ...]] = (
    ChineseStyleEntry(
        "小黑怪诞插画",
        "这条视频使用小黑怪诞插画风格。",
        "xiaohei-white-first-v1",
    ),
    ChineseStyleEntry(
        "编辑动效插画",
        "这条视频使用编辑动效插画风格。",
        "editorial-motion-v2",
    ),
    ChineseStyleEntry(
        "语义手绘插画",
        "这条视频使用语义手绘插画风格。",
        "semantic-handdrawn-v3",
    ),
    ChineseStyleEntry(
        "动态文字卡片",
        "这条视频使用动态文字卡片风格，画面以文字关系、路径和轻量图标为主。",
        "semantic-handdrawn-v3/type-led",
    ),
    *(
        ChineseStyleEntry(theme.chinese_name, theme.invocation, theme.id)
        for theme in _THEME_VALUES
    ),
)


def get_theme(theme_id: str) -> IllustrationTheme:
    if not isinstance(theme_id, str):
        raise IllustrationThemeError("illustration-theme-invalid")
    try:
        return THEMES[theme_id]
    except KeyError:
        raise IllustrationThemeError("illustration-theme-invalid") from None


def resolve_visual_style(requested: object) -> ResolvedVisualStyle:
    """Resolve one exact registered visual target for new production."""

    target = DEFAULT_VISUAL_TARGET if requested == "default" else requested
    if not isinstance(target, str):
        raise IllustrationThemeError("illustration-style-invalid")

    # V5：点号后缀格式 "<theme_id>.<effect_id>"（如 sponge-host-handdrawn-v1.ink-color-reveal）
    if "." in target:
        base_theme, _, effect = target.partition(".")
        # 效果必须在注册表内
        if effect not in VISUAL_EFFECTS:
            raise IllustrationThemeError("illustration-style-invalid")
        # 主题必须在该效果的白名单内
        if base_theme not in EFFECT_THEME_WHITELIST.get(effect, frozenset()):
            raise IllustrationThemeError("illustration-style-invalid")
        # 主题必须是已注册的主题
        if base_theme not in THEMES:
            raise IllustrationThemeError("illustration-style-invalid")
        return ResolvedVisualStyle(
            target=target,
            schema_version=5,
            visual_system=PROFILED_VISUAL_SYSTEM,
            visual_theme=base_theme,
            illustration_skill="ra-video-illustrations",
            visual_effect=effect,
        )

    if target in THEMES:
        return ResolvedVisualStyle(
            target=target,
            schema_version=4,
            visual_system=PROFILED_VISUAL_SYSTEM,
            visual_theme=target,
            illustration_skill="ra-video-illustrations",
        )
    legacy = {
        "xiaohei-white-first-v1": (
            1,
            "xiaohei-white-first-v1",
            None,
            "katerj-xiaohei-illustrations",
        ),
        "editorial-motion-v2": (
            2,
            "editorial-motion-v2",
            None,
            "ra-video-illustrations",
        ),
        "semantic-handdrawn-v3": (
            3,
            "semantic-handdrawn-v3",
            None,
            "ra-video-illustrations",
        ),
        TYPE_LED_TARGET: (
            3,
            "semantic-handdrawn-v3",
            None,
            "ra-video-illustrations",
        ),
    }
    try:
        schema_version, visual_system, visual_theme, illustration_skill = legacy[
            target
        ]
    except KeyError:
        raise IllustrationThemeError("illustration-style-invalid") from None
    return ResolvedVisualStyle(
        target=target,
        schema_version=schema_version,
        visual_system=visual_system,
        visual_theme=visual_theme,
        illustration_skill=illustration_skill,
    )


__all__ = [
    "CHINESE_STYLE_CATALOG",
    "DEFAULT_VISUAL_TARGET",
    "EFFECT_THEME_WHITELIST",
    "PROFILED_VISUAL_SYSTEM",
    "THEMES",
    "TYPE_LED_TARGET",
    "VISUAL_EFFECTS",
    "ChineseStyleEntry",
    "IllustrationTheme",
    "IllustrationThemeError",
    "ResolvedVisualStyle",
    "get_theme",
    "resolve_visual_style",
]

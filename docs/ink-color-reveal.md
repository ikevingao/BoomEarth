# BoomEarth ink-color-reveal 手绘动效规范与使用指南

## 1. 概述与设计背景

`ink-color-reveal` 是 BoomEarth 视频插画系统的进阶手绘显现动效（Phase 1）。
设计灵感来源于开源白板渲染引擎 [cs-board](https://github.com/ChenShuo2004/cs-board)（MIT 协议）的三阶段手绘理念：
- **阶段一：墨线显现**。画面首先呈现纯白底与对比鲜明的纯黑线稿，还原真实的钢笔/勾线笔下笔轮廓。
- **阶段二：交叉淡化**。墨线稿在彩色层就位的同时逐渐减退。
- **阶段三：彩色渐染**。彩色原图从灰度（grayscale）同步过渡到全彩，仿佛水彩在白纸上层层晕染铺开。

本效果在 Phase 1 阶段采用**轻量纯净**路线：
- 离线派生：基于纯 PIL 图像算法提取高质量确定性黑白墨线稿，无需引入重型依赖；
- 动效呈现：基于 GSAP 双层 DOM 堆叠时间轴，无缝契合 BoomEarth 的 Chromium 逐帧离线渲染栈。

---

## 2. 触发与配置规则

### 2.1 Schema V5 与白名单机制
为了确保历史存量工程（V1-V4）100% 绝对不受任何破坏，`ink-color-reveal` 采用显式版本升级与白名单准入：
- **模式版本**：`schema_version: 5`
- **准入主题白名单**：当前开放给 `sponge-host-handdrawn-v1`（方块海绵手绘主题）；其余主题不可越权使用。
- **默认机制不变**：若未显式指定效果后缀，系统默认采用主题固有的转场动效（如 scale-settle）。

### 2.2 交接稿触发语法
在视频项目的 `交接稿.md` 头部 Frontmatter 中声明带后缀的 visual 字段：

```yaml
---
status: 制作中
visual: "sponge-host-handdrawn-v1.ink-color-reveal"
illustration_skill: "ra-video-illustrations"
---
```

编译工具（`compile_content_plan.py`）将自动解析并将其绑定到内容计划中的 `visual_effect: "ink-color-reveal"`。

---

## 3. 墨线稿离线派生机制

### 3.1 确定性算法保证
派生模块位于 `src/boomearth/video/ink_variant.py`：
1. 输入彩色插画 PNG；
2. 转换为单通道灰度（L mode）；
3. 增强对比度（factor=3.0）强化边缘笔触；
4. 阈值二值化（threshold=200，深色置 0，亮色置 255）；
5. 转换回 RGB 并无损输出为 PNG 字节流。

**确定性保障**：相同输入必然输出相同 SHA-256 哈希。

### 3.2 派生脚本 CLI
在生成全套场景彩色插画后，运行派生脚本：
```bash
uv run python automation/scripts/derive_ink_variants.py \
  --project-dir "01-内容生产/视频工作台/制作中/<项目目录>"
```
- 输出目录：`工程/ink-variants/<theme_id>/scene-*-ink.png`
- 回执记录：`工程/ink-variants.json`，遵循严格的 `no-clobber` 幂等保护机制。

---

## 4. GSAP 双层 DOM 动效节奏

在渲染工程生成阶段（`render_project.py`），场景插画容器将输出双层堆叠结构：
```html
<div class="ink-color-stack">
  <img class="ink-color-layer" id="scene-01--visual--color" src="assets/.../scene-01.png" style="opacity:0" />
  <img class="ink-layer" id="scene-01--visual--ink" src="assets/ink-variants/.../scene-01-ink.png" style="opacity:0" />
</div>
```

对应时间轴（GSAP Timeline）执行精细控制的三段节奏：
1. **0.0s ~ 0.6s**：墨线层 `opacity: 0 -> 1`（ease: `power2.out`），黑白线条清晰显现。
2. **0.6s ~ 1.1s**：墨线层 `opacity: 1 -> 0`（ease: `sine.in`，时长 0.5s），优雅淡出。
3. **0.6s ~ 1.5s**：彩色层 `opacity: 0 -> 1` 伴随 `filter: grayscale(1) -> grayscale(0)`（ease: `sine.out`，时长 0.9s），色彩饱和充盈。

---

## 5. Phase 2 演进路线（未来规划）

在当前 Phase 1 验证稳定后，Phase 2 将复用既有的 `visual_effect: "ink-color-reveal"` 接口协议，探索：
1. **OpenCV 笔画拓扑提取**：对墨线稿进行骨架细化（Zhang-Suen 算法）与连通分支排序；
2. **SVG/Canvas 逐笔动态勾勒**：实现由粗到细、按笔画笔顺由上至下、由左至右的手绘绘制体验；
3. **聚色扫掠过渡**：彩色自墨线轮廓向外泛染扩散。

# 本地 IndexTTS2 与云端 API 双轨并存完善实施报告

## 1. 任务完成概览

根据 `implementation_plan.md` 的要求，已完成本地 IndexTTS2 部署与云端 TTS（微软 Edge-TTS / 阿里百炼 CosyVoice）的双轨并存体系改造。

- **零破坏性与向后兼容**：
  - `tests/test_config.py`：12 项基础配置测试 100% 通过；
  - `tests/test_indextts2.py`：103 项本地 IndexTTS2 核心与防伪测试 100% 通过。
- **动态工厂与云端合成**：
  - 新增 `src/boomearth/audio/cloud_tts.py`（实现 `CloudTTSNarrator` 与 `CloudTTSRouting`）；
  - 新增 `src/boomearth/audio/narrator_factory.py`（实现 `load_narrator` 动态调度工厂）；
  - 更新 `src/boomearth/audio/__init__.py` 导出统一接口；
  - 新增 `tests/test_cloud_tts.py`（包含 Edge-TTS / CosyVoice 路由解析、环境校验、16-bit PCM WAV 转换、1.12× 语速拉伸及 `VoiceManifest` 生成的全部测试用例，100% 通过）。
- **环境诊断与配置模板**：
  - `src/boomearth/config.py`：平滑支持 `TTS_PROVIDER`, `TTS_VOICE`, `IMAGEGEN_PROVIDER`, `IMAGEGEN_MODEL`；
  - `automation/scripts/check_env.py`：当配置非本地模式时，平滑跳过本地 IndexTTS2 路径检查；
  - `automation/config/tts-routing.cloud.example.json`：新增云端路由示例模板。

---

## 2. 修改与新增文件清单

| 文件路径 | 状态 | 职责与改动说明 |
| :--- | :--- | :--- |
| `pyproject.toml` | [MODIFY] | 引入 `edge-tts>=6.1.12` 依赖，提供免费高品质解说音色 |
| `src/boomearth/config.py` | [MODIFY] | 平滑支持可选云端环境变量字段，保持原有 `REQUIRED_VARIABLES` 契约不变 |
| `automation/scripts/check_env.py` | [MODIFY] | 在 `TTS_PROVIDER != "indextts2-local"` 时跳过本地 IndexTTS2 物理路径检查 |
| `src/boomearth/audio/cloud_tts.py` | [NEW] | 实现 `CloudTTSNarrator`，自动执行音频转换、1.12× 变速并生成 `VoiceManifest` |
| `src/boomearth/audio/narrator_factory.py` | [NEW] | 实现 `load_narrator(route_path)` 工厂方法，根据 `provider` 自动分发 |
| `src/boomearth/audio/__init__.py` | [MODIFY] | 导出 `CloudTTSNarrator`、`load_narrator` 等统一接口 |
| `automation/config/tts-routing.cloud.example.json` | [NEW] | 提供云端模式的标准路由配置示例模板 |
| `tests/test_cloud_tts.py` | [NEW] | 针对云端 TTS 路由、合成管线及环境检查的测试套件 |

---

## 3. 测试验证结果

```powershell
# 1. 基础配置测试 (12 项)
uv run pytest tests/test_config.py -q
# 输出: 12 passed in 0.09s

# 2. 云端 TTS 与工厂测试 (7 项)
uv run pytest tests/test_cloud_tts.py -q
# 输出: 7 passed in 3.20s

# 3. 本地 IndexTTS2 核心与防伪测试 (103 项)
uv run pytest tests/test_indextts2.py -q
# 输出: 103 passed in 197.06s (0:03:17)
```

---

## 4. 用户切换模式指南

### 切换为【云端 Edge-TTS（推荐，免 Key）】
将 `automation/config/tts-routing.json` 替换或修改为：
```json
{
  "schema_version": 1,
  "provider": "edge-tts",
  "model": "azure-neural",
  "voice_id": "zh-CN-YunxiNeural",
  "playback_speed": 1.12,
  "used_fallback": false
}
```

### 切换为【云端 阿里百炼 CosyVoice】
在 `.env` 中配置 `DASHSCOPE_API_KEY`，并将 `automation/config/tts-routing.json` 设置为：
```json
{
  "schema_version": 1,
  "provider": "dashscope-cosyvoice",
  "model": "cosyvoice-v1",
  "voice_id": "longxiaochun",
  "playback_speed": 1.12,
  "used_fallback": false
}
```

### 切换回【本地 IndexTTS2 模式】
将 `automation/config/tts-routing.json` 恢复为本地配置（参考 `tts-routing.example.json`），即可无缝恢复本地 GPU 推理模式。

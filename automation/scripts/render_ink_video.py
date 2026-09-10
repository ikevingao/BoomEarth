"""Render ink-color-reveal handdrawn animated video for BoomEarth production projects."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path
import numpy as np
from PIL import Image

def render_ink_video(project_dir: Path) -> Path:
    project_dir = Path(project_dir).resolve()
    engineering = project_dir / "工程"
    media = engineering / "media"
    illustrations_dir = media / "illustrations"
    ink_dir = engineering / "ink-variants" / "sponge-host-handdrawn-v1"
    narration_path = media / "narration.wav"
    output_media = media / "render.mp4"
    final_output = project_dir / "成片" / f"{project_dir.name}.mp4"
    final_output.parent.mkdir(parents=True, exist_ok=True)

    # 4 scenes timing
    scenes = [
        {"id": "scene-01", "start": 0.0, "end": 4.44},
        {"id": "scene-02", "start": 4.44, "end": 22.22},
        {"id": "scene-03", "start": 22.22, "end": 28.80},
        {"id": "scene-04", "start": 28.80, "end": 33.10},
    ]

    # Pre-process scene canvases
    scene_canvases = {}
    print("Preparing 1920x1080 scene canvases...")
    for sc in scenes:
        sid = sc["id"]
        color_path = illustrations_dir / f"{sid}.png"
        ink_path = ink_dir / f"{sid}-ink.png"

        c_img = Image.open(color_path).convert("RGB")
        i_img = Image.open(ink_path).convert("RGB")

        scale = min(1920 / c_img.width, 1080 / c_img.height)
        nw, nh = int(c_img.width * scale), int(c_img.height * scale)
        c_scaled = c_img.resize((nw, nh), Image.Resampling.LANCZOS)
        i_scaled = i_img.resize((nw, nh), Image.Resampling.LANCZOS)

        ox = (1920 - nw) // 2
        oy = (1080 - nh) // 2

        c_arr = np.ones((1080, 1920, 3), dtype=np.float32) * 255.0
        c_arr[oy:oy+nh, ox:ox+nw] = np.array(c_scaled, dtype=np.float32)

        i_arr = np.ones((1080, 1920, 3), dtype=np.float32) * 255.0
        i_arr[oy:oy+nh, ox:ox+nw] = np.array(i_scaled, dtype=np.float32)

        # Grayscale
        gray_arr = np.dot(c_arr[..., :3], [0.2989, 0.5870, 0.1140])
        g_arr = np.stack([gray_arr] * 3, axis=-1)

        # 自动检测实际墨线插画内容的真实 X 轴起始与结束坐标，消除走空白区域带来的延迟
        non_white = np.any(i_arr < 240, axis=-1)
        ink_cols = np.where(np.any(non_white, axis=0))[0]
        if len(ink_cols) > 0:
            c_start_x = max(0.0, float(ink_cols[0] - 8))
            c_end_x = min(1920.0, float(ink_cols[-1] + 12))
        else:
            c_start_x = 0.0
            c_end_x = 1920.0

        static_bytes = np.clip(c_arr, 0, 255).astype(np.uint8).tobytes()

        scene_canvases[sid] = {
            "c_arr": c_arr,
            "g_arr": g_arr,
            "i_arr": i_arr,
            "static_bytes": static_bytes,
            "c_start_x": c_start_x,
            "c_end_x": c_end_x,
        }

    total_duration = 33.10
    fps = 30
    total_frames = int(round(total_duration * fps))
    print(f"Total frames to render: {total_frames} ({total_duration}s @ {fps}fps)")

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", "1920x1080",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",
        "-i", str(narration_path),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(final_output),
    ]

    pipe = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

    # Load subtitles & word-level timestamps
    captions_file = media / "captions.json"
    words_file = media / "captions_words.json"
    captions = []
    words = []
    if captions_file.exists():
        with open(captions_file, encoding="utf-8") as f:
            captions = json.load(f)
    if words_file.exists():
        with open(words_file, encoding="utf-8") as f:
            words = json.load(f)

    font_path = "C:/Windows/Fonts/msyhbd.ttc"
    if not Path(font_path).exists():
        font_path = "C:/Windows/Fonts/msyh.ttc"
    from PIL import ImageDraw, ImageFont
    font = ImageFont.truetype(font_path, 44)

    # Pre-calculate subtitle geometry and layout
    prepared_captions = []
    for cap in captions:
        cap_text = cap["text"]
        cap_words = [
            w for w in words
            if not w.get("isGap", False) and w["start"] >= cap["start"] - 0.05 and w["end"] <= cap["end"] + 0.05
        ]
        if not cap_words:
            dur = cap["end"] - cap["start"]
            c_count = len(cap_text)
            c_dur = dur / max(1, c_count)
            cap_words = [
                {"text": char, "start": cap["start"] + i * c_dur, "end": cap["start"] + (i + 1) * c_dur}
                for i, char in enumerate(cap_text)
            ]

        word_positions = []
        curr_offset = 0.0
        for w in cap_words:
            w_text = w["text"]
            w_w = font.getlength(w_text)
            word_positions.append({
                "text": w_text,
                "start": w["start"],
                "end": w["end"],
                "rel_x": curr_offset,
                "width": w_w,
            })
            curr_offset += w_w

        total_w = curr_offset if curr_offset > 0 else font.getlength(cap_text)
        start_x = (1920 - total_w) / 2
        base_y = 1080 - 140
        pad_x, pad_y = 28, 12
        pill_box = (
            int(start_x - pad_x),
            int(base_y - pad_y),
            int(start_x + total_w + pad_x),
            int(base_y + 44 + pad_y),
        )
        bw = pill_box[2] - pill_box[0]
        bh = pill_box[3] - pill_box[1]

        prepared_captions.append({
            "start": cap["start"],
            "end": cap["end"],
            "words": word_positions,
            "pill_box": pill_box,
            "bw": bw,
            "bh": bh,
            "pad_x": pad_x,
            "pad_y": pad_y,
        })

    xs = np.arange(1920, dtype=np.float32)[None, :, None]

    t0 = time.time()
    for frame_idx in range(total_frames):
        t = frame_idx / float(fps)
        # Find current scene
        cur_sc = scenes[-1]
        for sc in scenes:
            if sc["start"] <= t < sc["end"]:
                cur_sc = sc
                break

        sid = cur_sc["id"]
        sc_data = scene_canvases[sid]
        s = t - cur_sc["start"]

        scene_duration = cur_sc["end"] - cur_sc["start"]
        # 预留结尾全彩定格时间（让画面与语音讲完同步定格），其余时间全部用于画面渐进展开
        hold_time = min(0.6, scene_duration * 0.08)
        active_time = max(1.0, scene_duration - hold_time)
        t_ink = active_time * 0.65
        t_col = active_time * 0.35

        x_start = sc_data["c_start_x"]
        x_end = sc_data["c_end_x"]
        span = x_end - x_start

        if s < t_ink:
            # 阶段 1：左边绘制墨线，右边保持纯白空白。画笔直接从第一笔实际线条开始往右画，0 空白延迟
            p = min(1.0, max(0.0, s / t_ink))
            edge = x_start + p * span
            feather = 20.0
            mask = np.clip((edge - xs) / feather, 0.0, 1.0)
            frame = mask * sc_data["i_arr"] + (1.0 - mask) * 255.0
        elif s < active_time:
            # 阶段 2：整幅墨线画全后，彩色从实际内容起点向终点逐级填色
            p_col = min(1.0, max(0.0, (s - t_ink) / t_col))
            edge_col = x_start + p_col * span
            feather = 20.0
            mask_col = np.clip((edge_col - xs) / feather, 0.0, 1.0)
            frame = mask_col * sc_data["c_arr"] + (1.0 - mask_col) * sc_data["i_arr"]
        else:
            # 阶段 3：画面完全绘制与填色完成，呈现高清全彩图，对应台词与字幕正好收尾讲完
            frame = sc_data["c_arr"].copy()

        # 叠加动态逐字展开字幕（与配音和画面同步逐步展开显示）
        for p_cap in prepared_captions:
            if p_cap["start"] <= t <= p_cap["end"]:
                has_spoken = any(t >= w["start"] for w in p_cap["words"])
                if has_spoken:
                    bw, bh = p_cap["bw"], p_cap["bh"]
                    pill_img = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
                    pdraw = ImageDraw.Draw(pill_img)
                    pdraw.rounded_rectangle([0, 0, bw, bh], radius=16, fill=(30, 32, 35, 215))

                    pad_x = p_cap["pad_x"]
                    pad_y = p_cap["pad_y"]
                    for w in p_cap["words"]:
                        if t >= w["start"]:
                            is_curr = w["start"] <= t <= w["end"]
                            col = (255, 230, 0, 255) if is_curr else (255, 255, 255, 255)
                            pdraw.text(
                                (pad_x + w["rel_x"], pad_y - 2),
                                w["text"],
                                font=font,
                                fill=col,
                                stroke_width=2,
                                stroke_fill=(20, 20, 20, 255),
                            )

                    pill_arr = np.array(pill_img, dtype=np.float32)
                    alpha = pill_arr[..., 3:4] / 255.0
                    box = p_cap["pill_box"]
                    sub_f = frame[box[1]:box[3], box[0]:box[2]]
                    frame[box[1]:box[3], box[0]:box[2]] = alpha * pill_arr[..., :3] + (1.0 - alpha) * sub_f
                break

        raw_bytes = np.clip(frame, 0, 255).astype(np.uint8).tobytes()
        pipe.stdin.write(raw_bytes)

    pipe.stdin.close()
    pipe.wait()
    print(f"Render completed in {time.time() - t0:.2f}s! Output: {final_output}")

    # Copy to render.mp4
    import shutil
    shutil.copyfile(final_output, output_media)

    # Re-generate contact sheet
    qc_dir = project_dir / "质检"
    qc_dir.mkdir(parents=True, exist_ok=True)
    contact_sheet_png = qc_dir / "contact-sheet.png"
    contact_sheet_jpg = qc_dir / "contact-sheet.jpg"

    times = [1.654, 8.271, 14.888, 18.196, 24.813, 31.43]
    captured_frames = []
    for ts in times:
        out_f = qc_dir / f"frame_{ts:.3f}.png"
        cmd = ["ffmpeg", "-y", "-ss", f"{ts:.3f}", "-i", str(final_output), "-frames:v", "1", str(out_f)]
        subprocess.run(cmd, capture_output=True)
        with Image.open(out_f) as im:
            captured_frames.append(im.copy())
        out_f.unlink(missing_ok=True)

    # Build 3x2 contact sheet
    # 3 cols, 2 rows, thumb size: 640x360
    sheet = Image.new("RGB", (1920, 720), (255, 255, 255))
    for idx, im in enumerate(captured_frames):
        thumb = im.resize((640, 360), Image.Resampling.LANCZOS)
        row = idx // 3
        col = idx % 3
        sheet.paste(thumb, (col * 640, row * 360))

    sheet.save(contact_sheet_png, format="PNG")
    sheet.save(contact_sheet_jpg, format="JPEG", quality=95)
    print("Updated contact sheet.")

    return final_output

if __name__ == "__main__":
    p = Path("01-内容生成/视频工作台/制作中/2026-09-09-ai-intro-verification-v1")
    render_ink_video(p)

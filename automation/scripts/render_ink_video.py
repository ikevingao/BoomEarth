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

        static_bytes = np.clip(c_arr, 0, 255).astype(np.uint8).tobytes()

        scene_canvases[sid] = {
            "c_arr": c_arr,
            "g_arr": g_arr,
            "i_arr": i_arr,
            "static_bytes": static_bytes,
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

        if s < 0.6:
            tau = s / 0.6
            alpha_ink = 1.0 - (1.0 - tau) ** 2
            frame = (1.0 - alpha_ink) * 255.0 + alpha_ink * sc_data["i_arr"]
            raw_bytes = np.clip(frame, 0, 255).astype(np.uint8).tobytes()
        elif s < 1.1:
            tau_ink = (s - 0.6) / 0.5
            alpha_ink = math.cos(tau_ink * math.pi / 2.0)
            tau_col = (s - 0.6) / 0.9
            alpha_col = math.sin(tau_col * math.pi / 2.0)
            g = 1.0 - math.sin(tau_col * math.pi / 2.0)
            col = g * sc_data["g_arr"] + (1.0 - g) * sc_data["c_arr"]
            current_col = (1.0 - alpha_col) * 255.0 + alpha_col * col
            ink_norm = sc_data["i_arr"] / 255.0
            ink_factor = (1.0 - alpha_ink) * 1.0 + alpha_ink * ink_norm
            frame = current_col * ink_factor
            raw_bytes = np.clip(frame, 0, 255).astype(np.uint8).tobytes()
        elif s < 1.5:
            tau_col = (s - 0.6) / 0.9
            g = 1.0 - math.sin(tau_col * math.pi / 2.0)
            frame = g * sc_data["g_arr"] + (1.0 - g) * sc_data["c_arr"]
            raw_bytes = np.clip(frame, 0, 255).astype(np.uint8).tobytes()
        else:
            raw_bytes = sc_data["static_bytes"]

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

import os
import subprocess
import json
from pathlib import Path
from typing import Any
from loguru import logger


class RenderEngine:
    def __init__(self, output_dir: str = "./output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_background(
        self, scene_desc: str, output_path: str, width: int = 1920, height: int = 1080,
    ) -> str:
        """Generate a background image using Pillow based on scene description."""
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
        import colorsys
        import hashlib

        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)

        seed = hashlib.md5(scene_desc.encode()).hexdigest()
        hue = (int(seed[:8], 16) % 360) / 360.0
        sat = 0.4 + (int(seed[8:12], 16) % 30) / 100.0
        light = 0.3 + (int(seed[12:16], 16) % 20) / 100.0

        r, g, b = [int(x * 255) for x in colorsys.hls_to_rgb(hue, light, sat)]
        r2 = min(255, r + 40)
        g2 = min(255, g + 40)
        b2 = min(255, b + 40)

        for y in range(height):
            ratio = y / height
            cr = int(r * (1 - ratio) + r2 * ratio)
            cg = int(g * (1 - ratio) + g2 * ratio)
            cb = int(b * (1 - ratio) + b2 * ratio)
            draw.line([(0, y), (width, y)], fill=(cr, cg, cb))

        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        import random
        random.seed(int(seed[:16], 16))
        for _ in range(20 + int(seed[:4], 16) % 30):
            cx = random.randint(0, width)
            cy = random.randint(0, height)
            radius = random.randint(20, 120)
            alpha = random.randint(5, 20)
            overlay_draw.ellipse(
                [cx - radius, cy - radius, cx + radius, cy + radius],
                fill=(255, 255, 255, alpha),
            )

        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        img = img.filter(ImageFilter.GaussianBlur(radius=2))

        img.save(output_path, quality=85)
        return output_path

    def create_text_overlay(
        self, text: str, output_path: str, width: int = 1920, height: int = 1080,
    ) -> str:
        """Create a text overlay image."""
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
        except (IOError, OSError):
            font = ImageFont.load_default()
            font_small = font

        lines = []
        current = ""
        for word in text.split():
            test = current + " " + word if current else word
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > width - 200:
                lines.append(current)
                current = word
            else:
                current = test
        if current:
            lines.append(current)

        total_height = len(lines) * 80
        y_start = (height - total_height) // 2

        padding = 40
        box_height = total_height + padding * 2
        draw.rectangle(
            [width // 2 - width // 3, y_start - padding,
             width // 2 + width // 3, y_start + box_height],
            fill=(0, 0, 0, 180),
        )

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            x = (width - line_width) // 2
            draw.text((x, y_start), line, fill=(255, 255, 255), font=font)
            y_start += 80

        img.save(output_path)
        return output_path

    def render_video(
        self,
        audio_path: str,
        image_paths: list[str],
        durations: list[float],
        output_path: str,
        resolution: tuple[int, int] = (1920, 1080),
        fps: int = 30,
    ) -> str:
        """Render a video from images and audio using FFmpeg."""
        output_path = str(self.output_dir / output_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        concat_file = self.output_dir / "concat.txt"
        with open(concat_file, "w") as f:
            for img_path, dur in zip(image_paths, durations):
                abs_path = os.path.abspath(img_path)
                f.write(f"file '{abs_path}'\n")
                f.write(f"duration {dur}\n")
            f.write(f"file '{os.path.abspath(image_paths[-1])}'\n")

        video_stem = output_path.rsplit(".", 1)[0]
        temp_video = video_stem + "_temp.mp4"

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
            "-s", f"{resolution[0]}x{resolution[1]}",
            "-preset", "fast",
            "-crf", "23",
            "-an",
            temp_video,
        ]
        logger.info(f"Rendering video (images): {' '.join(cmd)}")
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)

        cmd2 = [
            "ffmpeg", "-y",
            "-i", temp_video,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            "-movflags", "+faststart",
            output_path,
        ]
        logger.info(f"Muxing audio: {' '.join(cmd2)}")
        subprocess.run(cmd2, check=True, capture_output=True, text=True, timeout=300)

        if os.path.exists(temp_video):
            os.remove(temp_video)
        if concat_file.exists():
            concat_file.unlink()

        logger.info(f"Video rendered: {output_path}")
        return output_path

    def get_video_info(self, video_path: str) -> dict[str, Any]:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration,size",
            "-show_entries", "stream=codec_type,codec_name",
            "-of", "json",
            video_path,
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            info = json.loads(result.stdout)
            duration = float(info.get("format", {}).get("duration", 0))
            size = int(info.get("format", {}).get("size", 0))
            return {
                "duration": duration,
                "size_bytes": size,
                "size_mb": round(size / (1024 * 1024), 2),
                "path": video_path,
            }
        except (json.JSONDecodeError, subprocess.TimeoutExpired, KeyError):
            return {"duration": 0, "size_bytes": 0, "size_mb": 0, "path": video_path}

import os
from .base import Stage, StageContext
from loguru import logger
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import colorsys
import hashlib


class ThumbnailStage(Stage):
    async def execute(self, ctx: StageContext) -> StageContext:
        logger.info(f"Generating thumbnail for: {ctx.job_id}")

        output_dir = ctx.get("assets_dir", "./assets")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"thumb_{ctx.job_id[:8]}.jpg")

        script = ctx.script or {}
        title = script.get("title", ctx.topic)

        self._generate_thumbnail(title, output_path)
        ctx.thumbnail_path = output_path

        logger.info(f"Thumbnail: {output_path}")
        return ctx

    def _generate_thumbnail(self, title: str, output_path: str):
        width, height = 1280, 720
        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)

        seed = hashlib.md5(title.encode()).hexdigest()
        hue = (int(seed[:8], 16) % 360) / 360.0
        r, g, b = [int(x * 255) for x in colorsys.hls_to_rgb(hue, 0.4, 0.7)]

        for y in range(height):
            ratio = y / height
            cr = int(r * (1 - ratio * 0.5))
            cg = int(g * (1 - ratio * 0.5))
            cb = int(b * (1 - ratio * 0.5))
            draw.line([(0, y), (width, y)], fill=(cr, cg, cb))

        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        import random
        random.seed(int(seed[:16], 16))
        for _ in range(3):
            cx = random.randint(100, width - 100)
            cy = random.randint(100, height - 100)
            r_size = random.randint(80, 200)
            overlay_draw.ellipse(
                [cx - r_size, cy - r_size, cx + r_size, cy + r_size],
                fill=(255, 255, 255, 15),
            )

        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        img = img.filter(ImageFilter.GaussianBlur(radius=1))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48
            )
        except (IOError, OSError):
            font = ImageFont.load_default()

        words = title.split()
        lines = []
        current = ""
        for word in words:
            test = current + " " + word if current else word
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > width - 120:
                lines.append(current)
                current = word
            else:
                current = test
        if current:
            lines.append(current)

        y_start = height // 2 - len(lines) * 35
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            x = (width - line_width) // 2
            draw.text((x + 3, y_start + 3), line, fill=(0, 0, 0, 200), font=font)
            draw.text((x, y_start), line, fill=(255, 255, 255), font=font)
            y_start += 70

        draw.rectangle([width - 200, 20, width - 20, 80], fill=(255, 0, 0, 230))
        draw.text((width - 180, 30), "PLAY", fill=(255, 255, 255), font=font)

        img.save(output_path, quality=90)

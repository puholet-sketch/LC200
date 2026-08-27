"""Render 21-inch Zumbo face + tire sizes on the LC200 side view."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

from render_stock20_fitment import (
    OUT_DIR,
    RIM_MM,
    ROOT,
    SRC_CAR,
    STOCK_OD,
    WHEELS,
    clip_below_ground,
    ground_y,
    make_tire_layer,
    paste_center,
)

SRC_ZUMBO = ROOT / "assets/img/zumbo-21-wheel.jpg"

# 21" rim is 21/20 of the 20" face.
RIM21 = 21 / 20

SIZES = [
    {"id": "275-50", "label": "275/50R21 комфорт", "od": 808.0, "side": 137.5, "tread": "ht"},
    {"id": "285-45", "label": "285/45R21 матч", "od": 790.0, "side": 128.0, "tread": "ht"},
    {"id": "295-45", "label": "295/45R21 шире", "od": 799.0, "side": 133.0, "tread": "ht"},
    {"id": "275-45", "label": "275/45R21 жёстче", "od": 781.0, "side": 124.0, "tread": "ht"},
    {"id": "285-40", "label": "285/40R21 не брать", "od": 761.0, "side": 114.0, "tread": "ht"},
]


def extract_zumbo_face(path: Path) -> Image.Image:
    """Circular face of the 21\" Zumbo product shot (studio, white ground)."""
    bgr = cv2.imread(str(path))
    if bgr is None:
        raise FileNotFoundError(path)
    h, w = bgr.shape[:2]
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    circles = cv2.HoughCircles(
        blur,
        cv2.HOUGH_GRADIENT,
        dp=1.1,
        minDist=80,
        param1=90,
        param2=35,
        minRadius=int(w * 0.35),
        maxRadius=int(w * 0.48),
    )
    if circles is None:
        raise RuntimeError(f"no rim circle in {path}")
    cx0, cy0 = w / 2.0, h / 2.0
    cx, cy, r = min(
        circles[0],
        key=lambda c: (float(c[0]) - cx0) ** 2 + (float(c[1]) - cy0) ** 2,
    )
    cx, cy, r = float(cx), float(cy), float(r) - 1.8
    r = min(r, cx - 1, cy - 1, w - cx - 1, h - cy - 1)

    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb).convert("RGBA")
    yy, xx = np.ogrid[:h, :w]
    rr = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    alpha = np.clip((r - 0.4 - rr) * 210, 0, 255).astype(np.uint8)
    pil.putalpha(Image.fromarray(alpha, "L"))
    box = (int(cx - r - 1), int(cy - r - 1), int(cx + r + 1), int(cy + r + 1))
    face = pil.crop(box)
    face = ImageEnhance.Contrast(face).enhance(1.16)
    return ImageEnhance.Brightness(face).enhance(1.04)


def render_21(car: Image.Image, face_src: Image.Image, spec: dict) -> Image.Image:
    out = car.convert("RGBA")
    scale = spec["od"] / STOCK_OD
    for cx, cy, rim20 in WHEELS:
        rim_r = rim20 * RIM21
        stock_tire_r = rim20 * (STOCK_OD / RIM_MM)
        new_tire_r = stock_tire_r * scale
        gy = ground_y(cx, cy, rim20)
        new_cy = gy - new_tire_r
        tire_px = int(round(new_tire_r * 2)) + 6
        rim_px = int(round(rim_r * 2 * 0.995))
        tire = make_tire_layer(tire_px, rim_px // 2, spec.get("tread", "ht"))
        tire = clip_below_ground(tire, cx, new_cy, gy)
        paste_center(out, tire, cx, new_cy)
        face = face_src.resize((rim_px, rim_px), Image.Resampling.LANCZOS)
        paste_center(out, face, cx, new_cy)
    return out.convert("RGB")


def crop_rear(img: Image.Image, spec: dict) -> Image.Image:
    cx, cy, rim20 = WHEELS[1]
    pad = int(rim20 * 2.15)
    box = (cx - pad, cy - pad - 36, cx + pad, cy + pad + 28)
    crop = img.crop(box).convert("RGBA")
    draw = ImageDraw.Draw(crop)
    stock_r = rim20 * (STOCK_OD / RIM_MM)
    scale = spec["od"] / STOCK_OD
    new_r = stock_r * scale
    gy = ground_y(cx, cy, rim20)
    new_cy = gy - new_r
    lx = cx - box[0]
    ly = new_cy - box[1]
    draw.ellipse((lx - stock_r, ly - stock_r, lx + stock_r, ly + stock_r), outline=(235, 10, 30, 150), width=2)
    bar = Image.new("RGBA", (crop.width, 36), (17, 17, 17, 200))
    crop.alpha_composite(bar, (0, crop.height - 36))
    d2 = ImageDraw.Draw(crop)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
    d2.text((12, crop.height - 28), spec["label"], fill=(255, 255, 255, 255), font=font)
    return crop.convert("RGB")


def main() -> None:
    face = extract_zumbo_face(SRC_ZUMBO)
    car = Image.open(SRC_CAR)
    comfort = None
    for spec in SIZES:
        full = render_21(car, face, spec)
        full_path = OUT_DIR / f"stock21-{spec['id']}.jpg"
        crop_path = OUT_DIR / f"stock21-{spec['id']}-wheel.jpg"
        full.save(full_path, quality=88, optimize=True)
        crop_rear(full, spec).save(crop_path, quality=88, optimize=True)
        print("wrote", full_path.name, crop_path.name)
        if spec["id"] == "275-50":
            comfort = full
    if comfort is not None:
        compare = OUT_DIR / "lc200-compare-21.jpg"
        comfort.save(compare, quality=88, optimize=True)
        print("wrote", compare.name)


if __name__ == "__main__":
    main()

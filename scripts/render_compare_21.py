"""Render 21-inch wheels on the LC200 side view for the 20 vs 21 compare."""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

from render_stock20_fitment import (
    OUT_DIR,
    RIM_MM,
    SRC_CAR,
    SRC_OEM,
    STOCK_OD,
    WHEELS,
    clip_below_ground,
    extract_oem_face,
    ground_y,
    make_tire_layer,
    paste_center,
)

# 21" rim is 21/20 of the 20" face.
RIM21 = 21 / 20

SIZES = [
    {"id": "275-50", "label": "275/50R21 комфорт", "od": 808.0, "side": 137.5, "dark": True, "tread": "ht"},
    {"id": "285-45", "label": "285/45R21 матч", "od": 790.0, "side": 128.0, "dark": True, "tread": "ht"},
    {"id": "295-45", "label": "295/45R21 шире", "od": 799.0, "side": 133.0, "dark": True, "tread": "ht"},
    {"id": "275-45", "label": "275/45R21 жёстче", "od": 781.0, "side": 124.0, "dark": True, "tread": "ht"},
    {"id": "285-40", "label": "285/40R21 не брать", "od": 761.0, "side": 114.0, "dark": True, "tread": "ht"},
]


def darken_face(face: Image.Image) -> Image.Image:
    """RST-style black machined face while keeping the Toyota cap readable."""
    rgb = face.convert("RGBA")
    arr = np.array(rgb).astype(np.float32)
    lum = arr[..., 0] * 0.3 + arr[..., 1] * 0.5 + arr[..., 2] * 0.2
    # Keep bright machined highlights, crush the grey pockets to charcoal.
    mix = np.clip((lum - 90) / 90, 0, 1)[..., None]
    charcoal = arr[..., :3] * 0.42
    silver = arr[..., :3] * 0.92
    arr[..., :3] = charcoal * (1 - mix) + silver * mix
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    return ImageEnhance.Contrast(out).enhance(1.12)


def render_21(car: Image.Image, oem: Image.Image, spec: dict) -> Image.Image:
    out = car.convert("RGBA")
    face_src = darken_face(oem) if spec.get("dark") else oem
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
    oem = extract_oem_face(SRC_OEM)
    car = Image.open(SRC_CAR)
    comfort = None
    for spec in SIZES:
        full = render_21(car, oem, spec)
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

"""Composite OEM 20\" face + tire sizes onto the LC200 side view."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC_CAR = ROOT / "assets/img/lc200-compare-20.png"
SRC_OEM = ROOT / "assets/img/oem-20-wheel.jpg"
OUT_DIR = ROOT / "assets/img"

WHEELS = ((291, 698, 83), (1162, 704, 83))
RIM_MM = 508.0
STOCK_OD = 793.0

SIZES = [
    {"id": "285-50", "label": "285/50R20 штат", "od": 793.0, "side": 142, "tread": "ht"},
    {"id": "275-55", "label": "275/55R20 комфорт", "od": 811.0, "side": 151, "tread": "ht"},
    {"id": "285-55", "label": "285/55R20 ширина", "od": 822.0, "side": 157, "tread": "ht"},
    {"id": "275-60", "label": "275/60R20 вид", "od": 838.0, "side": 165, "tread": "ht"},
    {"id": "275-55-at", "label": "275/55R20 A/T", "od": 811.0, "side": 151, "tread": "at"},
]


def extract_oem_face(path: Path) -> Image.Image:
    bgr = cv2.imread(str(path))
    if bgr is None:
        raise FileNotFoundError(path)
    h, w = bgr.shape[:2]
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    cardboard = cv2.inRange(hsv, (8, 40, 40), (35, 255, 255))
    metal = cv2.bitwise_not(cardboard)
    metal = cv2.morphologyEx(metal, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
    metal = cv2.morphologyEx(metal, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    ys, xs = np.where(metal > 0)
    cx = float(np.median(xs))
    cy = float(np.median(ys))
    dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
    r = float(np.percentile(dist, 95.5))
    r = min(r, cx - 6, cy - 6, w - cx - 6, h - cy - 6)

    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32)
    yy, xx = np.ogrid[:h, :w]
    rr = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    opaque = rr <= r - 2
    mean = rgb[opaque].mean(axis=0)
    # Kill the cool indoor cast; match studio-grey OEM on the car.
    target = np.array([118.0, 117.0, 116.0], dtype=np.float32)
    rgb *= target / np.maximum(mean, 1.0)
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)

    pil = Image.fromarray(rgb).convert("RGBA")
    alpha = np.clip((r - 0.4 - rr) * 210, 0, 255).astype(np.uint8)
    pil.putalpha(Image.fromarray(alpha, "L"))
    box = (int(cx - r - 1), int(cy - r - 1), int(cx + r + 1), int(cy + r + 1))
    return pil.crop(box)


def make_tire_layer(size: int, rim: int, tread: str) -> Image.Image:
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    cy = cx = size / 2.0
    yy, xx = np.ogrid[:size, :size]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    outer = size / 2.0 - 1.6
    t = np.clip((d - rim) / max(outer - rim, 1), 0, 1)
    rubber = (d <= outer) & (d >= rim - 2)
    # Sidewall is a bit lighter; tread crown is darker.
    shade = (26 + (1 - t) * 28 + t * 6).astype(np.float32)
    ang = np.arctan2(yy - cy, xx - cx)
    ribs = (np.abs(np.sin((d - rim) * 0.55)) < 0.18) & (t > 0.12) & (t < 0.78)
    shade = np.where(ribs, shade + 10, shade)
    if tread == "at":
        blocks = (np.sin(ang * 32) > 0.05) & (t > 0.62)
        shade = np.where(blocks, shade + 18, shade - 4)
        outer = outer + np.sin(ang * 36) * 1.15
        rubber = (d <= outer) & (d >= rim - 2)
    # Specular ring near the rim flange
    lip = (d > rim - 1.2) & (d < rim + 3.2)
    shade = np.where(lip, np.minimum(shade + 36, 90), shade)
    shade = np.clip(shade, 8, 96)
    arr[..., 0] = shade.astype(np.uint8)
    arr[..., 1] = shade.astype(np.uint8)
    arr[..., 2] = shade.astype(np.uint8)
    arr[..., 3] = np.where(rubber, 255, 0)
    edge = np.abs(d - outer)
    fade = np.clip((1.5 - edge) / 1.5, 0, 1)
    arr[..., 3] = np.where(edge < 1.5, (arr[..., 3] * fade).astype(np.uint8), arr[..., 3])
    return Image.fromarray(arr, "RGBA")


def paste_center(base: Image.Image, overlay: Image.Image, cx: float, cy: float) -> None:
    x = int(round(cx - overlay.width / 2))
    y = int(round(cy - overlay.height / 2))
    base.alpha_composite(overlay, (x, y))


def ground_y(cx: int, cy: int, rim_r: int) -> float:
    return cy + rim_r * (STOCK_OD / RIM_MM)


def clip_below_ground(layer: Image.Image, cx: float, cy: float, gy: float) -> Image.Image:
    arr = np.array(layer)
    top = cy - layer.height / 2
    for y in range(arr.shape[0]):
        abs_y = top + y
        if abs_y > gy + 1:
            t = min((abs_y - gy) / 7.0, 1.0)
            arr[y, :, 3] = (arr[y, :, 3] * (1 - t)).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def render_variant(car: Image.Image, oem: Image.Image, spec: dict) -> Image.Image:
    out = car.convert("RGBA")
    scale = spec["od"] / STOCK_OD
    for cx, cy, rim_r in WHEELS:
        stock_tire_r = rim_r * (STOCK_OD / RIM_MM)
        new_tire_r = stock_tire_r * scale
        gy = ground_y(cx, cy, rim_r)
        new_cy = gy - new_tire_r
        tire_px = int(round(new_tire_r * 2)) + 6
        rim_px = int(round(rim_r * 2 * 0.995))
        tire = make_tire_layer(tire_px, rim_px // 2, spec["tread"])
        tire = clip_below_ground(tire, cx, new_cy, gy)
        paste_center(out, tire, cx, new_cy)
        face = oem.resize((rim_px, rim_px), Image.Resampling.LANCZOS)
        paste_center(out, face, cx, new_cy)
    return out.convert("RGB")


def crop_rear(img: Image.Image, spec: dict) -> Image.Image:
    cx, cy, rim_r = WHEELS[1]
    pad = int(rim_r * 2.15)
    box = (cx - pad, cy - pad - 36, cx + pad, cy + pad + 28)
    crop = img.crop(box).convert("RGBA")
    draw = ImageDraw.Draw(crop)
    # Stock OD ghost so the extra sidewall is readable.
    if spec["od"] > STOCK_OD + 1:
        stock_r = rim_r * (STOCK_OD / RIM_MM)
        new_r = stock_r * (spec["od"] / STOCK_OD)
        gy = ground_y(cx, cy, rim_r)
        new_cy = gy - new_r
        lx = cx - box[0]
        ly = new_cy - box[1]
        r = stock_r
        draw.ellipse((lx - r, ly - r, lx + r, ly + r), outline=(235, 10, 30, 160), width=2)
    label = spec["label"]
    bar = Image.new("RGBA", (crop.width, 36), (17, 17, 17, 200))
    crop.alpha_composite(bar, (0, crop.height - 36))
    d2 = ImageDraw.Draw(crop)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
    d2.text((12, crop.height - 28), label, fill=(255, 255, 255, 255), font=font)
    return crop.convert("RGB")


def contact_sheet(crops: list[Image.Image]) -> Image.Image:
    w = 420
    h = 420
    gap = 12
    n = len(crops)
    sheet = Image.new("RGB", (n * w + (n - 1) * gap, h), (244, 244, 244))
    for i, im in enumerate(crops):
        sheet.paste(im.resize((w, h), Image.Resampling.LANCZOS), (i * (w + gap), 0))
    return sheet


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    oem = extract_oem_face(SRC_OEM)
    car = Image.open(SRC_CAR)
    crops = []
    for spec in SIZES:
        full = render_variant(car, oem, spec)
        full_path = OUT_DIR / f"stock20-{spec['id']}.jpg"
        crop_path = OUT_DIR / f"stock20-{spec['id']}-wheel.jpg"
        crop = crop_rear(full, spec)
        full.save(full_path, quality=88, optimize=True)
        crop.save(crop_path, quality=88, optimize=True)
        crops.append(crop)
        print("wrote", full_path.name, crop_path.name)
    sheet = contact_sheet(crops)
    sheet_path = OUT_DIR / "stock20-sheet.jpg"
    sheet.save(sheet_path, quality=86, optimize=True)
    print("wrote", sheet_path.name, sheet.size)


if __name__ == "__main__":
    main()

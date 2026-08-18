# -*- coding: utf-8 -*-
"""Generate FitPulse app icons (PNG) for PWA/APK."""
import os
from PIL import Image, ImageDraw

BG = (15, 17, 23, 255)
LIME = (210, 240, 0, 255)
BLUE = (0, 238, 252, 255)


def rounded(size, radius, fill):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=fill)
    return img


def dumbbell(img, size):
    d = ImageDraw.Draw(img)
    s = size / 100.0
    c = size / 2.0
    # bar
    bw = 8 * s
    bl = 46 * s
    d.rounded_rectangle([c - bl / 2, c - bw / 2, c + bl / 2, c + bw / 2], radius=4 * s, fill=LIME)
    # weight plates
    pw = 10 * s
    ph = 30 * s
    y0 = c - ph / 2
    for x in (c - bl / 2 - pw, c + bl / 2):
        d.rounded_rectangle([x, y0, x + pw, y0 + ph], radius=3 * s, fill=LIME)
    # outer cap plates (smaller, darker)
    cap_w = 6 * s
    cap_h = 20 * s
    y1 = c - cap_h / 2
    for x in (c - bl / 2 - pw - cap_w, c + bl / 2 + pw):
        d.rounded_rectangle([x, y1, x + cap_w, y1 + cap_h], radius=2 * s, fill=(180, 211, 0, 255))
    # neon glint line
    d.rounded_rectangle([c - bl / 2, c + bw / 2 - 1.5 * s, c + bl / 2, c + bw / 2], radius=1, fill=BLUE)


def make(size, out, maskable=False, radius=None):
    pad = int(size * 0.04)
    if maskable:
        radius = int(size * 0.45)
        img = rounded(size, radius, BG)
    else:
        radius = radius if radius is not None else int(size * 0.22)
        img = rounded(size, radius, BG)
    inner = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    dumbbell(inner, size)
    if maskable:
        # scale dumbbell down to fit safe zone (80%)
        inner = inner.resize((int(size * 0.8), int(size * 0.8)), Image.LANCZOS)
        img.alpha_composite(inner, (int(size * 0.1), int(size * 0.1)))
    else:
        img.alpha_composite(inner, (pad, pad))
    img.save(out, "PNG")
    print("wrote", out, size, "x", size)


if __name__ == "__main__":
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "icons")
    os.makedirs(base, exist_ok=True)
    make(192, os.path.join(base, "icon-192.png"))
    make(512, os.path.join(base, "icon-512.png"))
    make(512, os.path.join(base, "icon-maskable-512.png"), maskable=True)
    make(180, os.path.join(base, "apple-touch-icon.png"), radius=41)
    print("done")
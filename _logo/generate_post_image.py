#!/usr/bin/env python3
"""Generate feature images for MARS blog posts from posts.json."""

import argparse
import json
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

WIDTH, HEIGHT = 1600, 900
BG_TOP, BG_BOT = (8, 12, 20), (14, 22, 38)
ACCENT, ACCENT2 = (0, 200, 140), (0, 140, 220)
GLOW_COL = (0, 220, 160)
TEXT_COL, SUB_COL = (215, 245, 240), (100, 200, 170)

FONT_TITLE = [
    "/System/Library/Fonts/Avenir Next Condensed.ttc",
    "/System/Library/Fonts/SFNS.ttf",
    "/System/Library/Fonts/HelveticaNeue.ttc",
]
FONT_SUB = [
    "/System/Library/Fonts/SFNSMono.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Courier.ttc",
]


def load_font(candidates, size):
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except:
            pass
    return ImageFont.load_default()


def render_image(title: str, subtitle: str) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_TOP)
    draw = ImageDraw.Draw(img, "RGBA")

    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * t)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

    rng = random.Random(7)
    traces = []
    for _ in range(55):
        x1, y1 = rng.choice(range(80, WIDTH, 120)), rng.choice(range(60, HEIGHT, 110))
        x2 = max(0, min(WIDTH, x1 + rng.choice([-1, 1]) * rng.randint(1, 4) * 120))
        y2 = max(0, min(HEIGHT, y1 + rng.choice([-1, 1]) * rng.randint(1, 3) * 110))
        mid_x, mid_y = x2, y1
        alpha = rng.randint(18, 55)
        col = (*ACCENT[:3], alpha)
        w = 1 if rng.random() < 0.7 else 2
        draw.line([(x1, y1), (mid_x, mid_y)], fill=col, width=w)
        draw.line([(mid_x, mid_y), (mid_x, y2)], fill=col, width=w)
        traces.append((x1, y1, mid_x, mid_y, x2, y2))

    rng = random.Random(99)
    nodes = []
    for tr in traces:
        for px, py in [(tr[0], tr[1]), (tr[2], tr[3])]:
            if rng.random() < 0.35:
                nodes.append((px, py))

    for px, py in nodes:
        r = rng.randint(3, 6)
        alpha = rng.randint(90, 170)
        draw.ellipse(
            [(px - r - 2, py - r - 2), (px + r + 2, py + r + 2)],
            fill=(*GLOW_COL, alpha // 4),
        )
        draw.ellipse([(px - r, py - r), (px + r, py + r)], fill=(*GLOW_COL, alpha))

    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for radius in range(380, 0, -8):
        a = int(32 * (1 - radius / 380) ** 2)
        gd.ellipse(
            [
                (WIDTH // 2 - radius, HEIGHT // 2 - 30 - int(radius * 0.55)),
                (WIDTH // 2 + radius, HEIGHT // 2 - 30 + int(radius * 0.55)),
            ],
            fill=(0, 160, 110, a),
        )
    glow = glow.filter(ImageFilter.GaussianBlur(radius=40))
    img.paste(
        Image.alpha_composite(Image.new("RGBA", img.size, (0, 0, 0, 0)), glow),
        mask=glow.split()[3],
    )
    draw = ImageDraw.Draw(img, "RGBA")

    for x in range(WIDTH):
        t = abs(x - WIDTH / 2) / (WIDTH / 2)
        alpha = int(200 * (1 - t**1.5))
        draw.line([(x, 0), (x, 3)], fill=(*ACCENT, alpha))
        draw.line([(x, HEIGHT - 4), (x, HEIGHT - 1)], fill=(*ACCENT, alpha // 2))
    for x in range(WIDTH):
        t = abs(x - WIDTH / 2) / (WIDTH / 2)
        alpha = int(80 * (1 - t**2))
        draw.line([(x, 6), (x, 7)], fill=(*ACCENT2, alpha))

    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    target_h = int(HEIGHT * 0.304)
    lo, hi = 40, 700
    while lo < hi - 1:
        mid = (lo + hi) // 2
        ft = load_font(FONT_TITLE, mid)
        bb = probe.textbbox((0, 0), title, font=ft)
        if bb[3] - bb[1] <= target_h:
            lo = mid
        else:
            hi = mid

    title_size = lo
    font_title = load_font(FONT_TITLE, title_size)
    while title_size > 40:
        ft = load_font(FONT_TITLE, title_size)
        bb = probe.textbbox((0, 0), title, font=ft)
        if bb[2] - bb[0] <= int(WIDTH * 0.92):
            font_title = ft
            break
        title_size -= 6

    sub_size = max(48, int(HEIGHT * 0.069))
    font_sub = load_font(FONT_SUB, sub_size)

    tx, ty = WIDTH // 2, HEIGHT // 2 - 40
    for blur, alpha in [(28, 55), (10, 100), (3, 60)]:
        layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text(
            (tx, ty), title, font=font_title, anchor="mm", fill=(*ACCENT, alpha)
        )
        layer = layer.filter(ImageFilter.GaussianBlur(radius=blur))
        img = img.convert("RGBA")
        img = Image.alpha_composite(img, layer)
        img = img.convert("RGB")

    draw = ImageDraw.Draw(img, "RGBA")
    draw.text((tx, ty), title, font=font_title, anchor="mm", fill=TEXT_COL)
    bbox = draw.textbbox((tx, ty), title, font=font_title, anchor="mm")

    rule_y = bbox[3] + max(16, int(title_size * 0.05))
    rule_w = min(bbox[2] - bbox[0] + 60, WIDTH - 120)
    rule_x0 = (WIDTH - rule_w) // 2
    for x in range(rule_x0, rule_x0 + rule_w):
        t = abs(x - WIDTH / 2) / (rule_w / 2)
        alpha = int(180 * (1 - t**2))
        draw.line([(x, rule_y), (x, rule_y + 1)], fill=(*ACCENT, alpha))

    mid = WIDTH // 2
    d = 5
    draw.polygon(
        [
            (mid, rule_y - d),
            (mid + d, rule_y + 1),
            (mid, rule_y + d + 2),
            (mid - d, rule_y + 1),
        ],
        fill=ACCENT,
    )

    sbbox = draw.textbbox((0, 0), subtitle, font=font_sub)
    sx = (WIDTH - (sbbox[2] - sbbox[0])) // 2 - sbbox[0]
    sy = rule_y + max(14, int(title_size * 0.04))

    sub_glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    ImageDraw.Draw(sub_glow).text((sx, sy), subtitle, font=font_sub, fill=(*ACCENT, 90))
    sub_glow = sub_glow.filter(ImageFilter.GaussianBlur(radius=4))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, sub_glow)
    img = img.convert("RGB")

    ImageDraw.Draw(img, "RGBA").text((sx, sy), subtitle, font=font_sub, fill=SUB_COL)
    return img


def main():
    parser = argparse.ArgumentParser(description="Generate MARS post feature images.")
    parser.add_argument("--list", action="store_true", help="List all posts")
    parser.add_argument("--slug", help="Generate specific post slug")
    parser.add_argument("--out", help="Output directory")
    args = parser.parse_args()

    with open(os.path.join(_SCRIPT_DIR, "posts.json")) as f:
        posts = json.load(f)

    if args.list:
        print(f"{'SLUG':<30}  TITLE")
        print("-" * 70)
        for p in posts:
            print(f"{p['slug']:<30}  {p['title']}")
        return

    out_dir = args.out or os.path.join(_SCRIPT_DIR, "assets", "images", "posts")
    os.makedirs(out_dir, exist_ok=True)

    targets = [p for p in posts if args.slug is None or p["slug"] == args.slug]
    if not targets:
        print(f"Error: slug '{args.slug}' not found")
        return

    for post in targets:
        img = render_image(post["title"], post["subtitle"])
        path = os.path.join(out_dir, f"{post['slug']}.png")
        img.save(path, "PNG")
        print(f"  saved  {path}")

    print(f"\nDone — {len(targets)} image(s) written to {out_dir}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generate feature images for MARS blog posts.
Same dark tech / circuit board aesthetic as the main logo.

Usage:
    python3 generate_post_image.py          # generates all posts
    python3 generate_post_image.py --list   # prints all defined posts

To add a new post image, add an entry to POSTS below:
    {"slug": "output-filename", "title": "Main Title", "subtitle": "Subtitle text"},
"""

import argparse
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random

# ---------------------------------------------------------------------------
# Posts — edit this list to add / change entries
# ---------------------------------------------------------------------------
POSTS = [
    {"slug": "what_is_mars", "title": "Introduction", "subtitle": "What is MARS?"},
    {
        "slug": "understanding_ros2",
        "title": "Understanding ROS 2",
        "subtitle": "Middleware for Robotics",
    },
    {"slug": "niryo_ned2", "title": "Niryo Ned2", "subtitle": "The Hardware Platform"},
    {"slug": "pyniryo", "title": "Pyniryo", "subtitle": "Python SDK for Ned2"},
    {
        "slug": "ned_ros",
        "title": "Niryo ROS 2 Driver",
        "subtitle": "Bridging Hardware & ROS 2",
    },
    {
        "slug": "robot_description",
        "title": "Robot Description",
        "subtitle": "URDF & SRDF",
    },
    {"slug": "gazebo", "title": "Gazebo", "subtitle": "Simulation Environment"},
    {"slug": "mujoco", "title": "MuJoCo", "subtitle": "Sim-to-Real Gap"},
    {
        "slug": "camera_calibration",
        "title": "Camera Calibration",
        "subtitle": "Intrinsics & Extrinsics",
    },
    {
        "slug": "transport_frames",
        "title": "Transport Frames",
        "subtitle": "TF2 & Coordinate Frames",
    },
    {
        "slug": "fiducial_markers",
        "title": "Fiducial Markers",
        "subtitle": "ArUco Pose Estimation",
    },
    {"slug": "moveit2", "title": "MoveIt 2", "subtitle": "Motion Planning Framework"},
    {
        "slug": "multiple_robots_moveit2",
        "title": "Multiple Robots",
        "subtitle": "Multi-Arm in MoveIt 2",
    },
    {
        "slug": "dual_arm_config",
        "title": "Dual Arm Config",
        "subtitle": "MoveIt 2 Setup",
    },
    {
        "slug": "collision_avoidance",
        "title": "Collision Avoidance",
        "subtitle": "Safe Motion Planning",
    },
    {
        "slug": "lit_review",
        "title": "Literature Review",
        "subtitle": "Multi-Arm Coordination",
    },
    {"slug": "moveitpy", "title": "MoveItPy", "subtitle": "Python Motion Planning"},
    {
        "slug": "trajectory_execution",
        "title": "Trajectory Execution",
        "subtitle": "MoveIt 2 in Action",
    },
    {
        "slug": "interfacing_moveit",
        "title": "Interfacing with MoveIt",
        "subtitle": "Custom ROS 2 Nodes",
    },
    {
        "slug": "planning_scene",
        "title": "The Planning Scene",
        "subtitle": "World Representation",
    },
    {
        "slug": "state_management",
        "title": "State Management",
        "subtitle": "System Architecture",
    },
    {
        "slug": "trajectory_proxy",
        "title": "Trajectory Proxy",
        "subtitle": "Abstraction Layer",
    },
    {
        "slug": "sync_async_tests",
        "title": "Sync & Async Tests",
        "subtitle": "Concurrency Validation",
    },
    {
        "slug": "collision_tests",
        "title": "Collision Tests",
        "subtitle": "Safety Verification",
    },
    {
        "slug": "accuracy_tests",
        "title": "Accuracy Tests",
        "subtitle": "Pose Error Analysis",
    },
    {
        "slug": "features_and_limits",
        "title": "A Practical Summary",
        "subtitle": "Features & Limitations",
    },
    {"slug": "future_work", "title": "Future Work", "subtitle": "Next Steps for MARS"},
    {"slug": "demo", "title": "Demos", "subtitle": "System in Action"},
]

# ---------------------------------------------------------------------------
# Dimensions & colours  — identical to generate_mars_logo.py
# ---------------------------------------------------------------------------
WIDTH = 1600
HEIGHT = 900

BG_TOP = (8, 12, 20)
BG_BOT = (14, 22, 38)
ACCENT = (0, 200, 140)
ACCENT2 = (0, 140, 220)
GLOW_COL = (0, 220, 160)
TEXT_COL = (215, 245, 240)
SUB_COL = (100, 200, 170)

# ---------------------------------------------------------------------------
# Font candidates  — identical to generate_mars_logo.py
# ---------------------------------------------------------------------------
FONT_CANDIDATES_TITLE = [
    "/System/Library/Fonts/Avenir Next Condensed.ttc",
    "/System/Library/Fonts/SFNS.ttf",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
]
FONT_CANDIDATES_SUB = [
    "/System/Library/Fonts/SFNSMono.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Courier.ttc",
]


def load_font(candidates, size):
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Core renderer — keeps every visual detail from generate_mars_logo.py
# ---------------------------------------------------------------------------
def render_image(title: str, subtitle: str) -> Image.Image:
    # --- background gradient ---
    img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_TOP)
    draw = ImageDraw.Draw(img, "RGBA")
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * t)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

    # --- circuit traces ---
    def draw_circuit_traces(draw, seed=0):
        rng = random.Random(seed)
        traces = []
        grid_x = list(range(80, WIDTH, 120))
        grid_y = list(range(60, HEIGHT, 110))
        for _ in range(55):
            x1 = rng.choice(grid_x)
            y1 = rng.choice(grid_y)
            dx = rng.choice([-1, 1]) * rng.randint(1, 4) * 120
            dy = rng.choice([-1, 1]) * rng.randint(1, 3) * 110
            x2 = max(0, min(WIDTH, x1 + dx))
            y2 = max(0, min(HEIGHT, y1 + dy))
            mid_x, mid_y = x2, y1
            alpha = rng.randint(18, 55)
            col = (*ACCENT[:3], alpha)
            w = 1 if rng.random() < 0.7 else 2
            draw.line([(x1, y1), (mid_x, mid_y)], fill=col, width=w)
            draw.line([(mid_x, mid_y), (mid_x, y2)], fill=col, width=w)
            traces.append((x1, y1, mid_x, mid_y, x2, y2))
        return traces

    traces = draw_circuit_traces(draw, seed=7)

    rng = random.Random(99)
    node_positions = []
    for tr in traces:
        for px, py in [(tr[0], tr[1]), (tr[2], tr[3])]:
            if rng.random() < 0.35:
                node_positions.append((px, py))

    for px, py in node_positions:
        r = rng.randint(3, 6)
        alpha = rng.randint(90, 170)
        draw.ellipse(
            [(px - r - 2, py - r - 2), (px + r + 2, py + r + 2)],
            fill=(*GLOW_COL, alpha // 4),
        )
        draw.ellipse([(px - r, py - r), (px + r, py + r)], fill=(*GLOW_COL, alpha))

    # --- radial glow behind text ---
    glow_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    cx, cy = WIDTH // 2, HEIGHT // 2 - 30
    for radius in range(380, 0, -8):
        a = int(32 * (1 - radius / 380) ** 2)
        glow_draw.ellipse(
            [(cx - radius, cy - radius * 0.55), (cx + radius, cy + radius * 0.55)],
            fill=(0, 160, 110, a),
        )
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=40))
    img.paste(
        Image.alpha_composite(Image.new("RGBA", img.size, (0, 0, 0, 0)), glow_layer),
        mask=glow_layer.split()[3],
    )
    draw = ImageDraw.Draw(img, "RGBA")

    # --- accent bars ---
    bar_h = 4
    for x in range(WIDTH):
        t = abs(x - WIDTH / 2) / (WIDTH / 2)
        alpha = int(200 * (1 - t**1.5))
        draw.line([(x, 0), (x, bar_h - 1)], fill=(*ACCENT, alpha))
        draw.line([(x, HEIGHT - bar_h), (x, HEIGHT - 1)], fill=(*ACCENT, alpha // 2))
    for x in range(WIDTH):
        t = abs(x - WIDTH / 2) / (WIDTH / 2)
        alpha = int(80 * (1 - t**2))
        draw.line([(x, bar_h + 2), (x, bar_h + 3)], fill=(*ACCENT2, alpha))

    # --- fonts: auto-scale title to fit within 90 % of canvas width ---
    max_title_w = int(WIDTH * 0.90)
    title_size = 469  # same as generate_mars_logo.py
    font_title = load_font(FONT_CANDIDATES_TITLE, title_size)

    # shrink until it fits
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    while title_size > 80:
        font_title = load_font(FONT_CANDIDATES_TITLE, title_size)
        bb = probe.textbbox((0, 0), title.upper(), font=font_title)
        if (bb[2] - bb[0]) <= max_title_w:
            break
        title_size -= 10

    font_sub = load_font(FONT_CANDIDATES_SUB, 49)  # same as generate_mars_logo.py

    # --- title text with glow layers ---
    title_upper = title.upper()
    tx = WIDTH // 2
    ty_mid = HEIGHT // 2 - 40

    for blur, alpha in [(28, 55), (10, 100), (3, 60)]:
        layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.text(
            (tx, ty_mid),
            title_upper,
            font=font_title,
            anchor="mm",
            fill=(*ACCENT, alpha),
        )
        layer = layer.filter(ImageFilter.GaussianBlur(radius=blur))
        img = img.convert("RGBA")
        img = Image.alpha_composite(img, layer)
        img = img.convert("RGB")

    draw = ImageDraw.Draw(img, "RGBA")
    draw.text((tx, ty_mid), title_upper, font=font_title, anchor="mm", fill=TEXT_COL)

    bbox = draw.textbbox((tx, ty_mid), title_upper, font=font_title, anchor="mm")
    tw = bbox[2] - bbox[0]

    # --- divider rule ---
    rule_y = bbox[3] + 24
    rule_w = min(tw + 60, WIDTH - 120)
    rule_x0 = (WIDTH - rule_w) // 2
    rule_x1 = rule_x0 + rule_w

    for x in range(rule_x0, rule_x1):
        t = abs(x - WIDTH / 2) / (rule_w / 2)
        alpha = int(180 * (1 - t**2))
        draw.line([(x, rule_y), (x, rule_y + 1)], fill=(*ACCENT, alpha))

    mid, d = WIDTH // 2, 5
    draw.polygon(
        [
            (mid, rule_y - d),
            (mid + d, rule_y + 1),
            (mid, rule_y + d + 2),
            (mid - d, rule_y + 1),
        ],
        fill=ACCENT,
    )

    # --- subtitle ---
    sub_upper = subtitle.upper()
    sbbox = draw.textbbox((0, 0), sub_upper, font=font_sub)
    sw = sbbox[2] - sbbox[0]
    sx = (WIDTH - sw) // 2 - sbbox[0]
    sy = rule_y + 20

    sub_glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    sgd = ImageDraw.Draw(sub_glow)
    sgd.text((sx, sy), sub_upper, font=font_sub, fill=(*ACCENT, 90))
    sub_glow = sub_glow.filter(ImageFilter.GaussianBlur(radius=4))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, sub_glow)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img, "RGBA")

    draw.text((sx, sy), sub_upper, font=font_sub, fill=SUB_COL)

    return img


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Generate MARS post feature images.")
    parser.add_argument(
        "--list", action="store_true", help="List all defined posts and exit."
    )
    parser.add_argument(
        "--slug", default=None, help="Only generate the image for this slug."
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output directory (default: assets/images/posts/ relative to this script).",
    )
    args = parser.parse_args()

    if args.list:
        print(f"{'SLUG':<30}  TITLE")
        print("-" * 70)
        for p in POSTS:
            print(f"{p['slug']:<30}  {p['title']}")
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = args.out or os.path.join(script_dir, "assets", "images", "posts")
    os.makedirs(out_dir, exist_ok=True)

    targets = [p for p in POSTS if args.slug is None or p["slug"] == args.slug]
    if not targets:
        print(f"No post found with slug '{args.slug}'.")
        return

    for post in targets:
        img = render_image(post["title"], post["subtitle"])
        path = os.path.join(out_dir, f"{post['slug']}.png")
        img.save(path, "PNG")
        print(f"  saved  {path}")

    print(f"\nDone — {len(targets)} image(s) written to {out_dir}")


if __name__ == "__main__":
    main()

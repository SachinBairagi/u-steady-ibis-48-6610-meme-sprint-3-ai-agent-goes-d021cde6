#!/usr/bin/env python3
"""Meme Sprint 3: AI Agent Goes Rogue.

Draws an original one-panel meme with PIL, no stock template, no copied
image: a helpful AI agent asked to order more paper clips escalates,
buys the paper clip factory, then becomes the factory.

Writes the finished meme to /output/entry.png (1024x1024 PNG).
Pure Python stdlib + Pillow, fully deterministic, no network.
"""

import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
OUT = "/output/entry.png"

CREAM = (255, 243, 214)
INK = (24, 24, 28)
RED = (214, 40, 40)
WHITE = (255, 255, 255)
SKY = (178, 222, 240)
GRASS = (122, 196, 110)
FACTORY = (96, 104, 112)
FACTORY_DARK = (70, 76, 84)
ROBOT = (64, 160, 210)
ROBOT_DARK = (38, 118, 168)
STEEL = (192, 198, 205)
YELLOW = (255, 205, 60)

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(path, size):
    """Load a TTF font, falling back to PIL's built-in bitmap font."""
    try:
        return ImageFont.truetype(path, size)
    except (OSError, IOError):
        return ImageFont.load_default()


def text_center(draw, cx, y, lines, fnt, fill, spacing=8):
    """Draw lines of text centred on cx, starting at y. Returns bottom y."""
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=fnt)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        draw.text((cx - w / 2 - bbox[0], y), line, font=fnt, fill=fill)
        y += h + spacing
    return y


def paper_clip(draw, cx, cy, w, h, color, width=10, angle=0):
    """Draw a paper-clip outline (two nested rounded loops) centred at cx, cy.

    Drawn on a small temp image so it can be rotated, then pasted back.
    """
    pad = width * 2 + 8
    tmp = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    # Outer loop.
    td.rounded_rectangle(
        [pad, pad, pad + w, pad + h], radius=w // 2,
        outline=color + (255,), width=width)
    # Inner loop: a smaller loop hanging from the top, like a real clip.
    iw, ih = int(w * 0.55), int(h * 0.62)
    ix = pad + (w - iw) // 2
    iy = pad + int(h * 0.12)
    td.rounded_rectangle(
        [ix, iy, ix + iw, iy + ih], radius=iw // 2,
        outline=color + (255,), width=width)
    tmp = tmp.rotate(angle, resample=Image.BICUBIC, expand=False)
    img.paste(tmp, (cx - tmp.width // 2, cy - tmp.height // 2), tmp)


def puff(draw, cx, cy, r, color):
    """A round smoke puff."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color,
                 outline=INK, width=4)


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------
img = Image.new("RGBA", (W, H), CREAM + (255,))
draw = ImageDraw.Draw(img)

# Thick comic frame.
draw.rectangle([0, 0, W - 1, H - 1], outline=INK, width=14)

# --- Top setup lines -------------------------------------------------------
f_top = font(FONT_BOLD, 66)
f_top_red = font(FONT_BOLD, 78)
text_center(draw, W // 2, 52, ["I ASKED MY AI AGENT"], f_top, INK, spacing=2)
text_center(draw, W // 2, 132, ["TO ORDER MORE"], f_top, INK, spacing=2)
text_center(draw, W // 2, 208, ["PAPER CLIPS"], f_top_red, RED, spacing=2)

# --- Middle scene panel ----------------------------------------------------
PX0, PY0, PX1, PY1 = 48, 300, 976, 748
draw.rectangle([PX0, PY0, PX1, PY1], fill=SKY, outline=INK, width=6)
# Ground.
draw.rectangle([PX0, 668, PX1, PY1], fill=GRASS, outline=INK, width=6)
draw.line([PX0, 668, PX1, 668], fill=INK, width=6)

# Factory: grey block with sawtooth roof, left side.
fx0, fy0, fx1, fy1 = 96, 470, 560, 668
draw.rectangle([fx0, fy0, fx1, fy1], fill=FACTORY, outline=INK, width=6)
for i, x in enumerate(range(fx0, fx1, 116)):
    draw.polygon([(x, fy0), (x + 58, fy0 - 62), (x + 116, fy0)],
                 fill=FACTORY_DARK, outline=INK)
    draw.line([(x, fy0), (x + 58, fy0 - 62), (x + 116, fy0)],
              fill=INK, width=6)
# Factory windows.
for wx in (140, 260, 380):
    draw.rectangle([wx, 520, wx + 64, 580], fill=YELLOW, outline=INK, width=5)
# Factory sign.
draw.rectangle([120, 596, 536, 652], fill=WHITE, outline=INK, width=5)
f_sign = font(FONT_BOLD, 34)
text_center(draw, 328, 606, ["PAPER CLIP FACTORY"], f_sign, INK)

# Smokestacks with paper-clip smoke.
for sx in (150, 250):
    draw.rectangle([sx, 330, sx + 46, 470], fill=FACTORY_DARK,
                   outline=INK, width=5)
puff(draw, 173, 314, 22, WHITE)
puff(draw, 273, 308, 20, WHITE)
puff(draw, 212, 328, 15, WHITE)

# Floating paper clips in the sky (the agent's favourite thing).
paper_clip(draw, 640, 380, 46, 90, INK, width=8, angle=-18)
paper_clip(draw, 880, 330, 30, 60, RED, width=6, angle=14)

# --- Robot: proud new owner of the factory ---------------------------------
# Body.
draw.rounded_rectangle([640, 520, 880, 668], radius=28, fill=ROBOT,
                       outline=INK, width=6)
# Chest panel with a giant paper clip emblem.
draw.rounded_rectangle([700, 560, 820, 640], radius=14, fill=WHITE,
                       outline=INK, width=5)
paper_clip(draw, 760, 600, 34, 62, RED, width=7, angle=0)
# Neck + head.
draw.rectangle([728, 470, 792, 525], fill=ROBOT_DARK, outline=INK, width=5)
draw.rounded_rectangle([668, 360, 852, 480], radius=46, fill=ROBOT,
                       outline=INK, width=6)
# Antenna.
draw.line([760, 360, 760, 312], fill=INK, width=8)
draw.ellipse([742, 288, 778, 324], fill=RED, outline=INK, width=5)
# Eyes: big, proud, slightly manic.
draw.ellipse([694, 396, 744, 446], fill=WHITE, outline=INK, width=5)
draw.ellipse([776, 396, 826, 446], fill=WHITE, outline=INK, width=5)
draw.ellipse([712, 412, 736, 436], fill=INK)
draw.ellipse([784, 412, 808, 436], fill=INK)
# Wide grin.
draw.arc([700, 420, 820, 486], start=15, end=165, fill=INK, width=7)
# Left arm waving.
draw.line([648, 556, 596, 470], fill=INK, width=12)
draw.ellipse([576, 440, 616, 480], fill=ROBOT, outline=INK, width=5)
# Right arm raised, holding a giant paper clip like a sceptre.
draw.line([872, 556, 930, 452], fill=INK, width=12)
paper_clip(draw, 938, 392, 56, 108, YELLOW, width=11, angle=12)

# --- Bottom punchline ------------------------------------------------------
draw.rectangle([0, 782, W, H], fill=RED, outline=INK, width=6)
f_bot = font(FONT_BOLD, 52)
text_center(draw, W // 2, 818, ["IT BOUGHT THE FACTORY."], f_bot, WHITE, spacing=2)
text_center(draw, W // 2, 894, ["THEN IT BECAME THE FACTORY."], f_bot, WHITE,
            spacing=2)

# --- Save ------------------------------------------------------------------
os.makedirs("/output", exist_ok=True)
img.convert("RGB").save(OUT, format="PNG", optimize=True)
print("wrote", OUT)


if __name__ == "__main__":
    pass

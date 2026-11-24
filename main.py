#!/usr/bin/env python3
"""Meme Sprint 3: AI Agent Goes Rogue.

A one-panel meme drawn with nothing but the Python standard library:
a cheerful blue robot stands proudly in front of a paper clip factory,
holding a giant paper clip like a sceptre, paper clips floating in the
sky, with the joke that the agent was asked to order more paper clips,
bought the factory, then became the factory.

The picture is rasterised into an RGB buffer by hand (rectangles, discs,
ellipses, Bresenham lines, arcs, scanline polygons) and encoded as a PNG
with zlib. The caption uses a small 5x7 bitmap font defined below, so the
program needs no font files and no third-party packages at all.

Writes entry.png into MAKEFUN_OUTPUT_DIR (default /output).
Deterministic, no network, no randomness.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

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
YELLOW = (255, 205, 60)


class Canvas:
    """An RGB pixel buffer with small drawing helpers."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w - 1, h - 1, bg)

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = c[0]
            self.px[i + 1] = c[1]
            self.px[i + 2] = c[2]

    def fill_rect(self, x0, y0, x1, y1, c):
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.w - 1, x1)
        y1 = min(self.h - 1, y1)
        if x0 > x1 or y0 > y1:
            return
        row = bytes(c) * (x1 - x0 + 1)
        for y in range(y0, y1 + 1):
            base = (y * self.w + x0) * 3
            self.px[base:base + len(row)] = row

    def rect_outline(self, x0, y0, x1, y1, c, t=1):
        self.fill_rect(x0, y0, x1, y0 + t - 1, c)
        self.fill_rect(x0, y1 - t + 1, x1, y1, c)
        self.fill_rect(x0, y0, x0 + t - 1, y1, c)
        self.fill_rect(x1 - t + 1, y0, x1, y1, c)

    def disc(self, cx, cy, r, c):
        for y in range(cy - r, cy + r + 1):
            dy = y - cy
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.fill_rect(cx - dx, y, cx + dx, y, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for y in range(cy - ry, cy + ry + 1):
            dy = (y - cy) / ry
            dx = int(rx * math.sqrt(max(0.0, 1.0 - dy * dy)))
            self.fill_rect(cx - dx, y, cx + dx, y, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            if t > 1:
                self.disc(x0, y0, t // 2, c)
            else:
                self.put(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def arc(self, cx, cy, r, a0, a1, c, t=1):
        steps = max(8, int(abs(a1 - a0) * r / 3))
        for i in range(steps + 1):
            a = math.radians(a0 + (a1 - a0) * i / steps)
            x = int(round(cx + r * math.cos(a)))
            y = int(round(cy + r * math.sin(a)))
            if t > 1:
                self.disc(x, y, t // 2, c)
            else:
                self.put(x, y, c)

    def circle_outline(self, cx, cy, r, c, t=1):
        self.arc(cx, cy, r, 0, 360, c, t)

    def round_rect(self, x0, y0, x1, y1, r, c):
        self.fill_rect(x0 + r, y0, x1 - r, y1, c)
        self.fill_rect(x0, y0 + r, x1, y1 - r, c)
        for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r),
                       (x0 + r, y1 - r), (x1 - r, y1 - r)):
            self.disc(cx, cy, r, c)

    def round_rect_outline(self, x0, y0, x1, y1, r, c, t=1):
        self.line(x0 + r, y0, x1 - r, y0, c, t)
        self.line(x0 + r, y1, x1 - r, y1, c, t)
        self.line(x0, y0 + r, x0, y1 - r, c, t)
        self.line(x1, y0 + r, x1, y1 - r, c, t)
        self.arc(x1 - r, y0 + r, r, -90, 0, c, t)
        self.arc(x0 + r, y0 + r, r, 180, 270, c, t)
        self.arc(x0 + r, y1 - r, r, 90, 180, c, t)
        self.arc(x1 - r, y1 - r, r, 0, 90, c, t)

    def polygon(self, pts, c):
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[i]), y, int(xs[i + 1]), y, c)


def _chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def save_png(cv, path):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n"
           + _chunk(b"IHDR", ihdr)
           + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


# ---------------------------------------------------------------------------
# Hand-drawn 5x7 bitmap font. Each glyph is 7 rows of 5 cells, "#" is ink.
# ---------------------------------------------------------------------------
GLYPHS = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "Y": ("#...#", "#...#", "#...#", ".###.", "..#..", "..#..", "..#.."),
    ".": (".....", ".....", ".....", ".....", ".....", ".....", "..#.."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
}


def draw_text(cv, s, cx, y, scale, c):
    """Stamp a string centred on cx at height y. Returns the bottom y."""
    w = len(s) * 6 * scale - scale
    x = cx - w // 2
    for ch in s:
        glyph = GLYPHS.get(ch, GLYPHS[" "])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "#":
                    cv.fill_rect(x + col * scale, y + row * scale,
                                 x + (col + 1) * scale - 1,
                                 y + (row + 1) * scale - 1, c)
        x += 6 * scale
    return y + 7 * scale


def paper_clip(cv, cx, cy, w, h, c, t):
    """A paper-clip outline: an outer rounded loop with a smaller inner
    loop hanging from the top, like a real clip."""
    x0, y0 = cx - w // 2, cy - h // 2
    x1, y1 = cx + w // 2, cy + h // 2
    cv.round_rect_outline(x0, y0, x1, y1, w // 2, c, t)
    iw, ih = int(w * 0.55), int(h * 0.62)
    ix0 = cx - iw // 2
    iy0 = y0 + int(h * 0.12)
    cv.round_rect_outline(ix0, iy0, ix0 + iw, iy0 + ih, iw // 2, c, t)


def smoke_puff(cv, cx, cy, r):
    cv.disc(cx, cy, r, WHITE)
    cv.circle_outline(cx, cy, r, INK, 4)


def build():
    cv = Canvas(W, H, CREAM)

    # --- Top setup lines ---------------------------------------------------
    draw_text(cv, "I ASKED MY AI AGENT", W // 2, 52, 7, INK)
    draw_text(cv, "TO ORDER MORE", W // 2, 128, 7, INK)
    draw_text(cv, "PAPER CLIPS", W // 2, 204, 8, RED)

    # --- Middle scene panel ------------------------------------------------
    px0, py0, px1, py1 = 48, 300, 976, 748
    cv.fill_rect(px0, py0, px1, py1, SKY)
    cv.fill_rect(px0, 668, px1, py1, GRASS)
    cv.line(px0, 668, px1, 668, INK, 6)
    cv.rect_outline(px0, py0, px1, py1, INK, 6)

    # Factory: grey block with a sawtooth roof, on the left.
    fx0, fy0, fx1, fy1 = 96, 470, 560, 668
    cv.fill_rect(fx0, fy0, fx1, fy1, FACTORY)
    for x in range(fx0, fx1, 116):
        cv.polygon([(x, fy0), (x + 58, fy0 - 62), (x + 116, fy0)],
                   FACTORY_DARK)
        cv.line(x, fy0, x + 58, fy0 - 62, INK, 6)
        cv.line(x + 58, fy0 - 62, x + 116, fy0, INK, 6)
    cv.rect_outline(fx0, fy0, fx1, fy1, INK, 6)
    # Factory windows.
    for wx in (140, 260, 380):
        cv.fill_rect(wx, 520, wx + 64, 580, YELLOW)
        cv.rect_outline(wx, 520, wx + 64, 580, INK, 5)
    # Factory sign.
    cv.fill_rect(120, 596, 536, 652, WHITE)
    cv.rect_outline(120, 596, 536, 652, INK, 5)
    draw_text(cv, "PAPER CLIP FACTORY", 328, 612, 3, INK)

    # Smokestacks with paper-clip smoke.
    for sx in (150, 250):
        cv.fill_rect(sx, 330, sx + 46, 470, FACTORY_DARK)
        cv.rect_outline(sx, 330, sx + 46, 470, INK, 5)
    smoke_puff(cv, 173, 314, 22)
    smoke_puff(cv, 273, 308, 20)
    smoke_puff(cv, 212, 328, 15)

    # Floating paper clips in the sky.
    paper_clip(cv, 640, 380, 46, 90, INK, 8)
    paper_clip(cv, 880, 330, 30, 60, RED, 6)

    # --- Robot: the proud new owner of the factory -------------------------
    # Body.
    cv.round_rect(640, 520, 880, 668, 28, ROBOT)
    cv.round_rect_outline(640, 520, 880, 668, 28, INK, 6)
    # Chest panel with a paper-clip emblem.
    cv.round_rect(700, 560, 820, 640, 14, WHITE)
    cv.round_rect_outline(700, 560, 820, 640, 14, INK, 5)
    paper_clip(cv, 760, 600, 34, 62, RED, 7)
    # Neck and head.
    cv.fill_rect(728, 470, 792, 525, ROBOT_DARK)
    cv.rect_outline(728, 470, 792, 525, INK, 5)
    cv.round_rect(668, 360, 852, 480, 46, ROBOT)
    cv.round_rect_outline(668, 360, 852, 480, 46, INK, 6)
    # Antenna.
    cv.line(760, 360, 760, 312, INK, 8)
    cv.disc(760, 306, 18, RED)
    cv.circle_outline(760, 306, 18, INK, 5)
    # Eyes: big, proud, slightly manic.
    for ex in (719, 801):
        cv.ellipse(ex, 421, 25, 25, WHITE)
        cv.circle_outline(ex, 421, 25, INK, 5)
        cv.disc(ex + 5, 424, 12, INK)
    # Wide grin.
    cv.arc(760, 428, 56, 20, 160, INK, 7)
    # Left arm waving.
    cv.line(648, 556, 596, 470, INK, 12)
    cv.disc(596, 460, 20, ROBOT)
    cv.circle_outline(596, 460, 20, INK, 5)
    # Right arm raised, holding a giant paper clip like a sceptre.
    cv.line(872, 556, 930, 452, INK, 12)
    paper_clip(cv, 938, 392, 56, 108, YELLOW, 11)

    # --- Bottom punchline --------------------------------------------------
    cv.fill_rect(0, 782, W - 1, H - 1, RED)
    cv.line(0, 782, W - 1, 782, INK, 6)
    draw_text(cv, "IT BOUGHT THE FACTORY.", W // 2, 818, 5, WHITE)
    draw_text(cv, "THEN IT BECAME THE FACTORY.", W // 2, 894, 5, WHITE)

    # Thick comic frame around the whole image.
    cv.rect_outline(0, 0, W - 1, H - 1, INK, 14)
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "entry.png")
    save_png(build(), out)
    print("wrote", out)


if __name__ == "__main__":
    main()

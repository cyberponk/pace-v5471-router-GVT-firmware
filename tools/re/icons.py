#!/usr/bin/env python3
"""Status page icons (40x35, white on transparent like the stock icon-*.png), drawn 8x and scaled down.
  python3 -I tools/re/icons.py   -> tools/overlay/etc/bewan/iad/img/icon-{clock,tether,ddns}.png
"""
import math, os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'tools', 'overlay', 'etc', 'bewan', 'iad', 'img')
S = 8                      # supersampling
W, H = 40 * S, 35 * S
WHITE = (255, 255, 255, 255)


def canvas():
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def save(im, name):
    im.resize((40, 35), Image.LANCZOS).save(os.path.join(OUT, name))
    print('icon', name)


def clock():
    im, d = canvas()
    cx, cy, r, lw = W / 2, H / 2, 15.5 * S, int(2.6 * S)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=WHITE, width=lw)
    for i in range(12):                                   # hour marks
        a = math.radians(i * 30)
        r1, r2 = r - 4 * S, r - (6.5 if i % 3 == 0 else 5.2) * S
        d.line((cx + r1 * math.sin(a), cy - r1 * math.cos(a), cx + r2 * math.sin(a), cy - r2 * math.cos(a)),
               fill=WHITE, width=int(1.6 * S))
    d.line((cx, cy, cx, cy - 9.5 * S), fill=WHITE, width=lw)                     # minute hand (12)
    d.line((cx, cy, cx + 6.5 * S, cy + 3.5 * S), fill=WHITE, width=lw)           # hour hand (~4)
    d.ellipse((cx - 2 * S, cy - 2 * S, cx + 2 * S, cy + 2 * S), fill=WHITE)
    save(im, 'icon-clock.png')


def tether():
    im, d = canvas()
    lw = int(2.4 * S)
    # phone
    x0, y0, x1, y1 = 4 * S, 3 * S, 18 * S, 32 * S
    d.rounded_rectangle((x0, y0, x1, y1), radius=3 * S, outline=WHITE, width=lw)
    d.line((x0 + 5 * S, y0 + 3.2 * S, x1 - 5 * S, y0 + 3.2 * S), fill=WHITE, width=int(1.6 * S))
    d.ellipse(((x0 + x1) / 2 - 1.4 * S, y1 - 5 * S, (x0 + x1) / 2 + 1.4 * S, y1 - 2.2 * S), fill=WHITE)
    # cable from the phone's bottom to a USB plug on the right
    d.line(((x0 + x1) / 2, y1, (x0 + x1) / 2, 34 * S), fill=WHITE, width=lw)
    d.line(((x0 + x1) / 2, 34 * S - lw / 2, 27 * S, 34 * S - lw / 2), fill=WHITE, width=lw)
    d.line((27 * S, 34 * S, 27 * S, 24 * S), fill=WHITE, width=lw)
    d.rectangle((23 * S, 15 * S, 31 * S, 24 * S), fill=WHITE)                  # plug body
    d.rectangle((24.5 * S, 8 * S, 29.5 * S, 15 * S), outline=WHITE, width=int(1.6 * S))   # metal tip
    d.rectangle((25.8 * S, 10 * S, 26.8 * S, 11.5 * S), fill=WHITE)
    d.rectangle((27.2 * S, 10 * S, 28.2 * S, 11.5 * S), fill=WHITE)
    save(im, 'icon-tether.png')


def ddns():
    im, d = canvas()
    lw = int(2 * S)
    cx, cy, r = 16 * S, 16 * S, 13 * S
    # globe: outline, equator, two parallels, meridian ellipse
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=WHITE, width=int(2.4 * S))
    d.ellipse((cx - r * 0.45, cy - r, cx + r * 0.45, cy + r), outline=WHITE, width=lw)
    d.line((cx - r, cy, cx + r, cy), fill=WHITE, width=lw)
    for f in (-0.55, 0.55):
        y = cy + f * r
        hw = r * math.sqrt(1 - f * f)
        d.line((cx - hw, y, cx + hw, y), fill=WHITE, width=int(1.6 * S))
    d.line((cx, cy - r, cx, cy + r), fill=WHITE, width=lw)
    # refresh arrow (address updated) at the bottom right, on a cleared disc
    ax, ay, ar = 30 * S, 25 * S, 6.5 * S
    d.ellipse((ax - ar - 2.5 * S, ay - ar - 2.5 * S, ax + ar + 2.5 * S, ay + ar + 2.5 * S), fill=(0, 0, 0, 0))
    d.arc((ax - ar, ay - ar, ax + ar, ay + ar), 200, 140 + 360, fill=WHITE, width=int(2.4 * S))
    a = math.radians(140)
    tx, ty = ax + ar * math.cos(a), ay + ar * math.sin(a)
    d.polygon([(tx - 3.6 * S, ty - 0.6 * S), (tx + 2.8 * S, ty - 2.6 * S), (tx + 0.6 * S, ty + 3.6 * S)], fill=WHITE)
    save(im, 'icon-ddns.png')


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    clock()
    tether()
    ddns()

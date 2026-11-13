import sys, math, random, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from people import *
ORANGE, BLUE, AQUA = '#D55E00', '#0072B2', '#CC79A7'
from PIL import ImageFont

import os as _os


def _font(bold):
    """Arial (used for the published figures); Liberation Sans is a metric-compatible fallback."""
    names = (["C:/Windows/Fonts/arialbd.ttf", "/Library/Fonts/Arial Bold.ttf",
              "/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"] if bold else
             ["C:/Windows/Fonts/arial.ttf", "/Library/Fonts/Arial.ttf",
              "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"])
    for p in names:
        if _os.path.exists(p):
            return ImageFont.truetype(p, 100)
    raise FileNotFoundError("Arial or Liberation Sans not found; install one of them")


_FR = _font(False)
_FB = _font(True)
def tw(s, size, bold=False):
    return (_FB if bold else _FR).getlength(s) / 100 * size

W, H = 510.24, 340.16            # pt; 180 x 120 mm
S = SVG(W, H, 180, 120)
A = S.add
random.seed(4)
TAKE = 6.8                        # takeaway font size
TAG = 6.5                         # tag font size

# ------------------------------------------------------------------ helpers
def panel_bg(x, y, w, h, c1, c2, id):
    A(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{S.lg(id, c1, c2)}"/>')

def title(x, y, letter, t):
    S.text(x, y, letter, 10.5, 'bold')
    S.text(x + 10, y, t, 8.5, 'bold')

def card(x, y, w, h):
    S.shadow_rect(x, y, w, h, 6, '#ffffff', depth=1.0)

def takeaway(x, y, w, h, s):
    A(f'<line x1="{x+8}" y1="{y+h-12.5}" x2="{x+w-8}" y2="{y+h-12.5}" stroke="{tint(GREY,.35)}" stroke-width=".6"/>')
    S.text(x + w / 2, y + h - 4.2, s, TAKE, 'normal', INK, 'middle')

def tag(cx, cy, label, col=None, train=False):
    """pill centred on (cx, cy). train -> grey pill, else coloured pill."""
    bold = True
    w = tw(label, TAG, bold) + 6; h = 8.4
    if train:
        fill, tc, st = tint(GREY, .45), shade(GREY, .62), f'stroke="{shade(GREY,.12)}" stroke-width=".5"'
    else:
        fill, tc, st = col, '#ffffff', ''
    A(f'<rect x="{cx-w/2:.2f}" y="{cy-h/2:.2f}" width="{w:.2f}" height="{h}" rx="{h/2}" fill="{fill}" {st}/>')
    S.text(cx, cy + 2.35, label, TAG, 'bold', tc, 'middle')
    return w

def bracket(x0, x1, y, col, up=True, sw=.8):
    d = -2.2 if up else 2.2
    A(f'<path d="M{x0:.2f},{y+d:.2f} L{x0:.2f},{y:.2f} L{x1:.2f},{y:.2f} L{x1:.2f},{y+d:.2f}" fill="none" stroke="{col}" stroke-width="{sw}" stroke-linejoin="miter"/>')

def tile(x, y, w, h, col, id=None):
    g = S.lg('t' + col[1:], tint(col, .22), shade(col, .08))
    A(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{min(w,h)*.22:.2f}" fill="{g}"/>'
      f'<rect x="{x+.6:.2f}" y="{y+.5:.2f}" width="{w-1.2:.2f}" height="{h*.32:.2f}" rx="{min(w,h)*.15:.2f}" fill="#fff" fill-opacity=".28"/>')

def strip(x, y, cols, tw_=7.2, th=7, gap=1.4):
    for i, c in enumerate(cols):
        tile(x + i * (tw_ + gap), y, tw_, th, c)

def squiggle(x0, x1, yc, amp, seed=1, n=None, col=INK, sw=.7, op=1):
    rnd = random.Random(seed); pts = []
    n = n or int((x1 - x0) / 1.6)
    for i in range(n + 1):
        t = i / n; xx = x0 + t * (x1 - x0)
        v = math.sin(t * 34 + seed) * .55 + math.sin(t * 81 + 2 * seed) * .3 + rnd.uniform(-.25, .25)
        pts.append(f'{xx:.2f},{yc - amp * v:.2f}')
    A(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{col}" stroke-width="{sw}" stroke-linejoin="round" stroke-opacity="{op}"/>')

def chip(x, y, code, col=ORANGE):
    g = S.lg('chip' + col[1:], tint(col, .15), shade(col, .1))
    A(f'<rect x="{x}" y="{y}" width="17" height="10.5" rx="5.25" fill="{g}"/>')
    S.text(x + 8.5, y + 7.7, code, 7, 'bold', '#ffffff', 'middle')

def arrow(x0, y, x1, c0=BLUE, c1=AQUA, id='arr', sw=2.6):
    g = S.lg(id, c0, c1, x2=1, y2=0)
    A(f'<rect x="{x0}" y="{y-sw/2}" width="{x1-x0-4}" height="{sw}" rx="{sw/2}" fill="{g}"/>'
      f'<path d="M{x1-5.5},{y-4} L{x1+.5},{y} L{x1-5.5},{y+4} Z" fill="{c1}" stroke="{c1}" stroke-width="1" stroke-linejoin="round"/>')

def head(x, y, ang, col, s=1.0):
    """filled arrowhead with tip at (x,y) pointing at angle ang (deg, 0 = right)."""
    a = math.radians(ang); L, Wd = 4.2 * s, 2.0 * s
    bx, by = x - L * math.cos(a), y - L * math.sin(a)
    px, py = -math.sin(a) * Wd, math.cos(a) * Wd
    A(f'<path d="M{x:.2f},{y:.2f} L{bx+px:.2f},{by+py:.2f} L{bx-px:.2f},{by-py:.2f} Z" fill="{col}"/>')

def building(x, y, w, h, col, kind='hospital'):
    gw = S.lg('bw' + col[1:] + kind, tint(col, .88), tint(col, .7))
    if kind == 'hospital':
        A(f'<rect x="{x}" y="{y-h}" width="{w}" height="{h}" rx="1.5" fill="{gw}" stroke="{tint(col,.35)}" stroke-width=".6"/>')
        A(f'<rect x="{x-1}" y="{y-h-2}" width="{w+2}" height="3" rx="1" fill="{tint(col,.25)}"/>')
        for r in range(2):
            for c in range(3):
                A(f'<rect x="{x+3+c*(w-6)/3+1:.2f}" y="{y-h+5+r*7:.2f}" width="{(w-6)/3-2:.2f}" height="4" rx=".6" fill="{tint(col,.45)}"/>')
        A(f'<rect x="{x+w/2-3}" y="{y-6}" width="6" height="6" fill="{tint(col,.3)}"/>')
    else:
        A(f'<path d="M{x},{y} L{x},{y-h*.62} L{x+w/2},{y-h} L{x+w},{y-h*.62} L{x+w},{y} Z" fill="{gw}" stroke="{tint(col,.35)}" stroke-width=".6" stroke-linejoin="round"/>')
        A(f'<path d="M{x-2},{y-h*.58} L{x+w/2},{y-h-2.5} L{x+w+2},{y-h*.58}" fill="none" stroke="{tint(col,.15)}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>')
        A(f'<rect x="{x+4}" y="{y-h*.5}" width="6" height="5" rx=".6" fill="{tint(col,.45)}"/>'
          f'<rect x="{x+w-10}" y="{y-h*.5}" width="6" height="5" rx=".6" fill="{tint(col,.45)}"/>'
          f'<rect x="{x+w/2-3}" y="{y-7}" width="6" height="7" rx=".8" fill="{tint(col,.3)}"/>')

def platform(cx, cy, rx, col):
    g = S.rg('pf' + col[1:], tint(col, .78), tint(col, .9), .5, .4, .7)
    A(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="5.5" fill="{g}"/>')

# ------------------------------------------------------------------ panel a
panel_bg(4, 4, W - 8, 134, '#f3f5f8', '#eef1f5', 'bga')
title(12, 19, 'a', 'Validation tiers')

# global legend (top right): training / test / leakage path
items = []
lx = 0
def leg_w():
    return (9 + 3 + tw('training', 6.8) + 9) + (3 * 7.4 + 2 + tw('test', 6.8) + 9) + (15 + 3 + tw('leakage path', 6.8))
lx = W - 14 - leg_w()
ly = 12
tile(lx, ly, 9, 7, GREY); S.text(lx + 12, ly + 6, 'training', 6.8, fill=MUTED)
lx += 9 + 3 + tw('training', 6.8) + 9
for i, c in enumerate([ORANGE, BLUE, AQUA]):
    tile(lx + i * 7.4, ly, 6.4, 7, c)
S.text(lx + 3 * 7.4 + 2, ly + 6, 'test', 6.8, fill=MUTED)
lx += 3 * 7.4 + 2 + tw('test', 6.8) + 9
A(f'<line x1="{lx}" y1="{ly+3.5}" x2="{lx+11}" y2="{ly+3.5}" stroke="{ORANGE}" stroke-width="1.1" stroke-dasharray="2.2 1.4"/>')
head(lx + 14.5, ly + 3.5, 0, ORANGE, .85)
S.text(lx + 18, ly + 6, 'leakage path', 6.8, fill=MUTED)

cy0, ch, cw = 26, 92, 158
xs = [12, 176, 340]
names = [('Within-subject', ORANGE), ('Subject-independent', BLUE), ('External', AQUA)]
takes = ['Same participants in training and test', 'New participant, same cohort', 'New cohort, site or device']
for (n, c), x, tk in zip(names, xs, takes):
    card(x, cy0, cw, ch)
    A(f'<path d="M{x},{cy0+6} A6,6 0 0 1 {x+6},{cy0} L{x+cw-6},{cy0} A6,6 0 0 1 {x+cw},{cy0+6} L{x+cw},{cy0+3.4} L{x},{cy0+3.4} Z" fill="{c}"/>')
    S.text(x + 8, cy0 + 15, n, 8, 'bold', shade(c, .12))
    takeaway(x, cy0, cw, ch, tk)
S.text(xs[0] + 8 + tw('Within-subject', 8, True) + 3, cy0 + 15, 'or record-wise', 7, 'normal', MUTED)

# a1: one participant; train and test windows both cut from own recording
x = xs[0]
gy_ = cy0 + 70
platform(x + 25, gy_, 19, GREY)
person(S, x + 25, gy_, .48, tint(INK, .55), scol=MUTED)
pat = [[GREY, GREY, ORANGE, GREY, GREY, GREY, ORANGE, GREY, GREY, GREY, ORANGE],
       [GREY, ORANGE, GREY, GREY, GREY, ORANGE, GREY, GREY, GREY, ORANGE, GREY]]
sx0, tw_, gp = x + 55, 7.4, 1.3
rows_y = [cy0 + 25, cy0 + 42]
for r, cols in enumerate(pat):
    yy = rows_y[r]
    strip(sx0, yy, cols, tw_, 9, gp)
    squiggle(sx0 + .5, sx0 + 11 * (tw_ + gp) - 1.8, yy + 4.5, 3.2, seed=3 + r, col='#ffffff', sw=.75, op=.95)
# connectors from the sensor to both recordings
sxp, syp = x + 30.5, cy0 + 65.5
for yy in rows_y:
    A(f'<path d="M{sxp},{syp} C{x+44},{syp} {x+44},{yy+4.5} {sx0-2},{yy+4.5}" fill="none" stroke="{MUTED}" stroke-width=".75" stroke-dasharray="1.6 1.4"/>')
# tags under row 2
c_tr = sx0 + 2 * (tw_ + gp) + tw_ / 2
c_te = sx0 + 5 * (tw_ + gp) + tw_ / 2
yb2 = rows_y[1] + 9
for cxx, lab, tr in [(c_tr, 'train', True), (c_te, 'test', False)]:
    A(f'<line x1="{cxx:.2f}" y1="{yb2+1}" x2="{cxx:.2f}" y2="{yb2+5.2}" stroke="{ORANGE if not tr else shade(GREY,.25)}" stroke-width=".7"/>')
    tag(cxx, yb2 + 9.4, lab, ORANGE, train=tr)

# a2: held-out participant from the same cohort
x = xs[1]
gy_ = cy0 + 62
platform(x + 79, gy_, 70, GREY)
for i, (px, col, hal) in enumerate([(x + 24, GREY, None), (x + 56, GREY, None), (x + 88, GREY, None), (x + 133, BLUE, BLUE)]):
    person(S, px, gy_, .42, col, pose='stand' if i % 2 else 'walk', scol=shade(GREY, .3) if col == GREY else BLUE, halo=hal)
A(f'<line x1="{x+111}" y1="{cy0+22}" x2="{x+111}" y2="{cy0+74}" stroke="{MUTED}" stroke-width=".7" stroke-dasharray="2 1.6"/>')
yt = cy0 + 70.5
bracket(x + 12, x + 100, yt - 3.2, shade(GREY, .2), up=True)
A(f'<rect x="{x+44}" y="{yt-5}" width="24" height="4" fill="#ffffff"/>')
tag(x + 56, yt, 'train', train=True)
tag(x + 133, yt, 'test', BLUE)

# a3: new cohort / site / device
x = xs[2]
gy_ = cy0 + 62
building(x + 23, gy_ - 6, 34, 24, GREY, 'hospital')
building(x + 110, gy_ - 6, 30, 26, AQUA, 'house')
platform(x + 42, gy_, 38, GREY)
platform(x + 124, gy_, 30, AQUA)
for px, col, pose in [(x + 18, GREY, 'stand'), (x + 66, GREY, 'walk')]:
    person(S, px, gy_, .42, col, pose=pose, scol=shade(GREY, .3))
for px, col, pose in [(x + 103, AQUA, 'walk'), (x + 145, AQUA, 'stand')]:
    person(S, px, gy_, .42, col, pose=pose, scol=AQUA, trousers='#3d4f5e', hair='#b9b2a6')
A(f'<line x1="{x+88}" y1="{cy0+22}" x2="{x+88}" y2="{cy0+74}" stroke="{MUTED}" stroke-width=".7" stroke-dasharray="2 1.6"/>')
bracket(x + 8, x + 80, yt - 3.2, shade(GREY, .2), up=True)
A(f'<rect x="{x+32}" y="{yt-5}" width="24" height="4" fill="#ffffff"/>')
tag(x + 44, yt, 'train', train=True)
bracket(x + 95, x + 152, yt - 3.2, AQUA, up=True)
A(f'<rect x="{x+113}" y="{yt-5}" width="22" height="4" fill="#ffffff"/>')
tag(x + 124, yt, 'test', AQUA)

# independence arrow
ya = 127.5
g = S.lgn('indep', [(0, ORANGE), (.5, BLUE), (1, AQUA)])
A(f'<rect x="14" y="{ya-1.5}" width="482" height="3" rx="1.5" fill="{g}"/>'
  f'<path d="M492,{ya-5} L500,{ya} L492,{ya+5} Z" fill="{AQUA}" stroke="{AQUA}" stroke-linejoin="round"/>')
A(f'<rect x="205" y="{ya-5.5}" width="100" height="11" rx="5.5" fill="#ffffff"/>')
S.text(255, ya + 2.4, 'Increasing independence', 6.8, 'bold', INK, 'middle')

# ------------------------------------------------------------------ panel b
bx, by, bw, bh = 4, 142, 272, 194
panel_bg(bx, by, bw, bh, '#fdf3ee', '#fbeee7', 'bgb')
title(12, by + 15, 'b', 'Leakage indicators')
cw2, ch2 = 125, 82
gx = [12, 12 + cw2 + 6]; gy = [by + 22, by + 22 + ch2 + 5]
cards_b = [('L1', 'Window overlap', 'Overlapping windows split across sets'),
           ('L2', 'Preprocessing leakage', 'Scaling fitted on test data'),
           ('L3', 'Test-data tuning', 'Threshold chosen on test score'),
           ('L4', 'Participant overlap', 'Same person in both sets')]
pos = [(gx[0], gy[0]), (gx[1], gy[0]), (gx[0], gy[1]), (gx[1], gy[1])]
for (code, name, tk), (x, y) in zip(cards_b, pos):
    card(x, y, cw2, ch2)
    chip(x + 6, y + 6, code)
    S.text(x + 27, y + 14, name, 7.4, 'bold')
    takeaway(x, y, cw2, ch2, tk)

# L1 window overlap
x, y = pos[0]
x1a, x1b = x + 12, x + 66        # train window
x2a, x2b = x + 50, x + 104       # test window
yc = y + 42
A(f'<rect x="{x1a}" y="{y+25}" width="{x1b-x1a}" height="31" rx="3" fill="{tint(GREY,.55)}" fill-opacity=".8" stroke="{shade(GREY,.25)}" stroke-width=".9"/>')
A(f'<rect x="{x2a}" y="{y+29}" width="{x2b-x2a}" height="31" rx="3" fill="{tint(ORANGE,.78)}" fill-opacity=".6" stroke="{ORANGE}" stroke-width=".9" stroke-dasharray="2.4 1.4"/>')
S.d(f'<pattern id="hatch" width="3" height="3" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="3" height="3" fill="{tint(ORANGE,.55)}"/><line x1="0" y1="0" x2="0" y2="3" stroke="{ORANGE}" stroke-width="1.1"/></pattern>')
A(f'<rect x="{x2a}" y="{y+29}" width="{x1b-x2a}" height="27" fill="url(#hatch)" fill-opacity=".9"/>')
squiggle(x + 7, x + 118, yc, 8, seed=7, col=INK, sw=.85)
bracket(x1a, x1b, y + 21.5, shade(GREY, .45), up=False, sw=1)
S.text(x1b + 3.5, y + 24, 'train window', TAG, 'bold', shade(GREY, .55))
bracket(x2a, x2b, y + 63.5, ORANGE, up=True, sw=1)
S.text(x2a - 3.5, y + 66, 'test window', TAG, 'bold', ORANGE, 'end')

# L2 scaler fitted on train AND test
x, y = pos[1]
fx = x + 62
strip(x + 10, y + 21, [GREY, GREY, GREY, GREY], 7, 7, 1.3)
strip(x + 90, y + 21, [ORANGE, ORANGE, ORANGE], 7, 7, 1.3)
tag(x + 10 + 16.4, y + 35, 'train', train=True)
tag(x + 90 + 11.0, y + 35, 'test', ORANGE)
# arrows into the scaler
A(f'<path d="M{x+38},{y+35} C{x+46},{y+35} {fx-14},{y+36} {fx-11},{y+42}" fill="none" stroke="{shade(GREY,.3)}" stroke-width="1.1"/>')
head(fx - 10.2, y + 43.6, 62, shade(GREY, .3))
A(f'<path d="M{x+92},{y+35} C{x+84},{y+35} {fx+14},{y+36} {fx+11},{y+42}" fill="none" stroke="{ORANGE}" stroke-width="1.3"/>')
head(fx + 10.2, y + 43.6, 118, ORANGE)
gf = S.lgn('funnel', [(0, shade(BLUE, .25)), (.35, tint(BLUE, .25)), (.7, BLUE), (1, shade(BLUE, .3))])
ft = y + 46
A(f'<path d="M{fx-16},{ft} L{fx+16},{ft} L{fx+3.6},{ft+11} L{fx+3.6},{ft+17} Q{fx},{ft+19.5} {fx-3.6},{ft+17} L{fx-3.6},{ft+11} Z" fill="{gf}"/>')
A(f'<ellipse cx="{fx}" cy="{ft}" rx="16" ry="3.4" fill="{tint(BLUE,.55)}" stroke="{shade(BLUE,.2)}" stroke-width=".6"/>'
  f'<ellipse cx="{fx}" cy="{ft+.5}" rx="12.6" ry="2.2" fill="{shade(BLUE,.35)}"/>')
for dx, dy in [(-5, 2.2), (3, 2.8), (7, 1.4)]:
    A(f'<circle cx="{fx+dx}" cy="{ft+dy}" r="1.05" fill="{ORANGE}"/>')
for dx, dy in [(-9, 1.0), (-1.5, 1.8)]:
    A(f'<circle cx="{fx+dx}" cy="{ft+dy}" r="1.05" fill="{GREY}"/>')
S.text(fx + 20, ft + 11.5, 'scaler', TAG, 'bold', shade(BLUE, .2))

# L3 threshold chosen on test score (score-versus-threshold curve, as in Style 2)
x, y = pos[2]
ax0, ax1 = x + 24, x + 112          # x-axis extent
ay0, ay1 = y + 58, y + 25           # y: bottom, top
import math as _m
pts = []
for k in range(61):
    t = k / 60
    v = 0.30 + 0.55 * _m.exp(-((t - 0.36) / 0.20) ** 2) + 0.06 * _m.sin(9 * t) * (1 - t) - 0.18 * t
    pts.append((ax0 + t * (ax1 - ax0), ay0 - max(0.05, min(0.98, v)) * (ay0 - ay1)))
pk = min(pts, key=lambda q: q[1])
area = f"M{pts[0][0]:.2f},{ay0} " + " ".join(f"L{a:.2f},{b:.2f}" for a, b in pts) + f" L{pts[-1][0]:.2f},{ay0} Z"
A(f'<path d="{area}" fill="{S.lg("l3area", tint(ORANGE,.55), tint(ORANGE,.92))}" fill-opacity=".9"/>')
A('<polyline points="' + " ".join(f"{a:.2f},{b:.2f}" for a, b in pts) + f'" fill="none" stroke="{INK}" stroke-width="1.1" stroke-linejoin="round"/>')
# axes
A(f'<line x1="{ax0}" y1="{ay0}" x2="{ax1+3}" y2="{ay0}" stroke="{MUTED}" stroke-width=".8"/>'
  f'<line x1="{ax0}" y1="{ay0}" x2="{ax0}" y2="{ay1-3}" stroke="{MUTED}" stroke-width=".8"/>')
head(ax1 + 4.2, ay0, 0, MUTED); head(ax0, ay1 - 4.2, -90, MUTED)
S.text((ax0 + ax1) / 2, ay0 + 7.0, "threshold", TAG, "normal", MUTED, "middle")
A(f'<text x="{ax0-4.5}" y="{(ay0+ay1)/2}" font-family="Liberation Sans, Arial, sans-serif" font-size="{TAG}" fill="{ORANGE}" font-weight="bold" text-anchor="middle" transform="rotate(-90 {ax0-4.5} {(ay0+ay1)/2})">test score</text>')
# chosen threshold at test-set peak
A(f'<line x1="{pk[0]:.2f}" y1="{pk[1]:.2f}" x2="{pk[0]:.2f}" y2="{ay0}" stroke="{ORANGE}" stroke-width="1" stroke-dasharray="2.2 1.4"/>')
A(f'<circle cx="{pk[0]:.2f}" cy="{pk[1]:.2f}" r="2.6" fill="{ORANGE}" stroke="#fff" stroke-width=".8"/>')
S.text(pk[0] + 5, pk[1] + 1.5, 'chosen on test', TAG, 'bold', ORANGE)

# L4 same participant in both sets
x, y = pos[3]
bt, bb = y + 31, y + 66
A(f'<rect x="{x+6}" y="{bt}" width="46" height="{bb-bt}" rx="5" fill="{tint(GREY,.72)}" stroke="{tint(GREY,.1)}" stroke-width=".7"/>')
A(f'<rect x="{x+92}" y="{bt}" width="27" height="{bb-bt}" rx="5" fill="{tint(ORANGE,.85)}" stroke="{tint(ORANGE,.3)}" stroke-width=".7"/>')
for i, col in enumerate([GREY, GREY, ORANGE]):
    person(S, x + 15 + i * 14, bb - 3, .28, col, pose='stand', sensor=None)
person(S, x + 105.5, bb - 3, .28, ORANGE, pose='stand', sensor=None)
tag(x + 29, bt - .6, 'train', train=True)
tag(x + 105.5, bt - .6, 'test', ORANGE)
ay = bt + 16
A(f'<line x1="{x+49}" y1="{ay}" x2="{x+100}" y2="{ay}" stroke="{ORANGE}" stroke-width="1.1" stroke-dasharray="2.2 1.4"/>')
head(x + 101.5, ay, 0, ORANGE)
A(f'<rect x="{x+71.5-(tw("same person", TAG, True)+3)/2}" y="{ay-11.5}" width="{tw("same person", TAG, True)+3}" height="8" rx="2" fill="#ffffff"/>')
S.text(x + 71.5, ay - 4.8, 'same person', TAG, 'bold', ORANGE, 'middle')

# ------------------------------------------------------------------ panel c
cx0 = 280
panel_bg(cx0, by, W - 4 - cx0, bh, '#eef4fb', '#eaf6f1', 'bgc')
title(cx0 + 8, by + 15, 'c', 'Acquisition shift')
# development -> intended use header
hx = W - 12
w2 = tw('intended use', TAG, True) + 8; w1 = tw('development', TAG, True) + 8
hy = by + 11.6
A(f'<rect x="{hx-w2}" y="{hy-4.4}" width="{w2}" height="8.8" rx="4.4" fill="{AQUA}"/>')
S.text(hx - w2 / 2, hy + 2.35, 'intended use', TAG, 'bold', '#ffffff', 'middle')
ax1 = hx - w2 - 15
arrow(ax1, hy, ax1 + 11, id='ca_h', sw=2.2)
A(f'<rect x="{ax1-3-w1}" y="{hy-4.4}" width="{w1}" height="8.8" rx="4.4" fill="{BLUE}"/>')
S.text(ax1 - 3 - w1 / 2, hy + 2.35, 'development', TAG, 'bold', '#ffffff', 'middle')

cw3 = (W - 4 - cx0 - 16 - 6) / 2
gxc = [cx0 + 8, cx0 + 8 + cw3 + 6]
posc = [(gxc[0], gy[0]), (gxc[1], gy[0]), (gxc[0], gy[1]), (gxc[1], gy[1])]
SC = cw3 / 113.0
cards_c = [('Setting', 'Laboratory → home'), ('Sensor placement', 'Ankle → wrist or waist'),
           ('Sensor orientation', 'Sensor rotated'), ('Device or cohort', 'New device or population')]
for (name, tk), (x, y) in zip(cards_c, posc):
    card(x, y, cw3, ch2)
    S.text(x + 7, y + 14, name, 7.4, 'bold')
    takeaway(x, y, cw3, ch2, tk)
    # colour bars: development (left) / intended use (right)
    A(f'<line x1="{x+6*SC+2}" y1="{y+64.5}" x2="{x+48*SC-2}" y2="{y+64.5}" stroke="{BLUE}" stroke-width="1.6" stroke-linecap="round"/>'
      f'<line x1="{x+65*SC+2}" y1="{y+64.5}" x2="{x+107*SC-2}" y2="{y+64.5}" stroke="{AQUA}" stroke-width="1.6" stroke-linecap="round"/>')

def grp(x, y):   # local 113-wide design space -> card
    A(f'<g transform="translate({x:.2f},{y-3.6:.2f}) scale({SC:.4f})">')
def endg():
    A('</g>')

def lab_room(x, y, w, h):
    col = BLUE
    A(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{S.lg("labw", tint(col,.86), tint(col,.75))}"/>')
    A(f'<path d="M{x},{y+h*.68} L{x+w},{y+h*.68} L{x+w},{y+h-3} Q{x+w},{y+h} {x+w-3},{y+h} L{x+3},{y+h} Q{x},{y+h} {x},{y+h-3} Z" fill="{tint(col,.62)}"/>')
    for k in range(1, 6):
        A(f'<line x1="{x+k*w/6:.2f}" y1="{y+h*.68}" x2="{x+k*w/6 + (k-3)*2.2:.2f}" y2="{y+h}" stroke="#fff" stroke-opacity=".6" stroke-width=".5"/>')
    A(f'<line x1="{x}" y1="{y+h*.84}" x2="{x+w}" y2="{y+h*.84}" stroke="#fff" stroke-opacity=".6" stroke-width=".5"/>')
    A(f'<line x1="{x+4}" y1="{y+h*.9}" x2="{x+8}" y2="{y+h*.76}" stroke="{shade(BLUE,.3)}" stroke-width="1"/>'
      f'<line x1="{x+w-5}" y1="{y+h*.9}" x2="{x+w-8}" y2="{y+h*.76}" stroke="{shade(BLUE,.3)}" stroke-width="1"/>')
    A(f'<circle cx="{x+w-8}" cy="{y+8}" r="3.6" fill="#fff" stroke="{shade(col,.2)}" stroke-width=".6"/>'
      f'<path d="M{x+w-8},{y+6} L{x+w-8},{y+8} L{x+w-6.6},{y+9}" stroke="{INK}" stroke-width=".5" fill="none"/>')
    A(f'<rect x="{x+3.5}" y="{y+7}" width="7" height="4.6" rx=".8" fill="{INK}"/><circle cx="{x+9.6}" cy="{y+9.3}" r="1.3" fill="{tint(col,.4)}"/>'
      f'<path d="M{x+7},{y+11.6} L{x+4},{y+h*.68+3} M{x+7},{y+11.6} L{x+10},{y+h*.68+3} M{x+7},{y+11.6} L{x+7},{y+h*.68+2}" stroke="{INK}" stroke-width=".55"/>')
    person(S, x + w / 2, y + h - 4, .29, tint(INK, .55), scol=BLUE)

def home_room(x, y, w, h):
    A(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{S.lg("homew", "#fbf4e8", "#f5ead9")}"/>')
    A(f'<path d="M{x},{y+h*.7} L{x+w},{y+h*.7} L{x+w},{y+h-3} Q{x+w},{y+h} {x+w-3},{y+h} L{x+3},{y+h} Q{x},{y+h} {x},{y+h-3} Z" fill="{S.lg("floorh", "#e0c49a", "#c9a676")}"/>')
    for k in range(1, 4):
        A(f'<line x1="{x}" y1="{y+h*.7+k*h*.075:.2f}" x2="{x+w}" y2="{y+h*.7+k*h*.075:.2f}" stroke="#fff" stroke-opacity=".35" stroke-width=".45"/>')
    A(f'<rect x="{x+4}" y="{y+5}" width="13" height="11" rx="1" fill="{S.lg("sky", tint(BLUE,.55), tint(BLUE,.8))}" stroke="#fff" stroke-width="1.1"/>'
      f'<line x1="{x+10.5}" y1="{y+5}" x2="{x+10.5}" y2="{y+16}" stroke="#fff" stroke-width=".8"/>')
    A(f'<rect x="{x+w-21}" y="{y+h*.7-9}" width="19" height="9" rx="2.4" fill="{S.lg("sofa", tint(AQUA,.2), shade(AQUA,.15))}"/>'
      f'<rect x="{x+w-22.5}" y="{y+h*.7-5.5}" width="4" height="6.5" rx="1.6" fill="{shade(AQUA,.2)}"/>'
      f'<rect x="{x+w-5.5}" y="{y+h*.7-5.5}" width="4" height="6.5" rx="1.6" fill="{shade(AQUA,.2)}"/>')
    A(f'<path d="M{x+w-26},{y+h*.7+1} L{x+w-28.5},{y+h*.7-5} L{x+w-23.5},{y+h*.7-5} Z" fill="#c9a676"/>'
      f'<path d="M{x+w-26},{y+h*.7-5} q-4,-6 -2,-9 M{x+w-26},{y+h*.7-5} q3,-5 4,-8 M{x+w-26},{y+h*.7-5} q0,-6 1,-10" stroke="{shade(AQUA,.25)}" stroke-width="1.3" fill="none" stroke-linecap="round"/>')
    A(f'<ellipse cx="{x+w/2}" cy="{y+h-4}" rx="{w*.36}" ry="2.6" fill="{tint(AQUA,.6)}"/>')
    person(S, x + w / 2 - 3, y + h - 4, .29, AQUA, scol=AQUA)

# setting
x, y = posc[0]
grp(x, y)
lab_room(6, 24, 42, 44)
arrow(51.5, 46, 61.5, id='ca')
home_room(65, 24, 42, 44)
endg()

# placement
x, y = posc[1]
grp(x, y)
platform(28, 70, 18, BLUE); platform(86, 70, 18, AQUA)
person(S, 28, 70, .47, tint(INK, .55), scol=BLUE)
person(S, 86, 70, .47, tint(INK, .55), pose='stand', sensor='wrist', scol=AQUA)
person(S, 86, 70, .47, tint(INK, .55), pose='stand', sensor='waist', scol=AQUA)
A(f'<circle cx="33.4" cy="66" r="5.6" fill="none" stroke="{BLUE}" stroke-width=".8" stroke-dasharray="1.5 1"/>')
A(f'<circle cx="90.5" cy="47.6" r="5" fill="none" stroke="{AQUA}" stroke-width=".8" stroke-dasharray="1.5 1"/>')
arrow(51.5, 46, 61.5, id='ca')
endg()

# orientation
def imu(cx, cy, rot, col, s=1.0, idn='i'):
    g1 = S.lg('cubeT' + idn, tint(col, .45), tint(col, .25))
    g2 = S.lg('cubeF' + idn, tint(col, .1), shade(col, .1))
    g3 = S.lg('cubeS' + idn, shade(col, .18), shade(col, .32))
    A(f'<g transform="translate({cx},{cy}) rotate({rot}) scale({s})">')
    A(f'<path d="M-10,-4 L0,-9 L12,-5 L2,0 Z" fill="{g1}"/>'
      f'<path d="M-10,-4 L2,0 L2,11 L-10,7 Z" fill="{g2}"/>'
      f'<path d="M2,0 L12,-5 L12,6 L2,11 Z" fill="{g3}"/>'
      f'<circle cx="-6.5" cy="0.8" r="1.1" fill="#fff"/>')
    for (dx, dy, c) in [(21, -8, INK), (-2, -21, INK), (-15, 10, INK)]:
        A(f'<line x1="1" y1="0" x2="{dx}" y2="{dy}" stroke="{shade(col,.35)}" stroke-width="1.15" marker-end="url(#ah{col[1:]})"/>')
    A('</g>')
for c in [BLUE, AQUA]:
    S.d(f'<marker id="ah{c[1:]}" viewBox="0 0 6 6" refX="5" refY="3" markerWidth="4" markerHeight="4" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="{shade(c,.35)}"/></marker>')
x, y = posc[2]
grp(x, y)
imu(25, 50, 0, BLUE, 1.0, 'a')
imu(88, 49, -35, AQUA, 1.0, 'b')
# rotation cue
A(f'<path d="M100,30 A15,15 0 0 1 104,52" fill="none" stroke="{AQUA}" stroke-width="1.1"/>')
endg()
x, y = posc[2]
A(f'<path d="M{x+(104)*SC:.2f},{y-3.6+52*SC:.2f} l-1.2,-3.6 l3.2,1.1 z" fill="{AQUA}"/>')
grp(x, y)
arrow(51.5, 46, 61.5, id='ca')
endg()

# device / cohort
def bust(cx, cy, col, s=1):
    A(f'<g transform="translate({cx},{cy}) scale({s})"><path d="M-6,8 Q-6,1 0,1 Q6,1 6,8 Z" fill="{S.lg("bu"+col[1:], tint(col,.15), shade(col,.12))}"/>'
      f'<circle cx="0" cy="-3.4" r="3.8" fill="{S.rg("skin", "#f7d3b2", "#e2a67c")}"/></g>')
x, y = posc[3]
grp(x, y)
A(f'<rect x="12" y="31.5" width="30" height="5" rx="2.5" fill="#2d3748"/>'
  f'<rect x="18" y="26" width="18" height="16" rx="3.5" fill="{S.lg("dev1", tint(BLUE,.25), shade(BLUE,.2))}"/>'
  f'<rect x="20" y="28" width="14" height="4" rx="1.6" fill="#fff" fill-opacity=".35"/>'
  f'<circle cx="32" cy="38" r="1.1" fill="#fff"/>')
wx, wy = 86, 35
A(f'<g transform="translate({wx},{wy}) scale(.82) translate({-wx},{-wy})">')
A(f'<path d="M{wx-6},{wy-16} L{wx+6},{wy-16} L{wx+5},{wy-8} L{wx-5},{wy-8} Z M{wx-5},{wy+8} L{wx+5},{wy+8} L{wx+6},{wy+16} L{wx-6},{wy+16} Z" fill="{shade(AQUA,.35)}"/>'
  f'<rect x="{wx-9}" y="{wy-10}" width="18" height="20" rx="5" fill="{S.lg("wat", "#4b5563", INK)}"/>'
  f'<rect x="{wx-7}" y="{wy-8}" width="14" height="16" rx="3.6" fill="{S.lg("scr", tint(AQUA,.2), shade(AQUA,.25))}"/>'
  f'<rect x="{wx+9}" y="{wy-3}" width="1.8" height="4" rx=".8" fill="#4b5563"/>'
  f'<polyline points="{wx-5},{wy+1} {wx-2.5},{wy+1} {wx-1},{wy-3.5} {wx+1},{wy+4} {wx+2.6},{wy+1} {wx+5},{wy+1}" fill="none" stroke="#fff" stroke-width=".9" stroke-linejoin="round"/></g>')
for i in range(3):
    bust(15 + i * 12, 60, [BLUE, shade(BLUE, .2), tint(BLUE, .3)][i])
for i in range(3):
    bust(74 + i * 12, 60, [AQUA, shade(AQUA, .2), tint(AQUA, .3)][i])
arrow(51.5, 46, 61.5, id='ca')
endg()

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fig1_mechanisms.svg'), 'w', encoding='utf-8').write(S.out())

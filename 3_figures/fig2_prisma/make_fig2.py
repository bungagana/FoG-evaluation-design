"""PRISMA 2020 flow diagram (new systematic review, databases and registers only)."""
from xml.sax.saxutils import escape
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


FR = _font(False)
FB = _font(True)
def tw(s, size, bold=False): return (FB if bold else FR).getlength(s) / 100 * size

MM = 72 / 25.4
W, H = 130 * MM, 150 * MM
INK, BAR, LINE, HEAD = '#1f2933', '#3f6fb5', '#1f2933', '#dde7f5'
FS = 6.9; LH = FS * 1.28
out = []
A = out.append

def text(x, y, s, size=FS, bold=False, anchor='start', fill=INK):
    A(f'<text x="{x:.2f}" y="{y:.2f}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" '
      f'font-weight="{"bold" if bold else "normal"}" fill="{fill}" text-anchor="{anchor}">{escape(s)}</text>')

def box(x, y, w, h, lines, center=False, fill='#ffffff'):
    """lines: list of (text, bold, indent)."""
    A(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}" stroke="{LINE}" stroke-width="0.8"/>')
    n = len(lines); top = y + (h - n * LH) / 2 + FS * 0.92
    for i, (s, b, ind) in enumerate(lines):
        if center: text(x + w / 2, top + i * LH, s, bold=b, anchor='middle')
        else: text(x + 6 + ind, top + i * LH, s, bold=b)

def arrow(x1, y1, x2, y2):
    A(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{LINE}" stroke-width="0.8"/>')
    import math
    a = math.atan2(y2 - y1, x2 - x1); L, Wd = 4.2, 1.9
    bx, by = x2 - L * math.cos(a), y2 - L * math.sin(a)
    px, py = -math.sin(a) * Wd, math.cos(a) * Wd
    A(f'<path d="M{x2:.2f},{y2:.2f} L{bx+px:.2f},{by+py:.2f} L{bx-px:.2f},{by-py:.2f} Z" fill="{LINE}"/>')

def phase(y, h, label):
    A(f'<rect x="2" y="{y:.2f}" width="16" height="{h:.2f}" rx="2.5" fill="{BAR}"/>')
    cx, cy = 10, y + h / 2
    A(f'<text x="{cx}" y="{cy}" font-family="Arial, Helvetica, sans-serif" font-size="{FS+0.6}" font-weight="bold" '
      f'fill="#ffffff" text-anchor="middle" dominant-baseline="central" transform="rotate(-90 {cx} {cy})">{label}</text>')

LX, LW = 26, 160          # left column
RX, RW = 204, W - 204 - 4  # right column
B = '• '
# header
A(f'<rect x="{LX}" y="2" width="{W-LX-4:.2f}" height="17" rx="2.5" fill="{HEAD}" stroke="{BAR}" stroke-width="0.8"/>')
text(LX + (W - LX - 4) / 2, 13.6, 'Identification of studies via databases and registers', FS + 0.6, True, 'middle')

# --- Identification
y0 = 27
idL = [('Records identified from:', True, 0), ('Databases (n = 1,663)', False, 0), (B + 'PubMed (n = 321)', False, 6),
       (B + 'IEEE Xplore (n = 229)', False, 6), (B + 'Scopus (n = 1,113)', False, 6), ('Registers (n = 0)', False, 0)]
idR = [('Records removed before screening:', True, 0), ('Duplicate records removed (n = 521)', False, 0),
       ('Records marked as ineligible by', False, 0), ('automation tools (n = 0)', False, 0),
       ('Records removed for other reasons', False, 0), ('(n = 217): published before 2018', False, 0)]
hI = len(idR) * LH + 10
box(LX, y0, LW, hI, idL); box(RX, y0, RW, hI, idR)
arrow(LX + LW, y0 + hI / 2, RX, y0 + hI / 2)
phase(y0, hI, 'Identification')

# --- Screening
y1 = y0 + hI + 16
scrR = [('Records excluded (n = 825):', True, 0), (B + 'Not about freezing of gait (n = 296)', False, 0),
        (B + 'Not a peer-reviewed primary study (n = 224)', False, 0), (B + 'Intervention study without a model (n = 75)', False, 0),
        (B + 'No wearable or vision input (n = 65)', False, 0), (B + 'Task out of scope (n = 65)', False, 0),
        (B + 'No automated model (n = 63)', False, 0), (B + 'Population out of scope (n = 37)', False, 0)]
hR1 = len(scrR) * LH + 10
hL1 = 2 * LH + 10
box(LX, y1 + (hR1 - hL1) / 2, LW, hL1, [('Records screened', True, 0), ('(n = 925)', False, 0)], center=True)
box(RX, y1, RW, hR1, scrR)
arrow(LX + LW / 2, y0 + hI, LX + LW / 2, y1 + (hR1 - hL1) / 2)
arrow(LX + LW, y1 + hR1 / 2, RX, y1 + hR1 / 2)
yA = y1 + (hR1 - hL1) / 2 + hL1

y2 = y1 + hR1 + 14
h2 = 2 * LH + 10
box(LX, y2, LW, h2, [('Reports sought for retrieval', True, 0), ('(n = 100)', False, 0)], center=True)
box(RX, y2, RW, h2, [('Reports not retrieved (n = 6):', True, 0), ('full text not accessible', False, 0)])
arrow(LX + LW / 2, yA, LX + LW / 2, y2); arrow(LX + LW, y2 + h2 / 2, RX, y2 + h2 / 2)

y3 = y2 + h2 + 14
exR = [('Reports excluded (n = 11):', True, 0), (B + 'No automated model (n = 4)', False, 0), (B + 'No performance metric (n = 3)', False, 0),
       (B + 'Task out of scope (n = 2)', False, 0), (B + 'No wearable or vision input (n = 1)', False, 0), (B + 'Not a peer-reviewed report (n = 1)', False, 0)]
hR3 = len(exR) * LH + 10
hL3 = 2 * LH + 10
box(LX, y3 + (hR3 - hL3) / 2, LW, hL3, [('Reports assessed for eligibility', True, 0), ('(n = 94)', False, 0)], center=True)
box(RX, y3, RW, hR3, exR)
arrow(LX + LW / 2, y2 + h2, LX + LW / 2, y3 + (hR3 - hL3) / 2)
arrow(LX + LW, y3 + hR3 / 2, RX, y3 + hR3 / 2)
yB = y3 + (hR3 - hL3) / 2 + hL3
phase(y1, y3 + hR3 - y1, 'Screening')

# --- Included
y4 = y3 + hR3 + 16
h4 = 2 * LH + 26
box(LX, y4, LW, h4, [('Studies included in review (n = 83)', True, 0), ('Reports of included studies (n = 83)', False, 0)], center=True)
arrow(LX + LW / 2, yB, LX + LW / 2, y4)
phase(y4, h4, 'Included')
Htot = y4 + h4 + 3
for s in [s for s in out if 'text' in s]: pass
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="130mm" height="{Htot/MM:.2f}mm" viewBox="0 0 {W:.2f} {Htot:.2f}">'
       f'<rect width="100%" height="100%" fill="#ffffff"/>' + ''.join(out) + '</svg>')
open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'fig2_prisma.svg'), 'w', encoding='utf-8').write(svg)
# width checks
for s, size, b in [('Not a peer-reviewed primary study (n = 224)', FS, False), ('Intervention study without a model (n = 75)', FS, False)]:
    print(s, tw(B + s, size, b) + 6, 'avail', RW)
print('height mm', Htot / MM)

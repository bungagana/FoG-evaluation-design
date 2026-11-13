"""Shared helpers for hand-authored SVG figures."""
ORANGE, BLUE, AQUA, GREY, INK, MUTED = '#D55E00', '#0072B2', '#CC79A7', '#c8c7c1', '#1f2933', '#6b7280'
FONT = "Arial, Helvetica, sans-serif"

def _rgb(h):
    h = h.lstrip('#'); return [int(h[i:i+2], 16) for i in (0, 2, 4)]
def _hex(c):
    return '#' + ''.join('%02x' % max(0, min(255, round(v))) for v in c)
def tint(h, f):   # f=0 -> colour, f=1 -> white
    return _hex([v + (255 - v) * f for v in _rgb(h)])
def shade(h, f):  # f=0 -> colour, f=1 -> black
    return _hex([v * (1 - f) for v in _rgb(h)])

class SVG:
    def __init__(self, W, H, wmm, hmm):
        self.W, self.H, self.wmm, self.hmm = W, H, wmm, hmm
        self.defs, self.body, self._g = [], [], set()
    def add(self, s): self.body.append(s)
    def d(self, s): self.defs.append(s)
    def lg(self, id, c1, c2, x2=0, y2=1, x1=0, y1=0):
        return c1
        if id in self._g: return f'url(#{id})'
        self._g.add(id)
        self.d(f'<linearGradient id="{id}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>')
        return f'url(#{id})'
    def lgn(self, id, stops, x1=0, y1=0, x2=1, y2=0):
        if id in self._g: return f'url(#{id})'
        self._g.add(id)
        st = ''.join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
        self.d(f'<linearGradient id="{id}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{st}</linearGradient>')
        return f'url(#{id})'
    def rg(self, id, c1, c2, cx=0.38, cy=0.32, r=0.75):
        if id in self._g: return f'url(#{id})'
        self._g.add(id)
        self.d(f'<radialGradient id="{id}" cx="{cx}" cy="{cy}" r="{r}"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></radialGradient>')
        return f'url(#{id})'
    def text(self, x, y, s, size=7, weight='normal', fill=INK, anchor='start', extra=''):
        self.add(f'<text x="{x:.2f}" y="{y:.2f}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" {extra}>{s}</text>')
    def shadow_rect(self, x, y, w, h, r, fill, stroke='none', sw=0, depth=1.0):
        # soft vector shadow: stacked translucent rects
        for i, (o, a) in enumerate([]):
            o *= depth
            self.add(f'<rect x="{x-o*0.35:.2f}" y="{y+o*0.6:.2f}" width="{w+o*0.7:.2f}" height="{h+o*0.5:.2f}" rx="{r+o*0.5:.2f}" fill="#1f2933" fill-opacity="{a}"/>')
        self.add(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    def out(self):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.wmm}mm" height="{self.hmm}mm" '
                f'viewBox="0 0 {self.W:.2f} {self.H:.2f}"><defs>{"".join(self.defs)}</defs>'
                f'<rect width="100%" height="100%" fill="#ffffff"/>{"".join(self.body)}</svg>')

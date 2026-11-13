from svgkit import *

def person(svg, x, y, s, shirt=GREY, pose='walk', sensor='ankle', scol=ORANGE,
           facing=1, hair='#dcd8d0', trousers='#465566', halo=None, uid='p'):
    """Illustrated person standing on ground point (x,y); height ~ 100*s."""
    sh = shirt
    g_shirt = svg.lg(f'sh{sh[1:]}', tint(sh, .18), shade(sh, .12), x2=1, y2=1)
    g_shirt_far = shade(sh, .22)
    g_skin = svg.rg('skin', '#f7d3b2', '#e2a67c')
    g_tr = svg.lg(f'tr{trousers[1:]}', tint(trousers, .12), shade(trousers, .1), x2=1, y2=0)
    g_shoe = svg.lg('shoe', '#4b5563', '#1f2933')
    out = []
    a = out.append
    if halo:
        a(f'<ellipse cx="0" cy="-48" rx="24" ry="56" fill="{halo}" fill-opacity=".16"/>')
    a('<ellipse cx="0" cy="0" rx="17" ry="3.2" fill="#1f2933" fill-opacity=".13"/>')

    def limb(pts, w, col):
        d = 'M' + ' L'.join(f'{px:.1f},{py:.1f}' for px, py in pts)
        a(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')

    def shoe(px, py, ang, col=g_shoe):
        a(f'<g transform="translate({px:.1f},{py:.1f}) rotate({ang})"><path d="M-3.4,-2.6 Q-3.8,1.6 -2.6,2.3 L8.6,2.3 Q10.4,2.1 10,0.2 Q9,-1.9 5,-2.4 L1.5,-3.6 Z" fill="{col}"/>'
          f'<path d="M-3.4,1.9 L9.9,1.9" stroke="#ffffff" stroke-opacity=".35" stroke-width=".8"/></g>')

    def sensor_at(px, py, ang=0, w=6.4, h=4.8):
        gs = svg.lg(f'sn{scol[1:]}', tint(scol, .25), shade(scol, .15))
        a(f'<g transform="translate({px:.1f},{py:.1f}) rotate({ang})">'
          f'<rect x="{-w/2-1.4}" y="{-1.1}" width="{w+2.8}" height="2.2" rx="1" fill="#2d3748"/>'
          f'<rect x="{-w/2}" y="{-h/2}" width="{w}" height="{h}" rx="1.3" fill="{gs}" stroke="{shade(scol,.3)}" stroke-width=".5"/>'
          f'<rect x="{-w/2+0.9}" y="{-h/2+0.7}" width="{w-1.8}" height="1.2" rx=".6" fill="#ffffff" fill-opacity=".45"/>'
          f'<circle cx="{w/2-1.4}" cy="{h/2-1.3}" r=".6" fill="#ffffff"/></g>')

    if pose == 'walk':
        hipF, kneeF, ankF = (1.5, -47), (8, -26), (11.5, -6.5)
        hipB, kneeB, ankB = (-1.5, -47), (-4.5, -26.5), (-13, -9)
        # far leg (back)
        limb([hipB, kneeB, ankB], 7.4, shade(trousers, .25))
        shoe(ankB[0] - 0.5, ankB[1] + 2.4, 22, '#111827')
        # far arm (forward swing) drawn behind torso
        limb([(-0.5, -73), (6.5, -60.5), (12.5, -53)], 5.2, g_shirt_far)
        a(f'<circle cx="13.3" cy="-52" r="2.6" fill="{shade("#e7b08a", .08)}"/>')
        # near leg (front)
        limb([hipF, kneeF, ankF], 7.6, g_tr)
        shoe(ankF[0] - 0.5, ankF[1] + 4.2, -4)
        sens = (ankF[0] - 0.6, ankF[1] - 2.2, 76)
        torso_rot = 7
        near_arm = [(1, -73), (-5.5, -60), (-8, -49)]
        hand = (-8.2, -47.5)
    else:
        hipF, kneeF, ankF = (3, -47), (3.4, -26), (3.6, -6)
        hipB, kneeB, ankB = (-3, -47), (-3.4, -26), (-3.6, -6)
        limb([hipB, kneeB, ankB], 7.4, shade(trousers, .2))
        shoe(-5.8, -2.2, 0, '#111827')
        limb([(-6.5, -73), (-9, -60), (-9.5, -49)], 5.2, g_shirt_far)
        a(f'<circle cx="-9.5" cy="-47.8" r="2.6" fill="{shade("#e7b08a", .08)}"/>')
        limb([hipF, kneeF, ankF], 7.6, g_tr)
        shoe(1.6, -2.0, 0)
        sens = (3.6, -9, 90)
        torso_rot = 0
        near_arm = [(6.5, -73), (9, -60), (9.5, -49)]
        hand = (9.5, -47.8)
    # torso + head group (slight forward stoop when walking)
    a(f'<g transform="rotate({torso_rot} 0 -47)">')
    a(f'<path d="M-8.2,-73.5 Q-8.6,-77.8 -3.5,-78.6 L3.5,-78.6 Q8.6,-77.8 8.2,-73.5 L7.4,-55 Q7.4,-45.5 4,-45 L-4,-45 Q-7.4,-45.5 -7.4,-55 Z" fill="{g_shirt}"/>')
    a(f'<path d="M-5.8,-74 Q-6.2,-62 -4.6,-50" stroke="#ffffff" stroke-opacity=".28" stroke-width="1.6" fill="none" stroke-linecap="round"/>')
    a(f'<rect x="-2.3" y="-82.2" width="4.6" height="5" rx="1.8" fill="#e2a67c"/>')
    a(f'<circle cx="0.6" cy="-88.6" r="7.4" fill="{g_skin}"/>')
    a(f'<path d="M-6.8,-87.2 Q-8.2,-97.6 1.4,-96.6 Q8.2,-96.2 8,-90.2 Q4.8,-93 0.4,-92.2 Q-3.6,-91.6 -4.6,-86.6 Z" fill="{hair}"/>')
    a(f'<circle cx="-5.2" cy="-87.6" r="1.6" fill="#e2a67c"/>')
    a(f'<circle cx="5.2" cy="-89.2" r=".75" fill="#1f2933"/>')
    a('</g>')
    # near arm
    d = 'M' + ' L'.join(f'{px:.1f},{py:.1f}' for px, py in near_arm)
    a(f'<g transform="rotate({torso_rot*0.6} 0 -47)"><path d="{d}" fill="none" stroke="{g_shirt}" stroke-width="5.4" stroke-linecap="round" stroke-linejoin="round"/>'
      f'<circle cx="{hand[0]}" cy="{hand[1]}" r="2.7" fill="{g_skin}"/>')
    if sensor == 'wrist':
        sensor_at(hand[0], hand[1] - 3.2, 0, 5.4, 4)
    a('</g>')
    if sensor == 'ankle':
        sensor_at(*sens)
    elif sensor == 'waist':
        sensor_at(5.8, -48.5, 90, 5.6, 4.2)
    elif sensor == 'thigh':
        sensor_at((hipF[0] + kneeF[0]) / 2 + 1.5, (hipF[1] + kneeF[1]) / 2, 70)
    svg.add(f'<g transform="translate({x:.2f},{y:.2f}) scale({s*facing:.4f},{s:.4f})">' + ''.join(out) + '</g>')

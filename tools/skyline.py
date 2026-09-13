import random
W, H = 1440, 250
GROUND = 232
out = []
a = out.append
r = random.Random(7)   # fixed: the art must be byte-identical on every regeneration

def win_grid(x, y, w, h, cols, rows, lit_chance, layer):
    """Ink windows, a few lit gold — the game's 'lit windows glow' read, at rest."""
    pad = 6 if layer == "fg" else 5
    cw = (w - pad * (cols + 1)) / cols
    ch = (h - pad * (rows + 1)) / rows
    if cw < 2.5 or ch < 3: return
    for c in range(cols):
        for rr in range(rows):
            wx = x + pad + c * (cw + pad)
            wy = y + pad + rr * (ch + pad)
            lit = r.random() < lit_chance
            f = "#f4d47c" if lit else "#2a2622"
            o = ".95" if lit else ".22"
            a(f'<rect x="{wx:.0f}" y="{wy:.0f}" width="{cw:.0f}" height="{ch:.0f}" fill="{f}" opacity="{o}"/>')

# --- far layer: flat silhouettes, no detail ---
a('<g fill="#a8b6c4" opacity=".55">')
x = -20
while x < W + 40:
    w = r.randint(46, 104); h = r.randint(46, 132)
    a(f'<rect x="{x}" y="{GROUND-h}" width="{w}" height="{h}"/>')
    x += w + r.randint(6, 26)
a('</g>')

# --- mid layer: the landmarks ride here (spec §5, parallax 0.55) ---
a('<g stroke="#2a2622" stroke-width="2" stroke-linejoin="round">')
mid = []
x = -30
while x < W + 40:
    w = r.randint(54, 116); h = r.randint(70, 168)
    mid.append((x, w, h)); x += w + r.randint(14, 40)
for (bx, bw, bh) in mid:
    a(f'<rect x="{bx}" y="{GROUND-bh}" width="{bw}" height="{bh}" fill="#e8cfa6"/>')
    win_grid(bx, GROUND-bh, bw, bh, max(2, bw//26), max(2, bh//24), .16, "mid")
a('</g>')

# Transamerica and Coit Tower ride the mid layer; the bridge is drawn last, nearest of all.
a('<g stroke="#2a2622" stroke-width="2.5" stroke-linejoin="round" fill="none">')
a('<path d="M1046 232 L1078 74 L1110 232 Z" fill="#e8cfa6"/>')
a('<path d="M1078 74 V52" stroke-width="3"/>')
a('<rect x="700" y="120" width="46" height="112" fill="#e8cfa6"/>')
a('<path d="M700 120 h46 l-8 -22 h-30 z" fill="#d9a9a2"/>')
a('<path d="M723 98 V78" stroke-width="3"/>')
a('</g>')

# --- foreground: landable roofs, vents, aerials (parallax 1.0) ---
a('<g stroke="#2a2622" stroke-width="2.5" stroke-linejoin="round">')
x = -40
while x < W + 40:
    w = r.randint(80, 150); h = r.randint(40, 104)
    y = GROUND - h
    a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#d9a9a2"/>')
    win_grid(x, y, w, h, max(2, w//30), max(1, h//26), .22, "fg")
    k = r.random()
    if k < .3:      # rooftop fan on a post
        cx = x + w * .3
        a(f'<path d="M{cx:.0f} {y} v-16 M{cx-11:.0f} {y-16} h22" fill="none"/>')
    elif k < .5:    # aerial
        cx = x + w * .7
        a(f'<path d="M{cx:.0f} {y} v-22 M{cx-7:.0f} {y-14} h14 M{cx-5:.0f} {y-20} h10" fill="none"/>')
    elif k < .62:   # water tank
        cx = x + w * .5
        a(f'<rect x="{cx-13:.0f}" y="{y-24}" width="26" height="20" fill="#e8cfa6"/>')
        a(f'<path d="M{cx-13:.0f} {y-24} l13 -9 l13 9 z" fill="#77685c"/>')
    x += w + r.randint(10, 30)
a('</g>')


# --- the Golden Gate, nearest layer of all: San Francisco opens the tour ---
ORANGE, DECK, TOP, ANCHOR = "#c9463d", 202, 58, 170
T1, T2 = 124, 252

def qbez(t, p0, p1, p2):
    u = 1 - t
    return (u*u*p0[0] + 2*u*t*p1[0] + t*t*p2[0], u*u*p0[1] + 2*u*t*p1[1] + t*t*p2[1])

a(f'<g stroke="{ORANGE}" stroke-width="3" stroke-linejoin="round" fill="none">')
a(f'<rect x="14" y="{DECK}" width="348" height="7" fill="{ORANGE}"/>')
spans = [((14, ANCHOR), (69, 150), (T1, TOP)),
         ((T1, TOP), (188, 206), (T2, TOP)),
         ((T2, TOP), (307, 150), (362, ANCHOR))]
for p0, p1, p2 in spans:
    a(f'<path d="M{p0[0]} {p0[1]} Q{p1[0]} {p1[1]} {p2[0]} {p2[1]}"/>')
    for i in range(1, 8):                       # hangers, cable down to deck
        hx, hy = qbez(i / 8, p0, p1, p2)
        if hy < DECK - 4:
            a(f'<path d="M{hx:.0f} {hy:.0f} V{DECK}" stroke-width="1.6"/>')
for tx in (T1, T2):                             # tower legs and their cross braces
    a(f'<path d="M{tx-7} {DECK+7} V{TOP-6} M{tx+7} {DECK+7} V{TOP-6} M{tx-7} {TOP-6} h14"/>')
    for by in (96, 136, 174):
        a(f'<path d="M{tx-7} {by} h14" stroke-width="2"/>')
a('</g>')

a(f'<rect x="0" y="{GROUND}" width="{W}" height="{H-GROUND}" fill="#77685c"/>')
a(f'<path d="M0 {GROUND} H{W}" stroke="#2a2622" stroke-width="3"/>')

print(f'<svg class="skyline" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" preserveAspectRatio="xMidYMax slice" aria-hidden="true" focusable="false">')
print("\n".join(out))
print('</svg>')

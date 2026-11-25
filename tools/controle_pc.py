#!/usr/bin/env python3
"""Ilustração de teclado + mouse (mouse à direita) para o lugar do desenho do
controle de Xbox (platform.ttpf, 1024x512), no mesmo estilo: corpo branco com
sombra lilás, contorno preto grosso, brilhos, e as teclas usadas no jogo em
preto brilhante com letra branca (como os botões A/B/X/Y do controle).
Desenho próprio. Letras em contorno na fonte da interface (fonte_jogo.py).

Uso: controle_pc.py <saida.svg>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fonte_jogo import text_outline  # noqa: E402

W, H = 1024, 512
INK = "#0b0b0f"
LILAC = "#b9a6e6"
LILAC_D = "#8f78cc"
OUT = 7          # contorno do corpo
KOUT = 3         # contorno das teclas

# teclas que o jogo usa (mapeamento do projeto): ficam pretas
USED = {"Esc", "Tab", "Q", "W", "R", "F", "A", "S", "D", "C", "V", "Shift", "Ctrl",
        "Space", "↑", "↓", "←", "→"}


def label(cx, cy, s, cap, fill):
    if s in ("↑", "↓", "←", "→"):
        a = cap * 0.55
        pts = {"↑": [(0, -a), (a, a * .6), (-a, a * .6)], "↓": [(0, a), (-a, -a * .6), (a, -a * .6)],
               "←": [(-a, 0), (a * .6, -a), (a * .6, a)], "→": [(a, 0), (-a * .6, a), (-a * .6, -a)]}[s]
        return '<polygon points="%s" fill="%s"/>' % (
            " ".join("%.1f,%.1f" % (cx + x, cy + y) for x, y in pts), fill)
    if s == "Space":
        return ""
    fam = "gta_art_deco_condensed_bold" if len(s) > 1 else "gta_art_deco_bold"
    g = text_outline(fam, s, cap / 0.7)
    dx = cx - (g["x0"] + g["x1"]) / 2
    dy = cy + g["cap"] / 2
    return '<path transform="translate(%.2f %.2f)" d="%s" fill="%s"/>' % (dx, dy, g["d"], fill)


def keycap(x, y, w, h, s):
    """Tecla com 'saia' lilás embaixo (volume), topo e brilho."""
    used = s in USED
    r = 7
    lip = 6
    top = "url(#kblack)" if used else "url(#kwhite)"
    skirt = "#1d1a26" if used else LILAC
    out = ('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%d" fill="%s" stroke="%s" '
           'stroke-width="%d"/>' % (x, y, w, h, r, skirt, INK, KOUT))
    out += ('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%d" fill="%s" stroke="%s" '
            'stroke-width="%d"/>' % (x + 2, y + 1, w - 4, h - lip - 1, r - 1, top, INK, KOUT - 1))
    # brilho no topo
    out += ('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="3" fill="#fff" '
            'fill-opacity="%s"/>' % (x + 7, y + 5, max(w - 14, 4), 4, ".55" if used else ".9"))
    if s:
        out += label(x + w / 2, y + (h - lip) / 2 + 1, s, 13 if len(s) == 1 else 11,
                     "#fff" if used else "#6b6680")
    return out


def keyboard(x0, y0, kw, gap):
    rows = [
        [("Esc", 1)] + [(c, 1) for c in "1234567890"] + [("-", 1), ("=", 1), ("Bksp", 2)],
        [("Tab", 1.5)] + [(c, 1) for c in "QWERTYUIOP"] + [("[", 1), ("]", 1), ("\\", 1.5)],
        [("Caps", 1.75)] + [(c, 1) for c in "ASDFGHJKL"] + [(";", 1), ("'", 1), ("Enter", 2.25)],
        [("Shift", 2.25)] + [(c, 1) for c in "ZXCVBNM"] + [(",", 1), (".", 1), ("/", 1),
                                                         ("Shift ", 1.75), ("↑", 1)],
        [("Ctrl", 1.25), ("", 1.25), ("Alt", 1.25), ("Space", 6.25), ("Alt ", 1), ("Fn", 1),
         ("←", 1), ("↓", 1), ("→", 1)],
    ]
    out = ""
    for r, row in enumerate(rows):
        x = x0
        for s, u in row:
            w = kw * u + gap * (u - 1)
            out += keycap(x, y0 + r * (kw + gap), w, kw, s.strip())
            x += w + gap
    return out


def main():
    out = sys.argv[1]
    kw, gap = 44, 6
    cols = 15                      # largura de 15 unidades (65%)
    kb_w = cols * kw + (cols - 1) * gap
    kb_h = 5 * kw + 4 * gap
    pad = 24
    bx = 16
    by = (512 - (5 * kw + 4 * gap + 2 * pad) - 14) // 2   # conjunto centralizado na altura
    bw, bh = kb_w + 2 * pad, kb_h + 2 * pad
    body = f'''
<defs>
  <linearGradient id="case" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#ffffff"/><stop offset=".55" stop-color="#f3f0fa"/>
    <stop offset="1" stop-color="{LILAC}"/></linearGradient>
  <linearGradient id="kwhite" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#ece8f6"/></linearGradient>
  <linearGradient id="kblack" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#3a3646"/><stop offset=".5" stop-color="#15131c"/>
    <stop offset="1" stop-color="#050408"/></linearGradient>
  <linearGradient id="mouse" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#ffffff"/><stop offset=".6" stop-color="#f1edf9"/>
    <stop offset="1" stop-color="{LILAC}"/></linearGradient>
  <linearGradient id="wheel" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#2a2633"/><stop offset=".5" stop-color="#55506a"/>
    <stop offset="1" stop-color="#15131c"/></linearGradient>
</defs>
<!-- teclado: sombra lilás, base, corpo -->
<rect x="{bx + 6}" y="{by + 14}" width="{bw}" height="{bh}" rx="30" fill="{LILAC_D}" stroke="{INK}" stroke-width="{OUT}"/>
<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="30" fill="url(#case)" stroke="{INK}" stroke-width="{OUT}"/>
<path d="M{bx + 40} {by + 10} L{bx + bw * .45} {by + 10} L{bx + bw * .38} {by + 22} L{bx + 34} {by + 22} Z" fill="#fff" fill-opacity=".9"/>
{keyboard(bx + pad, by + pad, kw, gap)}
<!-- faixas de brilho em diagonal, como no controle (sem recorte: dentro do corpo) -->
<polygon points="{bx + bw * .53},{by + 6} {bx + bw * .60},{by + 6} {bx + bw * .45},{by + bh - 6} {bx + bw * .38},{by + bh - 6}" fill="#ffffff" opacity=".16"/>
<polygon points="{bx + bw * .63},{by + 6} {bx + bw * .65},{by + 6} {bx + bw * .50},{by + bh - 6} {bx + bw * .48},{by + bh - 6}" fill="#ffffff" opacity=".22"/>
'''
    # mouse à direita, em pé, ao lado do teclado e centralizado na altura dele
    s = 4.5
    kb_right = bx + bw
    mx = kb_right + (1024 - kb_right) / 2 - 4
    my = by + bh / 2
    mouse = f'''
<g transform="translate({mx:.1f} {my:.1f}) scale({s}) translate(-32 -32.5)">
  <path d="M32 6 C46 6 52 15 52 26 L52 45 C52 56 43 63 32 63 C21 63 12 56 12 45 L12 26 C12 15 18 6 32 6 Z" transform="translate(2 3)" fill="{LILAC_D}" stroke="{INK}" stroke-width="{OUT / s:.3f}"/>
  <path d="M32 4 C45 4 50 13 50 24 L50 44 C50 54 42 61 32 61 C22 61 14 54 14 44 L14 24 C14 13 19 4 32 4 Z" fill="url(#mouse)" stroke="{INK}" stroke-width="{OUT / s:.3f}" stroke-linejoin="round"/>
  <path d="M32 4 C19 4 14 13 14 24 L14 28 L32 28 Z" fill="url(#kwhite)" stroke="{INK}" stroke-width="{KOUT / s * 1.4:.3f}" stroke-linejoin="round"/>
  <path d="M32 4 C45 4 50 13 50 24 L50 28 L32 28 Z" fill="url(#kwhite)" stroke="{INK}" stroke-width="{KOUT / s * 1.4:.3f}" stroke-linejoin="round"/>
  <rect x="28.5" y="10" width="7" height="13" rx="3.5" fill="url(#wheel)" stroke="{INK}" stroke-width="{KOUT / s * 1.2:.3f}"/>
  <path d="M19 11 C21 8 25 6.5 28 6.5" fill="none" stroke="#fff" stroke-width="{3 / s:.3f}" stroke-linecap="round"/>
  <path d="M18 34 C17 40 18 47 21 52" fill="none" stroke="#fff" stroke-opacity=".85" stroke-width="{4 / s:.3f}" stroke-linecap="round"/>
</g>'''
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
           f'{body}{mouse}</svg>')
    with open(out, "w") as f:
        f.write(svg)
    print("ok:", out)


if __name__ == "__main__":
    main()

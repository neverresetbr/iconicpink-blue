#!/usr/bin/env python3
"""Imagens do README: a folha com os 38 ícones de PC e uma demo dos prompts
num fundo limpo (sem nada do jogo além das letras, que vêm da fonte da
interface pela sua cópia). Gera SVG e converte para PNG com ferramentas/raster.

Uso: vitrine.py <pasta_saida>   (gera sheet.png e demo.png)
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from teclas_pc import designs  # noqa: E402

FONT = 'font-family="Helvetica Neue, Helvetica, Arial, sans-serif"'
COND = 'font-family="Helvetica Neue, Helvetica, Arial, sans-serif" font-stretch="condensed"'
PINK, BLUE = "#ff4f9a", "#3d8bff"

GROUPS = [
    ("Keys", [(33, "F"), (31, "R"), (36, "Q"), (39, "V"), (25, "C"),
              (12, "W"), (14, "A"), (13, "S"), (15, "D")]),
    ("Wide keys", [(30, "Shift"), (32, "Space"), (34, "Tab"), (38, "Esc"), (16, "Ctrl")]),
    ("Arrow keys", [(4, "Up"), (5, "Down"), (6, "Left"), (7, "Right"), (8, "None"),
                    (9, "All"), (10, "Up/Down"), (11, "Left/Right")]),
    ("WASD", [(17, "WASD"), (18, "W/S"), (19, "A/D"), (20, "Rotate L"), (58, "Rotate L alt")]),
    ("Mouse", [(26, "Mouse"), (37, "Left click"), (35, "Right click"), (21, "Up"),
               (22, "Down"), (23, "Left"), (24, "Right"), (27, "Up/Down"),
               (28, "Left/Right"), (29, "Move"), (59, "Move alt")]),
]


def icon(n, cx, cy, scale, body=None):
    body = body or designs()[n]
    return ('<g transform="translate(%.1f %.1f) scale(%g) translate(-32 -32)">%s</g>'
            % (cx, cy, scale, body))


def bg(w, h, rx=22):
    return f'''<defs>
  <radialGradient id="gb" cx="8%" cy="0%" r="70%"><stop offset="0" stop-color="{BLUE}" stop-opacity=".22"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>
  <radialGradient id="gp" cx="96%" cy="100%" r="60%"><stop offset="0" stop-color="{PINK}" stop-opacity=".20"/><stop offset="1" stop-color="{PINK}" stop-opacity="0"/></radialGradient>
</defs>
<rect width="{w}" height="{h}" rx="{rx}" fill="#0d1016"/>
<rect width="{w}" height="{h}" rx="{rx}" fill="url(#gb)"/>
<rect width="{w}" height="{h}" rx="{rx}" fill="url(#gp)"/>'''


def sheet():
    d = designs()
    W, cell, scale, cols = 1400, 124, 0.9, 11
    parts, y = [], 70
    for title, items in GROUPS:
        parts.append('<text x="48" y="%d" %s font-size="15" font-weight="700" fill="#8a93a3" '
                     'letter-spacing="1.5">%s</text>' % (y, FONT, title.upper()))
        y += 20
        for i, (n, label) in enumerate(items):
            col, row = i % cols, i // cols
            cx = 48 + cell / 2 + col * cell
            cy = y + 62 + row * 150
            parts.append(icon(n, cx, cy, scale, d[n]))
            parts.append('<text x="%.1f" y="%d" text-anchor="middle" %s font-size="14" '
                         'font-weight="600" fill="#e8ebf0">%s</text>' % (cx, cy + 66, FONT, label))
            parts.append('<text x="%.1f" y="%d" text-anchor="middle" %s font-size="12" '
                         'fill="#6c7584">%d</text>' % (cx, cy + 84, FONT, n))
        y += 150 * ((len(items) - 1) // cols + 1) + 26
    H = y + 10
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
            f'height="{H}">{bg(W, H)}{"".join(parts)}</svg>')


PRESSED = {"#fff": "rgb(72,72,72)", "#000": "rgb(205,205,205)",
           "rgb(103,103,103)": "rgb(140,140,140)"}


def pressed(body):
    return re.sub("|".join(re.escape(k) for k in PRESSED), lambda m: PRESSED[m.group(0)], body)


_W = {}


def text_w(s, size, font="HelveticaNeue-Medium"):
    """Largura real do texto (CoreText, via ferramentas/texto_svg)."""
    import json
    key = (s, size, font)
    if key not in _W:
        r = subprocess.run([os.path.join(HERE, "texto_svg")], input=json.dumps([[font, size, s]]),
                           capture_output=True, text=True, check=True)
        _W[key] = json.loads(r.stdout)[0]["w"]
    return _W[key]


def demo():
    """Prompts nos lugares do jogo, num fundo limpo."""
    d = designs()
    W, H = 1600, 900
    s = 44 / 70.4   # ícone de ajuda: 44 px para o espaço de 70,4
    p = []

    def line(x, y, parts, size=26, gap=10, color="#fff", cond=False):
        """Texto e ícones em linha; parts: str ou (n, escala, corpo)."""
        out, cx = [], x
        for it in parts:
            if isinstance(it, str):
                w = text_w(it, size, "HelveticaNeue-CondensedBold" if cond else "HelveticaNeue-Medium")
                out.append('<text x="%.1f" y="%.1f" %s font-size="%d" font-weight="%s" fill="%s">%s</text>'
                           % (cx, y + size * 0.36, COND if cond else FONT, size,
                              "700" if cond else "500", color, it))
                cx += w + gap
            else:
                n, sc, body = it
                half = 35.2 * sc
                out.append(icon(n, cx + half, y, sc, body))
                cx += 2 * half + gap
        return "".join(out), cx

    # caixa de ajuda (canto superior esquerdo), do tamanho do texto
    rows = [["Press", (33, s, d[33]), "to enter the plane."],
            ["Hold", (35, s, d[35]), "to aim and", (37, s, d[37]), "to shoot."],
            ["Crouch", (16, s, d[16]), "and move quietly."],
            ["Use", (4, s, d[4]), "to open the phone."]]
    pad, lh = 28, 54
    widths = [line(0, 0, r)[1] - 10 for r in rows]
    p.append('<rect x="60" y="60" width="%.1f" height="%d" rx="3" fill="#000" fill-opacity=".72"/>'
             % (max(widths) + 2 * pad, len(rows) * lh + 2 * pad - 8))
    for i, r in enumerate(rows):
        p.append(line(60 + pad, 60 + pad + 23 + i * lh, r)[0])
    # prompt de contexto (pílula azul embaixo, no centro)
    txt, end = line(0, 0, ["Hold", (33, 40 / 70.4, d[33]), "to open"], size=28)
    pw = end - 10 + 60
    p.append('<rect x="%.1f" y="768" width="%.1f" height="70" rx="35" fill="rgb(15,84,140)" '
             'fill-opacity=".95"/>' % ((W - pw) / 2, pw))
    p.append(line((W - pw) / 2 + 30, 803, ["Hold", (33, 40 / 70.4, d[33]), "to open"], size=28)[0])
    # QTE no meio (disco, trilho, arco rosa) com apertar repetido
    cx, cy, r = 1010, 400, 56
    p.append('<circle cx="%d" cy="%d" r="%d" fill="#000" fill-opacity=".7"/>' % (cx, cy, r - 6))
    p.append('<circle cx="%d" cy="%d" r="%d" fill="none" stroke="#fff" stroke-opacity=".15" '
             'stroke-width="10"/>' % (cx, cy, r))
    import math
    a = 2 * math.pi * 0.62
    ex, ey = cx + r * math.sin(a), cy - r * math.cos(a)
    p.append('<path d="M%d %d A%d %d 0 1 1 %.1f %.1f" fill="none" stroke="rgb(237,84,153)" '
             'stroke-width="10"/>' % (cx, cy - r, r, r, ex, ey))
    p.append(icon(32, cx, cy, 52 / 70.4))
    p.append('<text x="%d" y="%d" text-anchor="middle" %s font-size="22" font-weight="700" '
             'fill="#fff" letter-spacing="1">MASH REPEATEDLY</text>' % (cx, cy + r + 44, COND))
    # canto inferior direito: lista, segurando e rodapé
    f = 36 / 70.4
    corner = [("WALK", 17), ("CAMERA", 29), ("SPRINT", 30), ("JUMP", 32), ("WEAPONS", 34),
              ("COVER", 36)]
    for i, (label, n) in enumerate(corner):
        y = 430 + i * 50
        p.append('<text x="1478" y="%d" text-anchor="end" %s font-size="24" font-weight="700" '
                 'fill="#fff">%s</text>' % (y + 9, COND, label))
        p.append(icon(n, 1512, y, f))
    p.append('<text x="1478" y="%d" text-anchor="end" %s font-size="24" font-weight="700" '
             'fill="#fff">AIMING (HOLDING)</text>' % (760 + 9, COND))
    p.append(icon(35, 1512, 760, f, pressed(d[35])))
    p.append('<text x="1300" y="%d" text-anchor="end" %s font-size="24" font-weight="700" '
             'fill="#fff">SELECT</text>' % (818 + 9, COND))
    p.append(icon(30, 1334, 818, f))
    p.append('<text x="1478" y="%d" text-anchor="end" %s font-size="24" font-weight="700" '
             'fill="#fff">BACK</text>' % (818 + 9, COND))
    p.append(icon(31, 1512, 818, f))
    # disabled
    p.append('<g opacity=".4"><text x="1478" y="%d" text-anchor="end" %s font-size="24" '
             'font-weight="700" fill="#fff">2D VIEW</text>%s</g>'
             % (380 + 9, COND, icon(25, 1512, 380, f)))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
            f'height="{H}">{bg(W, H)}{"".join(p)}</svg>')


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    raster = os.path.join(HERE, "raster")
    for name, svg, width in (("sheet", sheet(), 2100), ("demo", demo(), 2400)):
        tmp = os.path.join(out, name + ".tmp.svg")
        with open(tmp, "w") as f:
            f.write(svg)
        subprocess.run([raster, tmp, os.path.join(out, name + ".png"), str(width)], check=True)
        os.remove(tmp)


if __name__ == "__main__":
    main()

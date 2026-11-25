#!/usr/bin/env python3
"""GIFs das animações de prompt para o README, com os nossos ícones de PC e a
mesma lógica da demo (valores do motor: apertado encolhe para 0,8 e troca de
cor em 6 quadros; anel de progresso; QTE com arco rosa). Fundo limpo.

Uso: gifs.py <pasta_saida>   (precisa de ferramentas/raster e do ffmpeg)
"""
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from teclas_pc import designs  # noqa: E402

FPS = 25
W, H = 640, 300
FONT = 'font-family="Helvetica Neue, Helvetica, Arial, sans-serif"'
COND = 'font-family="Helvetica Neue, Helvetica, Arial, sans-serif" font-stretch="condensed"'
PINK, BLUE = "#ff4f9a", "#3d8bff"
D = designs()
LERP = 6 / 30.0                       # LERP_DURATION_FRAMES = 6 (a 30 quadros/s)
GAP = 7.0                             # anel: distância da borda do ícone


def clamp(x):
    return max(0.0, min(1.0, x))


def out_cubic(x):
    return 1 - (1 - clamp(x)) ** 3


def in_out(x):
    x = clamp(x)
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


def press_k(t, down, up):
    if t < down:
        return 0.0
    if t < up:
        return out_cubic((t - down) / LERP)
    return 1 - out_cubic((t - up) / LERP)


def mix(a, b, k):
    return "rgb(%d,%d,%d)" % tuple(round(x + (y - x) * k) for x, y in zip(a, b))


def tint(body, k):
    """Cor de apertado (COLOR_PROMPT_PRESSED) misturada pelo fator k."""
    if k <= 0:
        return body
    table = {"#fff": mix((255,) * 3, (72,) * 3, k), "#000": mix((0,) * 3, (205,) * 3, k),
             "rgb(103,103,103)": mix((103,) * 3, (140,) * 3, k)}
    return re.sub("|".join(re.escape(x) for x in table), lambda m: table[m.group(0)], body)


def icon(n, cx, cy, px, k=0.0):
    """Ícone n com 64 unidades = px pixels; k = apertado (encolhe para 0,8)."""
    sc = px / 64.0 * (1 - 0.2 * k)
    return ('<g transform="translate(%.2f %.2f) scale(%.4f) translate(-32 -32)">%s</g>'
            % (cx, cy, sc, tint(D[n], k)))


def ring(n, cx, cy, px, prog, color="#fff", glow=0.0):
    """Anel que segue o contorno da tecla (tecla simples ou larga)."""
    s = px / 64.0
    if n in (16, 30, 32, 34, 38):
        x, y, w, h, r = 0, 8, 64, 48, 10.5
    else:
        x, y, w, h, r = 0, 0, 64, 64, 13.5
    x, y, w, h, r = x - GAP, y - GAP, w + 2 * GAP, h + 2 * GAP, r + GAP
    d = ("M%.2f %.2f H%.2f A%g %g 0 0 1 %.2f %.2f V%.2f A%g %g 0 0 1 %.2f %.2f "
         "H%.2f A%g %g 0 0 1 %.2f %.2f V%.2f A%g %g 0 0 1 %.2f %.2f Z"
         % (x + w / 2, y, x + w - r, r, r, x + w, y + r, y + h - r, r, r, x + w - r, y + h,
            x + r, r, r, x, y + h - r, y + r, r, r, x + r, y))
    length = 2 * (w + h) - 8 * r + 2 * math.pi * r
    g = '<g transform="translate(%.2f %.2f) scale(%.4f) translate(-32 -32)">' % (cx, cy, s)
    g += '<path d="%s" fill="none" stroke="#000" stroke-opacity=".55" stroke-width="5"/>' % d
    if prog > 0:
        g += ('<path d="%s" fill="none" stroke="%s" stroke-width="5" stroke-dasharray="%.2f %.2f"/>'
              % (d, color, length * prog, length * 2))
    if glow > 0:
        g += ('<path d="%s" fill="none" stroke="#fff" stroke-opacity="%.3f" stroke-width="%.2f"/>'
              % (d, 0.5 * (1 - glow), 5 + 16 * glow))
    return g + "</g>"


def frame(body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs>
  <radialGradient id="gb" cx="8%" cy="0%" r="80%"><stop offset="0" stop-color="{BLUE}" stop-opacity=".22"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>
  <radialGradient id="gp" cx="96%" cy="100%" r="70%"><stop offset="0" stop-color="{PINK}" stop-opacity=".20"/><stop offset="1" stop-color="{PINK}" stop-opacity="0"/></radialGradient>
</defs>
<rect width="{W}" height="{H}" fill="#0d1016"/><rect width="{W}" height="{H}" fill="url(#gb)"/><rect width="{W}" height="{H}" fill="url(#gp)"/>
{body}</svg>'''


def caption(txt):
    return ('<text x="%d" y="%d" text-anchor="middle" %s font-size="15" font-weight="700" '
            'fill="#8a93a3" letter-spacing="1.5">%s</text>' % (W / 2, H - 24, FONT, txt))


# ---- cenas: cada uma devolve (duração, função t -> corpo SVG) ----------------
def press():
    def f(t):
        k = press_k(t, 0.9, 1.15)
        return ('<rect x="110" y="92" width="420" height="76" rx="3" fill="#000" fill-opacity=".72"/>'
                '<text x="136" y="140" %s font-size="26" font-weight="500" fill="#fff">Press</text>'
                % FONT + icon(33, 236, 130, 40, k)
                + '<text x="272" y="140" %s font-size="26" font-weight="500" fill="#fff">to enter the plane.</text>' % FONT
                + caption("PRESS"))
    return 2.0, f


def hold():
    def f(t):
        d0, hd = 0.4, 1.6
        k = press_k(t, d0, d0 + hd)
        prog = in_out((t - d0) / hd) if d0 <= t < d0 + hd else (1.0 if d0 + hd <= t < d0 + hd + .5 else 0)
        glow = clamp((t - d0 - hd) / .5) if d0 + hd <= t < d0 + hd + .5 else 0
        if glow:
            prog = 1 - glow
        return ('<rect x="170" y="98" width="300" height="70" rx="35" fill="rgb(15,84,140)" fill-opacity=".95"/>'
                '<text x="204" y="142" %s font-size="27" font-weight="500" fill="#fff">Hold</text>' % FONT
                + ring(33, 300, 133, 38, prog, glow=glow) + icon(33, 300, 133, 38, k)
                + '<text x="340" y="142" %s font-size="27" font-weight="500" fill="#fff">to open</text>' % FONT
                + caption("HOLD"))
    return 3.0, f


def mash():
    def f(t):
        tap = 0.19
        if t < 2.4:
            ph = (t % tap) / tap
            k = out_cubic(ph / .45) if ph < .45 else 1 - out_cubic((ph - .45) / .55)
            prog = min(1.0, t / 2.2)
        else:
            k, prog = 0.0, max(0.0, 1 - (t - 2.4) / 0.6)
        return (ring(32, W / 2, 118, 64, prog, color=PINK) + icon(32, W / 2, 118, 64, k)
                + '<text x="%d" y="200" text-anchor="middle" %s font-size="22" font-weight="700" '
                  'fill="#fff" letter-spacing="1">MASH REPEATEDLY</text>' % (W / 2, COND)
                + caption("MASH"))
    return 3.0, f


def qte():
    def f(t):
        cx, cy, r, fill = W / 2, 122, 56, 1.6
        p = min(1.0, t / fill)
        body = ('<circle cx="%d" cy="%d" r="%d" fill="#000" fill-opacity=".7"/>' % (cx, cy, r - 6)
                + '<circle cx="%d" cy="%d" r="%d" fill="none" stroke="#fff" stroke-opacity=".15" '
                  'stroke-width="9"/>' % (cx, cy, r))
        if t < fill:
            a = 2 * math.pi * p
            ex, ey = cx + r * math.sin(a), cy - r * math.cos(a)
            body += ('<path d="M%d %d A%d %d 0 %d 1 %.2f %.2f" fill="none" stroke="rgb(237,84,153)" '
                     'stroke-width="9"/>' % (cx, cy - r, r, r, 1 if p > .5 else 0, ex, ey))
        else:
            g = clamp((t - fill) / 0.7)
            body += ('<circle cx="%d" cy="%d" r="%.2f" fill="none" stroke="#fff" stroke-opacity="%.3f" '
                     'stroke-width="3"/>' % (cx, cy, r + 28 * out_cubic(g), 1 - g))
        k = press_k(t, fill - 0.05, fill + 0.2)
        return body + icon(33, cx, cy, 50, k) + caption("QUICK-TIME EVENT")
    return 2.6, f


def holding():
    def f(t):
        rows = [("WALK", 17, 0), ("AIM", 35, press_k(t, 0.4, 1.8)), ("SHOOT", 37,
                max(press_k(t, 0.8, 1.0), press_k(t, 1.2, 1.4)))]
        body = ""
        for i, (label, n, k) in enumerate(rows):
            y = 70 + i * 54
            body += ('<text x="380" y="%d" text-anchor="end" %s font-size="26" font-weight="700" '
                     'fill="#fff">%s</text>' % (y + 9, COND, label)) + icon(n, 418, y, 36, k)
        return body + caption("PRESSED / HOLDING")
    return 2.4, f


SCENES = {"press": press, "hold": hold, "mash": mash, "qte": qte, "holding": holding}


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    raster = os.path.join(HERE, "raster")
    for name, scene in SCENES.items():
        dur, f = scene()
        tmp = tempfile.mkdtemp()
        n = int(round(dur * FPS))
        for i in range(n):
            svg = os.path.join(tmp, "f.svg")
            with open(svg, "w") as fo:
                fo.write(frame(f(i / FPS)))
            subprocess.run([raster, svg, os.path.join(tmp, "f%03d.png" % i), str(W)],
                           check=True, stdout=subprocess.DEVNULL)
        gif = os.path.join(out, name + ".gif")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i",
                        os.path.join(tmp, "f%03d.png"), "-vf",
                        "split[a][b];[a]palettegen=max_colors=128:stats_mode=full[p];"
                        "[b][p]paletteuse=dither=sierra2_4a", "-loop", "0", gif], check=True)
        shutil.rmtree(tmp)
        print("ok:", gif, "%d quadros, %d KB" % (n, os.path.getsize(gif) // 1024))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Desenhos de PC (teclado e mouse) para os 38 símbolos
platform_xbsx.input_icons.Main_Button_N, em SVG, no espaço de 64x64 dos
originais.

Regras (ANCORA.md, seção 2): sem círculos; um só padrão de medidas e de
estética; o mesmo mouse (aprovado) em todos os lugares.

Convenção de cor, igual à do jogo (pesquisa em gameplay de Xbox, 2026-11-25):
- a forma é BRANCA e os detalhes (letra, contorno) são PRETOS; no jogo o
  contorno preto some no fundo escuro e a letra parece vazada;
- parte ACIONADA = branca; parte NÃO acionada = cinza (103), como no
  direcional original.
Desenhos próprios. Uso: teclas_pc.py <pasta_saida_svg>
"""
import math
import os
import sys

# ---- padrão visual -------------------------------------------------------
K, W, G = "#000", "#fff", "rgb(103,103,103)"
STROKE = 3
SPAN = 61.0                       # caixa útil dos ícones de Xbox (1,5 a 62,5)
# PADRÃO DE TAMANHO (medido com ferramentas/medir, contorno incluído):
# a maior dimensão de todo ícone é 64, centrado em (32, 32), como os
# originais de Xbox (círculos e direcional = 64x64).
#   tecla simples 64x64 | tecla larga 64x48 | WASD/setas 64x43 |
#   mouse 64 de altura | mouse com setas 64 de altura | girar dentro de 64x64
KEY = (1.5, 1.5, SPAN, SPAN, 12)
WIDE = (1.5, 9.5, SPAN, 45, 9)
# TIPOGRAFIA: as fontes da própria interface do jogo (gfxfontlib_efigs.gfx).
# As letras A/B/X/Y dos botões originais são gta_art_deco_bold (proporção
# idêntica, erro 0,005). Altura das maiúsculas (cap) igual à dos originais.
FAMILY_KEY = "gta_art_deco_bold"             # tecla simples e WASD
FAMILY_WIDE = "gta_art_deco_condensed_bold"  # tecla larga ("Shift" cabe na altura do LB)
CAP_KEY = 25.6                               # = A, B, X, Y originais
CAP_WIDE = 22.2                              # = LB, RB originais
# bloco de 4 teclas em T (WASD e setas): teclas quadradas, largura total
GAP = 2
# bloco em T (WASD e setas do teclado): maior que o 64 (de propósito: em 64
# ficava pequeno). BLOCK_SPAN = largura das 3 teclas sem o contorno; por fora, +3.
BLOCK_SPAN = 73.0
MINI = (BLOCK_SPAN - 2 * GAP) / 3       # 23
CAP_MINI = MINI * 0.55                  # ~12,7
# seta padrão (triângulo arredondado, do tamanho das setas originais)
ARROW_W, ARROW_H = 18, 11
OUTLINE = 2.5                      # contorno dos detalhes soltos (setas)


# Quadro do SVG: o espaço de 64 (centro 32,32) com margem de 16 em volta, para
# as setas do mouse com setas caberem por fora sem corte. É o mesmo quadro em
# todos os ícones, então a escala é sempre a mesma (3,64 px por unidade).
VIEW = (-16.0, 96.0)


def svg(body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="%g %g %g %g" '
            'width="349" height="349">%s</svg>' % (VIEW[0], VIEW[0], VIEW[1], VIEW[1], body))


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fonte_jogo import text_outline  # noqa: E402


def text(x, y, s, cap, family=FAMILY_KEY, fill=K):
    """Texto como FORMA na fonte do jogo (não fonte instalada): idêntico em
    qualquer renderizador e pronto para ir ao .gfx. `cap` = altura das
    maiúsculas. Centralizado na horizontal pela caixa das letras e na vertical
    pela altura das maiúsculas."""
    size = cap / 0.7                    # cap/size = 0,70 nas gta_art_deco
    g = text_outline(family, s, size)
    dx = x - (g["x0"] + g["x1"]) / 2
    dy = y + g["cap"] / 2
    return ('<path transform="translate(%.2f %.2f)" d="%s" fill="%s"/>' % (dx, dy, g["d"], fill))


def rect(x, y, w, h, r, fill=W, stroke=STROKE):
    return ('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s" stroke="%s" '
            'stroke-width="%g"/>' % (x, y, w, h, r, fill, K, stroke))


def tri(cx, cy, d, a, b, color=K, sw=1.5, outline=None):
    pts = {"up": [(cx, cy - b), (cx + a, cy + b), (cx - a, cy + b)],
           "down": [(cx, cy + b), (cx - a, cy - b), (cx + a, cy - b)],
           "left": [(cx - b, cy), (cx + b, cy - a), (cx + b, cy + a)],
           "right": [(cx + b, cy), (cx - b, cy + a), (cx - b, cy - a)]}[d]
    return ('<polygon points="%s" fill="%s" stroke="%s" stroke-width="%g" '
            'stroke-linejoin="round"/>' % (" ".join("%g,%g" % p for p in pts), color, outline or color, sw))


def arrow(cx, cy, d):
    """Seta solta (fora de tecla): forma branca com contorno preto, para não
    sumir no fundo escuro do jogo (regra 2 da âncora)."""
    return tri(cx, cy, d, ARROW_W / 2, ARROW_H / 2, color=W, sw=OUTLINE, outline=K)


def space_symbol(cx, cy, w=36, h=11):
    """Símbolo de barra de espaço (⎵), desenhado como linha."""
    return ('<path d="M%g %g L%g %g L%g %g L%g %g" fill="none" stroke="%s" stroke-width="4.5" '
            'stroke-linecap="round" stroke-linejoin="round"/>'
            % (cx - w / 2, cy - h / 2, cx - w / 2, cy + h / 2, cx + w / 2, cy + h / 2,
               cx + w / 2, cy - h / 2, K))


def keycap(label, wide=False):
    x, y, w, h, r = WIDE if wide else KEY
    out = rect(x, y, w, h, r)
    if label == "SPACE":
        return out + space_symbol(x + w / 2, y + h / 2 + 2)
    if wide:
        return out + text(x + w / 2, y + h / 2, label, CAP_WIDE, FAMILY_WIDE)
    return out + text(x + w / 2, y + h / 2, label, CAP_KEY)


def keycap_arrow(d):
    """Tecla simples com uma seta (direcional com uma só direção)."""
    x, y, w, h, r = KEY
    return rect(x, y, w, h, r) + tri(x + w / 2, y + h / 2, d, 12.5, 8, sw=2)


DIRS = ("up", "left", "down", "right")


def t_block(labels, on):
    """4 teclas em T. on: conjunto de direções acionadas (brancas); as outras
    ficam cinza. on=None: todas brancas (neutro)."""
    total_h = MINI * 2 + GAP
    y_top = 32 - total_h / 2
    y_bot = y_top + MINI + GAP
    xs = [32 - MINI * 1.5 - GAP, 32 - MINI / 2, 32 + MINI / 2 + GAP]
    pos = {"up": (xs[1], y_top), "left": (xs[0], y_bot), "down": (xs[1], y_bot),
           "right": (xs[2], y_bot)}
    out = ""
    for key in DIRS:
        x, y = pos[key]
        fill = W if on is None or key in on else G
        out += rect(x, y, MINI, MINI, MINI * 0.2, fill)
        lab = labels.get(key)
        if lab:
            out += text(x + MINI / 2, y + MINI / 2, lab, CAP_MINI)
        else:
            out += tri(x + MINI / 2, y + MINI / 2, key, MINI * 0.26, MINI * 0.16, sw=1)
    return out


WASD = {"up": "W", "left": "A", "down": "S", "right": "D"}
ARROWS = {}


def wasd(on=None):
    return t_block(WASD, on)


def arrow_keys(on=None):
    return t_block(ARROWS, on)


# ---- mouse aprovado ---------------------------------------------------------
def mouse_shape(body=W, left=None, right=None, wheel=None):
    """Mouse aprovado. Partes sem cor própria seguem a cor do corpo."""
    left, right, wheel = left or body, right or body, wheel or body
    b = ("M32 4 C45 4 50 13 50 24 L50 44 C50 54 42 61 32 61 "
         "C22 61 14 54 14 44 L14 24 C14 13 19 4 32 4 Z")
    lb = "M32 4 C19 4 14 13 14 24 L14 28 L32 28 Z"
    rb = "M32 4 C45 4 50 13 50 24 L50 28 L32 28 Z"
    p = '<path d="%s" fill="%s" stroke="%s" stroke-width="%g" stroke-linejoin="round"/>'
    return (p % (b, body, K, STROKE) + p % (lb, left, K, STROKE) + p % (rb, right, K, STROKE)
            + '<rect x="28.5" y="10" width="7" height="13" rx="3.5" fill="%s" stroke="%s" '
              'stroke-width="2.5"/>' % (wheel, K))


# o desenho do mouse aprovado tem 57 de altura (y 4 a 61, centro 32,5); BASE
# leva a 61 (64 com o contorno), centrado em 32
BASE = SPAN / 57.0


def mouse(scale=1.0, cx=32.0, cy=32.0, **parts):
    """Mouse aprovado. scale=1: 64 de altura (padrão). O traço fica igual em
    qualquer escala."""
    body = mouse_shape(**parts)
    s = BASE * scale
    body = body.replace('stroke-width="3"', 'stroke-width="%g"' % (STROKE / s))
    body = body.replace('stroke-width="2.5"', 'stroke-width="%g"' % (2.5 / s))
    return ('<g transform="translate(%g %g) scale(%g) translate(-32 -32.5)">%s</g>'
            % (cx, cy, s, body))


def mouse_outer(scale):
    """Meia largura e meia altura do mouse na escala, com o contorno."""
    s = BASE * scale
    return 18 * s + STROKE / 2, 28.5 * s + STROKE / 2


def mouse_button(side):
    """Botão acionado em branco, resto do mouse em cinza (convenção do jogo)."""
    return mouse(body=G, **{side: W})


# mouse com setas: o MOUSE segue o padrão (41,6 x 64, centrado em 32,32), igual
# ao mouse sozinho; as setas ficam por fora e não contam no padrão. Respiro igual de ARROW_GAP entre cada seta e o mouse.
ARROW_GAP = 1.0
# alcance da seta a partir do centro dela, com o contorno (vale para a ponta e
# para a base: meia altura + meio contorno; conferido com ferramentas/medir)
ARROW_TIP = ARROW_H / 2 + OUTLINE / 2
ARROW_REACH = ARROW_GAP + 2 * ARROW_TIP     # quanto a seta passa do mouse


def mouse_arrows(dirs):
    out = mouse()
    hw, hh = mouse_outer(1.0)
    off_v = hh + ARROW_GAP + ARROW_TIP
    off_h = hw + ARROW_GAP + ARROW_TIP
    pos = {"up": (32, 32 - off_v), "down": (32, 32 + off_v),
           "left": (32 - off_h, 32), "right": (32 + off_h, 32)}
    return out + "".join(arrow(*pos[d], d) for d in dirs)


# girar: seta curva branca com contorno preto, abraçando o mouse por cima
ROT_T = 5.0                         # espessura da haste (branca)
ROT_R = 24.8                        # raio do arco
ROT_C = (32.0, 36.0)                # centro do arco
ROT_FROM, ROT_TO = 178.0, 360.0     # meia volta por cima; ponta para baixo, ao lado do mouse
ROT_HEAD_L, ROT_HEAD_W = 10.0, 13.0


def rotate_arrow():
    cx, cy = ROT_C
    a0, a1 = math.radians(ROT_FROM), math.radians(ROT_TO)
    p0 = (cx + ROT_R * math.cos(a0), cy + ROT_R * math.sin(a0))
    p1 = (cx + ROT_R * math.cos(a1), cy + ROT_R * math.sin(a1))
    tg = (-math.sin(a1), math.cos(a1))            # direção do giro no fim
    nm = (math.cos(a1), math.sin(a1))
    tip = (p1[0] + tg[0] * ROT_HEAD_L, p1[1] + tg[1] * ROT_HEAD_L)
    b1 = (p1[0] + nm[0] * ROT_HEAD_W / 2, p1[1] + nm[1] * ROT_HEAD_W / 2)
    b2 = (p1[0] - nm[0] * ROT_HEAD_W / 2, p1[1] - nm[1] * ROT_HEAD_W / 2)
    large = 1 if (ROT_TO - ROT_FROM) % 360 > 180 else 0
    d = "M%.2f %.2f A%g %g 0 %d 1 %.2f %.2f" % (p0[0], p0[1], ROT_R, ROT_R, large, p1[0], p1[1])
    head = " ".join("%.2f,%.2f" % q for q in (tip, b1, b2))
    shaft = '<path d="%s" fill="none" stroke="%s" stroke-width="%g" stroke-linecap="%s"/>'
    return (shaft % (d, K, ROT_T + 2 * OUTLINE, "round")
            + '<polygon points="%s" fill="%s" stroke="%s" stroke-width="%g" stroke-linejoin="round"/>'
            % (head, K, K, 2 * OUTLINE)
            + shaft % (d, W, ROT_T, "butt")
            + '<path d="M%.2f %.2f m0 0" />' % p0
            + '<circle cx="%.2f" cy="%.2f" r="%g" fill="%s"/>' % (p0[0], p0[1], ROT_T / 2, W)
            + '<polygon points="%s" fill="%s"/>' % (head, W))


# deslocamento medido com ferramentas/medir para centralizar o conjunto
ROT_MOUSE_FIX = (-1.8, -2.9)
ROT_MOUSE_H = 46.0                  # altura do mouse dentro do girar


def mouse_rotate():
    sc = ROT_MOUSE_H / 64.0
    cy = 64 - ROT_MOUSE_H / 2
    return '<g transform="translate(%g %g)">%s</g>' % (
        ROT_MOUSE_FIX + (mouse(sc, cy=cy) + rotate_arrow(),))


def designs():
    d = {}
    # direcional -> setas do teclado; uma direção = tecla única grande
    d[4] = keycap_arrow("up")
    d[5] = keycap_arrow("down")
    d[6] = keycap_arrow("left")
    d[7] = keycap_arrow("right")
    d[8] = arrow_keys(set())                    # nenhuma acionada: tudo cinza
    d[9] = arrow_keys(set(DIRS))                # todas
    d[10] = arrow_keys({"up", "down"})
    d[11] = arrow_keys({"left", "right"})
    # analógico esquerdo -> WASD; uma direção = tecla única grande
    d[12] = keycap("W")
    d[13] = keycap("S")
    d[14] = keycap("A")
    d[15] = keycap("D")
    d[16] = keycap("Ctrl", wide=True)
    d[17] = wasd()                              # neutro: tudo branco
    d[18] = wasd({"up", "down"})
    d[19] = wasd({"left", "right"})
    d[20] = wasd()                              # girar: teclado não gira, fica o WASD
    d[58] = wasd()
    # analógico direito -> mouse com setas
    d[21] = mouse_arrows(("up",))
    d[22] = mouse_arrows(("down",))
    d[23] = mouse_arrows(("left",))
    d[24] = mouse_arrows(("right",))
    d[25] = keycap("C")
    d[26] = mouse()
    d[27] = mouse_arrows(("up", "down"))
    d[28] = mouse_arrows(("left", "right"))
    # girar: no PC ninguém gira o mouse; generaliza para "mover o mouse" (4 setas)
    d[29] = mouse_arrows(("up", "down", "left", "right"))
    d[59] = mouse_arrows(("up", "down", "left", "right"))
    # botões
    d[30] = keycap("Shift", wide=True)
    d[31] = keycap("R")
    d[32] = keycap("SPACE", wide=True)
    d[33] = keycap("F")
    d[34] = keycap("Tab", wide=True)
    d[35] = mouse_button("right")
    d[36] = keycap("Q")
    d[37] = mouse_button("left")
    d[38] = keycap("Esc", wide=True)
    d[39] = keycap("V")
    return d


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for n, body in sorted(designs().items()):
        with open(os.path.join(out, "botao_%02d.svg" % n), "w") as f:
            f.write(svg(body))
    print("SVGs:", len(designs()))


if __name__ == "__main__":
    main()

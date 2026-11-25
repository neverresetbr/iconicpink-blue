#!/usr/bin/env python3
"""Prepara, a partir da SUA cópia do jogo, os dois arquivos que o gerador usa.
Só lê o .rpf; nada do jogo vem neste repositório.

  1. Garimpa o data.rpf (rpf9_garimpo.py) e guarda em <pasta_jogo>/:
     - input_icons.gfx: o filme com os ícones de controle originais;
     - gfxfontlib_efigs.gfx: a biblioteca de fontes da interface (a menor que
       tem gta_art_deco_bold e gta_art_deco_condensed_bold, a das línguas
       ocidentais).
  2. Converte os ícones originais para SVG (gfx_svg.py) e normaliza no mesmo
     espaço de 64 (<pasta_jogo>/xbox64/botao_NN.svg), para comparar com os de PC.

Uso: preparar.py <caminho/do/data.rpf> [pasta_jogo]   (padrão: ./game)
"""
import os
import re
import subprocess
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from rpf9_garimpo import carve  # noqa: E402

ICONS_TAG = b"platform_xbsx.input_icons.Main_Button_30"
FONTS_TAG = (b"gta_art_deco_bold", b"gta_art_deco_condensed_bold")
BUTTONS = list(range(4, 40)) + [58, 59]


def raw(data):
    return data[:8] + zlib.decompress(data[8:]) if data[:3] == b"CFX" else data


def main():
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.getcwd(), "game")
    os.makedirs(out, exist_ok=True)
    icons, fonts = None, []
    print("lendo", src, "(pode levar alguns minutos)")
    for off, data in carve(src, []):
        if data[:3] not in (b"GFX", b"CFX"):
            continue
        r = raw(data)
        if ICONS_TAG in r and icons is None:
            icons = data
            print("ícones de controle encontrados em 0x%x" % off)
        if all(t in r for t in FONTS_TAG):
            fonts.append((len(r), off, data))
    if icons is None or not fonts:
        sys.exit("não achei %s no arquivo; confira se é o data.rpf"
                 % ("os ícones" if icons is None else "as fontes"))
    size, off, font = min(fonts)
    print("fontes da interface em 0x%x (%d bytes)" % (off, size))
    with open(os.path.join(out, "input_icons.gfx"), "wb") as f:
        f.write(icons)
    with open(os.path.join(out, "gfxfontlib_efigs.gfx"), "wb") as f:
        f.write(font)

    svg_dir = os.path.join(out, "xbox_svg")
    subprocess.run([sys.executable, "-I", os.path.join(HERE, "gfx_svg.py"),
                    os.path.join(out, "input_icons.gfx"), svg_dir], check=True,
                   stdout=subprocess.DEVNULL)
    x64 = os.path.join(out, "xbox64")
    os.makedirs(x64, exist_ok=True)
    for n in BUTTONS:
        p = os.path.join(svg_dir, "platform_xbsx.input_icons.Main_Button_%d.svg" % n)
        if not os.path.exists(p):
            continue
        s = open(p).read()
        s = re.sub(r'viewBox="[^"]*"', 'viewBox="-3.2 -3.2 70.4 70.4"', s, count=1)
        s = re.sub(r'width="\d+" height="\d+"', 'width="256" height="256"', s, count=1)
        with open(os.path.join(x64, "botao_%02d.svg" % n), "w") as f:
            f.write(s)
    print("pronto:", out)


if __name__ == "__main__":
    main()

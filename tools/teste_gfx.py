#!/usr/bin/env python3
"""Teste da Fase 2: confere o input_icons.gfx gerado por gfx_build.py.

1. Tudo que não é forma nem sprite (código AS3, nomes exportados, classes,
   cabeçalho) continua byte a byte igual ao original.
2. Os 38 sprites Main_Button_N existem, com os mesmos ids e nomes.
3. Relendo o arquivo novo com gfx_svg.py (leitor independente), cada botão
   bate com o SVG aprovado (SSIM >= 0,995, comparado em PNG com ffmpeg).
4. Tamanho: não passa do original (descomprimido e comprimido).

Uso: teste_gfx.py <original.gfx> <novo.gfx> <pasta_svg_pc>
Precisa de ferramentas/raster (macOS) e do ffmpeg.
"""
import os
import re
import struct
import subprocess
import sys
import tempfile
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gfx_build import read_tags  # noqa: E402


def load(p):
    d = open(p, "rb").read()
    return d[:8] + zlib.decompress(d[8:]) if d[:3] == b"CFX" else d


def norm(src, dst):
    s = open(src).read()
    s = re.sub(r'viewBox="[^"]*"', 'viewBox="-16 -16 96 96"', s, count=1)
    s = re.sub(r'width="\d+" height="\d+"', 'width="349" height="349"', s, count=1)
    s = re.sub(r"(<svg[^>]*>)", r'\1<rect x="-16" y="-16" width="96" height="96" fill="rgb(40,90,160)"/>',
               s, count=1)
    open(dst, "w").write(s)


def main():
    orig, new, svg_dir = sys.argv[1:4]
    a, b = load(orig), load(new)
    falhas = []
    ha = 8 + (5 + 4 * (a[8] >> 3) + 7) // 8 + 4
    hb = 8 + (5 + 4 * (b[8] >> 3) + 7) // 8 + 4
    if a[:4] != b[:4] or a[8:ha] != b[8:hb]:
        falhas.append("cabeçalho diferente")
    keep = lambda d, h: [raw for c, raw, p, l in read_tags(d, h) if c not in (32, 39)]  # noqa: E731
    if keep(a, ha) != keep(b, hb):
        falhas.append("tags fora das formas/sprites mudaram")
    spr = lambda d, h: sorted(struct.unpack_from("<H", d, p)[0] for c, raw, p, l in read_tags(d, h) if c == 39)  # noqa: E731
    if spr(a, ha) != spr(b, hb):
        falhas.append("ids dos sprites mudaram")
    if len(b.rstrip(b"\0")) > len(a) or len(zlib.compress(b, 9)) > len(zlib.compress(a, 9)):
        falhas.append("maior que o original")
    tmp = tempfile.mkdtemp()
    subprocess.run([sys.executable, "-I", os.path.join(HERE, "gfx_svg.py"), new, tmp],
                   check=True, stdout=subprocess.DEVNULL)
    piores = []
    for f in sorted(os.listdir(svg_dir)):
        m = re.match(r"botao_(\d+)\.svg$", f)
        if not m:
            continue
        n = int(m.group(1))
        lido = os.path.join(tmp, "platform_xbsx.input_icons.Main_Button_%d.svg" % n)
        if not os.path.exists(lido):
            falhas.append("botão %d não encontrado no arquivo novo" % n)
            continue
        pa, pb = os.path.join(tmp, "a.svg"), os.path.join(tmp, "b.svg")
        norm(os.path.join(svg_dir, f), pa)
        norm(lido, pb)
        for x in (pa, pb):
            subprocess.run([os.path.join(HERE, "raster"), x, x[:-4] + ".png", "480"],
                           check=True, stdout=subprocess.DEVNULL)
        r = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", pa[:-4] + ".png", "-i",
                            pb[:-4] + ".png", "-lavfi", "ssim=stats_file=-", "-f", "null", "-"],
                           capture_output=True, text=True)
        v = float(re.search(r"All:([\d.]+)", r.stdout + r.stderr).group(1))
        piores.append((v, n))
        if v < 0.995:
            falhas.append("botão %d diferente do aprovado (SSIM %.4f)" % (n, v))
    piores.sort()
    print("tamanho: %d bytes (original %d); comprimido %d (original %d)"
          % (len(b), len(a), len(zlib.compress(b, 9)), len(zlib.compress(a, 9))))
    print("SSIM: mínimo %.4f (botão %d), média %.4f, %d botões"
          % (piores[0][0], piores[0][1], sum(v for v, _ in piores) / len(piores), len(piores)))
    for f in falhas:
        print("FALHA:", f)
    print("OK" if not falhas else "%d falha(s)" % len(falhas))
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()

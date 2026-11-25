#!/usr/bin/env python3
"""Teste do padrão de tamanho dos ícones de PC (ANCORA.md, seção 3).

Roda ferramentas/medir em cada SVG e confere:
- centro em (32, 32), tolerância 0,5;
- nada passa de 64 (tolerância 0,3);
- cada tipo no tamanho padrão (tolerância 0,6).
Mouse com setas: as setas NÃO contam no padrão. O mouse é o
padrão (41,6 x 64, centrado em 32,32) e cada seta passa ARROW_REACH dele; o
teste confere a caixa total e o centro esperados para isso.
Uso: teste_padrao.py <pasta_svg>   (sai com código 1 se algo reprovar)
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# N -> (largura, altura) esperadas; None = só o limite de 64 e o centro
SIMPLES = (64, 64)
LARGA = (64, 48)
sys.path.insert(0, HERE)
from teclas_pc import BLOCK_SPAN, MINI, GAP  # noqa: E402
BLOCO = (BLOCK_SPAN + 3, 2 * MINI + GAP + 3)   # passa de 64 de propósito
MOUSE = (41.6, 64)
ESPERADO = {}
for n in (4, 5, 6, 7, 12, 13, 14, 15, 25, 31, 33, 36, 39):
    ESPERADO[n] = SIMPLES
for n in (16, 30, 32, 34, 38):
    ESPERADO[n] = LARGA
for n in (8, 9, 10, 11, 17, 18, 19, 20, 58):
    ESPERADO[n] = BLOCO
for n in (26, 35, 37):
    ESPERADO[n] = MOUSE
sys.path.insert(0, HERE)
from teclas_pc import ARROW_REACH  # noqa: E402
SETAS = {21: "u", 22: "d", 23: "l", 24: "r", 27: "ud", 28: "lr", 29: "udlr", 59: "udlr"}
CENTRO = {}
for n, d in SETAS.items():
    a = ARROW_REACH
    ESPERADO[n] = (MOUSE[0] + a * (("l" in d) + ("r" in d)), MOUSE[1] + a * (("u" in d) + ("d" in d)))
    CENTRO[n] = (32 + a / 2 * (("r" in d) - ("l" in d)), 32 + a / 2 * (("d" in d) - ("u" in d)))


def main():
    d = sys.argv[1]
    files = sorted(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".svg"))
    out = subprocess.run([os.path.join(HERE, "medir")] + files, capture_output=True, text=True).stdout
    falhas = 0
    for line in out.strip().splitlines()[1:]:
        name, w, h, cx, cy = line.split("\t")
        n = int(name.split("_")[1].split(".")[0])
        w, h, cx, cy = map(float, (w, h, cx, cy))
        erros = []
        ex, ey = CENTRO.get(n, (32, 32))
        if abs(cx - ex) > 0.5 or abs(cy - ey) > 0.5:
            erros.append("descentrado (%.1f, %.1f), esperado (%.1f, %.1f)" % (cx, cy, ex, ey))
        if n not in SETAS and ESPERADO.get(n) != BLOCO and (w > 64.3 or h > 64.3):
            erros.append("passa de 64 (%.1f x %.1f)" % (w, h))
        exp = ESPERADO.get(n)
        if exp and (abs(w - exp[0]) > 0.6 or abs(h - exp[1]) > 0.6):
            erros.append("tamanho %.1f x %.1f, esperado %g x %g" % (w, h, exp[0], exp[1]))
        status = "OK  " if not erros else "FALHA"
        falhas += bool(erros)
        print("%s botao_%02d  %5.1f x %5.1f  centro (%.1f, %.1f)  %s"
              % (status, n, w, h, cx, cy, "; ".join(erros)))
    print("\n%d ícones, %d com falha" % (len(out.strip().splitlines()) - 1, falhas))
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()

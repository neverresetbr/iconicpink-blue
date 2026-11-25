#!/usr/bin/env python3
"""Banner do repositório (SVG): só o título e a frase, sem ícones.

Uso: banner.py <saida.svg>
"""
import os
import sys

FONT = 'font-family="Helvetica Neue, Helvetica, Arial, sans-serif"'
PINK, BLUE = "#ff4f9a", "#3d8bff"


def main():
    out = sys.argv[1]
    W, H = 1280, 300
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs>
  <radialGradient id="gb" cx="10%" cy="0%" r="80%"><stop offset="0" stop-color="{BLUE}" stop-opacity=".40"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>
  <radialGradient id="gp" cx="95%" cy="100%" r="75%"><stop offset="0" stop-color="{PINK}" stop-opacity=".36"/><stop offset="1" stop-color="{PINK}" stop-opacity="0"/></radialGradient>
  <linearGradient id="ln" x1="0" x2="1"><stop offset="0" stop-color="{PINK}"/><stop offset="1" stop-color="{BLUE}"/></linearGradient>
</defs>
<rect width="{W}" height="{H}" rx="22" fill="#0d1016"/>
<rect width="{W}" height="{H}" rx="22" fill="url(#gb)"/>
<rect width="{W}" height="{H}" rx="22" fill="url(#gp)"/>
<text x="{W / 2}" y="142" text-anchor="middle" {FONT} font-size="78" font-weight="800" fill="#fff">iconicpink<tspan fill="{PINK}">-</tspan>blue</text>
<rect x="{W / 2 - 90}" y="166" width="180" height="6" rx="3" fill="url(#ln)"/>
<text x="{W / 2}" y="222" text-anchor="middle" {FONT} font-size="24" font-weight="500" fill="#c3c9d4">PC keys (keyboard &amp; mouse) in place of Xbox controller icons</text>
</svg>
'''
    with open(out, "w") as f:
        f.write(svg)
    print("ok:", out)


if __name__ == "__main__":
    main()

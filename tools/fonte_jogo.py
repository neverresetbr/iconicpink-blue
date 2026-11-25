#!/usr/bin/env python3
"""Lê as fontes da interface do jogo (DefineFont3 dentro do gfxfontlib_efigs.gfx,
garimpado do data.rpf) e converte texto em contorno SVG com elas.

O arquivo sai da sua cópia do jogo (ferramentas/preparar.py) e fica fora do
repositório: é do jogo.
Uso como módulo:  text_outline("gta_art_deco_bold", "Shift", 24)
Uso de linha de comando (mostruário):
  fonte_jogo.py <gfxfontlib.gfx> <saida.svg> "texto"
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# onde procurar a biblioteca de fontes (extraída da sua cópia por preparar.py):
# variável GTA_FONTES, depois game/, jogo/ e saida/fontes_jogo/
_CANDIDATES = [os.environ.get("GTA_FONTES", ""),
               os.path.join(HERE, "..", "game", "gfxfontlib_efigs.gfx"),
               os.path.join(HERE, "..", "jogo", "gfxfontlib_efigs.gfx"),
               os.path.join(HERE, "..", "saida", "fontes_jogo", "gfxfontlib_efigs.gfx")]
DEFAULT = next((c for c in _CANDIDATES if c and os.path.exists(c)), _CANDIDATES[1])
EM = 1024 * 20  # DefineFont3: quadro de 1024 unidades em twips


class Bits:
    def __init__(self, data, pos):
        self.d, self.byte, self.bit = data, pos, 0

    def align(self):
        if self.bit:
            self.bit, self.byte = 0, self.byte + 1

    def u(self, n):
        v = 0
        for _ in range(n):
            v = (v << 1) | ((self.d[self.byte] >> (7 - self.bit)) & 1)
            self.bit += 1
            if self.bit == 8:
                self.bit, self.byte = 0, self.byte + 1
        return v

    def s(self, n):
        v = self.u(n)
        return v - (1 << n) if n and v & (1 << (n - 1)) else v


def glyph_edges(data, pos):
    """SHAPE de um glifo: lista de segmentos (x0,y0,ctrl,x1,y1,f0,f1)."""
    b = Bits(data, pos)
    nf, nl = b.u(4), b.u(4)
    x = y = f0 = f1 = 0
    edges = []
    while True:
        if b.u(1) == 0:
            nn, ls, fs1, fs0, mv = b.u(1), b.u(1), b.u(1), b.u(1), b.u(1)
            if not (nn or ls or fs1 or fs0 or mv):
                break
            if mv:
                n = b.u(5)
                x, y = b.s(n), b.s(n)
            if fs0:
                f0 = b.u(nf)
            if fs1:
                f1 = b.u(nf)
            if ls:
                b.u(nl)
        elif b.u(1):
            n = b.u(4) + 2
            if b.u(1):
                dx, dy = b.s(n), b.s(n)
            elif b.u(1):
                dx, dy = 0, b.s(n)
            else:
                dx, dy = b.s(n), 0
            edges.append((x, y, None, x + dx, y + dy, f0, f1))
            x, y = x + dx, y + dy
        else:
            n = b.u(4) + 2
            cx, cy, ax, ay = b.s(n), b.s(n), b.s(n), b.s(n)
            c = (x + cx, y + cy)
            edges.append((x, y, c, c[0] + ax, c[1] + ay, f0, f1))
            x, y = c[0] + ax, c[1] + ay
    return edges


def contours(edges):
    """Liga os segmentos preenchidos em contornos fechados (coordenadas em twips)."""
    segs = [(e[0], e[1], e[2], e[3], e[4]) for e in edges if e[6]]
    segs += [(e[3], e[4], e[2], e[0], e[1]) for e in edges if e[5] and not e[6]]
    by_start = {}
    for s in segs:
        by_start.setdefault((s[0], s[1]), []).append(s)
    used, out = set(), []
    for s in segs:
        if id(s) in used:
            continue
        used.add(id(s))
        loop, start, cur = [s], (s[0], s[1]), (s[3], s[4])
        while cur != start:
            nxt = next((t for t in by_start.get(cur, []) if id(t) not in used), None)
            if nxt is None:
                break
            used.add(id(nxt))
            loop.append(nxt)
            cur = (nxt[3], nxt[4])
        out.append(loop)
    return out


class Font:
    def __init__(self, name, glyphs, advance, ascent, descent):
        self.name, self.glyphs, self.advance = name, glyphs, advance
        self.ascent, self.descent = ascent, descent


def load(path=DEFAULT):
    data = open(path, "rb").read()
    if data[:3] == b"CFX":
        import zlib
        data = data[:8] + zlib.decompress(data[8:])
    b = Bits(data, 8)
    nbits = b.u(5)
    pos = 8 + (5 + 4 * nbits + 7) // 8 + 4
    fonts = {}
    while pos < len(data):
        h = struct.unpack_from("<H", data, pos)[0]
        code, ln = h >> 6, h & 0x3F
        pos += 2
        if ln == 0x3F:
            ln = struct.unpack_from("<I", data, pos)[0]
            pos += 4
        if code == 75:
            fonts.update([_font(data, pos)])
        pos += ln
        if code == 0:
            break
    return fonts


def _font(data, p):
    flags = data[p + 2]
    wide_off, wide_codes, has_layout = flags & 0x08, flags & 0x04, flags & 0x80
    nl = data[p + 4]
    name = data[p + 5:p + 5 + nl].rstrip(b"\0").decode("latin1")
    q = p + 5 + nl
    n = struct.unpack_from("<H", data, q)[0]
    q += 2
    table = q
    fmt, size = ("<I", 4) if wide_off else ("<H", 2)
    offsets = [struct.unpack_from(fmt, data, table + i * size)[0] for i in range(n)]
    code_off = struct.unpack_from(fmt, data, table + n * size)[0]
    codes_at = table + code_off
    if wide_codes:
        codes = [struct.unpack_from("<H", data, codes_at + 2 * i)[0] for i in range(n)]
        after = codes_at + 2 * n
    else:
        codes = list(data[codes_at:codes_at + n])
        after = codes_at + n
    glyphs = {}
    for i, c in enumerate(codes):
        glyphs[chr(c)] = contours(glyph_edges(data, table + offsets[i]))
    advance, ascent, descent = {}, EM * 0.8, EM * 0.2
    if has_layout:
        ascent, descent = struct.unpack_from("<hh", data, after)
        adv = struct.unpack_from("<%dh" % n, data, after + 6)
        advance = {chr(c): adv[i] for i, c in enumerate(codes)}
    return name, Font(name, glyphs, advance, ascent, descent)


_cache = {}


def font(name, path=DEFAULT):
    if path not in _cache:
        _cache[path] = load(path)
    return _cache[path][name]


def text_outline(name, s, size, path=DEFAULT):
    """Mesmo formato do texto_svg: d, w (avanço), caixa x0..y1 e cap."""
    f = font(name, path)
    k = size / float(EM)
    d, x = [], 0.0
    xs, ys = [], []
    for ch in s:
        for loop in f.glyphs.get(ch, []):
            for j, (x0, y0, c, x1, y1) in enumerate(loop):
                if j == 0:
                    d.append("M%.2f %.2f" % (x + x0 * k, y0 * k))
                if c:
                    d.append("Q%.2f %.2f %.2f %.2f" % (x + c[0] * k, c[1] * k, x + x1 * k, y1 * k))
                else:
                    d.append("L%.2f %.2f" % (x + x1 * k, y1 * k))
                xs += [x + x0 * k, x + x1 * k]
                ys += [y0 * k, y1 * k]
            d.append("Z")
        x += f.advance.get(ch, EM * 0.5) * k
    cap = font_cap(f) * k
    return {"d": "".join(d), "w": x, "x0": min(xs), "x1": max(xs), "y0": min(ys),
            "y1": max(ys), "cap": cap}


def font_cap(f):
    ys = [p for loop in f.glyphs.get("H", []) for seg in loop for p in (seg[1], seg[4])]
    return -min(ys) if ys else f.ascent * 0.7


def main():
    src, out, sample = sys.argv[1], sys.argv[2], sys.argv[3]
    fonts = load(src)
    rows, y = [], 60
    for name in fonts:
        g = text_outline(name, sample, 40, src)
        rows.append('<text x="10" y="%d" font-size="14" fill="#888">%s</text>' % (y - 44, name))
        rows.append('<path transform="translate(10 %d)" d="%s" fill="#000"/>' % (y, g["d"]))
        y += 80
    with open(out, "w") as f:
        f.write('<svg xmlns="http://www.w3.org/2000/svg" width="900" height="%d" viewBox="0 0 900 %d">'
                '<rect width="900" height="%d" fill="#fff"/>%s</svg>' % (y, y, y, "".join(rows)))
    print("fontes:", ", ".join(fonts))


if __name__ == "__main__":
    main()

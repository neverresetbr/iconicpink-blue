#!/usr/bin/env python3
"""Converte as formas vetoriais de um .gfx (Scaleform, cabeçalho GFX = SWF)
em SVG: uma por forma (DefineShape*) e uma por símbolo exportado (sprite
com nome, ex.: platform_xbsx.input_icons.Main_Button_5), montada a partir
do primeiro quadro.

Uso: gfx_svg.py <arquivo.gfx> <pasta_saida>
Só lê o arquivo. Suporta preenchimento sólido e gradiente (aprox.), linhas,
matrizes e transformação de cor do PlaceObject2/3.
"""
import os
import struct
import sys
import zlib


class Bits:
    def __init__(self, data, pos=0):
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

    def fb(self, n):
        return self.s(n) / 65536.0

    def u8(self):
        self.align()
        v = self.d[self.byte]
        self.byte += 1
        return v

    def u16(self):
        self.align()
        v = struct.unpack_from("<H", self.d, self.byte)[0]
        self.byte += 2
        return v


def rect(b):
    b.align()
    n = b.u(5)
    r = [b.s(n) for _ in range(4)]
    b.align()
    return r  # xmin xmax ymin ymax (twips)


def matrix(b):
    b.align()
    sx = sy = 1.0
    r0 = r1 = 0.0
    if b.u(1):
        n = b.u(5)
        sx, sy = b.fb(n), b.fb(n)
    if b.u(1):
        n = b.u(5)
        r0, r1 = b.fb(n), b.fb(n)
    n = b.u(5)
    tx, ty = b.s(n), b.s(n)
    b.align()
    return (sx, r0, r1, sy, tx, ty)  # a b c d e f (SVG: a=sx b=r0 c=r1 d=sy)


def cxform(b, alpha=True):
    b.align()
    has_add, has_mult = b.u(1), b.u(1)
    n = b.u(4)
    k = 4 if alpha else 3
    mult = [b.s(n) / 256.0 for _ in range(k)] if has_mult else [1.0] * k
    add = [b.s(n) for _ in range(k)] if has_add else [0] * k
    b.align()
    if not alpha:
        mult.append(1.0)
        add.append(0)
    return mult, add


def color(b, alpha):
    r, g, bl = b.u8(), b.u8(), b.u8()
    a = b.u8() if alpha else 255
    return (r, g, bl, a)


def fill_styles(b, shape_ver):
    n = b.u8()
    if n == 0xFF:
        n = b.u16()
    out = []
    for _ in range(n):
        t = b.u8()
        if t == 0x00:
            out.append(("solid", color(b, shape_ver >= 3)))
        elif t in (0x10, 0x12, 0x13):
            m = matrix(b)
            b.align()
            b.u(2)
            b.u(2)
            ng = b.u(4)
            stops = []
            for _ in range(ng):
                ratio = b.u8()
                stops.append((ratio, color(b, shape_ver >= 3)))
            if t == 0x13:
                b.u16()
            out.append(("grad", (t, m, stops)))
        elif 0x40 <= t <= 0x43:
            bid = b.u16()
            matrix(b)
            out.append(("bitmap", bid))
        else:
            raise ValueError("fill style %x" % t)
    return out


def line_styles(b, shape_ver):
    n = b.u8()
    if n == 0xFF:
        n = b.u16()
    out = []
    for _ in range(n):
        w = b.u16()
        if shape_ver == 4:
            b.align()
            b.u(2)
            join = b.u(2)
            has_fill = b.u(1)
            b.u(1); b.u(1); b.u(1); b.u(5); b.u(1); b.u(2)
            if join == 2:
                b.u16()
            if has_fill:
                fs = fill_styles_one(b)
                out.append((w, fs))
            else:
                out.append((w, color(b, True)))
        else:
            out.append((w, color(b, shape_ver >= 3)))
    return out


def fill_styles_one(b):
    t = b.u8()
    if t == 0:
        return color(b, True)
    m = matrix(b)
    b.align(); b.u(4)
    ng = b.u(4) if False else None
    return (128, 128, 128, 255)


def shape(data, pos, ver):
    b = Bits(data, pos)
    sid = b.u16()
    bounds = rect(b)
    if ver == 4:
        rect(b)
        b.u8()
    fills = fill_styles(b, ver)
    lines = line_styles(b, ver)
    b.align()
    nf, nl = b.u(4), b.u(4)
    x = y = 0
    f0 = f1 = ln = 0
    groups = []  # (fills, lines, edges)
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
                ln = b.u(nl)
            if nn:
                groups.append((fills, lines, edges))
                edges = []
                fills = fill_styles(b, ver)
                lines = line_styles(b, ver)
                b.align()
                nf, nl = b.u(4), b.u(4)
                f0 = f1 = ln = 0
        else:
            if b.u(1):
                n = b.u(4) + 2
                if b.u(1):
                    dx, dy = b.s(n), b.s(n)
                elif b.u(1):
                    dx, dy = 0, b.s(n)
                else:
                    dx, dy = b.s(n), 0
                edges.append((x, y, None, x + dx, y + dy, f0, f1, ln))
                x, y = x + dx, y + dy
            else:
                n = b.u(4) + 2
                cx, cy, ax, ay = b.s(n), b.s(n), b.s(n), b.s(n)
                c = (x + cx, y + cy)
                edges.append((x, y, c, c[0] + ax, c[1] + ay, f0, f1, ln))
                x, y = c[0] + ax, c[1] + ay
    groups.append((fills, lines, edges))
    return sid, bounds, groups


def rgba(c, cx=None):
    r, g, b, a = c
    if cx:
        (mr, mg, mb, ma), (ar, ag, ab, aa) = cx
        r, g, b, a = (max(0, min(255, int(v * m + ad))) for v, m, ad in
                      ((r, mr, ar), (g, mg, ag), (b, mb, ab), (a, ma, aa)))
    return "rgb(%d,%d,%d)" % (r, g, b), a / 255.0


def seg_d(seg, first):
    x0, y0, c, x1, y1 = seg
    s = ("M%g %g" % (x0 / 20, y0 / 20)) if first else ""
    if c:
        return s + "Q%g %g %g %g" % (c[0] / 20, c[1] / 20, x1 / 20, y1 / 20)
    return s + "L%g %g" % (x1 / 20, y1 / 20)


def chain(segs):
    """Liga segmentos (x0,y0,c,x1,y1) em contornos fechados."""
    by_start = {}
    for s in segs:
        by_start.setdefault((s[0], s[1]), []).append(s)
    used = set()
    out = []
    for s in segs:
        if id(s) in used:
            continue
        d = seg_d(s, True)
        used.add(id(s))
        start, cur = (s[0], s[1]), (s[3], s[4])
        while cur != start:
            nxt = next((t for t in by_start.get(cur, []) if id(t) not in used), None)
            if nxt is None:
                break
            used.add(id(nxt))
            d += seg_d(nxt, False)
            cur = (nxt[3], nxt[4])
        out.append(d + "Z")
    return "".join(out)


def shape_svg(groups, cx=None):
    parts = []
    for fills, lines, edges in groups:
        for fi, style in enumerate(fills, 1):
            segs = [(e[0], e[1], e[2], e[3], e[4]) for e in edges if e[6] == fi]
            segs += [(e[3], e[4], e[2], e[0], e[1]) for e in edges if e[5] == fi]
            if not segs:
                continue
            if style[0] == "solid":
                col, op = rgba(style[1], cx)
            elif style[0] == "grad":
                stops = style[1][2]
                mid = stops[len(stops) // 2][1]
                col, op = rgba(mid, cx)
            else:
                col, op = "rgb(255,0,255)", 1.0
            parts.append('<path d="%s" fill="%s" fill-opacity="%.3f" fill-rule="nonzero"/>'
                         % (chain(segs), col, op))
        for li, (w, c) in enumerate(lines, 1):
            es = [e for e in edges if e[7] == li]
            if not es:
                continue
            d = "".join(seg_d((e[0], e[1], e[2], e[3], e[4]), True) for e in es)
            col, op = rgba(c if len(c) == 4 else (128, 128, 128, 255), cx)
            parts.append('<path d="%s" fill="none" stroke="%s" stroke-opacity="%.3f" '
                         'stroke-width="%g" stroke-linecap="round" stroke-linejoin="round"/>'
                         % (d, col, op, max(w / 20, 0.5)))
    return "".join(parts)


def tags(data, pos, end):
    while pos < end:
        h = struct.unpack_from("<H", data, pos)[0]
        code, ln = h >> 6, h & 0x3F
        pos += 2
        if ln == 0x3F:
            ln = struct.unpack_from("<I", data, pos)[0]
            pos += 4
        yield code, pos, ln
        pos += ln
        if code == 0:
            break


def place(data, pos, ln, code):
    b = Bits(data, pos)
    if code == 26:
        flags = b.u8()
        flags2 = 0
    else:
        flags, flags2 = b.u8(), b.u8()
    depth = b.u16()
    if code == 70 and (flags2 & 0x08 or (flags2 & 0x10 and flags & 0x02)):
        # nome de classe (raro aqui): pula string
        while data[b.byte]:
            b.byte += 1
        b.byte += 1
    cid = b.u16() if flags & 0x02 else None
    m = matrix(b) if flags & 0x04 else None
    cx = cxform(b) if flags & 0x08 else None
    return depth, cid, m, cx, bool(flags & 0x01)


def main():
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    data = open(src, "rb").read()
    sig = data[:3]
    if sig in (b"CFX", b"CWS"):
        data = data[:8] + zlib.decompress(data[8:])
    b = Bits(data, 8)
    rect(b)
    pos = b.byte + 4
    shapes, sprites, symbols = {}, {}, {}
    for code, p, ln in tags(data, pos, len(data)):
        if code in (2, 22, 32, 83):
            ver = {2: 1, 22: 2, 32: 3, 83: 4}[code]
            try:
                sid, bounds, groups = shape(data, p, ver)
                shapes[sid] = (bounds, groups)
            except Exception as e:  # noqa: BLE001
                print("forma não lida:", e)
        elif code == 39:
            sid, frames = struct.unpack_from("<HH", data, p)
            display = {}
            for c2, p2, l2 in tags(data, p + 4, p + ln):
                if c2 in (26, 70):
                    depth, cid, m, cx, move = place(data, p2, l2, c2)
                    old = display.get(depth, (None, None, None))
                    display[depth] = (cid if cid is not None else old[0],
                                      m if m is not None else old[1],
                                      cx if cx is not None else old[2])
                elif c2 == 28:
                    display.pop(struct.unpack_from("<H", data, p2)[0], None)
                elif c2 == 1:
                    break
            sprites[sid] = display
        elif code == 76:
            n = struct.unpack_from("<H", data, p)[0]
            q = p + 2
            for _ in range(n):
                tid = struct.unpack_from("<H", data, q)[0]
                e = data.index(b"\0", q + 2)
                symbols[tid] = data[q + 2:e].decode("latin1")
                q = e + 1

    def render(cid, mat, cx, depth=0):
        if depth > 12:
            return "", None
        if cid in shapes:
            bounds, groups = shapes[cid]
            return shape_svg(groups, cx), bounds
        if cid in sprites:
            body, bb = "", None
            for d in sorted(sprites[cid]):
                ccid, m, ccx = sprites[cid][d]
                inner, ib = render(ccid, m, ccx or cx, depth + 1)
                if not inner:
                    continue
                m = m or (1, 0, 0, 1, 0, 0)
                body += '<g data-cid="%d" transform="matrix(%g %g %g %g %g %g)">%s</g>' % (
                    ccid, m[0], m[1], m[2], m[3], m[4] / 20, m[5] / 20, inner)
                if ib:
                    xs = [ib[0], ib[1]]
                    ys = [ib[2], ib[3]]
                    pts = [(m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5])
                           for x in xs for y in ys]
                    nb = [min(p[0] for p in pts), max(p[0] for p in pts),
                          min(p[1] for p in pts), max(p[1] for p in pts)]
                    bb = nb if bb is None else [min(bb[0], nb[0]), max(bb[1], nb[1]),
                                                min(bb[2], nb[2]), max(bb[3], nb[3])]
            return body, bb
        return "", None

    def write(name, cid):
        body, bb = render(cid, None, None)
        if not body or not bb:
            return False
        x0, x1, y0, y1 = (v / 20 for v in bb)
        w, h = max(x1 - x0, 1), max(y1 - y0, 1)
        pad = max(w, h) * 0.05
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="%g %g %g %g" '
               'width="%d" height="%d">%s</svg>') % (
            x0 - pad, y0 - pad, w + 2 * pad, h + 2 * pad,
            256, max(int(256 * (h + 2 * pad) / (w + 2 * pad)), 1), body)
        with open(os.path.join(out, name + ".svg"), "w") as f:
            f.write(svg)
        return True

    n = 0
    for cid, name in sorted(symbols.items()):
        if cid and write(name.replace(":", "_"), cid):
            n += 1
    for cid in sorted(shapes):
        write("forma_%04d" % cid, cid)
    print("formas %d, sprites %d, símbolos %d (SVG de símbolo: %d)"
          % (len(shapes), len(sprites), len(symbols), n))


if __name__ == "__main__":
    main()

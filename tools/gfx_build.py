#!/usr/bin/env python3
"""Fase 2: grava os desenhos de PC (SVGs de teclas_pc.py) dentro de uma CÓPIA
do input_icons.gfx. Só o desenho muda:

- cada sprite platform_xbsx.input_icons.Main_Button_N mantém o id, o nome
  exportado, a classe AS3 e a posição; o conteúdo dele passa a ser as nossas
  formas (uma DefineShape3 por elemento do SVG, em profundidades 1, 2, 3...);
- as formas antigas saem; o código (DoABC), ExportAssets e SymbolClass ficam
  byte a byte iguais.

Convenção das formas, igual à dos originais: preenchimento em fillStyle0 com o
contorno externo no sentido horário e os furos no anti-horário; coordenadas
em twips (1/20) no espaço 0..64; curvas só quadráticas (as cúbicas e os
cantos arredondados viram quadráticas).

Uso: gfx_build.py <input_icons.gfx original> <pasta_svg_pc> <saida.gfx> [--tamanho-original]
  --tamanho-original: completa com zeros depois da tag End até o tamanho do
  original (para caber no mesmo lugar do .rpf, se for preciso; teste da Fase 3).
"""
import math
import os
import re
import struct
import sys
import xml.etree.ElementTree as ET
import zlib

TW = 20  # twips por unidade


# ---------------------------------------------------------------- geometria
def mat_mul(a, b):
    # matriz afim (a, b, c, d, e, f): x' = a x + c y + e ; y' = b x + d y + f
    return (a[0] * b[0] + a[2] * b[1], a[1] * b[0] + a[3] * b[1],
            a[0] * b[2] + a[2] * b[3], a[1] * b[2] + a[3] * b[3],
            a[0] * b[4] + a[2] * b[5] + a[4], a[1] * b[4] + a[3] * b[5] + a[5])


IDENT = (1, 0, 0, 1, 0, 0)


def parse_transform(s):
    m = IDENT
    for name, args in re.findall(r"(\w+)\(([^)]*)\)", s or ""):
        v = [float(x) for x in re.split(r"[ ,]+", args.strip()) if x]
        if name == "translate":
            t = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif name == "scale":
            t = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif name == "matrix":
            t = tuple(v)
        else:
            raise ValueError("transform não suportado: " + name)
        m = mat_mul(m, t)
    return m


def apply(m, p):
    return (m[0] * p[0] + m[2] * p[1] + m[4], m[1] * p[0] + m[3] * p[1] + m[5])


def cubic_to_quads(p0, c1, c2, p3, n=4):
    """Aproxima uma cúbica por n quadráticas (subdivisão uniforme)."""
    def pt(t):
        u = 1 - t
        return (u ** 3 * p0[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t ** 3 * p3[0],
                u ** 3 * p0[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t ** 3 * p3[1])

    def dpt(t):
        u = 1 - t
        return (3 * u * u * (c1[0] - p0[0]) + 6 * u * t * (c2[0] - c1[0]) + 3 * t * t * (p3[0] - c2[0]),
                3 * u * u * (c1[1] - p0[1]) + 6 * u * t * (c2[1] - c1[1]) + 3 * t * t * (p3[1] - c2[1]))
    out = []
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        a, b = pt(t0), pt(t1)
        da, db = dpt(t0), dpt(t1)
        # controle = cruzamento das tangentes; se paralelas, ponto médio
        h = t1 - t0
        da, db = (da[0] * h, da[1] * h), (db[0] * h, db[1] * h)
        den = da[0] * db[1] - da[1] * db[0]
        if abs(den) < 1e-9:
            c = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        else:
            s = ((b[0] - a[0]) * db[1] - (b[1] - a[1]) * db[0]) / den
            c = (a[0] + da[0] * s, a[1] + da[1] * s)
        out.append((c, b))
    return out


def arc_quads(cx, cy, r, a0, a1, n=2):
    """Arco de círculo (graus, sentido de a0 para a1) em n quadráticas."""
    out = []
    for i in range(n):
        t0 = math.radians(a0 + (a1 - a0) * i / n)
        t1 = math.radians(a0 + (a1 - a0) * (i + 1) / n)
        tm = (t0 + t1) / 2
        k = r / math.cos((t1 - t0) / 2)
        out.append(((cx + k * math.cos(tm), cy + k * math.sin(tm)),
                    (cx + r * math.cos(t1), cy + r * math.sin(t1))))
    return out


def path_subpaths(d):
    """d de SVG (M L H V C Q Z, absolutos) -> subcaminhos [(início, [(c|None, p)]), fechado]."""
    toks = re.findall(r"[MLHVCQZmlhvcqz]|-?\d*\.?\d+(?:e-?\d+)?", d)
    i, cmd, cur, start = 0, None, (0.0, 0.0), (0.0, 0.0)
    subs, segs = [], None

    def num():
        nonlocal i
        v = float(toks[i])
        i += 1
        return v
    while i < len(toks):
        if re.match(r"[A-Za-z]", toks[i]):
            cmd = toks[i]
            i += 1
            if cmd.islower() and cmd not in "z":
                raise ValueError("comando relativo não suportado: " + cmd)
        if cmd == "M":
            if segs:
                subs.append([start, segs, False])
            cur = start = (num(), num())
            segs = []
            cmd = "L"
        elif cmd == "L":
            cur = (num(), num())
            segs.append((None, cur))
        elif cmd == "H":
            cur = (num(), cur[1])
            segs.append((None, cur))
        elif cmd == "V":
            cur = (cur[0], num())
            segs.append((None, cur))
        elif cmd == "Q":
            c = (num(), num())
            cur = (num(), num())
            segs.append((c, cur))
        elif cmd == "C":
            c1, c2, p = (num(), num()), (num(), num()), (num(), num())
            segs.extend(cubic_to_quads(cur, c1, c2, p))
            cur = p
        elif cmd in "Zz":
            if segs is not None:
                if cur != start:
                    segs.append((None, start))
                subs.append([start, segs, True])
            segs, cur = None, start
            cmd = None
        else:
            raise ValueError("comando inesperado: %r" % cmd)
    if segs:
        subs.append([start, segs, False])
    return subs


def rect_subpath(x, y, w, h, rx):
    rx = min(rx, w / 2, h / 2)
    if rx <= 0:
        return [[(x, y), [(None, (x + w, y)), (None, (x + w, y + h)), (None, (x, y + h)),
                          (None, (x, y))], True]]
    segs = [(None, (x + w - rx, y))]
    segs += arc_quads(x + w - rx, y + rx, rx, -90, 0)
    segs.append((None, (x + w, y + h - rx)))
    segs += arc_quads(x + w - rx, y + h - rx, rx, 0, 90)
    segs.append((None, (x + rx, y + h)))
    segs += arc_quads(x + rx, y + h - rx, rx, 90, 180)
    segs.append((None, (x, y + rx)))
    segs += arc_quads(x + rx, y + rx, rx, 180, 270)
    return [[(x + rx, y), segs, True]]


COLORS = {"#fff": (255, 255, 255), "#ffffff": (255, 255, 255), "#000": (0, 0, 0),
          "#000000": (0, 0, 0), "white": (255, 255, 255), "black": (0, 0, 0)}


def color(s):
    if not s or s == "none":
        return None
    s = s.strip().lower()
    if s in COLORS:
        return COLORS[s]
    m = re.match(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", s)
    if m:
        return tuple(int(v) for v in m.groups())
    raise ValueError("cor não suportada: " + s)


def svg_elements(path):
    """Elementos desenháveis do SVG, em ordem, já com a matriz acumulada."""
    root = ET.parse(path).getroot()
    out = []

    def walk(el, m, inh):
        tag = el.tag.split("}")[-1]
        m = mat_mul(m, parse_transform(el.get("transform")))
        st = dict(inh)
        for k in ("fill", "stroke", "stroke-width"):
            if el.get(k) is not None:
                st[k] = el.get(k)
        if tag in ("svg", "g"):
            for ch in el:
                walk(ch, m, st)
            return
        if tag == "path":
            subs = path_subpaths(el.get("d"))
        elif tag == "rect":
            subs = rect_subpath(float(el.get("x", 0)), float(el.get("y", 0)),
                                float(el.get("width")), float(el.get("height")),
                                float(el.get("rx", 0)))
        elif tag == "polygon":
            pts = [float(v) for v in re.split(r"[ ,]+", el.get("points").strip())]
            pts = list(zip(pts[::2], pts[1::2]))
            subs = [[pts[0], [(None, p) for p in pts[1:]] + [(None, pts[0])], True]]
        else:
            raise ValueError("elemento não suportado: " + tag)
        out.append((subs, m, color(st.get("fill", "#000")), color(st.get("stroke")),
                    float(st.get("stroke-width", 1))))
    walk(root, IDENT, {})
    return out


# ------------------------------------------------------------ codificação SWF
class BitW:
    def __init__(self):
        self.bits = []

    def u(self, v, n):
        for i in range(n - 1, -1, -1):
            self.bits.append((v >> i) & 1)

    def s(self, v, n):
        self.u(v & ((1 << n) - 1), n)

    def align(self):
        while len(self.bits) % 8:
            self.bits.append(0)

    def bytes(self):
        self.align()
        return bytes(int("".join(map(str, self.bits[i:i + 8])), 2) for i in range(0, len(self.bits), 8))


def sbits(*vals):
    return max(max((abs(v).bit_length() + 1) for v in vals), 1)


def rect_bytes(x0, x1, y0, y1):
    n = sbits(x0, x1, y0, y1)
    w = BitW()
    w.u(n, 5)
    for v in (x0, x1, y0, y1):
        w.s(v, n)
    return w.bytes()


def poly_of(start, segs):
    """Polígono aproximado (pontos de controle entram como vértices)."""
    pts = [start]
    for c, p in segs:
        if c:
            pts.append(c)
        pts.append(p)
    return pts


def point_in(poly, pt):
    x, y, inside = pt[0], pt[1], False
    for i in range(len(poly)):
        x0, y0 = poly[i - 1]
        x1, y1 = poly[i]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside


def reverse(start, segs):
    pts = [start] + [p for _, p in segs]
    ctrls = [c for c, _ in segs]
    new = []
    for i in range(len(segs) - 1, -1, -1):
        new.append((ctrls[i], pts[i]))
    return pts[-1], new


def shape_tag(sid, subs, m, fill, stroke, sw):
    # transforma e arredonda para twips
    def tw(p):
        q = apply(m, p)
        return (int(round(q[0] * TW)), int(round(q[1] * TW)))
    scale = math.sqrt(abs(m[0] * m[3] - m[1] * m[2]))
    tsubs = []
    for start, segs, closed in subs:
        s0 = tw(start)
        ts = [((tw(c) if c else None), tw(p)) for c, p in segs]
        tsubs.append([s0, ts, closed])
    # preenchimento: externo horário, furo anti-horário (par/ímpar de inclusão)
    if fill is not None:
        polys = [poly_of(s, g) for s, g, _ in tsubs]
        for i, (s, g, closed) in enumerate(tsubs):
            if not closed:
                continue
            probe = polys[i][0]
            depth = sum(1 for j, pj in enumerate(polys) if j != i and point_in(pj, probe))
            area = sum(polys[i][k - 1][0] * polys[i][k][1] - polys[i][k][0] * polys[i][k - 1][1]
                       for k in range(len(polys[i]))) / 2.0
            want_positive = depth % 2 == 0
            if (area > 0) != want_positive:
                tsubs[i][0], tsubs[i][1] = reverse(s, g)
    lw = int(round(sw * scale * TW)) if stroke is not None else 0
    xs = [p[0] for s, g, _ in tsubs for p in [s] + [q for c, pp in g for q in ([c] if c else []) + [pp]]]
    ys = [p[1] for s, g, _ in tsubs for p in [s] + [q for c, pp in g for q in ([c] if c else []) + [pp]]]
    h = lw // 2
    body = struct.pack("<H", sid) + rect_bytes(min(xs) - h, max(xs) + h, min(ys) - h, max(ys) + h)
    if fill is not None:
        body += bytes([1, 0x00]) + bytes(fill) + b"\xff"
    else:
        body += b"\x00"
    if stroke is not None:
        body += bytes([1]) + struct.pack("<H", lw) + bytes(stroke) + b"\xff"
    else:
        body += b"\x00"
    nf, nl = (1 if fill is not None else 0), (1 if stroke is not None else 0)
    w = BitW()
    w.u(nf, 4)
    w.u(nl, 4)
    first = True
    for s, g, closed in tsubs:
        # StyleChangeRecord com moveTo absoluto
        w.u(0, 1)
        w.u(0, 1)                     # StateNewStyles
        w.u(1 if (first and nl) else 0, 1)   # StateLineStyle
        w.u(0, 1)                     # StateFillStyle1
        w.u(1 if (first and nf) else 0, 1)   # StateFillStyle0
        w.u(1, 1)                     # StateMoveTo
        n = sbits(s[0], s[1])
        w.u(n, 5)
        w.s(s[0], n)
        w.s(s[1], n)
        if first and nf:
            w.u(1, nf)
        if first and nl:
            w.u(1, nl)
        first = False
        cur = s
        for c, p in g:
            if c is None:
                dx, dy = p[0] - cur[0], p[1] - cur[1]
                if dx == 0 and dy == 0:
                    continue
                n = max(sbits(dx, dy), 2)
                w.u(1, 1)
                w.u(1, 1)
                w.u(n - 2, 4)
                if dx != 0 and dy != 0:
                    w.u(1, 1)
                    w.s(dx, n)
                    w.s(dy, n)
                else:
                    w.u(0, 1)
                    w.u(1 if dx == 0 else 0, 1)
                    w.s(dy if dx == 0 else dx, n)
            else:
                cx, cy = c[0] - cur[0], c[1] - cur[1]
                ax, ay = p[0] - c[0], p[1] - c[1]
                n = max(sbits(cx, cy, ax, ay), 2)
                w.u(1, 1)
                w.u(0, 1)
                w.u(n - 2, 4)
                for v in (cx, cy, ax, ay):
                    w.s(v, n)
            cur = p
    w.u(0, 6)                         # EndShapeRecord
    body += w.bytes()
    return tag(32, body)


def tag(code, body):
    if len(body) < 0x3F and code not in (32, 39):
        return struct.pack("<H", (code << 6) | len(body)) + body
    return struct.pack("<HI", (code << 6) | 0x3F, len(body)) + body


# --------------------------------------------------------------- montagem
def read_tags(d, pos):
    out = []
    while pos < len(d):
        h = struct.unpack_from("<H", d, pos)[0]
        code, ln = h >> 6, h & 0x3F
        p = pos + 2
        if ln == 0x3F:
            ln = struct.unpack_from("<I", d, p)[0]
            p += 4
        out.append((code, d[pos:p + ln], p, ln))
        pos = p + ln
        if code == 0:
            break
    return out


def main():
    src, svg_dir, out = sys.argv[1:4]
    pad = "--tamanho-original" in sys.argv[4:]
    d = open(src, "rb").read()
    if d[:3] == b"CFX":
        d = d[:8] + zlib.decompress(d[8:])
    nb = d[8] >> 3
    hdr_end = 8 + (5 + 4 * nb + 7) // 8 + 4
    tags = read_tags(d, hdr_end)
    # nomes exportados: id do sprite -> N
    names = {}
    for code, raw, p, ln in tags:
        if code == 56:
            n = struct.unpack_from("<H", d, p)[0]
            q = p + 2
            for _ in range(n):
                i = struct.unpack_from("<H", d, q)[0]
                e = d.index(b"\0", q + 2)
                m = re.search(rb"Main_Button_(\d+)$", d[q + 2:e])
                if m:
                    names[i] = int(m.group(1))
                q = e + 1
    used_ids = {struct.unpack_from("<H", d, p)[0] for code, raw, p, ln in tags if code in (32, 39)}
    next_id = max(used_ids) + 1
    out_tags, new_shapes, total_shape_bytes = [], 0, 0
    for code, raw, p, ln in tags:
        if code == 32:
            continue                         # formas antigas saem
        if code == 39:
            sid = struct.unpack_from("<H", d, p)[0]
            n = names.get(sid)
            svg = os.path.join(svg_dir, "botao_%02d.svg" % n) if n is not None else None
            if not svg or not os.path.exists(svg):
                raise SystemExit("sem desenho para o sprite %d (N=%s)" % (sid, n))
            places = b""
            for depth, (subs, m, fill, stroke, sw) in enumerate(svg_elements(svg), 1):
                if fill is None and stroke is None:
                    continue
                st = shape_tag(next_id, subs, m, fill, stroke, sw)
                out_tags.append(st)
                total_shape_bytes += len(st)
                new_shapes += 1
                # PlaceObject2: HasCharacter + HasMatrix, matriz identidade mínima (1 byte)
                body = bytes([0x06]) + struct.pack("<HH", depth, next_id) + b"\x00"
                places += tag(26, body)
                next_id += 1
            frames = struct.unpack_from("<H", d, p + 2)[0]
            spr = struct.pack("<HH", sid, frames) + places + b"\x00\x00"
            out_tags.append(tag(39, spr))
            continue
        out_tags.append(raw)
    body = d[8:hdr_end] + b"".join(out_tags)
    if pad:
        if 8 + len(body) > len(d):
            raise SystemExit("não cabe: %d bytes, original %d" % (8 + len(body), len(d)))
        body += b"\x00" * (len(d) - 8 - len(body))
    res = d[:4] + struct.pack("<I", 8 + len(body)) + body
    with open(out, "wb") as f:
        f.write(res)
    comp = len(zlib.compress(res, 9))
    print("formas novas: %d (%d bytes); arquivo: %d bytes (original %d); comprimido: %d bytes"
          % (new_shapes, total_shape_bytes, len(res), len(d), comp))


if __name__ == "__main__":
    main()

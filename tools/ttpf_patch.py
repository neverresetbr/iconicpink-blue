#!/usr/bin/env python3
"""Troca a imagem de uma textura BC7 de um .ttpf, gravando uma CÓPIA (o
original só é lido). Feito para o platform.ttpf (desenho do controle,
1024x512, BC7, tiling de 64 KB, 1 mip, um bloco zlib).

Passos: lê o PNG (RGBA 8 bits) -> comprime em BC7 (modo 6, em Python puro) ->
arranja os blocos no tiling do console (inverso do detile.py) -> zlib ->
grava a cópia, ajustando só o offset do bloco seguinte no cabeçalho.

Uso: ttpf_patch.py <original.ttpf> <imagem.png> <saida.ttpf> [indice_textura=0]
"""
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from detile import BLOCK_LOG2, DISPLAY, pattern, spread  # noqa: E402
from ttpf import Pack  # noqa: E402


# ------------------------------------------------------------------ PNG
def read_png(path):
    d = open(path, "rb").read()
    assert d[:8] == b"\x89PNG\r\n\x1a\n", "não é PNG"
    pos, idat, w = 8, b"", 0
    while pos < len(d):
        ln, kind = struct.unpack_from(">I4s", d, pos)
        body = d[pos + 8:pos + 8 + ln]
        if kind == b"IHDR":
            w, h, depth, ctype, _, _, inter = struct.unpack(">IIBBBBB", body)
            assert depth == 8 and ctype in (2, 6) and inter == 0, "PNG precisa ser RGB/RGBA 8 bits"
            ch = 4 if ctype == 6 else 3
        elif kind == b"IDAT":
            idat += body
        pos += 12 + ln
    raw = zlib.decompress(idat)
    stride = w * ch
    out, prev, i = bytearray(), bytearray(stride), 0
    for _ in range(h):
        f = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        for x in range(stride):
            a = line[x - ch] if x >= ch else 0
            b = prev[x]
            c = prev[x - ch] if x >= ch else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + b) & 255
            elif f == 3:
                line[x] = (line[x] + ((a + b) >> 1)) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        out += line if ch == 4 else bytes(v for k in range(w) for v in (*line[3 * k:3 * k + 3], 255))
        prev = line
    return w, h, bytes(out)


# ------------------------------------------------------------------ BC7 modo 6
W4 = [0, 4, 9, 13, 17, 21, 26, 30, 34, 38, 43, 47, 51, 55, 60, 64]


def _axis(px, mean):
    """Eixo principal (iteração de potência na covariância RGBA)."""
    cov = [[0.0] * 4 for _ in range(4)]
    for p in px:
        d = [p[k] - mean[k] for k in range(4)]
        for a in range(4):
            for b in range(a, 4):
                cov[a][b] += d[a] * d[b]
    for a in range(4):
        for b in range(a):
            cov[a][b] = cov[b][a]
    v = [cov[k][k] + 1e-3 for k in range(4)]
    for _ in range(8):
        n = [sum(cov[a][b] * v[b] for b in range(4)) for a in range(4)]
        m = max(abs(x) for x in n) or 1.0
        v = [x / m for x in n]
    return v


def _quant(e, p):
    return max(0, min(127, int(round((e - p) / 2.0))))


def encode_block(px):
    """16 pixels RGBA (listas) -> 16 bytes BC7 modo 6."""
    opaque = [p for p in px if p[3] > 0] or px
    cm = [sum(p[k] for p in opaque) / len(opaque) for k in range(3)]
    px = [p if p[3] > 0 else [cm[0], cm[1], cm[2], 0] for p in px]
    mean = [sum(p[k] for p in px) / 16.0 for k in range(4)]
    ax = _axis(px, mean)
    ts = [sum((p[k] - mean[k]) * ax[k] for k in range(4)) for p in px]
    l2 = sum(a * a for a in ax) or 1.0
    t0, t1 = min(ts) / l2, max(ts) / l2
    e0 = [mean[k] + t0 * ax[k] for k in range(4)]
    e1 = [mean[k] + t1 * ax[k] for k in range(4)]
    best = None
    for p0 in (0, 1):
        for p1 in (0, 1):
            q0 = [_quant(v, p0) for v in e0]
            q1 = [_quant(v, p1) for v in e1]
            a = [(q << 1) | p0 for q in q0]
            b = [(q << 1) | p1 for q in q1]
            pal = [[((64 - w) * a[k] + w * b[k] + 32) >> 6 for k in range(4)] for w in W4]
            idx, err = [], 0
            for p in px:
                bi, be = 0, 1 << 30
                wa = p[3] / 255.0 if p[3] > 0 else 0.0
                for i, c in enumerate(pal):
                    e = ((p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2 + (p[2] - c[2]) ** 2) * wa \
                        + 2 * (p[3] - c[3]) ** 2
                    if e < be:
                        bi, be = i, e
                idx.append(bi)
                err += be
            if best is None or err < best[0]:
                best = (err, q0, q1, p0, p1, idx)
    _, q0, q1, p0, p1, idx = best
    if idx[0] >= 8:                       # âncora: bit alto do índice 0 tem de ser 0
        q0, q1, p0, p1 = q1, q0, p1, p0
        idx = [15 - i for i in idx]
    bits, n = 1 << 6, 7                   # modo 6
    for v in (q0[0], q1[0], q0[1], q1[1], q0[2], q1[2], q0[3], q1[3]):
        bits |= v << n
        n += 7
    bits |= p0 << n
    bits |= p1 << (n + 1)
    n += 2
    for i, v in enumerate(idx):
        w = 3 if i == 0 else 4
        bits |= v << n
        n += w
    return bits.to_bytes(16, "little")


def encode_bc7(w, h, rgba):
    out = bytearray()
    for by in range(0, h, 4):
        for bx in range(0, w, 4):
            px = []
            for y in range(4):
                o = ((by + y) * w + bx) * 4
                for x in range(4):
                    px.append(list(rgba[o + 4 * x:o + 4 * x + 4]))
            out += encode_block(px)
    return bytes(out)


# ------------------------------------------------------------------ tiling
def tile(lin, w_px, h_px, bpe, mode, block=4):
    """Inverso exato de detile.detile (mesmo endereço, cópia no outro sentido)."""
    w, h = -(-w_px // block), -(-h_px // block)
    log2 = BLOCK_LOG2[mode]
    element_log2 = bpe.bit_length() - 1
    elements_log2 = log2 - element_log2
    bw_log2 = (elements_log2 + 1) // 2
    bw, bh = 1 << bw_log2, 1 << (elements_log2 - bw_log2)
    pitch = -(-w // bw) * bw
    rows = -(-h // bh) * bh
    out = bytearray(pitch * rows * bpe)
    px, py = (spread(a) for a in pattern(1 if mode in DISPLAY else 0, element_log2, log2))
    for y in range(h):
        row = (((y // bh) * (pitch // bw)) << log2) + py[y % bh]
        for x in range(w):
            t = row + ((x // bw) << log2) + px[x % bw]
            s = (y * w + x) * bpe
            out[t:t + bpe] = lin[s:s + bpe]
    return bytes(out)


# ------------------------------------------------------------------ montagem
def main():
    src, png, out = sys.argv[1:4]
    ti = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    pack = Pack(src)
    t = pack.textures[ti]
    if (t["fmt"] >> 4) & 0xFF != 0x31 or t["cls"] != 0:
        raise SystemExit("só BC7 com tiling de 64 KB (classe 0) é suportado")
    import bisect
    size = t["w"] * t["h"]                      # BC7: 16 bytes por bloco 4x4 = 1 byte/pixel
    j = bisect.bisect_right(pack.ustart, t["u0"]) - 1
    if pack.blocks[j][1] != 8 or t["u0"] + size > pack.blocks[j + 1][2]:
        raise SystemExit("a textura tem de estar inteira num único bloco zlib")
    old, why = pack.block_bytes(j)
    if old is None:
        raise SystemExit("não consegui ler o bloco: " + why)
    w, h, rgba = read_png(png)
    if (w, h) != (t["w"], t["h"]):
        raise SystemExit("a imagem tem de ser %dx%d" % (t["w"], t["h"]))
    print("comprimindo em BC7 (%dx%d, %d blocos)..." % (w, h, w * h // 16))
    tiled = tile(encode_bc7(w, h, rgba), w, h, 16, 10)
    s = t["u0"] - pack.blocks[j][2]
    new = bytearray(old)
    if s + len(tiled) > len(new):
        raise SystemExit("textura maior que o bloco")
    new[s:s + len(tiled)] = tiled
    comp = zlib.compress(bytes(new), 9)
    off = pack.blocks[j][0]
    nxt = pack.blocks[j + 1][0]
    if nxt != len(pack.m):
        raise SystemExit("esperava o bloco da textura no fim do arquivo")
    body = comp + b"\0" * (-len(comp) % 256)
    head = bytearray(pack.m[:off])
    # offset do bloco seguinte (fim do arquivo) em unidades de 256, bits 0-21 do lo
    lo, hi = struct.unpack_from("<II", head, 0x18 + 8 * (j + 1))
    lo = (lo & ~0x3FFFFF) | ((off + len(body)) // 256)
    struct.pack_into("<II", head, 0x18 + 8 * (j + 1), lo, hi)
    with open(out, "wb") as f:
        f.write(bytes(head) + body)
    print("ok: %s (%d bytes; original %d); bloco zlib %d bytes (original %d)"
          % (out, len(head) + len(body), len(pack.m), len(comp), nxt - off))


if __name__ == "__main__":
    main()

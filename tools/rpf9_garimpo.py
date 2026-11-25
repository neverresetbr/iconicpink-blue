#!/usr/bin/env python3
"""Garimpa (carving) arquivos de um .rpf (RPF9) sem usar o índice.

O índice (TOC) do RPF9 é criptografado, mas o conteúdo não: cada arquivo é um
ou mais streams zlib comuns, alinhados em 16 bytes. Arquivos grandes viram
uma cadeia de blocos de 64 KiB: um bloco continua no próximo quando
descomprime para exatamente 65.536 bytes e o próximo stream começa no slot
alinhado logo depois. (Fonte: notas públicas do GTA6-Asset-Info e do
PercyStar, só lidas; código escrito aqui.)

Uso: rpf9_garimpo.py <arquivo.rpf> <pasta_saida> [palavra1,palavra2,...]
Guarda: todo arquivo Scaleform (GFX/CFX/FWS/CWS) e todo arquivo cujo
conteúdo tenha alguma das palavras. Só lê o .rpf.
"""
import mmap
import os
import re
import struct
import sys
import zlib

FULL = 65536
HDR = re.compile(rb"\x78[\x01\x5e\x9c\xda]")


def inflate_at(m, off, limit=4 * FULL):
    d = zlib.decompressobj()
    try:
        out = d.decompress(m[off:off + limit], 0)
    except zlib.error:
        return None, 0
    if not d.eof:
        return None, 0
    used = min(limit, len(m) - off) - len(d.unused_data)
    return out, used


def carve(path, keywords):
    f = open(path, "rb")
    m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    toc_end = struct.unpack_from("<I", m, 4)[0]
    pos = (toc_end + 15) & ~15
    while True:
        hit = HDR.search(m, pos)
        if not hit:
            break
        off = hit.start()
        if off % 16:
            pos = off + 1
            continue
        out, used = inflate_at(m, off)
        if out is None or len(out) < 16:
            pos = off + 16
            continue
        start, parts = off, [out]
        nxt = (off + used + 15) & ~15
        while len(parts[-1]) == FULL:
            more, used2 = inflate_at(m, nxt)
            if more is None:
                break
            parts.append(more)
            nxt = (nxt + used2 + 15) & ~15
        yield start, b"".join(parts)
        pos = nxt


def kind_of(data):
    h = data[:4]
    if h[:3] in (b"GFX", b"CFX", b"FWS", b"CWS"):
        return "gfx"
    if h == b"PSIN":
        return "psin"
    if data.lstrip(b"\xef\xbb\xbf \r\n\t")[:1] == b"<":
        return "xml"
    return "bin"


def main():
    src, out = sys.argv[1], sys.argv[2]
    words = [w.encode() for w in (sys.argv[3].split(",") if len(sys.argv) > 3 else [])]
    os.makedirs(out, exist_ok=True)
    base = os.path.splitext(os.path.basename(src))[0]
    n = kept = 0
    for off, data in carve(src, words):
        n += 1
        k = kind_of(data)
        hit = [w.decode() for w in words if w in data]
        if k == "gfx" or hit:
            kept += 1
            name = "%s_%010x_%s%s.%s" % (base, off, k, ("_" + "+".join(hit)) if hit else "", k)
            with open(os.path.join(out, name), "wb") as fo:
                fo.write(data)
            print("guardado", name, len(data), "bytes")
    print("%s: %d arquivos garimpados, %d guardados" % (base, n, kept))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Tira metadados de imagens antes de publicar (nada do computador vai junto).

- PNG: mantém só os blocos de imagem (IHDR, PLTE, tRNS, IDAT, IEND); remove
  EXIF, textos, data, perfil de cor (iCCP) e qualquer outro bloco.
- GIF: remove extensões de comentário e de texto; mantém só a de loop
  (NETSCAPE2.0) e o controle de quadro.
- Confere e avisa (sem mudar) SVG com <metadata> ou nomes de programa.

Uso: limpar_metadados.py <pasta_ou_arquivos...> [--conferir]
  --conferir: só lista o que tem, sem alterar (sai com 1 se achar algo).
"""
import os
import struct
import sys

KEEP_PNG = {b"IHDR", b"PLTE", b"tRNS", b"IDAT", b"IEND"}


def png(path, check):
    d = open(path, "rb").read()
    if d[:8] != b"\x89PNG\r\n\x1a\n":
        return []
    pos, out, dropped = 8, [d[:8]], []
    while pos < len(d):
        ln, kind = struct.unpack_from(">I4s", d, pos)
        chunk = d[pos:pos + 12 + ln]
        if kind in KEEP_PNG:
            out.append(chunk)
        else:
            dropped.append(kind.decode("latin1"))
        pos += 12 + ln
    if dropped and not check:
        open(path, "wb").write(b"".join(out))
    return dropped


def gif(path, check):
    d = open(path, "rb").read()
    if d[:3] != b"GIF":
        return []
    flags = d[10]
    pos = 13 + (3 * (2 << (flags & 7)) if flags & 0x80 else 0)
    out, dropped = bytearray(d[:pos]), []
    while pos < len(d):
        b = d[pos]
        if b == 0x3B:                                   # fim
            out.append(b)
            break
        if b == 0x21:                                   # extensão
            label = d[pos + 1]
            q = pos + 2
            subs = bytearray()
            while d[q]:
                subs += d[q:q + 1 + d[q]]
                q += 1 + d[q]
            q += 1
            keep = label == 0xF9 or (label == 0xFF and d[pos + 3:pos + 14] == b"NETSCAPE2.0")
            if keep:
                out += d[pos:q]
            else:
                dropped.append({0xFE: "comentário", 0x01: "texto", 0xFF: "aplicação"}.get(label, hex(label)))
            pos = q
        elif b == 0x2C:                                 # imagem
            lflags = d[pos + 9]
            q = pos + 10 + (3 * (2 << (lflags & 7)) if lflags & 0x80 else 0)
            q += 1                                      # tamanho mínimo do LZW
            while d[q]:
                q += 1 + d[q]
            q += 1
            out += d[pos:q]
            pos = q
        else:
            raise ValueError("GIF inesperado em %s (%d)" % (path, pos))
    if dropped and not check:
        open(path, "wb").write(bytes(out))
    return dropped


def svg(path):
    s = open(path, encoding="utf8", errors="replace").read().lower()
    return [w for w in ("<metadata", "inkscape", "sodipodi", "adobe", "creator", "author") if w in s]


def main():
    check = "--conferir" in sys.argv
    paths = []
    for a in sys.argv[1:]:
        if a.startswith("--"):
            continue
        if os.path.isdir(a):
            for root, _, files in os.walk(a):
                if "/.git" in root:
                    continue
                paths += [os.path.join(root, f) for f in files]
        else:
            paths.append(a)
    found = 0
    for p in sorted(paths):
        ext = p.lower().rsplit(".", 1)[-1]
        got = png(p, check) if ext == "png" else gif(p, check) if ext == "gif" else \
            svg(p) if ext == "svg" else []
        if got:
            found += 1
            print(("tem: " if check or ext == "svg" else "limpo: ") + p, got)
    print("%d arquivo(s) com metadados%s" % (found, "" if check else " (PNG/GIF já limpos)"))
    sys.exit(1 if check and found else 0)


if __name__ == "__main__":
    main()

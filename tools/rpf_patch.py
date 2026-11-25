#!/usr/bin/env python3
"""Fase 3, opção A: faz uma CÓPIA do data.rpf com o input_icons.gfx novo no
lugar do original. O .rpf original só é lido.

- Acha o filme dos ícones (por conteúdo; ou use --offset) e o tamanho do
  stream zlib original.
- Comprime o arquivo novo com o mesmo tipo de cabeçalho zlib e exige que caiba
  no espaço do stream original. Recomendado: o .gfx com --tamanho-original
  (mesmo tamanho descomprimido do original, caso o índice guarde esse valor).
- Grava a cópia, escreve o stream novo no mesmo offset e zera o resto do
  espaço do stream antigo.
- Confere: a cópia tem o mesmo tamanho; fora desse espaço, é byte a byte igual
  ao original; no offset, descomprime exatamente para o arquivo novo.

Uso: rpf_patch.py <data.rpf original> <input_icons_novo.gfx> <saida/data.rpf> [--offset 0x...]
"""
import hashlib
import os
import shutil
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from rpf9_garimpo import carve, inflate_at  # noqa: E402

TAG = b"platform_xbsx.input_icons.Main_Button_30"
LEVEL = {0x01: 1, 0x5E: 4, 0x9C: 6, 0xDA: 9}


def find(path):
    for off, data in carve(path, []):
        if data[:3] in (b"GFX", b"CFX") and TAG in data:
            return off
    raise SystemExit("não achei o filme dos ícones em " + path)


def sha_outside(path, a, b, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        pos = 0
        size = os.path.getsize(path)
        while pos < size:
            n = min(chunk, size - pos)
            if pos < b and pos + n > a:          # pula a região [a, b)
                if pos < a:
                    h.update(f.read(a - pos))
                f.seek(b)
                pos = b
                continue
            h.update(f.read(n))
            pos += n
    return h.hexdigest()


def main():
    src, new_gfx, out = sys.argv[1:4]
    off = int(sys.argv[sys.argv.index("--offset") + 1], 0) if "--offset" in sys.argv else find(src)
    with open(src, "rb") as f:
        import mmap
        m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        old, used = inflate_at(m, off)
        hdr = m[off:off + 2]
        m.close()
    if old is None or TAG not in old:
        raise SystemExit("no offset 0x%x não está o filme dos ícones" % off)
    new = open(new_gfx, "rb").read()
    comp = zlib.compress(new, LEVEL.get(hdr[1], 9))
    print("offset 0x%x; stream original: %d bytes (descomprime para %d); novo: %d bytes "
          "(descomprime para %d)" % (off, used, len(old), len(comp), len(new)))
    if len(comp) > used:
        raise SystemExit("não cabe: o stream novo é maior que o original")
    if len(new) != len(old):
        print("aviso: tamanho descomprimido diferente do original (%d x %d); "
              "use o .gfx gerado com --tamanho-original" % (len(new), len(old)))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    print("copiando o .rpf (só leitura do original)...")
    shutil.copyfile(src, out)
    with open(out, "r+b") as f:
        f.seek(off)
        f.write(comp + b"\0" * (used - len(comp)))
    # conferência
    if os.path.getsize(out) != os.path.getsize(src):
        raise SystemExit("FALHA: tamanho da cópia diferente")
    if sha_outside(src, off, off + used) != sha_outside(out, off, off + used):
        raise SystemExit("FALHA: a cópia mudou fora do espaço do stream")
    with open(out, "rb") as f:
        import mmap
        m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        back, _ = inflate_at(m, off)
        m.close()
    if back != new:
        raise SystemExit("FALHA: o stream gravado não descomprime para o arquivo novo")
    print("OK: cópia em %s; só %d bytes do espaço do stream mudaram; o resto é igual ao original"
          % (out, used))


if __name__ == "__main__":
    main()

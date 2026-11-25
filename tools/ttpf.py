#!/usr/bin/env python3
"""Leitor do pacote de texturas .ttpf (cabeçalho RDS5 + bloco ETPF).

Formato (descoberto em 2026-11-25, só leitura):
  RDS5   u32 magic 'RDS5', u32 n_blocos, u32 tamanho_descomprimido_total,
         u32 ?, u32 ?, u32 0, depois n_blocos entradas de 8 bytes:
           lo: bits 0-21  offset comprimido no arquivo / 256
               bits 26-29 compressão: 8 = zlib, 1/4/7 = BCPack BC1/BC4/BC7, 0 = sem compressão
               bits 30-31 + páginas de 4 KiB no offset descomprimido
           hi: bits 0-19  offset descomprimido / 16 KiB
               (offset real = hi*16 KiB + (lo>>30)*4 KiB)
  ETPF   u32 magic 'ETPF', u32 0x27a, u32 n_texturas, u32 ?,
         n_texturas registros de 16 bytes:
           u32 dims: bits 0-13 largura-1, bits 14-27 altura-1, bits 28-31 ?
           u32 formato (byte 3 = classe de layout)
           u32 bits 0-19 início descomprimido / 4 KiB
           u32 ?
Nada é escrito nos arquivos do jogo.
"""
import bisect
import mmap
import os
import struct
import subprocess
import zlib

ZLIB = 8
RAW = 0  # bloco guardado sem compressão
# tipo de compressão do bloco -> número BC do BCPack
BCPACK = {1: 1, 4: 4, 7: 7}


class Pack:
    def __init__(self, path):
        self.file = open(path, "rb")
        self.m = mmap.mmap(self.file.fileno(), 0, access=mmap.ACCESS_READ)
        m = self.m
        assert m[:4] == b"RDS5", "não é RDS5"
        n = struct.unpack_from("<I", m, 4)[0]
        self.blocks = []
        for i in range(n):
            lo, hi = struct.unpack_from("<II", m, 0x18 + 8 * i)
            self.blocks.append(((lo & 0x3FFFFF) * 256, (lo >> 26) & 0xF,
                                (hi & 0xFFFFF) * 16384 + (lo >> 30) * 4096))
        self.ustart = [b[2] for b in self.blocks]
        base = m.find(b"ETPF", 0, 0x200000)
        count = struct.unpack_from("<I", m, base + 8)[0]
        self.textures = []
        for i in range(count):
            d, fm, st, x = struct.unpack_from("<4I", m, base + 16 + 16 * i)
            self.textures.append({
                "i": i,
                "w": (d & 0x3FFF) + 1,
                "h": ((d >> 14) & 0x3FFF) + 1,
                "top": d >> 28,
                "fmt": fm & 0xFFFF,
                "cls": fm >> 24,
                "fmt_raw": fm,
                "u0": (st & 0xFFFFF) * 4096,
                "st_hi": st >> 20,
                "x": x,
            })
        for t, nxt in zip(self.textures, self.textures[1:] + [None]):
            t["u1"] = nxt["u0"] if nxt else self.ustart[-1]
            t["size"] = t["u1"] - t["u0"]
        self.cache = {}

    def decode_bcpack(self, cache_dir, cli, only=None):
        """Decodifica em lote os blocos BCPack (tipos 1, 4 e 7 = BC1, BC4, BC7)
        com bcpack-cli, para cache_dir. `only`: conjunto de índices de bloco."""
        os.makedirs(cache_dir, exist_ok=True)
        jobs = []
        for j in range(len(self.blocks) - 1):
            off, kind, u = self.blocks[j]
            if kind not in BCPACK or (only is not None and j not in only):
                continue
            out = os.path.join(cache_dir, "bloco_%05d.bin" % j)
            self.cache[j] = out
            if os.path.exists(out):
                continue
            raw = self.m[off:self.blocks[j + 1][0]]
            src = out + ".bcp"
            with open(src, "wb") as f:
                f.write(raw)
            jobs.append("\t".join([src, out, str(BCPACK[kind]),
                                   str(self.blocks[j + 1][2] - u)]))
        if jobs:
            lista = os.path.join(cache_dir, "lote.tsv")
            with open(lista, "w") as f:
                f.write("\n".join(jobs))
            r = subprocess.run([cli, lista], capture_output=True, text=True)
            print("bcpack:", r.stdout.strip(), (r.stderr.strip().splitlines() or [""])[:3])
            for line in jobs:
                os.remove(line.split("\t")[0])

    def blocks_of(self, t):
        """Índices dos blocos que a textura t ocupa."""
        j = bisect.bisect_right(self.ustart, t["u0"]) - 1
        k = bisect.bisect_left(self.ustart, t["u1"])
        return range(j, k)

    def block_bytes(self, j):
        """Bloco j descomprimido; None se faltar no disco ou não for zlib."""
        off, kind, u = self.blocks[j]
        end = self.blocks[j + 1][0] if j + 1 < len(self.blocks) else len(self.m)
        usize = self.blocks[j + 1][2] - u
        raw = self.m[off:end] if end > off else b""
        if not raw or raw[:64] == bytes(64):
            return None, "faltando"
        if kind == RAW:
            return (raw[:usize], "ok") if len(raw) >= usize else (None, "incompleto")
        if kind != ZLIB:
            cached = self.cache.get(j) if self.cache else None
            if cached and os.path.exists(cached):
                with open(cached, "rb") as f:
                    out = f.read()
                if len(out) == usize:
                    return out, "ok"
            return None, "bcpack%d" % kind
        try:
            d = zlib.decompressobj()
            out = d.decompress(raw)
        except zlib.error:
            return None, "zlib-erro"
        if not d.eof or len(out) != usize:
            return None, "incompleto"
        return out, "ok"

    def read(self, u0, u1):
        """Bytes descomprimidos [u0, u1); (None, motivo) se algum bloco falhar."""
        j = bisect.bisect_right(self.ustart, u0) - 1
        k = bisect.bisect_left(self.ustart, u1)
        parts = []
        for c in range(j, k):
            b, why = self.block_bytes(c)
            if b is None:
                return None, why
            parts.append(b)
        data = b"".join(parts)
        s = u0 - self.blocks[j][2]
        return data[s:s + (u1 - u0)], "ok"

    def texture_bytes(self, t):
        return self.read(t["u0"], t["u1"])

#!/usr/bin/env python3
"""Desfaz o tiling de uma textura 2D do Xbox Series (GPU GFX10) com 1 mip.

Porte direto de victory-fork/crates/victory-formats/src/texture.rs
(Layout::tiled + pattern + spread), só para o caso 2D, 1 mip, 1 amostra,
modos sem XOR (0 linear, 1/2 256B, 5/6 4KB, 9/10 64KB).

Uso: detile.py <entrada> <saida> <largura_px> <altura_px> <bytes_por_bloco> <modo>
  bytes_por_bloco: 16 para BC7/BC3/BC5, 8 para BC1/BC4 (bloco = 4x4 texels)
"""
import sys

MICRO = [
    [b"x0x1x2x3y0y1y2y3", b"--x0x1x2y0y1y2x3", b"----x0x1y0y1y2x2",
     b"------x0y0y1x1x2", b"--------y0y1x0x1"],
    [b"x0x1x2y1y0y2x3y3", b"--x0x1x2y0y1y2x3", b"----x0x1y0y1x2y2",
     b"------x0y0x1x2y1", b"--------x0y0x1y1"],
]
BLOCK_LOG2 = {0: 0, 1: 8, 2: 8, 5: 12, 6: 12, 9: 16, 10: 16}
DISPLAY = {2, 6, 10}


def pattern(kind, element_log2, block_log2):
    axes = [[], []]
    micro = MICRO[kind][element_log2]
    for bit in range(8):
        axis, index = chr(micro[2 * bit]), micro[2 * bit + 1] - ord("0")
        if axis not in "xy":
            continue
        to = axes[0 if axis == "x" else 1]
        while len(to) <= index:
            to.append(0)
        to[index] = bit
    order = [1, 0]
    for i, bit in enumerate(range(8, block_log2)):
        axes[order[i % 2]].append(bit)
    return axes


def spread(bits):
    return [sum(((c >> i) & 1) << to for i, to in enumerate(bits))
            for c in range(1 << len(bits))]


def detile(data, w_px, h_px, bpe, mode, block=4):
    w, h = -(-w_px // block), -(-h_px // block)  # em elementos
    out = bytearray(w * h * bpe)
    log2 = BLOCK_LOG2[mode]
    if log2 == 0:
        pitch = -(-w // (256 // bpe)) * (256 // bpe)
        for y in range(h):
            out[y * w * bpe:(y + 1) * w * bpe] = data[y * pitch * bpe:(y * pitch + w) * bpe]
        return bytes(out)
    element_log2 = bpe.bit_length() - 1
    elements_log2 = log2 - element_log2
    bw_log2 = (elements_log2 + 1) // 2
    bw, bh = 1 << bw_log2, 1 << (elements_log2 - bw_log2)
    pitch = -(-w // bw) * bw
    px, py = (spread(a) for a in pattern(1 if mode in DISPLAY else 0, element_log2, log2))
    for y in range(h):
        row = (((y // bh) * (pitch // bw)) << log2) + py[y % bh]
        for x in range(w):
            t = row + ((x // bw) << log2) + px[x % bw]
            l = (y * w + x) * bpe
            out[l:l + bpe] = data[t:t + bpe]
    return bytes(out)


if __name__ == "__main__":
    src, dst, w_px, h_px, bpe, mode = sys.argv[1:7]
    data = open(src, "rb").read()
    open(dst, "wb").write(detile(data, int(w_px), int(h_px), int(bpe), int(mode)))


def mip0_offset(w_px, h_px, bpe, mode, mips, block=4):
    """Offset do mip 0 dentro da fatia (addrlib: mips menores primeiro, depois
    da cauda). Porte de Layout::tiled (caso 2D fino, 1 amostra)."""
    log2 = BLOCK_LOG2[mode]
    if mips <= 1 or log2 == 0:
        return 0
    element_log2 = bpe.bit_length() - 1
    elements_log2 = log2 - element_log2
    bw_log2 = (elements_log2 + 1) // 2
    bw, bh = 1 << bw_log2, 1 << (elements_log2 - bw_log2)
    tail_max = (bw >> 1, bh)
    max_in_tail = 0 if log2 == 8 else (1 + (1 << (log2 - 9)) if log2 <= 11 else log2 - 4)
    sizes, first_tail = [], mips
    for i in range(mips):
        pw = -(-(-(-w_px // block)) // (1 << i))
        ph = -(-(-(-h_px // block)) // (1 << i))
        if pw <= tail_max[0] and ph <= tail_max[1] and mips - i <= max_in_tail:
            first_tail = i
            break
        sizes.append((-(-pw // bw) * bw) * (-(-ph // bh) * bh) * bpe)
    off = (1 << log2) if first_tail < mips else 0
    return off + sum(sizes[1:first_tail])

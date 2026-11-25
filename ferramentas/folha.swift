// Monta uma folha de contato (grade) com vários PNGs, sobre fundo xadrez,
// com o número de cada um embaixo. Tudo local.
//
// Compilar: swiftc -O folha.swift -o folha
// Uso:      folha <saida.png> <colunas> <celula_px> <img1.png> [img2.png ...]
//           (o rótulo é o nome do arquivo sem extensão)
//           FOLHA_ESCALA_COMUM=1: mesma escala para todas as imagens (a maior
//           cabe na célula), para comparar tamanhos de verdade.
import AppKit
import CoreGraphics
import Foundation
import ImageIO
import UniformTypeIdentifiers

let a = CommandLine.arguments
guard a.count >= 5, let cols = Int(a[2]), let cell = Int(a[3]) else {
    print("uso: folha <saida.png> <colunas> <celula_px> <imgs...>")
    exit(1)
}
let files = Array(a[4...])
let label = 16
let rows = (files.count + cols - 1) / cols
let W = cols * cell, H = rows * (cell + label)
let cs = CGColorSpace(name: CGColorSpace.sRGB)!
let ctx = CGContext(data: nil, width: W, height: H, bitsPerComponent: 8, bytesPerRow: 0,
                    space: cs, bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
ctx.setFillColor(CGColor(gray: 0.15, alpha: 1))
ctx.fill(CGRect(x: 0, y: 0, width: W, height: H))
NSGraphicsContext.current = NSGraphicsContext(cgContext: ctx, flipped: false)

let comum = ProcessInfo.processInfo.environment["FOLHA_ESCALA_COMUM"] == "1"
var maior = 1.0
if comum {
    for p in files { if let i = NSImage(contentsOfFile: p) { maior = max(maior, Double(i.size.width), Double(i.size.height)) } }
}
for (n, path) in files.enumerated() {
    let cx = (n % cols) * cell
    let cy = H - (n / cols + 1) * (cell + label) + label
    // xadrez para enxergar a transparência
    let sq = max(cell / 16, 4)
    for yy in stride(from: 0, to: cell, by: sq) {
        for xx in stride(from: 0, to: cell, by: sq) {
            let dark = ((xx / sq) + (yy / sq)) % 2 == 0
            ctx.setFillColor(CGColor(gray: dark ? 0.55 : 0.75, alpha: 1))
            ctx.fill(CGRect(x: cx + xx, y: cy + yy, width: sq, height: sq))
        }
    }
    // NSImage lê PNG, JPEG e SVG (SVG em escala fiel ao viewBox)
    if let img = NSImage(contentsOfFile: path) {
        let iw = Double(img.size.width), ih = Double(img.size.height)
        let s = comum ? Double(cell) / maior : min(Double(cell) / iw, Double(cell) / ih)
        let w = iw * s, h = ih * s
        ctx.interpolationQuality = .high
        img.draw(in: NSRect(x: Double(cx) + (Double(cell) - w) / 2,
                            y: Double(cy) + (Double(cell) - h) / 2, width: w, height: h))
    }
    let name = URL(fileURLWithPath: path).deletingPathExtension().lastPathComponent
    let attrs: [NSAttributedString.Key: Any] = [
        .font: NSFont.monospacedSystemFont(ofSize: 11, weight: .regular),
        .foregroundColor: NSColor.white,
    ]
    NSAttributedString(string: name, attributes: attrs)
        .draw(at: NSPoint(x: cx + 3, y: cy - label + 2))
}
let out = ctx.makeImage()!
let dest = CGImageDestinationCreateWithURL(URL(fileURLWithPath: a[1]) as CFURL,
                                           UTType.png.identifier as CFString, 1, nil)!
CGImageDestinationAddImage(dest, out, nil)
CGImageDestinationFinalize(dest)
print("ok: \(a[1]) (\(files.count) imagens)")

// Converte um SVG em PNG (macOS, NSImage), na largura pedida.
//
// Compilar: swiftc -O raster.swift -o raster
// Uso:      raster <entrada.svg> <saida.png> <largura_px>
import AppKit
import Foundation

let a = CommandLine.arguments
guard a.count == 4, let width = Int(a[3]), let img = NSImage(contentsOfFile: a[1]) else {
    print("uso: raster <entrada.svg> <saida.png> <largura_px>")
    exit(1)
}
let w = width, h = Int((Double(width) * Double(img.size.height) / Double(img.size.width)).rounded())
let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: w, pixelsHigh: h, bitsPerSample: 8,
                           samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
                           colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
rep.size = NSSize(width: w, height: h)
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
NSGraphicsContext.current?.imageInterpolation = .high
img.draw(in: NSRect(x: 0, y: 0, width: w, height: h))
NSGraphicsContext.current = nil
try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: a[2]))
print("ok: \(a[2]) (\(w)x\(h))")

// Teste de tamanho: mede a caixa ocupada (pixels não brancos e não
// transparentes) de cada PNG e imprime em unidades do espaço de 64 dos ícones
// (lê o viewBox quadrado de cada SVG; 10 px por unidade).
//
// Compilar: swiftc -O medir.swift -o medir
// Uso:      medir <icone1.svg> [icone2.svg ...]
import AppKit
import Foundation

print("arquivo\tlargura\taltura\tcentro_x\tcentro_y")
func viewBox(_ path: String) -> (Double, Double) {
    let text = (try? String(contentsOfFile: path, encoding: .utf8)) ?? ""
    if let r = text.range(of: "viewBox=\"[^\"]*\"", options: .regularExpression) {
        let v = text[r].dropFirst(9).dropLast().split(separator: " ").compactMap { Double($0) }
        if v.count == 4 { return (v[0], v[2]) }
    }
    return (-3.2, 70.4)
}
for path in CommandLine.arguments.dropFirst() {
    guard let img = NSImage(contentsOfFile: path) else { continue }
    let (origin, units) = viewBox(path)
    // renderiza em escala fixa: 10 px por unidade
    let w = Int(units * 10), h = Int(units * 10)
    let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: w, pixelsHigh: h, bitsPerSample: 8,
                               samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
                               colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
    NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
    NSColor.white.setFill(); NSRect(x: 0, y: 0, width: w, height: h).fill()
    img.draw(in: NSRect(x: 0, y: 0, width: w, height: h))
    NSGraphicsContext.current = nil
    let cg = rep.cgImage!
    var data = [UInt8](repeating: 0, count: w * h * 4)
    let ctx = CGContext(data: &data, width: w, height: h, bitsPerComponent: 8, bytesPerRow: w * 4,
                        space: CGColorSpace(name: CGColorSpace.sRGB)!,
                        bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
    ctx.setFillColor(CGColor(gray: 1, alpha: 1))
    ctx.fill(CGRect(x: 0, y: 0, width: w, height: h))
    ctx.draw(cg, in: CGRect(x: 0, y: 0, width: w, height: h))
    var minX = w, minY = h, maxX = -1, maxY = -1
    for y in 0..<h {
        for x in 0..<w {
            let i = (y * w + x) * 4
            if data[i] < 235 || data[i + 1] < 235 || data[i + 2] < 235 {
                minX = min(minX, x); maxX = max(maxX, x)
                minY = min(minY, y); maxY = max(maxY, y)
            }
        }
    }
    if maxX < 0 { print("\(path)\tvazio"); continue }
    let s = units / Double(w)
    let bw = Double(maxX - minX + 1) * s, bh = Double(maxY - minY + 1) * s
    let cx = origin + (Double(minX + maxX + 1) / 2) * s
    let cy = origin + (Double(minY + maxY + 1) / 2) * s
    let name = URL(fileURLWithPath: path).lastPathComponent
    print(String(format: "%@\t%.1f\t%.1f\t%.1f\t%.1f", name, bw, bh, cx, cy))
}

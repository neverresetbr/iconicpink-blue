// Converte texto em contorno vetorial (path SVG) com CoreText, para que as
// letras das teclas fiquem idênticas em qualquer renderizador e possam ir
// para o .gfx como forma (o jogo não recebe fonte nova).
//
// Compilar: swiftc -O texto_svg.swift -o texto_svg
// Uso:      echo '[["HelveticaNeue-Bold", 36, "Shift"], ...]' | texto_svg
// Saída:    JSON: [{"d": "...", "w": avanço, "x0","y0","x1","y1": caixa,
//                   "cap": altura das maiúsculas}]  (y para baixo, base em 0)
import CoreText
import Foundation

let input = FileHandle.standardInput.readDataToEndOfFile()
let items = try JSONSerialization.jsonObject(with: input) as! [[Any]]
var out: [[String: Any]] = []

func fmt(_ v: CGFloat) -> String { String(format: "%.2f", Double(v)) }

for it in items {
    let name = it[0] as! String
    let size = CGFloat((it[1] as? Double) ?? Double(it[1] as! Int))
    let text = it[2] as! String
    let font = CTFontCreateWithName(name as CFString, size, nil)
    let attr = NSAttributedString(string: text,
                                  attributes: [NSAttributedString.Key(kCTFontAttributeName as String): font])
    let line = CTLineCreateWithAttributedString(attr)
    let path = CGMutablePath()
    for run in CTLineGetGlyphRuns(line) as! [CTRun] {
        let n = CTRunGetGlyphCount(run)
        var glyphs = [CGGlyph](repeating: 0, count: n)
        var pos = [CGPoint](repeating: .zero, count: n)
        CTRunGetGlyphs(run, CFRange(location: 0, length: n), &glyphs)
        CTRunGetPositions(run, CFRange(location: 0, length: n), &pos)
        let runFont = (CTRunGetAttributes(run) as NSDictionary)[kCTFontAttributeName] as! CTFont
        for i in 0..<n {
            // fonte tem y para cima; SVG tem y para baixo
            var t = CGAffineTransform(a: 1, b: 0, c: 0, d: -1, tx: pos[i].x, ty: pos[i].y)
            if let g = CTFontCreatePathForGlyph(runFont, glyphs[i], &t) { path.addPath(g) }
        }
    }
    var d = ""
    path.applyWithBlock { el in
        let p = el.pointee.points
        switch el.pointee.type {
        case .moveToPoint: d += "M\(fmt(p[0].x)) \(fmt(p[0].y))"
        case .addLineToPoint: d += "L\(fmt(p[0].x)) \(fmt(p[0].y))"
        case .addQuadCurveToPoint: d += "Q\(fmt(p[0].x)) \(fmt(p[0].y)) \(fmt(p[1].x)) \(fmt(p[1].y))"
        case .addCurveToPoint:
            d += "C\(fmt(p[0].x)) \(fmt(p[0].y)) \(fmt(p[1].x)) \(fmt(p[1].y)) \(fmt(p[2].x)) \(fmt(p[2].y))"
        case .closeSubpath: d += "Z"
        @unknown default: break
        }
    }
    let bb = path.boundingBoxOfPath
    let w = CGFloat(CTLineGetTypographicBounds(line, nil, nil, nil))
    out.append(["d": d, "w": Double(w), "x0": Double(bb.minX), "y0": Double(bb.minY),
                "x1": Double(bb.maxX), "y1": Double(bb.maxY), "cap": Double(CTFontGetCapHeight(font))])
}
let data = try JSONSerialization.data(withJSONObject: out)
FileHandle.standardOutput.write(data)

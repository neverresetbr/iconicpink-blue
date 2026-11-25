#!/usr/bin/env python3
"""Demo local das animações de prompt (HTML que se abre direto do disco, sem
rede). Reproduz o que o motor faz com os ícones, com os valores lidos do
hud (ferramentas/abc_consts.py):

  InputIconV2.PRESSED_SCALE = 0.8          (ícone encolhe ao apertar)
  InputIconV2.COMPLETION_GLOW_ALPHA = 0.5  (brilho ao completar)
  InputIconV2.COMPLETION_GLOW_SCALE_WITH_GUTTER = 1.0 / NO_GUTTER = 0.68
  InputIconV2.ICON_OFFSET = -32            (ícone de 64 centrado)
  InputIconV2.TYPE_PRESS/HOLD/MASH/ROTATE = 0/1/2/3, ROTATE_DURATION = 360
  InputIconTarget.LERP_DURATION_FRAMES = 6 (troca de cor em 6 quadros)
  MeterMicrogame.EFFECT_STROKE_THIN = 3, EFFECT_ALPHA_15 = 0.15, EFFECT_ALPHA_70 = 0.7

As curvas (HOLD_EASE, MASH_EASE, PRESSED_EASE) e as cores exatas do anel
estão no bytecode, não em constantes: aqui são aproximações.

Uso: demo_animacoes.py <svg_xbox64> <svg_pc> <saida.html>
"""
import json
import os
import re
import sys

ICONS = {"A": 30, "B": 31, "X": 32, "Y": 33, "LB": 34, "LT": 35, "RB": 36, "RT": 37,
         "MENU": 38, "VIEW": 39, "LS": 17, "RS": 26, "L3": 16, "R3": 25, "UP": 4,
         "DOWN": 5, "LEFT": 6, "RIGHT": 7, "DPAD": 9, "LS_ROT": 20, "RS_ROT": 29,
         "LS_UP": 12, "LS_DOWN": 13, "LS_LEFT": 14, "LS_RIGHT": 15,
         "RS_UPDOWN": 27, "RS_LEFTRIGHT": 28, "RS_UP": 21, "RS_DOWN": 22,
         "RS_LEFT": 23, "RS_RIGHT": 24, "DPAD_NONE": 8, "DPAD_UD": 10, "DPAD_LR": 11,
         "LS_UD": 18, "LS_LR": 19}

PRESSED = {"#fff": "rgb(72,72,72)", "rgb(255,255,255)": "rgb(72,72,72)",
           "#000": "rgb(205,205,205)", "rgb(0,0,0)": "rgb(205,205,205)",
           "rgb(103,103,103)": "rgb(140,140,140)"}


def clean(s):
    s = re.sub(r"<\?xml[^>]*\?>", "", s)
    s = re.sub(r'\s(width|height)="[^"]*"', "", s, count=2)
    return s.strip()


def pressed(s):
    return re.sub("|".join(re.escape(k) for k in PRESSED), lambda m: PRESSED[m.group(0)], s)


def load(d, n):
    s = clean(open(os.path.join(d, "botao_%02d.svg" % n)).read())
    return [s, pressed(s)]


# anel de progresso que segue o contorno da tecla (teste).
# RING_GAP = distância da borda externa do ícone até o meio do traço do anel.
RING_GAP = 7.0
SIMPLE = {4, 5, 6, 7, 12, 13, 14, 15, 25, 31, 33, 36, 39}
WIDE = {16, 30, 32, 34, 38}
MOUSE = {26, 35, 37}
MOUSE_BODY = ("M32 4 C45 4 50 13 50 24 L50 44 C50 54 42 61 32 61 "
              "C22 61 14 54 14 44 L14 24 C14 13 19 4 32 4 Z")


def rrect(x, y, w, h, r):
    """Retângulo arredondado começando no meio de cima, em sentido horário."""
    g = RING_GAP
    x, y, w, h, r = x - g, y - g, w + 2 * g, h + 2 * g, r + g
    return ("M%.2f %.2f H%.2f A%g %g 0 0 1 %.2f %.2f V%.2f A%g %g 0 0 1 %.2f %.2f "
            "H%.2f A%g %g 0 0 1 %.2f %.2f V%.2f A%g %g 0 0 1 %.2f %.2f Z"
            % (x + w / 2, y, x + w - r, r, r, x + w, y + r, y + h - r, r, r, x + w - r, y + h,
               x + r, r, r, x, y + h - r, y + r, r, r, x + r, y))


def measure(d, nums):
    import subprocess
    here = os.path.dirname(os.path.abspath(__file__))
    files = [os.path.join(d, "botao_%02d.svg" % n) for n in nums]
    medir = os.path.join(here, "medir")
    if not os.path.exists(medir):           # sem o medir (só macOS): caixa padrão de 64
        return {n: (64.0, 64.0, 32.0, 32.0) for n in nums}
    out = subprocess.run([medir] + files, capture_output=True, text=True).stdout
    res = {}
    for line in out.strip().splitlines()[1:]:
        name, w, h, cx, cy = line.split("\t")
        res[int(name.split("_")[1].split(".")[0])] = tuple(float(v) for v in (w, h, cx, cy))
    return res


def ring_pc(n, box):
    if n in SIMPLE:
        return rrect(0, 0, 64, 64, 13.5)
    if n in WIDE:
        return rrect(0, 8, 64, 48, 10.5)
    if n in MOUSE:
        # mouse: mesmo desenho do corpo, afastado RING_GAP em toda a volta
        s = 61 / 57.0
        hw, hh = 18 * s + 1.5, 28.5 * s + 1.5
        sx, sy = (hw + RING_GAP) / 18.0, (hh + RING_GAP) / 28.5
        pts = re.sub(r"(-?[\d.]+) (-?[\d.]+)",
                     lambda m: "%.2f %.2f" % (32 + (float(m.group(1)) - 32) * sx,
                                             32 + (float(m.group(2)) - 32.5) * sy), MOUSE_BODY)
        return pts
    w, h, cx, cy = box
    return rrect(cx - w / 2, cy - h / 2, w, h, 10)


RING_XBOX = "M32 -7 A39 39 0 0 1 32 71 A39 39 0 0 1 32 -7 Z"


def main():
    xdir, pdir, out = sys.argv[1:4]
    boxes = measure(pdir, sorted(set(ICONS.values())))
    data = {k: {"xbox": load(xdir, n), "pc": load(pdir, n),
                "ring": {"xbox": RING_XBOX, "pc": ring_pc(n, boxes[n])}}
            for k, n in ICONS.items()}
    html = TEMPLATE.replace("/*ICONS*/", json.dumps(data))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w") as f:
        f.write(html)
    print("ok:", out)


TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<title>Demo das animações de prompt (local)</title>
<style>
  :root { --pink: rgb(237,84,153); }
  * { box-sizing: border-box; }
  body { margin: 0; background: #0b0c10; color: #fff;
         font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; }
  header { display: flex; gap: 24px; align-items: center; padding: 18px 28px;
           border-bottom: 1px solid #222; position: sticky; top: 0; background: #0b0c10f0; z-index: 5; }
  header h1 { font-size: 17px; margin: 0; font-weight: 700; letter-spacing: .02em; }
  header .note { font-size: 12px; color: #888; flex: 1; }
  .seg { display: inline-flex; border: 1px solid #444; border-radius: 6px; overflow: hidden; }
  .seg button { background: none; color: #bbb; border: 0; padding: 7px 14px; font: inherit;
                font-size: 13px; cursor: pointer; }
  .seg button.on { background: #fff; color: #000; font-weight: 700; }
  main { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
         gap: 18px; padding: 24px 28px 40px; }
  .card { border-radius: 4px; overflow: hidden; border: 1px solid #1d1f26; }
  .stage { height: 250px; position: relative;
           background: radial-gradient(120% 90% at 30% 20%, #3d4a5c 0%, #1b222d 45%, #0c0f14 100%); }
  .stage.warm { background: radial-gradient(120% 90% at 70% 10%, #8a5a4a 0%, #3a2a33 45%, #111018 100%); }
  .cap { padding: 11px 14px 13px; background: #121419; }
  .cap b { font-size: 14px; }
  .cap code { font-size: 11px; color: #9aa; background: #1c1f26; padding: 1px 5px; border-radius: 3px; }
  .cap p { margin: 5px 0 0; font-size: 12px; color: #8a8f99; line-height: 1.45; }
  .icon { position: relative; display: inline-block; vertical-align: middle; flex: none; }
  /* o SVG tem quadro de 96 (64 + margem de 16); a caixa do ícone representa 70,4 */
  .icon .lay { position: absolute; inset: -18.18%; transform-origin: 50% 50%; }
  .icon .lay.v70 { inset: 0; }
  .icon .lay svg { width: 100%; height: 100%; display: block; }
  .icon .ring { position: absolute; inset: -40%; width: 180%; height: 180%; pointer-events: none; overflow: visible; }
  .help { position: absolute; left: 18px; top: 18px; background: rgba(0,0,0,.72); border-radius: 2px;
          padding: 14px 16px; font-size: 16px; line-height: 1; display: flex; flex-direction: column; gap: 10px; }
  .row { display: flex; align-items: center; gap: 8px; white-space: nowrap; }
  .pill { position: absolute; left: 50%; bottom: 22px; transform: translateX(-50%);
          background: rgba(15,84,140,.95); border-radius: 40px; padding: 10px 20px;
          display: flex; align-items: center; gap: 9px; font-size: 17px; white-space: nowrap; }
  .corner { position: absolute; right: 20px; bottom: 18px; display: flex; flex-direction: column;
            align-items: flex-end; gap: 9px; }
  .corner .row { font-family: "Helvetica Neue", Helvetica, sans-serif; font-stretch: condensed;
                 font-weight: 700; font-size: 15px; letter-spacing: .03em; }
  .center { position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%);
            display: flex; flex-direction: column; align-items: center; gap: 18px; }
  .qlabel { font-weight: 700; font-size: 13px; letter-spacing: .06em; }
  .off { opacity: .4; }
  #teste .stage { height: 120px; cursor: crosshair; user-select: none; }
  #teste .keys { position: absolute; inset: 18px; display: flex; flex-wrap: wrap; gap: 18px 22px;
                 align-content: flex-start; justify-content: center; }
  #teste .k { display: flex; flex-direction: column; align-items: center; gap: 6px; font-size: 11px; color: #9aa; }
  footer { padding: 0 28px 30px; font-size: 12px; color: #667; line-height: 1.6; }
</style></head>
<body>
<header>
  <h1>Demo das animações de prompt</h1>
  <span class="note">Simulação local do que o motor faz (valores lidos do hud). Não é captura do jogo.</span>
  <span class="seg" id="plat"><button data-p="pc" class="on">PC</button><button data-p="xbox">Xbox</button></span>
  <span class="seg" id="anel"><button data-r="contorno" class="on">anel no contorno</button><button data-r="redondo">anel redondo</button></span>
  <span class="seg" id="vel"><button data-v="1" class="on">1x</button><button data-v="0.35">lento</button></span>
</header>
<main id="grid"></main>
<footer>
  Valores do motor usados: PRESSED_SCALE 0,8 · COMPLETION_GLOW_ALPHA 0,5 · COMPLETION_GLOW_SCALE 1,0 (com trilho) / 0,68 (sem) ·
  troca de cor em 6 quadros (LERP_DURATION_FRAMES) · traço do QTE 3 (EFFECT_STROKE_THIN) · trilho do QTE a 15% (EFFECT_ALPHA_15).
  Aproximados (estão no bytecode, não em constantes): curvas de easing, tempo de segurar, cor do anel de segurar.
</footer>
<script>
const ICONS = /*ICONS*/;
let PLAT = "pc", SPEED = 1, RING = "contorno";
const all = [];

/* ---- ícone: camada normal + camada apertada (cor do motor) + anel ---- */
function makeIcon(key, size) {
  const el = document.createElement("span");
  el.className = "icon"; el.style.width = el.style.height = size + "px";
  el.innerHTML = '<span class="lay n"></span><span class="lay p"></span>' +
    '<svg class="ring" viewBox="-31.36 -31.36 126.72 126.72">' +
    '<path class="gut" fill="none" stroke-width="5" stroke-linejoin="round"/>' +
    '<path class="arc" fill="none" stroke-width="5" stroke-linecap="butt" stroke-linejoin="round" pathLength="1"/>' +
    '<path class="glow" fill="none" stroke-width="5" stroke-linejoin="round"/></svg>';
  const ic = { el, key, n: el.querySelector(".n"), p: el.querySelector(".p"),
    gut: el.querySelector(".gut"), arc: el.querySelector(".arc"), glow: el.querySelector(".glow") };
  paint(ic); all.push(ic);
  set(ic, {});
  return ic;
}
function paint(ic) {
  const v = ICONS[ic.key][PLAT];
  ic.n.innerHTML = v[0]; ic.p.innerHTML = v[1];
  const v70 = v[0].includes('viewBox="-3.2');      /* originais de Xbox */
  ic.n.classList.toggle("v70", v70); ic.p.classList.toggle("v70", v70);
  const d = ICONS[ic.key].ring[RING === "contorno" ? PLAT : "xbox"];
  for (const e of [ic.gut, ic.arc, ic.glow]) e.setAttribute("d", d);
}
/* estado: tint 0..1 (apertado), scale, ring 0..1, gutter bool, ringColor, glow 0..1 */
function set(ic, s) {
  const t = s.tint || 0, sc = s.scale == null ? 1 : s.scale;
  ic.n.style.opacity = 1 - t; ic.p.style.opacity = t;
  ic.n.style.transform = ic.p.style.transform = "scale(" + sc + ")";
  const r = s.ring || 0;
  ic.gut.setAttribute("stroke", s.gutter ? "rgba(0,0,0,.55)" : "none");
  ic.arc.setAttribute("stroke", r > 0 ? (s.ringColor || "#fff") : "none");
  ic.arc.style.strokeDasharray = Math.max(r, 0.0001) + " 2";
  const g = s.glow || 0;
  /* brilho ao completar: COMPLETION_GLOW_ALPHA = 0,5, abre e some */
  ic.glow.setAttribute("stroke", g > 0 ? "rgba(255,255,255," + (0.5 * (1 - g)) + ")" : "none");
  ic.glow.setAttribute("stroke-width", 5 + 16 * g);
  ic.el.style.opacity = s.alpha == null ? 1 : s.alpha;
}

/* ---- easing ---- */
const clamp = (x) => Math.max(0, Math.min(1, x));
const outCubic = (x) => 1 - Math.pow(1 - clamp(x), 3);
const inOut = (x) => { x = clamp(x); return x < .5 ? 4*x*x*x : 1 - Math.pow(-2*x + 2, 3) / 2; };
const LERP = 6 / 60;   /* LERP_DURATION_FRAMES = 6 */
/* apertar: encolhe para 0,8 e tinge em 6 quadros; volta ao soltar */
function pressCurve(t, down, up) {
  if (t < down) return 0;
  if (t < up) return outCubic((t - down) / LERP);
  return 1 - outCubic((t - up) / LERP);
}
const pressedState = (k) => ({ tint: k, scale: 1 - 0.2 * k });

/* ---- montagem dos cartões ---- */
const grid = document.getElementById("grid");
function card(title, code, text, build, warm) {
  const c = document.createElement("section"); c.className = "card";
  c.innerHTML = '<div class="stage' + (warm ? " warm" : "") + '"></div><div class="cap"><b>' + title +
    '</b> <code>' + code + '</code><p>' + text + '</p></div>';
  grid.appendChild(c);
  return build(c.querySelector(".stage"));
}
function row(parent, parts) {
  const r = document.createElement("div"); r.className = "row";
  const out = {};
  for (const p of parts) {
    if (typeof p === "string") { const s = document.createElement("span"); s.textContent = p; r.appendChild(s); }
    else { const ic = makeIcon(p[0], p[1]); r.appendChild(ic.el); out[p[2] || p[0]] = ic; }
  }
  parent.appendChild(r); return { el: r, icons: out };
}
function box(stage, cls) { const b = document.createElement("div"); b.className = cls; stage.appendChild(b); return b; }

const anims = [];

/* 1. apertar */
anims.push(card("Apertar", "TYPE_PRESS",
  "Caixa de ajuda. Ao apertar, o ícone encolhe para 0,8 (PRESSED_SCALE) e troca para a cor de apertado em 6 quadros; ao soltar, volta.",
  (st) => {
    const h = box(st, "help");
    const a = row(h, ["Pressione", ["Y", 38], "para entrar no avião."]);
    row(h, ["Use", ["UP", 38], "para abrir o celular."]);
    return (t) => { const T = t % 2.4; set(a.icons.Y, pressedState(pressCurve(T, 1.2, 1.45))); };
  }));

/* 2. segurar */
anims.push(card("Segurar", "TYPE_HOLD",
  "Pílula de contexto. Enquanto segura, o ícone fica apertado e o anel enche (drawRing); ao completar, brilho a 50% (COMPLETION_GLOW_ALPHA) e some.",
  (st) => {
    const p = box(st, "pill");
    const r = row(p, ["Segure", ["Y", 40], "para abrir"]);
    p.appendChild(r.el.firstChild); p.appendChild(r.el.firstChild); p.appendChild(r.el.firstChild); r.el.remove();
    return (t) => {
      const T = t % 3.6, D = 0.5, H = 1.6;
      const held = T >= D && T < D + H;
      const k = held ? outCubic((T - D) / LERP) : (T >= D + H ? 1 - outCubic((T - D - H) / LERP) : 0);
      const ring = T < D ? 0 : T < D + H ? inOut((T - D) / H) : (T < D + H + .5 ? 1 : 0);
      const glow = T >= D + H && T < D + H + .5 ? (T - D - H) / .5 : 0;
      set(r.icons.Y, Object.assign(pressedState(k), { ring, gutter: true, glow }));
    };
  }, true));

/* 3. apertar repetido */
anims.push(card("Apertar repetido", "TYPE_MASH",
  "QTE de força (academia, lutas). Cada toque encolhe o ícone e avança o anel, que volta se você parar.",
  (st) => {
    const c = box(st, "center");
    const r = row(c, [["X", 58]]);
    const l = document.createElement("div"); l.className = "qlabel"; l.textContent = "APERTE REPETIDAMENTE"; c.appendChild(l);
    return (t) => {
      const T = t % 4, tap = 0.19;
      let k = 0, prog = 0;
      if (T < 2.6) { const ph = (T % tap) / tap; k = ph < .45 ? outCubic(ph / .45) : 1 - outCubic((ph - .45) / .55); prog = Math.min(1, T / 2.4); }
      else prog = Math.max(0, 1 - (T - 2.6) / 0.9);
      set(r.icons.X, Object.assign(pressedState(k), { ring: prog, gutter: true, ringColor: "var(--pink)" }));
    };
  }));

/* 4. QTE no mundo */
anims.push(card("Evento de tempo (QTE)", "MeterMicrogame",
  "Disco escuro, trilho a 15% e arco rosa com traço 3. Apertou na hora certa: o anel fica branco, cresce e some.",
  (st) => {
    const c = box(st, "center");
    const wrap = document.createElement("div"); wrap.style.cssText = "position:relative;width:150px;height:150px";
    wrap.innerHTML = '<svg viewBox="0 0 150 150" style="position:absolute;inset:0;overflow:visible">' +
      '<circle cx="75" cy="75" r="50" fill="rgba(0,0,0,.70)"/>' +
      '<circle cx="75" cy="75" r="58" fill="none" stroke="rgba(255,255,255,.15)" stroke-width="7"/>' +
      '<circle class="q" cx="75" cy="75" r="58" fill="none" stroke="rgb(237,84,153)" stroke-width="7" transform="rotate(-90 75 75)"/>' +
      '<circle class="ok" cx="75" cy="75" r="58" fill="none" stroke="#fff" stroke-width="3"/></svg>';
    c.appendChild(wrap);
    const ic = makeIcon("Y", 56); ic.el.style.cssText += ";position:absolute;left:47px;top:47px";
    ic.el.querySelector(".ring").style.display = "none";
    wrap.appendChild(ic.el);
    const q = wrap.querySelector(".q"), ok = wrap.querySelector(".ok"), C = 2 * Math.PI * 58;
    q.style.strokeDasharray = C;
    return (t) => {
      const T = t % 3.2, fill = 1.8;
      const p = Math.min(1, T / fill);
      q.style.strokeDashoffset = C * (1 - p);
      q.style.opacity = T < fill ? 1 : 0;
      const g = T >= fill ? clamp((T - fill) / 0.7) : 0;
      ok.setAttribute("r", 58 + 26 * outCubic(g)); ok.style.opacity = T >= fill ? 1 - g : 0;
      set(ic, pressedState(pressCurve(T, fill - .05, fill + .2)));
    };
  }, true));

/* 5. girar */
anims.push(card("Girar", "TYPE_ROTATE",
  "Girar o analógico. No PC vira “mover o mouse” (mouse com as 4 setas). O motor tem ROTATE_DURATION = 360; o anel enche enquanto você gira.",
  (st) => {
    const c = box(st, "center");
    const r = row(c, [["RS_ROT", 64]]);
    const l = document.createElement("div"); l.className = "qlabel"; l.textContent = "MOVA O MOUSE"; c.appendChild(l);
    return (t) => {
      const T = t % 3; const ring = T < 2.2 ? T / 2.2 : 1;
      const glow = T >= 2.2 && T < 2.7 ? (T - 2.2) / .5 : 0;
      set(r.icons.RS_ROT, { ring: T < 2.7 ? ring : 0, gutter: true, glow });
    };
  }));

/* 6. segurando na lista do canto */
anims.push(card("Apertado / segurando", "COLOR_PROMPT_PRESSED",
  "Lista do canto inferior direito. Enquanto segura, o ícone escurece e inverte (miolo cinza-escuro, letra clara).",
  (st) => {
    const c = box(st, "corner");
    row(c, ["ANDAR", ["LS", 34]]);
    const m = row(c, ["MIRAR", ["LT", 34]]);
    const f = row(c, ["ATIRAR", ["RT", 34]]);
    return (t) => {
      const T = t % 4;
      set(m.icons.LT, pressedState(pressCurve(T, 0.6, 3.2)));
      set(f.icons.RT, pressedState(pressCurve(T, 1.6, 1.9) + pressCurve(T, 2.3, 2.6)));
    };
  }, true));

/* 7. indisponível */
anims.push(card("Indisponível", "alpha",
  "Ação que não dá para usar agora: ícone e texto ficam acinzentados (como o “2D VIEW” no mapa).",
  (st) => {
    const c = box(st, "corner");
    row(c, ["ZOOM", ["RS_UPDOWN", 34]]);
    const off = row(c, ["VISÃO 2D", ["R3", 34]]);
    row(c, ["MARCAR", ["A", 34]]);
    return (t) => { const T = t % 4, a = T < 2 ? 1 : 0.4; off.el.style.opacity = a; };
  }));

/* 8. combinação */
anims.push(card("Combinação", "_primaryIcon + _secondaryIcon",
  "Dois ícones lado a lado. Segurar os dois: cada um fica apertado na sua vez.",
  (st) => {
    const h = box(st, "help");
    const r = row(h, ["Segure", ["LT", 38], "e", ["RT", 38], "para levantar."]);
    return (t) => {
      const T = t % 3.4;
      set(r.icons.LT, pressedState(pressCurve(T, 0.7, 2.6)));
      set(r.icons.RT, pressedState(pressCurve(T, 1.2, 2.6)));
    };
  }, true));

/* 9. rodapé de menu */
anims.push(card("Rodapé de menu", "canto inferior direito",
  "“SELECIONAR / VOLTAR” em linha, caixa alta condensada. Cada toque segue a regra do apertar.",
  (st) => {
    const c = box(st, "corner");
    const r = row(c, ["SELECIONAR", ["A", 34], "  VOLTAR", ["B", 34]]);
    return (t) => {
      const T = t % 3;
      set(r.icons.A, pressedState(pressCurve(T, 0.8, 1.0)));
      set(r.icons.B, pressedState(pressCurve(T, 2.0, 2.2)));
    };
  }));

/* 10a. todos os mouses, grandes, para conferir */
anims.push(card("Todos os mouses", "mouse aprovado em todos os lugares",
  "Todos os ícones de mouse, no mesmo tamanho. Botões: o lado acionado fica branco e o resto cinza. Setas soltas brancas com contorno, com o mesmo respiro do mouse nos quatro lados.",
  (st) => {
    st.style.height = "300px";
    const c = box(st, "center");
    c.style.cssText += ";flex-direction:row;flex-wrap:wrap;justify-content:center;gap:6px 2px;width:96%";
    for (const [k, l] of [["RS","câmera (26)"],["RT","botão esq. (37)"],["LT","botão dir. (35)"],
                          ["RS_UP","cima (21)"],["RS_DOWN","baixo (22)"],["RS_LEFT","esquerda (23)"],
                          ["RS_RIGHT","direita (24)"],["RS_UPDOWN","cima/baixo (27)"],
                          ["RS_LEFTRIGHT","esq./dir. (28)"],["RS_ROT","mover o mouse (29/59)"]]) {
      const w = document.createElement("div");
      w.style.cssText = "display:flex;flex-direction:column;align-items:center;gap:24px;font-size:11px;color:#9aa;width:118px";
      const ic = makeIcon(k, 104); w.appendChild(ic.el);
      const s = document.createElement("span"); s.textContent = l; w.appendChild(s);
      c.appendChild(w);
    }
    return () => {};
  }));
grid.lastChild.style.gridColumn = "1 / -1";

/* 10a2. teclado (bloco em T) ao lado do mouse, mesma escala */
anims.push(card("WASD e setas do teclado", "bloco em T, ao lado do mouse",
  "Mesma escala dos outros ícones. Tecla acionada em branco, não acionada em cinza.",
  (st) => {
    st.style.height = "260px";
    const c = box(st, "center");
    c.style.cssText += ";flex-direction:row;flex-wrap:wrap;justify-content:center;gap:6px 8px;width:96%";
    for (const [k, l] of [["RS","mouse (26)"],["LS","WASD (17/20/58)"],["LS_UD","W/S (18)"],["LS_LR","A/D (19)"],
                          ["DPAD","setas, todas (9)"],["DPAD_NONE","nenhuma (8)"],["DPAD_UD","cima/baixo (10)"],
                          ["DPAD_LR","esq./dir. (11)"]]) {
      const w = document.createElement("div");
      w.style.cssText = "display:flex;flex-direction:column;align-items:center;gap:24px;font-size:11px;color:#9aa;width:128px";
      const ic = makeIcon(k, 104); w.appendChild(ic.el);
      const s = document.createElement("span"); s.textContent = l; w.appendChild(s);
      c.appendChild(w);
    }
    return () => {};
  }));
grid.lastChild.style.gridColumn = "1 / -1";

/* 10b. lista do canto com os mouses */
anims.push(card("Na lista do canto", "como aparece no jogo",
  "Lista do canto inferior direito com os ícones de mouse, no tamanho real do texto.",
  (st) => {
    const c = box(st, "corner");
    row(c, ["ANDAR", ["LS", 34]]);
    row(c, ["CÂMERA", ["RS_ROT", 34]]);
    row(c, ["ZOOM", ["RS_UPDOWN", 34]]);
    row(c, ["GIRAR A ARMA", ["RS_LEFTRIGHT", 34]]);
    return () => {};
  }, true));

/* 10. teste com o teclado e o mouse de verdade */
const KEYMAP = { KeyW: "LS_UP", KeyA: "LS_LEFT", KeyS: "LS_DOWN", KeyD: "LS_RIGHT",
  ShiftLeft: "A", ShiftRight: "A", KeyR: "B", Space: "X", KeyF: "Y", Tab: "LB", KeyQ: "RB",
  Escape: "MENU", KeyV: "VIEW", ControlLeft: "L3", ControlRight: "L3", KeyC: "R3",
  ArrowUp: "UP", ArrowDown: "DOWN", ArrowLeft: "LEFT", ArrowRight: "RIGHT" };
const MOUSEMAP = { 0: "RT", 2: "LT" };
const live = {};
(function () {
  const c = document.createElement("section"); c.className = "card"; c.id = "teste";
  c.style.gridColumn = "1 / -1";
  c.innerHTML = '<div class="stage"><div class="keys"></div></div><div class="cap"><b>Teste com o seu teclado e mouse</b> ' +
    '<code>apertar + segurar</code><p>Aperte as teclas (W A S D, Shift, Espaço, R, F, Q, Tab, Esc, V, C, Ctrl, setas) ou clique ' +
    'com os botões do mouse aqui dentro. Toque rápido = apertar; segure = o anel enche.</p></div>';
  grid.appendChild(c);
  const keys = c.querySelector(".keys");
  const order = [["LS_UP","W"],["LS_LEFT","A"],["LS_DOWN","S"],["LS_RIGHT","D"],["A","Shift (A)"],["X","Espaço (X)"],
    ["B","R (B)"],["Y","F (Y)"],["LB","Tab (LB)"],["RB","Q (RB)"],["LT","botão dir. (LT)"],["RT","botão esq. (RT)"],
    ["MENU","Esc (Menu)"],["VIEW","V (View)"],["L3","Ctrl (L3)"],["R3","C (R3)"],["UP","↑"],["DOWN","↓"],["LEFT","←"],["RIGHT","→"]];
  for (const [k, lbl] of order) {
    const w = document.createElement("div"); w.className = "k";
    const ic = makeIcon(k, 52); w.appendChild(ic.el);
    const s = document.createElement("span"); s.textContent = lbl; w.appendChild(s);
    keys.appendChild(w);
    live[k] = { ic, down: null, up: null };
  }
  const stage = c.querySelector(".stage");
  const press = (k) => { const L = live[k]; if (L && L.down == null) { L.down = now(); L.up = null; } };
  const release = (k) => { const L = live[k]; if (L && L.down != null) { L.up = now(); } };
  addEventListener("keydown", (e) => { const k = KEYMAP[e.code]; if (k) { e.preventDefault(); press(k); } });
  addEventListener("keyup", (e) => { const k = KEYMAP[e.code]; if (k) { e.preventDefault(); release(k); } });
  stage.addEventListener("mousedown", (e) => { const k = MOUSEMAP[e.button]; if (k) { e.preventDefault(); press(k); } });
  addEventListener("mouseup", (e) => { const k = MOUSEMAP[e.button]; if (k) release(k); });
  stage.addEventListener("contextmenu", (e) => e.preventDefault());
  anims.push(() => {
    const T = now();
    for (const k in live) {
      const L = live[k];
      if (L.down == null) { set(L.ic, {}); continue; }
      const HOLD = 1.0;
      const end = L.up == null ? T : L.up;
      const held = end - L.down;
      const ring = held > 0.18 ? clamp((held - 0.18) / HOLD) : 0;
      let tint = outCubic((T - L.down) / LERP);
      let glow = 0;
      if (L.up != null) {
        tint = Math.min(tint, 1 - outCubic((T - L.up) / LERP));
        if (ring >= 1) glow = clamp((T - L.up) / 0.5);
        if (T - L.up > (ring >= 1 ? 0.5 : LERP)) { L.down = null; set(L.ic, {}); continue; }
      } else if (ring >= 1) glow = 0;
      set(L.ic, Object.assign(pressedState(tint), { ring: L.up != null && ring >= 1 ? 1 - glow : ring, gutter: ring > 0, glow }));
    }
  });
})();

/* ---- relógio ---- */
let clock = 0, last = performance.now();
const now = () => clock;
function frame(ts) {
  clock += (ts - last) / 1000 * SPEED; last = ts;
  for (const a of anims) a(clock);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

document.getElementById("plat").onclick = (e) => {
  const p = e.target.dataset.p; if (!p) return; PLAT = p;
  for (const b of e.currentTarget.children) b.classList.toggle("on", b.dataset.p === p);
  all.forEach(paint);
};
document.getElementById("anel").onclick = (e) => {
  const r = e.target.dataset.r; if (!r) return; RING = r;
  for (const b of e.currentTarget.children) b.classList.toggle("on", b.dataset.r === r);
  all.forEach(paint);
};
document.getElementById("vel").onclick = (e) => {
  const v = e.target.dataset.v; if (!v) return; SPEED = +v;
  for (const b of e.currentTarget.children) b.classList.toggle("on", b.dataset.v === v);
};
</script>
</body></html>
"""

if __name__ == "__main__":
    main()

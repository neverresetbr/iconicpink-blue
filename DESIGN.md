# Design anchor: PC keys in place of Xbox buttons

**English** · [Português (BR)](ANCORA.md)

The fixed reference for **every** icon. Check here before drawing or changing
anything, and run the tests (section 5) before approving.

---

## 1. How the game uses the icons

The artwork lives in one file, `input_icons.gfx` (38 symbols
`platform_xbsx.input_icons.Main_Button_N`). **The engine shows, animates and
tints them** (`hud.gfx`, class `InputIconHint`). We replace **only the
artwork**; the engine keeps doing everything else on its own.

### 1.1 Interaction types (engine: `TYPE_PRESS`, `TYPE_HOLD`, `TYPE_MASH`)

| Type | In game | What the engine does |
|---|---|---|
| **Press** (`TYPE_PRESS`) | "Press [RB] to take cover." | shows the icon; on press it flashes and rescales (`PRESSED_SCALE`) |
| **Hold** (`TYPE_HOLD`) | "Hold [LT] to…", "Hold ⓧ to open" | same icon; the text says "Hold"; in the world a **progress ring** appears (`drawRing`) |
| **Mash** (`TYPE_MASH`) | gym, fights | the icon **pulses** (`MASH_EASE`, `mashAnimationCount`) |
| **Quick-time event** (`MeterMicrogame`) | key in the middle of the screen or attached to an object | **dark disc + track + pink progress arc**, icon in the centre; on success the ring turns white and grows |
| **Pressed / holding** (`COLOR_PROMPT_PRESSED`) | corner list while held | the icon **darkens and inverts**: dark-grey body, light letter and outline |
| **Unavailable** | "2D VIEW" on the map | icon and text **greyed out** |
| **Combination** | "Hold [L2] and [R2]" | two icons side by side (`_primaryIcon` / `_secondaryIcon`) |
| **Rotate** (`TYPE_ROTATE`) | rotate the stick | the ring follows the turn (`ROTATE_DURATION = 360`) |

**Engine values** (read from the AS3 code in `hud.gfx`):
`PRESSED_SCALE = 0.8`, `COMPLETION_GLOW_ALPHA = 0.5`,
`COMPLETION_GLOW_SCALE` 1.0 (with track) / 0.68 (without), 64-unit icon
centred (`ICON_OFFSET = -32`), colour change over 6 frames
(`LERP_DURATION_FRAMES`), QTE with a stroke of 3 (`EFFECT_STROKE_THIN`) and a
15% track (`EFFECT_ALPHA_15`). Easing curves and hold time live in the
bytecode (still approximated).

**Checked in the hud code:**
- The button icon is created with `getDefinition("…Main_Button_N")`, placed at
  (-32, -32) and added; the engine **never calls `stop`/`gotoAndStop` on it**.
  A multi-frame icon would loop on its own → **micro-animation is possible
  without touching the engine**.
- The engine only drives its own clips: `gutter` (the progress ring, a
  **multi-frame clip**: progress picks the frame), `gutterBackground`,
  `completionGlow`, `urgent` and `rotate.animation`.

### 1.2 Micro-animation: tested and dropped

We tested the mouse sliding towards its arrow (possible without touching the
engine, see above). **Decision: no animation.** The icons stay still.

### 1.3 Where they appear

| Place | Look |
|---|---|
| **Help box** (top left) | translucent black, square corners, regular text; icon inline, ~1.6× the cap height |
| **Context prompt** (bottom centre) | blue pill, "Hold ⓧ to open" |
| **Bottom right, lists** (map, minigames) | condensed CAPS on the right, icon after the text |
| **Bottom right, menu footer** | "SELECT Ⓐ  BACK Ⓑ" in a row |
| **In the world** (QTE, objects) | icon inside the engine's disc/ring, near the character or object |

---

## 2. Drawing rules (for ALL icons)

1. **No circles.** The circle is console-button language.
2. **White shape, black details** (letter, outline, arrows). In game the black
   outline disappears on dark backgrounds and the letter looks cut out. This is
   what lets the engine tint, invert and grey out our icons like the originals.
3. **Active = white, inactive = grey `rgb(103,103,103)`**, like the original
   D-pad. **Never black for "active"**: it vanishes on dark backgrounds.
4. **Stroke of 3** on every frame (2.5 on small details).
5. **Mouse:** always the approved mouse (`approved/mouse/`).
6. **Letters = vector outlines in the game's typeface**, never an installed
   font (see 4).
7. **Nothing rotates on PC.** "Rotate the stick" becomes what a PC player
   actually does: left (20, 58) = plain WASD; right (29, 59) = move the mouse
   (mouse with 4 arrows). No curved arrow.
8. **Loose arrow (outside a key) = white shape with a 2.5 black outline**
   (arrows around the mouse). A loose black arrow vanishes on dark
   backgrounds. Arrows inside a white key stay black.

## 3. Size standard (64-unit space, like the originals)

The **largest dimension of every icon is 64**, outline included, **centred on
(32, 32)**. Measured by `tools/medir`. Exceptions: the arrows around the mouse
sit outside the 64 (the mouse itself follows the standard), and the T-block is
larger on purpose. SVGs use a 96 frame (`viewBox -16 -16 96 96`) so nothing is
clipped; the scale is the same for all.

| Type | Size | Icons (N) |
|---|---|---|
| Single key (W, A, S, D, F, R, Q, C, V, single arrow) | **64 × 64** | 4-7, 12-15, 25, 31, 33, 36, 39 |
| Wide key (Shift, Space, Tab, Esc, Ctrl) | **64 × 48** | 16, 30, 32, 34, 38 |
| T-block (WASD and arrow keys), square 23-unit keys, letters 55% of the key | **76 × 51** (larger than 64 on purpose: at 64 it looked small) | 8-11, 17-20, 58 |
| Mouse | **41.6 × 64** | 26, 35, 37 |
| Mouse with arrows: **the mouse is the standard** (41.6 × 64, centred on 32,32); arrows sit **outside and don't count** (even gap of 1, each arrow extends 14.5 past the mouse) | mouse 41.6 × 64 | 21-24, 27, 28, 29, 59 |

Xbox originals, for comparison: circles and D-pad 64 × 64, LB/RB 64 × 39,
LT/RT 61 × 64.

## 4. Typography (the game's own interface fonts)

Fonts read from `gfxfontlib_efigs.gfx` by `tools/fonte_jogo.py`. The file comes
from your copy of the game (`tools/preparar.py` → `game/`).

| Use | Font | Cap height | Why |
|---|---|---|---|
| Single key and WASD | `gta_art_deco_bold` | 25.6 (WASD: 12.7) | the typeface of the original A/B/X/Y letters (identical proportions, error 0.005) at the same height |
| Wide key | `gta_art_deco_condensed_bold` | 22.2 | same height as the original LB/RB; "Shift" fits exactly (51.1 of 51) |

## 5. Required tests (always, before approving)

1. `python3 tools/teclas_pc.py output/svg`
2. `python3 tools/teste_padrao.py output/svg` → must print
   **38 ícones, 0 com falha** (centre, 64 limit, size per type).
3. Check against the approved set: `approved/teclas_pc.sha256` (38 OK).
4. Xbox × PC comparison sheet at the same scale (see README).
5. Prompt demo: `python3 tools/demo_animacoes.py game/xbox64 output/svg output/demo.html`.
   Check press, hold, mash, rotate, the QTE and the pressed state on both PC
   and Xbox icons.

## 6. Mapping

Table in `README.md`.

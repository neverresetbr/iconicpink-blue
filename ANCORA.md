# ÂNCORA DE PRODUÇÃO: teclas de PC no lugar dos botões de Xbox

[English](DESIGN.md) · **Português (BR)**

Referência fixa para **todo** ícone. Antes de desenhar ou mudar qualquer
coisa, conferir aqui. Antes de aprovar, rodar os testes (seção 5).

---

## 1. Como o jogo usa os ícones

O desenho fica num só arquivo, `input_icons.gfx` (38 símbolos
`platform_xbsx.input_icons.Main_Button_N`). **Quem mostra, anima e pinta é o
motor** (`hud.gfx`, classe `InputIconHint`). Nós trocamos **só o desenho**; o
motor continua fazendo todo o resto sozinho.

### 1.1 Tipos de interação (do motor: `TYPE_PRESS`, `TYPE_HOLD`, `TYPE_MASH`)

| Tipo | No jogo | O que o motor faz |
|---|---|---|
| **Apertar** (`TYPE_PRESS`) | "Pressione [RB] para se proteger." | mostra o ícone; ao apertar, pisca e muda a escala (`PRESSED_SCALE`) |
| **Segurar** (`TYPE_HOLD`) | "Segure [LT] para…", "Hold ⓧ to open" | o mesmo ícone; o texto diz "Segure"; no mundo aparece um **anel de progresso** (`drawRing`) |
| **Apertar repetido** (`TYPE_MASH`) | academia, lutas | o ícone **pulsa** (`MASH_EASE`, `mashAnimationCount`) |
| **Evento de tempo (QTE)** (`MeterMicrogame`) | tecla no meio da tela ou presa a um objeto | **disco escuro + trilho + arco de progresso rosa**, com o ícone no centro; ao acertar, o anel fica branco e cresce |
| **Apertado / segurando** (`COLOR_PROMPT_PRESSED`) | lista do canto enquanto segura | o ícone **escurece e inverte**: miolo cinza-escuro, letra e contorno claros |
| **Indisponível** | "2D VIEW" no mapa | ícone e texto **acinzentados** |
| **Combinação** | "Segure [L2] e [R2]", "LEVANTAR L2 R2" | dois ícones lado a lado (`_primaryIcon` / `_secondaryIcon`) |
| **Girar** (`TYPE_ROTATE`) | girar o analógico | anel acompanha a volta (`ROTATE_DURATION = 360`) |

**Valores do motor** (lidos do código AS3 do `hud.gfx`):
`PRESSED_SCALE = 0.8`, `COMPLETION_GLOW_ALPHA = 0.5`,
`COMPLETION_GLOW_SCALE` 1,0 (com trilho) / 0,68 (sem), ícone de 64 centrado
(`ICON_OFFSET = -32`), troca de cor em 6 quadros (`LERP_DURATION_FRAMES`),
QTE com traço 3 (`EFFECT_STROKE_THIN`) e trilho a 15% (`EFFECT_ALPHA_15`).
As curvas de easing e o tempo de segurar ficam no bytecode (ainda aproximados).

**Conferido no código do hud:**
- O ícone do botão é criado com `getDefinition("…Main_Button_N")`, posto em
  (-32, -32) e adicionado; o motor **nunca chama `stop`/`gotoAndStop` nele**.
  Um ícone com vários quadros roda em loop sozinho → **micro animação é
  possível sem mexer no motor**.
- O motor só controla os clipes dele: `gutter` (o anel de progresso, que é um
  **clipe com quadros**: o progresso escolhe o quadro), `gutterBackground`,
  `completionGlow`, `urgent` e `rotate.animation` (animação própria do girar).

### 1.2 Micro animação: testada e descartada

Testamos o mouse andando para o lado da seta (dá para fazer sem mexer no
motor, ver acima). **Decisão: sem animação.** Os ícones
ficam parados.

### 1.3 Onde aparecem

| Lugar | Como é |
|---|---|
| **Caixa de ajuda** (canto superior esquerdo) | fundo preto translúcido, cantos retos, texto comum; ícone na linha, ~1,6x a altura das maiúsculas |
| **Prompt de contexto** (embaixo, no centro) | pílula azul, "Segure ⓧ para abrir" |
| **Canto inferior direito, listas** (mapa, minigames) | CAIXA ALTA condensada à direita, ícone depois do texto |
| **Canto inferior direito, rodapé de menus** | "SELECIONAR Ⓐ  VOLTAR Ⓑ" em linha |
| **No mundo** (QTE, objetos) | ícone dentro do disco/anel do motor, perto da personagem ou do objeto |

---

## 2. Regras de desenho (valem para TODOS os ícones)

1. **Sem círculos.** Círculo é linguagem de botão de console.
2. **Forma branca, detalhes pretos** (letra, contorno, setas). No jogo, o
   contorno preto some no fundo escuro e a letra parece vazada. É essa regra
   que faz o motor conseguir tingir, inverter e acinzentar nossos ícones como
   faz com os originais.
3. **Acionado = branco, não acionado = cinza `rgb(103,103,103)`**, como no
   direcional original. **Nunca preto para "acionado"**: some no fundo escuro.
4. **Traço de 3** em todas as molduras (2,5 nos detalhes pequenos).
5. **Mouse:** sempre o mouse aprovado (`approved/mouse/`).
6. **Letras = contorno vetorial na fonte do jogo**, nunca fonte instalada
   (ver 4).
7. **Nada gira no PC.** "Girar o analógico" vira o gesto que o jogador de PC
   faz de verdade: esquerdo (20, 58) = WASD comum; direito (29, 59) = mover o
   mouse (mouse com as 4 setas). Sem seta curva.
8. **Seta solta (fora de tecla) = forma branca com contorno preto** de 2,5
   (setas do mouse com setas). Seta preta solta some
   no fundo escuro. Seta dentro de tecla branca continua preta.

## 3. Padrão de tamanho (espaço de 64, como os originais)

A **maior dimensão de todo ícone é 64**, com o contorno incluído, e ele fica
**centrado em (32, 32)**. Medido por `tools/medir`. Exceção: as setas
do mouse com setas ficam por fora do 64 (o mouse é que segue o padrão). Os
SVGs usam quadro de 96 (`viewBox -16 -16 96 96`) para as setas não serem
cortadas; a escala é a mesma em todos.

| Tipo | Tamanho | Ícones (N) |
|---|---|---|
| Tecla simples (W, A, S, D, F, R, Q, C, V, seta sozinha) | **64 × 64** | 4-7, 12-15, 25, 31, 33, 36, 39 |
| Tecla larga (Shift, Espaço, Tab, Esc, Ctrl) | **64 × 48** | 16, 30, 32, 34, 38 |
| Bloco em T (WASD e setas do teclado), teclas quadradas 1:1 de 23, letras 55% da tecla | **76 × 51** (passa do 64 de propósito: em 64 ficava pequeno) | 8-11, 17-20, 58 |
| Mouse | **41,6 × 64** | 26, 35, 37 |
| Mouse com setas: **o mouse é o padrão** (41,6 × 64, centrado em 32,32); as setas ficam **por fora e não contam** (respiro igual de 1, cada seta passa 14,5 do mouse) | mouse 41,6 × 64 | 21-24, 27, 28, 29, 59 |

Originais de Xbox, para comparar: círculos e direcional 64 × 64, LB/RB
64 × 39, LT/RT 61 × 64.

## 4. Tipografia (fontes da própria interface do jogo)

Fontes lidas do `gfxfontlib_efigs.gfx` por `tools/fonte_jogo.py`. O
arquivo sai da sua cópia do jogo (`tools/preparar.py` → `game/`).

| Uso | Fonte | Altura das maiúsculas | Por quê |
|---|---|---|---|
| Tecla simples e WASD | `gta_art_deco_bold` | 25,6 (WASD: 12,7) | é a fonte das letras A/B/X/Y originais (proporção idêntica, erro 0,005) e a mesma altura |
| Tecla larga | `gta_art_deco_condensed_bold` | 22,2 | mesma altura do LB/RB original; "Shift" cabe exatamente (51,1 de 51) |

## 5. Testes obrigatórios (sempre, antes de aprovar)

1. `python3 tools/teclas_pc.py output/svg`
2. `python3 tools/teste_padrao.py output/svg` → tem de dar
   **38 ícones, 0 com falha** (centro, limite de 64, tamanho por tipo).
3. Conferência com os aprovados: `approved/teclas_pc.sha256` (38 OK).
4. Folha de comparação Xbox × PC na mesma escala (ver README).
5. Demo dos prompts: `python3 tools/demo_animacoes.py game/xbox64 output/svg output/demo.html`.
   Conferir apertar, segurar, repetido, girar, o QTE e o estado apertado nos
   ícones de PC e de Xbox.

## 6. Mapeamento

Tabela no `README.md`.

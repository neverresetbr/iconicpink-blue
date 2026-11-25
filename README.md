# iconicpink-blue

Teclas de **PC (teclado e mouse)** para o lugar dos ícones de controle de
Xbox na interface do GTA VI. Desenhos próprios, vetoriais, no estilo da
interface do jogo: forma branca, detalhes pretos, letras na fonte da própria
interface.

> **Nada do jogo está neste repositório.** Para gerar os ícones você precisa
> da **sua cópia** do jogo: o `preparar.py` tira dela a fonte da interface e os
> ícones originais (para comparar). Testado com a versão de Xbox Series 1.0.2.1.

## Requisitos

- Python 3.9 ou mais novo (só a biblioteca padrão).
- Opcional, só no macOS: Swift (`swiftc`) para o teste de tamanho e a folha
  de comparação.

## Uso

```sh
# 1. Extrair da sua cópia (só lê o .rpf). Cria a pasta jogo/
python3 ferramentas/preparar.py "/caminho/para/data.rpf"

# 2. Gerar os 38 ícones de PC em SVG
python3 ferramentas/teclas_pc.py saida/svg

# 3. Conferir com os aprovados (tem de dar 38 OK)
cd saida/svg && shasum -a 256 -c ../../aprovados/teclas_pc.sha256 && cd ../..

# 4. (macOS) Teste de tamanho: tem de dar "38 ícones, 0 com falha"
swiftc -O ferramentas/medir.swift -o ferramentas/medir
python3 ferramentas/teste_padrao.py saida/svg

# 5. (macOS) Folha Xbox x PC na mesma escala
swiftc -O ferramentas/folha.swift -o ferramentas/folha
args=(); for f in saida/svg/botao_*.svg; do n=$(basename "$f"); args+=("jogo/xbox64/$n" "$f"); done
FOLHA_ESCALA_COMUM=1 ferramentas/folha saida/folha_comparacao.png 8 128 "${args[@]}"

# 6. Demo dos prompts (apertar, segurar, repetido, girar, QTE, apertado...)
python3 ferramentas/demo_animacoes.py jogo/xbox64 saida/svg saida/demo.html
```

A demo é um HTML que roda sozinho, sem internet.

## Mapeamento (símbolo `Main_Button_N` → PC)

| N | Controle | PC |
|---|---|---|
| 30 | A | Shift |
| 31 | B | R |
| 32 | X | Espaço |
| 33 | Y | F |
| 34 | LB | Tab |
| 35 | LT | botão direito do mouse |
| 36 | RB | Q |
| 37 | RT | botão esquerdo do mouse |
| 38 | Menu | Esc |
| 39 | View | V |
| 12-15 | analógico esquerdo (uma direção) | W, S, A, D |
| 16 | L3 | Ctrl |
| 17-20, 58 | analógico esquerdo (neutro, pares, girar) | bloco WASD |
| 21-24, 27, 28 | analógico direito (direções) | mouse com setas |
| 25 | R3 | C |
| 26 | analógico direito (neutro) | mouse |
| 29, 59 | girar o analógico direito | mover o mouse (4 setas) |
| 4-7 | direcional (uma direção) | seta do teclado |
| 8-11 | direcional (nenhuma, todas, pares) | bloco de setas |

## Estado

- Pronto: os 38 desenhos, o teste de tamanho, a folha e a demo.
- Falta: gravar os desenhos de volta no `input_icons.gfx` (trocar as formas de
  cada `Main_Button_N` mantendo símbolos e ids). Só o desenho muda; a lógica
  do jogo que decide e anima os prompts fica como está.

Regras de desenho, medidas e tipografia: [`ANCORA.md`](ANCORA.md).

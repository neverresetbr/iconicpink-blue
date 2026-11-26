# iconicpink-blue, parte 2 (Windows): instala o lançador visual.
#
# Funciona com qualquer fork do VIctory (não muda nenhuma linha dele): o atalho
# abre o Lancador.exe, que abre o seu programa de sempre e cuida do visual
# (tela de abertura, ícone da janela e da barra de tarefas, cursor).
#
# O que faz (tudo neste computador, nada é baixado):
#  - gera icon.ico (16 a 256 px) do logo do pacote (logo\gta6_logo.png) ou do
#    -Logo que você passar (PNG com fundo transparente); sem nenhum dos dois,
#    recorta o emblema do ícone oficial que a build traz (xbs_logo_480.png);
#  - copia a tela de abertura da build (xbs_splash.png);
#  - usa o cursor do pacote (cursor\radar.cur), ou o -Cursor que você passar;
#    -SemCursor deixa o cursor do Windows como está;
#  - compila o Lancador.cs com o compilador que já vem no Windows (.NET 4) e
#    com o ícone no próprio .exe;
#  - cria o atalho na Área de Trabalho e no Menu Iniciar.
# Tudo fica em %LOCALAPPDATA%\iconicpink-blue. A pasta do jogo e o fork não
# são tocados.
#
# Exemplos
#   VIctory e forks (Belobug, avatarmanz...), compilados por você:
#     powershell -ExecutionPolicy Bypass -File instalar.ps1 instalar `
#       -Jogo "D:\jogo\game_scarlett_master.exe" -Logo "D:\logo.png" `
#       -Programa "D:\VIctory\target\release\victory.exe" -Pasta "D:\VIctory" `
#       -Argumentos 'run "D:\jogo\game_scarlett_master.exe" --execute'
#   DexNom (depois do Setup.cmd dele):
#     powershell -ExecutionPolicy Bypass -File instalar.ps1 instalar `
#       -Jogo "D:\jogo\game_scarlett_master.exe" -Logo "D:\logo.png" `
#       -Programa "$env:LOCALAPPDATA\DexNom Runtime\victory-play.exe"
#   (com a pasta-espelho da parte 1, use o game_scarlett_master.exe dela)
#
# Remover (apaga só os atalhos e a pasta %LOCALAPPDATA%\iconicpink-blue):
#   powershell -ExecutionPolicy Bypass -File instalar.ps1 remover
param(
    [Parameter(Mandatory = $true, Position = 0)][ValidateSet("instalar", "remover")][string]$Acao,
    [string]$Jogo,
    [string]$Programa,
    [string]$Argumentos = "",
    [string]$Pasta,
    [string]$Logo,
    [string]$Cursor,
    [switch]$SemCursor,
    [string]$Nome = "Grand Theft Auto VI"
)
$ErrorActionPreference = "Stop"
$destino = Join-Path $env:LOCALAPPDATA "iconicpink-blue"
$visual = Join-Path $destino "visual"
$marca = Join-Path $destino ".iconicpink-blue"
$atalhos = @(
    (Join-Path ([Environment]::GetFolderPath("Desktop")) "$Nome.lnk"),
    (Join-Path ([Environment]::GetFolderPath("Programs")) "$Nome.lnk")
)

if ($Acao -eq "remover") {
    foreach ($a in $atalhos) { if (Test-Path -LiteralPath $a) { Remove-Item -LiteralPath $a; Write-Host "removido: $a" } }
    if (Test-Path -LiteralPath $marca) { Remove-Item -LiteralPath $destino -Recurse -Force; Write-Host "removido: $destino" }
    return
}

if (-not $Jogo -or -not $Programa) { throw "instalar precisa de -Jogo (o game_scarlett_master.exe) e -Programa (o que abre o jogo)" }
foreach ($p in @($Jogo, $Programa)) { if (-not (Test-Path -LiteralPath $p)) { throw "não achei $p" } }
$pastaJogo = Split-Path -Parent $Jogo
$arte = Join-Path $pastaJogo "xbs_splash.png"
if (-not (Test-Path -LiteralPath $arte)) { throw "não achei a tela de abertura da build em $arte" }
if (-not $Pasta) { $Pasta = Split-Path -Parent $Programa }
$csc = Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if (-not (Test-Path -LiteralPath $csc)) { throw "não achei o compilador do .NET Framework 4 em $csc" }

Add-Type -AssemblyName System.Drawing
$TAMANHOS = 16, 20, 24, 32, 40, 48, 64, 96, 128, 256

# Uma imagem do ícone: o logo inteiro centrado num quadrado transparente, ou
# um recorte quadrado (x, y, lado) com cantos arredondados.
function Desenhar([System.Drawing.Image]$src, [int]$t, $recorte) {
    $bmp = New-Object System.Drawing.Bitmap $t, $t, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
    if ($recorte) {
        $r = [Math]::Max(2, [int]($t * 0.16))
        $c = New-Object System.Drawing.Drawing2D.GraphicsPath
        $c.AddArc(0, 0, 2 * $r, 2 * $r, 180, 90); $c.AddArc($t - 2 * $r, 0, 2 * $r, 2 * $r, 270, 90)
        $c.AddArc($t - 2 * $r, $t - 2 * $r, 2 * $r, 2 * $r, 0, 90); $c.AddArc(0, $t - 2 * $r, 2 * $r, 2 * $r, 90, 90)
        $c.CloseFigure(); $g.SetClip($c)
        $g.DrawImage($src, (New-Object System.Drawing.Rectangle 0, 0, $t, $t),
            (New-Object System.Drawing.Rectangle $recorte[0], $recorte[1], $recorte[2], $recorte[2]),
            [System.Drawing.GraphicsUnit]::Pixel)
    } else {
        $k = $t / [Math]::Max($src.Width, $src.Height)
        $w = $src.Width * $k; $h = $src.Height * $k
        $g.DrawImage($src, (New-Object System.Drawing.RectangleF (($t - $w) / 2), (($t - $h) / 2), $w, $h))
    }
    $g.Dispose()
    return $bmp
}

# .ico: até 128 px em BMP (BGRA de baixo para cima + máscara zerada), 256 em PNG.
function Novo-Ico([string]$png, [string]$saida, $recorte) {
    $src = [System.Drawing.Image]::FromFile($png)
    $blobs = @()
    try {
        foreach ($t in $TAMANHOS) {
            $bmp = Desenhar $src $t $recorte
            if ($t -ge 256) {
                $ms = New-Object System.IO.MemoryStream
                $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
                $blobs += , $ms.ToArray()
            } else {
                $rect = New-Object System.Drawing.Rectangle 0, 0, $t, $t
                $data = $bmp.LockBits($rect, [System.Drawing.Imaging.ImageLockMode]::ReadOnly,
                    [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
                $px = New-Object byte[] ($data.Stride * $t)
                [Runtime.InteropServices.Marshal]::Copy($data.Scan0, $px, 0, $px.Length)
                $bmp.UnlockBits($data)
                $ms = New-Object System.IO.MemoryStream
                $bw = New-Object System.IO.BinaryWriter $ms
                $bw.Write([uint32]40); $bw.Write([int32]$t); $bw.Write([int32](2 * $t)); $bw.Write([uint16]1)
                $bw.Write([uint16]32); $bw.Write([uint32]0); $bw.Write([uint32]0); $bw.Write([int32]0)
                $bw.Write([int32]0); $bw.Write([uint32]0); $bw.Write([uint32]0)
                for ($y = $t - 1; $y -ge 0; $y--) { $bw.Write($px, $y * $data.Stride, $t * 4) }
                $bw.Write((New-Object byte[] ([Math]::Floor(($t + 31) / 32) * 4 * $t)))
                $bw.Flush()
                $blobs += , $ms.ToArray()
            }
            $bmp.Dispose()
        }
    } finally { $src.Dispose() }
    $ms = New-Object System.IO.MemoryStream
    $bw = New-Object System.IO.BinaryWriter $ms
    $bw.Write([uint16]0); $bw.Write([uint16]1); $bw.Write([uint16]$TAMANHOS.Count)
    $offset = 6 + 16 * $TAMANHOS.Count
    for ($i = 0; $i -lt $TAMANHOS.Count; $i++) {
        $b = [byte]($TAMANHOS[$i] % 256)
        $bw.Write($b); $bw.Write($b); $bw.Write([byte]0); $bw.Write([byte]0)
        $bw.Write([uint16]1); $bw.Write([uint16]32); $bw.Write([uint32]$blobs[$i].Length); $bw.Write([uint32]$offset)
        $offset += $blobs[$i].Length
    }
    foreach ($blob in $blobs) { $bw.Write($blob) }
    $bw.Flush()
    [IO.File]::WriteAllBytes($saida, $ms.ToArray())
}

New-Item -ItemType Directory -Force -Path $visual | Out-Null
Set-Content -LiteralPath $marca -Value "pasta criada pelo instalar.ps1 do iconicpink-blue"
$ico = Join-Path $visual "icon.ico"
if (-not $Logo) {
    $padrao = Join-Path $PSScriptRoot "logo\gta6_logo.png"
    if (Test-Path -LiteralPath $padrao) { $Logo = $padrao }
}
if ($Logo) {
    if (-not (Test-Path -LiteralPath $Logo)) { throw "não achei o logo em $Logo" }
    Novo-Ico $Logo $ico $null
} else {
    $oficial = Join-Path $pastaJogo "xbs_logo_480.png"
    if (-not (Test-Path -LiteralPath $oficial)) { throw "sem -Logo e sem $oficial" }
    Novo-Ico $oficial $ico @(112, 100, 256)     # o emblema "VI" do ícone oficial
}
Copy-Item -LiteralPath $arte -Destination (Join-Path $visual "splash.png") -Force
$cur = Join-Path $visual "cursor.cur"
if (-not $Cursor -and -not $SemCursor) {
    $padrao = Join-Path $PSScriptRoot "cursor\radar.cur"
    if (Test-Path -LiteralPath $padrao) { $Cursor = $padrao }
}
if ($Cursor -and -not $SemCursor) { Copy-Item -LiteralPath $Cursor -Destination $cur -Force }
elseif (Test-Path -LiteralPath $cur) { Remove-Item -LiteralPath $cur }
Write-Host "visual pronto em $visual"

$exe = Join-Path $destino "Lancador.exe"
$fonte = Join-Path $PSScriptRoot "Lancador.cs"
& $csc /nologo /target:winexe /optimize+ "/win32icon:$ico" /r:System.Core.dll /r:System.Drawing.dll `
    /r:System.Windows.Forms.dll "/out:$exe" $fonte
if ($LASTEXITCODE -ne 0) {
    # se o compilador recusar o ícone, o .exe sai sem ele (o atalho e a janela continuam com o ícone)
    Write-Warning "compilando de novo sem o ícone no .exe"
    & $csc /nologo /target:winexe /optimize+ /r:System.Core.dll /r:System.Drawing.dll `
        /r:System.Windows.Forms.dll "/out:$exe" $fonte
    if ($LASTEXITCODE -ne 0) { throw "o Lancador.cs não compilou (veja acima)" }
}
Write-Host "lançador: $exe"

$shell = New-Object -ComObject WScript.Shell
foreach ($a in $atalhos) {
    $l = $shell.CreateShortcut($a)
    $l.TargetPath = $exe
    $l.Arguments = "--visual `"$visual`" --pasta `"$Pasta`" -- `"$Programa`" $Argumentos"
    $l.WorkingDirectory = $Pasta
    $l.IconLocation = "$ico,0"
    $l.Description = $Nome
    $l.Save()
    Write-Host "atalho: $a"
}
Write-Host "pronto. Se aparecer o ícone antigo, é o cache do Windows: reinicie o Explorer."

# Fase 3/4 (Windows): monta uma PASTA-ESPELHO do jogo com os arquivos
# modificados, sem tocar na pasta original.
#
# - arquivos: hard link para o original (mesmo disco NTFS; não precisa de
#   administrador). Se o original estiver em outro disco, usa link simbólico
#   (precisa do Modo de Desenvolvedor ou de administrador);
# - pastas sem nada trocado: junção para a original;
# - pastas que contêm um arquivo trocado (ex.: data\ttdb\ui): pasta de verdade,
#   montada do mesmo jeito por dentro;
# - arquivos trocados: cópia do modificado.
#
# Montar:
#   powershell -ExecutionPolicy Bypass -File pasta_pc.ps1 montar `
#       -Original "D:\victory-data\game" -Destino "D:\victory-data\game_pc" `
#       -DataRpf "D:\iconicpink\data.rpf" -PlatformTtpf "D:\iconicpink\platform.ttpf"
#   (-DataRpf e -PlatformTtpf são opcionais; use um, outro ou os dois)
#   depois: $env:VICTORY_GAME_DIR = "D:\victory-data\game_pc"
#
# Desmontar (remove SÓ os atalhos e as cópias; a pasta original fica intacta):
#   powershell -ExecutionPolicy Bypass -File pasta_pc.ps1 desmontar -Destino "D:\victory-data\game_pc"
param(
    [Parameter(Mandatory = $true, Position = 0)][ValidateSet("montar", "desmontar")][string]$Acao,
    [string]$Original,
    [string]$DataRpf,
    [string]$PlatformTtpf,
    [Parameter(Mandatory = $true)][string]$Destino
)
$ErrorActionPreference = "Stop"
$MARCA = ".pasta_espelho_iconicpink"   # só existe na pasta-espelho; o desmontar exige

function Espelhar([string]$de, [string]$para, [hashtable]$trocas, [string]$rel) {
    New-Item -ItemType Directory -Path $para | Out-Null
    foreach ($item in Get-ChildItem -LiteralPath $de -Force) {
        $r = if ($rel) { "$rel\$($item.Name)" } else { $item.Name }
        $alvo = Join-Path $para $item.Name
        $chave = $r.ToLower()
        if ($trocas.ContainsKey($chave)) {
            Copy-Item -LiteralPath $trocas[$chave] -Destination $alvo
            $trocas.Remove($chave)
        } elseif ($item.PSIsContainer) {
            $dentro = @($trocas.Keys | Where-Object { $_.StartsWith($chave + "\") })
            if ($dentro.Count -gt 0) {
                Espelhar $item.FullName $alvo $trocas $r
            } else {
                New-Item -ItemType Junction -Path $alvo -Target $item.FullName | Out-Null
            }
        } else {
            try { New-Item -ItemType HardLink -Path $alvo -Target $item.FullName | Out-Null }
            catch { New-Item -ItemType SymbolicLink -Path $alvo -Target $item.FullName | Out-Null }
        }
    }
}

function Montar {
    if (-not (Test-Path -LiteralPath $Original)) { throw "não achei a pasta do jogo: $Original" }
    if (Test-Path -LiteralPath $Destino) { throw "$Destino já existe; desmonte antes" }
    $o = (Resolve-Path -LiteralPath $Original).Path
    $trocas = @{}
    if ($DataRpf) { $trocas["data.rpf"] = (Resolve-Path -LiteralPath $DataRpf).Path }
    if ($PlatformTtpf) { $trocas["data\ttdb\ui\platform.ttpf"] = (Resolve-Path -LiteralPath $PlatformTtpf).Path }
    if ($trocas.Count -eq 0) { throw "passe -DataRpf e/ou -PlatformTtpf" }
    foreach ($k in @($trocas.Keys)) {
        $orig = Join-Path $o $k
        if (-not (Test-Path -LiteralPath $orig)) { throw "não achei $k na pasta do jogo" }
        if ($trocas[$k] -eq (Resolve-Path -LiteralPath $orig).Path) { throw "o arquivo modificado de $k é o próprio original!" }
    }
    $pedidos = @($trocas.Keys)
    Espelhar $o $Destino $trocas ""
    Set-Content -LiteralPath (Join-Path $Destino $MARCA) -Value "pasta-espelho criada por pasta_pc.ps1"
    if ($trocas.Count -gt 0) { throw "não encontrei na pasta do jogo: $($trocas.Keys -join ', ')" }
    foreach ($k in $pedidos) {
        $h = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $Destino $k)).Hash
        Write-Host "trocado: $k  SHA256 $h"
    }
    Write-Host "pronto: $Destino"
    Write-Host "agora: `$env:VICTORY_GAME_DIR = `"$Destino`""
}

function Limpar([string]$pasta) {
    foreach ($item in Get-ChildItem -LiteralPath $pasta -Force) {
        $link = [bool]($item.Attributes -band [IO.FileAttributes]::ReparsePoint)
        if ($item.PSIsContainer -and $link) {
            # remove só a junção (nunca o conteúdo da pasta original)
            [IO.Directory]::Delete($item.FullName, $false)
        } elseif ($item.PSIsContainer) {
            # pasta de verdade criada pelo montar (ex.: data\ttdb\ui): limpa por dentro
            Limpar $item.FullName
        } else {
            # hard link / link simbólico / cópia: remover não afeta o original
            [IO.File]::Delete($item.FullName)
        }
    }
    [IO.Directory]::Delete($pasta, $false)
}

if ($Acao -eq "montar") {
    if (-not $Original) { throw "montar precisa de -Original" }
    Montar
} else {
    if (-not (Test-Path -LiteralPath $Destino)) { Write-Host "nada a desmontar"; return }
    if (-not (Test-Path -LiteralPath (Join-Path $Destino $MARCA))) {
        throw "$Destino não é uma pasta-espelho (falta $MARCA); não removo nada"
    }
    Limpar $Destino
    Write-Host "desmontado: $Destino (original intacto)"
}

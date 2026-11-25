# Fase 3/4 (Windows): monta uma PASTA-ESPELHO do jogo com o data.rpf
# modificado, sem tocar na pasta original.
#
# - arquivos: hard link para o original (mesmo disco NTFS; não precisa de
#   administrador). Se o original estiver em outro disco, usa link simbólico
#   (precisa do Modo de Desenvolvedor ou de administrador);
# - pastas (data, pack): junção para a original;
# - data.rpf: a cópia modificada (copiada para a pasta-espelho).
#
# Montar:
#   powershell -ExecutionPolicy Bypass -File pasta_pc.ps1 montar `
#       -Original "D:\victory-data\game" -DataRpf "D:\iconicpink\data.rpf" `
#       -Destino "D:\victory-data\game_pc"
#   depois: set VICTORY_GAME_DIR=D:\victory-data\game_pc  (ou game_dir no victory.toml)
#
# Desmontar (remove SÓ os atalhos e a cópia; a pasta original fica intacta):
#   powershell -ExecutionPolicy Bypass -File pasta_pc.ps1 desmontar -Destino "D:\victory-data\game_pc"
param(
    [Parameter(Mandatory = $true, Position = 0)][ValidateSet("montar", "desmontar")][string]$Acao,
    [string]$Original,
    [string]$DataRpf,
    [Parameter(Mandatory = $true)][string]$Destino
)
$ErrorActionPreference = "Stop"

function Montar {
    if (-not (Test-Path -LiteralPath (Join-Path $Original "data.rpf"))) { throw "não achei data.rpf em $Original" }
    if (-not (Test-Path -LiteralPath $DataRpf)) { throw "não achei o data.rpf modificado: $DataRpf" }
    if (Test-Path -LiteralPath $Destino) { throw "$Destino já existe; desmonte antes" }
    $o = (Resolve-Path -LiteralPath $Original).Path
    if ((Resolve-Path -LiteralPath $DataRpf).Path -eq (Join-Path $o "data.rpf")) { throw "o -DataRpf é o original!" }
    New-Item -ItemType Directory -Path $Destino | Out-Null
    foreach ($item in Get-ChildItem -LiteralPath $o -Force) {
        $alvo = Join-Path $Destino $item.Name
        if ($item.Name -ieq "data.rpf") { continue }
        if ($item.PSIsContainer) {
            New-Item -ItemType Junction -Path $alvo -Target $item.FullName | Out-Null
        } else {
            try { New-Item -ItemType HardLink -Path $alvo -Target $item.FullName | Out-Null }
            catch { New-Item -ItemType SymbolicLink -Path $alvo -Target $item.FullName | Out-Null }
        }
    }
    Copy-Item -LiteralPath $DataRpf -Destination (Join-Path $Destino "data.rpf")
    $h = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $Destino "data.rpf")).Hash
    Write-Host "pronto: $Destino"
    Write-Host "SHA256 do data.rpf na pasta-espelho: $h"
    Write-Host "agora: set VICTORY_GAME_DIR=$Destino"
}

function Desmontar {
    if (-not (Test-Path -LiteralPath $Destino)) { Write-Host "nada a desmontar"; return }
    foreach ($item in Get-ChildItem -LiteralPath $Destino -Force) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint -and $item.PSIsContainer) {
            # remove só a junção (nunca o conteúdo da pasta original)
            [IO.Directory]::Delete($item.FullName, $false)
        } elseif ($item.PSIsContainer) {
            throw "pasta inesperada em $($item.FullName); não removo nada"
        } else {
            # hard link / link simbólico / cópia: remover não afeta o original
            [IO.File]::Delete($item.FullName)
        }
    }
    [IO.Directory]::Delete($Destino, $false)
    Write-Host "desmontado: $Destino (original intacto)"
}

if ($Acao -eq "montar") {
    if (-not $Original -or -not $DataRpf) { throw "montar precisa de -Original e -DataRpf" }
    Montar
} else {
    Desmontar
}

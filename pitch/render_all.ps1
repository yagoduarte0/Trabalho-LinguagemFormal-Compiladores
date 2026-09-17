# Renderiza todas as cenas do pitch AEGIS na ordem e gera o HTML de apresentacao.
#
#   .\render_all.ps1            -> rascunho rapido (480p)
#   .\render_all.ps1 -Qualidade h   -> qualidade final (1080p)
#   .\render_all.ps1 -SomenteHtml   -> so regera o HTML, sem renderizar

param(
    [ValidateSet("l", "m", "h")]
    [string]$Qualidade = "l",
    [switch]$SomenteHtml
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# A ordem desta lista e a ordem da apresentacao.
$cenas = @(
    @{ arquivo = "scenes\s01_abertura.py";    classe = "Abertura" },
    @{ arquivo = "scenes\s02_sumario.py";     classe = "SumarioExecutivo" },
    @{ arquivo = "scenes\s03_problema.py";    classe = "Problema" },
    @{ arquivo = "scenes\s04_solucao.py";     classe = "Solucao" },
    @{ arquivo = "scenes\s05_arquitetura.py"; classe = "ComoFunciona" },
    @{ arquivo = "scenes\s06_mercado.py";     classe = "Mercado" },
    @{ arquivo = "scenes\s07_modelo.py";      classe = "ModeloDeNegocio" },
    @{ arquivo = "scenes\s08_financeiro.py";  classe = "PlanoFinanceiro" },
    @{ arquivo = "scenes\s09_cronograma.py";  classe = "Cronograma" },
    @{ arquivo = "scenes\s10_encerramento.py"; classe = "Encerramento" }
)

if (-not $SomenteHtml) {
    $total = $cenas.Count
    for ($i = 0; $i -lt $total; $i++) {
        $cena = $cenas[$i]
        Write-Host "[$($i + 1)/$total] renderizando $($cena.classe)..." -ForegroundColor Cyan
        python -m manim --quality $Qualidade $cena.arquivo $cena.classe
        if ($LASTEXITCODE -ne 0) {
            Write-Host "FALHOU em $($cena.classe)" -ForegroundColor Red
            exit 1
        }
    }
}

$ordem = $cenas | ForEach-Object { $_.classe }

Write-Host "gerando pitch.html..." -ForegroundColor Cyan
python -m manim_slides convert @ordem pitch.html --to html --offline --one-file

Write-Host ""
Write-Host "Pronto. Abra pitch.html no Chrome e aperte F11 para tela cheia." -ForegroundColor Green
Write-Host "Avancar: seta direita ou espaco. Voltar: seta esquerda." -ForegroundColor Green

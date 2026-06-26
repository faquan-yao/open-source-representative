# Export Marp slides to PNG images (Windows)
# Usage: export-slide-images.ps1 -MarpFile "path/to/slides.marp.md" [-OutputDir "path/to/video/slides"]

param(
    [Parameter(Mandatory = $true)]
    [string]$MarpFile,

    [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"

$MarpFile = Resolve-Path $MarpFile
$PptDir = Split-Path -Parent $MarpFile
if (-not $OutputDir) {
    $OutputDir = Join-Path $PptDir "video\slides"
} else {
    $OutputDir = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputDir)
}

$SkillDir = Split-Path -Parent $PSScriptRoot
$TechnologyDir = Split-Path -Parent $SkillDir
$ThemeDir = Join-Path $TechnologyDir "document-to-presentation\templates\theme"

if (-not (Test-Path $MarpFile)) {
    Write-Error "Marp file not found: $MarpFile"
}

$VideoDir = Split-Path -Parent $OutputDir
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
New-Item -ItemType Directory -Force -Path $VideoDir | Out-Null

# Marp --images uses output path as filename prefix (creates prefix.001, prefix.002, ...)
$OutputPrefix = Join-Path $VideoDir "slides"

Write-Host "[INFO] Converting: $MarpFile"
Write-Host "[INFO] Output dir: $OutputDir"
Write-Host "[INFO] Theme:      $ThemeDir"

npx --yes @marp-team/marp-cli $MarpFile `
    --images png `
    -o $OutputPrefix `
    --no-stdin `
    --theme-set $ThemeDir

if ($LASTEXITCODE -ne 0) {
    Write-Error "marp-cli failed with exit code $LASTEXITCODE"
}

# Marp writes video/slides.001 (PNG without extension)
Remove-Item -Path (Join-Path $OutputDir "*.png") -Force -ErrorAction SilentlyContinue
$rawImages = Get-ChildItem -Path $VideoDir -File | Where-Object { $_.Name -match '^slides\.\d+$' } | Sort-Object Name
if ($rawImages.Count -eq 0) {
    Write-Error "No slide images were created under $VideoDir"
}

$i = 1
foreach ($img in $rawImages) {
    $dest = Join-Path $OutputDir ("{0:D3}.png" -f $i)
    Copy-Item -Path $img.FullName -Destination $dest -Force
    $i++
}

$images = Get-ChildItem -Path $OutputDir -Filter "*.png" | Sort-Object Name
Write-Host "[OK] Normalized $($images.Count) slide images to $OutputDir"

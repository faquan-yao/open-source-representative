# Export Marp markdown to PPTX (Windows)
# Usage: export-pptx.ps1 -MarpFile "path/to/slides.marp.md" [-OutputFile "path/to/out.pptx"]

param(
    [Parameter(Mandatory = $true)]
    [string]$MarpFile,

    [string]$OutputFile = ""
)

$ErrorActionPreference = "Stop"

$MarpFile = Resolve-Path $MarpFile
if (-not $OutputFile) {
    $base = [System.IO.Path]::ChangeExtension($MarpFile, $null).TrimEnd('.')
    if ($base -match '\.marp$') { $base = $base -replace '\.marp$', '' }
    $OutputFile = "$base.pptx"
} else {
    $OutputFile = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputFile)
}

$SkillDir = Split-Path -Parent $PSScriptRoot
$ThemeDir = Join-Path $SkillDir "templates\theme"

if (-not (Test-Path $MarpFile)) {
    Write-Error "Marp file not found: $MarpFile"
}

Write-Host "[INFO] Converting: $MarpFile"
Write-Host "[INFO] Output:     $OutputFile"
Write-Host "[INFO] Theme:      $ThemeDir"

npx --yes @marp-team/marp-cli $MarpFile `
    --pptx `
    -o $OutputFile `
    --no-stdin `
    --theme-set $ThemeDir

if ($LASTEXITCODE -ne 0) {
    Write-Error "marp-cli failed with exit code $LASTEXITCODE"
}

if (-not (Test-Path $OutputFile)) {
    Write-Error "PPTX was not created: $OutputFile"
}

$size = (Get-Item $OutputFile).Length
Write-Host "[OK] Created $OutputFile ($size bytes)"

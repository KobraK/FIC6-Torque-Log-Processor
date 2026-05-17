param(
    [switch]$SkipInstall
)

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$SrcDir = Join-Path $RepoRoot 'src'
$DocsDir = Join-Path $RepoRoot 'docs'
$BuildDir = Join-Path $RepoRoot 'build'
$ReleaseDir = Join-Path $RepoRoot 'release'
Set-Location $RepoRoot

$VenvDir = Join-Path $RepoRoot '.build-venv-311'
$VenvPython = Join-Path $VenvDir 'Scripts\python.exe'
$ExeName = 'FIC6_Torque_Processor'
$BuildPython = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"

if (-not (Test-Path $BuildPython)) {
    $BuildPython = 'python'
}

if (-not (Test-Path $VenvPython)) {
    & $BuildPython -m venv $VenvDir
}

if (-not $SkipInstall) {
    & $VenvPython -m pip install --upgrade pip
    & $VenvPython -m pip install -r (Join-Path $RepoRoot 'requirements.txt')
    & $VenvPython -m pip install pyinstaller
}

$addData = @(
    "$(Join-Path $RepoRoot 'requirements.txt');.",
    "$(Join-Path $SrcDir 'txt_to_csv.py');.",
    "$(Join-Path $SrcDir 'sanitize_column_headers.py');.",
    "$(Join-Path $SrcDir 'sanitize_column_headers_2ndstep_time.py');.",
    "$(Join-Path $SrcDir 'resample_merge.py');.",
    "$(Join-Path $SrcDir 'rpm_offset_correction.py');.",
    "$(Join-Path $SrcDir 'AFR_analysis_by_powerband.py');.",
    "$(Join-Path $SrcDir 'fuel_trim_analysis.py');.",
    "$(Join-Path $SrcDir 'interactive_plot_corrected_auto.py');."
)

$args = @(
    '--noconfirm',
    '--clean',
    '--onefile',
    '--windowed',
    '--name', $ExeName,
    '--distpath', $ReleaseDir,
    '--workpath', (Join-Path $BuildDir 'pyinstaller'),
    '--specpath', (Join-Path $BuildDir 'spec')
)

foreach ($item in $addData) {
    $args += '--add-data'
    $args += $item
}

$args += (Join-Path $SrcDir 'main.py')

& $VenvPython -m PyInstaller @args
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

$exePath = Join-Path $ReleaseDir "$ExeName.exe"
if (-not (Test-Path $exePath)) {
    throw "Build completed without creating $exePath"
}

$readmePath = Join-Path $DocsDir 'PORTABLE_START_HERE.txt'
if (Test-Path $readmePath) {
    Copy-Item $readmePath (Join-Path $ReleaseDir 'START_HERE.txt') -Force
}

Write-Host ""
Write-Host "Portable EXE created:"
Write-Host $exePath

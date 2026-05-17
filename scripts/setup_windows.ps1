param(
    [switch]$NoLaunch
)

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
Set-Location $RepoRoot

function Get-PythonLauncher {
    $candidates = @(
        @{ Command = 'py'; Args = @('-3.13') },
        @{ Command = 'py'; Args = @('-3.12') },
        @{ Command = 'py'; Args = @('-3.11') },
        @{ Command = 'py'; Args = @('-3.10') },
        @{ Command = 'py'; Args = @('-3') },
        @{ Command = 'python'; Args = @() }
    )

    foreach ($candidate in $candidates) {
        try {
            $versionArgs = @()
            $versionArgs += $candidate.Args
            $versionArgs += '-c'
            $versionArgs += "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')"
            $versionText = & $candidate.Command @versionArgs
            if ($LASTEXITCODE -ne 0) {
                continue
            }

            $version = [version]$versionText.Trim()
            if ($version -ge [version]'3.10') {
                return [pscustomobject]@{
                    Command = $candidate.Command
                    Args = $candidate.Args
                    Version = $version
                }
            }
        } catch {
            continue
        }
    }

    return $null
}

$python = Get-PythonLauncher
if (-not $python) {
    throw "Python 3.10+ was not found. Install Python first, then rerun this setup."
}

$VenvDir = Join-Path $RepoRoot '.venv'
$VenvPython = Join-Path $VenvDir 'Scripts\python.exe'

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating virtual environment in $VenvDir"
    $venvArgs = @()
    $venvArgs += $python.Args
    $venvArgs += '-m'
    $venvArgs += 'venv'
    $venvArgs += $VenvDir
    & $python.Command @venvArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create the virtual environment."
    }
}

Write-Host "Using Python $($python.Version) from $($python.Command)"
Write-Host "Upgrading pip and installing requirements..."
& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "pip upgrade failed."
}

& $VenvPython -m pip install -r (Join-Path $RepoRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) {
    throw "Dependency installation failed."
}

Write-Host ""
Write-Host "Setup complete."
Write-Host "The app is ready in $VenvDir"

if (-not $NoLaunch) {
    Write-Host "Launching the GUI..."
    & $VenvPython (Join-Path $RepoRoot 'src\main.py')
}

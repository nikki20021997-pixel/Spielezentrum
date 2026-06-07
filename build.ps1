$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Path $MyInvocation.MyCommand.Path -Parent
Set-Location $scriptDir

if (!(Test-Path -Path './version.txt')) {
    Write-Error 'version.txt fehlt. Erstelle sie mit einer Versionsnummer wie 1.0.0.'
}

$version = Get-Content './version.txt' -Raw
$version = $version.Trim()
if ([string]::IsNullOrWhiteSpace($version)) {
    Write-Error 'Die Versionsnummer in version.txt ist leer.'
}

$exeName = "spielezentrum_$version.exe"
$releaseDir = Join-Path $scriptDir 'release'

Write-Host "Baue Version $version..."
# Remove previous build artifacts to ensure a fresh build
if (Test-Path -Path './dist') { Remove-Item -Recurse -Force './dist' }
if (Test-Path -Path './build') { Remove-Item -Recurse -Force './build' }
if (Test-Path -Path './__pycache__') { Remove-Item -Recurse -Force './__pycache__' }

python -m PyInstaller --noconfirm --clean --onefile --windowed --name "spielezentrum_$version" spielezentrum.py

if (!(Test-Path -Path $releaseDir)) {
    New-Item -Path $releaseDir -ItemType Directory | Out-Null
}

$distExe = Join-Path $scriptDir "dist\$exeName"
if (!(Test-Path -Path $distExe)) {
    Write-Error "Build fehlgeschlagen: $distExe wurde nicht gefunden."
}

$destExe = Join-Path $releaseDir $exeName
Copy-Item -Path $distExe -Destination $destExe -Force

$zipName = "spielezentrum_v$version.zip"
$zipPath = Join-Path $releaseDir $zipName
if (Test-Path -Path $zipPath) {
    Remove-Item -Path $zipPath -Force
}
Compress-Archive -Path $destExe -DestinationPath $zipPath

Write-Host "Build abgeschlossen."
Write-Host "Executable: $destExe"
Write-Host "ZIP: $zipPath"

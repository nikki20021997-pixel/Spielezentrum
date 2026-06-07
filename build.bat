@echo off
setlocal

if not exist version.txt (
  echo version.txt fehlt. Erstelle sie mit einer Versionsnummer wie 1.0.0.
  exit /b 1
)
for /f "delims=" %%v in (version.txt) do set VERSION=%%v
if "%VERSION%"=="" (
  echo version.txt darf nicht leer sein.
  exit /b 1
)
set EXE_NAME=spielezentrum_%VERSION%.exe
set RELEASE_DIR=release

echo Baue Version %VERSION%...
rem Clean previous build artifacts to ensure fresh build
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist __pycache__ rmdir /s /q __pycache__

python -m PyInstaller --noconfirm --clean --onefile --windowed --name spielezentrum_%VERSION% spielezentrum.py
if errorlevel 1 (
  echo Build fehlgeschlagen.
  exit /b 1
)
if not exist %RELEASE_DIR% mkdir %RELEASE_DIR%
copy /y dist\%EXE_NAME% %RELEASE_DIR%\%EXE_NAME%
powershell -Command "Compress-Archive -Path '%RELEASE_DIR%\%EXE_NAME%' -DestinationPath '%RELEASE_DIR%\spielezentrum_v%VERSION%.zip' -Force"
echo Build abgeschlossen.
echo Executable: %RELEASE_DIR%\%EXE_NAME%
echo ZIP: %RELEASE_DIR%\spielezentrum_v%VERSION%.zip
endlocal

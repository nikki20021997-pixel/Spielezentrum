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
set APP_EXE=spielezentrum_%VERSION%.exe
set LAUNCHER_EXE=launcher_%VERSION%.exe
set RELEASE_DIR=release

rem Entferne alte lokale Release-Artefakte außer der aktuellen Version
if exist %RELEASE_DIR% (
  echo Loesche alte lokale Artefakte aus %RELEASE_DIR%...
  powershell -Command "Get-ChildItem -Path '%RELEASE_DIR%\*' -Include 'spielezentrum_*.exe','launcher_*.exe','spielezentrum_v*.zip','launcher_v*.zip' -File | Where-Object { $_.Name -notlike '*%VERSION%*' } | Remove-Item -Force"
)

echo Baue Version %VERSION%...
rem Clean previous build artifacts to ensure fresh build
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist __pycache__ rmdir /s /q __pycache__

rem Build main application
python -m PyInstaller --noconfirm --clean --onefile --windowed --name spielezentrum_%VERSION% --distpath dist\app --workpath build\app --specpath build\app spielezentrum.py
if errorlevel 1 (
  echo Build der Hauptanwendung fehlgeschlagen.
  exit /b 1
)

rem Build launcher
set LAUNCHER_CONFIG=%CD%\update_config.json
python -m PyInstaller --noconfirm --clean --onefile --windowed --name launcher_%VERSION% --add-data "%LAUNCHER_CONFIG%;." --distpath dist\launcher --workpath build\launcher --specpath build\launcher launcher.py
if errorlevel 1 (
  echo Build des Launchers fehlgeschlagen.
  exit /b 1
)

if not exist %RELEASE_DIR% mkdir %RELEASE_DIR%
copy /y dist\app\%APP_EXE% %RELEASE_DIR%\%APP_EXE%
copy /y dist\launcher\%LAUNCHER_EXE% %RELEASE_DIR%\%LAUNCHER_EXE%
copy /y update_config.json %RELEASE_DIR%\update_config.json

powershell -Command "Compress-Archive -Path '%RELEASE_DIR%\%APP_EXE%' -DestinationPath '%RELEASE_DIR%\spielezentrum_v%VERSION%.zip' -Force"
powershell -Command "Compress-Archive -Path '%RELEASE_DIR%\%LAUNCHER_EXE%' -DestinationPath '%RELEASE_DIR%\launcher_v%VERSION%.zip' -Force"

rem Entferne alte lokale Git-Tags außer dem aktuellen Release-Tag, falls Git installiert ist
where git >nul 2>&1
if errorlevel 0 (
  git rev-parse --is-inside-work-tree >nul 2>&1
  if errorlevel 0 (
    echo Entferne alte Git-Tags, behalte nur v%VERSION%...
    for /f "delims=" %%g in ('git tag') do (
      if /I not "%%g"=="v%VERSION%" (
        echo Loesche lokalen Tag %%g
        git tag -d "%%g" >nul 2>&1
        echo Loesche entfernten Tag %%g, falls vorhanden
        git push origin --delete "%%g" >nul 2>&1
      )
    )
  ) else (
    echo Kein Git-Repository erkannt, Git-Tag-Cleanup wird uebersprungen.
  )
) else (
  echo Git nicht gefunden, Git-Tag-Cleanup wird uebersprungen.
)

set "GIT_PATH="
if exist "%ProgramFiles%\Git\cmd\git.exe" (
  set "GIT_PATH=%ProgramFiles%\Git\cmd\git.exe"
) else if exist "%ProgramFiles%\Git\bin\git.exe" (
  set "GIT_PATH=%ProgramFiles%\Git\bin\git.exe"
) else if exist "%ProgramFiles(x86)%\Git\cmd\git.exe" (
  set "GIT_PATH=%ProgramFiles(x86)%\Git\cmd\git.exe"
) else if exist "%ProgramFiles(x86)%\Git\bin\git.exe" (
  set "GIT_PATH=%ProgramFiles(x86)%\Git\bin\git.exe"
)
if defined GIT_PATH (
  for %%D in ("%GIT_PATH%") do (
    set "PATH=%%~dpD;%PATH%"
    echo Git gefunden: %GIT_PATH%, fuege %%~dpD zum PATH hinzu.
  )
)

set "GH_PATH="
if exist "%ProgramFiles%\GitHub CLI\gh.exe" (
  set "GH_PATH=%ProgramFiles%\GitHub CLI\gh.exe"
) else if exist "%ProgramFiles(x86)%\GitHub CLI\gh.exe" (
  set "GH_PATH=%ProgramFiles(x86)%\GitHub CLI\gh.exe"
) else (
  where gh >nul 2>&1
  if not errorlevel 1 (
    for /f "delims=" %%p in ('where gh') do if not defined GH_PATH set "GH_PATH=%%p"
  )
)

if defined GH_PATH (
  echo GitHub CLI gefunden: %GH_PATH%
) else (
  echo GitHub CLI 'gh' nicht gefunden. Upload der Release-Artefakte wird uebersprungen.
  set "UPLOAD_SKIPPED=1"
)

if not defined GH_PATH (
  goto :SKIP_GH_UPLOAD
)

"%GH_PATH%" auth status >nul 2>&1
if errorlevel 1 (
  if defined GITHUB_TOKEN (
    echo GitHub CLI ist nicht authentifiziert. Versuche automatische Anmeldung mit GITHUB_TOKEN...
    set "GH_TOKEN_FILE=%TEMP%\gh_token_%RANDOM%.txt"
    >"%GH_TOKEN_FILE%" echo %GITHUB_TOKEN%
    "%GH_PATH%" auth login --with-token < "%GH_TOKEN_FILE%"
    del /f /q "%GH_TOKEN_FILE%" >nul 2>&1
    "%GH_PATH%" auth status >nul 2>&1
    if errorlevel 1 (
      echo Automatische Anmeldung mit Token fehlgeschlagen. Upload wird uebersprungen.
      set "UPLOAD_SKIPPED=1"
      pause >nul
      goto :SKIP_GH_UPLOAD
    )
  ) else (
    echo GitHub CLI ist nicht authentifiziert. Starte "gh auth login --web"...
    "%GH_PATH%" auth login --web
    "%GH_PATH%" auth status >nul 2>&1
    if errorlevel 1 (
      echo Anmeldung nicht abgeschlossen. Upload wird uebersprungen.
      set "UPLOAD_SKIPPED=1"
      pause >nul
      goto :SKIP_GH_UPLOAD
    )
  )
)

echo GitHub Release v%VERSION% hochladen...
set "GH_OUTPUT=%TEMP%\gh_upload_%RANDOM%.txt"
set "GH_ASSETS_OUTPUT=%TEMP%\gh_assets_%RANDOM%.txt"
"%GH_PATH%" release view v%VERSION% >"%GH_OUTPUT%" 2>&1
if errorlevel 1 (
  echo Release v%VERSION% existiert nicht. Erstelle neuen Release...
  "%GH_PATH%" release create v%VERSION% "%RELEASE_DIR%\%APP_EXE%" "%RELEASE_DIR%\%LAUNCHER_EXE%" "%RELEASE_DIR%\spielezentrum_v%VERSION%.zip" "%RELEASE_DIR%\launcher_v%VERSION%.zip" --title "Release v%VERSION%" --notes "Automatisch erstellt von build.bat" >"%GH_OUTPUT%" 2>&1
  if errorlevel 1 (
    echo Fehler: Release konnte nicht erstellt werden.
    type "%GH_OUTPUT%"
    set "UPLOAD_SKIPPED=1"
    pause >nul
  ) else (
    echo Release erstellt und Artefakte hochgeladen.
    echo Verfügbare Release-Artefakte:
    "%GH_PATH%" release view v%VERSION% --json assets --jq ".assets[].name" >"%GH_ASSETS_OUTPUT%" 2>&1
    type "%GH_ASSETS_OUTPUT%" 2>nul
  )
) else (
  echo Entferne alte GitHub Releases ausser v%VERSION%...
  for /f "delims=" %%t in ('"%GH_PATH%" release list --limit 100 --json tagName --jq ".[].tagName"') do (
    if /I not "%%t"=="v%VERSION%" (
      echo Loesche GitHub Release %%t...
      "%GH_PATH%" release delete %%t --yes >"%GH_OUTPUT%" 2>&1
      if errorlevel 1 (
        echo Warnung: Loeschen von %%t fehlgeschlagen.
        type "%GH_OUTPUT%"
      )
    )
  )
  echo Release v%VERSION% existiert bereits. Aktualisiere Artefakte...
  "%GH_PATH%" release upload v%VERSION% "%RELEASE_DIR%\%APP_EXE%" "%RELEASE_DIR%\%LAUNCHER_EXE%" "%RELEASE_DIR%\spielezentrum_v%VERSION%.zip" "%RELEASE_DIR%\launcher_v%VERSION%.zip" --clobber >"%GH_OUTPUT%" 2>&1
  if errorlevel 1 (
    echo Fehler: Artefakte konnten nicht hochgeladen werden.
    type "%GH_OUTPUT%"
    set "UPLOAD_SKIPPED=1"
    pause >nul
  ) else (
    echo Artefakte aktualisiert.
    echo Verfügbare Release-Artefakte:
    "%GH_PATH%" release view v%VERSION% --json assets --jq ".assets[].name" >"%GH_ASSETS_OUTPUT%" 2>&1
    type "%GH_ASSETS_OUTPUT%" 2>nul
  )
)
if exist "%GH_OUTPUT%" del /f /q "%GH_OUTPUT%" >nul 2>&1
if exist "%GH_ASSETS_OUTPUT%" del /f /q "%GH_ASSETS_OUTPUT%" >nul 2>&1

:SKIP_GH_UPLOAD
if defined UPLOAD_SKIPPED (
  echo Druecke eine Taste zum Beenden...
  pause >nul
)

rem Wenn vorhanden: commit und push der Release-Dateien in den Repo-Ordner `release/`
set "COMMIT_OUTPUT=%TEMP%\git_commit_%RANDOM%.txt"
where git >nul 2>&1
if errorlevel 0 (
  git rev-parse --is-inside-work-tree >nul 2>&1
  if errorlevel 0 (
    echo Commit release-Artefakte in das Git-Repository unter release/...
    rem Entferne alte release-Dateien aus Git (behalte nur die aktuelle Version)
    pushd "%RELEASE_DIR%" >nul 2>&1
    for %%F in (*.*) do (
      echo %%F | findstr /I "%VERSION%" >nul
      if errorlevel 1 (
        echo Entferne alte Datei %%F aus Git...
        git rm -f "%RELEASE_DIR%\%%F" >"%COMMIT_OUTPUT%" 2>&1
      )
    )
    popd >nul 2>&1

    git add "%RELEASE_DIR%\%APP_EXE%" "%RELEASE_DIR%\%LAUNCHER_EXE%" "%RELEASE_DIR%\spielezentrum_v%VERSION%.zip" "%RELEASE_DIR%\launcher_v%VERSION%.zip" >"%COMMIT_OUTPUT%" 2>&1
    git commit -m "Add release v%VERSION%" >"%COMMIT_OUTPUT%" 2>&1
    if errorlevel 1 (
      echo Keine neuen Änderungen zu committen oder Commit fehlgeschlagen.
      type "%COMMIT_OUTPUT%" 2>nul
    ) else (
      echo Pushe Release-Dateien in Branch 'main'...
      git push origin main >"%COMMIT_OUTPUT%" 2>&1
      if errorlevel 1 (
        echo Fehler beim Pushen der Release-Dateien.
        type "%COMMIT_OUTPUT%" 2>nul
        pause >nul
      ) else (
        echo Release-Dateien erfolgreich in 'release/' auf Branch 'main' gepusht.
      )
    )
  ) else (
    echo Arbeitsverzeichnis ist kein Git-Repository; push wird uebersprungen.
  )
) else (
  echo Git nicht gefunden; push der Release-Dateien wird uebersprungen.
)
if exist "%COMMIT_OUTPUT%" del /f /q "%COMMIT_OUTPUT%" >nul 2>&1

echo Build abgeschlossen.
echo App: %RELEASE_DIR%\%APP_EXE%
echo Launcher: %RELEASE_DIR%\%LAUNCHER_EXE%
echo App ZIP: %RELEASE_DIR%\spielezentrum_v%VERSION%.zip
echo Launcher ZIP: %RELEASE_DIR%\launcher_v%VERSION%.zip
endlocal

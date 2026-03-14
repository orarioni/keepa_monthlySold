@echo off
setlocal

cd /d "%~dp0"

set "APP_NAME=KeepaMonthlySales"
set "PYTHON_EXE=.venv\Scripts\python.exe"
set "DIST_DIR=dist\%APP_NAME%"
set "EXE_PATH=%DIST_DIR%\%APP_NAME%.exe"

echo ========================================
echo   Build Release for %APP_NAME%
echo ========================================
echo.

if not exist "%PYTHON_EXE%" (
    echo [ERROR] 仮想環境の Python が見つかりません: %PYTHON_EXE%
    echo [INFO] 先に以下を実行してください:
    echo        py -m venv .venv
    echo        .\.venv\Scripts\Activate.ps1
    echo        python -m pip install -r requirements.txt
    goto :error
)

echo [INFO] Python executable:
"%PYTHON_EXE%" -c "import sys; print(sys.executable)"
if errorlevel 1 goto :error

echo.
echo [INFO] Installing requirements...
"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo.
echo [INFO] Building executable...
"%PYTHON_EXE%" -m PyInstaller --noconfirm --clean --onedir --name "%APP_NAME%" keepa_enrich.py
if errorlevel 1 goto :error

if not exist "%EXE_PATH%" (
    echo [ERROR] ビルド成果物が見つかりません: %EXE_PATH%
    goto :error
)

echo.
echo [INFO] Copying launcher batch files...
if exist "run.bat" (
    copy /Y "run.bat" "%DIST_DIR%\" >nul
    if errorlevel 1 goto :error
)

if exist "run_burst.bat" (
    copy /Y "run_burst.bat" "%DIST_DIR%\" >nul
    if errorlevel 1 goto :error
)

if exist "run_drip.bat" (
    copy /Y "run_drip.bat" "%DIST_DIR%\" >nul
    if errorlevel 1 goto :error
)

echo.
echo [INFO] Copying README...
if exist "README_keepa.md" (
    copy /Y "README_keepa.md" "%DIST_DIR%\" >nul
    if errorlevel 1 goto :error
)

echo.
echo [INFO] Preparing editable config.ini...
if exist "config.ini" (
    copy /Y "config.ini" "%DIST_DIR%\config.ini" >nul
    if errorlevel 1 goto :error
    echo [INFO] config.ini をコピーしました。
) else (
    if exist "config.ini.example" (
        copy /Y "config.ini.example" "%DIST_DIR%\config.ini" >nul
        if errorlevel 1 goto :error
        echo [INFO] config.ini.example から config.ini を作成しました。
    ) else (
        echo [ERROR] config.ini も config.ini.example も見つかりません。
        goto :error
    )
)

echo.
echo [INFO] Copying optional files...
if exist "output.xlsx" (
    copy /Y "output.xlsx" "%DIST_DIR%\" >nul
    if errorlevel 1 goto :error
    echo [INFO] output.xlsx をコピーしました。
)

if exist "asin_cache.csv" (
    copy /Y "asin_cache.csv" "%DIST_DIR%\" >nul
    if errorlevel 1 goto :error
    echo [INFO] asin_cache.csv をコピーしました。
)

echo.
echo ========================================
echo [OK] Build completed successfully.
echo ========================================
echo [INFO] Release folder:
echo        %CD%\%DIST_DIR%
echo.
echo [INFO] 配布前に確認:
echo   1. %DIST_DIR%\config.ini を必要に応じて編集
echo   2. APIキーが引用符なしで入っているか確認
echo   3. output.xlsx を差し替える
echo   4. run.bat で起動確認
echo.
pause
exit /b 0

:error
echo.
echo ========================================
echo [ERROR] Build failed.
echo ========================================
pause
exit /b 1
@echo off
rem Keepa Monthly Sales - drip mode launcher for cmd.exe
cd /d "%~dp0"

KeepaMonthlySales.exe --mode drip
if errorlevel 1 (
  echo エラーで終了しました。keepa_enrich.log を確認してください。
) else (
  echo 正常終了しました。
)

pause

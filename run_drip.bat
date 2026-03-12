@echo off
rem Keepa Monthly Sales - drip mode launcher for cmd.exe
cd /d "%~dp0"

KeepaMonthlySales.exe --mode drip --tokens-per-minute 5 --interval-seconds 60 --stop-when-tokens-below 10 --max-zero-budget-cycles 3 --max-token-status-failures 3
if errorlevel 1 (
  echo エラーで終了しました。keepa_enrich.log を確認してください。
) else (
  echo 正常終了しました。
)

pause

@echo off
chcp 65001 >nul 2>&1
echo.
echo =========================================
echo  NEO-DOCK -- Backend Baslatiliyor
echo =========================================
echo.

set "PYTHON=C:\Users\Taykuth\AppData\Local\Programs\Python\Python311\python.exe"
set "PROJECT=c:\Users\Taykuth\Desktop\Tez [Frontend]\neodock"
set "PYTHONUTF8=1"
set "PYTHONPATH=%PROJECT%"

cd /d "%PROJECT%"

echo [1/2] Ortam kontrol ediliyor...
"%PYTHON%" -c "import fastapi; import uvicorn; print('Paketler hazir.')" 2>&1
if errorlevel 1 (
    echo HATA: Paketler eksik.
    pause
    exit /b 1
)

echo.
echo [2/2] API sunucusu baslatiliyor...
echo   --^> http://localhost:8000
echo   --^> http://localhost:8000/docs  (Swagger UI)
echo.
echo Durdurmak icin CTRL+C
echo.

"%PYTHON%" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

pause

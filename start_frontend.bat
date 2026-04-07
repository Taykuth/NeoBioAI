@echo off
echo.
echo =========================================
echo  NEO-DOCK -- Frontend Baslatiliyor
echo =========================================
echo.

cd /d "c:\Users\Taykuth\Desktop\Tez [Frontend]\neodock\frontend"

if not exist "node_modules" (
    echo [1/2] npm paketleri kuruluyor... (ilk seferde surebilir)
    npm install
)

echo.
echo [2/2] Gelistirme sunucusu baslatiliyor...
echo   --> http://localhost:3000
echo   --> Dashboard: http://localhost:3000/dashboard
echo.
echo Durdurmak icin CTRL+C
echo.

npm run dev

pause

@echo off
cd /d "%~dp0"
py run_detil_su.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Gagal menjalankan aplikasi.
    echo Pastikan Python sudah terinstall dan dependensi sudah dipasang.
    echo.
    pause
)

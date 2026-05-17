@echo off
echo ============================================
echo  PlanHub v1.0 - Compilation PyInstaller
echo ============================================

REM Vérifier Python
python --version >nul 2>&1 || (echo Python non trouvé. Installez Python 3.10+. & pause & exit /b 1)

REM Installer dépendances
echo.
echo Installation des dépendances...
pip install customtkinter pillow matplotlib pandas openpyxl reportlab pyinstaller

REM Compilation
echo.
echo Compilation en cours...
pyinstaller ^
  --onefile ^
  --windowed ^
  --name "PlanHub" ^
  --add-data "license_validator.py;." ^
  --add-data "data;data" ^
  --add-data "assets;assets" ^
  --hidden-import customtkinter ^
  --hidden-import PIL ^
  --hidden-import matplotlib ^
  --hidden-import pandas ^
  --hidden-import openpyxl ^
  --hidden-import reportlab ^
  main.py

echo.
if exist dist\PlanHub.exe (
  echo ============================================
  echo  SUCCES ! Executable : dist\PlanHub.exe
  echo ============================================
) else (
  echo ECHEC de la compilation. Verifiez les erreurs ci-dessus.
)
pause

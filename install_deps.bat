@echo off
echo Installation des dependances PlanHub...
pip install customtkinter>=5.2.0 Pillow>=10.0.0 matplotlib>=3.7.0 pandas>=2.0.0 openpyxl>=3.1.0 reportlab>=4.0.0
echo.
echo Lancement de PlanHub en mode développement...
python main.py
pause

@echo off
echo ============================================
echo  PlanHub — Initialisation GitHub
echo ============================================
echo.

set /p GITHUB_USER=Entrez votre username GitHub : 
set /p REPO_NAME=Nom du depot GitHub (PlanHub) : 

if "%REPO_NAME%"=="" set REPO_NAME=PlanHub

echo.
echo Initialisation Git...
git init
git add .
git commit -m "Initial commit — PlanHub v1.0"
git branch -M main
git remote add origin https://github.com/%GITHUB_USER%/%REPO_NAME%.git

echo.
echo Push vers GitHub...
git push -u origin main

echo.
echo ============================================
echo  Allez sur : https://github.com/%GITHUB_USER%/%REPO_NAME%/actions
echo  La compilation demarre automatiquement !
echo  PlanHub.exe sera disponible dans ~ 8 minutes
echo ============================================
pause

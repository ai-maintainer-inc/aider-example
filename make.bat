@echo off
SETLOCAL

REM Variables
SET IMAGE_NAME=aider_harness
SET HOME=/app

:menu
echo.
echo Please choose:
echo [1] Build
echo [2] Run
echo [3] Clean
echo [Q] Quit
set /p choice="Enter your choice: "

if "%choice%"=="1" goto build
if "%choice%"=="2" goto run
if "%choice%"=="3" goto clean
if /I "%choice%"=="Q" exit /b

goto menu

:build
docker build -t %IMAGE_NAME% .
goto menu

:run
docker run -e OPENAI_API_KEY=%OPENAI_API_KEY% -v %cd%:%HOME% %IMAGE_NAME%
goto menu

:clean
docker rmi -f %IMAGE_NAME%
goto menu

ENDLOCAL

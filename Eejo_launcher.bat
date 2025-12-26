@echo off
REM Get the directory of the current .bat file
set "scriptDir=%~dp0"

REM Define the Python file name
set "pythonFile=SwTimerMain.py"

REM Get the current IPv4 address (excluding loopback and virtual adapters)
for /f "tokens=2 delims=:" %%f in ('ipconfig ^| findstr /R "IPv4.*" ^| findstr /V "169.254"') do (
    set "ip=%%f"
    goto :foundIP
)

:foundIP
REM Trim leading space
set "ip=%ip:~1%"

REM Define Edge path and arguments
set "edgePath=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

set "edgeArgs=--inprivate --start-fullscreen --force-device-scale-factor=0.7 http://localhost:8000/EejoPages/LiveDisplay.html"

REM set "edgeArgs=--inprivate --kiosk http://localhost:8000/EejoPages/LiveDisplay.html --edge-kiosk-type=fullscreen --force-device-scale-factor=0.6"

REM Start Microsoft Edge in kiosk fullscreen private mode
start "" "%edgePath%" %edgeArgs%

REM Wait a few seconds to let the browser launch
timeout /t 5 /nobreak >nul

REM Run the Python file
python "%scriptDir%%pythonFile%"

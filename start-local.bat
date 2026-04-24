@echo off
setlocal

set "ROOT=%~dp0"
set "BACKEND_DIR=%ROOT%backend"
set "FRONTEND_DIR=%ROOT%frontend"
set "VENV_PY=%BACKEND_DIR%\.venv\Scripts\python.exe"
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=5173"

echo ========================================
echo MMagent local startup
echo ========================================
echo.

echo [0/4] Cleaning old local processes on ports %BACKEND_PORT% and %FRONTEND_PORT%...
for %%P in (%BACKEND_PORT% %FRONTEND_PORT%) do (
  for /f "tokens=5" %%I in ('netstat -ano ^| findstr /R /C:":%%P .*LISTENING"') do (
    echo       stopping PID %%I on port %%P
    taskkill /PID %%I /F >nul 2>nul
  )
)

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python was not found. Please install Python 3.11+ and try again.
  pause
  exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] npm was not found. Please install Node.js and try again.
  pause
  exit /b 1
)

if not exist "%VENV_PY%" (
  echo [1/4] Creating backend virtual environment...
  python -m venv "%BACKEND_DIR%\.venv"
  if errorlevel 1 (
    echo [ERROR] Failed to create backend virtual environment.
    pause
    exit /b 1
  )
) else (
  echo [1/4] Backend virtual environment already exists.
)

echo [2/4] Preparing backend dependencies...
"%VENV_PY%" -m pip --version >nul 2>nul
if errorlevel 1 (
  echo       pip is missing in .venv, bootstrapping...
  "%VENV_PY%" -m ensurepip --upgrade >nul 2>nul
)

"%VENV_PY%" -m pip --version >nul 2>nul
if errorlevel 1 (
  echo       using system pip to repair .venv...
  python -m pip --python "%VENV_PY%" install --upgrade pip
  if errorlevel 1 (
    echo [ERROR] Failed to bootstrap pip in backend virtual environment.
    pause
    exit /b 1
  )
)

"%VENV_PY%" -m pip install -r "%BACKEND_DIR%\requirements.txt"
if errorlevel 1 (
  echo [ERROR] Failed to install backend dependencies.
  pause
  exit /b 1
)

if not exist "%FRONTEND_DIR%\node_modules" (
  echo [3/4] Installing frontend dependencies...
  pushd "%FRONTEND_DIR%"
  call npm install
  if errorlevel 1 (
    popd
    echo [ERROR] Failed to install frontend dependencies.
    pause
    exit /b 1
  )
  popd
) else (
  echo [3/4] Frontend dependencies already installed.
)

echo [4/4] Starting backend and frontend...
echo.

start "MMagent Backend" /D "%BACKEND_DIR%" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port %BACKEND_PORT%"
start "MMagent Frontend" /D "%FRONTEND_DIR%" cmd /k "npm run dev -- --host 127.0.0.1 --port %FRONTEND_PORT%"

echo Backend API:  http://127.0.0.1:%BACKEND_PORT%
echo Frontend UI:  http://127.0.0.1:%FRONTEND_PORT%
echo.
echo Two new terminal windows have been opened.
echo Close those windows to stop the services.
echo.
pause

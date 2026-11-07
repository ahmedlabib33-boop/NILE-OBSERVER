@echo off
setlocal
title Nile Observer - Local Application

cls
echo.
echo ================================================================================
echo   NILE OBSERVER - LOCAL APPLICATION
echo ================================================================================
echo.
echo   Starting the Wave application in wave-repo...
echo   First run installs dependencies and builds the frontend.
echo   Later runs reuse unchanged setup and build files.
echo.
echo   Live source availability is checked after API startup.
echo   Polling and coverage depend on each configured provider.
echo.

if not exist "%~dp0wave-repo\run.bat" (
  echo   ERROR: Missing application launcher
  echo   Expected: wave-repo\run.bat
  echo.
  exit /b 2
)

echo   Launching application...
echo.
echo   Access URL: http://127.0.0.1:8000/#radar
echo   Login: local Wave account
echo   API token file: wave-repo\data\access-token
echo   APP_API_KEY overrides the token file when configured.
echo.
echo   Browser opens automatically after the API health check.
echo   Source report: wave-repo\data\startup-status.log
echo   Check current source status: run.bat -StatusOnly
echo   Prepare without starting: run.bat -SetupOnly
echo.
echo ================================================================================
echo.

call "%~dp0wave-repo\run.bat" %*
exit /b %errorlevel%

@echo off
setlocal
if not exist "%~dp0wave-repo\run.bat" (
  echo Missing application launcher: wave-repo\run.bat
  exit /b 2
)
call "%~dp0wave-repo\run.bat" %*
exit /b %errorlevel%

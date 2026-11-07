@echo off
setlocal EnableDelayedExpansion

cls
echo.
echo ================================================================================
echo   NILE OBSERVER - UNIFIED FREE RADAR SYSTEM
echo ================================================================================
echo.
echo   Starting production application...
echo   - OpenSky Network (Aircraft ADS-B)
echo   - AISDecoder (Vessel AIS)
echo   - NOAA NEXRAD (Weather Radar)
echo.
echo   System: 100%% Free, Zero Configuration, Always ON
echo   Status: Autonomous 30-second polling cycle
echo.

if not exist "%~dp0wave-repo\run.bat" (
  echo   ERROR: Missing application launcher
  echo   Expected: wave-repo\run.bat
  echo.
  exit /b 2
)

echo   ✓ Launching application...
echo.
echo   Access URL: http://127.0.0.1:8000
echo   Token: data/access-token
echo.
echo   Features:
echo   - Satellite Radar interface (unified detection)
echo   - Real-time observations
echo   - Auto-update detection (see UPDATE button)
echo   - Source diagnostics
echo   - Historical scene access
echo.
echo ================================================================================
echo.

call "%~dp0wave-repo\run.bat" %*
exit /b %errorlevel%

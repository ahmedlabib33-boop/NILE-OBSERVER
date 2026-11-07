@echo off
setlocal EnableDelayedExpansion

cls
echo.
echo ================================================================================
echo   NILE OBSERVER - UNIFIED FREE RADAR SYSTEM
echo ================================================================================
echo.
echo   GitHub: https://github.com/ahmedlabib33-boop/NILE-OBSERVER
echo   Status: PRODUCTION READY
echo.
echo   Starting autonomous unified radar system...
echo   - OpenSky Network (Aircraft ADS-B)
echo   - AISDecoder (Vessel AIS)
echo   - NOAA NEXRAD (Weather Radar)
echo.
echo   System: 100%% Free, Zero Configuration, Always ON
echo   Polling: Autonomous 30-second cycle
echo   Login: Auto-login (no token entry required)
echo.

if not exist "%~dp0wave-repo\run.bat" (
  echo   ERROR: Missing application launcher
  echo   Expected: wave-repo\run.bat
  echo.
  exit /b 2
)

echo   ✓ Launching application...
echo.
echo   ┌─ Access Information ─────────────────────────────────────┐
echo   │ URL:     http://127.0.0.1:8000                          │
echo   │ Token:   auto-fetched (data/access-token)               │
echo   │ Browser: Opens automatically on first access            │
echo   └──────────────────────────────────────────────────────────┘
echo.
echo   Features:
echo   ✓ Satellite Radar (unified detection)
echo   ✓ Real-time observations
echo   ✓ Auto-update detection (UPDATE button)
echo   ✓ Source diagnostics
echo   ✓ Historical scene access
echo   ✓ Auto-login (persistent sessions)
echo.
echo ================================================================================
echo.

call "%~dp0wave-repo\run.bat" %*
exit /b %errorlevel%

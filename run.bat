@echo off
setlocal EnableDelayedExpansion

cls
echo.
echo ================================================================================
echo   NILE OBSERVER - UNIFIED FREE RADAR SYSTEM
echo ================================================================================
echo.
echo   🛰️  Version 1.0.0 - PRODUCTION READY
echo   📍 GitHub: https://github.com/ahmedlabib33-boop/NILE-OBSERVER
echo   ✅ Status: FULLY OPERATIONAL - All Systems Ready
echo.
echo   UNIFIED DETECTION SYSTEM:
echo   ├─ ✈️  OpenSky Network (Aircraft ADS-B - Global)
echo   ├─ 🚢 AISDecoder (Vessel AIS - Maritime)
echo   └─ 🌧️  NOAA NEXRAD (Weather Radar - US+)
echo.
echo   SYSTEM CAPABILITIES:
echo   ├─ 100%% FREE infrastructure ($0/month)
echo   ├─ Zero configuration (auto-startup)
echo   ├─ Always ON (24/7 autonomous operation)
echo   ├─ 30-second polling cycle
echo   ├─ Auto-login (no token entry)
echo   ├─ UPDATE button (real-time code reloads)
echo   └─ Persistent sessions (survives restart)
echo.

if not exist "%~dp0wave-repo\run.bat" (
  echo   ❌ ERROR: Missing application launcher
  echo   Expected: wave-repo\run.bat
  echo.
  exit /b 2
)

echo   🚀 LAUNCHING APPLICATION...
echo.
echo   ┌──────────────────────────────────────────────────────────┐
echo   │  ACCESS INFORMATION                                      │
echo   │                                                          │
echo   │  URL:      http://127.0.0.1:8000                        │
echo   │  Token:    auto-fetched from data/access-token          │
echo   │  Login:    automatic (no manual entry required)         │
echo   │  Browser:  opens automatically                          │
echo   └──────────────────────────────────────────────────────────┘
echo.
echo   INTERFACE FEATURES:
echo   ✓ Satellite Radar    - Unified real-time detection
echo   ✓ Real-time Feed     - Live observation stream
echo   ✓ Interactive Map    - Location-based tracking
echo   ✓ Source Diagnostics - Health monitoring
echo   ✓ Historical Scenes  - Past observations
echo   ✓ Auto-Update        - Code reload button
echo   ✓ Auto-Login         - Persistent sessions
echo.
echo   DEPLOYMENT OPTIONS:
echo   • Local:  Run this script (you are here)
echo   • Cloud:  git clone + run.bat on Heroku/Railway/AWS
echo   • Docker: Build with included Dockerfile
echo.
echo ================================================================================
echo.

call "%~dp0wave-repo\run.bat" %*
exit /b %errorlevel%

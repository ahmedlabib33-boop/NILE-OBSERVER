param([switch]$SetupOnly, [switch]$Reinstall, [switch]$NoBrowser, [switch]$StatusOnly)
$ErrorActionPreference = 'Stop'
$appRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Set-Location $appRoot
function Invoke-Checked {
    param([scriptblock]$Command)
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "Command failed (exit $LASTEXITCODE)" }
}
function Get-InputHash([string[]]$Paths) {
    $hashes = foreach ($entry in ($Paths | Sort-Object)) {
        $stream = [IO.File]::OpenRead((Resolve-Path -LiteralPath $entry).Path)
        $hasher = [Security.Cryptography.SHA256]::Create()
        try { ([BitConverter]::ToString($hasher.ComputeHash($stream))).Replace('-', '') }
        finally { $hasher.Dispose(); $stream.Dispose() }
    }
    return $hashes -join ':'
}
function Test-CurrentServer {
    try {
        $health = Invoke-RestMethod 'http://127.0.0.1:8000/api/health' -TimeoutSec 2
        return $health.status -eq 'ok' -and $health.application -eq 'unified-free-radar' -and $health.app_root -eq $appRoot
    } catch { return $false }
}
if ($StatusOnly) {
    if (!(Test-CurrentServer)) { throw 'The Unified Free Radar application from this folder is not running on port 8000.' }
    Invoke-Checked { & .\.venv\Scripts\python.exe scripts/runtime_status.py }
    exit 0
}
if (!$SetupOnly -and !$Reinstall -and (Test-CurrentServer)) {
    Write-Host 'Unified Free Radar is already running from this folder.'
    Invoke-Checked { & .\.venv\Scripts\python.exe scripts/runtime_status.py }
    if (!$NoBrowser) { Start-Process 'http://127.0.0.1:8000/#satellite' }
    exit 0
}
if (!(Test-Path '.venv/Scripts/python.exe')) {
    Invoke-Checked { py -3.12 -m venv .venv }
}
$pythonHash = Get-InputHash @('pyproject.toml')
$pythonStamp = '.venv/setup-pyproject.sha256'
if ($Reinstall -or !(Test-Path $pythonStamp) -or (Get-Content $pythonStamp -Raw).Trim() -ne $pythonHash) {
    Write-Host 'Installing application dependencies...'
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        Invoke-Checked { uv pip install --python .venv/Scripts/python.exe -e '.[vision,sar,test]' }
    } else {
        Invoke-Checked { .\.venv\Scripts\python.exe -m ensurepip --upgrade }
        Invoke-Checked { .\.venv\Scripts\python.exe -m pip install -e '.[vision,sar,test]' }
    }
    Set-Content $pythonStamp $pythonHash
}
if (!(Test-Path '.env')) { Copy-Item '.env.example' '.env' }
New-Item -ItemType Directory -Force 'data' | Out-Null
$npmHash = Get-InputHash @('frontend/package.json', 'frontend/package-lock.json')
$npmStamp = 'frontend/node_modules/.nile-setup.sha256'
if ($Reinstall -or !(Test-Path $npmStamp) -or (Get-Content $npmStamp -Raw).Trim() -ne $npmHash) {
    Invoke-Checked { npm.cmd --prefix frontend ci --no-audit --no-fund }
    Set-Content $npmStamp $npmHash
}
$buildPaths = @(Get-ChildItem 'frontend/src', 'frontend/public' -Recurse -File -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
$buildPaths += @(Get-ChildItem 'frontend' -File | Where-Object { $_.Name -match '^(package.*\.json|index\.html|tsconfig.*\.json|vite\.config\..*)$' } | Select-Object -ExpandProperty FullName)
$buildHash = Get-InputHash $buildPaths
$buildStamp = 'frontend/node_modules/.nile-build.sha256'
if ($Reinstall -or !(Test-Path 'frontend/dist/index.html') -or !(Test-Path $buildStamp) -or (Get-Content $buildStamp -Raw).Trim() -ne $buildHash) {
    Invoke-Checked { npm.cmd --prefix frontend run build }
    Set-Content $buildStamp $buildHash
}
Invoke-Checked { .\.venv\Scripts\alembic.exe upgrade head }
if ($SetupOnly) { Write-Host 'Unified Free Radar setup complete.'; exit 0 }
if (Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue) {
    throw 'Port 8000 belongs to another app. Close that app before launching Unified Free Radar.'
}
Write-Host 'Starting Unified Free Radar: http://127.0.0.1:8000/#satellite'
Write-Host "Token file: $appRoot\data\access-token"
$server = Start-Process -FilePath (Join-Path $appRoot '.venv/Scripts/python.exe') -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000', '--ws-max-size', '262144') -WorkingDirectory $appRoot -WindowStyle Hidden -RedirectStandardOutput 'data/server.stdout.log' -RedirectStandardError 'data/server.stderr.log' -PassThru
try {
    $deadline = [DateTime]::UtcNow.AddSeconds(90)
    while (!(Test-CurrentServer)) {
        if ($server.HasExited) { throw 'Server startup failed. See nile-observer/data/server.stderr.log.' }
        if ([DateTime]::UtcNow -gt $deadline) { throw 'Server did not become healthy within 90 seconds.' }
        Start-Sleep -Milliseconds 500
    }
    Invoke-Checked { .\.venv\Scripts\python.exe scripts/runtime_status.py }
    if (!$NoBrowser) { Start-Process 'http://127.0.0.1:8000/#satellite' }
    Write-Host 'Unified Free Radar is running. Close this launcher or press Ctrl+C to stop.'
    Wait-Process -Id $server.Id
    if ($server.ExitCode -and $server.ExitCode -ne 0) { throw "Server exited with code $($server.ExitCode)." }
} finally {
    if (!$server.HasExited) { Stop-Process -Id $server.Id -ErrorAction SilentlyContinue }
}

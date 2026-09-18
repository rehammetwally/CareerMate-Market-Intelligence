# CareerMate Market Intelligence — Service Manager
param ([string]$Command = "help")

$RootDir    = $PSScriptRoot
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$VenvPython = "d:\Projects\DEPI-Career-Advisor\.venv\Scripts\python.exe"

function Show-Help {
    Write-Host ""
    Write-Host "  CareerMate Market Intelligence" -ForegroundColor Cyan
    Write-Host "  ==============================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Usage: .\run.ps1 [command]" -ForegroundColor White
    Write-Host ""
    Write-Host "  Commands:" -ForegroundColor Yellow
    Write-Host "    install    Install all dependencies (npm + pip)"
    Write-Host "    test       Run full backend test suite"
    Write-Host "    backend    Start FastAPI on port 8001"
    Write-Host "    frontend   Start React Dashboard"
    Write-Host "    all        Start both backend and frontend"
    Write-Host "    help       Show this message"
    Write-Host ""
}

switch ($Command.ToLower()) {

    "install" {
        Write-Host "[1/2] Installing Python backend dependencies..." -ForegroundColor Cyan
        $env:PYTHONPATH = "$RootDir;$BackendDir"
        & $VenvPython -m pip install -r "$BackendDir\requirements.txt" --quiet
        Write-Host "      Backend deps installed" -ForegroundColor Green

        Write-Host "[2/2] Installing Node frontend dependencies..." -ForegroundColor Cyan
        Push-Location $FrontendDir
        npm install --silent
        Pop-Location
        Write-Host "      Frontend deps installed" -ForegroundColor Green
        Write-Host ""
        Write-Host "  All done! Run: .\run.ps1 all" -ForegroundColor Green
    }

    "test" {
        Write-Host "Running backend tests..." -ForegroundColor Green
        $env:PYTHONPATH = "$RootDir;$BackendDir"
        & $VenvPython -m pytest "$BackendDir\tests" -v
    }

    "backend" {
        Write-Host ""
        Write-Host "  Starting Market Intelligence API" -ForegroundColor Cyan
        Write-Host "  Port : 8001" -ForegroundColor White
        Write-Host "  Docs : http://localhost:8001/docs" -ForegroundColor White
        Write-Host ""
        $env:PYTHONPATH = "$RootDir;$BackendDir"
        & $VenvPython -m uvicorn app:app --app-dir $BackendDir --host 0.0.0.0 --port 8001 --reload
    }

    "frontend" {
        Write-Host ""
        Write-Host "  Starting Market Intelligence Dashboard" -ForegroundColor Cyan
        Write-Host "  URL : http://localhost:3001" -ForegroundColor White
        Write-Host ""
        $env:BROWSER = "none"
        $env:PORT = "3001"
        Push-Location $FrontendDir
        npm start
        Pop-Location
    }

    "all" {
        Write-Host ""
        Write-Host "  Launching full stack..." -ForegroundColor Cyan

        # Backend in new window
        $backendCmd = "cd '$RootDir'; `$env:PYTHONPATH='$RootDir;$BackendDir'; & '$VenvPython' -m uvicorn app:app --app-dir '$BackendDir' --host 0.0.0.0 --port 8001 --reload"
        Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

        Start-Sleep -Seconds 2

        Write-Host "  Backend started (port 8001)" -ForegroundColor Green
        Write-Host "  Starting frontend (port 3001)..." -ForegroundColor Cyan

        $env:BROWSER = "none"
        $env:PORT = "3001"
        Push-Location $FrontendDir
        npm start
        Pop-Location
    }

    default { Show-Help }
}

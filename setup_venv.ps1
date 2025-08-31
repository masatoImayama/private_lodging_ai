Write-Host "Creating Python virtual environment..." -ForegroundColor Green

# Try different Python commands
$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
} else {
    Write-Host "Python not found. Please install Python first." -ForegroundColor Red
    exit 1
}

Write-Host "Using Python command: $pythonCmd" -ForegroundColor Yellow
& $pythonCmd -m venv venv

if (Test-Path ".\venv\Scripts\Activate.ps1") {
    Write-Host "`nActivating virtual environment..." -ForegroundColor Green
    & .\venv\Scripts\Activate.ps1
    
    Write-Host "`nInstalling dependencies..." -ForegroundColor Green
    & .\venv\Scripts\python.exe -m pip install --upgrade pip
    & .\venv\Scripts\pip.exe install -r requirements.txt
} else {
    Write-Host "Virtual environment creation failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`nVirtual environment setup complete!" -ForegroundColor Green
Write-Host "To activate the environment, run: .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
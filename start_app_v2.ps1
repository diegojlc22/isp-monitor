$env:PYTHONPATH = "C:\Users\DiegoLima\.gemini\antigravity\scratch\isp_monitor"

# Start Backend
Write-Host "Starting Backend..."
Start-Process -NoNewWindow -FilePath "python" -ArgumentList "-m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000"

# Start Frontend
Write-Host "Starting Frontend..."
Set-Location frontend
Start-Process -NoNewWindow -FilePath "npm" -ArgumentList "run dev -- --host"

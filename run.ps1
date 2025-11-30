Write-Host "--- AGENT 007 START ---" -ForegroundColor Green

# 1. Wybierz komende (python lub py)
$p = "python"; if (!(Get-Command $p -EA 0)) { $p = "py" }

# 2. Sprawdz czy dziala
try { & $p --version } catch { 
    Write-Host "Nie znaleziono Pythona! Zrestartuj komputer." -ForegroundColor Red; exit 
}

# 3. Uruchom
Write-Host "Uzywam: $p"
& $p setup.py
& $p main.py

Read-Host "Nacisnij Enter aby zamknac..."
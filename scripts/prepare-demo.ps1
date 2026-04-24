# Refresh all snapshots
$API_URL = "http://localhost:8000"

Write-Host "Refreshing reference data..."
Invoke-RestMethod -Method Post -Uri "$API_URL/ingest/reference/load"

Write-Host "Refreshing FX (USDMYR)..."
Invoke-RestMethod -Method Post -Uri "$API_URL/ingest/market/fx" -ContentType "application/json" -Body '{"pair":"USDMYR"}'

Write-Host "Refreshing FX (CNYMYR)..."
Invoke-RestMethod -Method Post -Uri "$API_URL/ingest/market/fx" -ContentType "application/json" -Body '{"pair":"CNYMYR"}'

Write-Host "Refreshing FX (THBMYR)..."
Invoke-RestMethod -Method Post -Uri "$API_URL/ingest/market/fx" -ContentType "application/json" -Body '{"pair":"THBMYR"}'

Write-Host "Refreshing Energy (BZ=F)..."
Invoke-RestMethod -Method Post -Uri "$API_URL/ingest/market/energy" -ContentType "application/json" -Body '{"symbol":"BZ=F"}'

Write-Host "Refreshing Holidays..."
Invoke-RestMethod -Method Post -Uri "$API_URL/ingest/holidays"

Write-Host "All snapshots refreshed. Ready for demo."

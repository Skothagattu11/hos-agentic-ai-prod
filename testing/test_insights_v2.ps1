# PowerShell test script for Insights V2 API
# Usage: .\testing\test_insights_v2.ps1

$BaseURL = "http://localhost:8002"
$ApiKey = "hosa_flutter_app_2024"
$UserID = "6241b25a-c2de-49fe-9476-1ada99ffe5ca"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Insights V2 - PowerShell Tests" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Health Check
Write-Host "Test 1: Health Check" -ForegroundColor Yellow
Write-Host "--------------------" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BaseURL/api/v2/insights/health" -Method Get
    Write-Host "✅ Success" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "❌ Failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 2: Generate Insights - Foundation Builder
Write-Host "Test 2: Generate Insights (Foundation Builder)" -ForegroundColor Yellow
Write-Host "----------------------------------------------" -ForegroundColor Yellow
try {
    $headers = @{
        "X-API-Key" = $ApiKey
        "Content-Type" = "application/json"
    }
    $body = @{
        archetype = "Foundation Builder"
        timeframe_days = 3
        force_refresh = $false
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$BaseURL/api/v2/insights/$UserID/generate" `
        -Method Post `
        -Headers $headers `
        -Body $body

    Write-Host "✅ Success" -ForegroundColor Green
    Write-Host "User ID: $($response.user_id)"
    Write-Host "Status: $($response.status)"
    Write-Host "Insights Count: $($response.metadata.insights_count)"
    Write-Host "Generation Time: $($response.metadata.generation_time_ms)ms"
    Write-Host "Model: $($response.metadata.model_used)"
    Write-Host ""
    Write-Host "Insights:" -ForegroundColor Cyan
    foreach ($insight in $response.insights) {
        Write-Host "  - [$($insight.priority)] $($insight.title)" -ForegroundColor White
        Write-Host "    Category: $($insight.category)"
        Write-Host "    Content: $($insight.content)"
        Write-Host "    Recommendation: $($insight.recommendation)"
        Write-Host ""
    }
} catch {
    Write-Host "❌ Failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 3: Generate Insights - Peak Performer
Write-Host "Test 3: Generate Insights (Peak Performer)" -ForegroundColor Yellow
Write-Host "------------------------------------------" -ForegroundColor Yellow
try {
    $headers = @{
        "X-API-Key" = $ApiKey
        "Content-Type" = "application/json"
    }
    $body = @{
        archetype = "Peak Performer"
        timeframe_days = 7
        force_refresh = $true
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$BaseURL/api/v2/insights/$UserID/generate" `
        -Method Post `
        -Headers $headers `
        -Body $body

    Write-Host "✅ Success" -ForegroundColor Green
    Write-Host "Archetype: $($response.metadata.archetype)"
    Write-Host "Timeframe: $($response.metadata.timeframe_days) days"
    Write-Host "Insights Count: $($response.metadata.insights_count)"
} catch {
    Write-Host "❌ Failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 4: Invalid API Key (should fail)
Write-Host "Test 4: Invalid API Key (Should Fail with 401)" -ForegroundColor Yellow
Write-Host "-----------------------------------------------" -ForegroundColor Yellow
try {
    $headers = @{
        "X-API-Key" = "invalid_key"
        "Content-Type" = "application/json"
    }
    $body = @{
        archetype = "Foundation Builder"
        timeframe_days = 3
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$BaseURL/api/v2/insights/$UserID/generate" `
        -Method Post `
        -Headers $headers `
        -Body $body

    Write-Host "❌ Should have failed but didn't" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 401) {
        Write-Host "✅ Correctly rejected with 401" -ForegroundColor Green
    } else {
        Write-Host "❌ Wrong status code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    }
}
Write-Host ""

# Test 5: Get Latest Insights (not yet implemented)
Write-Host "Test 5: Get Latest Insights (Not Yet Implemented)" -ForegroundColor Yellow
Write-Host "-------------------------------------------------" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BaseURL/api/v2/insights/$UserID/latest" -Method Get
    Write-Host "Status: $($response.status)"
    Write-Host "Message: $($response.message)"
} catch {
    Write-Host "❌ Failed: $_" -ForegroundColor Red
}
Write-Host ""

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Tests Complete" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

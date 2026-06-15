# 导出 OpenAPI Schema 到 docs/openapi.yaml
param(
    [string]$Output = "..\docs\openapi.yaml"
)

$backend = Join-Path $PSScriptRoot "..\backend"
Push-Location $backend
try {
    python manage.py spectacular --file $Output --validate 2>&1
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "OpenAPI 已导出: $Output"
} finally {
    Pop-Location
}

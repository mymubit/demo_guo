# Windows：确保 docker 在 PATH 中并启动 Postgres + Redis
$dockerBin = "C:\Program Files\Docker\Docker\resources\bin"
if (Test-Path $dockerBin) {
    $env:Path = "$dockerBin;$env:Path"
}

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "Starting Postgres + Redis ..."
docker compose up db redis -d
if ($LASTEXITCODE -ne 0) {
    Write-Error "docker compose failed. Try: Docker Desktop -> Troubleshoot -> Restart"
    exit $LASTEXITCODE
}

docker compose ps
Write-Host "Done. DB=localhost:5432  Redis=127.0.0.1:6379 (password: redis_password_2024)"

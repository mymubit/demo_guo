# 生产部署前环境变量检查
param()

$required = @("SECRET_KEY", "API_SIGN_SECRET", "SKILL_ENCRYPT_KEY")
$missing = @()
foreach ($name in $required) {
    $val = [Environment]::GetEnvironmentVariable($name)
    if (-not $val) { $missing += $name; continue }
    if ($val -match "insecure|change-me|change_me|django-insecure") {
        Write-Error "$name 仍为占位符，请设置安全值。"
        exit 1
    }
}
if ($missing.Count -gt 0) {
    Write-Error "缺少必填环境变量: $($missing -join ', ')"
    exit 1
}
Write-Host "部署环境变量检查通过。"

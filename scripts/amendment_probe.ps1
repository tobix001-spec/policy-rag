# Isolate which v2 change affects amendment questions (15 cases, no judge, ~1 min per variant).
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
$env:UV_PROJECT_ENVIRONMENT = "$env:USERPROFILE\.venvs\policy-rag"
$env:PYTHONUNBUFFERED = "1"; $env:PYTHONWARNINGS = "ignore"; $env:TRANSFORMERS_VERBOSITY = "error"
$log = Join-Path $root "logs\pipeline.log"
$variants = [ordered]@{
    "probe-amend-v2"                  = @()
    "probe-amend-no-amendments-first" = @("--set", "amendments_first=false")
    "probe-amend-no-entity-filter"    = @("--set", "entity_filter=false")
}
"[{0:HH:mm:ss}] ===== amendment probe: 3 variants x 15 cases =====" -f (Get-Date) | Out-File -Encoding utf8 $log
foreach ($name in $variants.Keys) {
    "[{0:HH:mm:ss}] ===== {1} {2} =====" -f (Get-Date), $name, ($variants[$name] -join " ") | Out-File -Append -Encoding utf8 $log
    & uv run --no-sync python -m policyrag.evaluation.evaluate --name $name --types amendment --no-judge @($variants[$name]) 2>$null |
        ForEach-Object { $_ | Out-File -Append -Encoding utf8 $log }
}
"[{0:HH:mm:ss}] ===== probe done =====" -f (Get-Date) | Out-File -Append -Encoding utf8 $log

# Run one evaluation with live output in logs/pipeline.log.
#   .\scripts\run_eval.ps1 -Name v2 -EvalArgs "--gate"
#   .\scripts\run_eval.ps1 -Name quick -EvalArgs "--limit","20","--no-judge"
# Watch it:  Get-Content logs\pipeline.log -Wait
param([Parameter(Mandatory)][string]$Name, [string[]]$EvalArgs = @("--gate"))

$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
$env:UV_PROJECT_ENVIRONMENT = "$env:USERPROFILE\.venvs\policy-rag"
$env:PYTHONUNBUFFERED = "1"; $env:PYTHONWARNINGS = "ignore"; $env:TRANSFORMERS_VERBOSITY = "error"
New-Item -ItemType Directory -Force logs | Out-Null
$log = Join-Path $root "logs\pipeline.log"
"[{0:HH:mm:ss}] ===== eval '{1}' {2} =====" -f (Get-Date), $Name, ($EvalArgs -join " ") | Out-File -Encoding utf8 $log
& uv run --no-sync python -m policyrag.evaluation.evaluate --name $Name @EvalArgs 2>$null |
    ForEach-Object { $_ | Out-File -Append -Encoding utf8 $log }
$code = $LASTEXITCODE
"[{0:HH:mm:ss}] ===== eval '{1}' finished (exit {2}) =====" -f (Get-Date), $Name, $code | Out-File -Append -Encoding utf8 $log
exit $code

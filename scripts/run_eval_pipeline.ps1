# Full evaluation pipeline: v0 baseline -> v1 (gated vs v0) -> ablations (gated vs accepted baseline).
# Live output goes to logs/pipeline.log; watch it with:  Get-Content logs\pipeline.log -Wait
param([int]$AblationLimit = 90)

$ErrorActionPreference = "Continue"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
$env:UV_PROJECT_ENVIRONMENT = "$env:USERPROFILE\.venvs\policy-rag"
$env:PYTHONUNBUFFERED = "1"
$env:PYTHONWARNINGS = "ignore"
$env:TRANSFORMERS_VERBOSITY = "error"
$env:HF_HUB_DISABLE_PROGRESS_BARS = "1"
New-Item -ItemType Directory -Force logs | Out-Null
$log = Join-Path $root "logs\pipeline.log"

function Say($msg) { $line = "[{0:HH:mm:ss}] {1}" -f (Get-Date), $msg; $line | Out-File -Append -Encoding utf8 $log }
function Run($title, [string[]]$evalArgs) {
    Say "===== $title ====="
    & uv run --no-sync python -m @evalArgs 2>$null | ForEach-Object { $_ | Out-File -Append -Encoding utf8 $log }
    $code = $LASTEXITCODE
    Say "===== $title finished (exit $code) ====="
    return $code
}

"" | Out-File -Encoding utf8 $log
Say "PolicyRAG eval pipeline started"

# v0 = the system before the eval-driven fixes (those fixes are config flags, so v0 is reproducible)
$null = Run "v0 baseline (180 cases, judge on, fixes OFF)" @("policyrag.evaluation.evaluate", "--name", "v0-baseline",
    "--set", "decompose_multi_entity=false", "--set", "grounding_check=false", "--set", "context_routing=false",
    "--update-baseline")

# v1 = current system, gated against v0
$v1 = Run "v1 (180 cases, judge on, fixes ON, gate vs v0)" @("policyrag.evaluation.evaluate", "--name", "v1", "--gate")
if ($v1 -eq 0) {
    Copy-Item reports\baseline.json reports\baseline_v0.json -Force
    & uv run --no-sync python -c "import json; r=json.load(open('reports/eval_v1.json',encoding='utf-8')); json.dump({'from':'eval_v1.json','summary':r['summary']}, open('reports/baseline.json','w',encoding='utf-8'), indent=2)"
    Say "v1 passed the gate -> promoted to reports/baseline.json (v0 kept as baseline_v0.json)"
} else {
    Say "v1 FAILED the gate -> baseline stays v0; inspect reports/eval_v1.md"
}

$null = Run "ablations ($AblationLimit-case subset, gate vs baseline)" @("policyrag.evaluation.ablations", "--limit", "$AblationLimit")
Say "PIPELINE DONE"

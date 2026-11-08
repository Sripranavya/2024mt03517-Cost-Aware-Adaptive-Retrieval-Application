<#
.SYNOPSIS
  Start the backend and frontend against LIVE AWS (Bedrock + OpenSearch + DynamoDB).

.DESCRIPTION
  1. In CloudShell run:  aws configure export-credentials --format powershell
  2. Select and COPY the three printed lines ($Env:AWS_ACCESS_KEY_ID=..., etc.).
  3. Run this script in a normal (non-admin) PowerShell window.

  The keys are read from the clipboard, kept only in this process and the two child
  windows, never written to a file or printed, and the clipboard is cleared afterwards.
  Sign-in uses DEMO_LOGIN (local password); everything else runs on AWS.

  Usage:  .\scripts\start_live_ui.ps1 [-Index hp-test|ms-test]
#>
param([string]$Index = "hp-test")

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"

$clip = (Get-Clipboard -Raw)
$found = @{}
foreach ($m in [regex]::Matches($clip, '(?im)\$?Env:(AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|AWS_SESSION_TOKEN)\s*=\s*["'']?([^"''\r\n]+)["'']?')) {
    $found[$m.Groups[1].Value.ToUpper()] = $m.Groups[2].Value.Trim()
}
foreach ($k in "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN") {
    if (-not $found.ContainsKey($k)) {
        throw "Clipboard has no $k. In CloudShell run: aws configure export-credentials --format powershell, copy the 3 lines, then rerun."
    }
    Set-Item -Path "Env:$k" -Value $found[$k]
}

$env:AWS_REGION = "ap-southeast-2"
$env:AWS_DEFAULT_REGION = "ap-southeast-2"
$account = & $py -c "import boto3; print(boto3.client('sts').get_caller_identity()['Account'])"
if ($account -ne "535635599719") { throw "Credentials check failed (got '$account')." }
Write-Host "Credentials OK for account $account" -ForegroundColor Green

$env:APP_ENV = "local"
$env:USE_LOCAL_MOCKS = "false"
$env:DEMO_LOGIN = "true"
$env:OPENSEARCH_ENDPOINT = "https://search-agentic-rag-vectors-6pugyoalemctez7us5xgrlq4yu.ap-southeast-2.es.amazonaws.com"
$env:OPENSEARCH_INDEX = $Index
$env:DYNAMODB_TABLE_NAME = "agentic-rag-state"
$env:S3_BUCKET_NAME = "pomdp-rag-535635599719-syd"
$env:BEDROCK_MODEL_ID = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
$env:BEDROCK_EMBED_MODEL_ID = "amazon.titan-embed-text-v2:0"
$env:BEDROCK_EMBED_DIMENSION = "256"
$env:LIVE_SOURCES = "false"; $env:SEED_SAMPLE_CORPUS = "false"; $env:SINGLE_SOURCE_CORPUS = "true"
$env:ITERATIVE_RETRIEVAL = "true"; $env:LLM_ACTIONS = "true"; $env:SHORT_ANSWERS = "true"
$env:ANSWER_DOCS = "8"; $env:REWARD_COST_WEIGHT = "40"; $env:RETRIEVAL_COST_USD = "0.0003"
$env:MAX_BUDGET_USD = "5"
$env:PRICE_PER_1K_INPUT_TOKENS = "0.001"; $env:PRICE_PER_1K_OUTPUT_TOKENS = "0.005"

$demoPassword = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 14 | ForEach-Object { [char]$_ })
$env:LOCAL_DEMO_PASSWORD = $demoPassword
$env:LOCAL_JWT_SECRET = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 40 | ForEach-Object { [char]$_ })

$backendCmd = "Set-Location '$root\backend'; & '$py' -m uvicorn app.main:app --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd
$frontendCmd = "Set-Location '$root\frontend'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Set-Clipboard -Value $demoPassword
# Temp handoff for local automated tests (read then deleted by the test runner).
Set-Content -Path (Join-Path $env:TEMP "pomdp_live_pw.txt") -Value $demoPassword -NoNewline
Write-Host ""
Write-Host "Backend  : http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Frontend : http://localhost:5173" -ForegroundColor Cyan
Write-Host "Index    : $Index (live OpenSearch)" -ForegroundColor Cyan
Write-Host "Sign in  : username 'demo' (any name works)" -ForegroundColor Yellow
Write-Host "Password : $demoPassword   (also copied to the clipboard)" -ForegroundColor Yellow
Write-Host "Keys expire after a while; rerun this script with fresh keys if calls fail." -ForegroundColor Yellow
Start-Sleep -Seconds 8
Start-Process "http://localhost:5173"

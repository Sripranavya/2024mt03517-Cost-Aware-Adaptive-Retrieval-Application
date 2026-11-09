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

  Usage:  .\scripts\start_live_ui.ps1 [-Index hp-test|ms-test] [-Password <fixed demo password>]
#>
param([string]$Index = "hp-test", [string]$Password = "")

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"

# Old servers keep their (expired) keys and block the ports, so refuse to start over them.
foreach ($port in 8000, 5173) {
    if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
        throw "Port $port is already in use. Close the old backend and frontend windows first."
    }
}

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

# The export also prints when these keys expire; show the time left so a short-lived set is
# noticed before the demo instead of halfway through it.
$exp = [regex]::Match($clip, '(?im)AWS_CREDENTIAL_EXPIRATION\s*=\s*["'']?([^"''\r\n]+)')
if ($exp.Success) {
    $left = [datetimeoffset]::Parse($exp.Groups[1].Value.Trim()) - [datetimeoffset]::UtcNow
    $mins = [math]::Floor($left.TotalMinutes)
    if ($mins -le 0) { throw "These keys have already expired. Run the export again in CloudShell." }
    $color = if ($mins -lt 20) { "Red" } else { "Green" }
    Write-Host "Keys valid for about $mins more minutes." -ForegroundColor $color
    if ($mins -lt 20) {
        Write-Host "That is short. Sign out and back in to the AWS console, reopen CloudShell, and export again for a fresh set." -ForegroundColor Yellow
    }
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

$demoPassword = if ($Password) { $Password } else { -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 14 | ForEach-Object { [char]$_ }) }
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

# Open the browser only once the servers really answer; a fixed sleep opened an empty tab
# whenever a server was slow or failed to start.
function Wait-Http([string]$Url, [int]$Seconds) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
            return [int]$r.StatusCode
        } catch {
            if ($_.Exception.Response) { return [int]$_.Exception.Response.StatusCode }
        }
        Start-Sleep -Seconds 2
    }
    return 0
}

Write-Host ""
Write-Host "Waiting for the servers..." -ForegroundColor Gray
$feStatus = Wait-Http "http://localhost:5173" 60
$beStatus = Wait-Http "http://localhost:8000/api/v1/health" 60
if ($feStatus -eq 200) {
    Write-Host "Frontend is up." -ForegroundColor Green
} else {
    Write-Host "Frontend did not start within 60 s. Check the frontend window for the error (a port may be busy or 'npm install' may be needed). Browser NOT opened." -ForegroundColor Red
}
if ($beStatus -eq 200) {
    Write-Host "Backend is up and AWS answers." -ForegroundColor Green
} elseif ($beStatus -eq 500) {
    Write-Host "Backend is up but AWS rejected it (500): the keys are probably expired. Export fresh keys and rerun." -ForegroundColor Red
} else {
    Write-Host "Backend did not answer within 60 s. Check the backend window for the error." -ForegroundColor Red
}
if ($feStatus -eq 200) { Start-Process "http://localhost:5173" }

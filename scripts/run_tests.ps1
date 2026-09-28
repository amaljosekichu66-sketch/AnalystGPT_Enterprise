<#
.SYNOPSIS
    Run the AnalystGPT Enterprise test suite and capture a readable UTF-8 log.

.DESCRIPTION
    Replaces the ad-hoc capture commands that produced `full_pytest_output.md`
    and `FULL_TEST_OUTPUT.md`. Those had three problems this script fixes:

      1. `>` and `Tee-Object` default to UTF-16LE in Windows PowerShell, which
         made the logs unreadable to grep, git diff and editor search.
      2. `2>&1` on a native executable wraps stderr lines in PowerShell
         ErrorRecords, so a harmless Streamlit stderr warning appeared at the
         top of the log as a NativeCommandError block that looked like a crash.
      3. `-s` disabled pytest's output capture, interleaving every application
         log line into the report and inflating it to ~2 MB.

.PARAMETER Output
    Destination log file. Default: test-results/pytest-<timestamp>.md

.PARAMETER Integration
    Also run tests marked `integration` (live Ollama / REST API). These are
    deselected by default because they depend on external services.

.PARAMETER Verbose_
    Use -v instead of -q, so each test node id appears in the log.

.EXAMPLE
    .\scripts\run_tests.ps1
    .\scripts\run_tests.ps1 -Integration
    .\scripts\run_tests.ps1 -Output logs\nightly.md -Verbose_
#>

[CmdletBinding()]
param(
    [string]$Output,
    [switch]$Integration,
    [switch]$Verbose_
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (-not $Output) {
    $stamp  = Get-Date -Format 'yyyyMMdd-HHmmss'
    $Output = Join-Path 'test-results' "pytest-$stamp.md"
}

$outputDir = Split-Path -Parent $Output
if ($outputDir -and -not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

$python = Join-Path $repoRoot 'venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    $python = 'python'
}

# Note: no -s. Capture stays on, so application logging only appears for
# failing tests instead of for all 535.
# 35 files contain characters outside cp1252 (currency symbols in the
# classifier regex, emoji in the Streamlit components, box-drawing in a
# docstring diagram). Without UTF-8 mode, any tool that reads them using the
# Windows locale encoding fails on them. Note that PYTHONIOENCODING is NOT
# sufficient - it only affects stdio, not the locale encoding.
$env:PYTHONUTF8 = '1'

$pytestArgs = @('-m', 'pytest')
$pytestArgs += if ($Verbose_) { '-v' } else { '-q' }
if ($Integration) {
    $pytestArgs += @('-m', 'integration or not integration')
}

Write-Host "Running: $python $($pytestArgs -join ' ')"
Write-Host "Log:     $Output"

# stderr is redirected at the process level rather than with PowerShell's
# `2>&1`, which avoids the NativeCommandError wrapping entirely.
$stderrFile = [System.IO.Path]::GetTempFileName()
try {
    & $python @pytestArgs 2> $stderrFile | Tee-Object -Variable captured | Out-Host
    $exitCode = $LASTEXITCODE

    $lines = @()
    $lines += "# Pytest Run - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    $lines += ''
    $lines += '```text'
    $lines += $captured
    $lines += '```'

    $stderrText = Get-Content $stderrFile -Raw -ErrorAction SilentlyContinue
    if ($stderrText -and $stderrText.Trim()) {
        $lines += ''
        $lines += '## stderr'
        $lines += ''
        $lines += '```text'
        $lines += $stderrText.TrimEnd()
        $lines += '```'
    }

    # -Encoding utf8 is the whole point: the log stays greppable.
    $lines | Out-File -FilePath $Output -Encoding utf8

    Write-Host ''
    Write-Host "Exit code: $exitCode"
    Write-Host "Saved UTF-8 log to: $Output"
    exit $exitCode
}
finally {
    Remove-Item $stderrFile -ErrorAction SilentlyContinue
}

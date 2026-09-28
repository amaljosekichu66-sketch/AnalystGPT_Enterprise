<#
.SYNOPSIS
    Run isort and black over the repository in UTF-8 mode.

.DESCRIPTION
    Wraps the formatters so they cannot silently skip files on Windows.

    35 files in this repository legitimately contain characters outside
    cp1252 - the currency symbols in `SemanticClassifier`'s regex, emoji in the
    Streamlit components, box-drawing characters in a docstring diagram. On a
    Windows console, Python's locale encoding is cp1252, and isort then fails
    to read those files:

        UserWarning: Unable to parse file tests/integration/test_ai_pipeline.py
        due to 'charmap' codec can't encode characters in position 4-6

    It reports that as a warning and moves on, so the file is never checked
    while the run still exits 0 - a file can drift out of style and the gate
    stays green.

    `PYTHONIOENCODING` does NOT fix this: it only affects stdio, not the
    locale encoding isort reads files with. `PYTHONUTF8=1` (Python UTF-8 mode)
    does, and is what this script sets.

.PARAMETER Check
    Verify only; do not rewrite files. This is the CI mode.

.EXAMPLE
    .\scripts\lint.ps1
    .\scripts\lint.ps1 -Check
#>

[CmdletBinding()]
param(
    [switch]$Check
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$python = Join-Path $repoRoot 'venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    $python = 'python'
}

# The whole point of this script.
$env:PYTHONUTF8 = '1'

$targets = @('src', 'tests')
$failed = $false

if ($Check) {
    Write-Host 'Checking import order (isort --check-only)...'
    & $python -m isort --check-only @targets
    if ($LASTEXITCODE -ne 0) { $failed = $true }

    Write-Host 'Checking formatting (black --check)...'
    & $python -m black --check @targets
    if ($LASTEXITCODE -ne 0) { $failed = $true }
}
else {
    Write-Host 'Sorting imports (isort)...'
    & $python -m isort @targets
    if ($LASTEXITCODE -ne 0) { $failed = $true }

    Write-Host 'Formatting (black)...'
    & $python -m black @targets
    if ($LASTEXITCODE -ne 0) { $failed = $true }
}

Write-Host ''
if ($failed) {
    Write-Host 'Lint FAILED.'
    exit 1
}

Write-Host 'Lint OK.'
exit 0

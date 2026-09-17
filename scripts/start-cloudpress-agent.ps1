[CmdletBinding()]
param(
    [string]$Origin = "https://auth-free-test-20260915.pages.dev",
    [ValidateRange(1, 300)]
    [int]$IntervalSeconds = 5,
    [SecureString]$RecoverySigningKey
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$companion = Join-Path $PSScriptRoot "start-cloudpress-companion.ps1"
$runner = Join-Path $PSScriptRoot "run_cloudpress_agent.py"

if (-not (Test-Path -LiteralPath $companion) -or -not (Test-Path -LiteralPath $runner)) {
    throw "No se encontró el companion o runner CloudPress."
}

# The runner has no bearer/token argument: it obtains only the local channel
# from the OS keyring and the companion remains the authorization boundary.
$runnerProcess = Start-Process -FilePath python -ArgumentList @($runner, "--origin", $Origin, "--interval", $IntervalSeconds) -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru
try {
    Write-Host "Runner CloudPress iniciado (PID $($runnerProcess.Id)). El companion se mantiene en primer plano para A2F."
    & $companion -Origin $Origin -RecoverySigningKey $RecoverySigningKey
}
finally {
    if ($runnerProcess -and -not $runnerProcess.HasExited) {
        Stop-Process -Id $runnerProcess.Id -ErrorAction SilentlyContinue
    }
}

[CmdletBinding()]
param(
    [string]$Origin = "https://auth-free-test-20260915.pages.dev",
    [SecureString]$RecoverySigningKey
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$broker = Join-Path $projectRoot "examples\cloudpress_loopback_broker.py"

function Test-ExactHttpsOrigin([string]$Value) {
    try { $uri = [Uri]$Value } catch { return $false }
    return $uri.Scheme -eq "https" -and
        [string]::IsNullOrEmpty($uri.UserInfo) -and
        $uri.AbsolutePath -eq "/" -and
        [string]::IsNullOrEmpty($uri.Query) -and
        [string]::IsNullOrEmpty($uri.Fragment) -and
        $uri.GetComponents([UriComponents]::SchemeAndServer, [UriFormat]::UriEscaped) -eq $Value
}

if (-not (Test-Path -LiteralPath $broker)) { throw "No se encontró el companion: $broker" }
if (-not (Test-ExactHttpsOrigin $Origin)) { throw "Origin debe ser un origen HTTPS exacto, sin ruta, query, fragmento ni credenciales." }
$keyPointer = [IntPtr]::Zero
try {
    if ($null -ne $RecoverySigningKey) {
        $keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($RecoverySigningKey)
        $plainKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer)
        if ([string]::IsNullOrWhiteSpace($plainKey) -or $plainKey.Length -lt 32) {
            throw "LSFA_RECOVERY_SIGNING_KEY debe tener al menos 32 caracteres. El companion no se inició."
        }
        $env:CLOUDPRESS_LSFA_RECOVERY_SIGNING_KEY = $plainKey
    } else {
        Write-Host "Usando, si existe, la clave de recuperación guardada en Windows Vault."
    }
    Write-Host "Iniciando companion LSFA para $Origin. Presiona Ctrl+C para detenerlo."
    & python $broker --origin $Origin --verifier src.lsfa.cloudpress_verifier:verify
}
finally {
    Remove-Item Env:CLOUDPRESS_LSFA_RECOVERY_SIGNING_KEY -ErrorAction SilentlyContinue
    if ($keyPointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPointer) }
}

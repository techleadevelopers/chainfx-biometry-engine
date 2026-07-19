$ErrorActionPreference = "Stop"

function New-Secret([int]$Bytes = 32) {
  $buffer = New-Object byte[] $Bytes
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  try {
    $rng.GetBytes($buffer)
  } finally {
    $rng.Dispose()
  }
  [Convert]::ToBase64String($buffer).TrimEnd('=').Replace('+', '-').Replace('/', '_')
}

$providerApiKey = "kyc_live_" + (New-Secret 32)
$faceBiometrySecret = "bio_live_" + (New-Secret 48)

Write-Host "KYC provider cloud env:"
Write-Host "KYC_PROVIDER_API_KEY=$providerApiKey"
Write-Host "FACE_BIOMETRY_SECRET=$faceBiometrySecret"
Write-Host ""
Write-Host "payment-gateway cloud env:"
Write-Host "KYC_ENGINE_PROVIDER_API_KEY=$providerApiKey"
Write-Host "FACE_BIOMETRY_SECRET=$faceBiometrySecret"

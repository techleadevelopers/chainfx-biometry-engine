param(
  [string]$BaseUrl = "http://127.0.0.1:9097",
  [string]$ApiKey = $env:KYC_PROVIDER_API_KEY,
  [int]$Runs = 25
)

$ErrorActionPreference = "Stop"
$headers = @{ "Content-Type" = "application/json" }
if ($ApiKey) { $headers["Authorization"] = "Bearer $ApiKey" }

$latencies = @()
$decisions = @{}
for ($i = 0; $i -lt $Runs; $i++) {
  $payload = @{
    RequestID = "bench-" + [guid]::NewGuid().ToString()
    UserID = "00000000-0000-0000-0000-000000000000"
    Level = 1
    DocumentURL = ""
    DocumentBackURL = ""
    FacialVideoURL = ""
    DeviceFingerprint = "bench-device"
    IPAddress = "127.0.0.1"
  }
  $started = Get-Date
  $response = Invoke-RestMethod -Method Post -Uri "$($BaseUrl.TrimEnd('/'))/analyze" -Headers $headers -Body ($payload | ConvertTo-Json -Depth 8) -TimeoutSec 60
  $elapsed = [int]((Get-Date) - $started).TotalMilliseconds
  $latencies += $elapsed
  $decision = [string]$response.decision
  if (-not $decisions.ContainsKey($decision)) { $decisions[$decision] = 0 }
  $decisions[$decision]++
}

$sorted = $latencies | Sort-Object
function Percentile([int[]]$Values, [int]$P) {
  if ($Values.Count -eq 0) { return 0 }
  $idx = [Math]::Ceiling(($Values.Count * $P) / 100) - 1
  if ($idx -lt 0) { $idx = 0 }
  if ($idx -ge $Values.Count) { $idx = $Values.Count - 1 }
  return $Values[$idx]
}

$report = [pscustomobject]@{
  runs = $Runs
  p50_ms = Percentile $sorted 50
  p95_ms = Percentile $sorted 95
  p99_ms = Percentile $sorted 99
  avg_ms = [int](($latencies | Measure-Object -Average).Average)
  decisions = $decisions
}

$out = "benchmark-{0}.json" -f (Get-Date -Format "yyyyMMdd-HHmmss")
$report | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $out
$report | ConvertTo-Json -Depth 8
Write-Host "Benchmark salvo em $out"

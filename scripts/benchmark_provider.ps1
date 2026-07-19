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
$quality = @{
  face_embedding_returned = 0
  embedding_512 = 0
  liveness_completed = 0
  ocr_completed = 0
  rules_explainable = 0
  media_rejected_or_reviewed = 0
}
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
  if ($response.embedding -and $response.embedding.Count -gt 0) { $quality.face_embedding_returned++ }
  if ($response.embedding -and $response.embedding.Count -eq 512) { $quality.embedding_512++ }
  if ($response.details.liveness) { $quality.liveness_completed++ }
  if ($response.details.document.ocr) { $quality.ocr_completed++ }
  if ($response.details.rules -and $response.details.rules.Count -gt 0) {
    $firstRule = $response.details.rules[0]
    if ($null -ne $firstRule.expected -and $null -ne $firstRule.received) { $quality.rules_explainable++ }
  }
  if ($decision -in @("manual_review", "rejected")) { $quality.media_rejected_or_reviewed++ }
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
  quality = $quality
  quality_rates = @{
    embedding_return_rate = [Math]::Round($quality.face_embedding_returned / [Math]::Max($Runs, 1), 4)
    embedding_512_rate = [Math]::Round($quality.embedding_512 / [Math]::Max($Runs, 1), 4)
    liveness_completion_rate = [Math]::Round($quality.liveness_completed / [Math]::Max($Runs, 1), 4)
    ocr_completion_rate = [Math]::Round($quality.ocr_completed / [Math]::Max($Runs, 1), 4)
    explainability_rate = [Math]::Round($quality.rules_explainable / [Math]::Max($Runs, 1), 4)
  }
  biometric_quality_metrics = @{
    false_accept_rate = "requires_labeled_dataset"
    false_reject_rate = "requires_labeled_dataset"
    eer = "requires_labeled_dataset"
    roc = "requires_labeled_dataset"
    accuracy = "requires_labeled_dataset"
    recall = "requires_labeled_dataset"
    precision = "requires_labeled_dataset"
  }
}

$out = "benchmark-{0}.json" -f (Get-Date -Format "yyyyMMdd-HHmmss")
$report | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $out
$report | ConvertTo-Json -Depth 8
Write-Host "Benchmark salvo em $out"

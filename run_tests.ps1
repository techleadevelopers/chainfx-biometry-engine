$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $root
try {
  $env:PYTHONPATH = Join-Path $root "src"
  python -m py_compile main.py src\kyc_local_ai\app.py src\kyc_local_ai\config.py src\kyc_local_ai\media.py src\kyc_local_ai\quality.py src\kyc_local_ai\liveness.py src\kyc_local_ai\face.py src\kyc_local_ai\ocr.py src\kyc_local_ai\pipeline.py src\kyc_local_ai\schema.py src\kyc_local_ai\decision_engine.py src\kyc_local_ai\fraud_engine.py src\kyc_local_ai\media_probe.py src\kyc_local_ai\workflow.py
  python -m unittest discover -s tests -v
} finally {
  Pop-Location
}

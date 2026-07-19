# ChainFX KYC Provider

Serviço local isolado para OCR, face embedding, liveness, antifraude e modelos ONNX da ChainFX.

Este diretório fica dentro da raiz do `payment-gateway` apenas como módulo local de trabalho. Ele está no `.gitignore` do gateway e deve virar um repo próprio quando for subir separado.

## Papel no Sistema

```text
payment-gateway
  KYCWorker
    -> KYC_ENGINE_PROVIDER_URL
       -> chainfx-kyc-provider /analyze
          -> OCR
          -> face embedding
          -> liveness
          -> antifraude
          -> resposta JSON
```

O gateway financeiro não roda modelo pesado. Ele chama este serviço por URL, recebe score/decisão/embedding e salva o embedding criptografado no banco.

## Estrutura

```text
main.py                         entrypoint local
src/kyc_local_ai/app.py         HTTP Flask: /health e /analyze
src/kyc_local_ai/config.py      env vars e thresholds
src/kyc_local_ai/media.py       download temporário de mídia
src/kyc_local_ai/quality.py     qualidade de imagem/documento
src/kyc_local_ai/ocr.py         hook de OCR próprio
src/kyc_local_ai/liveness.py    análise de vídeo, movimento, replay
src/kyc_local_ai/face.py        embedding facial e comparação
src/kyc_local_ai/pipeline.py    score final e decisão
models/                         modelos ONNX locais
```

## Modules

The provider is organized as modular KYC infrastructure. Each module can evolve independently as the system moves from baseline heuristics to production-grade local AI models.

- **Video Capture Pipeline**: receives the guided facial video URL from the mobile KYC flow and treats it as the primary biometric capture source.
- **Frame Extraction**: extracts representative frames from the video for face analysis, audit, liveness and future model inference.
- **Face Detection**: isolates the face region from document images and video frames before embedding generation.
- **Face Embedding**: generates the mathematical face signature using a local ONNX model configured by `FACE_EMBEDDING_ONNX`.
- **Liveness Detection**: validates real presence through motion, pose, blink/replay checks and the local model configured by `LIVENESS_ONNX`.
- **Face Matching**: compares the document face embedding with the video face embedding and returns a similarity score.
- **OCR Integration**: extracts structured document data through local OCR or an internal `OCR_PROVIDER_URL`.
- **Risk Scoring**: combines document quality, face match, liveness, replay risk, duplicate risk and contextual signals into a final score.
- **Fraud Engine**: flags screen replay, low-quality evidence, missing models, suspicious motion, duplicate face hashes and manual-review cases.
- **Metrics & Benchmarking**: exposes latency and decision metadata through the gateway metrics flow and supports external benchmark scripts.
- **Decision Engine**: produces auditable rule results, reasons and final decision without hiding everything behind a single score.
- **Workflow Events**: returns simple state events such as media received, OCR completed, liveness completed, face completed and decision completed.

## Variáveis

```text
KYC_PROVIDER_HOST=0.0.0.0
KYC_PROVIDER_PORT=9097
KYC_PROVIDER_API_KEY=local-secret
FACE_BIOMETRY_SECRET=secret-forte
FACE_EMBEDDING_ONNX=models/face_embedding.onnx
LIVENESS_ONNX=models/liveness.onnx
OCR_PROVIDER_URL=
KYC_MIN_APPROVAL_SCORE=88
KYC_MIN_FACE_SCORE=86
KYC_MIN_LIVENESS_SCORE=82
```

Generate production secrets:

```powershell
.\scripts\generate_secrets.ps1
```

Use the same generated API key on both sides:

```text
chainfx-kyc-provider:
KYC_PROVIDER_API_KEY=<generated>

payment-gateway:
KYC_ENGINE_PROVIDER_API_KEY=<same generated value>
KYC_ENGINE_PROVIDER_URL=https://<your-kyc-provider-cloud-url>/analyze
```

Use the same `FACE_BIOMETRY_SECRET` in `payment-gateway` and keep it stable. Rotating this secret requires a planned biometric re-enrollment or a key-version migration strategy.

## Rodar Local

```powershell
cd C:\Users\Paulo\Desktop\payment-gateway\chainfx-kyc-provider
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Health:

```powershell
Invoke-RestMethod http://127.0.0.1:9097/health
```

## Tests

Run before publishing this folder as its own repository:

```powershell
cd C:\Users\Paulo\Desktop\payment-gateway\chainfx-kyc-provider
.\run_tests.ps1
```

The suite validates:

- `/health` contract.
- `/analyze` bearer-token protection.
- `/analyze` response shape expected by `payment-gateway`.
- Embedding and `embedding_hash` are returned.
- The service does not approve KYC when local AI models are missing.
- High scores with configured models can approve.
- Low liveness rejects.
- Low face match rejects.
- Schema validation rejects invalid payloads.
- Decision engine returns rules and explainable reasons.
- Pipeline returns per-stage timings and workflow events.

To confirm the full backend persistence path, run an integration KYC request through `payment-gateway` and then check:

```sql
SELECT decision, score, latency_ms, flags
FROM kyc_analysis_results
ORDER BY created_at DESC
LIMIT 5;

SELECT user_id, latest_kyc_request_id, embedding_hash, model_version, consent_at
FROM user_face_biometrics
ORDER BY updated_at DESC
LIMIT 5;
```

Expected no-gap behavior:

- `kyc_analysis_results` must be created for each processed KYC request.
- `user_face_biometrics` must be created only after `approved`.
- `face_embedding_encrypted` must be populated in the database, but never returned in API JSON.
- If models are missing, decision must be `manual_review`, not `approved`.

No `payment-gateway`:

```text
KYC_ENGINE_PROVIDER_URL=http://127.0.0.1:9097/analyze
KYC_ENGINE_PROVIDER_API_KEY=local-secret
FACE_BIOMETRY_SECRET=secret-forte
```

## Produção

Em produção, suba este diretório como repo/serviço separado:

```text
chainfx-kyc-provider
  -> rede privada
  -> URL interna
  -> modelos ONNX versionados/gerenciados fora do payment-gateway
  -> logs sem mídia sensível
  -> métricas próprias
```

Sem modelos reais configurados, o serviço retorna `manual_review` com flag `local_models_not_configured`. Ele não aprova biometria bancária falsa.

## Roadmap

### Phase 1 - Real OCR

Implement local OCR, preferably through a self-hosted OCR module such as PaddleOCR or an equivalent internal engine.

Expected fields:

```json
{
  "ocr": {
    "name": { "value": "Joao Silva", "confidence": 0.99 },
    "cpf": { "value": "12345678909", "confidence": 0.98 },
    "birth_date": { "value": "1990-01-01", "confidence": 0.97 },
    "document_number": { "value": "1234567", "confidence": 0.95 },
    "issuer": { "value": "SSP", "confidence": 0.91 },
    "issue_date": { "value": "2020-01-01", "confidence": 0.90 },
    "expiry_date": { "value": "2030-01-01", "confidence": 0.90 }
  }
}
```

### Phase 2 - Face Detection

Before embedding generation:

```text
document/video frame -> detect face -> align -> crop -> normalize -> embedding
```

### Phase 3 - Real Face Embedding

Replace the current placeholder path with a local ONNX model:

```text
face crop -> FACE_EMBEDDING_ONNX -> 512 floats -> similarity
```

The provider returns the embedding to `payment-gateway`; the gateway encrypts and stores it.

### Phase 4 - Real Liveness

Use the guided video to detect:

- head movement;
- blink;
- yaw/pitch/roll;
- optical flow;
- replay;
- screen reflection;
- deepfake/synthetic texture.

### Phase 5 - Benchmark Suite

Benchmark OCR, embedding, liveness and scoring with local fixtures:

```text
100 videos -> OCR -> embedding -> liveness -> score -> metrics
```

Current benchmark runner:

```powershell
.\scripts\benchmark_provider.ps1 -BaseUrl http://127.0.0.1:9097 -Runs 100
```

Metrics:

- P50/P95/P99;
- throughput;
- CPU/memory in future;
- approval/manual/rejected distribution;
- FAR/FRR/EER when labeled datasets exist.

### Phase 6 - Vector Similarity

The provider must not own the database. Vector search should be coordinated by `payment-gateway` or a dedicated vector service:

```text
new embedding -> top-k search -> candidate duplicate faces -> manual review
```

### Phase 7 - Explainability

Every response should include `rules`, `reasons`, `flags`, `timings_ms` and `workflow_events`.

### Phase 8 - Observability

Track:

- approval rate;
- manual-review rate;
- similarity distribution;
- liveness distribution;
- per-stage latency.

### Phase 9 - Security

- No database in this provider.
- No financial business logic.
- No image/video/embedding in logs.
- API-key auth today; mTLS can be added later.
- Gateway encrypts embeddings at rest.
- Retention/deletion policy remains in `payment-gateway`.

### Phase 10 - Documentation

Keep README focused on architecture, API contract, pipeline diagram, benchmark and operational limits.

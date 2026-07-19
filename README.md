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

## Variáveis

```text
KYC_PROVIDER_HOST=127.0.0.1
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

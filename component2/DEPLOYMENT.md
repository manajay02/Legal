# 🚀 HuggingFace Deployment Guide

## Overview

The CivilModel backend has been updated to use **HuggingFace Serverless Inference API** instead of local Ollama. This allows the fine-tuned Qwen2.5-3B model to run without any local GPU requirements.

## Prerequisites

1. **HuggingFace Account**: Create account at https://huggingface.co
2. **API Token**: Get read-only token from https://huggingface.co/settings/tokens
3. **Fine-tuned Model**: Upload your `civilmodel_qwen3b_v1` adapter to HuggingFace

## Step 1: Upload Model to HuggingFace

### Option A: Using CLI
```bash
# Install HuggingFace CLI
pip install huggingface_hub

# Login
huggingface-cli login

# Upload adapter (from extracted ZIP)
huggingface-cli upload your-username/civilmodel-qwen3b-lora ./civilmodel_qwen3b_v1
```

### Option B: Using Web Interface
1. Go to https://huggingface.co/new
2. Create new model repository: `civilmodel-qwen3b-lora`
3. Upload all files from `civilmodel_qwen3b_v1` folder
4. Make it public (or keep private with your token)

## Step 2: Configure Environment

Create/update `.env` file with your credentials:

```env
# HuggingFace Configuration (REQUIRED)
HUGGINGFACE_MODEL_ID=your-username/civilmodel-qwen3b-lora
HUGGINGFACE_API_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
HUGGINGFACE_TIMEOUT=120
HUGGINGFACE_MAX_RETRIES=5
HUGGINGFACE_RETRY_DELAY=8
```

**Get your token:**
1. Go to https://huggingface.co/settings/tokens
2. Create new token (read access is sufficient)
3. Copy and paste into `.env`

## Step 3: Install Dependencies

The backend already has `requests` installed, so no new dependencies needed!

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1  # Windows PowerShell

# Verify requests is installed
pip list | grep requests
```

## Step 4: Test the Integration

```bash
# Start the server
uvicorn app.main:app --reload --port 8000

# Test with a sample document
# Upload PDF via POST /api/v1/upload
# Process via POST /api/v1/process/{document_id}
```

## How It Works

### Cold Start Handling
HuggingFace Serverless API "sleeps" models after inactivity. The first request triggers a cold start:

1. **First request**: Returns HTTP 503 with `"Model is currently loading"`
2. **Automatic retry**: Backend waits 8 seconds and retries (up to 5 times)
3. **Subsequent requests**: Fast (<5 seconds) since model stays warm

### Request Flow
```
1. OCR Text → format_prompt()
2. Format with Qwen chat template (<|im_start|>system...>)
3. POST to HuggingFace API with retry logic
4. Parse JSON response
5. Return structured data
```

### Error Handling
- **503 Service Unavailable**: Automatic retry with backoff
- **Timeout**: 120s default, configurable
- **Network errors**: Retry up to 5 times
- **Invalid JSON**: Returns fallback structure with error

## Cost & Limits

### Free Tier (Serverless Inference)
- ✅ **Free** for public models
- ✅ No credit card required
- ⏱️ Cold start: ~30-60 seconds first request
- 🔄 Auto-scale to zero after inactivity
- 📊 Rate limits: ~1000 requests/hour

### Paid Inference Endpoints (Optional)
If you need guaranteed uptime:
- Dedicated GPU: $0.60-$1.20/hour
- No cold starts
- Higher throughput
- See: https://huggingface.co/pricing#endpoints

## Troubleshooting

### "HUGGINGFACE_API_TOKEN is not set"
- Add token to `.env` file
- Restart FastAPI server

### "Model failed to load after 5 attempts"
- Increase `HUGGINGFACE_MAX_RETRIES` to 10
- Increase `HUGGINGFACE_RETRY_DELAY` to 15
- Check HuggingFace status: https://status.huggingface.co

### "API error (HTTP 401)"
- Invalid or expired token
- Generate new token at https://huggingface.co/settings/tokens

### "API error (HTTP 404)"
- Model ID wrong in `.env`
- Model not uploaded or private (needs token with access)

### Slow responses
- First request is slow (cold start): Wait 30-60s
- Subsequent requests fast: <5s
- Consider paid endpoint for guaranteed performance

## Comparison: HuggingFace vs Ollama

| Feature | HuggingFace | Ollama (Old) |
|---------|-------------|--------------|
| **Setup** | API token only | Install Ollama + download model |
| **Cost** | Free tier available | Free (local) |
| **GPU Required** | No | Recommended |
| **Cold Start** | 30-60s first request | None |
| **Deployment** | Cloud-ready | Local only |
| **Scalability** | Auto-scale | Manual |
| **Model Updates** | Push to HF Hub | Re-download |

## Next Steps

1. ✅ Upload model to HuggingFace
2. ✅ Configure `.env` with token
3. ✅ Test with sample PDFs
4. 📊 Monitor performance in HuggingFace dashboard
5. 🚀 Deploy FastAPI to cloud (Render, Railway, etc.)

## Production Deployment

Once tested locally, deploy to cloud:

### Option 1: Render.com (Free)
```yaml
# render.yaml
services:
  - type: web
    name: civilmodel-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: HUGGINGFACE_MODEL_ID
        value: your-username/civilmodel-qwen3b-lora
      - key: HUGGINGFACE_API_TOKEN
        sync: false  # Add via Render dashboard
```

### Option 2: Railway.app
1. Connect GitHub repo
2. Add environment variables in dashboard
3. Deploy automatically on push

---

**Your model is now cloud-ready! 🎉**

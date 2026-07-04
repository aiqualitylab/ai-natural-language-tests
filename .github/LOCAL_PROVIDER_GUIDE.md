# Local Provider CI/CD Documentation

## Overview

This project now supports **privacy-first test generation** using local LLM endpoints. No HTML or test data is sent to cloud APIs when using local providers.

## Supported Local Providers

### 1. **Ollama** (Recommended for CI/CD)
- Open-source models: Llama, Mistral, Neural-Chat, etc.
- Simple setup: Download from https://ollama.ai
- No API keys required

**CI/CD Usage:**
- Manual trigger: `Actions → Local Provider Test → Run workflow`
- Select provider: `ollama`
- Select model: `neural-chat` (recommended), `mistral`, `llama2`
- Frameworks: `cypress`, `playwright`, `webdriverio`

### 2. **vLLM** (High Throughput)
- High-performance inference server
- Supports multiple model types
- OpenAI-compatible API

**Setup:**
```bash
pip install vllm
python -m vllm.entrypoints.openai.api_server \
  --model mistralai/Mistral-7B-Instruct-v0.1 \
  --port 8000
```

### 3. **LM Studio** (GUI-Based)
- Simple graphical interface
- Local model management
- OpenAI-compatible API

**Setup:** Download from https://lmstudio.ai/

## CI/CD Workflows

### Main Workflow (`ci.yml`)
- **Default:** Uses OpenAI (requires `OPENAI_API_KEY` secret)
- **Optional Ollama Job:** Add `[ollama]` to commit message OR manually trigger with `llm_provider=ollama`
- Frameworks: Cypress, Playwright, WebdriverIO (parallel)

**Trigger with Ollama:**
```bash
git commit -m "Test generation [ollama]"
```

### Local Provider Workflow (`local-provider-test.yml`)
- **Dedicated workflow** for privacy-first testing
- Manual workflow dispatch only
- Supports: Ollama, vLLM, LM Studio
- Configurable: Model, Frameworks, Requirements, URL

**Features:**
- Model pulling (for Ollama)
- Health checks
- Detailed logging
- Result artifacts

## Getting Started

### Local Development

**1. Start Ollama:**
```bash
ollama serve
# In another terminal:
ollama pull neural-chat
```

**2. Generate tests locally:**
```bash
OLLAMA_BASE_URL=http://localhost:11434/v1 \
OLLAMA_MODEL=neural-chat \
python qa_automation.py "Test login" \
  --url https://example.com/login \
  --llm ollama
```

### GitHub Actions

**1. Use main CI with Ollama service (ci.yml):**
- Add to commit message: `[ollama]`
- Automatically runs Ollama job in parallel with OpenAI tests

**2. Use dedicated local provider workflow:**
- Go to **Actions** tab
- Select **Local Provider Test**
- Click **Run workflow**
- Choose provider, model, frameworks, URL
- Wait for results

## Demo & Test URLs

Public sandbox URLs you can test with (no authentication required):

| Application | URL | Test Ideas |
|-------------|-----|-----------|
| **The Internet (Login)** | `https://the-internet.herokuapp.com/login` | Login forms, validation, error messages |
| **The Internet (Dynamic)** | `https://the-internet.herokuapp.com/dynamic_loading/1` | Wait conditions, dynamic content loading |
| **The Internet (Tables)** | `https://the-internet.herokuapp.com/tables` | Table parsing, data extraction |
| **The Internet (Upload)** | `https://the-internet.herokuapp.com/upload` | File upload handling |
| **The Internet (Drag Drop)** | `https://the-internet.herokuapp.com/drag_and_drop` | Complex interactions |

**Quick test with Ollama (local development):**
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Generate and run test
OLLAMA_BASE_URL=http://localhost:11434/v1 \
OLLAMA_MODEL=neural-chat \
python qa_automation.py \
  "Test login with valid username admin and password password" \
  --url https://the-internet.herokuapp.com/login \
  --framework playwright \
  --llm ollama \
  --run
```

**Expected output:**
- Generated test file in `tests/generated/`
- Test runs and reports results
- No data sent to cloud APIs

## Configuration

### Environment Variables

**Ollama:**
```bash
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=neural-chat
```

**Local OpenAI-compatible:**
```bash
LOCAL_OPENAI_BASE_URL=http://localhost:8000/v1
LOCAL_OPENAI_MODEL=gpt-3.5-turbo
```

### Model Recommendations

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| `neural-chat` | 7B | Fast | Good | **CI/CD** (recommended) |
| `mistral` | 7B | Fast | Excellent | General purpose |
| `llama2` | 7B/13B | Medium | Good | Default Ollama model |
| `mistral-medium` | 34B | Slow | Excellent | High-quality tests |

## Troubleshooting

### Ollama Model Not Found
```bash
# List available models
curl http://localhost:11434/api/tags | jq

# Pull missing model
ollama pull neural-chat
```

### Connection Refused
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve
```

### Local Endpoint Timeout in CI
- Increase model timeout in `qa_config.py` if needed
- Use smaller models (neural-chat, mistral) for faster inference
- Check available resources on CI runner

### Generated Tests Fail with Local Models
- Local models may have different output patterns
- Increase prompt specificity in requirements
- Use simpler test cases for initial testing

## Security & Privacy

**Privacy-First Benefits:**
- No HTML sent to cloud APIs
- No model training on your data
- Full control over infrastructure
- Works offline (after model download)

**CI/CD Best Practices:**
- Keep local endpoints in private runners if possible
- Use air-gapped networks for sensitive testing
- Audit generated tests before deployment

## Performance Metrics

Typical performance on GitHub Actions (4-core runner):

| Provider | Model | Inference Time | Memory |
|----------|-------|-----------------|--------|
| Ollama | neural-chat | 30-45s | 6-8GB |
| Ollama | mistral | 25-40s | 8-10GB |
| vLLM | Mistral-7B | 15-20s | 10-12GB |

## Advanced: Custom Models

To use your own Ollama model:

1. Create a `Modelfile`:
```
FROM llama2
PARAMETER temperature 0
PARAMETER top_p 0.9
```

2. Build and tag:
```bash
ollama create my-custom-model -f Modelfile
ollama run my-custom-model
```

3. Update CI workflow:
```yaml
- name: Pull model
  run: curl -X POST http://localhost:11434/api/pull -d '{"name": "my-custom-model"}'
```

## Support

- **Ollama:** https://ollama.ai
- **vLLM:** https://vllm.ai
- **LM Studio:** https://lmstudio.ai
- **Project Issues:** GitHub Issues with `[local-provider]` tag

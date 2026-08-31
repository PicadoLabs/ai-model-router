# Model Router

Intelligent, explainable, cost- and latency-aware LLM request routing platform and AI Traffic Control Room.

---

## Overview

Model Router intercepts incoming AI requests, analyzes their task type and complexity, evaluates available models against a configurable multi-criteria scoring objective, selects the optimal candidate, and dispatches the request with automatic fallback handling and budget guards.

The platform is designed local-first, allowing full local development and testing using Mock models or local Ollama instances without requiring paid external API keys.

---

## Core Capabilities

- Dual-Mode Request Analyzer: Deterministic heuristics (<3ms latency overhead) for 12 task types, continuous complexity scoring (0.0 to 1.0), and requirement detection, plus an optional LLM classifier mode.
- Explainable Routing Engine: Multi-criteria weighted scoring across Quality, Cost Efficiency, Speed, Capabilities, and Reliability with transparent decision factor reports and candidate rejection logs.
- Provider Abstraction: Decoupled adapters for Mock (simulation), Ollama (local), OpenAI, Anthropic, and Google Gemini.
- Resilience and Fallback: Automated retry classification for transient errors (timeouts, HTTP 429, 503) and tiered fallback to local/mock alternatives.
- Budget Guards: Real-time spend tracking with automated threshold interventions (80% cost optimization, 95% local-only saver, 100% block).
- Traffic Control Room UI: Real-time dark operational interface featuring live topology graphs, playground inspector, SSE live request stream, visual rules builder, and cost savings simulator.
- Developer CLI: Terminal diagnostics (`modelrouter doctor`), routing dry-run (`route`), execution (`run`), model catalog (`models`), and analytics (`analytics`).

---

## Quickstart

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 2. Backend Setup
```bash
# Clone the repository
git clone https://github.com/your-org/model-router.git
cd model-router

# Install dependencies
pip install -r requirements.txt

# Run system diagnostics
python backend/app/cli/main.py doctor

# Start API server (port 8000)
python backend/main.py
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
# Access UI at http://localhost:5173
```

---

## CLI Usage Examples

```bash
# Inspect routing decision for a coding prompt (Dry Run)
python backend/app/cli/main.py route "Write a Python function to parse JSON"

# Route and execute a complex debugging query
python backend/app/cli/main.py run "Debug this distributed async deadlock in high-throughput worker pool"

# List active models in registry
python backend/app/cli/main.py models

# View aggregate system analytics
python backend/app/cli/main.py analytics
```

---

## Testing & Build Verification

```bash
# Run backend test suite (15 unit, integration, and e2e tests)
pytest backend/tests

# Build frontend production bundle
cd frontend
npm run build
```

---

## License

MIT License. Open-source software.

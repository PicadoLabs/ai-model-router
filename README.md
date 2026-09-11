# Model Router

Intelligent, explainable, cost- and latency-aware LLM request routing platform and AI Traffic Control Room.

---

## Overview

Model Router intercepts incoming AI requests, analyzes their task type and continuous complexity, evaluates available models against a configurable multi-criteria scoring objective, selects the optimal candidate, and dispatches the request with automatic fallback handling and budget guards.

The platform is designed local-first, allowing full local development and testing using Mock models or local Ollama instances without requiring paid external API keys.

---

## Key Features

- **Dual-Mode Request Analyzer**: Deterministic heuristics (<3ms latency overhead) for 12 task types, continuous complexity scoring (0.05 to 0.99), and requirement detection, plus an optional LLM classifier mode.
- **Explainable Routing Engine**: Multi-criteria weighted scoring across Quality, Cost Efficiency, Speed, Capabilities, and Reliability with transparent decision factor reports and candidate rejection logs.
- **Provider Abstraction**: Decoupled adapters for Mock (simulation), Ollama (local), OpenAI, Anthropic, and Google Gemini.
- **Resilience and Tiered Fallback**: Automated retry classification for transient errors (timeouts, HTTP 429, 503) and tiered fallback to local/mock alternatives.
- **Budget Control Guards**: Real-time spend tracking with automated threshold interventions (80% cost optimization, 95% local-only saver, 100% block).
- **Traffic Control Room UI**: Real-time operational interface with seamless dark/light mode switching, featuring live topology graphs, playground inspector, SSE live request stream, telemetry export as CSV/JSON, visual rules builder, and cost savings simulator.
- **Developer CLI**: Terminal diagnostics (`doctor`), routing dry-run (`route`), execution (`run`), model catalog (`models`), and analytics (`analytics`).

---

## Architecture & Workflow

```text
[ Client / SDK / Typer CLI ]
           │
           ▼
[ FastAPI Gateway (Port 8000) ]
           │
  ┌────────┴──────────────────────────┐
  │ 1. Request Analyzer (<3ms)        │  --> Task Type, Complexity, Context Size
  │ 2. Priority Rules Evaluation      │  --> Conditional Overrides
  │ 3. Candidate Hard Pruning         │  --> Filter Ineligible Models (Context / Caps)
  │ 4. Multi-Criteria Scoring         │  --> Normalized 0-100 Score across 5 Dimensions
  │ 5. Decision Factor Generator      │  --> Itemized Explainability Breakdown
  └────────┬──────────────────────────┘
           │
           ▼
[ Fallback Supervisor & Provider Layer ]
  ├── Local: Ollama Provider (qwen2.5-coder, llama3.2, deepseek-r1)
  ├── Simulated: In-Memory Mock Provider (Zero Cost)
  └── Cloud: OpenAI, Anthropic, Google Gemini (Optional)
           │
           ▼
[ Storage & Observability Engine ]
  ├── Asynchronous SQLite WAL Database (`model_router.db`)
  └── Server-Sent Events (SSE) Stream -> React Control Room (Port 5173)
```

---

## Supported Platforms & Prerequisites

### Supported Platforms
- Linux (Ubuntu 20.04+, Debian 11+, Fedora)
- macOS (macOS 12+ / Apple Silicon & Intel)
- Windows (Windows 10, Windows 11 / PowerShell & WSL2)

### Prerequisites
- Python 3.10, 3.11, or 3.12
- Node.js 18+ and npm
- (Optional) [Ollama](https://ollama.com/) for local model inference

---

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/PicadoLabs/AI-Model-Router.git
cd AI-Model-Router
```

### 2. Backend Installation
```bash
# Create and activate virtual environment
python -m venv venv
# On Linux/macOS:
source venv/bin/activate
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Install Python dependencies
pip install -r requirements.txt

# Create environment file from template
cp .env.example .env
```

### 3. Frontend Installation
```bash
cd frontend
npm install
cd ..
```

---

## Configuration & Environment Variables

Configuration is loaded via Pydantic Settings from the `.env` file:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `APP_ENV` | `development` | Application environment (`development`, `production`, `test`) |
| `PORT` | `8000` | FastAPI server port |
| `HOST` | `0.0.0.0` | FastAPI server host |
| `DATABASE_URL` | `sqlite+aiosqlite:///./model_router.db` | SQLAlchemy database connection URI |
| `ROUTER_ANALYZER` | `rules` | Default analyzer mode (`rules` for heuristics, `llm` for model classifier) |
| `DEFAULT_ROUTING_POLICY` | `balanced` | Default routing weights (`balanced`, `lowest_cost`, `lowest_latency`, `highest_quality`) |
| `BASELINE_MODEL_ID` | `mock-power` | Reference model ID for calculating baseline cost savings |
| `DEFAULT_PROVIDER` | `mock` | Default execution provider (`mock`, `ollama`) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama HTTP endpoint |
| `OPENAI_API_KEY` | *(empty)* | Optional OpenAI API Key |
| `ANTHROPIC_API_KEY` | *(empty)* | Optional Anthropic API Key |
| `GEMINI_API_KEY` | *(empty)* | Optional Google Gemini API Key |
| `DAILY_BUDGET` | `10.00` | Daily spend limit in USD |
| `MONTHLY_BUDGET` | `100.00` | Monthly spend limit in USD |
| `MAX_RETRIES` | `2` | Maximum retries before triggering cascading fallback |
| `PROVIDER_TIMEOUT_SECONDS` | `30.0` | Provider HTTP timeout in seconds |

---

## Quickstart

### 1. Run System Diagnostics
```bash
python backend/app/cli/main.py doctor
```

### 2. Start the Backend API Server
```bash
python backend/main.py
# API server running at http://127.0.0.1:8000
# Interactive API docs available at http://127.0.0.1:8000/docs
```

### 3. Start the Control Room UI
In a separate terminal:
```bash
cd frontend
npm run dev
# Access UI at http://localhost:5173
```

---

## CLI Usage

The built-in Typer CLI provides terminal commands for inspection, diagnostics, and testing:

```bash
# Run system diagnostics & provider health checks
python backend/app/cli/main.py doctor

# Inspect routing decision for a prompt without executing (Dry Run)
python backend/app/cli/main.py route "Write a Python function to parse JSON"

# Route and execute a query through the selected model
python backend/app/cli/main.py run "Debug this distributed async deadlock in worker pool"

# List all registered models in the catalog
python backend/app/cli/main.py models

# View system-wide routing performance and cost savings analytics
python backend/app/cli/main.py analytics
```

---

## REST API Usage

### 1. Dry-Run Routing (`POST /api/route`)
```bash
curl -X POST http://127.0.0.1:8000/api/route \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write a quicksort algorithm in Python", "policy": "balanced"}'
```

### 2. End-to-End Routed Generation (`POST /api/generate`)
```bash
curl -X POST http://127.0.0.1:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain the difference between TCP and UDP", "policy": "lowest_cost"}'
```

### 3. Fetch Registered Models (`GET /api/models`)
```bash
curl http://127.0.0.1:8000/api/models
```

### 4. Export Historical Traffic (`GET /api/traffic/export`)
Export all persisted traffic records for auditing, accounting, or latency analysis:

```bash
# Export as JSON
curl -OJ "http://127.0.0.1:8000/api/traffic/export?format=json"

# Export as CSV
curl -OJ "http://127.0.0.1:8000/api/traffic/export?format=csv"
```

Each export includes the timestamp, request ID, prompt preview, task type, complexity, selected model, input/output/total tokens, cost saved, and total latency. The `format` query parameter accepts only `csv` or `json`.

The same export is available in the frontend under **Traffic**. Select `CSV` or `JSON` beside **Export Telemetry**, then click the button to download the complete historical traffic dataset.

---

## Running Tests

The test suite includes 18 automated unit, integration, and end-to-end tests covering prompt heuristics, candidate pruning, scoring weights, provider execution, error fallbacks, REST endpoints, and CSV/JSON traffic exports:

```bash
# Run the backend test suite from the repository root
pytest backend/tests

# Or run it from the backend directory
cd backend
python -m pytest tests

# Run frontend production build test
cd frontend
npm run build
```

---

## Project Structure

```text
AI-Model-Router/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   ├── pull_request_template.md
│   └── workflows/
│       └── ci.yml
├── backend/
│   ├── app/
│   │   ├── analytics/       # Cost savings and aggregate analytics service
│   │   ├── analyzer/        # Dual-mode request analyzer (heuristics & LLM)
│   │   ├── api/             # FastAPI REST endpoints and request handlers
│   │   ├── budgets/         # Spend tracking and automated threshold manager
│   │   ├── cli/             # Typer CLI application (doctor, route, run, etc.)
│   │   ├── config/          # Pydantic Settings environment configuration
│   │   ├── experiments/     # A/B policy experimentation service
│   │   ├── fallback/        # Error classifier and tiered fallback supervisor
│   │   ├── models/          # Pydantic schemas (RequestAnalysis, RoutingDecision)
│   │   ├── observability/   # Redacted structured JSON event logger
│   │   ├── providers/       # Decoupled adapters (Mock, Ollama, Cloud)
│   │   ├── router/          # Core scoring matrix, pruner, and rules engine
│   │   └── storage/         # SQLAlchemy models and SQLite async database
│   ├── tests/               # Pytest test suite (15 passing tests)
│   ├── main.py              # FastAPI application entrypoint
│   └── requirements.txt     # Python backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/      # UI components (Navbar, RoutingMap topology graph)
│   │   ├── pages/           # Control Room pages (Dashboard, Playground, Rules, etc.)
│   │   └── types/           # TypeScript data interfaces
│   └── package.json         # Node.js dependencies
├── .env.example             # Configuration template
├── .gitignore               # Git exclusions
├── CODE_OF_CONDUCT.md       # Contributor Covenant Code of Conduct
├── CONTRIBUTING.md          # Contribution guidelines and workflow
├── LICENSE                  # MIT License
├── README.md                # Project documentation
├── requirements.txt         # Root Python dependencies
└── SECURITY.md              # Vulnerability reporting and security policy
```

---

## Contributing

We welcome contributions from the community. Please review [CONTRIBUTING.md](CONTRIBUTING.md) for details on our development setup, coding standards, branch conventions, and pull request process.

Please note that this project is released with a [Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

---

## Security

Security and privacy are core to Model Router. For vulnerability reporting procedures and our zero-secret-exposure policy, please refer to [SECURITY.md](SECURITY.md).

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## PicadoLabs

Maintained and architected by **PicadoLabs**.

- **Organization**: [PicadoLabs](https://github.com/PicadoLabs)
- **Website**: [https://picadolabs.me](https://picadolabs.me)
- **Contact**: [picadolabs@gmail.com](mailto:picadolabs@gmail.com)

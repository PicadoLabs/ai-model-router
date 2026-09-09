# Security Policy

## Supported Versions

| Version | Supported |
| :--- | :--- |
| `1.0.x` | Yes |
| `< 1.0` | No |

---

## Reporting a Vulnerability

The Model Router team takes security and data privacy seriously. If you discover a vulnerability, please report it privately.

**DO NOT disclose vulnerabilities in public GitHub issues or discussions.**

### How to Report Privately
Please email your findings directly to the security team at:
**[picadolabs@gmail.com](mailto:picadolabs@gmail.com)**

### What to Include in Your Report
To help us triage and resolve the issue quickly, please include:
1. Description of the vulnerability.
2. Steps to reproduce the issue (including sample payloads or configuration).
3. Potential impact and attack vectors.
4. Any proposed fixes or remediations if available.

### Response Timeline
- **Initial Response**: Within 48 hours of receipt.
- **Triage & Assessment**: Within 5 business days.
- **Remediation & Patch Release**: Coordinated with the reporter prior to public release.

---

## Security Principles & Architecture

Model Router is built with defense-in-depth principles:
1. **Zero-Secret Exposure**: Provider API keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`) are read strictly from local environment variables and never stored in SQLite database tables or returned to web clients.
2. **Log Redaction**: Observability logging automatically sanitizes dictionary keys matching authorization headers and secret patterns.
3. **Local-First Privacy**: Complete inference can run locally via Mock or Ollama providers with zero telemetry sent to third-party cloud servers.

# Model Router Security Policy

## Reporting Security Vulnerabilities
If you discover any security issues with API token handling, prompt injection vectors, or data exposure, please contact the maintainers immediately.

## Zero-Secret Exposure Policy
1. **API Keys**: External provider tokens (OpenAI, Anthropic, Gemini) are read strictly from local environment variables (`.env`) or secure system secrets.
2. **Logs & Transcripts**: All outgoing observability logs automatically redact authorization headers, bearer tokens, and secrets.
3. **Database Integrity**: SQLite storage only stores model identifiers and usage statistics; raw credentials are never persisted in plaintext database tables.
4. **Browser Privacy**: Frontend client queries never receive or handle backend API keys.

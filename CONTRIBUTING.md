# Contributing to Model Router

Thank you for your interest in contributing to Model Router. We welcome contributions from developers of all skill levels.

---

## Code of Conduct

All contributors and maintainers are expected to adhere to the [Code of Conduct](CODE_OF_CONDUCT.md). Please report unacceptable behavior to [picadolabs@gmail.com](mailto:picadolabs@gmail.com).

---

## Getting Started

### Prerequisites
- **Python**: 3.10, 3.11, or 3.12
- **Node.js**: 18+ and npm
- **Git**
- (Optional) **Ollama**: For testing local model dispatch

### Local Development Setup

1. **Fork and Clone the Repository**:
   ```bash
   git clone https://github.com/<your-username>/AI-Model-Router.git
   cd AI-Model-Router
   ```

2. **Set Up Python Virtual Environment**:
   ```bash
   python -m venv venv
   # On Linux/macOS:
   source venv/bin/activate
   # On Windows:
   .\venv\Scripts\Activate.ps1

   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   ```

4. **Set Up Frontend**:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

5. **Verify Diagnostics**:
   ```bash
   python backend/app/cli/main.py doctor
   ```

---

## Development Workflow

1. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   # or for bug fixes:
   git checkout -b fix/issue-description
   ```

2. **Make Changes**:
   - Write clean, type-annotated, self-documenting code.
   - Maintain the zero-secret-exposure architecture (never hardcode tokens or credentials).
   - Preserve sub-3ms routing performance in the heuristics engine.

3. **Run Backend Tests**:
   ```bash
   pytest backend/tests
   ```

4. **Verify Frontend Build**:
   ```bash
   cd frontend
   npm run build
   cd ..
   ```

---

## Code Standards & Style

### Python (Backend)
- Follow PEP 8 guidelines.
- Use type hints for all function signatures and schema definitions.
- Write unit/integration tests in `backend/tests/` for new endpoints or routing logic.
- Keep external provider credentials strictly inside `.env` configuration.

### TypeScript / React (Frontend)
- Adhere to functional React component patterns with typed props.
- Use Tailwind CSS utility classes and design tokens consistent with the dark control room theme.
- Ensure `npm run build` runs with zero TypeScript or bundler errors.

---

## Pull Request Process

1. Ensure all existing 15 pytest tests pass.
2. Add tests for any new features or bug fixes.
3. Update relevant documentation in `README.md` if parameters, routes, or workflows changed.
4. Open a Pull Request on GitHub with a clear summary and motivation following the PR template.
5. A maintainer will review your submission.

---

## Questions & Support

If you have questions, open a GitHub Discussion or reach out to the maintainers at [picadolabs@gmail.com](mailto:picadolabs@gmail.com).

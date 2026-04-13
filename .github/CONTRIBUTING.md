# Contributing to claude-code-idea-receiver

Thank you for your interest in contributing! This guide will help you get started.

---

## Development Setup

```bash
git clone https://github.com/Rinamo2026/claude-code-idea-receiver
cd idea-receiver
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate.bat

pip install -r requirements.txt
```

### Prerequisites

- Python 3.11+
- [Claude CLI](https://claude.ai/code) (`claude` must be in PATH)
- Git

### Configuration

Defaults work for local development. Create `.env` only if needed:

```env
# Optional: set your own dev root (default: ./projects/)
DEV_ROOT=/home/yourname/dev
```

### Running locally

```bash
bash start.sh      # Linux / macOS
start_silent.bat   # Windows
```

---

## Code Style

| Convention | Rule |
|-----------|------|
| Naming | `snake_case` for variables, functions, files |
| Language | English primary; Japanese OK in comments and docstrings |
| Line length | 100 chars max |
| Imports | stdlib → third-party → local (separated by blank lines) |

No formatter is enforced yet — just keep it consistent with the surrounding code.

---

## Testing

There is no automated test suite yet. Test your changes manually:

```bash
# Dry-run the full pipeline against a local project
python -c "
import asyncio
from classifier import classify_idea
result = asyncio.run(classify_idea('Build a habit tracker app with AI coaching'))
print(result)
"
```

For UI changes, open `http://localhost:8702` and verify the relevant flows.

---

## Adding a New Domain

1. Open `domains.py`
2. Add a new `DomainConfig` entry to the `DOMAINS` dict
3. Define team members, phases, and innovation gate criteria
4. Test by submitting an idea that should map to your new domain
5. Update the "10 Domains" table in `README.md` and `README.ja.md`

---

## Pull Request Guidelines

- **One PR per concern** — don't mix bug fixes with new features
- **Describe the change** — fill in the PR template
- **Test manually** — confirm the pipeline still works end-to-end
- **Update docs** — if you change behavior, update README / comments

---

## Reporting Bugs

Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md).  
Include logs from `idea-receiver.log` and your OS / Python / Claude CLI version.

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](../LICENSE).

---
applyTo: '**'
---
# Project Rules & Guidelines

## Code of Conduct & Style
- Follow PEP 8 for Python code.
- Ensure all Python environments use `venv`.
- Use descriptive variable and function names.
- Document complex functions and classes.

## AI Skills & workflows
This project leverages several AI skills located in `.github/skills/`. When performing tasks, consider using these specialized agents:

### 1. GitHub Workflow Automation (`github-workflow-automation`)
- **Use for**: CI/CD setup, PR automation, issue triage.
- **Location**: `.github/skills/github-workflow-automation/`

### 2. WebApp Testing (`webapp-testing`)
- **Use for**: Writing and running Python Playwright tests.
- **Location**: `.github/skills/webapp-testing/`
- **Helper**: `python .github/skills/webapp-testing/scripts/with_server.py`

### 3. UI/UX Expert (`ui-ux-pro-max`)
- **Use for**: Design reviews, accessibility checks, component styling.
- **Location**: `.github/skills/ui-ux-pro-max/`

### 4. Docker Expert (`docker-expert`)
- **Use for**: Dockerfile optimization, container security, docker-compose setup.
- **Location**: `.github/skills/docker-expert/`

## Testing Strategy
- Run all tests before pushing: `python run_tests.py`
- Use the `smart-tests` workflow in CI to save time.

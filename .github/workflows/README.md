# GitHub Actions Workflows

This directory contains automated workflows configured for this project, leveraging the skills defined in `.github/skills`.

## Available Workflows

### 1. Python Tests (`python-tests.yml`)
- **Triggers**: Push and Pull Request to main/master branches.
- **Description**: Runs the project's test suite using `run_tests.py`.
- **References**: `webapp-testing` skill (Python automation).

### 2. AI Code Review (`ai-review.yml`)
- **Triggers**: Pull Request events.
- **Description**: Uses Google's **Gemini 2.5 Flash** to review code changes in PRs (Fast & Cost-effective).
- **Requirements**: Requires `GEMINI_API_KEY` secret in GitHub repository settings.
- **References**: `github-workflow-automation` skill.

### 3. Smart Test Selection (`smart-tests.yml`)
- **Triggers**: Pull Request events.
- **Description**: Analyzes changed files in a PR and intelligently selects which test suites to run (API, Presentation, or All) to save time and resources.
- **References**: `github-workflow-automation` skill.

### 4. Branch Cleanup (`branch-cleanup.yml`)
- **Triggers**: Weekly schedule (Sundays) or manual dispatch.
- **Description**: Identifies branches that haven't been updated in over 30 days and creates a GitHub Issue listing them for cleanup.
- **References**: `github-workflow-automation` skill.

### 5. Configure Branch Protection (`configure-protection.yml`)
- **Triggers**: Manual dispatch only.
- **Description**: One-click setup to enforce protection rules on the `main` branch (Requires PR approvals, status checks pass: `test`, `review`).
- **References**: `github-workflow-automation` skill.

## Configuration

To enable the AI Code Review, go to your repository Settings -> Secrets and variables -> Actions, and add:
- `GEMINI_API_KEY`: Your Google Gemini API key.

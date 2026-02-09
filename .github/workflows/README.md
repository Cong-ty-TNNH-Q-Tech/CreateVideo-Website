# GitHub Actions Workflows

This directory contains automated workflows configured for this project, leveraging the skills defined in `.github/skills`.

## Available Workflows

### 1. Docker Build, Optimize & Push (`docker-build-push.yml`)
- **Triggers**: 
  - Push to `main` and `develop` branches
  - Version tags (`v*.*.*`)
  - Pull Requests to main
  - Manual workflow dispatch
- **Description**: 
  - Builds Docker image với multi-stage build
  - Tối ưu hóa image size với **docker-slim** (giảm 50-60%)
  - Push optimized image to GitHub Container Registry (ghcr.io)
  - Tạo báo cáo tối ưu hóa (image sizes, reduction %)
  - Support semantic versioning và multiple tags
- **Output**: 
  - `ghcr.io/cong-ty-tnnh-q-tech/createvideo-website:latest`
  - `ghcr.io/cong-ty-tnnh-q-tech/createvideo-website:v1.0.0`
  - `ghcr.io/cong-ty-tnnh-q-tech/createvideo-website:develop`
- **References**: `docker-expert` skill, `github-workflow-automation` skill
- **Documentation**: [docs/DOCKER_DEPLOYMENT.md](../../docs/DOCKER_DEPLOYMENT.md)

### 2. AI Code Review (`ai-review.yml`)
- **Triggers**: Pull Request events.
- **Description**: Uses Google's **Gemini 2.5 Flash** to review code changes in PRs (Fast & Cost-effective).
- **Requirements**: Requires `GEMINI_API_KEY` secret in GitHub repository settings.
- **References**: `github-workflow-automation` skill.

### 3. Branch Cleanup (`branch-cleanup.yml`)
- **Triggers**: Weekly schedule (Sundays) or manual dispatch.
- **Description**: Identifies branches that haven't been updated in over 30 days and creates a GitHub Issue listing them for cleanup.
- **References**: `github-workflow-automation` skill.

### 6. Configure Branch Protection (`configure-protection.yml`)
- **Triggers**: Manual dispatch only.
- **Description**: One-click setup to enforce protection rules on the `main` branch (Requires PR approvals, status checks pass: `test`, `review`).
- **References**: `github-workflow-automation` skill.

### 4. Configure Branch Protection (`configure-protection.yml`)

To enable the AI Code Review, go to your repository Settings -> Secrets and variables -> Actions, and add:
- `GEMINI_API_KEY`: Your Google Gemini API key.

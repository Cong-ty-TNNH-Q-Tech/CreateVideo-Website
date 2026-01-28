# AI DevKit Rules

## Project Context
This project uses ai-devkit for structured AI-assisted development. Phase documentation is located in `docs/ai/`.

## Documentation Structure
- `docs/ai/requirements/` - Problem understanding and requirements
- `docs/ai/design/` - System architecture and design decisions (include mermaid diagrams)
- `docs/ai/planning/` - Task breakdown and project planning
- `docs/ai/implementation/` - Implementation guides and notes
- `docs/ai/testing/` - Testing strategy and test cases
- `docs/ai/deployment/` - Deployment and infrastructure docs
- `docs/ai/monitoring/` - Monitoring and observability setup

## Code Style & Standards
- Follow the project's established code style and conventions
- Write clear, self-documenting code with meaningful variable names
- Add comments for complex logic or non-obvious decisions

## Development Workflow
- Review phase documentation in `docs/ai/` before implementing features
- Keep requirements, design, and implementation docs updated as the project evolves
- Reference the planning doc for task breakdown and priorities
- Copy the testing template (`docs/ai/testing/README.md`) before creating feature-specific testing docs

## AI Interaction Guidelines
- When implementing features, first check relevant phase documentation
- For new features, start with requirements clarification
- Update phase docs when significant changes or decisions are made

## Testing & Quality
- Write tests alongside implementation
- Follow the testing strategy defined in `docs/ai/testing/`
- Use `/writing-test` to generate unit and integration tests targeting 100% coverage
- Ensure code passes all tests before considering it complete

## Documentation
- Update phase documentation when requirements or design changes
- Keep inline code comments focused and relevant
- Document architectural decisions and their rationale
- Use mermaid diagrams for any architectural or data-flow visuals (update existing diagrams if needed)
- Record test coverage results and outstanding gaps in `docs/ai/testing/`

## Key Commands
When working on this project, you can run commands to:
- Understand project requirements and goals (`review-requirements`)
- Review architectural decisions (`review-design`)
- Plan and execute tasks (`execute-plan`)
- Verify implementation against design (`check-implementation`)
- Suggest missing tests (`suggest-tests`)
- Perform structured code reviews (`code-review`)

# Activated Skills & AI Agents

This project is equipped with specialized AI skills located in `.github/skills/`.

## Available Agents

### 1. 🔧 GitHub Workflow Automation (`github-workflow-automation`)
- **Key Capabilities**: Automating PR reviews, issue triage, CI/CD pipelines, and Git operations.
- **Triggers**: Automated via GitHub Actions (see `.github/workflows/`) or invoked manually.
- **Usage**:
  - **PR Reviews**: Open a PR to trigger AI code review.
  - **Smart Tests**: PRs automatically run relevant tests based on changed files.
  - **Branch Cleanup**: Runs weekly to report stale branches.
  - **Manual**: Use tags like `@ai-helper` in comments (if configured).

### 2. 🐍 WebApp Testing (`webapp-testing`)
- **Key Capabilities**: Python-based Playwright testing for local web applications.
- **Location**: `.github/skills/webapp-testing/`
- **Usage**:
  - Use `python .github/skills/webapp-testing/scripts/with_server.py` to run tests against a live server.
  - Write test scripts in `tests/` using native `playwright.sync_api`.

### 3. 🎭 Playwright Skill (`playwright-skill`)
- **Key Capabilities**: General-purpose browser automation and E2E testing using Node.js/TypeScript.
- **Usage**:
  - Best for generating complex automation scripts or cross-browser testing scenarios.
  - Can be used to verify UI behavior, screenshots, and responsive design.

### 4. 🎨 UI/UX Pro Max (`ui-ux-pro-max`)
- **Key Capabilities**: Expert design advice, accessibility checks, color palettes, and component library usage (Shadcn/UI, Tailwind).
- **Usage**: Ask for design reviews, accessibility audits (`color-contrast`, `aria-labels`), or code improvements for frontend components.

### 5. 🐳 Docker Expert (`docker-expert`)
- **Key Capabilities**: Optimization of Dockerfiles, multi-stage builds, and container security.
- **Usage**: Consult when writing `Dockerfile` or `docker-compose.yml` to ensure best practices (layer caching, size reduction).

## Interaction Guidelines for Skills
- **Context Awareness**: When asking for help, specify which agent/skill matches your need (e.g., "Act as the Docker Expert to optimize this file").
- **Automation First**: Prefer using the configured GitHub Actions for routine tasks (testing, linting, reviewing).

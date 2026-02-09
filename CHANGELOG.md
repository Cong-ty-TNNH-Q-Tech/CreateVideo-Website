# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-02-09

### CI/CD & Docker Optimization
- **Docker Build Automation**: Added comprehensive GitHub Actions workflow for automated Docker image building and deployment
  - Auto-build on push to `main` and `develop` branches
  - Semantic versioning support with tags (`v*.*.*`)
  - Multi-stage Docker build with CUDA 11.8 support
- **Image Optimization**: Integrated docker-slim for image size reduction
  - Reduces image size by 50-60% (from ~8.5GB to ~3-4GB)
  - Automated optimization in CI/CD pipeline
  - Comprehensive path preservation for AI models and dependencies
- **GitHub Container Registry**: Auto-push optimized images to GHCR
  - Multiple tags: `latest`, `develop`, semantic versions
  - Commit-specific tags for reproducibility
  - Public access with proper permissions
- **Deployment Improvements**:
  - Added pull-and-run scripts for Windows (PowerShell) and Linux (Bash)
  - Created `docker-compose.prod.yml` for production deployment
  - Comprehensive deployment documentation in `docs/DOCKER_DEPLOYMENT.md`
- **Documentation Updates**:
  - Updated README with pre-built image quick start
  - Added CI/CD badges and GHCR links
  - Enhanced workflows documentation with Docker build info

## [Previous] - 2026-02-06

### Cleanup & Maintenance
- **Git Configuration**: Updated `.gitignore` to exclude all media files (audio, video, images) and their directories.
- **Code Cleanup**: Removed unnecessary test files and markdown documentation to streamline the repository.
    - Deleted entire `tests/` directory with test files
    - Removed `test_moviepy.py`
    - Removed installation docs: `QUICK_INSTALL.md`, `INSTALL_BUILD_TOOLS.md`, `FIX_VIENEU_INSTALL.md`
    - Removed `docs/TROUBLESHOOTING.md`
- **Media Files**: Removed tracked media files from Git history to reduce repository size.

### Features & Enhancements (Since 2026-01-28)
- **Presentation Video Export**: Added full presentation video export with PPT support and enhanced styling (PR #9).
- **Audio System Improvements**: 
    - Implemented audio progress bar and auto-merge functionality
    - Refactored audio UX with centralized voice settings and preview feature
    - Fixed audio merge errors in presentation controller (PR #8)
- **Multi-Language TTS**: Implemented Step 3 with comprehensive text-to-speech system (PR #7).
    - Integrated VieNeu-TTS for Vietnamese
    - Added TTS/SadTalker test pages
- **Script Generation**: 
    - Integrated Gemini 2.5 Flash for script generation
    - Auto-detect input language for script generation (PR #6)
    - Fixed data persistence 404 errors and added bulk save (PR #5)
- **Infrastructure**:
    - Added complete Docker Compose configuration with GPU support
    - Migrated to `google.genai` SDK with auto model download
    - Complete README rewrite with comprehensive documentation

## [Previous] - 2026-01-28

### Refactor
- **MVC Architecture**: Migrated the entire application structure to the MVC (Model-View-Controller) pattern.
    - Split `app.py` into `models`, `controllers`, and `services`.
    - Implemented Application Factory pattern in `app/__init__.py`.
    - Created `PresentationModel` for data persistence.
    - Moved configuration to `config.py`.
- **Directory Structure**: Moved `utils` and `services` into the `app` directory for better organization.
- **SadTalker Integration**: Moved `SadTalker` core engine into `app/SadTalker` and encapsulated its logic within `app/services/video_generator.py`.
- **Unit Tests**: Updated `tests/` to align with the new application factory and directory structure.

### CI/CD & DevOps
- **GitHub Actions**: Added workflows for Python testing, AI Code Review, and maintenance.
- **AI Review**: Updated AI Review workflow to support Gemini 2.5 Flash and use Vietnamese prompts.

### Documentation & Agents
- **AI DevKit**: Added AI DevKit documentation (`docs/ai/`) and agent skills (`.github/skills/`).
- **Rules**: Updated `AGENTS.md` and added project rules.

### Core Features (Previous)
- **Step 1 & 2**: Implemented PPT/PDF upload and Gemini API integration for text generation (2026-01-24).
- **SadTalker**: Integrated SadTalker for video generation, fixed GPU/CPU switching issues, and improved UI/UX (2026-01-23).

## History being tracked

### 2026-01-28
- `35ba7c8` refactor: move SadTalker to app directory and create VideoGenerationService
- `2d4727d` Merge pull request #4 from Cong-ty-TNNH-MoneyEveryWhere/refactor/mvc-structure
- `b087f7a` refactor: move utils and services into app directory structure
- `8789485` Merge pull request #3 from Cong-ty-TNNH-MoneyEveryWhere/refactor/mvc-structure
- `ed644d4` refactor: migrate application structure to MVC pattern
- `0dddb25` Update AI Review prompt to use Vietnamese
- `e1658f7` Merge pull request #2 from Cong-ty-TNNH-MoneyEveryWhere/temp
- `0d0947f` chore: delete some files
- `d7991f2` Update AI Review workflow to support Gemini 2.5 Flash
- `a9a00eb` Update AGENTS.md and add project rules with skill instructions
- `0eaee3c` Add GitHub Actions workflows for Python testing, AI review, and maintenance
- `97653f6` feat: add agent skills
- `860961e` docs: add ai devkit

### 2026-01-24
- `29140ee` Merge pull request #1 from Cong-ty-TNNH-MoneyEveryWhere/feature/step1-step2-implementation
- `fedbde0` chore: Remove implementation/documentation files
- `c1d25ec` feat: Implement Step 1 (PPT/PDF upload) and Step 2 (Gemini API integration)

### 2026-01-23
- `2492480` Refactor requirements and update app logic
- `3221dd9` Update: Integrate SadTalker, fix GPU/CPU issues, add UI/UX

### 2026-01-22
- `dbf655a` Merge remote-tracking branch 'origin/main' into main
- `4fa3748` Initial commit

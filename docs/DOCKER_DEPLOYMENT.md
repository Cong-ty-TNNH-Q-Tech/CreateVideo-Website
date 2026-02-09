# Docker Build & Deployment Guide

## 🚀 Tự động Build Docker Image với GitHub Actions

Dự án này được cấu hình tự động build, tối ưu hóa và push Docker image lên GitHub Container Registry (GHCR) khi có thay đổi code.

### Workflow CI/CD

- **File cấu hình**: [.github/workflows/docker-build-push.yml](.github/workflows/docker-build-push.yml)
- **Trigger**: Push to `main`, `develop` branches hoặc tags `v*.*.*`
- **Registry**: GitHub Container Registry (`ghcr.io`)

### Các bước tự động

1. **Build Docker image** với multi-stage build
2. **Tối ưu hóa** với docker-slim (giảm 40-70% kích thước)
3. **Test** image đã tối ưu
4. **Push** lên GHCR với các tags:
   - `latest` (branch main)
   - `develop` (branch develop)
   - `v1.0.0`, `v1.0`, `v1` (semantic versioning tags)
   - `main-sha-<commit>` (commit-specific)

## 📦 Pull Image từ GHCR

### Bước 1: Authenticate với GHCR

```bash
# Tạo Personal Access Token (PAT) với quyền read:packages
# GitHub Settings -> Developer settings -> Personal access tokens

# Login to GHCR
echo $GITHUB_PAT | docker login ghcr.io -u USERNAME --password-stdin
```

### Bước 2: Pull Image

```bash
# Pull latest version
docker pull ghcr.io/cong-ty-tnnh-q-tech/createvideo-website:latest

# Pull specific version
docker pull ghcr.io/cong-ty-tnnh-q-tech/createvideo-website:v1.0.0

# Pull develop version
docker pull ghcr.io/cong-ty-tnnh-q-tech/createvideo-website:develop
```

## 🏃 Run Container

### Run với Docker

```bash
docker run -d \
  --name videoteaching \
  --gpus all \
  -p 5000:5000 \
  -e GEMINI_API_KEY=your_api_key_here \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/static/uploads:/app/static/uploads \
  -v $(pwd)/static/results:/app/static/results \
  -v $(pwd)/app/SadTalker/checkpoints:/app/app/SadTalker/checkpoints \
  ghcr.io/cong-ty-tnnh-q-tech/createvideo-website:latest
```

### Run với Docker Compose (Production)

```bash
# Tạo file .env
cat > .env << EOF
GEMINI_API_KEY=your_api_key_here
IMAGE_TAG=latest
EOF

# Run với compose
docker-compose -f docker-compose.prod.yml up -d
```

## 🔧 Build Local (Development)

### Build thường

```bash
# Build image
docker build -t videoteaching:dev .

# Run
docker run -it --rm \
  --gpus all \
  -p 5000:5000 \
  -e GEMINI_API_KEY=your_key \
  videoteaching:dev
```

### Build và tối ưu với docker-slim

```bash
# Install docker-slim
curl -L -o ds.tar.gz https://github.com/slimtoolkit/slim/releases/download/1.40.11/dist_linux.tar.gz
tar -xvzf ds.tar.gz
sudo mv dist_linux/* /usr/local/bin/

# Build image
docker build -t videoteaching:pre-slim .

# Optimize với docker-slim
docker-slim build \
  --target videoteaching:pre-slim \
  --tag videoteaching:slim \
  --http-probe=false \
  --continue-after=30 \
  --include-path '/app' \
  --include-path '/usr/local/lib/python3.11' \
  --expose 5000

# Check kích thước
docker images | grep videoteaching
```

## 📊 So sánh Kích thước Image

| Version | Size | Reduction |
|---------|------|-----------|
| Original | ~8.5 GB | - |
| Optimized (docker-slim) | ~3-4 GB | 50-60% |

## 🔐 GitHub Container Registry Setup

### 1. Enable Container Registry

- Vào repository **Settings** -> **Packages**
- Enable **Improved container support**

### 2. Set Package Visibility

- Vào package **Settings**
- Set **Visibility** to Public hoặc Private
- Add **Access** cho teams/users nếu cần

### 3. Configure Secrets (Tự động)

GitHub Actions tự động sử dụng `GITHUB_TOKEN` có sẵn, không cần config thêm secrets.

## 🎯 Trigger Manual Build

```bash
# Trigger workflow manually từ GitHub UI
# Actions tab -> Docker Build, Optimize & Push -> Run workflow

# Hoặc push tag để trigger
git tag v1.0.0
git push origin v1.0.0
```

## 📝 Best Practices

### 1. Versioning Strategy

```bash
# Development builds
git push origin develop  # -> ghcr.io/.../createvideo-website:develop

# Production releases
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0  # -> ghcr.io/.../createvideo-website:v1.0.0
```

### 2. Cache Management

Workflow sử dụng GitHub Actions cache để tăng tốc builds:
- Layer cache được lưu giữa các builds
- Invalidate cache khi thay đổi dependencies

### 3. Security

- ✅ Image được build với non-root user
- ✅ Health checks được cấu hình
- ✅ Secrets quản lý qua GitHub Secrets
- ✅ Image scanning (có thể thêm trivy/snyk)

## 🐛 Troubleshooting

### Image quá lớn?

```bash
# Kiểm tra layers
docker history ghcr.io/cong-ty-tnnh-q-tech/createvideo-website:latest

# Phân tích image
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  wagoodman/dive:latest \
  ghcr.io/cong-ty-tnnh-q-tech/createvideo-website:latest
```

### Build fails on docker-slim?

Docker-slim có thể fail nếu app cần nhiều dependencies runtime. Trong trường hợp này:
1. Tùy chỉnh `--include-path` trong workflow
2. Hoặc disable docker-slim optimization bằng cách comment step đó

### Pull access denied?

```bash
# Kiểm tra authentication
docker logout ghcr.io
echo $GITHUB_PAT | docker login ghcr.io -u USERNAME --password-stdin

# Kiểm tra package visibility (phải là Public hoặc có access rights)
```

## 🔗 Resources

- [GitHub Container Registry Docs](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker Slim Documentation](https://github.com/slimtoolkit/slim)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

## 📞 Support

Nếu gặp vấn đề với CI/CD pipeline hoặc Docker builds, create issue tại repository.

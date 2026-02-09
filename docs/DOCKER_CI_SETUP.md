# Docker CI/CD Setup Checklist

## ✅ Hoàn thành cấu hình

### 1. GitHub Actions Workflow
- [x] File: `.github/workflows/docker-build-push.yml`
- [x] Triggers: Push to main/develop, tags v*.*.*, PRs, manual dispatch
- [x] Features:
  - Multi-stage Docker build
  - docker-slim optimization (50-60% size reduction)
  - GitHub Container Registry push
  - Multiple image tags (latest, develop, semver)
  - Automated testing của optimized image
  - Optimization report generation

### 2. Docker Configuration
- [x] Dockerfile: Multi-stage build với CUDA 11.8
- [x] docker-compose.prod.yml: Production deployment từ GHCR
- [x] .dockerignore: Optimized build context

### 3. Deployment Scripts
- [x] `scripts/pull-and-run.sh`: Linux/Mac deployment script
- [x] `scripts/pull-and-run.ps1`: Windows PowerShell deployment script

### 4. Documentation
- [x] `docs/DOCKER_DEPLOYMENT.md`: Comprehensive deployment guide
- [x] README.md: Updated với pre-built image instructions
- [x] `.github/workflows/README.md`: Workflow documentation
- [x] CHANGELOG.md: Ghi nhận các thay đổi

## 🚀 Next Steps - Setup trên GitHub

### 1. Enable GitHub Actions
```bash
# Actions đã được enable mặc định, verify tại:
# https://github.com/Cong-ty-TNNH-Q-Tech/CreateVideo-Website/actions
```

### 2. Trigger First Build
```bash
# Option A: Push to main branch
git add .
git commit -m "ci: add Docker build automation with slim optimization"
git push origin main

# Option B: Create version tag
git tag -a v1.0.0 -m "Release v1.0.0 with Docker CI/CD"
git push origin v1.0.0

# Option C: Manual workflow dispatch
# Vào GitHub Actions UI -> Docker Build, Optimize & Push -> Run workflow
```

### 3. Monitor Build Progress
```
1. Vào: https://github.com/Cong-ty-TNNH-Q-Tech/CreateVideo-Website/actions
2. Click vào workflow run mới nhất
3. Xem logs của từng step:
   - Build Docker image
   - Optimize with docker-slim
   - Test optimized image
   - Push to GHCR
```

### 4. Verify Image on GHCR
```bash
# Sau khi workflow hoàn thành, image sẽ có tại:
# https://github.com/orgs/Cong-ty-TNNH-Q-Tech/packages/container/package/createvideo-website

# Pull và test:
docker pull ghcr.io/cong-ty-tnnh-q-tech/createvideo-website:latest
docker images | grep createvideo-website
```

### 5. Set Package Visibility (if needed)
```
1. Vào package settings:
   https://github.com/orgs/Cong-ty-TNNH-Q-Tech/packages/container/createvideo-website/settings
2. Set "Change package visibility" to Public (nếu muốn public)
3. Configure access cho team members nếu cần
```

## 🧪 Testing the Setup

### Test 1: Local Pull & Run
```bash
# Set API key
export GEMINI_API_KEY=your_api_key_here

# Run pull script
bash scripts/pull-and-run.sh

# Verify app is running
curl http://localhost:5000/
```

### Test 2: Production Deployment
```bash
# Create .env file
cat > .env << EOF
GEMINI_API_KEY=your_api_key_here
IMAGE_TAG=latest
EOF

# Run with docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Test 3: Version Tags
```bash
# Push a version tag
git tag v1.0.1
git push origin v1.0.1

# Verify multiple tags available:
docker pull ghcr.io/cong-ty-tnnh-q-tech/createvideo-website:v1.0.1
docker pull ghcr.io/cong-ty-tnnh-q-tech/createvideo-website:v1.0
docker pull ghcr.io/cong-ty-tnnh-q-tech/createvideo-website:v1
```

## 📊 Expected Results

### Image Sizes
- **Original image**: ~8.5 GB
- **Optimized with docker-slim**: ~3-4 GB
- **Size reduction**: 50-60%

### Build Time
- **First build**: ~15-25 minutes (download dependencies)
- **Cached builds**: ~5-10 minutes
- **docker-slim optimization**: ~3-5 minutes

### Available Tags
After successful build, these tags will be available:
- `ghcr.io/cong-ty-tnnh-q-tech/createvideo-website:latest`
- `ghcr.io/cong-ty-tnnh-q-tech/createvideo-website:main`
- `ghcr.io/cong-ty-tnnh-q-tech/createvideo-website:main-sha-<commit>`
- `ghcr.io/cong-ty-tnnh-q-tech/createvideo-website:v1.0.0` (if tagged)

## 🐛 Troubleshooting

### Workflow fails on docker-slim step
**Solution**: docker-slim có thể fail nếu app cần nhiều dependencies. Update `--include-path` trong workflow để thêm paths cần thiết.

### Permission denied when pushing to GHCR
**Solution**: Verify GitHub Actions có quyền `packages: write` trong workflow permissions.

### Image quá lớn sau optimization
**Solution**: 
1. Check docker-slim logs trong workflow
2. Thêm `--include-path` cho các paths cần thiết
3. Có thể tắm docker-slim bằng cách comment step đó

### Cannot pull image - access denied
**Solution**:
1. Verify package visibility (Public/Private)
2. Login to GHCR: `echo $GITHUB_PAT | docker login ghcr.io -u USERNAME --password-stdin`
3. Check package permissions

## 📞 Support

- **Workflow logs**: Check GitHub Actions tab
- **Docker issues**: See `docs/DOCKER_DEPLOYMENT.md`
- **General help**: Create GitHub issue

## 🎉 Success Criteria

- [ ] Workflow runs successfully on push to main
- [ ] Image pushed to GHCR with correct tags
- [ ] Image size reduced by 50%+ with docker-slim
- [ ] Can pull and run image locally
- [ ] App accessible at http://localhost:5000
- [ ] GPU support works (if available)

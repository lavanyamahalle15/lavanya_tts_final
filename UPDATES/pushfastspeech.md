# Steps to Push Fastspeech2_HS with Git LFS

## 1. Install and Initialize Git LFS
```bash
# Install Git LFS (if not already installed)
brew install git-lfs  # For macOS
# OR
apt-get install git-lfs  # For Ubuntu/Debian

# Initialize Git LFS
git lfs install
```

## 2. Create Essential Files

### Create .gitignore
```bash
# Create .gitignore file
cat > .gitignore << 'EOL'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/
.env
.venv
env.bak/
venv.bak/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Project specific
static/audio/*
!static/audio/.gitkeep

# Large files and models
*.pth
*.pt
*.ckpt
*.bin

# Logs
*.log
logs/

# Temporary files
tmp/
EOL
```

### Create .gitattributes
```bash
# Create .gitattributes file
cat > .gitattributes << 'EOL'
*.pth filter=lfs diff=lfs merge=lfs -text
Fastspeech2_HS/**/*.pth filter=lfs diff=lfs merge=lfs -text
Fastspeech2_HS/**/model/model.pth filter=lfs diff=lfs merge=lfs -text
Fastspeech2_HS/**/model/config.yaml filter=lfs diff=lfs merge=lfs -text
EOL
```

## 3. Remove Any Existing Git Submodule
```bash
# Remove any existing .git directory in Fastspeech2_HS
rm -rf Fastspeech2_HS/.git
```

## 4. Track Large Files with Git LFS
```bash
# Track .pth files with Git LFS
git lfs track "*.pth"
git lfs track "Fastspeech2_HS/**/*.pth"
git lfs track "Fastspeech2_HS/**/model/model.pth"
git lfs track "Fastspeech2_HS/**/model/config.yaml"
```

## 5. Add and Commit Files
```bash
# Remove everything from Git's index
git rm -rf --cached .

# Add all files back
git add .

# Commit changes
git commit -m "Initialize repository with Git LFS tracking"
```

## 6. Push to GitHub
```bash
# Push to main branch
git push origin main --force
```

## 7. Verify Files are Tracked
```bash
# List all files tracked by Git LFS
git lfs ls-files
```

## Common Issues and Solutions

### 1. Git LFS Quota Issues
If you hit Git LFS bandwidth/storage quota:
- Consider purchasing additional Git LFS storage
- Or use alternative storage solutions for model files

### 2. Large File Push Failures
If pushing large files fails:
- Try pushing in smaller batches
- Ensure stable internet connection
- Increase Git buffer size:
  ```bash
  git config http.postBuffer 524288000
  ```

### 3. Submodule Issues
If Fastspeech2_HS is detected as a submodule:
```bash
# Remove submodule references
rm -rf Fastspeech2_HS/.git
git rm --cached Fastspeech2_HS
git add Fastspeech2_HS/
```

## Verification Steps

After pushing, verify:
1. Check GitHub repository to ensure model files show up as LFS files
2. Download the repository on another machine to test LFS pulls
3. Check file sizes in the repository to ensure they're properly tracked

## Notes
- Make sure you have sufficient Git LFS quota before pushing
- Large model files (>100MB) must be tracked by Git LFS
- Keep your Git LFS cache clean: `git lfs prune`
- Monitor your Git LFS bandwidth usage on GitHub 
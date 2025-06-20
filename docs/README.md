# Multilingual Text-to-Speech (TTS) System: Full Setup & Deployment Guide

This guide provides a comprehensive, step-by-step process for setting up, developing, and deploying the Lavanya-TTS system (FastSpeech2 + HiFi-GAN) on local and cloud platforms (Render, DigitalOcean, Docker, etc.).

---

## 1. System Requirements
- **OS:** Windows, Linux, or macOS
- **Python:** 3.10 (recommended)
- **RAM:** 2GB+ (4GB+ for production)
- **Storage:** 10GB+ (for models and dependencies)
- **(Optional) GPU:** CUDA-compatible for faster inference

---

## 2. Environment Setup

### 2.1. Create Python Environment
```bash
conda create -n tts_env python=3.10 -y
conda activate tts_env
```

### 2.2. Install Core Dependencies
```bash
# PyTorch and TorchAudio (CPU)
pip install torch==2.0.1 torchaudio==2.0.2
# Flask and Gunicorn
pip install flask==3.1.0 gunicorn flask_cors
# ESPnet and TTS dependencies
pip install espnet espnet2 soundfile
# Language and utility packages
pip install numpy scipy PyYAML indic-num2words nltk indic-unified-parser pandas matplotlib requests
```

---

## 3. Project Download & Directory Structure

### 3.1. Clone the Repository
```bash
git clone [https://github.com/lavanyamahalle14/lavanya_tts.git]
cd lavanya_tts3

after clonning repository u have to download model file manually from https://github.com/lavanyamahalle14/lavanya_tts/blob/main/Fastspeech2_HS/marathi/male/model/model.pth
as it has large size and place it in its desired location 
```

### 3.2. Directory Structure
```
.
├── app.py
├── Dockerfile
├── gunicorn_config.py
├── Procfile
├── requirements.txt
├── runtime.txt
├── render.yaml
├── Fastspeech2_HS/
│   ├── app.py
│   ├── inference.py
│   ├── phone_dict/
│   ├── [language]/[gender]/model/
│   │   ├── model.pth
│   │   ├── config.yaml
│   │   ├── feats_stats.npz
│   │   ├── energy_stats.npz
│   │   └── pitch_stats.npz
│   └── ...
├── static/
│   └── audio/
└── templates/
    └── index.html
```

---

## 4. Model Files & Git LFS

### 4.1. Large Files (model.pth, config.yaml if large)
- Track with Git LFS:
```bash
git lfs track "Fastspeech2_HS/[language]/[gender]/model/model.pth"
git add .gitattributes
git add -f Fastspeech2_HS/[language]/[gender]/model/model.pth
```

### 4.2. Small Files (feats_stats.npz, energy_stats.npz, pitch_stats.npz)
- Add as regular files:
```bash
git add Fastspeech2_HS/[language]/[gender]/model/feats_stats.npz
# ...repeat for all .npz files...
```

### 4.3. Commit and Push
```bash
git commit -m "Add model files for [language] [gender]"
git push origin main
```

---

## 5. Model File Format & Permissions

- All `.npz` stats files must be plain NumPy arrays (not pickled).

- Use only the filename (not a path) for `stats_file` in `config.yaml`.
- Permissions:
  - Model, stats, and dictionary files: `644`
  - Output/temp directories: `777`






---

## 6. Running Locally

### 6.1. Prepare Directories
```bash
mkdir -p static/audio Fastspeech2_HS/tmp
chmod 777 static/audio Fastspeech2_HS/tmp
```

### 6.2. Start the Application
```bash
conda activate tts_env
python app.py
```
- App runs at: http://localhost:4005

### 6.3. Test Inference
```bash
cd Fastspeech2_HS
python inference.py --sample_text "नमस्कार" --language marathi --gender male --alpha 1.0 --output_file output_marathi.wav
```

---

## 7. Deployment (Docker/Render/DigitalOcean)

### 7.1. Dockerfile Example
```dockerfile
FROM python:3.10
WORKDIR /app
COPY . .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["gunicorn", "app:app", "--config", "gunicorn_config.py", "--timeout", "120", "--workers", "1", "--threads", "4"]
```

### 7.2. Render/DigitalOcean Setup
- Use Docker deployment for full Git LFS support.
- Set environment variable `TTS_MODEL_ROOT` to `/app/Fastspeech2_HS` (or as needed).
- Ensure all model files are present in the image (run `git lfs pull` before building).

1. Ensure all required model files are present for each supported language/gender.
2. Run `git lfs pull` locally before building Docker images.
3. Build and deploy Docker image (do not use `RUN git lfs pull` in Dockerfile).
4. After deployment, verify file hashes and test file loading in the container:
   - `md5sum /app/Fastspeech2_HS/<lang>/<gender>/model/feats_stats.npz`
   - `python3 -c "import numpy as np; np.load('/app/Fastspeech2_HS/<lang>/<gender>/model/feats_stats.npz', allow_pickle=False)"`
5. Test API/web app end-to-end.
6. Monitor logs for errors/timeouts.


### 7.3. After Deployment: Verify
```bash
# In the deployed container:
python3 -c "import numpy as np; np.load('/app/Fastspeech2_HS/[language]/[gender]/model/feats_stats.npz', allow_pickle=False)"
```
- If no error, deployment is correct.

---

## 8. Troubleshooting & Common Errors

| Error/Issue                                 | Cause                        | Solution                                 |
|---------------------------------------------|------------------------------|------------------------------------------|
| ValueError: pickled data                    | .npz saved with pickle       | Re-save as plain NumPy arrays            |
| FileNotFoundError: feats_stats.npz          | Wrong path or missing file   | Check config, ensure file is present     |
| SIGKILL (exit code 137/9)                   | Out of memory/CPU            | Upgrade plan, optimize model             |
| Request timed out                           | Inference too slow           | Limit input, load models at startup      |
| ModuleNotFoundError: flask_cors             | Missing dependency           | Add to requirements.txt                  |

---

## 9. Best Practices & Tips
- Use only the filename for `stats_file` in config.yaml.
- Patch config.yaml at runtime to use absolute paths if needed.
- Only track large files with LFS; use regular Git for small files.
- Always run `git lfs pull` before building Docker images.
- Load models and vocoders once at startup, not per request.
- Limit input text length to avoid timeouts.
- Monitor logs for errors and optimize for your deployment environment.


---

## 10. Quick Commands Reference
```bash
# Start application
conda activate tts_env && python app.py
# Kill existing process and restart
pkill -f "python app.py" && conda activate tts_env && python app.py
# Check installed packages
pip list
# Test model file loading
python3 -c "import numpy as np; np.load('Fastspeech2_HS/[language]/[gender]/model/feats_stats.npz', allow_pickle=False)"
```

---


## 11. Adding a New Language/Gender (Checklist)
### 11.1. Prepare Model Files
- [x] Place all required files (`model.pth`, `config.yaml`, `feats_stats.npz`, `energy_stats.npz`, `pitch_stats.npz`) in the correct model directory.
- [x] Ensure all `.npz` stats files are plain NumPy arrays (not pickled).

### 11.2. Git LFS and File Tracking
- [x] Track only large files with LFS (e.g., `model.pth`, large `config.yaml`).
- [x] Commit small files as regular files.
- [x] Use only the filename for `stats_file` in config.yaml.

### 11.3. Permissions
- [x] Set permissions: model, stats, and dictionary files to 644.
- [x] Set permissions: output/temp dirs (e.g., `Fastspeech2_HS/tmp`, `static/audio`) to 777.

### 11.4. Backend Logic
- [x] Update backend logic to select the correct model directory for the new language/gender.

### 11.5. Testing After Deployment
- [x] Test file hashes:
  - `md5sum Fastspeech2_HS/english/male/model/feats_stats.npz`
  - `md5sum Fastspeech2_HS/hindi/male/model/feats_stats.npz`
  - After deployment, in container:
    - `md5sum /app/Fastspeech2_HS/english/male/model/feats_stats.npz`
    - `md5sum /app/Fastspeech2_HS/hindi/male/model/feats_stats.npz`
- [x] Test file loading:
  - `python3 -c "import numpy as np; np.load('/app/Fastspeech2_HS/english/male/model/feats_stats.npz', allow_pickle=False)"`
  - `python3 -c "import numpy as np; np.load('/app/Fastspeech2_HS/hindi/male/model/feats_stats.npz', allow_pickle=False)"`
- [x] Test inference and audio output via API/web app.
 `cat Fastspeech2_HS/access.log`

---




## 12 Checklist for Adding English (or Any New Model):

1. **Model Files**
   - Place all required files (`model.pth`, `config.yaml`, `feats_stats.npz`, `energy_stats.npz`, `pitch_stats.npz`, etc.) in model.

2. **Stats Files Format**
   - Make sure all `.npz` stats files are saved as plain NumPy arrays (not pickled).  
     Use your `fix_stats.py` script if needed.
     
    `fix_stats.py`
    import numpy as np
for fname in ["feats_stats.npz", "energy_stats.npz", "pitch_stats.npz"]:
    print(f"Processing {fname}...")
    data = np.load(fname, allow_pickle=True)
    np.savez(fname, **data)
    print(f"Re-saved {fname} as plain NumPy .npz (no pickle).")
     
    run in terminal-cd Fastspeech2_HS/english/male/model && python3 fix_stats.py

3. **Git LFS Tracking**
   - Only track large files (e.g., `model.pth`, possibly `config.yaml`) with Git LFS.
   - Do **not** track small stats files (`*.npz`) with LFS—commit them as regular files.
  
git lfs track "Fastspeech2_HS/english/male/model/model.pth"
git add .gitattributes
git add Fastspeech2_HS/english/male/model/model.pth
git commit -m "Track English male model.pth with LFS"

Fastspeech2_HS/hindi/male/model/model.pth
Fastspeech2_HS/hindi/male/model/config.yaml
Fastspeech2_HS/hindi/male/model/feats_stats.npz
Fastspeech2_HS/hindi/male/model/energy_stats.npz
Fastspeech2_HS/hindi/male/model/pitch_stats.npz

git lfs ls-files

git add .gitattributes
git add Fastspeech2_HS/english/male/model/model.pth
git add Fastspeech2_HS/english/male/model/config.yaml
git add Fastspeech2_HS/hindi/male/model/model.pth
git add Fastspeech2_HS/hindi/male/model/config.yaml
git commit -m "Track English and Hindi male model files with Git LFS"
git push origin main
4. **config.yaml**
   - Use only the filename for `stats_file` entries (e.g., `feats_stats.npz`), not a path.

5. **Permissions**
   - All model, stats, and dictionary files: `644`
   chmod 644 Fastspeech2_HS/english/male/model/*
   - Any output or temp directories: `777`
   chmod 777 Fastspeech2_HS/tmp
   chmod 777 static/audio

6. **Code Logic**
   - Update your backend to select the correct model directory for English male, just as you do for Marathi male.

7. **Test**
git add Fastspeech2_HS/english/male/model/feats_stats.npz
git add Fastspeech2_HS/english/male/model/energy_stats.npz
git add Fastspeech2_HS/english/male/model/pitch_stats.npz
git commit -m "Re-save English male stats files as plain NumPy arrays"
git push origin main
   - After deployment, check:
     - File hashes match between local and container.
     - `np.load(..., allow_pickle=False)` works for all `.npz` files.
     - Inference runs and audio is generated.
run this in render shell-    
python3 -c "import numpy as np; np.load('/app/Fastspeech2_HS/english/male/model/feats_stats.npz', allow_pickle=False)"
--- 
   


**Summary:**  
- Yes, repeat the same best practices for English as you did for Marathi.
- This will prevent LFS/cache issues and ensure smooth deployment.


  # =====================

# DETAILED COMMANDS & CHECKLIST FOR MODEL FILES, LFS, AND DEPLOYMENT
   # =====================

## 1. Git LFS Tracking and Adding Large Files

 `Track large model files with LFS`
`(Do this once for each new model file)`


git lfs track "Fastspeech2_HS/marathi/male/model/model.pth"

git lfs track "Fastspeech2_HS/english/male/model/model.pth"

git lfs track "Fastspeech2_HS/hindi/male/model/model.pth"

git lfs track "Fastspeech2_HS/english/male/model/config.yaml"

git lfs track "Fastspeech2_HS/hindi/male/model/config.yaml"

git add .gitattributes





 `Add large files (force if .gitignore blocks them)`

git add -f Fastspeech2_HS/marathi/male/model/model.pth

`-repeat for other .pth and large .yaml files-`

git add -f Fastspeech2_HS/english/male/model/model.pth

git add -f Fastspeech2_HS/hindi/male/model/model.pth
 
git add -f Fastspeech2_HS/english/male/model/config.yaml

git add -f Fastspeech2_HS/hindi/male/model/config.yaml

## 2. Add Small Stats Files as Regular Files

git add Fastspeech2_HS/marathi/male/model/feats_stats.npz
   `...repeat for all .npz files for each language/gender...`
git add Fastspeech2_HS/english/male/model/feats_stats.npz
git add Fastspeech2_HS/english/male/model/energy_stats.npz
git add Fastspeech2_HS/english/male/model/pitch_stats.npz
git add Fastspeech2_HS/hindi/male/model/feats_stats.npz
git add Fastspeech2_HS/hindi/male/model/energy_stats.npz
git add Fastspeech2_HS/hindi/male/model/pitch_stats.npz

## 3. Commit and Push

git commit -m "Track model.pth and config.yaml with LFS; add stats files as regular files for all models"
git push origin main

## 4. Verify LFS Tracking

git lfs ls-files

## 5. Permissions (run in shell)

chmod 644 Fastspeech2_HS/english/male/model/*

chmod 644 Fastspeech2_HS/hindi/male/model/*

chmod 777 Fastspeech2_HS/tmp

chmod 777 static/audio

## 6. Check File Hashes and Loading (local and after deployment)

md5sum Fastspeech2_HS/english/male/model/feats_stats.npz

md5sum Fastspeech2_HS/hindi/male/model/feats_stats.npz

 `After deployment, in container:`

md5sum /app/Fastspeech2_HS/english/male/model/feats_stats.npz

md5sum /app/Fastspeech2_HS/hindi/male/model/feats_stats.npz

python3 -c "import numpy as np; np.load('/app/Fastspeech2_HS/english/male/model/feats_stats.npz', allow_pickle=False)"

python3 -c "import numpy as np; np.load('/app/Fastspeech2_HS/hindi/male/model/feats_stats.npz', allow_pickle=False)"





# =====================

---

🎉 **Lavanya-TTS is now robust, portable, and ready for production and scaling!**
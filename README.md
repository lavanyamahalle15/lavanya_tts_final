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
pip install espnet soundfile
# Language and utility packages
pip install numpy scipy PyYAML indic-num2words nltk indic-unified-parser pandas matplotlib requests
```
pip install num2words
conda activate tts_env && pip list | grep num2words

**add new lang**
in model file 
add fix_stats.py
import numpy as np

for fname in ["feats_stats.npz", "energy_stats.npz", "pitch_stats.npz"]:
    print(f"Processing {fname}...")
    data = np.load(fname, allow_pickle=True)
    np.savez(fname, **data)
    print(f"Re-saved {fname} as plain NumPy .npz (no pickle).")

in terminal run :cd Fastspeech2_HS/ekalipi/male/model && python3 fix_stats.py
. **config.yaml**
   - Use only the filename for `stats_file` entries (e.g., `feats_stats.npz`), not a path.
. **Permissions**
   - All model, stats, and dictionary files: `644`
   chmod 644 Fastspeech2_HS/english/male/model/*
   - Any output or temp directories: `777`
   chmod 777 Fastspeech2_HS/tmp
   chmod 777 static/audio
---


## 3. Project Download & Directory Structure

### 3.1. Clone the Repository
```bash
git clone [your-repository-url]
cd lavanya_tts3
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
- [x] Place all required files (`model.pth`, `config.yaml`, `feats_stats.npz`, `energy_stats.npz`, `pitch_stats.npz`) in the correct model directory.
- [x] Ensure all `.npz` stats files are plain NumPy arrays (not pickled).
- [x] Track only large files with LFS; commit small files as regular files.
- [x] Use only the filename for `stats_file` in config.yaml.
- [x] Set permissions: files to 644, output/temp dirs to 777.
- [x] Update backend logic to select the correct model directory.
- [x] Test after deployment: file hashes, np.load, inference, and audio output.

---

## 12. Support & Further Help
- Check the troubleshooting section above.
- Verify your Python and package versions.
- Ensure all model files are in place and permissions are correct.
- For further help, open an issue on the project repository.

---

🎉 **Lavanya-TTS is now robust, portable, and ready for production and scaling!**
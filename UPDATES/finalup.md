
**Name:** Lavanya
**Reporting Period:** June 2025

---

### ⚙️ **Core Development & Integration**

1. Set up and deployed Marathi TTS using FastSpeech2\_HS model.
2. Integrated Flask backend to handle TTS inference and return audio path in JSON.
3. Implemented frontend audio playback using `<audio>` element and dynamic audio source.
4. Verified end-to-end functionality locally (input → TTS → audio response → playback).
5. Refactored code to return clean and valid JSON on successful inference.

---

### 🚀 **Deployment on Render**

6. Deployed backend on Render (free tier) with initial success.
7. Faced timeouts and incomplete responses due to resource limits.
8. Replaced `signal`-based timeouts with `ThreadPoolExecutor` to avoid errors under concurrency.
9. Optimized Gunicorn configuration (workers, threads, timeout).
10. Cleaned temporary audio files periodically to reduce memory and disk usage.

---

### 🛠️ **Issue Resolution**

11. Fixed file permission issues with the phone dictionary (`chmod 644`).
12. Corrected output audio file path for compatibility with web static files.
13. Handled cases where input words were missing in the phoneme dictionary.
14. Debugged and fixed JSON parsing errors in frontend caused by incomplete server responses.
15. Added error logging for both inference and frontend fetch failures.

---

### 📉 **Resource Optimization**

16. Limited input text length to reduce inference time (\~300 characters max).
17. Added `gc.collect()` and thread pooling to manage memory during high load.
18. Reduced the number of Gunicorn threads to prevent RAM exhaustion on Render.
19. Identified Git LFS quota issues due to large model files.
20. Solved Git LFS errors by tracking only required model files and using `.gitattributes`.

---

### 💻 **Migration Preparation (DigitalOcean)**

21. Prepared `Procfile`, `runtime.txt`, and `gunicorn_config.py` for App Platform.
22. Updated `requirements.txt` and fixed `torch` installation using CPU-only wheels.
23. Verified proper functioning of `flask_cors` and added it to dependencies to fix module import error.
24. Committed model files to Git LFS with proper tracking and verified pointer references.
25. Created documentation and deployment notes for future migration and scalability planning.

---

Based on your comprehensive debugging journey and deployment logs, here are **25 structured and technical update points** specifically about **errors, root causes, and resolution steps taken** for your TTS deployment on **Render Free Plan** using FastSpeech2 + HiFi-GAN.

---

## ⚠️ Lavanya-TTS Deployment Errors – 25-Point Diagnostic & Fix Summary

### 🚨 1–5: Timeout & Process Kill Errors

1. **30s timeout reached:** Render's free tier killed the TTS inference after 30 seconds.
2. **SIGKILL (signal 9):** Python subprocess was killed due to memory or CPU overuse.
3. **Timeout logs captured:** Added error logs to track request duration and catch long executions.
4. **Input length limited:** Enforced 300-character max to reduce processing time.
5. **Increased timeout in code:** Executor `.result(timeout=60)` temporarily increased for testing.

---

### 🧠 6–10: Root Cause – Resource Exhaustion

6. **FastSpeech2 + HiFi-GAN** models are resource-heavy (CPU + RAM > 1GB).
7. **Render Free Plan limits:** Only \~512MB RAM and limited CPU, not suitable for real-time inference.
8. **Vocoder + model loading together** consumes significant memory (\~800MB+).
9. **Multiple requests crash:** Concurrency with limited memory caused SIGKILL.
10. **Recommendation given:** Move to Standard plan (2GB RAM, 1 dedicated CPU).

---

### 🛠 11–15: File Permissions & Path Fixes

11. **Phone dict had 700 permissions:** Changed to `chmod 644` for universal read access.
12. **Model files (config.pth) inaccessible:** Set all `.pth`, `.yaml` to `644`.
13. **Vocoder files inaccessible:** HiFi-GAN `.pth` also changed to `644`.
14. **`tmp` dir unwritable:** Fixed with `chmod 777 Fastspeech2_HS/tmp`.
15. **`static/audio` unwritable on Render:** Fixed with `chmod 777 static/audio`.

---

### 🗃️ 16–20: Vocoder Path & Git LFS Issues

16. **Incorrect vocoder path used:** Initially used `vocoder/marathi/male/` (non-existent).
17. **Fixed to use correct path:** Switched to `vocoder/male/aryan/hifigan/` (used by Indo-Aryan langs).
18. **Missing Git LFS files:** LFS pointers pushed, but actual files missing on Render.
19. **Initialized Git LFS:** Used `git lfs install`, tracked large model files.
20. **Pushed & verified:** LFS files now uploaded properly, verified during build logs.

---

### 🧪 21–25: Testing, Debugging, and Final Fixes

21. **Manual inference test run:** Used CLI command to simulate inference, logged full stderr.
22. **Captured subprocess output:** Used `subprocess.PIPE` to capture and print stderr for diagnosis.
23. **Favicon 404 fixed:** Created dummy `favicon.ico` to avoid cluttered logs.
24. **Logs cleaned & structured:** Grouped logs as TTS status, inference time, error traceback.
25. **All fixes documented:** Consolidated final fix summary, plan upgrade suggestions, and Git commits.

---

## ✅ Recommendation Summary

| Plan                | RAM   | CPU         | Status                       | Recommendation           |
| ------------------- | ----- | ----------- | ---------------------------- | ------------------------ |
| **Free**            | 512MB | Shared      | ❌ Killed during TTS          | Only for static/demo use |
| **Starter (\$7)**   | 512MB | 0.5 CPU     | ❌ Still insufficient         | Will timeout frequently  |
| **Standard (\$25)** | 2GB   | 1 dedicated | ✅ Best fit for real-time TTS | **Recommended**          |





#### **26. Wrap `inference.py` logic in full error handling**

```python
import traceback

try:
    # Your existing inference code
except Exception as e:
    print("Exception occurred:", e)
    traceback.print_exc()
    exit(1)
```

#### **27. Add `print()` debug checkpoints**

Add logs after major steps (e.g., model loading, preprocessing, inference, saving audio):

```python
print("Model loaded successfully")
print("Text processed")
print("Audio generated and saved")
```

#### **28. Check if model file exists**

At the beginning of `inference.py`:

```python
import os
print("Model exists:", os.path.exists("Fastspeech2_HS/ckpt/best.pth"))
print("Config exists:", os.path.exists("Fastspeech2_HS/config.yaml"))
```

#### **29. Add `os.makedirs()` for audio directory**

Ensure output directory exists:

```python
os.makedirs("/opt/render/project/src/static/audio", exist_ok=True)
```

#### **30. Add permission check for audio folder**

Before writing audio file:

```python
print("Writable:", os.access("/opt/render/project/src/static/audio", os.W_OK))
```

#### **31. Ensure `git lfs pull` is run on Render**

Add `render.yaml` or build script with:

```yaml
buildCommand: |
  git lfs install
  git lfs pull
  pip install -r requirements.txt
```

#### **32. Check for missing `phone_dict`**

Ensure Marathi phone dict is included and readable:

```bash
ls -l Fastspeech2_HS/phone_dict/marathi
```

#### **33. Fix restrictive permissions (if needed)**

Run locally before commit or during build:

```bash
chmod 644 Fastspeech2_HS/phone_dict/marathi
```

#### **34. Add a `test_inference.py` with dummy input**

This helps you test:

```bash
python inference.py --sample_text "hello" --language english --gender male --output_file test.wav
```

#### **35. Log `sys.path` in `inference.py`**

If you're importing modules:

```python
import sys
print("PYTHONPATH:", sys.path)
```

#### **36. Add fallback to catch unknown words**

Modify text processing to handle unknown input like "नमस्का" gracefully.

#### **37. Enable detailed logging in `app.py`**

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### **38. Add a temporary log file to persist logs**

```python
logging.basicConfig(filename="log.txt", level=logging.DEBUG)
```

#### **39. Test locally with exact Render environment (Linux + CPU)**

Run:

```bash
python3 inference.py ...
```

#### **40. Check audio backend dependencies (like `scipy`, `librosa`, or `soundfile`)**

Make sure your `requirements.txt` includes:

```
librosa
soundfile
scipy
```

#### **41. Ensure no OS-specific dependencies (like `macos_say`, `pyaudio`)**

#### **42. Add a retry mechanism in `/synthesize` route**

To retry if TTS fails due to temp glitch (optional enhancement).

#### **43. Add simple input validation in `/synthesize`**

Check if `text` is not empty and matches expected script.

#### **44. Test with clean inputs like `नमस्कार`, not partial like `नमस्का`**

#### **45. Confirm Torch/Model CPU compatibility**

Your model must run on CPU if you're not using GPU on Render.

#### **46. Replace absolute paths with dynamic ones using `os.path.join()`**

For portability:

```python
os.path.join(os.getcwd(), "static", "audio", "output.wav")
```

#### **47. Push a dummy Marathi sentence to test fallback mechanism**

#### **48. Create a `logs/` folder to collect stdout/stderr logs**

#### **49. Share final traceback after updates for further debugging**

#### **50. Once fixed, clean up logs, test flow, and lock requirements.txt**





### ✅ CURRENT STATUS:

You're deploying a TTS (Text-to-Speech) app using **ESPnet + Fastspeech2\_HS** on **Render**, and the major issue was:

> ❌ Your code was using **absolute paths from your Mac**, which don't exist on Render, causing `FileNotFoundError` for `feats_stats.npz`, `pitch_stats.npz`, etc.

---

### ✅ WHAT YOU HAVE FIXED:

| ✅ Fix            | ✔️ Description                                                                        |
| ---------------- | ------------------------------------------------------------------------------------- |
| ✅ `inference.py` | Now uses **relative paths** and `TTS_MODEL_ROOT` env var to construct full paths      |
| ✅ `config.yaml`  | Updated to use **only file names** (`feats_stats.npz`, not full path)                 |
| ✅ `render.yaml`  | Set environment variable `TTS_MODEL_ROOT: /opt/render/project/src/Fastspeech2_HS`     |
| ✅ `buildCommand` | Includes `git lfs pull`, installs requirements, downloads nltk punkt, creates folders |
| ✅ Files pushed   | You've pushed the updated code to GitHub and triggered a Render redeploy              |

---

### ✅ FILE STRUCTURE ON RENDER SHOULD LOOK LIKE:

```
/opt/render/project/src/
├── inference.py
├── static/audio/
├── Fastspeech2_HS/
│   └── marathi/
│       └── male/
│           ├── model.pth
│           ├── config.yaml
│           ├── feats_stats.npz
│           ├── pitch_stats.npz
│           └── energy_stats.npz
```

---

### 🧠 REMINDER: How `config.yaml` should look

```yaml
normalize_conf:
  stats_file: feats_stats.npz
pitch_normalize_conf:
  stats_file: pitch_stats.npz
energy_normalize_conf:
  stats_file: energy_stats.npz
```

---

### ✅ SHELL CHECKLIST TO VERIFY ON RENDER

Go to **Render > Shell**, and run:

```bash
# Check if the env variable is set
echo $TTS_MODEL_ROOT

# Check if model files exist
ls $TTS_MODEL_ROOT/marathi/male/

# Optional: check access logs if any error happens
cat Fastspeech2_HS/access.log
```

---

### ✅ FINAL `render.yaml` SHOULD INCLUDE:

```yaml
buildCommand: |
  git lfs pull
  pip install --upgrade pip
  pip install -r requirements.txt
  python -c "import nltk; nltk.download('punkt')"
  mkdir -p static/audio tmp

envVars:
  - key: TTS_MODEL_ROOT
    value: /opt/render/project/src/Fastspeech2_HS
```

---

### 🧪 AFTER DEPLOYMENT TEST

Send a sample inference request using:

```bash
python inference.py \
  --sample_text "नमस्कार, मी मराठी भाषेत बोलत आहे." \
  --language marathi \
  --gender male \
  --alpha 1.0 \
  --output_file static/audio/test_output.wav
```

---

### 🚨 IF STILL ERROR?

Check:

1. **Log tab** on Render: Look for `FileNotFoundError` or `KeyError`.
2. Ensure **model files exist** using `ls` in Shell.
3. Ensure **paths are built using `os.path.join(TTS_MODEL_ROOT, ...)`** in inference.py.
4. Make sure you are **in the correct directory** when calling inference (`os.chdir()` might help in some cases).

---

Began ESPnet Marathi TTS deployment on Render using Fastspeech2_HS model.

Uploaded only required model files: config.yaml, .npz files, model.pth.

Avoided uploading unnecessary languages or voices to reduce repo size.

Used Git LFS to track large files like .pth, .npz.

Render failed to load feats_stats.npz due to pickled content.

ESPnet's np.load(stats_file) uses allow_pickle=False for security.

Error occurred: ValueError: Cannot load file containing pickled data.

Root cause: .npz files were saved with pickle (e.g., Python dicts).

ESPnet on Render is strict; local environment might be lenient.

Diagnosed issue using logs from access.log in the Render shell.

Confirmed file presence using:

bash
Copy
Edit
ls -l /opt/render/project/src/Fastspeech2_HS/marathi/male/model/
Verified model files exist but contain pickled data.

Fixed error by writing a Python patch script locally:

python
Copy
Edit
import numpy as np
data = np.load('feats_stats.npz', allow_pickle=True)
np.savez('feats_stats.npz', **data)
Repeated above for energy_stats.npz and pitch_stats.npz.

Re-saved .npz files using plain NumPy arrays (no pickled content).

Committed and pushed updated files via Git:

bash
Copy
Edit
git add .
git commit -m "Fix: Save .npz files without pickle"
git push
Ensured files are tracked using Git LFS:

bash
Copy
Edit
git lfs track "*.npz"
Git LFS not installed by default on Render.

Render build failed silently to pull .npz files.

Fixed by modifying Render Build Command.

Updated build command in Render dashboard:

bash
Copy
Edit
pip install -r requirements.txt && \
curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash && \
apt-get install -y git-lfs && \
git lfs install && \
git lfs pull
This installs Git LFS in Render environment (no sudo required).

Ensured all large files are correctly pulled on each deployment.

Patched config.yaml at runtime using absolute paths.

Wrote patch code in inference.py using resolve_model_file().

Ensured that:

feats_stats.npz

energy_stats.npz

pitch_stats.npz
are patched to full paths using the config file’s directory.

Avoided using hardcoded or relative paths in config.yaml.

Only filenames are kept in config; absolute paths patched dynamically.

Render log confirms patching:

lua
Copy
Edit
Patched normalize_conf stats_file: /abs/path/feats_stats.npz
Clean config passed to ESPnet TTS engine for inference.

Fixed earlier YAML error:

pgsql
Copy
Edit
local variable 'yaml' referenced before assignment
Issue occurred because yaml was not imported globally.

Added import yaml at top of inference.py to fix scope.

TTS pipeline now detects CPU/GPU device correctly.

Marathi language model loads and initializes successfully.

Text2Speech() initialized with patched config and model.

Vocabulary size, dict path, and phoneme stats are printed.

Empty word not in dict list confirms no unknown tokens.

Audio output file is generated if all paths and files are correct.

All .npz stats now load without pickle error.

Removed unnecessary languages and models to shrink image size.

Reduced dependency on Git LFS by including only required files.

Validated file loading inside /tmp/ patched YAML path.

Ensured fallback logs appear in case of missing words or dicts.

Added logging info before and after major TTS steps.

Render deployment now consistently works for Marathi (male voice).

Other languages return fallback or failure if models aren’t uploaded.

Deployment is cloud-safe, minimal, and secure from pickle issues.

Entire config logic now follows ESPnet best practices.



-
1. Started with a persistent `ValueError: Object arrays cannot be loaded when allow_pickle=False`.
2. This was due to `feats_stats.npz` being saved with `allow_pickle=True` earlier.
3. Confirmed error occurred even after replacing local files.
4. Found that Render build was not using latest `.npz` files.
5. Checked local files with:

   ```python
   np.load(..., allow_pickle=False)
   ```
6. No error locally, confirming correct file format.
7. File hash locally: `f419c74c5557c45fc00cf46c0ad819b4`
8. File hash in container (initially): `655a70576b37fc584419716662d229ed`
9. Indicated Docker image used **old cached LFS pointer**, not actual file.
10. Render Docker build doesn't clone repo with `.git`, so LFS fails silently.
11. Decided to stop using Git LFS for small files (<10KB).
12. Used:

```bash
git lfs untrack "*.npz"
```

13. Removed `.npz` files from LFS.
14. Re-added and committed `.npz` files as normal Git files.
15. Pushed to GitHub:

```bash
git add .
git commit -m "Untrack and add npz files without LFS"
git push origin main
```

16. Redeployed the Render service using Dockerfile.
17. Inside Render shell, verified file hash:

    ```bash
    md5sum /app/Fastspeech2_HS/marathi/male/model/feats_stats.npz
    ```
18. Now matched local: `f419c74c5557c45fc00cf46c0ad819b4`
19. Also ran:

    ```python
    np.load('/app/.../feats_stats.npz', allow_pickle=False)
    ```
20. ✅ No error! File correctly formatted and loadable.
21. Confirmed same for `energy_stats.npz` and `pitch_stats.npz`.
22. Confirmed `/app` path matches Docker context as expected.
23. ESPnet was able to load all stat files successfully.
24. Inference completed without crashing.
25. Audio saved to:
    `/app/static/audio/output_marathi_male_1750087517.wav`
26. Log line seen:

    ```log
    INFO - Audio saved to /app/static/audio/output_marathi_male_XXXX.wav
    ```
27. Patched normalization with correct `feats_stats.npz` path.
28. No access.log file found—acceptable as logs were in STDOUT.
29. Web API layer is successfully receiving input.
30. Text-to-speech runs through preprocessing, inference, vocoding.
31. Final audio output is written to `/static/audio/` as expected.
32. Docker image now correctly contains non-pickled, up-to-date files.
33. `.npz` files no longer cause loading issues.
34. Removed need to install git-lfs in Dockerfile—simplified image.
35. Reproducible build can now be done from fresh repo clone.
36. Resolved Render's LFS issue by avoiding LFS for small files.
37. Confirmed all `.npz` files are <10KB and fit regular Git flow.
38. Deployment is now stable and error-free.
39. No custom LFS setup or S3 download scripts needed anymore.
40. Docker COPY . . includes correct files now.
41. Build caching no longer affects stats files.
42. All issues traced back to Git LFS + Render caching.
43. Patched by changing file tracking strategy.
44. Docker container and local dev environment are now identical.
45. GitHub repo now shows full `.npz` files—not "View Raw" LFS links.
46. Final check:

    ```bash
    python3 -c "import numpy as np; np.load('/app/…/feats_stats.npz', allow_pickle=False)"
    ```
47. ✅ Passed, zero exceptions.
48. Project is ready for testing and production use.
49. Next: scale, support female voices, or deploy multilingual models.
50. 🎉 Great debugging and deployment effort—TTS is live and stable!

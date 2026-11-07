# Instagram Audio Downloader + Whisper Transcriber (Windows)

This project downloads audio from Instagram videos that your logged-in browser
account is authorized to access, converts it to MP3 using FFmpeg, and transcribes
the audio with OpenAI Whisper.

## 1. Prerequisites

- Windows 10/11
- Python 3.10 or 3.11 recommended
- FFmpeg installed and available in PATH
- Instagram login in the browser selected in `main.py`
- Internet access for downloads and the first Whisper model download

Check Python and FFmpeg in PowerShell:

```powershell
py --version
ffmpeg -version
```

If `py` is not recognized, reinstall Python from https://www.python.org/downloads/
and enable **Add Python to PATH** during installation.

### Install FFmpeg

In an Administrator PowerShell:

```powershell
winget source update
winget install --id Gyan.FFmpeg -e --source winget
```

Close and reopen PowerShell, then verify:

```powershell
ffmpeg -version
```

If WinGet reports a source error, try:

```powershell
winget source reset --force
winget source update
```

## 2. Configure

Open `main.py` and check these settings near the top:

```python
ACCOUNT_URL = "https://www.instagram.com/devops_cloud_ai_with_sanjeev/"
BROWSER = "chrome"
MODEL_NAME = "medium"
```

Supported browser values commonly include `chrome`, `firefox`, `edge`, and `brave`.
Use the browser where you are logged in to Instagram.

Whisper model options:
- `tiny`: fastest, lower accuracy
- `base`: light
- `small`: balanced
- `medium`: better accuracy, higher RAM and processing requirements
- `large`: highest resource demand

## 3. Install Python packages

Open PowerShell in this project folder:

```powershell
cd C:\instagram_transcriber
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

If PowerShell blocks activation, you can skip activation and use:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 4. Run

With the virtual environment activated:

```powershell
py main.py
```

Or double-click `run.bat`.

## 5. Output

Files are saved beside `main.py`:

```text
output/
  devops_cloud_ai_with_sanjeev/
    audio/        # MP3 audio files
    transcripts/  # UTF-8 .txt transcripts
```

The script skips transcript files that already exist and are non-empty.

## Troubleshooting

### FFmpeg not found
Reopen the terminal after installing FFmpeg. Run `ffmpeg -version`.
If it still fails, ensure the FFmpeg `bin` directory is in the Windows PATH.

### Browser cookie/database error
Close all browser windows and rerun the script. Some browsers lock their cookie database.
Make sure the selected browser profile is logged in to Instagram.

### Instagram login, rate-limit, or access errors
Instagram may restrict automated requests or change its site behavior. Update yt-dlp:

```powershell
py -m pip install --upgrade yt-dlp
```

Do not attempt to bypass access controls. Only download content you own or have permission to download.

### Whisper is slow or runs out of memory
Change `MODEL_NAME = "small"` (or `"base"`) in `main.py`. The medium model can require several GB of RAM.
The first model download requires internet; transcription can run offline after the model is cached.

## Notes

- This is a community-tool workflow, not an official Instagram export feature.
- Downloading and reuse must comply with Instagram's terms, copyright, and applicable law.
- The script uses automatic language detection. Whisper can transcribe Hindi and English, but mixed-language accuracy varies with audio quality.

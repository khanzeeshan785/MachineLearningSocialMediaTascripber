# Instagram Reels Transcriber (Windows)

## What it does
1. Opens Instagram in a separate persistent Chrome profile.
2. You log in manually once (if needed), then press ENTER in the terminal.
3. Collects visible Reel/video candidate URLs from the selected public/accessible profile.
4. Exports the logged-in browser cookies locally for yt-dlp.
5. Downloads audio from each URL using yt-dlp + FFmpeg.
6. Transcribes audio with OpenAI Whisper Medium (Hindi/English auto-detection).
7. Creates one combined file: `output/all_transcripts.txt`, with each video title followed by its transcript.

Only use this for content you own or are authorized to access. The script does not bypass login, private-account restrictions, challenges, or rate limits. A Reel URL is a candidate; a successful yt-dlp download is what confirms that its media is accessible.

## Requirements
- Windows 10/11
- Python 3.10 or 3.11 recommended
- Google Chrome
- FFmpeg installed and available on PATH (`ffmpeg -version` should work)
- Internet access for downloads and first-time Whisper model download

## Setup (PowerShell or CMD)
Open terminal in this extracted folder:

```bat
py -3.11 -m venv myenv
myenv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
```

The collector uses your installed Google Chrome executable and a separate browser profile at:
`%LOCALAPPDATA%\InstagramCollectorChrome`

It does NOT use your normal Chrome profile. On first run, log into Instagram in the opened window. The login session is saved in this dedicated profile.

## Run
```bat
myenv\Scripts\activate
python main.py
```

## Output structure
```text
output/
  video_urls.txt
  instagram_videos.json
  instagram_cookies.txt
  video_metadata.json
  audio/
    VIDEO_ID.mp3
  transcripts/
    VIDEO_ID.txt
  all_transcripts.txt
```

## Important settings in main.py
- `RUN_COLLECTOR = True`: opens the browser and collects URLs each run.
- Set `RUN_COLLECTOR = False`: skips browser collection and uses existing `output/video_urls.txt`.
- `MODEL_NAME = "medium"`: better quality but slow on CPU. Set `"small"` for faster transcription.

## Notes
- Keep the `output/instagram_cookies.txt` file private. It contains session cookies. Do not share or upload it.
- If Instagram blocks a request or a Reel is unavailable, that URL may fail; the script continues with the other URLs.
- Re-run safely: existing MP3 files and transcript files are skipped.
- `all_transcripts.txt` is rebuilt from all existing individual transcript files each run.

from pathlib import Path
import sys
import traceback

import yt_dlp
import whisper

# -------------------- CONFIGURATION --------------------
ACCOUNT_URL = "https://www.instagram.com/devops_cloud_ai_with_sanjeev/"
ACCOUNT_URL = "https://www.instagram.com/p/Dfa8-IPJnhA/"
BROWSER = "firefox"
# MODEL_NAME = "large-v3"
MODEL_NAME = "medium"

# ------------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "output" / "devops_cloud_ai_with_sanjeev"
AUDIO_DIR = OUTPUT_DIR / "audio"
TRANSCRIPT_DIR = OUTPUT_DIR / "transcripts"


def download_videos(account_url: str, audio_dir: Path, browser: str) -> None:
    """Download audio from videos accessible to the logged-in browser account."""
    audio_dir.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(audio_dir / "%(title).150s_%(id)s.%(ext)s"),
        "noplaylist": False,
        "ignoreerrors": True,
        "continuedl": True,
        "overwrites": False,
        "quiet": False,
        "no_warnings": False,
        "cookiesfrombrowser": (browser,),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }
        ],
    }

    print(f"Downloading accessible videos from:\n{account_url}")
    print(f"Reading login cookies from: {browser}")
    print("Only download content you own or are authorized to access.\n")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([account_url])


def transcribe_all(audio_dir: Path, transcript_dir: Path, model_name: str) -> None:
    """Transcribe each supported audio file and save a UTF-8 text file."""
    transcript_dir.mkdir(parents=True, exist_ok=True)

    extensions = ("*.mp3", "*.m4a", "*.wav", "*.ogg", "*.opus", "*.flac", "*.aac")
    audio_files = sorted(
        file_path
        for pattern in extensions
        for file_path in audio_dir.glob(pattern)
    )

    if not audio_files:
        print("No audio files found. Check the Instagram download step.")
        return

    print(f"\nLoading Whisper '{model_name}' model...")
    print("The first run downloads the model; this can take time.\n")
    model = whisper.load_model(model_name)
    print("Model loaded.\n")
    print(f"Found {len(audio_files)} audio file(s).\n")

    for index, audio_file in enumerate(audio_files, start=1):
        transcript_file = transcript_dir / f"{audio_file.stem}.txt"

        if transcript_file.exists() and transcript_file.stat().st_size > 0:
            print(f"[{index}/{len(audio_files)}] Already transcribed; skipping: {audio_file.name}")
            continue

        print(f"[{index}/{len(audio_files)}] Transcribing: {audio_file.name}")
        try:
            result = model.transcribe(
                str(audio_file),
                language=None,       # Auto-detect language, including Hindi/English
                task="transcribe",
                fp16=False,          # More compatible with CPU-only Windows installs
            )

            with transcript_file.open("w", encoding="utf-8") as output_file:
                output_file.write(f"Source: {audio_file.name}\n")
                output_file.write("=" * 70 + "\n\n")
                output_file.write(result.get("text", "").strip())
                output_file.write("\n")

            print(f"Saved: {transcript_file.name}\n")
        except Exception:
            print(f"Could not transcribe {audio_file.name}:")
            traceback.print_exc()
            print()


def main() -> int:
    if not ACCOUNT_URL.startswith("https://www.instagram.com/"):
        print("Please set ACCOUNT_URL to a valid Instagram URL in main.py.")
        return 1

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("Instagram Audio Downloader + Whisper Transcriber")
    print("=" * 65)

    try:
        print("\nSTEP 1: Downloading audio...\n")
        download_videos(ACCOUNT_URL, AUDIO_DIR, BROWSER)
    except Exception as error:
        print("\nDownload step failed.")
        print(f"Reason: {error}")
        print(
            "\nCheck that you are logged in to Instagram in the selected browser, "
            "then close the browser and try again. Instagram may also restrict "
            "automated access."
        )
        return 1

    print("\nSTEP 2: Transcribing downloaded audio...\n")
    try:
        transcribe_all(AUDIO_DIR, TRANSCRIPT_DIR, MODEL_NAME)
    except Exception as error:
        print(f"\nTranscription step failed: {error}")
        traceback.print_exc()
        return 1

    print("\n" + "=" * 65)
    print("PROCESS FINISHED")
    print(f"Audio files:   {AUDIO_DIR}")
    print(f"Transcripts:   {TRANSCRIPT_DIR}")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(main())



# from pathlib import Path
# import sys
# import traceback

# import yt_dlp
# import whisper

# # -------------------- CONFIGURATION --------------------
# ACCOUNT_URL = "https://www.instagram.com/devops_cloud_ai_with_sanjeev/"

# BROWSER = "chrome"
# # MODEL_NAME = "large-v3"
# MODEL_NAME = "medium"

# # ------------------------------------------------------

# PROJECT_DIR = Path(__file__).resolve().parent
# OUTPUT_DIR = PROJECT_DIR / "output" / "devops_cloud_ai_with_sanjeev"
# AUDIO_DIR = OUTPUT_DIR / "audio"
# TRANSCRIPT_DIR = OUTPUT_DIR / "transcripts"


# def download_videos(account_url: str, audio_dir: Path, browser: str) -> None:
#     """Download audio from videos accessible to the logged-in browser account."""
#     audio_dir.mkdir(parents=True, exist_ok=True)

#     ydl_opts = {
#         "format": "bestaudio/best",
#         "outtmpl": str(audio_dir / "%(title).150s_%(id)s.%(ext)s"),
#         "noplaylist": False,
#         "ignoreerrors": True,
#         "continuedl": True,
#         "overwrites": False,
#         "quiet": False,
#         "no_warnings": False,
#         "cookiesfrombrowser": (browser,),
#         "postprocessors": [
#             {
#                 "key": "FFmpegExtractAudio",
#                 "preferredcodec": "mp3",
#                 "preferredquality": "128",
#             }
#         ],
#     }

#     print(f"Downloading accessible videos from:\n{account_url}")
#     print(f"Reading login cookies from: {browser}")
#     print("Only download content you own or are authorized to access.\n")

#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         ydl.download([account_url])


# def transcribe_all(audio_dir: Path, transcript_dir: Path, model_name: str) -> None:
#     """Transcribe each supported audio file and save a UTF-8 text file."""
#     transcript_dir.mkdir(parents=True, exist_ok=True)

#     extensions = ("*.mp3", "*.m4a", "*.wav", "*.ogg", "*.opus", "*.flac", "*.aac")
#     audio_files = sorted(
#         file_path
#         for pattern in extensions
#         for file_path in audio_dir.glob(pattern)
#     )

#     if not audio_files:
#         print("No audio files found. Check the Instagram download step.")
#         return

#     print(f"\nLoading Whisper '{model_name}' model...")
#     print("The first run downloads the model; this can take time.\n")
#     model = whisper.load_model(model_name)
#     print("Model loaded.\n")
#     print(f"Found {len(audio_files)} audio file(s).\n")

#     for index, audio_file in enumerate(audio_files, start=1):
#         transcript_file = transcript_dir / f"{audio_file.stem}.txt"

#         if transcript_file.exists() and transcript_file.stat().st_size > 0:
#             print(f"[{index}/{len(audio_files)}] Already transcribed; skipping: {audio_file.name}")
#             continue

#         print(f"[{index}/{len(audio_files)}] Transcribing: {audio_file.name}")
#         try:
#             result = model.transcribe(
#                 str(audio_file),
#                 language=None,       # Auto-detect language, including Hindi/English
#                 task="transcribe",
#                 fp16=False,          # More compatible with CPU-only Windows installs
#             )

#             with transcript_file.open("w", encoding="utf-8") as output_file:
#                 output_file.write(f"Source: {audio_file.name}\n")
#                 output_file.write("=" * 70 + "\n\n")
#                 output_file.write(result.get("text", "").strip())
#                 output_file.write("\n")

#             print(f"Saved: {transcript_file.name}\n")
#         except Exception:
#             print(f"Could not transcribe {audio_file.name}:")
#             traceback.print_exc()
#             print()


# def main() -> int:
#     if not ACCOUNT_URL.startswith("https://www.instagram.com/"):
#         print("Please set ACCOUNT_URL to a valid Instagram URL in main.py.")
#         return 1

#     AUDIO_DIR.mkdir(parents=True, exist_ok=True)
#     TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)

#     print("=" * 65)
#     print("Instagram Audio Downloader + Whisper Transcriber")
#     print("=" * 65)

#     try:
#         print("\nSTEP 1: Downloading audio...\n")
#         download_videos(ACCOUNT_URL, AUDIO_DIR, BROWSER)
#     except Exception as error:
#         print("\nDownload step failed.")
#         print(f"Reason: {error}")
#         print(
#             "\nCheck that you are logged in to Instagram in the selected browser, "
#             "then close the browser and try again. Instagram may also restrict "
#             "automated access."
#         )
#         return 1

#     print("\nSTEP 2: Transcribing downloaded audio...\n")
#     try:
#         transcribe_all(AUDIO_DIR, TRANSCRIPT_DIR, MODEL_NAME)
#     except Exception as error:
#         print(f"\nTranscription step failed: {error}")
#         traceback.print_exc()
#         return 1

#     print("\n" + "=" * 65)
#     print("PROCESS FINISHED")
#     print(f"Audio files:   {AUDIO_DIR}")
#     print(f"Transcripts:   {TRANSCRIPT_DIR}")
#     print("=" * 65)
#     return 0


# if __name__ == "__main__":
#     sys.exit(main())

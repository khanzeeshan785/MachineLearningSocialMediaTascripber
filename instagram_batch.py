
from pathlib import Path
import traceback

import whisper
import yt_dlp


PROJECT_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = PROJECT_DIR / "output"

AUDIO_DIR = (
    OUTPUT_DIR
    / "devops_cloud_ai_with_sanjeev"
    / "audio"
)

TRANSCRIPT_DIR = (
    OUTPUT_DIR
    / "devops_cloud_ai_with_sanjeev"
    / "transcripts"
)

URLS_FILE = OUTPUT_DIR / "video_urls.txt"

COOKIE_FILE = OUTPUT_DIR / "instagram_cookies.txt"

MODEL_NAME = "medium"

AUDIO_EXTENSIONS = (
    ".mp3",
    ".m4a",
    ".wav",
    ".ogg",
    ".opus",
    ".flac",
    ".aac"
)


def load_video_urls(file_path=URLS_FILE):

    urls = []

    seen = set()

    paths = [
        Path(file_path),
        PROJECT_DIR / "video_urls.txt"
    ]

    for path in paths:

        if not path.exists():
            continue

        try:

            for line in path.read_text(
                encoding="utf-8"
            ).splitlines():

                url = line.strip().split("?")[0]

                if (
                    url.startswith(
                        "https://www.instagram.com/"
                    )
                    and url not in seen
                ):

                    seen.add(url)

                    urls.append(url)

        except OSError as exc:

            print(
                f"Warning: could not read URL file "
                f"{path}: {exc}"
            )

    return urls


def find_existing_audio(video_id):

    for ext in AUDIO_EXTENSIONS:

        candidate = AUDIO_DIR / f"{video_id}{ext}"

        if (
            candidate.exists()
            and candidate.stat().st_size > 0
        ):

            return candidate

    return None


def download_audio(url):

    AUDIO_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    video_id = url.rstrip("/").split("/")[-1]

    existing = find_existing_audio(video_id)

    if existing:

        print(
            f"Already downloaded: {existing.name}"
        )

        return {
            "url": url,
            "status": "already_downloaded",
            "file": str(existing)
        }

    options = {

        "format": "bestaudio/best",

        "outtmpl": str(
            AUDIO_DIR / "%(id)s.%(ext)s"
        ),

        "noplaylist": True,

        "ignoreerrors": False,

        "continuedl": True,

        "overwrites": False,

        "quiet": False,

        "no_warnings": False,

        "retries": 3,

        "fragment_retries": 3,

        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128"
            }
        ]
    }

    if (
        COOKIE_FILE.exists()
        and COOKIE_FILE.stat().st_size > 0
    ):

        options["cookiefile"] = str(COOKIE_FILE)

    try:

        with yt_dlp.YoutubeDL(options) as ydl:

            ydl.download([url])

        audio_file = find_existing_audio(video_id)

        if audio_file:

            print(
                f"Audio ready: {audio_file.name}"
            )

            return {
                "url": url,
                "status": "downloaded",
                "file": str(audio_file)
            }

        print(
            f"Download did not create a supported "
            f"audio file for {video_id}."
        )

        return {
            "url": url,
            "status": "failed",
            "file": None
        }

    except Exception as exc:

        print(
            f"Download failed for {video_id}: {exc}"
        )

        return {
            "url": url,
            "status": "failed",
            "error": str(exc),
            "file": None
        }


def download_all_audio(urls):

    AUDIO_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    results = []

    for index, url in enumerate(
        urls,
        start=1
    ):

        video_id = url.rstrip("/").split("/")[-1]

        print("\n" + "-" * 65)

        print(
            f"[{index}/{len(urls)}] {video_id}"
        )

        print(url)

        results.append(
            download_audio(url)
        )

    downloaded = sum(
        r["status"] == "downloaded"
        for r in results
    )

    skipped = sum(
        r["status"] == "already_downloaded"
        for r in results
    )

    failed = sum(
        r["status"] == "failed"
        for r in results
    )

    print("\nDOWNLOAD SUMMARY")
    print("=" * 50)

    print("Downloaded:", downloaded)
    print("Already downloaded:", skipped)
    print("Failed:", failed)

    return results


def transcribe_all(
    audio_dir=AUDIO_DIR,
    transcript_dir=TRANSCRIPT_DIR,
    model_name=MODEL_NAME
):

    transcript_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    audio_files = sorted(
        p
        for p in audio_dir.iterdir()
        if (
            p.is_file()
            and p.suffix.lower() in AUDIO_EXTENSIONS
        )
    ) if audio_dir.exists() else []

    if not audio_files:

        print(
            "No audio files found. "
            "Nothing to transcribe."
        )

        return 0

    pending = [
        p
        for p in audio_files
        if (
            not (
                transcript_dir / f"{p.stem}.txt"
            ).exists()
            or (
                transcript_dir / f"{p.stem}.txt"
            ).stat().st_size == 0
        )
    ]

    print(
        f"\nAudio files found: {len(audio_files)}"
    )

    print(
        f"Already transcribed: "
        f"{len(audio_files) - len(pending)}"
    )

    if not pending:
        return len(audio_files)

    print(
        f"\nLoading Whisper '{model_name}' model..."
    )

    model = whisper.load_model(model_name)

    completed = len(audio_files) - len(pending)

    for index, audio_file in enumerate(
        pending,
        start=1
    ):

        transcript_file = (
            transcript_dir
            / f"{audio_file.stem}.txt"
        )

        print(
            f"\n[{index}/{len(pending)}] "
            f"Transcribing: {audio_file.name}"
        )

        try:

            result = model.transcribe(
                str(audio_file),
                language=None,
                task="transcribe",
                fp16=False
            )

            text = result.get(
                "text",
                ""
            ).strip()

            with transcript_file.open(
                "w",
                encoding="utf-8"
            ) as out:

                out.write(
                    f"VIDEO TITLE: Instagram video "
                    f"{audio_file.stem}\n"
                )

                out.write(
                    f"SOURCE AUDIO: {audio_file.name}\n"
                )

                out.write("=" * 70 + "\n\n")

                out.write(text + "\n")

            completed += 1

            print(
                "Transcript saved:",
                transcript_file.name
            )

        except Exception:

            print(
                f"Transcription failed for "
                f"{audio_file.name}; continuing."
            )

            traceback.print_exc()

    return completed


def create_combined_transcript(
    output_dir=OUTPUT_DIR,
    transcript_dir=TRANSCRIPT_DIR
):

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    transcript_files = (
        sorted(transcript_dir.glob("*.txt"))
        if transcript_dir.exists()
        else []
    )

    combined_file = (
        output_dir / "all_transcripts.txt"
    )

    with combined_file.open(
        "w",
        encoding="utf-8"
    ) as out:

        out.write(
            "INSTAGRAM COMPLETE TRANSCRIPT\n"
        )

        out.write("=" * 80 + "\n\n")

        for index, transcript_file in enumerate(
            transcript_files,
            start=1
        ):

            out.write(
                f"\nVIDEO {index}: "
                f"{transcript_file.stem}\n"
            )

            out.write("-" * 80 + "\n\n")

            out.write(
                transcript_file.read_text(
                    encoding="utf-8"
                )
            )

            out.write("\n\n")

    print(
        "\nCombined transcript saved:",
        combined_file
    )

    return combined_file


# Compatibility function for older main.py versions.
def download_audio_from_urls(
    urls,
    audio_dir=AUDIO_DIR,
    browser=None
):

    global AUDIO_DIR

    AUDIO_DIR = Path(audio_dir)

    return download_all_audio(urls)


def main():

    urls = load_video_urls()

    if not urls:

        print(
            f"No URLs found. Run the collector first: "
            f"{URLS_FILE}"
        )

        return 1

    results = download_all_audio(urls)

    transcribed = transcribe_all()

    create_combined_transcript()

    failed = sum(
        item["status"] == "failed"
        for item in results
    )

    print(
        f"\nFinished. URLs={len(urls)}, "
        f"transcribed={transcribed}, "
        f"failed downloads={failed}"
    )

    return 0 if failed == 0 else 2


if __name__ == "__main__":

    import sys

    sys.exit(main())

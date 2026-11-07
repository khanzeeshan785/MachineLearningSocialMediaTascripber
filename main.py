
from pathlib import Path
import sys
import traceback

from instagram_browser_collector import collect_video_urls

from instagram_batch import (
    URLS_FILE,
    AUDIO_DIR,
    TRANSCRIPT_DIR,
    MODEL_NAME,
    load_video_urls,
    download_all_audio,
    transcribe_all,
    create_combined_transcript,
)


PROFILE_URL = (
    "https://www.instagram.com/"
    "devops_cloud_ai_with_sanjeev/"
)

RUN_COLLECTOR = True


def main():

    URLS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    AUDIO_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    TRANSCRIPT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("=" * 65)
    print("INSTAGRAM VIDEO TRANSCRIBER")
    print("=" * 65)

    # STEP 1: COLLECT URLS

    if RUN_COLLECTOR:

        print(
            "\nSTEP 1: Collecting Instagram URLs"
        )

        try:

            found = collect_video_urls(
                profile_url=PROFILE_URL,
                urls_file=URLS_FILE,
                browser="chrome"
            )

            print(
                f"\nCollector returned: "
                f"{len(found)} unique candidate URLs"
            )

        except Exception as exc:

            print(
                f"\nCollector failed: {exc}"
            )

            traceback.print_exc()

            print(
                "Will try to continue with URLs already saved."
            )

    # STEP 2: LOAD URLS

    urls = load_video_urls(URLS_FILE)

    print(
        f"\nTotal unique URLs available: {len(urls)}"
    )

    if not urls:

        print(
            "No URLs found. Check Instagram login "
            "and profile access."
        )

        return 1

    # STEP 3: DOWNLOAD AUDIO

    print("\nSTEP 2: Downloading audio")

    results = download_all_audio(urls)

    downloaded = sum(
        x["status"] == "downloaded"
        for x in results
    )

    skipped = sum(
        x["status"] == "already_downloaded"
        for x in results
    )

    failed = sum(
        x["status"] == "failed"
        for x in results
    )

    print(
        f"\nDownload summary: {downloaded} downloaded, "
        f"{skipped} already present, "
        f"{failed} failed."
    )

    # STEP 4: TRANSCRIBE

    print("\nSTEP 3: Whisper transcription")

    try:

        completed = transcribe_all(
            AUDIO_DIR,
            TRANSCRIPT_DIR,
            MODEL_NAME
        )

    except Exception as exc:

        print(
            f"Whisper setup/model error: {exc}"
        )

        traceback.print_exc()

        return 1

    # STEP 5: COMBINED TRANSCRIPT

    print(
        "\nSTEP 4: Creating combined transcript"
    )

    combined_file = create_combined_transcript()

    # FINAL SUMMARY

    print("\n" + "=" * 65)
    print("PROCESS FINISHED")
    print("=" * 65)

    print("URLs:", len(urls))
    print("Downloaded:", downloaded)
    print("Already downloaded:", skipped)
    print("Failed downloads:", failed)
    print("Transcripts available:", completed)

    print("Audio folder:", AUDIO_DIR)
    print("Transcript folder:", TRANSCRIPT_DIR)
    print("Combined transcript:", combined_file)

    return 0 if failed == 0 else 2


if __name__ == "__main__":

    sys.exit(main())

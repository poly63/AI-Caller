#!/usr/bin/env python3
"""Asterisk monitor -> SmartCall bridge.

Adapted from the zip project's callai watcher pattern and wired to this API:
- detect completed .wav files from Asterisk monitor directory
- normalize audio to 16k mono
- transcribe with faster-whisper
- create call + send transcript + end + analyze in SmartCall backend
"""

import os
import re
import time
import json
import shutil
import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple

import httpx
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None


WATCH_DIR = Path(os.getenv("ASTERISK_MONITOR_DIR", "/var/spool/asterisk/monitor"))
BASE_DIR = Path(os.getenv("SMARTCALL_BRIDGE_DIR", str(Path.home() / "call-ai-bridge")))

TMP_DIR = BASE_DIR / "tmp"
OUT_DIR = BASE_DIR / "output"
PROCESSED_DIR = BASE_DIR / "processed"
DONE_DIR = PROCESSED_DIR / "done"
LOG_FILE = BASE_DIR / "logs" / "bridge.log"

API_BASE = os.getenv("SMARTCALL_API_BASE", "http://127.0.0.1:8000/api")
TENANT_ID = os.getenv("SMARTCALL_TENANT_ID", "public")
MODEL_SIZE = os.getenv("SMARTCALL_WHISPER_MODEL", "base")
MODEL_DEVICE = os.getenv("SMARTCALL_WHISPER_DEVICE", "cpu")
TARGET_LANG = os.getenv("SMARTCALL_TARGET_LANG", "en")

FILE_STABLE_WAIT_SEC = int(os.getenv("SMARTCALL_FILE_STABLE_WAIT_SEC", "2"))
FILE_STABLE_RETRIES = int(os.getenv("SMARTCALL_FILE_STABLE_RETRIES", "12"))

# example filename:
# internal-7001-7002-20260207-155417-1770459857.26.wav
REC_NAME_RE = re.compile(
    r"^(?P<prefix>[^-]+)-(?P<src>[^-]+)-(?P<dst>[^-]+)-(?P<date>\d{8})-(?P<time>\d{6})-.*\.wav$"
)


def setup_logging() -> logging.Logger:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
    )
    return logging.getLogger("asterisk_bridge")


logger = setup_logging()


def ensure_dirs() -> None:
    for directory in [TMP_DIR, OUT_DIR, PROCESSED_DIR, DONE_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def wait_until_file_complete(filepath: Path) -> bool:
    previous_size = -1
    for _ in range(FILE_STABLE_RETRIES):
        try:
            current_size = filepath.stat().st_size
        except FileNotFoundError:
            return False
        if current_size == previous_size and current_size > 0:
            return True
        previous_size = current_size
        time.sleep(FILE_STABLE_WAIT_SEC)
    return False


def parse_agent_and_customer(filename: str) -> Tuple[str, str]:
    match = REC_NAME_RE.match(filename)
    if match:
        src = match.group("src")
        dst = match.group("dst")
        return src, dst
    stem = Path(filename).stem
    return "AUTO_AGENT", stem


def convert_audio_to_mono_16k(src_wav: Path, dst_wav: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src_wav),
        "-ar",
        "16000",
        "-ac",
        "1",
        "-af",
        "volume=2.5,aresample=16000",
        str(dst_wav),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    if not dst_wav.exists() or dst_wav.stat().st_size == 0:
        raise RuntimeError(f"FFmpeg conversion failed for {src_wav}")


class Transcriber:
    def __init__(self) -> None:
        self.model = None
        if WhisperModel is None:
            logger.warning("faster-whisper not available; transcription will be skipped.")
            return
        logger.info("Loading Whisper model=%s device=%s", MODEL_SIZE, MODEL_DEVICE)
        self.model = WhisperModel(
            MODEL_SIZE,
            device=MODEL_DEVICE,
            compute_type="int8" if MODEL_DEVICE == "cpu" else "float16",
        )

    def transcribe_file(self, wav_path: Path) -> str:
        if self.model is None:
            return ""
        segments, _ = self.model.transcribe(str(wav_path), language="en", vad_filter=True)
        lines = [segment.text.strip() for segment in segments if segment.text.strip()]
        return "\n".join(lines)


class SmartCallApi:
    def __init__(self) -> None:
        self.client = httpx.Client(timeout=60.0)

    def _headers(self) -> dict:
        return {"Content-Type": "application/json", "X-Tenant-Id": TENANT_ID}

    def start_call(self, agent_id: str, customer_number: str) -> Optional[str]:
        payload = {
            "agent_id": agent_id,
            "agent_name": f"Ext {agent_id}",
            "customer_number": customer_number,
            "customer_name": "Asterisk Caller",
            "direction": "inbound",
            "language": "en",
            "translated_language": TARGET_LANG,
        }
        response = self.client.post(f"{API_BASE}/calls/start", headers=self._headers(), json=payload)
        response.raise_for_status()
        return response.json().get("id")

    def push_transcript(self, call_id: str, transcript: str) -> None:
        if not transcript.strip():
            return
        payload = {
            "speaker": "agent",
            "text": transcript,
            "timestamp": 0,
            "source_lang": "en",
            "target_lang": TARGET_LANG,
        }
        response = self.client.post(
            f"{API_BASE}/calls/{call_id}/transcript",
            headers=self._headers(),
            json=payload,
        )
        response.raise_for_status()

    def end_and_analyze(self, call_id: str) -> None:
        end_response = self.client.post(
            f"{API_BASE}/calls/{call_id}/end",
            headers=self._headers(),
            json={},
        )
        end_response.raise_for_status()

        analyze_response = self.client.post(
            f"{API_BASE}/calls/{call_id}/analyze",
            headers=self._headers(),
            json={},
        )
        # analyze can fail if transcript empty; keep watcher resilient
        if analyze_response.status_code >= 400:
            logger.warning("Analyze skipped for call=%s status=%s", call_id, analyze_response.status_code)


class CallHandler(FileSystemEventHandler):
    def __init__(self, transcriber: Transcriber, api: SmartCallApi) -> None:
        self.transcriber = transcriber
        self.api = api

    def on_created(self, event) -> None:
        if event.is_directory:
            return
        if not event.src_path.endswith(".wav"):
            return

        wav_path = Path(event.src_path)
        try:
            self.process(wav_path)
        except Exception as exc:
            logger.exception("Error processing %s: %s", wav_path.name, exc)

    def process(self, wav_path: Path) -> None:
        done_flag = DONE_DIR / f"{wav_path.name}.done"
        if done_flag.exists():
            return

        if not wait_until_file_complete(wav_path):
            logger.warning("File not stable, skipping: %s", wav_path)
            return

        logger.info("New call file detected: %s", wav_path.name)
        normalized_wav = TMP_DIR / wav_path.name
        transcript_file = OUT_DIR / f"{wav_path.stem}.txt"
        archived_wav = PROCESSED_DIR / wav_path.name

        convert_audio_to_mono_16k(wav_path, normalized_wav)
        transcript = self.transcriber.transcribe_file(normalized_wav)
        transcript_file.write_text(transcript, encoding="utf-8")

        agent_id, customer_number = parse_agent_and_customer(wav_path.name)
        call_id = self.api.start_call(agent_id=agent_id, customer_number=customer_number)
        if not call_id:
            raise RuntimeError("Failed to create call in SmartCall API")

        self.api.push_transcript(call_id, transcript)
        self.api.end_and_analyze(call_id)

        shutil.copy2(wav_path, archived_wav)
        done_flag.write_text(
            json.dumps(
                {
                    "source": str(wav_path),
                    "normalized": str(normalized_wav),
                    "transcript_file": str(transcript_file),
                    "call_id": call_id,
                },
                ensure_ascii=True,
            ),
            encoding="utf-8",
        )

        normalized_wav.unlink(missing_ok=True)
        logger.info("Processed %s -> call_id=%s", wav_path.name, call_id)


def main() -> None:
    ensure_dirs()
    logger.info("Watching Asterisk directory: %s", WATCH_DIR)
    logger.info("SmartCall API: %s", API_BASE)

    transcriber = Transcriber()
    api = SmartCallApi()
    handler = CallHandler(transcriber=transcriber, api=api)

    observer = Observer()
    observer.schedule(handler, str(WATCH_DIR), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping bridge...")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()

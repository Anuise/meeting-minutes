"""`mm transcribe-submit` — Recording 轉成 Media 的行為。

沿用 `test_ingest.py` 的形狀：準備 fixture 目錄、執行一次子指令、
斷言檔案系統的結果與 stdout 的 JSON。ffmpeg 不是新接縫——容器裡裝了真的，
測試素材用它自己產一段極短的靜音，真的轉一次。
"""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import fixtures

MM = Path(__file__).resolve().parent.parent / "scripts" / "mm.py"

# Meeting slug 含空格與中文：參數以 argv list 傳、不經 shell 的證據
MEETING = "2026-08-05 平台會議"


def run_mm(*args):
    return subprocess.run(
        [sys.executable, str(MM), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def submit(root, meeting=MEETING):
    result = run_mm("transcribe-submit", meeting, "--root", str(root))
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def rawdata_dir(root, meeting=MEETING):
    target = root / "rawdata" / meeting
    target.mkdir(parents=True, exist_ok=True)
    return target


def media_dir(root, meeting=MEETING):
    return root / "media" / meeting


def media_files(root, meeting=MEETING):
    directory = media_dir(root, meeting)
    if not directory.is_dir():
        return set()
    return {
        path.relative_to(directory).as_posix()
        for path in directory.rglob("*")
        if path.is_file()
    }


def is_mp3(path):
    head = path.read_bytes()[:3]
    # ffmpeg 的 mp3 muxer 預設寫 ID3v2 標頭；沒有標頭時就是 frame sync
    return head == b"ID3" or head[0] == 0xFF


def test_recordings_become_media(tmp_path):
    raw = rawdata_dir(tmp_path)
    fixtures.write_silent_recording(raw / "morning.wav")
    fixtures.write_silent_recording(raw / "screen.mp4", video=True)

    payload = submit(tmp_path)

    transcoded = {entry["recording"]: entry["media"] for entry in payload["transcoded"]}
    assert set(transcoded) == {"morning.wav", "screen.mp4"}
    for recording, media in transcoded.items():
        target = media_dir(tmp_path) / media
        assert target.is_file(), f"{recording} 沒有產出 Media"
        assert target.stat().st_size > 0
        assert is_mp3(target), f"{media} 不是 mp3"


def test_media_filename_keeps_the_recording_extension(tmp_path):
    raw = rawdata_dir(tmp_path)
    fixtures.write_silent_recording(raw / "meeting.m4a")
    fixtures.write_silent_recording(raw / "meeting.mp4", video=True)

    payload = submit(tmp_path)

    # 同名不同格式的兩份錄音不會互相蓋掉
    assert {entry["media"] for entry in payload["transcoded"]} == {
        "meeting.m4a.mp3",
        "meeting.mp4.mp3",
    }
    assert media_files(tmp_path) == {"meeting.m4a.mp3", "meeting.mp4.mp3"}


def test_recordings_in_subdirectories_are_found(tmp_path):
    raw = rawdata_dir(tmp_path)
    (raw / "第一段").mkdir()
    fixtures.write_silent_recording(raw / "第一段" / "part1.wav")

    payload = submit(tmp_path)

    assert [entry["recording"] for entry in payload["transcoded"]] == ["第一段/part1.wav"]
    assert media_files(tmp_path) == {"第一段/part1.wav.mp3"}


def test_material_that_is_not_a_recording_is_left_alone(tmp_path):
    raw = rawdata_dir(tmp_path)
    fixtures.write_docx(raw / "minutes.docx", "上週待辦回顧")
    fixtures.write_png(raw / "whiteboard.png")
    fixtures.write_silent_recording(raw / "morning.wav")

    payload = submit(tmp_path)

    assert [entry["recording"] for entry in payload["transcoded"]] == ["morning.wav"]
    assert media_files(tmp_path) == {"morning.wav.mp3"}


def test_media_newer_than_its_recording_is_not_transcoded_again(tmp_path):
    raw = rawdata_dir(tmp_path)
    recording = raw / "morning.wav"
    fixtures.write_silent_recording(recording)

    submit(tmp_path)
    media = media_dir(tmp_path) / "morning.wav.mp3"
    os.utime(media, (media.stat().st_atime, recording.stat().st_mtime + 10))
    before = media.stat().st_mtime_ns

    payload = submit(tmp_path)

    assert payload["transcoded"] == []
    assert [entry["recording"] for entry in payload["skipped"]] == ["morning.wav"]
    assert media.stat().st_mtime_ns == before


def test_media_older_than_its_recording_is_transcoded_again(tmp_path):
    raw = rawdata_dir(tmp_path)
    recording = raw / "morning.wav"
    fixtures.write_silent_recording(recording)

    submit(tmp_path)
    media = media_dir(tmp_path) / "morning.wav.mp3"
    os.utime(media, (media.stat().st_atime, recording.stat().st_mtime - 10))

    payload = submit(tmp_path)

    assert [entry["recording"] for entry in payload["transcoded"]] == ["morning.wav"]
    assert media.stat().st_mtime > recording.stat().st_mtime


def test_one_broken_recording_does_not_stop_the_batch(tmp_path):
    raw = rawdata_dir(tmp_path)
    (raw / "broken.mp3").write_bytes(b"not really audio" * 100)
    fixtures.write_silent_recording(raw / "morning.wav")

    payload = submit(tmp_path)

    failed = {entry["recording"]: entry for entry in payload["failed"]}
    assert set(failed) == {"broken.mp3"}
    assert failed["broken.mp3"]["error"]

    assert [entry["recording"] for entry in payload["transcoded"]] == ["morning.wav"]
    # 半成品留著會被下一次的 mtime 判定當成轉好了
    assert media_files(tmp_path) == {"morning.wav.mp3"}


def snapshot(directory):
    return {
        str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def test_rawdata_is_never_written_to(tmp_path):
    raw = rawdata_dir(tmp_path)
    fixtures.write_silent_recording(raw / "morning.wav")
    fixtures.write_silent_recording(raw / "screen.mp4", video=True)
    (raw / "broken.mp3").write_bytes(b"not really audio" * 100)
    fixtures.write_docx(raw / "minutes.docx", "上週待辦回顧")

    before = snapshot(tmp_path / "rawdata")
    submit(tmp_path)

    assert snapshot(tmp_path / "rawdata") == before


def test_missing_meeting_exits_nonzero(tmp_path):
    (tmp_path / "rawdata").mkdir()

    result = run_mm(
        "transcribe-submit", "2026-01-01-nonexistent", "--root", str(tmp_path)
    )

    assert result.returncode != 0
    assert "2026-01-01-nonexistent" in result.stderr

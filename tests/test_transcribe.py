"""`mm transcribe-submit` — Recording 轉成 Media、送上 ASR Service 的行為。

兩個接縫：CLI 子行程（與 `test_ingest.py` 相同的形狀），以及 ASR Service 的
HTTP 邊界（`fake_asr` 起一個真的 server，靠環境變數把 CLI 指過去）。
ffmpeg 不是接縫——容器裡裝了真的，測試素材用它自己產一段極短的靜音，真的轉一次。
"""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import fixtures
import pytest
from fake_asr import FakeAsr

MM = Path(__file__).resolve().parent.parent / "scripts" / "mm.py"

# Meeting slug 含空格與中文：參數以 argv list 傳、不經 shell 的證據
MEETING = "2026-08-05 平台會議"


@pytest.fixture
def asr():
    fake = FakeAsr().start()
    yield fake
    fake.stop()


def run_mm(*args, url=None):
    environment = dict(os.environ)
    environment.pop("MM_ASR_URL", None)
    if url:
        environment["MM_ASR_URL"] = url
    return subprocess.run(
        [sys.executable, str(MM), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
    )


def submit(root, asr, meeting=MEETING):
    result = run_mm("transcribe-submit", meeting, "--root", str(root), url=asr.url)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def fetch(root, asr, meeting=MEETING):
    result = run_mm("transcribe-fetch", meeting, "--root", str(root), url=asr.url)
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


def task_record(root, media_relative, meeting=MEETING):
    path = media_dir(root, meeting) / f"{media_relative}.task.json"
    return json.loads(path.read_text(encoding="utf-8"))


def is_mp3(path):
    head = path.read_bytes()[:3]
    # ffmpeg 的 mp3 muxer 預設寫 ID3v2 標頭；沒有標頭時就是 frame sync
    return head == b"ID3" or head[0] == 0xFF


# --- 轉檔 --------------------------------------------------------------------


def test_recordings_become_media(tmp_path, asr):
    raw = rawdata_dir(tmp_path)
    fixtures.write_silent_recording(raw / "morning.wav")
    fixtures.write_silent_recording(raw / "screen.mp4", video=True)

    payload = submit(tmp_path, asr)

    submitted = {entry["recording"]: entry for entry in payload["submitted"]}
    assert set(submitted) == {"morning.wav", "screen.mp4"}
    for recording, entry in submitted.items():
        assert entry["transcoded"] is True
        target = media_dir(tmp_path) / entry["media"]
        assert target.is_file(), f"{recording} 沒有產出 Media"
        assert target.stat().st_size > 0
        assert is_mp3(target), f"{entry['media']} 不是 mp3"


def test_media_filename_keeps_the_recording_extension(tmp_path, asr):
    raw = rawdata_dir(tmp_path)
    fixtures.write_silent_recording(raw / "meeting.m4a")
    fixtures.write_silent_recording(raw / "meeting.mp4", video=True)

    payload = submit(tmp_path, asr)

    # 同名不同格式的兩份錄音不會互相蓋掉
    assert {entry["media"] for entry in payload["submitted"]} == {
        "meeting.m4a.mp3",
        "meeting.mp4.mp3",
    }


def test_recordings_in_subdirectories_are_found(tmp_path, asr):
    raw = rawdata_dir(tmp_path)
    (raw / "第一段").mkdir()
    fixtures.write_silent_recording(raw / "第一段" / "part1.wav")

    payload = submit(tmp_path, asr)

    assert [entry["recording"] for entry in payload["submitted"]] == ["第一段/part1.wav"]
    assert (media_dir(tmp_path) / "第一段" / "part1.wav.mp3").is_file()


def test_material_that_is_not_a_recording_is_left_alone(tmp_path, asr):
    raw = rawdata_dir(tmp_path)
    fixtures.write_docx(raw / "minutes.docx", "上週待辦回顧")
    fixtures.write_png(raw / "whiteboard.png")
    fixtures.write_silent_recording(raw / "morning.wav")

    payload = submit(tmp_path, asr)

    assert [entry["recording"] for entry in payload["submitted"]] == ["morning.wav"]
    assert media_files(tmp_path) == {"morning.wav.mp3", "morning.wav.mp3.task.json"}


def test_media_newer_than_its_recording_is_not_transcoded_again(tmp_path, asr):
    raw = rawdata_dir(tmp_path)
    recording = raw / "morning.wav"
    fixtures.write_silent_recording(recording)

    submit(tmp_path, asr)
    media = media_dir(tmp_path) / "morning.wav.mp3"
    # 記錄刪掉、Media 留著：重跑該重新送出，但不該重新轉檔
    (media_dir(tmp_path) / "morning.wav.mp3.task.json").unlink()
    os.utime(media, (media.stat().st_atime, recording.stat().st_mtime + 10))
    before = media.stat().st_mtime_ns

    payload = submit(tmp_path, asr)

    assert [entry["transcoded"] for entry in payload["submitted"]] == [False]
    assert media.stat().st_mtime_ns == before


def test_media_older_than_its_recording_is_transcoded_again(tmp_path, asr):
    raw = rawdata_dir(tmp_path)
    recording = raw / "morning.wav"
    fixtures.write_silent_recording(recording)

    submit(tmp_path, asr)
    media = media_dir(tmp_path) / "morning.wav.mp3"
    (media_dir(tmp_path) / "morning.wav.mp3.task.json").unlink()
    os.utime(media, (media.stat().st_atime, recording.stat().st_mtime - 10))

    payload = submit(tmp_path, asr)

    assert [entry["transcoded"] for entry in payload["submitted"]] == [True]
    assert media.stat().st_mtime > recording.stat().st_mtime


def test_one_broken_recording_does_not_stop_the_batch(tmp_path, asr):
    raw = rawdata_dir(tmp_path)
    (raw / "broken.mp3").write_bytes(b"not really audio" * 100)
    fixtures.write_silent_recording(raw / "morning.wav")

    payload = submit(tmp_path, asr)

    failed = {entry["recording"]: entry for entry in payload["failed"]}
    assert set(failed) == {"broken.mp3"}
    assert failed["broken.mp3"]["error"]

    assert [entry["recording"] for entry in payload["submitted"]] == ["morning.wav"]
    # 半成品留著會被下一次的 mtime 判定當成轉好了
    assert media_files(tmp_path) == {"morning.wav.mp3", "morning.wav.mp3.task.json"}


# --- 上傳 --------------------------------------------------------------------


def test_media_is_uploaded_and_the_task_is_recorded(tmp_path, asr):
    raw = rawdata_dir(tmp_path)
    fixtures.write_silent_recording(raw / "morning.wav")

    payload = submit(tmp_path, asr)

    assert len(asr.uploads) == 1
    upload = asr.uploads[0]
    assert upload["language"] == "Chinese"
    assert upload["filename"] == "morning.wav.mp3"
    assert upload["size"] == (media_dir(tmp_path) / "morning.wav.mp3").stat().st_size

    entry = payload["submitted"][0]
    assert entry["task"] == upload["task"]
    record = task_record(tmp_path, "morning.wav.mp3")
    assert record["task"] == upload["task"]
    assert record["recording"] == "morning.wav"
    assert record["language"] == "Chinese"


def test_a_recording_already_submitted_is_not_sent_again(tmp_path, asr):
    raw = rawdata_dir(tmp_path)
    fixtures.write_silent_recording(raw / "morning.wav")
    first = submit(tmp_path, asr)

    payload = submit(tmp_path, asr)

    assert payload["submitted"] == []
    assert [entry["task"] for entry in payload["skipped"]] == [
        first["submitted"][0]["task"]
    ]
    # 佇列裡不會出現兩份一樣的任務
    assert len(asr.uploads) == 1


def test_a_completed_task_is_not_sent_again(tmp_path, asr):
    raw = rawdata_dir(tmp_path)
    fixtures.write_silent_recording(raw / "morning.wav")
    first = submit(tmp_path, asr)
    asr.finish(first["submitted"][0]["task"], [(0.0, 12.0, "早上的討論")])

    payload = submit(tmp_path, asr)

    assert [entry["status"] for entry in payload["skipped"]] == ["done"]
    assert len(asr.uploads) == 1


def test_upload_is_blocked_when_the_service_is_full(tmp_path, asr):
    raw = rawdata_dir(tmp_path)
    fixtures.write_silent_recording(raw / "morning.wav")
    asr.storage["free_bytes"] = 128

    payload = submit(tmp_path, asr)

    assert payload["submitted"] == []
    assert "剩" in payload["failed"][0]["error"]
    assert asr.uploads == []
    assert media_files(tmp_path) == {"morning.wav.mp3"}


def test_upload_is_blocked_when_the_media_exceeds_the_single_file_limit(tmp_path, asr):
    raw = rawdata_dir(tmp_path)
    fixtures.write_silent_recording(raw / "morning.wav")
    asr.storage["max_upload_mb"] = 0

    payload = submit(tmp_path, asr)

    assert payload["submitted"] == []
    assert "單檔上限" in payload["failed"][0]["error"]
    assert asr.uploads == []


def test_remaining_space_is_reported(tmp_path, asr):
    raw = rawdata_dir(tmp_path)
    fixtures.write_silent_recording(raw / "morning.wav")

    payload = submit(tmp_path, asr)

    assert payload["storage"]["free_bytes"] == asr.storage["free_bytes"]
    assert payload["storage"]["max_upload_mb"] == asr.storage["max_upload_mb"]


def test_missing_service_url_exits_nonzero(tmp_path, asr):
    raw = rawdata_dir(tmp_path)
    fixtures.write_silent_recording(raw / "morning.wav")

    result = run_mm("transcribe-submit", MEETING, "--root", str(tmp_path))

    assert result.returncode != 0
    assert "MM_ASR_URL" in result.stderr
    assert asr.uploads == []


# --- 取回 --------------------------------------------------------------------


def notes_dir(root, meeting=MEETING):
    return root / "notes" / meeting


def submit_one(tmp_path, asr, name="morning.wav"):
    """送出一份 Recording，回傳它的 Transcription Task id。"""
    fixtures.write_silent_recording(rawdata_dir(tmp_path) / name)
    return submit(tmp_path, asr)["submitted"][0]["task"]


def test_a_finished_task_becomes_a_note(tmp_path, asr):
    task = submit_one(tmp_path, asr)
    asr.finish(
        task,
        [(0.0, 90.0, "第一段的討論內容"), (90.0, 185.5, "第二段的討論內容")],
        duration_sec=185.5,
    )

    payload = fetch(tmp_path, asr)

    assert payload["pending"] == []
    entry = payload["fetched"][0]
    assert entry == {
        "recording": "morning.wav",
        "task": task,
        "note": "morning.wav.md",
        "chunks": 2,
        "failed_chunks": 0,
    }

    note = (notes_dir(tmp_path) / "morning.wav.md").read_text(encoding="utf-8")
    # 開頭標明來源與任務，使用者看到 source 引用時查得回原始錄音
    assert "# morning.wav（語音轉文字）" in note
    assert f"- 來源：rawdata/{MEETING}/morning.wav" in note
    assert f"ASR Service task {task}" in note
    assert "語言 Chinese" in note
    assert "時長 186 秒" in note
    assert "2 段" in note
    # 每個分段一個帶起訖時間碼的小節
    assert "## 00:00:00–00:01:30" in note
    assert "## 00:01:30–00:03:05" in note
    assert "第一段的討論內容" in note
    assert "第二段的討論內容" in note


def test_an_unfinished_task_reports_progress_and_writes_no_note(tmp_path, asr):
    task = submit_one(tmp_path, asr)
    asr.progress(task, completed=3, total=8, pct=37.5)

    payload = fetch(tmp_path, asr)

    assert payload["fetched"] == []
    assert payload["pending"] == [
        {
            "recording": "morning.wav",
            "task": task,
            "status": "processing",
            "progress_pct": 37.5,
            "completed_chunks": 3,
            "total_chunks": 8,
        }
    ]
    assert not notes_dir(tmp_path).exists()


def test_a_note_edited_by_hand_is_not_overwritten(tmp_path, asr):
    task = submit_one(tmp_path, asr)
    asr.finish(task, [(0.0, 30.0, "機器轉出來的內容")])
    fetch(tmp_path, asr)

    note = notes_dir(tmp_path) / "morning.wav.md"
    note.write_text("我自己校對過的逐字稿\n", encoding="utf-8")
    record_file = media_dir(tmp_path) / "morning.wav.mp3.task.json"
    os.utime(note, (note.stat().st_atime, record_file.stat().st_mtime + 10))

    payload = fetch(tmp_path, asr)

    assert payload["fetched"] == []
    assert [entry["note"] for entry in payload["skipped"]] == ["morning.wav.md"]
    assert note.read_text(encoding="utf-8") == "我自己校對過的逐字稿\n"


def test_a_recording_in_a_subdirectory_keeps_its_path_in_the_note(tmp_path, asr):
    raw = rawdata_dir(tmp_path)
    (raw / "第一段").mkdir()
    fixtures.write_silent_recording(raw / "第一段" / "part1.wav")
    task = submit(tmp_path, asr)["submitted"][0]["task"]
    asr.finish(task, [(0.0, 12.0, "子資料夾裡的錄音")])

    payload = fetch(tmp_path, asr)

    assert payload["fetched"][0]["note"] == "第一段/part1.wav.md"
    note = notes_dir(tmp_path) / "第一段" / "part1.wav.md"
    assert f"- 來源：rawdata/{MEETING}/第一段/part1.wav" in note.read_text(
        encoding="utf-8"
    )


def test_fetch_before_submit_exits_nonzero(tmp_path, asr):
    rawdata_dir(tmp_path)

    result = run_mm("transcribe-fetch", MEETING, "--root", str(tmp_path), url=asr.url)

    assert result.returncode != 0
    assert MEETING in result.stderr


# --- 不變式 ------------------------------------------------------------------


def snapshot(directory):
    return {
        str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def test_rawdata_is_never_written_to(tmp_path, asr):
    raw = rawdata_dir(tmp_path)
    fixtures.write_silent_recording(raw / "morning.wav")
    fixtures.write_silent_recording(raw / "screen.mp4", video=True)
    (raw / "broken.mp3").write_bytes(b"not really audio" * 100)
    fixtures.write_docx(raw / "minutes.docx", "上週待辦回顧")

    before = snapshot(tmp_path / "rawdata")
    submit(tmp_path, asr)

    assert snapshot(tmp_path / "rawdata") == before


def test_missing_meeting_exits_nonzero(tmp_path, asr):
    (tmp_path / "rawdata").mkdir()

    result = run_mm(
        "transcribe-submit",
        "2026-01-01-nonexistent",
        "--root",
        str(tmp_path),
        url=asr.url,
    )

    assert result.returncode != 0
    assert "2026-01-01-nonexistent" in result.stderr

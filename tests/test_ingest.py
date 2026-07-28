"""`mm ingest` — Raw Material 轉成 Note 的行為。

沿用 `test_init.py` 的形狀：準備 fixture 目錄、執行一次子指令、
斷言檔案系統的結果與 stdout 的 JSON。
"""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import fixtures

MM = Path(__file__).resolve().parent.parent / "scripts" / "mm.py"

MEETING = "2026-07-28-project-weekly"

# 前四個是 ADR-0003 點名的副檔名；.flac 只有寫死清單接得到（容器內 mime 表沒有它）；
# .mpeg 反過來只有 mimetypes 接得到。兩條路徑都要有測試。
AUDIO_FILENAMES = (
    "recording.mp3",
    "recording.m4a",
    "recording.wav",
    "recording.mp4",
    "recording.flac",
    "recording.mpeg",
)

# .png 在寫死清單裡，.ico 只有 mimetypes 認得。
IMAGE_FILENAMES = ("whiteboard.png", "logo.ico")


def run_mm(*args):
    return subprocess.run(
        [sys.executable, str(MM), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def ingest(root, meeting=MEETING):
    result = run_mm("ingest", meeting, "--root", str(root))
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def rawdata_dir(root, meeting=MEETING):
    target = root / "rawdata" / meeting
    target.mkdir(parents=True, exist_ok=True)
    return target


def notes_dir(root, meeting=MEETING):
    return root / "notes" / meeting


# 每個支援格式一個小 fixture，值是轉出來的 Note 裡必須看得到的字串。
def write_every_supported_format(directory):
    fixtures.write_pdf(directory / "agenda.pdf", "Quarterly review agenda")
    fixtures.write_docx(directory / "minutes.docx", "上週待辦回顧")
    fixtures.write_pptx(directory / "slides.pptx", "架構調整")
    fixtures.write_xlsx(directory / "budget.xlsx", "維運費用")
    fixtures.write_html(directory / "page.html", "客戶回饋")
    fixtures.write_csv(directory / "attendees.csv", "王小明")
    fixtures.write_json(directory / "config.json", "先加上快取層")
    fixtures.write_xml(directory / "notes.xml", "決議事項")
    fixtures.write_epub(directory / "handbook.epub", "會議守則")
    fixtures.write_msg(directory / "mail.msg", "王小明", "場地確認", "會議室已借到")

    return {
        "agenda.pdf": "Quarterly review agenda",
        "minutes.docx": "上週待辦回顧",
        "slides.pptx": "架構調整",
        "budget.xlsx": "維運費用",
        "page.html": "客戶回饋",
        "attendees.csv": "王小明",
        "config.json": "先加上快取層",
        "notes.xml": "決議事項",
        "handbook.epub": "會議守則",
        "mail.msg": "會議室已借到",
    }


def test_every_supported_format_becomes_a_note(tmp_path):
    expected = write_every_supported_format(rawdata_dir(tmp_path))

    payload = ingest(tmp_path)

    ingested = {entry["raw"]: entry["note"] for entry in payload["ingested"]}
    assert set(ingested) == set(expected)
    for raw, marker in expected.items():
        note = notes_dir(tmp_path) / ingested[raw]
        assert note.is_file(), f"{raw} 沒有產出 Note"
        assert marker in note.read_text(encoding="utf-8")


def test_note_filename_keeps_the_raw_material_filename(tmp_path):
    write_every_supported_format(rawdata_dir(tmp_path))

    payload = ingest(tmp_path)

    for entry in payload["ingested"]:
        # 副檔名留在 Note 檔名裡，slides.pdf 與 slides.docx 才不會撞在一起
        assert entry["note"] == f"{entry['raw']}.md"


def test_files_in_subdirectories_are_ingested_too(tmp_path):
    raw = rawdata_dir(tmp_path)
    (raw / "photos").mkdir()
    fixtures.write_docx(raw / "photos" / "minutes.docx", "白板照旁的手寫記錄")

    payload = ingest(tmp_path)

    assert [entry["raw"] for entry in payload["ingested"]] == ["photos/minutes.docx"]
    note = notes_dir(tmp_path) / "photos" / "minutes.docx.md"
    assert "白板照旁的手寫記錄" in note.read_text(encoding="utf-8")


def test_audio_is_reported_as_unsupported_with_a_transcript_hint(tmp_path):
    raw = rawdata_dir(tmp_path)
    for filename in AUDIO_FILENAMES:
        (raw / filename).write_bytes(b"not really audio")
    fixtures.write_docx(raw / "minutes.docx", "上週待辦回顧")

    payload = ingest(tmp_path)

    unsupported = {entry["raw"]: entry for entry in payload["unsupported"]}
    assert set(unsupported) == set(AUDIO_FILENAMES)
    for entry in unsupported.values():
        assert "逐字稿" in entry["message"]

    # 錄音被跳過，但不影響其他素材，也不留下 Note
    assert [entry["raw"] for entry in payload["ingested"]] == ["minutes.docx"]
    assert {path.name for path in notes_dir(tmp_path).iterdir()} == {"minutes.docx.md"}


def test_images_are_reported_as_unsupported_and_leave_no_note(tmp_path):
    raw = rawdata_dir(tmp_path)
    fixtures.write_png(raw / "whiteboard.png")
    fixtures.write_png(raw / "logo.ico")  # 內容不重要，這裡測的是副檔名的判定
    fixtures.write_docx(raw / "minutes.docx", "上週待辦回顧")

    payload = ingest(tmp_path)

    unsupported = {entry["raw"]: entry for entry in payload["unsupported"]}
    assert set(unsupported) == set(IMAGE_FILENAMES)
    for entry in unsupported.values():
        assert "圖片" in entry["message"]

    # 空的 Note 比沒有 Note 更糟：使用者會以為照片的內容進去了
    assert [entry["raw"] for entry in payload["ingested"]] == ["minutes.docx"]
    assert {path.name for path in notes_dir(tmp_path).iterdir()} == {"minutes.docx.md"}


def test_note_newer_than_its_raw_material_is_skipped(tmp_path):
    raw = rawdata_dir(tmp_path)
    fixtures.write_docx(raw / "minutes.docx", "第一版")

    ingest(tmp_path)
    note = notes_dir(tmp_path) / "minutes.docx.md"
    note.write_text("我自己改過的 Note\n", encoding="utf-8")
    os.utime(note, (note.stat().st_atime, (raw / "minutes.docx").stat().st_mtime + 10))

    payload = ingest(tmp_path)

    assert payload["ingested"] == []
    skipped = {entry["raw"]: entry for entry in payload["skipped"]}
    assert skipped["minutes.docx"]["note"] == "minutes.docx.md"
    assert note.read_text(encoding="utf-8") == "我自己改過的 Note\n"


def test_note_older_than_its_raw_material_is_converted_again(tmp_path):
    raw = rawdata_dir(tmp_path)
    fixtures.write_docx(raw / "minutes.docx", "第一版")

    ingest(tmp_path)
    note = notes_dir(tmp_path) / "minutes.docx.md"

    fixtures.write_docx(raw / "minutes.docx", "第二版")
    os.utime(note, (note.stat().st_atime, note.stat().st_mtime - 10))

    payload = ingest(tmp_path)

    assert [entry["raw"] for entry in payload["ingested"]] == ["minutes.docx"]
    assert "第二版" in note.read_text(encoding="utf-8")


def test_one_broken_file_does_not_stop_the_batch(tmp_path):
    raw = rawdata_dir(tmp_path)
    fixtures.write_broken_pdf(raw / "broken.pdf")
    fixtures.write_docx(raw / "minutes.docx", "上週待辦回顧")
    fixtures.write_html(raw / "page.html", "客戶回饋")

    payload = ingest(tmp_path)

    failed = {entry["raw"]: entry for entry in payload["failed"]}
    assert set(failed) == {"broken.pdf"}
    assert failed["broken.pdf"]["error"]

    assert sorted(entry["raw"] for entry in payload["ingested"]) == [
        "minutes.docx",
        "page.html",
    ]
    assert not (notes_dir(tmp_path) / "broken.pdf.md").exists()


def snapshot(directory):
    return {
        str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def test_rawdata_is_never_written_to(tmp_path):
    raw = rawdata_dir(tmp_path)
    write_every_supported_format(raw)
    fixtures.write_broken_pdf(raw / "broken.pdf")
    for filename in AUDIO_FILENAMES:
        (raw / filename).write_bytes(b"not really audio")
    for filename in IMAGE_FILENAMES:
        fixtures.write_png(raw / filename)

    before = snapshot(tmp_path / "rawdata")
    ingest(tmp_path)

    assert snapshot(tmp_path / "rawdata") == before


def test_missing_meeting_exits_nonzero(tmp_path):
    (tmp_path / "rawdata").mkdir()

    result = run_mm("ingest", "2026-01-01-nonexistent", "--root", str(tmp_path))

    assert result.returncode != 0
    assert "2026-01-01-nonexistent" in result.stderr

"""`mm list` — 每個 Meeting 走到哪一步、有哪些模板可用。

沿用同一形狀：準備 fixture 目錄、執行一次子指令、斷言 stdout 的 JSON。
"""

import json
import subprocess
import sys
from pathlib import Path

MM = Path(__file__).resolve().parent.parent / "scripts" / "mm.py"

STAGES = ("raw_material", "note", "minutes_record", "deliverable")


def run_mm(*args):
    return subprocess.run(
        [sys.executable, str(MM), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def listing(root):
    result = run_mm("list", "--root", str(root))
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def meetings_by_slug(root):
    return {entry["slug"]: entry for entry in listing(root)["meetings"]}


def write(path, content="內容\n"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_raw_material(root, slug):
    write(root / "rawdata" / slug / "agenda.md")


def make_note(root, slug):
    write(root / "notes" / slug / "agenda.md.md")


def make_record(root, slug):
    write(root / "records" / f"{slug}.yaml", "meta: {}\n")


def make_deliverable(root, slug):
    write(root / "output" / slug / "minutes.md")


# 每種完成度一個 Meeting，一次列出來才看得出彼此的狀態沒有互相污染
def make_every_completeness(root):
    make_raw_material(root, "01-raw-only")

    make_raw_material(root, "02-note-no-record")
    make_note(root, "02-note-no-record")

    make_raw_material(root, "03-record-no-deliverable")
    make_note(root, "03-record-no-deliverable")
    make_record(root, "03-record-no-deliverable")

    make_raw_material(root, "04-complete")
    make_note(root, "04-complete")
    make_record(root, "04-complete")
    make_deliverable(root, "04-complete")

    (root / "rawdata" / "05-empty").mkdir(parents=True)

    return {
        "01-raw-only": (True, False, False, False),
        "02-note-no-record": (True, True, False, False),
        "03-record-no-deliverable": (True, True, True, False),
        "04-complete": (True, True, True, True),
        "05-empty": (False, False, False, False),
    }


def test_every_completeness_reports_the_right_stages(tmp_path):
    expected = make_every_completeness(tmp_path)

    meetings = meetings_by_slug(tmp_path)

    assert set(meetings) == set(expected)
    for slug, stages in expected.items():
        actual = tuple(meetings[slug][stage] for stage in STAGES)
        assert actual == stages, f"{slug} 的階段狀態不對"


def test_meetings_are_sorted_by_slug(tmp_path):
    for slug in ("2026-07-28-weekly", "2026-01-05-kickoff", "2026-03-11-review"):
        make_raw_material(tmp_path, slug)

    slugs = [entry["slug"] for entry in listing(tmp_path)["meetings"]]

    assert slugs == [
        "2026-01-05-kickoff",
        "2026-03-11-review",
        "2026-07-28-weekly",
    ]


def test_meeting_without_rawdata_directory_is_still_listed(tmp_path):
    # 使用者刪掉 rawdata/ 或只拿到別人給的 Note，這場 Meeting 不能就這樣消失
    make_note(tmp_path, "note-only")
    make_record(tmp_path, "record-only")
    make_deliverable(tmp_path, "deliverable-only")

    meetings = meetings_by_slug(tmp_path)

    assert set(meetings) == {"note-only", "record-only", "deliverable-only"}
    assert meetings["note-only"]["raw_material"] is False
    assert meetings["note-only"]["note"] is True
    assert meetings["record-only"]["minutes_record"] is True
    assert meetings["deliverable-only"]["deliverable"] is True


def test_files_in_subdirectories_count_as_content(tmp_path):
    write(tmp_path / "rawdata" / "nested" / "photos" / "board.md")

    assert meetings_by_slug(tmp_path)["nested"]["raw_material"] is True


def test_empty_skeleton_lists_no_meetings(tmp_path):
    for relative in ("rawdata", "notes", "records", "output"):
        (tmp_path / relative).mkdir()

    assert listing(tmp_path)["meetings"] == []


def test_missing_skeleton_is_not_an_error(tmp_path):
    payload = listing(tmp_path)

    assert payload["meetings"] == []
    assert payload["schemas"] == []
    assert payload["markdown_templates"] == []
    assert payload["docx_templates"] == []


def test_available_templates_are_listed(tmp_path):
    write(tmp_path / "templates/schema/default.yaml", "name: default\n")
    write(tmp_path / "templates/schema/acceptance.yaml", "name: acceptance\n")
    write(tmp_path / "templates/markdown/default.md.j2", "# {{ meta.title }}\n")
    (tmp_path / "templates/docx").mkdir(parents=True)
    (tmp_path / "templates/docx/client-a.docx").write_bytes(b"PK\x03\x04")
    # Docx Source 還沒打洞，不能拿來渲染，所以不算在可用模板裡
    write(tmp_path / "templates/docx-source/client-a.docx", "尚未打洞")
    # 這三個不是模板，交給 render 只會炸掉
    write(tmp_path / "templates/schema/README.md", "怎麼寫 schema\n")
    write(tmp_path / "templates/markdown/.gitkeep", "")
    (tmp_path / "templates/docx/~$client-a.docx").write_bytes(b"word lock file")

    payload = listing(tmp_path)

    assert payload["schemas"] == ["acceptance.yaml", "default.yaml"]
    assert payload["markdown_templates"] == ["default.md.j2"]
    assert payload["docx_templates"] == ["client-a.docx"]


def test_init_output_is_listed_as_available_templates(tmp_path):
    result = run_mm("init", "--root", str(tmp_path))
    assert result.returncode == 0, result.stderr

    payload = listing(tmp_path)

    assert payload["schemas"] == ["default.yaml"]
    assert payload["markdown_templates"] == ["default.md.j2"]
    assert payload["docx_templates"] == ["default.docx"]
    assert payload["meetings"] == []

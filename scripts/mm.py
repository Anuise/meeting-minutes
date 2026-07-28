#!/usr/bin/env python3
"""meeting-minutes 的唯一程式進入點。

吃 argv、把結構化結果以 JSON 印到 stdout、錯誤走 exit code、完全非互動。
所有選單、確認、判斷與模型呼叫都留在 skill（agent）端。
"""

import argparse
import json
import mimetypes
import sys
from pathlib import Path

VERSION = "0.1.0"

DIRECTORIES = (
    "rawdata",
    "notes",
    "records",
    "output",
    "templates/schema",
    "templates/markdown",
    "templates/docx",
    "templates/docx-source",
)


DEFAULT_SCHEMA = """\
# Default Minutes Schema：正式會議記錄型。
# 決定 Minutes Record 有哪些欄位。可以複製一份再改，做成其他會議型態的 schema。

name: default
label: 正式會議記錄

meta:
  - { key: title, label: 會議名稱, type: text }
  - { key: datetime, label: 日期時間, type: datetime }
  - { key: location, label: 地點, type: text }
  - { key: chair, label: 主席, type: text }
  - { key: recorder, label: 記錄人, type: text }
  - { key: attendees, label: 出席者, type: people }
  - { key: absentees, label: 缺席者, type: people }

body:
  - key: topics
    label: 議題
    type: list
    fields:
      - { key: title, label: 題目, type: text }
      - { key: discussion, label: 討論摘要, type: text }
      # 決議巢狀在議題底下，保留「哪條決議屬於哪個題目」的關係
      - key: resolutions
        label: 決議
        type: list
        fields:
          - { key: text, label: 決議內容, type: text }
          - { key: source, label: 來源, type: source }

  - key: action_items
    label: 待辦事項
    type: list
    fields:
      - { key: task, label: 事項, type: text }
      - { key: owner, label: 負責人, type: text }
      - { key: due, label: 期限, type: date }
      - { key: source, label: 來源, type: source }

  - { key: next_meeting, label: 下次會議, type: text }
"""

DEFAULT_MARKDOWN_TEMPLATE = """\
# {{ meta.title or '未提及' }}

| 項目 | 內容 |
| --- | --- |
| 日期時間 | {{ meta.datetime or '未提及' }} |
| 地點 | {{ meta.location or '未提及' }} |
| 主席 | {{ meta.chair or '未提及' }} |
| 記錄人 | {{ meta.recorder or '未提及' }} |
| 出席者 | {{ meta.attendees | default([], true) | join('、') or '未提及' }} |
| 缺席者 | {{ meta.absentees | default([], true) | join('、') or '未提及' }} |

## 議題
{% for topic in topics | default([], true) %}
### {{ loop.index }}. {{ topic.title or '未提及' }}

{{ topic.discussion or '未提及' }}

決議：
{%- for resolution in topic.resolutions | default([], true) %}
- {{ resolution.text or '未提及' }}（來源：{{ resolution.source or '未提及' }}）
{%- else %}
- 未提及
{%- endfor %}
{% else %}
未提及
{% endfor %}
## 待辦事項

| 事項 | 負責人 | 期限 | 來源 |
| --- | --- | --- | --- |
{%- for item in action_items | default([], true) %}
| {{ item.task or '未提及' }} | {{ item.owner or '未提及' }} | \
{{ item.due or '未提及' }} | {{ item.source or '未提及' }} |
{%- else %}
| 未提及 | 未提及 | 未提及 | 未提及 |
{%- endfor %}

## 下次會議

{{ next_meeting or '未提及' }}
"""

DOCX_META_ROWS = (
    ("日期時間", "{{ meta.datetime or '未提及' }}"),
    ("地點", "{{ meta.location or '未提及' }}"),
    ("主席", "{{ meta.chair or '未提及' }}"),
    ("記錄人", "{{ meta.recorder or '未提及' }}"),
    ("出席者", "{{ meta.attendees | default([], true) | join('、') or '未提及' }}"),
    ("缺席者", "{{ meta.absentees | default([], true) | join('、') or '未提及' }}"),
)

DOCX_ACTION_COLUMNS = (
    ("事項", "{{ item.task or '未提及' }}"),
    ("負責人", "{{ item.owner or '未提及' }}"),
    ("期限", "{{ item.due or '未提及' }}"),
    ("來源", "{{ item.source or '未提及' }}"),
)


def write_default_docx(target):
    """產生一份已標上 Jinja2 變數、能被 docxtpl 直接渲染的 default Docx Template。"""
    from docx import Document

    document = Document()
    document.add_paragraph("{{ meta.title or '未提及' }}", style="Title")

    meta_table = document.add_table(rows=0, cols=2)
    meta_table.style = "Table Grid"
    for label, expression in DOCX_META_ROWS:
        cells = meta_table.add_row().cells
        cells[0].text = label
        cells[1].text = expression

    document.add_heading("議題", level=1)
    document.add_paragraph("{%p for topic in topics | default([], true) %}")
    document.add_heading("{{ loop.index }}. {{ topic.title or '未提及' }}", level=2)
    document.add_paragraph("{{ topic.discussion or '未提及' }}")
    document.add_paragraph(
        "{%p for resolution in topic.resolutions | default([], true) %}"
    )
    document.add_paragraph(
        "決議：{{ resolution.text or '未提及' }}"
        "（來源：{{ resolution.source or '未提及' }}）",
        style="List Bullet",
    )
    document.add_paragraph("{%p endfor %}")
    document.add_paragraph("{%p endfor %}")

    document.add_heading("待辦事項", level=1)
    action_table = document.add_table(rows=1, cols=len(DOCX_ACTION_COLUMNS))
    action_table.style = "Table Grid"
    header = action_table.rows[0].cells
    for index, (label, _) in enumerate(DOCX_ACTION_COLUMNS):
        header[index].text = label
    action_table.add_row().cells[0].text = (
        "{%tr for item in action_items | default([], true) %}"
    )
    repeated_row = action_table.add_row().cells
    for index, (_, expression) in enumerate(DOCX_ACTION_COLUMNS):
        repeated_row[index].text = expression
    action_table.add_row().cells[0].text = "{%tr endfor %}"

    document.add_heading("下次會議", level=1)
    document.add_paragraph("{{ next_meeting or '未提及' }}")

    document.save(str(target))


def write_text(content):
    return lambda target: target.write_text(content, encoding="utf-8")


# 每個 default 檔案配一個 writer。docx 得用程式產生，其餘是固定文字。
SEEDS = (
    ("templates/schema/default.yaml", write_text(DEFAULT_SCHEMA)),
    ("templates/markdown/default.md.j2", write_text(DEFAULT_MARKDOWN_TEMPLATE)),
    ("templates/docx/default.docx", write_default_docx),
)


def cmd_init(args):
    """建立骨架與 default 模板。已存在的一律跳過，絕不覆蓋使用者改過的內容。"""
    root = Path(args.root)
    created = []
    skipped = []

    for relative in DIRECTORIES:
        target = root / relative
        if target.is_dir():
            skipped.append(relative)
        else:
            target.mkdir(parents=True)
            created.append(relative)

    for relative, write in SEEDS:
        target = root / relative
        if target.exists():
            skipped.append(relative)
        else:
            write(target)
            created.append(relative)

    return {"root": str(root), "created": created, "skipped": skipped}


class CommandError(Exception):
    """使用者能修正的錯誤：訊息走 stderr、走非零 exit code。"""

    EXIT_CODE = 1  # 2 是 argparse 的用法錯誤，留給它


# ADR-0003：不收音訊、影片。ADR-0005：不收圖片。
# 兩份清單是地板——寫死才不會隨基底映像的 mime 表版本漂移；mimetypes 只做補漏。
AUDIO_SUFFIXES = frozenset(
    {
        ".mp3", ".m4a", ".m4b", ".wav", ".flac", ".aac", ".ogg", ".opus",
        ".wma", ".aiff", ".amr",
        ".mp4", ".m4v", ".mov", ".mkv", ".avi", ".webm", ".wmv", ".flv",
    }
)
IMAGE_SUFFIXES = frozenset(
    {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff", ".heic"}
)

AUDIO_MESSAGE = "不支援音訊與影片。請先自行轉成逐字稿，再把逐字稿放進 rawdata/。"
IMAGE_MESSAGE = (
    "不轉圖片：容器內沒有文字辨識能力，轉出來只會是空的 Note。"
    "照片上的內容需要進會議記錄的話，請自行補一份文字說明放進 rawdata/。"
)


def unsupported_message(raw):
    """回傳「這個檔案為什麼不轉」；該轉的回 None。"""
    suffix = raw.suffix.lower()
    if suffix in AUDIO_SUFFIXES:
        return AUDIO_MESSAGE
    if suffix in IMAGE_SUFFIXES:
        return IMAGE_MESSAGE

    mimetype = mimetypes.guess_type(raw.name)[0] or ""
    if mimetype.startswith(("audio/", "video/")):
        return AUDIO_MESSAGE
    if mimetype.startswith("image/"):
        return IMAGE_MESSAGE
    return None


def cmd_ingest(args):
    """把 rawdata/<meeting>/ 底下的檔案機械轉成 notes/<meeting>/ 的 markdown。

    只寫 notes/，絕不寫 rawdata/。單一檔案失敗不中斷整批，失敗項目集中回報。
    """
    from markitdown import MarkItDown

    root = Path(args.root)
    raw_root = root / "rawdata" / args.meeting
    if not raw_root.is_dir():
        raise CommandError(f"找不到 Raw Material 目錄：rawdata/{args.meeting}")
    note_root = root / "notes" / args.meeting

    markitdown = MarkItDown()
    ingested = []
    skipped = []
    unsupported = []
    failed = []

    for raw in sorted(path for path in raw_root.rglob("*") if path.is_file()):
        relative = raw.relative_to(raw_root).as_posix()

        message = unsupported_message(raw)
        if message:
            unsupported.append({"raw": relative, "message": message})
            continue

        # 副檔名留在 Note 檔名裡：看得出來源，且 slides.pdf 與 slides.docx 不會互相蓋掉
        note_relative = f"{relative}.md"
        note = note_root / note_relative
        # 只在 Note 確實比 Raw Material 新時跳過：時間戳打平時寧可多轉一次，
        # 也不要漏掉使用者剛換上去的素材。
        if note.exists() and note.stat().st_mtime > raw.stat().st_mtime:
            skipped.append({"raw": relative, "note": note_relative})
            continue

        try:
            markdown = markitdown.convert(str(raw)).markdown
        except Exception as error:
            failed.append({"raw": relative, "error": f"{type(error).__name__}: {error}"})
            continue

        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(markdown, encoding="utf-8")
        ingested.append({"raw": relative, "note": note_relative})

    return {
        "meeting": args.meeting,
        "rawdata": str(raw_root),
        "notes": str(note_root),
        "ingested": ingested,
        "skipped": skipped,
        "unsupported": unsupported,
        "failed": failed,
    }


PLANNED_SUBCOMMANDS = """\
尚未實作的子指令（各自由後續 ticket 帶進來）：
  render        把 Minutes Record 套模板變成 Deliverable
  check         列出空欄位、缺 source、模板變數對不到 schema
  scan-docx     列出 Docx Source 的段落與表格儲存格供打洞
  apply-docx    依對照表把 Docx Source 打洞成 Docx Template
  list          回報每個 Meeting 進行到哪一步
"""


def build_parser():
    parser = argparse.ArgumentParser(
        prog="mm",
        description="meeting-minutes CLI",
        epilog=PLANNED_SUBCOMMANDS,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"mm {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="建立資料夾骨架與 default 模板")
    init.add_argument("--root", default="/work", help="骨架的根目錄（預設 /work）")
    init.set_defaults(func=cmd_init)

    ingest = subparsers.add_parser("ingest", help="把 Raw Material 轉成 Note")
    ingest.add_argument("meeting", help="Meeting slug，即 rawdata/ 底下的資料夾名稱")
    ingest.add_argument("--root", default="/work", help="骨架的根目錄（預設 /work）")
    ingest.set_defaults(func=cmd_ingest)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        payload = args.func(args)
    except CommandError as error:
        sys.stderr.write(f"{error}\n")
        return CommandError.EXIT_CODE
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

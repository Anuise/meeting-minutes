---
name: mm-ingest
description: 把一場 Meeting 的 Raw Material（PDF、Word、PowerPoint、Excel、HTML、CSV、JSON、XML、EPub、Outlook 郵件、圖片）機械轉成 notes/<meeting>/ 底下的 Note。使用者把檔案原封不動丟進 rawdata/<meeting>/ 之後呼叫；重跑安全，沒變動的檔案會被跳過。錄音檔一律拒絕，請使用者先自行轉逐字稿。
---

# mm-ingest

純機械轉檔，不涉及理解，不呼叫模型。只寫 `notes/`，**絕不寫 `rawdata/`**——那是使用者唯一一份原始素材，而且不在版控裡（compose 也以唯讀掛載它）。

## 1. 先確認 Docker daemon

```bash
docker info
```

失敗就**停手**，原樣輸出這句話給使用者，不要繼續、不要重試、不要自動啟動任何背景程式，也不要退回宿主 Python：

> Docker daemon 沒有回應。請先啟動 Docker Desktop，等它的狀態變成 Running，再重新執行 mm-ingest。這個專案的所有程式都在容器內執行，宿主端不會安裝任何 Python 套件。

## 2. 決定要處理哪一場 Meeting

使用者沒指定就列出候選，讓他選，不要自己猜：

```bash
ls rawdata
```

`rawdata/` 是空的就告訴使用者先把素材放進 `rawdata/<meeting>/`（`<meeting>` 建議 `YYYY-MM-DD-短描述`），不要幫他建空資料夾。

## 3. 轉檔

```bash
docker compose run --rm mm ingest <meeting>
```

stdout 是 JSON：

```json
{
  "meeting": "2026-07-28-project-weekly",
  "rawdata": "/work/rawdata/2026-07-28-project-weekly",
  "notes": "/work/notes/2026-07-28-project-weekly",
  "ingested": [{ "raw": "slides.pptx", "note": "slides.pptx.md" }],
  "skipped": [{ "raw": "agenda.pdf", "note": "agenda.pdf.md" }],
  "unsupported": [{ "raw": "recording.mp3", "message": "..." }],
  "failed": [{ "raw": "broken.pdf", "error": "FileConversionException: ..." }]
}
```

四個清單的意思：

- `ingested`：這次轉出來的 Note。Note 檔名是「原檔名 + `.md`」（`slides.pptx.md`），副檔名刻意留著，使用者看到 source 引用時能直接對回原檔。
- `skipped`：Note 已存在且比 Raw Material 新，所以沒動它。使用者手動修過的 Note 不會被覆蓋。
- `unsupported`：`.mp3` / `.m4a` / `.wav` / `.mp4`。ADR-0003 的決定，不是漏做。其他副檔名的錄音（例如 `.flac`）會落在 `failed`，這時請比照這裡的說明處理。
- `failed`：這個檔案轉失敗，其餘檔案照常處理，整批不中斷。

只要指令跑得起來，exit code 就是 0——`failed` 有東西也一樣。**不要只看 exit code**，一定要讀 JSON。exit code 非零代表指令本身跑不了（例如 `rawdata/<meeting>/` 不存在），錯誤訊息在 stderr。

## 4. 回報

把四個清單講成人話。三件事一定要說出來，不能安靜吞掉：

- 有 `unsupported` 就明確告訴使用者：「這幾個錄音檔沒有處理，請先用你手邊的工具轉成逐字稿，再把逐字稿（.txt / .docx / .md）放進 `rawdata/<meeting>/` 重跑一次。」不要提議由你來轉錄，容器裡沒有轉錄能力。
- 有 `failed` 就逐項列出檔名與錯誤，並說明其他檔案都已經處理完；建議使用者自己另存一份可讀的格式再重跑。
- 圖片會產出**空的 Note**（容器裡沒有 exiftool，也沒有接視覺模型）。素材裡有白板照時要提醒使用者：照片上的內容不會進 Note，需要的話請自己補一份文字說明放進 `rawdata/`。

接下來的步驟是 Extract 與 Render（`mm-minutes`）。

## 邊界

- 不要為了「幫忙」而寫入、搬移、改名或刪除 `rawdata/` 裡的任何東西。
- 不要在宿主端安裝任何 Python 套件、不要建 venv、不要繞過容器直接跑 `scripts/mm.py`。理由見 `docs/adr/0004-all-code-runs-in-docker-compose.md`。
- 不要自己試著轉錄音訊。理由見 `docs/adr/0003-no-audio-ingest.md`。

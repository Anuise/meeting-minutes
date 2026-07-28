---
name: mm-ingest
description: 把一場 Meeting 的 Raw Material（PDF、Word、PowerPoint、Excel、HTML、CSV、JSON、XML、EPub、Outlook 郵件）機械轉成 notes/<meeting>/ 底下的 Note。使用者把檔案原封不動丟進 rawdata/<meeting>/ 之後呼叫；重跑安全，沒變動的檔案會被跳過。錄音與圖片一律拒絕並說明該怎麼補。
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
- `unsupported`：音訊、影片（ADR-0003）與圖片（ADR-0005）。刻意拒絕，不是漏做，每一項都帶著該怎麼補的 `message`。判定是「寫死的副檔名清單 + mimetype 補漏」，兩層都漏掉的冷門格式會落在 `failed`，這時請照 `message` 的精神自己說明。
- `failed`：這個檔案轉失敗，其餘檔案照常處理，整批不中斷。

只要指令跑得起來，exit code 就是 0——`failed` 有東西也一樣。**不要只看 exit code**，一定要讀 JSON。exit code 非零代表指令本身跑不了（例如 `rawdata/<meeting>/` 不存在），錯誤訊息在 stderr。

## 4. 回報

把四個清單講成人話。三件事一定要說出來，不能安靜吞掉：

- 有 `unsupported` 就把每一項的 `message` 轉成人話講給使用者聽。錄音／影片：請他先用手邊的工具轉成逐字稿，再把逐字稿（.txt / .docx / .md）放進 `rawdata/<meeting>/` 重跑。圖片：白板照上的內容不會進 Note，需要的話請他自己補一份文字說明放進 `rawdata/`。
- 不要提議由你來轉錄音訊或讀圖。容器裡沒有這兩種能力，理由見 `docs/adr/0003-no-audio-ingest.md` 與 `docs/adr/0005-no-image-ingest.md`。
- 有 `failed` 就逐項列出檔名與錯誤，並說明其他檔案都已經處理完；建議使用者自己另存一份可讀的格式再重跑。

接下來的步驟是 Extract 與 Render（`mm-minutes`）。

## 邊界

- 不要為了「幫忙」而寫入、搬移、改名或刪除 `rawdata/` 裡的任何東西。
- 不要在宿主端安裝任何 Python 套件、不要建 venv、不要繞過容器直接跑 `scripts/mm.py`。理由見 `docs/adr/0004-all-code-runs-in-docker-compose.md`。
- 不要自己試著轉錄音訊，也不要自己讀圖補內容。理由見 `docs/adr/0003-no-audio-ingest.md` 與 `docs/adr/0005-no-image-ingest.md`。

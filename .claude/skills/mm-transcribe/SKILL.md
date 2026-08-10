---
name: mm-transcribe
description: 把一場 Meeting 的錄音與錄影（Recording）轉成 notes/<meeting>/ 底下的逐字稿 Note —— 轉成 mp3、送上內網的 ASR Service、等它轉完、把帶時間碼的逐字稿落成 Note。使用者把錄音原封不動丟進 rawdata/<meeting>/ 之後呼叫；重跑安全，已轉好的不重轉、已送出的不重送。等待是常態，一小時的會議可能要等上數十分鐘。
---

# mm-transcribe

Transcribe 位於 Ingest **之前**，把 Recording 變成 Note。之後的 Ingest → Extract →
Render 完全不變。**不呼叫模型**——Extract 仍是唯一呼叫模型的步驟。

分兩步是因為 ASR Service 是非同步的：**Submit** 轉檔並上傳、拿回 Transcription
Task；**Fetch** 查狀態，完成就寫 Note，沒完成就回進度。理由見
`docs/adr/0006-transcribe-recordings-via-asr-service.md`。

只寫 `media/` 與 `notes/`，**絕不寫 `rawdata/`**——那是使用者唯一一份原始素材，
而且不在版控裡（compose 也以唯讀掛載它）。

## 1. 先確認 Docker daemon

```bash
docker info
```

失敗就**停手**，原樣輸出這句話給使用者，不要繼續、不要重試、不要自動啟動任何背景程式，也不要退回宿主 Python：

> Docker daemon 沒有回應。請先啟動 Docker Desktop，等它的狀態變成 Running，再重新執行 mm-transcribe。這個專案的所有程式都在容器內執行，宿主端不會安裝任何 Python 套件。

## 2. 決定要處理哪一場 Meeting

使用者沒指定就用清單讓他選，並優先提示 `pending_recording: true` 的那幾場——那是「有錄音還沒變成 Note」的意思：

```bash
docker compose run --rm mm list
```

## 3. Submit：轉檔並送上 ASR Service

```bash
docker compose run --rm mm transcribe-submit <meeting>
```

stdout 是 JSON：

```json
{
  "meeting": "2026-08-05 平台會議",
  "submitted": [
    {
      "recording": "morning.wav",
      "media": "morning.wav.mp3",
      "task": "da2e5a94...",
      "status": "pending",
      "transcoded": true
    }
  ],
  "resumed": [],
  "skipped": [],
  "failed": [],
  "storage": { "free_bytes": 15358926848, "max_upload_mb": 4096 }
}
```

四個清單的意思：

- `submitted`：這次送出去的。`transcoded: false` 代表 mp3 已經在了，只是重新送出。
- `resumed`：上次失敗的任務，這次呼叫服務端續傳，**沒有重新上傳** mp3。
- `skipped`：已經有任務在跑或已經跑完，不重送。佇列裡不會出現兩份一樣的任務。
- `failed`：這一份錄音在轉檔或上傳時出事，其餘照常處理，整批不中斷。

`storage` 是服務端的剩餘空間。**不要**自己去刪服務端的任務——剩餘空間吃緊時把數字講給使用者聽，由他決定。

只要指令跑得起來，exit code 就是 0，`failed` 有東西也一樣。**不要只看 exit code**。exit code 非零代表指令本身跑不了：`rawdata/<meeting>/` 不存在，或沒設定 `MM_ASR_URL`（見「環境」）。

## 4. Fetch：等它轉完，把逐字稿落成 Note

```bash
docker compose run --rm mm transcribe-fetch <meeting>
```

```json
{
  "fetched": [
    {
      "recording": "morning.wav",
      "task": "da2e5a94...",
      "note": "morning.wav.md",
      "chunks": 12,
      "failed_chunks": 0
    }
  ],
  "pending": [
    {
      "recording": "afternoon.wav",
      "task": "7f1c...",
      "status": "processing",
      "progress_pct": 37.5,
      "completed_chunks": 3,
      "total_chunks": 8
    }
  ],
  "skipped": [],
  "failed": [],
  "degraded": []
}
```

- `pending` 還有東西就**再跑一次 Fetch**，中間隔一段時間（一兩分鐘）。每次都把
  `progress_pct` 與 `completed_chunks / total_chunks` 講給使用者聽，**不要沉默地等**。
- **等待是常態。** 一小時的會議錄音可能遠超過十分鐘，這正是拆成兩步的原因。中途被打斷也沒關係：任務在服務端繼續跑，之後再 Fetch 接得上。
- `fetched` 是這次落成的 Note。`failed_chunks` 不是 0，或 `degraded` 有東西，代表那份 Note 裡有段落沒轉出來、留著警語——**一定要講給使用者聽**，那些話是真的漏掉了，不是沒人講。
- `skipped`：Note 比 Transcription Task 記錄新，代表使用者手動校對過，不覆寫。
- `failed`：整份任務失敗。**重跑 Submit** 就會走服務端的續傳，不必也不要另外找工具重轉。

`pending` 與 `failed` 都清空、每一份 Recording 都有 Note，才算收工。

## 5. 回報

按順序講，一句一件事：

1. 送出了幾份、跳過幾份、續傳幾份。
2. 等待期間的進度（每次 Fetch 都講）。
3. 哪些 Note 落地了，路徑是什麼。
4. `degraded` 與 `failed_chunks`：哪一份 Note 的哪些段落沒轉出來。
5. 服務端剩餘空間，如果吃緊就提醒使用者自己去清。

接下來的步驟是 Ingest → Extract → Render（`mm-minutes`）。

## 環境

ASR Service 的位址由環境變數 `MM_ASR_URL` 提供，值放在專案根目錄的 `.env`（不進 git）：

```
MM_ASR_URL=https://<asr-service 的位址>
```

沒設定時 CLI 會直接報錯講出要設什麼。**不要**把位址寫進程式碼或 compose 檔，也不要在指令列傳——那是環境的屬性，不是命令的屬性。

## 邊界

- 不要為了「幫忙」而寫入、搬移、改名或刪除 `rawdata/` 裡的任何東西。
- 不要在宿主端安裝任何 Python 套件、不要建 venv、不要繞過容器直接跑 `scripts/mm.py`。理由見 `docs/adr/0004-all-code-runs-in-docker-compose.md`。
- **不要自己用別的工具硬轉錄音**，也不要建議使用者這樣做。錄音一律走 Transcribe。
- 圖片仍然不處理。白板照的內容需要進會議記錄的話，請使用者自己補一份文字說明放進 `rawdata/`，理由見 `docs/adr/0005-no-image-ingest.md`。
- 不要刪除 ASR Service 上的任務。刪了本地記錄就指向死 id，重抓的路也斷掉。
- `media/` 底下的 mp3 與 `.task.json` 是機器產的，可以整個刪掉重建；但**刪了 `.task.json` 就等於放棄那次轉錄**，下次 Submit 會重新上傳一份。

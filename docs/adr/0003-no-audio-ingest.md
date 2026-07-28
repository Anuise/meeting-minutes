# 不收音訊，Raw Material 只收文件

Raw Material 不接受錄音檔。會議錄音必須先由外部工具轉成逐字稿，才能放進 `rawdata/<meeting>/`。Ingest 遇到 `.mp3` / `.m4a` / `.wav` / `.mp4` 會跳過並提示。

## 為什麼要記下來

markitdown 的文件明確宣稱支援 "Audio (EXIF metadata and speech transcription)"，未來讀者看到我們排除音訊，合理會認為是漏做而想加回來。實際查證原始碼後，那個支援對會議錄音不成立：

- 轉錄後端是 `speech_recognition` 的 `recognizer.recognize_google()` —— Google 免費 Web Speech 端點，設計給幾秒到幾十秒的短語音。
- `recognizer.record(source)` 整檔一次送出，**沒有任何分段**。一小時的會議錄音送進去等於白送。
- 預設語系 en-US。本專案的會議是繁體中文。
- 沒有講者分離，沒有時間軸。

也就是說：「markitdown 支援什麼我們就支援什麼」這個原則對文件類（PDF / docx / pptx / xlsx / html / csv / epub / msg）完全成立，唯獨對音訊不成立。

## Considered Options

**改接 Whisper（本地 faster-whisper 或 API）。** 技術上可行且效果好，但引入一個相當份量的新依賴與新的失敗面，而使用者手邊已有可用的轉錄工具。決定先不做，需求出現時再開一份新的 ADR 推翻這份。

## Consequences

- 容器映像**刻意不安裝** markitdown 的 `audio-transcription` extra。依賴清單本身就是這個決定的證據。
- 流程在「取得逐字稿」這一步斷在系統之外，由使用者自行銜接。

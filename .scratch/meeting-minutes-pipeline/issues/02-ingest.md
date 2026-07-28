# 02 — Ingest：Raw Material 轉成 Note

**What to build:** 使用者把一場會議留下的檔案原封不動丟進 `rawdata/<meeting>/`，不需要事先判斷「這個格式支援嗎」，然後呼叫一個 skill，`notes/<meeting>/` 就出現對應的 markdown。素材很多時重跑很快，因為沒變動的檔案會被跳過；其中一個檔案壞掉不會擋住整批，最後會一次列出所有失敗項目；錄音檔會被明確拒絕並告訴使用者要先自行轉逐字稿。

使用者可以確信這一步絕對不會動到 Raw Material——那是唯一一份原始素材，而且不在版控裡。

**Blocked by:** 01 — 容器骨架與 `mm-init`

**Status:** ready-for-agent

- [x] `ingest` 子指令加入 CLI，吃 argv、把結果以 JSON 印到 stdout、錯誤走 exit code、完全非互動。
- [x] `mm-ingest` skill 可手動呼叫，開頭做 Docker daemon 健康檢查。
- [x] PDF、Word、PowerPoint、Excel、HTML、CSV、JSON、XML、EPub 與 Outlook 郵件各有一個小 fixture，執行後產出對應 Note。（圖片改為明確拒絕，見下方 Comments）
- [x] `.mp3`、`.m4a`、`.wav`、`.mp4`（以及其他音訊／影片副檔名）被跳過，且出現在回報中並附「請先自行轉成逐字稿」的說明；不是安靜跳過。
- [x] Note 已存在且比對應的 Raw Material 新時被跳過，且跳過的項目出現在回報中。
- [x] 單一檔案轉換失敗時，其餘檔案照常處理，失敗項目集中列在回報的失敗清單中，整批不中斷。
- [x] Note 的檔名看得出它來自哪一份 Raw Material，使用者看到 source 引用時能立刻對回原檔。
- [x] 測試斷言：執行前後 `rawdata/` 目錄下所有檔案位元組完全未變。
- [x] compose 中 `rawdata` 確實以唯讀掛載。

## Comments

**2026-07-28 — 圖片改為明確拒絕，而不是產出空 Note。** 實作時發現容器內 markitdown 對圖片只會產出空字串：內容來源只有 exiftool metadata 與 `llm_client`，而基底映像沒裝 exiftool、CLI 依 ADR-0004 也不接模型。空 Note 比沒有 Note 更糟——它看起來像處理過了，Extract 卻讀不到東西，白板照上的決議會安靜消失。使用者裁決：排除圖片，歸 `unsupported` 並附「請自行補一份文字說明」。寫成 `docs/adr/0005-no-image-ingest.md`，`CONTEXT.md` 的 Raw Material 定義同步更新。

**2026-07-28 — 音訊判定改成兩層。** 只擋 ADR-0003 點名的四個副檔名時，`.flac`、`.mov` 這類會落在 `failed` 而拿到「轉檔失敗」而不是「請先轉逐字稿」。改為「寫死清單（地板，不隨基底映像的 mime 表漂移）+ `mimetypes` 補漏」，同一個機制也用在圖片。ADR-0003 補了一段說明清單非窮舉。

**2026-07-28 — 遞迴子目錄。** 原票沒要求，但 `iterdir()` 會安靜忽略整個資料夾（使用者常把一包照片原封不動拖進來）。實作為 `rglob` + 鏡射相對路徑，使用者裁決保留。

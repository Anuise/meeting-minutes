# 02 — Ingest：Raw Material 轉成 Note

**What to build:** 使用者把一場會議留下的檔案原封不動丟進 `rawdata/<meeting>/`，不需要事先判斷「這個格式支援嗎」，然後呼叫一個 skill，`notes/<meeting>/` 就出現對應的 markdown。素材很多時重跑很快，因為沒變動的檔案會被跳過；其中一個檔案壞掉不會擋住整批，最後會一次列出所有失敗項目；錄音檔會被明確拒絕並告訴使用者要先自行轉逐字稿。

使用者可以確信這一步絕對不會動到 Raw Material——那是唯一一份原始素材，而且不在版控裡。

**Blocked by:** 01 — 容器骨架與 `mm-init`

**Status:** ready-for-agent

- [ ] `ingest` 子指令加入 CLI，吃 argv、把結果以 JSON 印到 stdout、錯誤走 exit code、完全非互動。
- [ ] `mm-ingest` skill 可手動呼叫，開頭做 Docker daemon 健康檢查。
- [ ] PDF、Word、PowerPoint、Excel、HTML、CSV、JSON、XML、EPub、Outlook 郵件與圖片各有一個小 fixture，執行後產出對應 Note。
- [ ] `.mp3`、`.m4a`、`.wav`、`.mp4` 被跳過，且出現在回報中並附「請先自行轉成逐字稿」的說明；不是安靜跳過。
- [ ] Note 已存在且比對應的 Raw Material 新時被跳過，且跳過的項目出現在回報中。
- [ ] 單一檔案轉換失敗時，其餘檔案照常處理，失敗項目集中列在回報的失敗清單中，整批不中斷。
- [ ] Note 的檔名看得出它來自哪一份 Raw Material，使用者看到 source 引用時能立刻對回原檔。
- [ ] 測試斷言：執行前後 `rawdata/` 目錄下所有檔案位元組完全未變。
- [ ] compose 中 `rawdata` 確實以唯讀掛載。

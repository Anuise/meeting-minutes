# 05 — 取回：Transcription Task → Note

**What to build:** 整條路打通。使用者跑 Fetch：任務還沒完成就看到進度（百分比、已完成幾段），完成了就在 `notes/<meeting>/` 出現一份逐字稿 Note。從這張票開始，錄音真的變成會議記錄的素材——後面的 Extract 與 Render 一行都不用改。

逐字稿不是一整塊文字，而是照 ASR Service 回的分段切成帶時間碼的小節，開頭標明它來自哪一個 Recording、哪一個 Transcription Task。

切段不是排版偏好，是**可查證性**：每筆決議與待辦都要帶指回 Note 的 source（路徑加行號）。一整塊純文字會讓所有 source 指向同一團，等於失去 ADR-0002 之後整條流程賴以成立的溯源能力。切段後行號自然分散，使用者也能拿時間碼回錄音裡聽。

Note 的結構見 spec 的 Implementation Decisions。

**Blocked by:** 04

**Status:** ready-for-agent

- [ ] 新增 Fetch 子命令，吃 Meeting slug、吐 JSON 到 stdout、完全非互動
- [ ] 任務未完成時回報進度百分比與已完成段數，**不寫 Note**
- [ ] JSON 明確區分「還在等的」與「已經落成 Note 的」，讓呼叫端知道什麼時候可以往下走
- [ ] 任務完成時把逐字稿寫成 Note，落在 `notes/<meeting>/` 底下，與其他 Note 平起平坐
- [ ] 逐字稿從任務詳情端點回的分段組出來，不用單獨的結果下載端點——分段自帶起訖秒數，那是時間碼唯一的來源
- [ ] Note 開頭標明來源 Recording 的路徑，以及 Transcription Task 的識別、語言、時長、段數
- [ ] 每個分段是一個帶起訖時間碼的小節
- [ ] Note 已存在且比 Transcription Task 記錄新時不覆寫——使用者可能手動修過逐字稿。這是 Ingest「Note 比 Raw Material 新就跳過」同一條規則的延伸
- [ ] 測試涵蓋：完成路徑落成 Note、時間碼小節切得對、Note 開頭的來源與任務資訊、未完成路徑只回進度不寫 Note、手改過的 Note 不被覆蓋
- [ ] 若 04 探明分段不帶文字，**停下來回報**，不要自己改走結果下載端點——那會讓 Note 退化成單一區塊，損及溯源能力，需要先討論

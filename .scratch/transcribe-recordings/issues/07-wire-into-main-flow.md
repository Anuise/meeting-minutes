# 07 — 串進主流程

**What to build:** 使用者只用主要入口就好。把錄音丟進 `rawdata/<meeting>/`，跑 `mm-minutes`，它自己會轉錄、等它轉完、再往下做 Ingest → Extract → Render，不必記得多跑一個步驟。

Meeting 清單上看得出哪一場有還沒轉成 Note 的 Recording，使用者知道哪些會議還卡著。

Ingest 遇到錄音時的訊息不再叫使用者自己去找轉錄工具——那句話現在是錯的。Ingest 的**行為**仍然一行不改：音訊與影片照樣落在 `unsupported`，因為 Ingest 的定義就是機械轉檔，把轉錄塞進去會弄髒它。ADR-0003 只被推翻一半，這句訊息是使用者唯一看得到那一半的地方。

**Blocked by:** 05

**Status:** ready-for-agent

- [ ] Meeting 清單多一個「有沒有 Recording 還沒變成 Note」的狀態
- [ ] 新增與 Ingest 對稱的 Transcribe skill：先確認 Docker daemon、選 Meeting、Submit、定期 Fetch 並回報進度、全部完成才收工
- [ ] Transcribe skill 講清楚等待是常態——一小時的會議轉錄可能遠超過十分鐘，這正是拆兩步的原因
- [ ] 主流程在 Ingest **之前**插入 Transcribe，沒有 Recording 的 Meeting 完全不受影響
- [ ] 主流程在等待期間把進度講給使用者聽，不是沉默
- [ ] Ingest skill 文件裡「請先自行轉成逐字稿」那段改成指向 Transcribe
- [ ] 不支援訊息的文字同步更新，並指回 ADR-0006
- [ ] 清單 skill 文件補上新的狀態欄位怎麼讀
- [ ] 所有 skill 的邊界條款同步：「不要自己試著轉錄音訊」對圖片仍然成立，對錄音則改為「交給 Transcribe，不要用別的工具硬轉」
- [ ] 測試涵蓋：清單新欄位的斷言；Ingest 訊息改了之後仍然把音訊列進 `unsupported` 且不留下 Note

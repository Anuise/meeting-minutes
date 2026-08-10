# 03 — 轉檔：Recording → Media

**What to build:** 使用者把會議錄音或錄影原封不動丟進 `rawdata/<meeting>/`，跑一次 Transcribe 的 Submit，`media/<meeting>/` 就出現對應的 mp3。原始素材一個位元都沒被動過。素材沒變就再跑幾次也不會重轉。

這一刀砍到底的是「轉檔」這條完整路徑：找出哪些素材是 Recording、轉成適合上傳的 mp3、放到一個跟 Raw Material 分開的地方。**這張票還不會上傳**——上傳是 04 的事，Submit 在這張票結束時是個只會轉檔的命令。

分開的理由是 context 大小：ffmpeg、HTTP、環境變數、兩套冪等規則塞進同一張票會爆掉。代價是這張票完成時 Submit 處於半成品狀態，這是刻意的。

轉檔參數（丟視訊、單聲道、16 kHz、32 kbps）與檔名規則見 spec 的 Implementation Decisions，那裡有每個選擇的理由。

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] 新增 Submit 子命令，吃 Meeting slug、吐 JSON 到 stdout、完全非互動，與既有子命令形狀一致
- [ ] 用 02 收斂出的分類找出 Recording，不另開副檔名清單
- [ ] 子資料夾裡的 Recording 也被找到
- [ ] Media 的檔名保留 Recording 的原副檔名，理由與 Note 的命名規則相同——看得出來源，且同名不同格式的兩份錄音不會互相蓋掉
- [ ] ffmpeg 裝進映像，由 CLI 以子行程呼叫；以 argv list 傳參、**不經 shell**（Meeting slug 含空格與中文）
- [ ] Media 目錄以讀寫掛載，`rawdata/` 維持唯讀
- [ ] `mm init` 的骨架清單加入 Media 目錄，重跑仍然跳過已存在的東西
- [ ] Media 已存在且比 Recording 新時不重轉，並在 JSON 裡回報為跳過——沿用 Ingest 的 mtime 慣例
- [ ] 一份 Recording 轉檔失敗不中斷整批，失敗項目集中回報
- [ ] 非 Recording 的素材完全不受影響，Submit 不碰它們
- [ ] 測試沿用既有 seam：子行程跑真 CLI、斷言檔案系統結果與 stdout JSON
- [ ] 測試素材用 ffmpeg 自己產一段極短的靜音，真的轉一次、驗 mp3 出得來
- [ ] 測試涵蓋「`rawdata/` 一個位元都沒被寫過」，照既有的雜湊快照手法
- [ ] 映像需要重新 build 這件事寫進票的完成回報（ADR-0004 已記下改依賴要手動 rebuild）

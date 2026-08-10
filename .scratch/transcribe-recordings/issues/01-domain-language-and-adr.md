# 01 — 領域語言與 ADR-0006

**What to build:** 讓這個 repo 的詞彙與決策紀錄先容納得下「錄音可以直接進來」這件事。讀者翻開領域語言時看得到 Recording、Media、Transcription Task 三個名詞與 Transcribe 一個動作，也看得懂 Raw Material 為什麼不再排除音訊；翻開決策紀錄時查得到 ADR-0003 被推翻了哪一半、以及為什麼。

放在最前面的理由：後面每一張票的訊息文字、註解與 skill 文件都要引用 ADR-0006 的編號。最後才寫，中間的票就得引用一個還不存在的東西。

這張票只動文件，不動任何程式碼與測試。

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [ ] 領域語言新增 **Recording**：Raw Material 裡的音訊或影片檔，是唯一需要經過外部服務才能變成 Note 的素材
- [ ] 領域語言新增 **Media**：Recording 轉出來、實際送去轉錄的 mp3，可拋棄、隨時可從 Recording 重建
- [ ] 領域語言新增 **Transcription Task**：ASR Service 上的一個轉錄任務，非同步
- [ ] 領域語言新增動作 **Transcribe**：把 Recording 變成 Note，分 Submit 與 Fetch 兩步，**不呼叫模型**（Extract 仍是唯一呼叫模型的步驟）
- [ ] Raw Material 的定義拿掉「不含音訊」，改為指向 ADR-0006；圖片仍然排除，ADR-0005 的敘述不動
- [ ] 每個新詞都附 `_Avoid_` 行，與既有詞條的格式一致
- [ ] 領域語言裡不出現任何實作細節——它是詞彙表，不是規格
- [ ] 新增 ADR-0006，標題點明「經由 ASR Service 轉錄 Recording」，並標明**部分取代** ADR-0003
- [ ] ADR-0006 記下：ADR-0003 自己預留的推翻條件如何成立（內網有了自建 ASR Service），以及被推翻的只有「Raw Material 不收音訊」，**Ingest 仍然不碰音訊**
- [ ] ADR-0006 記下：為何 `rawdata/` 仍維持唯讀掛載，而 Media 另立目錄
- [ ] ADR-0006 記下：**為何關閉 TLS 憑證驗證**——憑證的 Subject Alternative Name 只涵蓋 `localhost` 與 `127.0.0.1`，用 LAN IP 連不可能驗過，掛 CA 也無效；連線仍加密但無法確認對端身分；並寫明「憑證修好就把它拿掉」這個拿掉的條件
- [ ] ADR-0006 記下：為何選 multipart 上傳而非可續傳的分塊上傳
- [ ] ADR-0006 記下：為何把 Transcribe 拆成 Submit 與 Fetch 兩步
- [ ] ADR-0003 本身不改寫——被取代的關係由 ADR-0006 單向宣告，既有紀錄保持原樣

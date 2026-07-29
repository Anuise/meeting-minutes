# 05 — Docx Deliverable

**What to build:** 同一份 Minutes Record 多產出一份 .docx。使用者在主流程中多一個選擇：要用哪一份 Docx Template，或是不用——不指定就只出 markdown、不產 .docx。

換一份 Docx Template 重新產出時，內容與 markdown 版本完全一致，兩份檔案可以互相對帳。這一步不呼叫模型，可以無限次重跑。

**Blocked by:** 04 — 主流程

**Status:** ready-for-agent

- [x] `render` 子指令接受選填的 Docx Template，輸出 .docx 到 `output/<meeting>/`。
- [x] 未指定 Docx Template 時只產 markdown，且不視為錯誤。
- [x] `mm-minutes` 多一個 Docx Template 選單，明確包含「不使用」這個選項。
- [x] 未填變數的回報涵蓋 Docx Template 的變數，不只 Markdown Template。
- [x] 測試：同一份 Minutes Record 分別套 Markdown Template 與 Docx Template，兩份 Deliverable 的內容一致。
- [x] 測試：空欄位在 .docx 中同樣呈現為「未提及」；巢狀與清單型欄位正確展開。
- [x] 測試：換一份 Docx Template 重跑，Minutes Record 未被修改。

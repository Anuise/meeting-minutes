# 06 — 把客戶的 .docx 變成 Docx Template

**What to build:** 使用者把客戶或公司給的 .docx 放進 `templates/docx-source/`，呼叫一個 skill，先看到一份「哪些段落是變動欄位、建議的變數名叫什麼」的對照表，可以逐項修改，確認後系統就地打洞產出 Docx Template。使用者不用自己在 Word 裡土法煉鋼打 Jinja2 標記，也不用擔心系統亂猜。

打洞後的 Docx Template 完整保留原始的頁首頁尾、logo、字型與表格樣式——交出去的文件看起來就是客戶自己的格式。原始的 Docx Source 絕對不被修改，隨時能重新來過。

同一個 skill 也負責用互動的方式建立 Markdown Template。

**Blocked by:** 05 — Docx Deliverable

**Status:** ready-for-agent

- [ ] `scan-docx` 子指令讀 Docx Source，回傳段落與表格儲存格的清單供判斷哪些是變動欄位。
- [ ] `apply-docx` 子指令帶著最終的變數對照表就地替換，輸出到 `templates/docx/`。
- [ ] `mm-template` skill 可手動呼叫：掃描、提出建議對照表、讓使用者逐項修改、確認後套用。
- [ ] `apply-docx` 正確處理 Word 把單一句子拆成多個 run 的情況——替換前在段落層級合併 run，跨 run 的字串能被比對到。
- [ ] 測試：fixture .docx 含頁首頁尾、表格與跨 run 句子，`scan-docx` 正確列出候選段落與儲存格。
- [ ] 測試：`apply-docx` 產出的 Docx Template 能被 docxtpl 成功渲染。
- [ ] 測試：執行後 `templates/docx-source/` 下的原檔位元組完全未變。
- [ ] 測試：跨多個 run 的句子被正確替換。
- [ ] 測試：頁首頁尾與表格樣式在打洞後保留。
- [ ] `mm-template` 也能以互動方式建立 Markdown Template，並列出目前可用的 Markdown Template 與 Docx Template。

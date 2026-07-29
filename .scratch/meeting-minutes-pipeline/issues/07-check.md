# 07 — 交付前的檢查

**What to build:** 使用者在交出去之前，看到一份清單：Minutes Record 有哪些欄位是空的、有哪些決議或待辦缺少 source、選定的模板裡有哪些變數在選定的 Minutes Schema 中找不到對應。檢查只列出清單、不阻擋流程——由使用者自己判斷哪些要處理、哪些可以接受。

Render 完成後自動跑一次，也可以單獨手動呼叫。

因為 Minutes Schema、Markdown Template、Docx Template 三者不強制綁定，這是唯一一道防止交付檔長出空格子的防線，所以訊息品質很重要：要講清楚是**哪一個變數**、在**哪一份模板**、對應不到**哪一套 schema**。

**Blocked by:** 05 — Docx Deliverable

**Status:** ready-for-agent

- [x] `check` 子指令加入 CLI，回傳結構化 JSON。
- [x] `mm-check` skill 可手動呼叫；`mm-minutes` 在 Render 後自動跑一次並顯示結果。
- [x] 偵測 Minutes Record 的空欄位，正例與反例各有測試。
- [x] 偵測缺少 `source` 的決議與待辦，正例與反例各有測試。
- [x] 偵測模板變數在 Minutes Schema 中找不到對應，正例與反例各有測試；Markdown Template 與 Docx Template 都涵蓋。
- [x] 訊息指名到變數、模板與 schema 三者，不是籠統的「有變數對不到」。
- [x] 測試斷言：即使有發現，exit code 仍為 0——回報而不阻擋。

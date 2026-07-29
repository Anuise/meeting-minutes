# 03 — 導覽：看到每個 Meeting 走到哪一步

**What to build:** 使用者呼叫一個 skill，看到所有 Meeting 各自的進度：有沒有 Raw Material、有沒有 Note、有沒有 Minutes Record、有沒有 Deliverable。同一份清單之後會成為主流程挑選 Meeting 時的來源，使用者不用手打資料夾名稱。

同時也列出目前有哪些 Minutes Schema、Markdown Template 與 Docx Template 可用。

**Blocked by:** 01 — 容器骨架與 `mm-init`

**Status:** ready-for-agent

- [x] `list` 子指令加入 CLI，回傳結構化 JSON：每個 Meeting 的 slug 與四個階段的完成狀態，以及可用的 Minutes Schema、Markdown Template、Docx Template 清單。
- [x] `mm-list` skill 可手動呼叫，透過容器執行（與其他 skill 一致，無例外），開頭做 Docker daemon 健康檢查。
- [x] 各種完成度的 fixture 目錄都回報正確的階段狀態：只有 Raw Material、有 Note 沒 Record、有 Record 沒 Deliverable、全部完成、空目錄。
- [x] 一個 Meeting 只出現在 `notes/` 或 `records/` 而 `rawdata/` 沒有對應目錄時，仍被列出且狀態正確——不是被漏掉。

三份模板清單按副檔名過濾（`schema/*.yaml`、`markdown/*.j2`、`docx/*.docx`，排除 Word 的 `~$` 鎖檔）：README、`.gitkeep`、鎖檔混進清單會被後續的 `render` 當成模板拿去用。

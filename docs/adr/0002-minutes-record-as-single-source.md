# Minutes Record 是唯一的內容真實來源

會議記錄的內容以結構化的 Minutes Record（`records/<meeting>.yaml`）存在，與呈現方式完全分離。Markdown Deliverable 與 Docx Deliverable 都只是把同一份 Minutes Record 套不同模板渲染出來的結果。Extract 是唯一呼叫模型的步驟，Render 不呼叫模型。

## Considered Options

**Markdown 為主，需要 docx 時再從 md 反解回變數。** 概念少一個，但解析 markdown 極脆——改一個標題文字就斷，等於把 schema 藏進 regex 裡。

**兩次生成：要 md 就生一次，要 docx 再生一次。** 實作最短，但同一場會議會得到兩份內容不一致的記錄，無法對帳。會議記錄是會被當成依據引用的東西，這不可接受。

## Consequences

- **人工修改不會被機器吃掉。** 重跑 `mm-minutes` 時，若 Minutes Record 已存在就只重新渲染，不重新抽取；要重抽必須明講（`--reextract`）。代價是往 `rawdata/` 補了新素材時，得自己記得加旗標。
- **換模板重出一份不花錢。** 不呼叫模型。
- Minutes Record 因此是**可拋棄性最低**的東西，放在自己的 `records/` 而不是會被覆寫清空的 `output/`。
- Minutes Record 每筆決議與待辦都帶 `source` 指回 Note；抽不到的欄位一律留空並在 Deliverable 上標「未提及」，不推測。會議記錄被引用時要能查證到源頭。
- 多一份 schema 要維護，且自由文字段落的語感可能被 schema 綁住。

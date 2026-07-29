# 04 — 主流程：Extract 與 markdown Deliverable

**What to build:** 第一次真的產出一份會議記錄。使用者呼叫主要入口 skill，從清單中選 Meeting、選 Minutes Schema、選 Markdown Template（都不用手打），系統讀 Note、產出 Minutes Record、渲染出 markdown Deliverable，並回報有哪些變數沒被填到。

Note 還沒產生或比 Raw Material 舊時，主流程自動補跑 Ingest 並明白告知它這麼做了，使用者不會因為忘記一個步驟而中斷。

Minutes Record 是唯一的內容真實來源，使用者可以直接手動編輯它來修正錯字或補上負責人。之後重跑主流程時**只會重新 Render，不會重新 Extract**——校對過的內容不會被機器蓋掉；要重抽必須明確要求。

**Blocked by:** 02 — Ingest；03 — 導覽

**Status:** ready-for-agent

- [x] `render` 子指令加入 CLI（此片只做 markdown 輸出），吃 Minutes Record 與 Markdown Template，輸出到 `output/<meeting>/`，並在 stdout JSON 中回報未填變數清單。
- [x] `mm-minutes` skill 可手動呼叫，是主要入口；開頭做 Docker daemon 健康檢查。
- [x] Meeting、Minutes Schema、Markdown Template 三者都以清單供選擇，清單來源與 03 一致。
- [x] Note 缺失或比 Raw Material 舊時自動補跑 Ingest，且在輸出中明說「已自動執行 Ingest」。
- [x] Extract 依選定的 Minutes Schema 產出 `records/<meeting>.yaml`。這是流程中唯一呼叫模型的步驟。
- [x] Extract 產出的每一筆決議與待辦都帶 `source`，指回是哪一份 Note 的哪一段。
- [x] Extract 抓不到的欄位一律留空，絕不推測；空欄位在 Deliverable 上呈現為「未提及」。
- [x] Extract 時把 `glossary.yaml` 一併送給模型，人名、職稱、產品名、縮寫不被寫錯。
- [x] `glossary.yaml` 以唯讀掛載進容器，且進版控。
- [x] Minutes Record 已存在時重跑只做 Render，不做 Extract；輸出中明說「沿用既有 Minutes Record」。
- [x] 明確要求重抽（`--reextract`）時才重新 Extract。
- [x] Minutes Record 寫在 `records/`，不寫在 `output/`；整個刪掉 `output/<meeting>/` 再重跑，Deliverable 完整重建且內容不變。
- [x] `render` 測試：巢狀欄位（決議掛在議題底下）與清單型欄位（待辦）正確展開；空欄位呈現為「未提及」；未填變數清單正確。

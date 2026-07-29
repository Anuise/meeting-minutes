---
name: mm-minutes
description: 產出一場 Meeting 的會議記錄 —— 從清單選 Meeting、Minutes Schema 與 Markdown Template，需要時自動補跑 Ingest，讀 Note 抽出 Minutes Record，再渲染成 markdown Deliverable，最後回報有哪些變數沒被填到。這是主要入口；Minutes Record 已存在時只重新 Render，不重抽。
---

# mm-minutes

主要入口。一次走完 Ingest（需要時）→ Extract（需要時）→ Render。

三個階段的分工要記牢：**Extract 是唯一呼叫模型的步驟**，由你做；Ingest 與 Render 是容器裡的確定性程式，由 CLI 做。Minutes Record 是唯一的內容真實來源（ADR-0002），使用者手動改過的內容絕不能被機器蓋掉。

## 1. 先確認 Docker daemon

```bash
docker info
```

失敗就**停手**，原樣輸出這句話給使用者，不要繼續、不要重試、不要自動啟動任何背景程式，也不要退回宿主 Python：

> Docker daemon 沒有回應。請先啟動 Docker Desktop，等它的狀態變成 Running，再重新執行 mm-minutes。這個專案的所有程式都在容器內執行，宿主端不會安裝任何 Python 套件。

## 2. 取得清單，讓使用者選三樣東西

```bash
docker compose run --rm mm list
```

清單來源與 `mm-list` 完全相同，不要自己去 `ls` 資料夾——兩邊會漂移。

要選的三樣，都**從清單挑，不要讓使用者手打**：

1. **Meeting** —— 從 `meetings` 挑。報給使用者時帶上每場的階段狀態（有沒有 Note、有沒有 Minutes Record），他才知道自己在選什麼。使用者已經指名了就不用問。
2. **Minutes Schema** —— 從 `schemas` 挑。只有一套就直接用，說一句「用 default.yaml」即可，不必問。
3. **Markdown Template** —— 從 `markdown_templates` 挑。同上。

`meetings` 是空的就請使用者把素材放進 `rawdata/<meeting>/`（建議 `YYYY-MM-DD-短描述`），不要幫他建空資料夾。三份模板清單都空的代表還沒跑過 `mm-init`。

這一片只產出 markdown。**不要**問使用者要不要 Docx Template。

## 3. 需要時補跑 Ingest

選定的 Meeting 在清單裡 `raw_material: true` 時，直接跑一次：

```bash
docker compose run --rm mm ingest <meeting>
```

它自己會跳過「Note 已存在且比 Raw Material 新」的檔案，所以無條件跑是安全的，而且這是唯一能發現「Note 比 Raw Material 舊」的方法——`list` 只看有沒有檔案，不看新舊。

讀回傳的 JSON，照實說：

- `ingested` 有東西 → 明說**已自動執行 Ingest**，轉了哪幾個檔（Note 缺失或比 Raw Material 舊）。
- `ingested` 是空的 → 不要說你跑了 Ingest，也不要說你沒跑；這一步沒有產生任何變化，不值得占用使用者的注意力。
- `unsupported`、`failed` 有東西 → 照 `mm-ingest` 的規矩逐項講清楚，不要安靜吞掉。這些素材的內容**不會**進 Note，因此也不會進會議記錄。

`raw_material: false` 但 `note: true`（使用者刪了 Raw Material，或直接拿到別人的 Note）→ **跳過這一步**，不要跑 ingest，它會因為找不到目錄而非零退出。兩者都是 false 就停手，請使用者先放素材。

## 4. Extract：讀 Note 產出 Minutes Record

`records/<meeting>.yaml` **已存在**時：**不要 Extract**。明說一句「沿用既有 Minutes Record（`records/<meeting>.yaml`）」，直接跳到第 5 步。使用者花時間校對過的內容不會被機器蓋掉，這是刻意的。

只有使用者**明確要求重抽**（說 `--reextract`、「重抽」、「重新 Extract」）時才重跑 Extract，覆蓋既有的 Minutes Record。重抽前先講清楚：他手動改過的內容會被蓋掉。

Extract 要做的事：

1. 讀完 `notes/<meeting>/` 底下**所有** Note。
2. 讀選定的 `templates/schema/<schema>` —— 它決定要抽哪些欄位、哪些是清單、哪些帶 source。
3. 讀 `glossary.yaml` —— 人名、職稱、產品名、縮寫、常見誤譯的對照，**每次 Extract 都要送進來**，抽出來的專有名詞照它寫，不要自己音譯或簡稱。
4. 依 Schema 的形狀寫出 `records/<meeting>.yaml`。

Minutes Record 的形狀（與 `mm-schema` 的規則一致）：`meta` 底下的欄位收在 `meta.<key>`，`body` 底下的區塊**攤平在最上層**（`topics`、`action_items`、`next_meeting`）。`type: list` 是物件清單，`type: people` 是字串清單，其餘是字串。

三條不能妥協的規則：

- **每一筆決議與待辦都要帶 `source`**，格式 `notes/<meeting>/<note 檔名>#L<行號>`，例如 `notes/2026-07-28-project-weekly/slides.pptx.md#L12`。行號指向那句話真正出現的位置——別人質疑時要查得到。多份 Note 都提到同一件事就挑講得最完整的那一份。
- **抓不到的欄位留空**（`''` 或 `[]`），**絕不推測**。沒講到地點就留空，不要從會議名稱猜；沒講到負責人就留空，不要指派給主席。Deliverable 上會顯示「未提及」，那是正確的結果，不是缺陷。
- **不要為了填滿版面而合併或發明內容**。討論摘要照實寫，沒有決議的議題就給空的 `resolutions`。

寫檔用 `records/<meeting>.yaml`，**不要**寫進 `output/`——`output/` 隨時可以整個刪掉重建，Minutes Record 不行。

## 5. Render

```bash
docker compose run --rm mm render <meeting> --markdown-template <template>
```

stdout 是 JSON：

```json
{
  "meeting": "2026-07-28-project-weekly",
  "minutes_record": "/work/records/2026-07-28-project-weekly.yaml",
  "markdown_template": "default.md.j2",
  "deliverables": ["/work/output/2026-07-28-project-weekly/minutes.md"],
  "unfilled": ["meta.location", "action_items[1].owner"]
}
```

`unfilled` 是**模板讀到卻沒被填到的變數路徑**，順序就是它們在 Deliverable 上出現的順序。它包含兩種情況：Minutes Record 裡是空的，以及 Minutes Record 裡根本沒有這個欄位（模板與 Schema 不強制綁定）。每一項在 Deliverable 上都是一個「未提及」。

Render 不呼叫模型，只讀 `records/` 與 `templates/`、只寫 `output/`。整個刪掉 `output/<meeting>/` 再重跑，內容完全一樣。

## 6. 回報

按順序講，一句一件事：

1. 有沒有自動補跑 Ingest（有就明說，並列出轉了哪幾個檔）。
2. Extract 是新抽的，還是沿用既有的 Minutes Record。
3. Deliverable 在哪裡：`output/<meeting>/minutes.md`。
4. `unfilled` 逐項列出來，用使用者看得懂的說法（`meta.location` → 「地點」，`action_items[1].owner` → 「第 2 筆待辦的負責人」），並說明這些格子在 Deliverable 上顯示為「未提及」。**不要**建議由你把它們補滿。

接著告訴使用者兩條路：

- 內容要改（錯字、補負責人）→ 直接編 `records/<meeting>.yaml`，再重跑 `mm-minutes`。它只會重新 Render，不會重抽。
- 素材有新增或更正 → 補進 `rawdata/<meeting>/`，然後明確要求重抽（`--reextract`）。**只補素材重跑是不會納入新素材的**，因為預設不重抽。

## 邊界

- **Minutes Record 已存在就不重抽**，除非使用者明確要求。這是這個 skill 最重要的一條，別為了「順便更新一下」而破壞它。
- 不要在宿主端安裝任何 Python 套件、不要建 venv、不要繞過容器直接跑 `scripts/mm.py`。理由見 `docs/adr/0004-all-code-runs-in-docker-compose.md`。
- 不要寫入 `rawdata/`，也不要改 `notes/` 裡的 Note。要修內容就改 Minutes Record。
- 不要改 `templates/` 底下的東西。Schema 要調整轉給 `mm-schema`。
- 不要自己轉錄音訊或讀圖補內容，理由見 `docs/adr/0003-no-audio-ingest.md` 與 `docs/adr/0005-no-image-ingest.md`。
- 這一片只產 markdown。.docx Deliverable 由後續 ticket 帶進來，現在不要嘗試產出，也不要用別的工具硬轉。

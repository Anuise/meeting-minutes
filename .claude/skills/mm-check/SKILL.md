---
name: mm-check
description: 交付前的檢查 —— 列出 Minutes Record 有哪些欄位是空的、有哪些決議或待辦缺少 source、選定的模板裡有哪些變數在選定的 Minutes Schema 中找不到對應。只列清單、不阻擋流程，由使用者自己判斷哪些要處理。使用者在把會議記錄交出去之前呼叫；`mm-minutes` 也會在 Render 之後自動跑一次。
---

# mm-check

只讀不寫，跑幾次都一樣。**回報而不阻擋**——有發現也是 exit 0，清單交給使用者判斷，不要自己動手改 Minutes Record。

Minutes Schema、Markdown Template、Docx Template 三者不強制綁定，任何模板都能配任何 schema。這是刻意的寬鬆，代價是交付檔可能長出空格子而沒人發現，而這個 skill 是唯一一道防線。所以回報時要講清楚是**哪一個變數**、在**哪一份模板**、對應不到**哪一套 schema**——CLI 的 `message` 已經把三者寫進去了，照著念就好。

## 1. 先確認 Docker daemon

```bash
docker info
```

失敗就**停手**，原樣輸出這句話給使用者，不要繼續、不要重試、不要自動啟動任何背景程式，也不要退回宿主 Python：

> Docker daemon 沒有回應。請先啟動 Docker Desktop，等它的狀態變成 Running，再重新執行 mm-check。這個專案的所有程式都在容器內執行，宿主端不會安裝任何 Python 套件。

## 2. 決定要檢查哪一場、配哪一套 schema 與模板

```bash
docker compose run --rm mm list
```

清單來源與 `mm-list` 完全相同，不要自己去 `ls` 資料夾。要選的四樣，都**從清單挑，不要讓使用者手打**：

1. **Meeting** —— 從 `meetings` 裡 `minutes_record: true` 的挑。沒有 Minutes Record 就沒得檢查，請使用者先跑 `mm-minutes`。
2. **Minutes Schema** —— 從 `schemas` 挑。只有一套就直接用，說一句「用 default.yaml」即可。
3. **Markdown Template** —— 從 `markdown_templates` 挑。同上。
4. **Docx Template** —— 從 `docx_templates` 挑，選項裡要包含「不使用」。挑他實際拿來交付的那一份；沒有要出 .docx 就省略。

被 `mm-minutes` 叫起來時**不要重問**——四樣它剛剛已經選過了，直接用同一組。

## 3. 跑檢查

```bash
docker compose run --rm mm check <meeting> --schema <schema> --markdown-template <template> --docx-template <docx>
```

沒有要檢查 .docx 就**整個省略 `--docx-template`**，不要傳空字串。

stdout 是 JSON：

```json
{
  "meeting": "2026-07-28-project-weekly",
  "minutes_record": "/work/records/2026-07-28-project-weekly.yaml",
  "schema": "default.yaml",
  "markdown_template": "default.md.j2",
  "docx_template": "org.docx",
  "blank_fields": [
    {
      "path": "meta.location",
      "label": "地點",
      "message": "Minutes Record 的「地點」是空的：meta.location"
    },
    {
      "path": "action_items[1].owner",
      "label": "負責人",
      "message": "Minutes Record 的「負責人」是空的：action_items[1].owner"
    }
  ],
  "missing_source": [
    {
      "path": "action_items[1].source",
      "label": "來源",
      "message": "Minutes Record 的「待辦事項」第 2 筆沒有 source，指不回 Note：action_items[1].source"
    }
  ],
  "unmapped_variables": [
    {
      "template": "org.docx",
      "kind": "docx",
      "variable": "meta.owner_org",
      "field": "meta.owner_org",
      "message": "Docx Template「org.docx」用到的變數 meta.owner_org，在 Minutes Schema「default.yaml」裡找不到對應欄位。"
    }
  ]
}
```

三份清單各自的意思：

- **`blank_fields`** —— 選定的 Minutes Schema 有這個欄位，Minutes Record 裡卻是空的，或根本沒有這一項。順序就是 Minutes Schema 上的欄位順序。整個區塊都不在（例如完全沒有 `meta:`）只報一次區塊本身，不會把底下每個欄位各報一遍。
- **`missing_source`** —— schema 裡 `type: source` 的欄位空著。缺 source 只會出現在這一份清單，不會同時混進 `blank_fields`。
- **`unmapped_variables`** —— 模板讀了一個 Minutes Schema 裡沒有的欄位。`kind` 分 `markdown` 與 `docx`，Docx Template 連頁首頁尾一起掃。`variable` 是模板上的寫法，`field` 是它實際對到的欄位路徑——迴圈變數會被換回它迭代的清單，所以模板寫 `resolution.text`、`field` 會是 `topics.resolutions.text`。兩者不同時 `message` 會兩個都講。

這與 `render` 回傳的 `unfilled` 不是同一件事：`unfilled` 看的是「模板讀到卻沒被填到」，`unmapped_variables` 是靜態比對模板與 schema，不看 Minutes Record 有什麼。

## 4. 回報

三份清單分開講，每一項照 `message` 念，然後補上該怎麼處理：

- `blank_fields` → 這些格子在 Deliverable 上是「未提及」。要補就直接編 `records/<meeting>.yaml`，再重跑 `mm-minutes`（它只會重新 Render）。**不要**建議由你把它們填滿，也不要自己動手——Extract 抓不到就是抓不到，猜出來的會議記錄不能被當成依據引用。
- `missing_source` → 這幾筆決議或待辦查不回 Note，別人質疑時無從對證。素材裡確實找得到出處就手動補 `source`（格式 `notes/<meeting>/<note 檔名>#L<行號>`）；素材裡本來就沒講，那空著是正確的。
- `unmapped_variables` → 模板與 schema 對不上。兩條路：換一份配得上的模板，或是用 `mm-schema` 把欄位加進 Minutes Schema 再重抽。

三份都空就講一句「沒有發現」，不要為了看起來有做事而把 JSON 整段貼給使用者。

最後明確說一句：**這些只是清單，沒有擋住任何東西**，Deliverable 已經在 `output/<meeting>/` 了，要不要處理由他決定。

## 邊界

- 這個 skill 不改任何東西。不要順手補 Minutes Record 的空欄位、不要幫忙編 source、不要動模板或 schema。
- 不要因為有發現就說「產出失敗」或建議重跑 Render。檢查不阻擋流程。
- 不要在宿主端安裝任何 Python 套件、不要建 venv、不要繞過容器直接跑 `scripts/mm.py`。理由見 `docs/adr/0004-all-code-runs-in-docker-compose.md`。
- 要改 Minutes Schema 轉給 `mm-schema`；要把客戶的 .docx 打洞成 Docx Template 轉給 `mm-template`。

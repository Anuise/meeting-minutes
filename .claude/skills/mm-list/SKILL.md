---
name: mm-list
description: 列出所有 Meeting 各自走到哪一步 —— 有沒有 Raw Material、有沒有 Note、有沒有 Minutes Record、有沒有 Deliverable，以及目前有哪些 Minutes Schema、Markdown Template、Docx Template 可用。使用者想知道「哪些會議還沒做完」時呼叫；也是主流程挑選 Meeting 時的清單來源。
---

# mm-list

只讀不寫，跑幾次都一樣。掃描邏輯留在 CLI，`mm-minutes` 的 Meeting picker 用同一份清單，兩邊不會漂移。

## 1. 先確認 Docker daemon

```bash
docker info
```

失敗就**停手**，原樣輸出這句話給使用者，不要繼續、不要重試、不要自動啟動任何背景程式，也不要退回宿主 Python：

> Docker daemon 沒有回應。請先啟動 Docker Desktop，等它的狀態變成 Running，再重新執行 mm-list。這個專案的所有程式都在容器內執行，宿主端不會安裝任何 Python 套件。

## 2. 取得清單

```bash
docker compose run --rm mm list
```

stdout 是 JSON：

```json
{
  "root": "/work",
  "meetings": [
    {
      "slug": "2026-07-28-project-weekly",
      "raw_material": true,
      "note": true,
      "minutes_record": false,
      "deliverable": false
    }
  ],
  "schemas": ["default.yaml"],
  "markdown_templates": ["default.md.j2"],
  "docx_templates": ["default.docx"]
}
```

四個階段旗標的意思：

- `raw_material`：`rawdata/<slug>/` 底下有檔案。
- `note`：`notes/<slug>/` 底下有檔案（Ingest 做過了）。
- `minutes_record`：`records/<slug>.yaml` 存在（Extract 做過了）。
- `deliverable`：`output/<slug>/` 底下有檔案（Render 做過了）。

判定只看「有沒有檔案」，不看新舊。空資料夾一律算 `false`——建了資料夾但還沒放東西，不是做完。

一場 Meeting 只要在四個目錄的任何一個出現就會被列出來，所以 `raw_material: false` 但 `note: true` 是合法狀態（使用者刪掉了 Raw Material，或直接拿到別人給的 Note）。**不要**把這種情況當成資料壞掉。

三份模板清單列的是檔名，直接拿去給後續子指令用。只列副檔名對得上的檔案（`schema/*.yaml`、`markdown/*.j2`、`docx/*.docx`，Word 的 `~$` 鎖檔除外），README 或 `.gitkeep` 不會混進來。`templates/docx-source/` 底下的 .docx 還沒打洞、不能渲染，刻意不列在 `docx_templates` 裡。

使用者說某份模板在他手上卻沒出現在清單裡，先看副檔名對不對——例如 Markdown Template 存成 `custom.md` 而不是 `custom.md.j2`。

## 3. 回報

按階段講人話，重點是「下一步該做什麼」：

- 只有 Raw Material → 下一步跑 `mm-ingest`。
- 有 Note 沒 Minutes Record → 下一步跑 `mm-minutes`（它會做 Extract 與 Render）。
- 有 Minutes Record 沒 Deliverable → 跑 `mm-minutes`，它只會重新 Render，不會重跑 Extract。
- 全部完成 → 沒事要做；要改內容就直接編 `records/<slug>.yaml` 再重跑 `mm-minutes`。

`meetings` 是空的就告訴使用者把素材放進 `rawdata/<meeting>/`（`<meeting>` 建議 `YYYY-MM-DD-短描述`），不要幫他建空資料夾。三份模板清單都是空的，代表還沒跑過 `mm-init`。

## 邊界

- 這個 skill 不改任何東西。不要順手幫使用者建目錄、跑 Ingest 或刪掉看起來沒用的資料夾。
- 不要在宿主端安裝任何 Python 套件、不要建 venv、不要繞過容器直接跑 `scripts/mm.py`。理由見 `docs/adr/0004-all-code-runs-in-docker-compose.md`。

# 01 — 容器骨架與 `mm-init`

**What to build:** 使用者 clone 這個 repo 之後，呼叫一個 skill，就得到一個可以馬上開始工作的環境：完整的資料夾骨架、一套 default Minutes Schema、一份 default Markdown Template、一份 default Docx Template、一份保護會議內容的 `.gitignore`，以及一個已經 build 好的容器映像。若 Docker Desktop 沒啟動，使用者看到的是一句講清楚該做什麼的提示，不是連線失敗的堆疊訊息。

這一片同時定下後續所有 ticket 的骨架：唯一的 CLI 進入點（此時只有 `--help` 與版本資訊）、docker compose 的掛載權限、以及容器內跑 pytest 的測試形狀。Repo 目前沒有既有測試，這一片建立的形狀就是後續的 prior art。

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [x] 在一個乾淨的 repo 上執行 `mm-init`，`rawdata/`、`notes/`、`records/`、`output/`、`templates/{schema,markdown,docx,docx-source}/` 全部出現。
- [x] `templates/schema/` 有一套 default Minutes Schema，形狀為「正式會議記錄型」：meta 區塊（會議名稱、日期時間、地點、主席、記錄人、出席者、缺席者）＋議題清單（每則含題目、討論摘要、決議與 source）＋待辦清單（每則含事項、負責人、期限與 source）＋下次會議。決議巢狀在議題底下。
- [x] `templates/markdown/` 有一份能配 default Minutes Schema 的 default Markdown Template，使用 Jinja2 語法。
- [x] `templates/docx/` 有一份 default Docx Template：一份已標上 Jinja2 變數、能被 docxtpl 直接渲染的 .docx。
- [x] `glossary.yaml` 被建立（可為空骨架），且進版控。
- [x] `.gitignore` 讓 `rawdata/`、`notes/`、`records/`、`output/` 全部不進版控；`templates/`、`glossary.yaml`、`scripts/`、`.claude/`、`docs/` 仍進版控。
- [x] 映像自建，基底 `python:3.13-slim` + uv，依賴 pin 死：markitdown（extras `pdf,docx,pptx,xlsx,xls,outlook`，**不含音訊 extra**）、docxtpl、python-docx、jinja2、pyyaml、pytest。
- [x] compose 掛載權限正確：`rawdata`、`scripts`、`glossary.yaml` 唯讀；`notes`、`records`、`output`、`templates` 讀寫；`.git`、`.claude`、`docs` 不進容器。
- [x] 容器是一次性的（`docker compose run --rm`），跑完不留背景程序。
- [x] Docker daemon 沒啟動時，skill 停手並輸出一句明確指示使用者啟動 Docker Desktop 的訊息；不自動啟動背景程式，不退回宿主 Python。
- [x] CLI 單一進入點存在且可在容器內執行，`--help` 列出將來會有的子指令。
- [x] pytest 能在容器內執行並通過（此時至少有一條煙霧測試），後續 ticket 沿用同一形狀：準備 fixture 目錄、執行一次子指令、斷言檔案系統結果與 stdout JSON。
- [x] 宿主端全程沒有安裝任何 Python 套件、沒有建立 venv。

## Comments

實作完成，8 條測試在容器內全綠（`docker compose run --rm test`）。

兩個與 spec 字面不同的決定：

- 新增 `init` 子指令（spec 的清單裡沒有）。default Docx Template 是二進位 .docx，必須由 python-docx 產生，而 ADR-0004 禁止在宿主跑 Python，所以骨架建立收進容器內的 `init`，`mm-init` skill 只負責 daemon 健康檢查、`mkdir` 掛載點、`docker compose build`、`docker compose run --rm mm init`。
- default 模板（`templates/schema/default.yaml`、`templates/markdown/default.md.j2`、`templates/docx/default.docx`）**不在 HEAD 進版控**，由 `mm init` 產生。`scripts/mm.py` 是這三份 default 的唯一來源，避免同一份內容在 repo 裡有兩份會無聲漂移。`.gitignore` 沒有排除 `templates/`，使用者改過的模板照樣進版控（criterion 不變）。

依賴 pin 死靠 `uv.lock` + `uv sync --frozen`；`pyproject.toml` 本身不寫版本範圍。

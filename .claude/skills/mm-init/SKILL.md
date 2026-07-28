---
name: mm-init
description: 初始化 meeting-minutes 的工作環境 —— 建好資料夾骨架、default Minutes Schema、default Markdown Template、default Docx Template，並把容器映像 build 好。clone 這個 repo 之後跑一次；之後重跑是安全的，已存在的東西一律跳過。
---

# mm-init

一個 repo 跑一次。重跑安全：`mm init` 對已存在的檔案與目錄一律跳過，不覆蓋任何使用者改過的內容。

## 1. 先確認 Docker daemon

```bash
docker info
```

失敗就**停手**，原樣輸出這句話給使用者，不要繼續、不要重試、不要自動啟動任何背景程式，也不要退回宿主 Python：

> Docker daemon 沒有回應。請先啟動 Docker Desktop，等它的狀態變成 Running，再重新執行 mm-init。這個專案的所有程式都在容器內執行，宿主端不會安裝任何 Python 套件。

## 2. 建好 bind mount 需要的頂層目錄

`docker-compose.yml` 把這些目錄掛進容器，掛載前它們必須存在於宿主端：

```bash
mkdir -p rawdata notes records output templates
```

`glossary.yaml` 以唯讀**檔案**掛載。它在版控裡，clone 就有；但若不存在，Docker 會在那個路徑建一個**目錄**，掛載就壞了。所以先確認它是檔案：

```bash
test -f glossary.yaml || printf 'people: {}\nproducts: {}\nabbreviations: {}\ncorrections: {}\n' > glossary.yaml
```

## 3. Build 映像

```bash
docker compose build
```

第一次會花幾分鐘（`python:3.13-slim` + uv，依賴由 `uv.lock` pin 死）。先 build 好，之後真正跑流程時就不用等。

## 4. 建立骨架與 default 模板

```bash
docker compose run --rm mm init
```

`--rm` 讓容器跑完就消失，不留背景程序。stdout 是 JSON：

```json
{ "root": "/work", "created": ["templates/schema", "..."], "skipped": ["rawdata", "..."] }
```

## 5. 確認測試在容器內能過

```bash
docker compose run --rm test
```

這是本 repo 唯一的測試入口（`test` service 的 entrypoint 就是 pytest）。後續 ticket 的測試沿用同一形狀：準備 fixture 目錄、執行一次子指令、斷言檔案系統結果與 stdout JSON。

## 6. 回報

把 `created` 與 `skipped` 整理成人話告訴使用者，並提醒兩件事：

- `rawdata/`、`notes/`、`records/`、`output/` 已被 `.gitignore` 排除，客戶的會議內容不會進版控。
- `templates/` 與 `glossary.yaml` **會**進版控，改過之後記得 commit。

接下來把會議素材放進 `rawdata/<meeting>/`，`<meeting>` 建議用 `YYYY-MM-DD-短描述`。

## 邊界

不要在宿主端安裝任何 Python 套件、不要建 venv、不要繞過容器直接跑 `scripts/mm.py`。理由見 `docs/adr/0004-all-code-runs-in-docker-compose.md`。

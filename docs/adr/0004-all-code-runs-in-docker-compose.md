# 所有程式一律在 docker compose 內執行

任何會執行程式碼的步驟都透過 `docker compose run --rm` 進行。宿主端除了 Docker Desktop 之外**零安裝** —— 不裝 Python 套件、不裝 markitdown、不建 venv。

## Consequences

**腳本必須完全非互動。** 這是約束逼出來的紀律，而且是好的：`scripts/*.py` 吃 argv、吐 JSON 到 stdout、錯誤走 exit code。所有選單、確認、判斷與模型呼叫都留在 agent 端。容器只做確定性的機械工作。

**掛載權限刻意收緊。** `rawdata/` 以唯讀掛載——它是原始素材、不進 git、弄丟就沒了，而 Ingest 本來就只讀它，唯讀零成本。`.git`、`.claude`、`docs` 根本不進容器。`notes/` `records/` `output/` `templates/` 讀寫。

**依賴版本 pin 死。** 映像自建（`python:3.13-slim` + uv），確保行為可重現、可離線執行。代價是改依賴要記得手動 rebuild。

**綁定 Docker Desktop。** 每個用到容器的 skill 開頭先跑 `docker info`；daemon 沒啟動就停手並明確告知，不自動幫使用者啟動背景程式，也不偷偷退回宿主 Python（那會違背這份決定的全部意義）。

**每次呼叫多 1–2 秒容器啟動成本。** 選一次性容器而非常駐 service，換取零殘留與零生命週期管理。這些 skill 都是低頻的人為操作，啟動成本攤得很薄。

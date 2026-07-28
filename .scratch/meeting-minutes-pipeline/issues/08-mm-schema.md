# 08 — 維護 Minutes Schema

**What to build:** 使用者為不同會議型態維護不同的 Minutes Schema——專案週會一套、客戶驗收會一套——不被單一格式綁死。呼叫一個 skill，可以看到目前有哪些 Schema 可用、用互動的方式一欄一欄建立新的、或是從既有的複製一份再修改。使用者不需要去查 YAML 的寫法。

這一片純粹是 agent 端讀寫 YAML，不執行程式碼，因此不用容器。

**Blocked by:** 01 — 容器骨架與 `mm-init`

**Status:** ready-for-agent

- [ ] `mm-schema` skill 可手動呼叫，列出 `templates/schema/` 下目前可用的 Minutes Schema。
- [ ] 互動式建立新 Schema：一欄一欄詢問，使用者全程不需要看到或撰寫 YAML 語法。
- [ ] 能從既有 Schema 複製一份再修改。
- [ ] 產出的 Schema 支援巢狀結構（決議掛在議題底下）與清單型欄位（待辦），能表達真實會議記錄的形狀。
- [ ] 產出的 Schema 可直接被 `mm-minutes` 的 Extract 選用，形狀與 default Minutes Schema 一致。
- [ ] 不呼叫容器，也不需要 Docker daemon。

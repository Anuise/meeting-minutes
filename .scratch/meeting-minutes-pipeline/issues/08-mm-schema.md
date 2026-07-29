# 08 — 維護 Minutes Schema

**What to build:** 使用者為不同會議型態維護不同的 Minutes Schema——專案週會一套、客戶驗收會一套——不被單一格式綁死。呼叫一個 skill，可以看到目前有哪些 Schema 可用、用互動的方式一欄一欄建立新的、或是從既有的複製一份再修改。使用者不需要去查 YAML 的寫法。

這一片純粹是 agent 端讀寫 YAML，不執行程式碼，因此不用容器。

**Blocked by:** 01 — 容器骨架與 `mm-init`

**Status:** ready-for-agent

- [x] `mm-schema` skill 可手動呼叫，列出 `templates/schema/` 下目前可用的 Minutes Schema。
- [x] 互動式建立新 Schema：一欄一欄詢問，使用者全程不需要看到或撰寫 YAML 語法。
- [x] 能從既有 Schema 複製一份再修改。
- [x] 產出的 Schema 支援巢狀結構（決議掛在議題底下）與清單型欄位（待辦），能表達真實會議記錄的形狀。
- [x] 產出的 Schema 可直接被 `mm-minutes` 的 Extract 選用，形狀與 default Minutes Schema 一致。
- [x] 不呼叫容器，也不需要 Docker daemon。

## Comments

**2026-07-29 — 這一片沒有程式碼，也沒有測試。** 交付物只有 `.claude/skills/mm-schema/SKILL.md`。spec 的 Testing Decisions 明訂「SKILL.md 是提示詞，不進測試」，而本片依 spec 不加任何 CLI 子指令（列清單是 agent 直接 `ls` 加讀檔），所以沒有可測的接縫。既有測試照跑，確認沒被打壞。

**2026-07-29 — `type` 收斂成封閉集合。** default schema 用到 `text`、`date`、`datetime`、`people`、`source`、`list` 六種，原本只是隱含在那一份檔案裡。互動式建立會遇到「預算金額」「是否通過」這種問法，不明講就會長出 `number`、`bool` 這類新 type，而 Extract 與 Render 都不認得，會安靜漏掉。SKILL.md 把六種寫成表，並要求塞不進去的一律用 `text` 承接。真的需要第七種時，得同步改 Extract 與 Render，屬於另一張票。

**2026-07-29 — 巢狀寫成兩層的預設，不寫成上限。** 議題底下掛決議是 default 的形狀，也是驗收條件要的。原本寫成硬上限，但 spec 沒有設過這條界線，替使用者關一扇 spec 沒關的門不對；改成「第三層先確認他真的需要」。

**2026-07-29 — 補上 Minutes Record 的落地形狀。** 只描述 schema 檔的形狀不夠：`meta` 收在 `meta.<key>`、`body` 的區塊攤平在最上層，這件事只藏在 `DEFAULT_MARKDOWN_TEMPLATE` 裡。不寫出來，互動式建立會長出 `key: meta` 的 body 區塊，一渲染就與 meta 撞名。SKILL.md 補了落地形狀與兩條命名規則。

**2026-07-29 — 列清單是本 skill 自己 `ls`，不走 03 的 `list` 子指令。** spec.md:136 把掃描收斂進 CLI 的理由是「不會與 `mm-minutes` 的 picker 各寫一份而漂移」，而同一段又明文豁免 `mm-schema` 用容器。兩者相衝時以豁免為準——為了列個目錄而要求 Docker daemon，會讓「純寫 YAML」這件事平白多一個前置條件。代價是 schema 清單有兩個來源，`list` 的輸出格式若改變，這裡不會自動跟上。

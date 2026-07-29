---
name: mm-schema
description: 維護 Minutes Schema —— 列出 templates/schema/ 底下目前有哪些可用、以一問一答建立新的一套、或從既有的複製一份再改。使用者全程不需要看到或撰寫 YAML。不用容器，也不需要 Docker daemon。
---

# mm-schema

Minutes Schema 決定 Minutes Record **記什麼**；它不決定 Deliverable **長什麼樣**——那是 Markdown Template 與 Docx Template 的事，三者不強制綁定。

這是七個 skill 中唯一不進容器的：只讀寫 `templates/schema/` 底下的 YAML，不執行任何程式碼。**不要跑 `docker info`，也不要跑 `docker compose`。**

一條貫穿全程的規則：**使用者不看 YAML。** 用欄位名稱與中文標籤跟他對話，YAML 由你寫。要覆述內容時用清單講，不要貼原始檔。

## 1. 列出現有 Schema

```bash
ls templates/schema
```

把每一份讀進來，一套一行報給使用者：檔名、`label`、meta 有幾個欄位、主體有哪些區塊。

目錄不存在或是空的，代表還沒跑過 `mm-init`，請使用者先跑，不要自己補建目錄或補寫 default。

使用者只是想知道有什麼可選，列完就結束。

## 2. 問使用者要做哪一件事

三選一，不要自己猜：

- 只是想看清單 —— 做完第 1 步就結束。
- **從既有複製一份再改**（第 4 節）—— 要做的是相似變體時最快。
- **從頭建立一套新的**（第 5 節）。

## 3. Schema 的形狀

以下是給你看的，不要貼給使用者。權威範例是 `templates/schema/default.yaml`，動手前先讀它一次。

```yaml
name: <檔名的 stem，英文 snake_case>
label: <中文，一句話講這套用在什麼會議>

meta:
  - { key: title, label: 會議名稱, type: text }

body:
  - key: topics
    label: 議題
    type: list
    fields:
      - { key: title, label: 題目, type: text }
      - key: resolutions
        label: 決議
        type: list
        fields:
          - { key: text, label: 決議內容, type: text }
          - { key: source, label: 來源, type: source }

  - { key: next_meeting, label: 下次會議, type: text }
```

`type` 是**封閉集合**，六個值，不要自創：

| type | 意思 | Minutes Record 裡是什麼 |
| --- | --- | --- |
| `text` | 一段文字 | 字串 |
| `date` | 日期 | `YYYY-MM-DD` 字串 |
| `datetime` | 日期加時間 | `YYYY-MM-DD HH:MM` 字串 |
| `people` | 一組人名 | 字串清單 |
| `source` | 指回 Note 的引用 | `notes/<meeting>/<note>#L<行>` 字串 |
| `list` | 重複出現的項目 | 物件清單，子欄位由 `fields` 定義 |

使用者要的欄位塞不進這六種時（例如「預算金額」「是否通過」），問清楚他想怎麼呈現，然後用 `text` 承接，**不要**新增 type。第七種 type 沒有任何一段程式碼或模板認得它：Extract 不知道該把它填成什麼形狀，`templates/` 下的模板也不會有對應寫法。真的需要，得連同 Extract 與模板一起改，那是另一張票。

Minutes Record 落地時的形狀：`meta` 底下的欄位收在 `meta.<key>`，`body` 底下的區塊則**攤平在最上層**（`topics`、`action_items`、`next_meeting` 就是這樣被模板引用的）。這是模板寫法的依據，也是下面兩條命名規則的由來。

其餘規則：

- `meta` 只放單層欄位，不放 `list`。它是會議的基本資料。
- `body` 可以放單層欄位（如 `next_meeting`），也可以放 `list`。`body` 的 `key` **不能叫 `meta`**，也不能與另一個 `body` 的 `key` 重複——它們攤在同一層，會互相蓋掉。
- `type: list` 一定要有 `fields`；`fields` 裡可以再放一層 `list`（決議掛在議題底下就是這樣來的）。兩層是實際會議記錄需要的深度；使用者想要第三層時先確認他真的需要，再深下去模板會難寫。
- 任何**會被拿出去引用查證**的紀錄（決議、待辦這類）都要有一個 `type: source` 的欄位。Extract 靠它指回 Note；schema 裡沒宣告這個欄位，抽出來的決議就沒有地方掛來源，日後被質疑時查不到。
- `key` 用英文 snake_case（它會變成模板裡的變數名），`label` 用中文（它是使用者看到的字）。同一層裡 `key` 不能重複。
- 最上層的 `name` 必須等於檔名的 stem：`templates/schema/client-signoff.yaml` 的 `name` 就是 `client-signoff`。

## 4. 從既有複製一份再改

1. 列出現有 Schema，讓使用者選一份當底稿。
2. 問新的檔名與 `label`。
3. 把底稿的欄位一區一區報給他（先 meta，再 body 的每個區塊），每一區問一次「這一區要加什麼、刪什麼、改什麼標籤？」不要一次把整份丟出去要他逐字校對。
4. 沒被提到的欄位原封不動保留，包括註解。

## 5. 從頭建立一套

一次問一件事，每一題都給預設值，使用者說「用預設」就往下走。順序：

1. **這套用在什麼會議？** —— 變成 `label`，也決定接下來該問什麼。
2. **檔名。** 由 `label` 給個建議（客戶驗收會 → `client-signoff`），讓他確認。
3. **meta 區塊。** 以 `default.yaml` 的 meta 欄位為起點，整組報給他，問要刪哪些、加哪些。
4. **主體有哪些區塊？** 以 `default.yaml` 的 body 區塊為起點。每一個問清楚是「只出現一次」還是「會有很多筆」——後者就是 `list`。
5. **每個 list 的子欄位。** 一個 list 問一輪。問完子欄位，接著問「這裡面有沒有需要再細分成多筆的東西？」有的話就是巢狀 list（例如議題底下的決議）。
6. **source。** 每個 list 都提醒一次：這一區的內容日後會被拿出來引用嗎？會的話就加 `source`。使用者說不用，尊重他，但要說清楚這一區日後查不到出處。

## 6. 寫檔

寫到 `templates/schema/<name>.yaml`。

- 檔名已存在就**先問**，不要直接覆蓋。
- **不要動 `templates/schema/default.yaml`**，除非使用者明確要求改的就是它。它是所有人的起點。
- 檔頭放兩行註解：這套用在什麼會議、從哪一份複製而來（如果是複製的）。欄位有不明顯的取捨時，在該行上方留一行註解說明理由。
- 寫完把結果覆述成人話讓使用者確認：meta 有哪些欄位、主體有哪些區塊、哪些區塊會有多筆、哪些帶 source。

## 7. 回報

- `templates/` **進版控**，改完提醒使用者 commit。
- 這套 Schema 之後會出現在 `mm-minutes` 的選單裡，選它就會照這些欄位抽。
- Schema 與模板不綁定：模板裡有而 Schema 裡沒有的變數，渲染時會留空。想知道對不上的有哪些，跑 `mm-check`——它只報告，不阻擋。

## 邊界

- 不呼叫容器，不做 Docker daemon 健康檢查，也不跑 `scripts/mm.py`。這一片沒有任何程式碼要執行，所以 `docs/adr/0004-all-code-runs-in-docker-compose.md` 沒有東西可以管——它不是那條規則的例外。
- 不碰 `records/`。改 Schema **不會**改寫既有的 Minutes Record，也不要試著幫使用者遷移——那是重新 Extract 的事。
- 不改 `templates/markdown/` 與 `templates/docx/`。使用者要模板配合新 Schema 就轉給 `mm-template`。
- 不要求使用者寫或讀 YAML，也不要因為某個模板碰巧有某個變數，就擅自往 Schema 加欄位。

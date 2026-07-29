---
name: mm-template
description: 維護兩種模板 —— 把客戶給的 .docx 打洞成可渲染的 Docx Template（先掃出候選欄位、提對照表讓使用者逐項確認、再就地替換），或以互動方式建立 Markdown Template；也列出目前有哪些模板可用。使用者不需要自己在 Word 裡打 Jinja2 標記，原始的 Docx Source 也絕對不會被改到。
---

# mm-template

模板決定 Deliverable **長什麼樣**；它不決定 Minutes Record **記什麼**——那是 Minutes Schema 的事（`mm-schema`），三者不強制綁定。

兩條規則貫穿全程：

- **使用者不看 Jinja2。** 用「這一格是會議名稱、那一格是主席」跟他對話，標記由你寫。
- **不亂猜。** 打洞前一定把完整對照表逐項報給他確認過，沒確認就不要跑 `apply-docx`。

## 1. 問使用者要做哪一件事

不要自己猜：

- 只是想看有哪些模板可用 —— 做完第 2 節就結束。
- **把 Docx Source 打洞成 Docx Template**（第 3 節）—— 客戶給了一份 .docx 樣板時走這條。
- **建立 Markdown Template**（第 4 節）。

只做第 4 節不需要容器，也不必做 Docker 健康檢查——那一片只是寫一個 `.j2` 文字檔。

## 2. 列出目前有哪些模板

先確認 Docker daemon：

```bash
docker info
```

失敗就**停手**，原樣輸出這句話給使用者，不要繼續、不要重試、不要自動啟動任何背景程式，也不要退回宿主 Python：

> Docker daemon 沒有回應。請先啟動 Docker Desktop，等它的狀態變成 Running，再重新執行 mm-template。這個專案的所有程式都在容器內執行，宿主端不會安裝任何 Python 套件。

```bash
docker compose run --rm mm list
```

stdout 的 JSON 裡 `markdown_templates` 與 `docx_templates` 就是目前可用的模板，直接拿檔名報給使用者。兩份清單都是空的代表還沒跑過 `mm-init`，請他先跑，不要自己補建目錄或補寫 default。

還沒打洞的素材不在上面那份清單裡（它們不能拿來渲染），另外看：

```bash
ls templates/docx-source
```

## 3. 把 Docx Source 打洞成 Docx Template

### 3.1 掃描

```bash
docker compose run --rm mm scan-docx "客戶樣板.docx"
```

回傳的 `items` 是文件上每一段文字，照文件順序，重複的文字只列一次：

```json
{
  "source": "客戶樣板.docx",
  "items": [
    { "where": "header", "kind": "paragraph", "text": "MoBagel 行動貝果｜內部文件" },
    { "where": "body", "kind": "paragraph", "text": "2026 年度客戶驗收會議記錄" },
    { "where": "body", "kind": "cell", "text": "日期", "table": 0, "row": 0, "column": 0 },
    { "where": "body", "kind": "cell", "text": "2026-07-28", "table": 0, "row": 0, "column": 1 }
  ]
}
```

- `where`：`body`、`header`、`footer`。
- `kind`：`paragraph` 或 `cell`；`cell` 另外帶 `table`／`row`／`column`，用它判斷「左邊是標籤、右邊是值」。
- `text` 是**整段**文字。Word 常把一句話拆成好幾個 run，掃描已經在段落層級接回來了，所以你看到的就是使用者眼裡的那一句。

### 3.2 判斷哪些是變動欄位

只換**值**，不換**標籤**——標籤是客戶格式的一部分。

| 換 | 不換 |
| --- | --- |
| 每場會議都不一樣的具體內容：會議名稱、日期時間、地點、人名、議題、決議、待辦、下次會議 | 表格的欄位名（「日期」「主席」「事項」）、句子裡的固定字（「會議名稱：」） |
| 頁首頁尾裡確實會變的東西（例如文件編號、會議日期） | 公司名、logo、頁碼、保密聲明、法律條文 |

拿不定主意的就**列出來問**，不要自己決定。寧可多問一項，也不要把客戶的固定格式打成一個洞。

### 3.3 決定變數名

變數名要對得上 Minutes Schema 的 key，否則渲染時只會留空。動手前先讀一次 `templates/schema/default.yaml`（或使用者打算搭配的那一套），常見對應：

| 文件上的東西 | 變數 |
| --- | --- |
| 會議名稱 | `{{ meta.title or '未提及' }}` |
| 日期時間／地點／主席／記錄人 | `{{ meta.datetime or '未提及' }}` 等 |
| 出席者、缺席者（多個人名） | `{{ meta.attendees \| default([], true) \| join('、') or '未提及' }}` |
| 下次會議 | `{{ next_meeting or '未提及' }}` |

一律加 `or '未提及'`：Extract 抓不到的欄位會留空，客戶文件上不該出現一個沒人知道為什麼的空格。寫法與 `templates/docx/default.docx` 一致，兩份模板讀起來才一樣。

### 3.4 提對照表給使用者逐項確認

一項一行，講人話，把「文件上的哪一段」對到「這是什麼欄位」：

> 1. 「2026 年度客戶驗收會議記錄」（本文標題）→ 會議名稱
> 2. 「2026-07-28」（表格第 1 列右欄）→ 日期時間
> 3. 「王小明」（表格第 2 列右欄，以及最後一段）→ 主席
> 4. 「MoBagel 行動貝果｜內部文件」（頁首）→ 不動，這是公司名

要提醒他兩件事：

- 對照表以**文字**為鍵，同一段文字在文件上出現幾次就會被換幾次。所以第 3 項那個人名在最後一段裡也會被換掉——這通常正是他要的，但要講出來。
- 別挑太短的字（單一個「王」、單一個「1」），會誤傷。挑能唯一辨識的整段文字。

### 3.5 套用

對照表走 stdin（`-T` 不能省，不然 docker 會吃掉 stdin）：

```bash
docker compose run --rm -T mm apply-docx "客戶樣板.docx" <<'JSON'
[
  { "text": "2026 年度客戶驗收會議記錄", "variable": "{{ meta.title or '未提及' }}" },
  { "text": "2026-07-28", "variable": "{{ meta.datetime or '未提及' }}" },
  { "text": "王小明", "variable": "{{ meta.chair or '未提及' }}" }
]
JSON
```

- 輸出到 `templates/docx/`，檔名預設與 Docx Source 同名；要改就加 `--output 別的名字.docx`（必須是 `.docx`）。
- 目標已存在會**報錯不覆蓋**。使用者確定要蓋掉才加 `--force`。改對照表重跑很正常，這是刻意讓他自己決定的。
- `templates/docx-source/` 底下的原檔不會被動到，隨時能重新來過。
- 頁首頁尾、logo、字型與表格樣式都留在原地，因為打洞只換段落裡的文字，不重建文件。

回傳的 `unmatched` 是**沒被打洞的原文**。它不是空的就要立刻回報使用者，並回頭看 `scan-docx` 的 `items` 是哪個字打錯了——那些欄位的原文還留在模板上，渲染時會原封不動出現在交付檔裡。除了打錯字，另一個常見原因是那一段裡有超連結：連結文字動不了，所以整段跳過，請使用者在 Word 裡把那一段的超連結移掉再重跑。

另外，替換是在段落層級合併 run 之後做的，所以同一段裡本來一半粗體一半不粗體的話，整段會統一成第一個 run 的格式。段落樣式、字型、表格樣式都不受影響。使用者的樣板真的靠段落內的粗細來表達重點時，先告知他這個代價。

### 3.6 需要跟著長出多列的表格

打洞只換文字，變不出新的一列。客戶樣板的待辦事項表格通常只有一列範例，要讓它跟著 Minutes Record 有幾筆就長幾列，得請使用者先在 Word 裡動一下 Docx Source：在範例列的**前後各插一列**，各隨手打一個標記字（例如「迴圈開始」「迴圈結束」），存檔後重新 `scan-docx`。然後把標記換成 docxtpl 的列迴圈：

```json
[
  { "text": "迴圈開始", "variable": "{%tr for item in action_items %}" },
  { "text": "迴圈結束", "variable": "{%tr endfor %}" },
  { "text": "補上錯誤訊息", "variable": "{{ item.task or '未提及' }}" },
  { "text": "張大同", "variable": "{{ item.owner or '未提及' }}" }
]
```

`{%tr %}` 會把它所在的那一整列吃掉，所以標記一定要獨立成列，不能跟內容擠在同一列。段落層級的重複（例如一則一則的議題）同理，用 `{%p for topic in topics %}` 放在自己的空段落裡。權威範例是 `templates/docx/default.docx`，不確定寫法就先掃它一次看看。

### 3.7 驗證

打完洞不要就說完成了。請使用者拿一場已經有 Minutes Record 的 Meeting 跑 `mm-minutes` 選這份新模板，實際開出來的 .docx 才算數。他手上還沒有任何 Minutes Record 的話，講清楚這份模板還沒被渲染過。

## 4. 建立 Markdown Template

`templates/markdown/default.md.j2` 是權威範例，動手前先讀它一次。使用者要的通常是它的變體，一次問一件事，每一題都給預設值：

1. **這份模板用在什麼場合？** 決定檔名，`.md.j2` 結尾（`templates/markdown/client-signoff.md.j2`）。
2. **要哪些區塊、什麼順序？** 以 default 的區塊為起點（會議基本資料表、議題、待辦事項表、下次會議），問要刪哪些、加哪些、換順序。
3. **每個區塊長什麼樣？** 表格還是清單、要不要顯示 source。
4. 空值一律 `or '未提及'`，多值欄位用 `| default([], true) | join('、')`，清單型欄位用 `{% for %}`。變數名對齊使用者打算搭配的 Minutes Schema。

寫檔規則同 `mm-schema`：檔名已存在就**先問**，不要直接覆蓋；**不要動 `default.md.j2`**，除非使用者明確要求改的就是它。寫完把結果覆述成人話讓他確認，不要貼 Jinja2 原始碼。

## 5. 回報

- `templates/` **進版控**，改完提醒使用者 commit。`templates/docx-source/` 底下的客戶原檔也在版控裡，那是刻意的——它是重新打洞的唯一素材。
- 新模板會出現在 `mm-minutes` 的選單裡。
- 模板與 Minutes Schema 不綁定：模板裡有而 Schema 裡沒有的變數，渲染時會留空。想知道對不上的有哪些，跑 `mm-check`——它只報告，不阻擋。

## 邊界

- 不寫 `templates/docx-source/`。原檔是使用者唯一一份客戶素材，`scan-docx` 與 `apply-docx` 都只讀它。使用者要改樣板本身（例如加標記列），請他在 Word 裡改，不要幫他改。
- 不在宿主端用 python-docx 直接改檔、不建 venv、不繞過容器跑 `scripts/mm.py`。理由見 `docs/adr/0004-all-code-runs-in-docker-compose.md`。
- 不碰 `records/` 與 `output/`。換模板不會改內容，重新產出是 `mm-minutes` 的事。
- 不改 `templates/schema/`。使用者要的欄位 Schema 裡沒有，轉給 `mm-schema`，不要為了讓模板有東西可讀就自己去加欄位。
- 沒讓使用者確認過對照表就不要跑 `apply-docx`；`unmatched` 不是空的就不要說打洞成功。

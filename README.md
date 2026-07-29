# meeting-minutes

把一場會議留下的雜亂素材（簡報、既有文件、逐字稿）變成一份可交付的正式會議記錄。

你不需要自己跑指令、也不需要寫 YAML 或在 Word 裡標記變數。整個流程都由 Claude Code 的 skills 帶你走，你只要把檔案放進資料夾，然後說一句話。

---

## 前置需求

| 需要 | 說明 |
| --- | --- |
| Docker Desktop | 這個專案**所有程式都在容器內執行**，宿主端不會裝任何 Python 套件。用之前先確認它的狀態是 Running。 |
| Claude Code | 在這個 repo 的根目錄開啟，skills 才讀得到。 |

Docker 沒開的話 skill 會直接停手並叫你去開，不會偷偷退回宿主 Python。

---

## 怎麼呼叫 skill

兩種都可以，效果一樣：

- 打斜線指令：`/mm-minutes`
- 直接用人話說：「幫我產出 7/28 週會的會議記錄」

用人話說時 Claude 會自己挑對應的 skill。不確定該用哪個就先跑 `/mm-list`。

---

## 第一次使用

Clone 完之後跑一次：

```
/mm-init
```

它會建好資料夾骨架、放進一套 default 的 Minutes Schema 與模板、build 好容器映像。重跑是安全的 —— 已存在的東西一律跳過，不會蓋掉你改過的內容。

---

## 日常流程

### 1. 把素材放進去

在 `rawdata/` 底下開一個資料夾，名字就是這場會議的代號（建議 `YYYY-MM-DD-短描述`），把檔案**原封不動**丟進去：

```
rawdata/
└── 2026-07-28-project-weekly/
    ├── slides.pptx
    ├── 逐字稿.docx
    └── 上次的會議記錄.pdf
```

支援：PDF、Word、PowerPoint、Excel、HTML、CSV、JSON、XML、EPub、Outlook 郵件。

**不支援錄音與圖片。** 錄音要先用外部工具轉成逐字稿再放進來；白板照要自己補一份文字說明。這是刻意的設計（見 `docs/adr/0003`、`docs/adr/0005`），skill 不會幫你硬轉。

### 2. 產出會議記錄

```
/mm-minutes
```

它會請你選四樣東西（都從清單挑，不用手打）：

1. **會議** —— 要處理哪一場
2. **Minutes Schema** —— 要記哪些欄位
3. **Markdown Template** —— markdown 長什麼樣
4. **Docx Template** —— 要不要順便產一份 .docx（預設不產，你沒說就不產）

然後它會一路跑完：轉檔 → 讀素材抽出內容 → 套模板渲染 → 交付前檢查。

### 3. 拿檔案

```
output/2026-07-28-project-weekly/
├── minutes.md
└── minutes.docx   ← 只有選了 Docx Template 才有
```

`/mm-minutes` 跑完會告訴你哪些格子沒填到（在交付檔上顯示為「未提及」）、哪些決議缺出處。**它不會替你猜內容** —— 素材裡沒講到的就留空。

---

## 全部 skills

| Skill | 什麼時候用 |
| --- | --- |
| `/mm-init` | Clone 完跑一次。建骨架、default 模板、build 映像。 |
| `/mm-list` | 想知道每場會議走到哪一步、目前有哪些 Schema 與模板可用。 |
| `/mm-minutes` | **主要入口。** 產出一場會議的記錄，一次走完全部階段。 |
| `/mm-ingest` | 只想把素材轉成 markdown、先檢查轉檔結果。`/mm-minutes` 需要時會自動跑，通常不用單獨呼叫。 |
| `/mm-check` | 交付前的體檢：哪些欄位空的、哪些決議缺出處、模板變數有沒有對不上。`/mm-minutes` 最後也會自動跑一次。 |
| `/mm-schema` | 要改「記哪些欄位」時用。一問一答建立新的一套，或從既有的複製再改。你全程不用看到 YAML。 |
| `/mm-template` | 客戶給了一份 .docx 範例，要把它變成可渲染的模板（打洞）。也可以建立新的 markdown 模板。你不用自己在 Word 裡標 Jinja2，原始檔絕對不會被改到。 |

---

## 想改東西的時候

| 你想做的事 | 怎麼做 |
| --- | --- |
| 改錯字、補負責人、補地點 | 直接編 `records/<會議>.yaml`，再跑一次 `/mm-minutes`。它只會重新渲染，**不會重抽**，你改的東西不會被蓋掉。 |
| 補了新素材，要納進來 | 檔案放進 `rawdata/<會議>/`，然後**明確要求重抽**（說「重抽」或 `--reextract`）。只補素材重跑是不會納入新素材的。 |
| 換一份 Word 樣板 | 重跑 `/mm-minutes`，換選一份 Docx Template。不重抽、不重讀素材。 |
| 換要記的欄位 | `/mm-schema` 建一套新的，下次跑 `/mm-minutes` 時選它。 |
| 客戶給了新的 .docx 範例 | `/mm-template` 把它打洞成 Docx Template。 |

---

## 檔案放在哪

| 路徑 | 是什麼 | 進版控？ |
| --- | --- | --- |
| `rawdata/<會議>/` | 你丟進來的原始檔案。系統只讀，絕不寫。 | ❌ |
| `notes/<會議>/` | 轉出來的 markdown。抽取階段唯一讀得到的形式。 | ❌ |
| `records/<會議>.yaml` | **會議記錄的內容本身。唯一的真實來源。** 可以手改，交付檔都由它渲染而來。 | ❌ |
| `output/<會議>/` | 實際交出去的檔案。可拋棄，隨時能重建。 | ❌ |
| `templates/` | Minutes Schema、Markdown Template、Docx Template。 | ✅ 改過記得 commit |
| `glossary.yaml` | 人名、職稱、產品名、縮寫對照。每次抽取都會送進去，避免專有名詞寫錯。 | ✅ 改過記得 commit |

前四項被 `.gitignore` 排除 —— **客戶的會議內容不會進版控**。

想讓專有名詞不再被寫錯，就去補 `glossary.yaml`，那是唯一該動的地方。

---

## 深入了解

- `CONTEXT.md` —— 這個專案的詞彙表：Meeting、Note、Minutes Record、Deliverable 各自是什麼、界線在哪
- `docs/adr/` —— 幾個一開始就定下、不打算回頭的決定（不吃音訊、不吃圖片、Minutes Record 是唯一來源、所有程式都跑在容器裡）

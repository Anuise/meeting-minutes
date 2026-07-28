# Spec: Meeting Minutes Pipeline

Status: ready-for-agent

## Problem Statement

一場會議結束後，留下來的是一堆散落的東西：投影片、白板照片、事前發的 PDF、事後別人丟來的 Word 文件、以及自己用別的工具轉出來的逐字稿。要把這些變成一份能交出去的正式會議記錄，目前得手動做三件都很煩的事：

1. 一個一個打開來讀，格式各異，有些還得先轉檔才看得懂。
2. 自己在腦中彙整出「誰出席、討論了什麼、決議是什麼、誰要在什麼時候前做什麼」。
3. 再把彙整結果手動排進客戶或公司規定的 Word 樣板裡——樣板每個客戶都不一樣。

做完之後，如果發現有一句話寫錯，或是客戶臨時說要換一份樣板，整個第 3 步得重來。而且沒有人能查證「這條決議到底是誰在哪裡講的」。

## Solution

一組七個 skill，把上述流程切成三個彼此獨立的階段，中間以一份結構化的 Minutes Record 銜接。

- **Ingest** 把 Raw Material 機械轉成 Note，使用者不需要在意原始格式。
- **Extract** 讀 Note，依選定的 Minutes Schema 產出 Minutes Record。這是唯一呼叫模型的步驟，每筆決議與待辦都帶 source 指回 Note，抓不到的欄位一律留空。
- **Render** 把 Minutes Record 套上 Markdown Template 與（選填的）Docx Template，產出 Deliverable。不呼叫模型，可以無限次重跑。

因為內容與呈現分離，「改一句話」變成改 Minutes Record 再重新 Render，「換一份樣板」變成換一個 Docx Template 再重新 Render——兩者都不需要重新讀素材，也不需要重新呼叫模型。

所有會執行程式碼的部分都在 docker compose 內跑，使用者的環境除了 Docker Desktop 之外不需要安裝任何東西。

## User Stories

### 初始化

1. 作為新使用者，我想要一個指令就建好整個資料夾骨架，這樣我不用照著文件手動 mkdir 七個目錄。
2. 作為新使用者，我想要初始化時就拿到一套堪用的 default Minutes Schema，這樣我第一場會議就能直接開始，不用先設計欄位。
3. 作為新使用者，我想要初始化時就拿到一份 default Markdown Template 與一份 default Docx Template，這樣我在還沒有客戶樣板時也能產出交付檔。
4. 作為新使用者，我想要初始化時自動建好 `.gitignore`，這樣客戶的會議內容不會在我沒注意的時候被 commit 進版控。
5. 作為新使用者，我想要初始化時就把容器映像 build 好，這樣第一次真正跑流程時不用等好幾分鐘。
6. 作為使用者，我想要在 Docker Desktop 沒啟動時得到一句話講清楚的提示，而不是一串 npipe 連線失敗的堆疊訊息。

### 放素材與 Ingest

7. 作為使用者，我想要把任何格式的會議素材直接丟進 Raw Material 目錄，這樣我不用先想「這個格式支援嗎」。
8. 作為使用者，我想要 Ingest 自動處理 PDF、Word、PowerPoint、Excel、HTML、CSV、JSON、XML、EPub、Outlook 郵件與圖片，這樣絕大多數素材都不用我先手動轉檔。
9. 作為使用者，我想要 Ingest 遇到錄音檔時明確告訴我「不支援，請先自行轉逐字稿」，而不是安靜跳過讓我以為它處理了。
10. 作為使用者，我想要 Ingest 跳過已經轉過而且沒有變動的檔案，這樣素材很多時重跑很快。
11. 作為使用者，我想要 Ingest 在某一個檔案轉失敗時繼續處理其他檔案，最後一次列出所有失敗的項目，這樣一個壞掉的 PDF 不會擋住整批。
12. 作為使用者，我想要 Note 的檔名看得出它來自哪一個 Raw Material，這樣我看到 source 引用時能立刻找到原檔。
13. 作為使用者，我想要確信 Ingest 絕對不會寫入 Raw Material 目錄，因為那是我唯一一份原始素材而且不在版控裡。

### Minutes Schema

14. 作為使用者，我想要看到目前有哪些 Minutes Schema 可用，這樣我知道有什麼選擇。
15. 作為使用者，我想要用互動的方式建立一套新的 Minutes Schema，一欄一欄問我，這樣我不用去查 YAML 的寫法。
16. 作為使用者，我想要從既有的 Minutes Schema 複製一份再修改，這樣建立相似的變體很快。
17. 作為使用者，我想要 Minutes Schema 支援巢狀結構（例如決議掛在議題底下）與清單型欄位（例如待辦事項），這樣它能表達真實會議記錄的形狀。
18. 作為使用者，我想要為不同會議型態維護不同的 Minutes Schema（專案週會一套、客戶驗收會一套），這樣我不用被單一格式綁死。

### 模板

19. 作為使用者，我想要用互動的方式建立 Markdown Template，這樣我能控制交付的 markdown 長什麼樣子。
20. 作為使用者，我想要把客戶給的 .docx 放進 Docx Source 目錄，然後由系統協助我把它變成可渲染的 Docx Template，這樣我不用自己在 Word 裡土法煉鋼打 Jinja2 標記。
21. 作為使用者，我想要在打洞前看到一份「哪些段落是變動欄位、建議變數名叫什麼」的對照表，並且能逐項修改，這樣我不用擔心系統亂猜。
22. 作為使用者，我想要打洞後的 Docx Template 完整保留原始的頁首頁尾、logo、字型與表格樣式，這樣交出去的文件看起來就是客戶自己的格式。
23. 作為使用者，我想要打洞流程正確處理 Word 把一句話拆成多個 run 的情況，這樣「會議名稱」這種被拆散的字串也能被正確替換。
24. 作為使用者，我想要打洞絕對不會修改到 Docx Source 的原檔，這樣我隨時能重新來過。
25. 作為使用者，我想要看到目前有哪些 Markdown Template 與 Docx Template 可用。

### 產出會議記錄

26. 作為使用者，我想要用一個指令走完整個產出流程，這樣日常使用我只要記一個字。
27. 作為使用者，我想要從清單中選擇 Meeting，而不是手打資料夾名稱，這樣不會因為打錯字而失敗。
28. 作為使用者，我想要從清單中選擇要用哪一套 Minutes Schema。
29. 作為使用者，我想要從清單中選擇要用哪一份 Markdown Template。
30. 作為使用者，我想要能夠選擇不使用任何 Docx Template，這種情況下就只產出 markdown、不產出 .docx。
31. 作為使用者，我想要在 Note 還沒產生或比 Raw Material 舊的時候，主流程自動幫我跑 Ingest 並告知它這麼做了，這樣我不會因為忘記一個步驟而中斷。
32. 作為使用者，我想要 Extract 產出的每一筆決議與待辦都帶著 source，指回是哪一份 Note 的哪一段，這樣別人質疑時我查得到。
33. 作為使用者，我想要 Extract 抓不到的欄位一律留空、在 Deliverable 上顯示「未提及」，絕不自行推測，這樣會議記錄可以被當成依據引用。
34. 作為使用者，我想要 Extract 時把 Glossary 一併送進去，這樣人名、產品名、縮寫不會被寫錯。
35. 作為使用者，我想要 Render 之後拿到 markdown 交付檔，以及（若有選 Docx Template）一份 .docx 交付檔。
36. 作為使用者，我想要 Render 完成後看到一份「哪些變數沒有被填到」的清單，這樣我在交出去之前知道有哪些空格。

### 修改與重跑

37. 作為使用者，我想要能直接手動編輯 Minutes Record 來修正錯字或補上負責人，這樣小修改不需要重新呼叫模型。
38. 作為使用者，我想要在 Minutes Record 已存在時重跑主流程只會重新 Render、不會重新 Extract，這樣我花時間校對過的內容不會被機器覆蓋掉。
39. 作為使用者，我想要在明確要求時（而不是預設）才重新 Extract，這樣行為是我控制的。
40. 作為使用者，我想要換一份 Docx Template 重新產出時，內容與 markdown 版本完全一致，這樣兩份檔案可以互相對帳。
41. 作為使用者，我想要 Deliverable 目錄可以隨時整個刪掉重建，這樣我不用擔心誤刪。
42. 作為使用者，我想要 Minutes Record 存放在與 Deliverable 分開的地方，這樣清理 Deliverable 不會弄丟我手動修改過的內容。

### 導覽與檢查

43. 作為使用者，我想要看到所有 Meeting 各自進行到哪一步（有沒有 Raw Material、有沒有 Note、有沒有 Minutes Record、有沒有 Deliverable），這樣我知道哪些還沒做完。
44. 作為使用者，我想要在產出前後看到 Minutes Record 有哪些欄位是空的。
45. 作為使用者，我想要看到有哪些決議或待辦缺少 source。
46. 作為使用者，我想要看到選定的模板裡有哪些變數在選定的 Minutes Schema 中找不到對應。
47. 作為使用者，我想要檢查只列出清單、不阻擋流程，這樣我自己判斷哪些要處理、哪些可以接受。

### Glossary

48. 作為使用者，我想要維護一份專案共用的人名、職稱、產品名、縮寫與常見誤譯對照，這樣每一場會議都受益。
49. 作為使用者，我想要 Glossary 進版控，這樣它的變更有歷史。

### 環境

50. 作為使用者，我想要除了 Docker Desktop 之外不需要在自己的電腦上安裝任何 Python 套件，這樣這個專案不會污染我的環境。
51. 作為使用者，我想要依賴版本被鎖死，這樣今天能跑的東西明天還能跑。
52. 作為使用者，我想要容器跑完就消失，這樣不會有殘留的背景程序吃我的記憶體。

## Implementation Decisions

### 目錄結構

以 `CONTEXT.md` 的術語為準。頂層資料夾：`rawdata/<meeting>/`（Raw Material）、`notes/<meeting>/`（Note）、`records/<meeting>.yaml`（Minutes Record）、`output/<meeting>/`（Deliverable）、`templates/`（其下 `schema/`、`markdown/`、`docx/`、`docx-source/`）、`glossary.yaml`（Glossary）。

Meeting 是平的、單層的，一個 Meeting 就是一場實際發生過的會議。不做專案層級的分組，不做跨 Meeting 的系列追蹤。Meeting slug 建議 `YYYY-MM-DD-短描述`，但不強制。

版控只涵蓋 `templates/`、`glossary.yaml`、`.claude/`、`scripts/`、`docs/`、`CONTEXT.md`、`CLAUDE.md`。`rawdata/`、`notes/`、`records/`、`output/` 一律 gitignore——它們是客戶會議內容。

### 唯一的程式進入點

所有機械工作收斂成單一 CLI，以子指令區分：`ingest`、`render`、`check`、`scan-docx`、`apply-docx`、`list`。這是整個專案唯一的程式接縫。

CLI 契約：吃 argv、把結構化結果以 JSON 印到 stdout、錯誤走 exit code、**完全非互動**。所有選單、確認、判斷與模型呼叫都留在 skill（agent）端。這是 ADR-0004 的直接後果，也是刻意的紀律——容器只做確定性的事。

### 七個 skill 與它們的觸發方式

| Skill | 觸發 | 用容器 |
| --- | --- | --- |
| `mm-init` | 手動，一個 repo 一次 | 是（build 映像） |
| `mm-ingest` | 手動；或由 `mm-minutes` 在 Note 缺失／過舊時自動補跑並告知 | 是 |
| `mm-schema` | 手動 | 否 |
| `mm-template` | 手動 | 是 |
| `mm-minutes` | 手動，主要入口 | 是 |
| `mm-list` | 手動；也是 `mm-minutes` 選 Meeting 時的清單來源 | 否 |
| `mm-check` | 手動；`mm-minutes` 在 Render 後自動跑一次 | 是 |

`mm-schema` 與 `mm-list` 不需要容器：前者是純互動地寫 YAML，後者是掃資料夾。

### 容器

`docker compose run --rm`，一次性。映像自建（`python:3.13-slim` + uv），依賴 pin 死：markitdown（extras 為 `pdf,docx,pptx,xlsx,xls,outlook`，**刻意排除音訊**）、docxtpl、python-docx、jinja2、pyyaml。

掛載：`rawdata` 唯讀、`scripts` 唯讀、`glossary.yaml` 唯讀；`notes`、`records`、`output`、`templates` 讀寫；`.git`、`.claude`、`docs` 不進容器。

每個用到容器的 skill 開頭先做 daemon 健康檢查，失敗即停手並明確告知使用者去啟動 Docker Desktop。不自動啟動背景程式，不退回宿主 Python。

### Minutes Schema 的形狀

default schema 是「正式會議記錄型」，包含 meta 區塊（會議名稱、日期時間、地點、主席、記錄人、出席者、缺席者）與主體（議題清單，每則議題含題目、討論摘要、決議與 source；待辦清單，每則含事項、負責人、期限與 source；下次會議）。決議巢狀在議題底下，以保留「哪條決議屬於哪個題目」的關係。

### 模板綁定

Minutes Schema、Markdown Template、Docx Template 三者**不強制綁定**。任何模板都能配任何 schema，渲染時對不到的變數就留空。安全網是 `mm-check` 的靜態掃描，它只報告不阻擋。

Markdown Template 與 Docx Template 都使用 Jinja2 語法，使用者只需要學一套。

### Docx Template 的產生

`scan-docx` 讀 Docx Source，回傳段落與表格儲存格的清單供 agent 判斷哪些是變動欄位。agent 產出建議的變數對照表交給使用者確認修改，再以 `apply-docx` 帶著最終對照表就地替換，輸出到 Docx Template 目錄。原檔不動。

`apply-docx` 必須處理 Word 把單一句子拆成多個 run 的情況——替換前需在段落層級合併 run，否則跨 run 的字串永遠比對不到。

### 重跑語意

`mm-minutes` 在 Minutes Record 已存在時只做 Render，不做 Extract。要重新 Extract 必須明確要求。這讓「人工修改 Minutes Record 再重新產出」成為第一等的工作流程。

## Testing Decisions

### 什麼是好測試

只測外部行為。每一條測試都從單一 CLI 接縫下手：準備一個 fixture 目錄，執行一次子指令，斷言檔案系統的結果與 stdout 的 JSON。不 import 內部模組、不斷言內部函式被呼叫、不斷言中間資料結構。內部怎麼重構都不該讓測試變紅。

測試在容器內執行（`docker compose run --rm` 跑 pytest），直接打 CLI，不經過 docker compose 那一層——那層是 skill 的責任，不是被測對象。

Repo 目前沒有既有測試，這批就是 prior art，後續測試應沿用同一形狀。

### 測什麼

**`ingest`**：各支援格式各一個小 fixture，確認產出 Note；錄音副檔名被跳過且出現在回報中；已存在且較新的 Note 被跳過；單一壞檔不中斷整批且出現在失敗清單；Raw Material 目錄在執行後位元組完全未變。

**`render`**：同一份 Minutes Record 分別套 Markdown Template 與 Docx Template，兩份 Deliverable 內容一致；空欄位呈現為「未提及」；未填變數清單正確；巢狀與清單型欄位正確展開。

**`check`**：空欄位偵測、缺 source 偵測、模板變數對不到 schema 的偵測，各自有正例與反例；確認它回報但不以非零 exit code 阻擋。

**`scan-docx`**：從一份含頁首頁尾、表格與跨 run 句子的 fixture .docx 中，正確列出候選段落與儲存格。

**`apply-docx`**：套用對照表後產出的 Docx Template 能被 docxtpl 成功渲染；原始 Docx Source 未被修改；跨多個 run 的句子被正確替換；頁首頁尾與表格樣式保留。

**`list`**：對各種完成度的 fixture 目錄回報正確的階段狀態。

### 不測什麼

Extract 不進測試——它是 agent 呼叫模型，不是 CLI 的一部分。SKILL.md 是提示詞，不進測試。docker compose 的掛載設定不進自動化測試。

## Out of Scope

- **音訊轉錄。** Raw Material 不收錄音檔，理由與實證見 ADR-0003。
- **PDF 交付檔。** 交付檔是 markdown 與 .docx。ADR-0001 的直接後果。
- **docx2tex、Java、LaTeX。** 見 ADR-0001。
- **跨 Meeting 的待辦匯總表。** Meeting 是平的，也不做上次待辦追蹤。
- **交付前的敏感資訊遮蔽（redact）。** 真要保密不該靠模型遮。
- **中英雙語輸出。**
- **會後通知信或 Slack 草稿。** 超出「會議記錄」的範圍。
- **清理中間產物的 skill。** 直接刪資料夾即可。
- **把這組 skill 打包成可分發的 plugin。** 目前只服務本 repo。
- **Minutes Record 的版本控制。** 它是客戶會議內容，不進 git；手動改壞只能重新 Extract。

## Further Notes

### 已知的取捨與其風險

**模板不綁 schema。** 使用者明確選擇了最寬鬆的方案，代價是交付檔可能長出空格子而沒人發現。唯一的防線是 `mm-check`，因此它的訊息品質很重要——要講清楚是哪一個變數、在哪一份模板、對應不到哪一套 schema。

**Minutes Record 不進版控。** 使用者手動修改的內容沒有歷史，改壞了只能重新 Extract 從頭校對。這是「會議內容不進 git」這條資安決定的必然代價，已知並接受。

**`--reextract` 需要使用者自己記得。** 往 Raw Material 補了新素材後重跑，預設只會重新 Render，不會納入新素材。若實際使用後發現常踩到，可再考慮在偵測到 Note 比 Minutes Record 新時主動詢問。

### 相關 ADR

- ADR-0001：用 docxtpl 產出 Docx Deliverable，不用 docx2tex
- ADR-0002：Minutes Record 是唯一的內容真實來源
- ADR-0003：不收音訊，Raw Material 只收文件
- ADR-0004：所有程式一律在 docker compose 內執行

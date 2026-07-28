# Meeting Minutes

把一場會議留下的雜亂素材（簡報、白板照、既有文件、逐字稿）變成一份可交付的正式會議記錄。

## Language

### 工作單位

**Meeting**:
一場實際發生過的會議，也是本系統的工作單位。每個 Meeting 有一個 slug，所有資料夾都以它為名。
_Avoid_: Project, Session

### 資料

**Raw Material**:
會議留下的原始檔案，未經處理。不含音訊與圖片——錄音需先由外部工具轉成逐字稿才進得來（ADR-0003），白板照的內容需自行補一份文字說明（ADR-0005）。放在 `rawdata/<meeting>/`。
_Avoid_: Input, Source file

**Note**:
Raw Material 轉成的 markdown。是抽取階段唯一讀得到的素材形式。放在 `notes/<meeting>/`。
_Avoid_: Input, Converted file, 逐字稿

**Minutes Record**:
一場 Meeting 的會議記錄內容本身，與呈現方式無關的結構化資料。唯一的內容真實來源，允許人工編修，所有交付檔都由它渲染而來。放在 `records/<meeting>.yaml`。
_Avoid_: Minutes, Output, Result, 中間產物

**Deliverable**:
由 Minutes Record 渲染出來、實際交出去的檔案。可拋棄，隨時可從 Minutes Record 重建。放在 `output/<meeting>/`。
_Avoid_: Result, 成品

**Glossary**:
本專案共用的人名、職稱、產品名、縮寫與常見誤譯對照。抽取時一併送給模型，避免專有名詞被寫錯。
_Avoid_: Dictionary, 詞典

### 模板

三種可維護物，各自獨立：Minutes Schema 決定「記什麼」，Markdown Template 與 Docx Template 決定「長什麼樣」。三者之間不強制綁定。

**Minutes Schema**:
一套會議記錄的欄位定義，決定 Minutes Record 有哪些欄位。可以有多套（例如專案週會一套、客戶驗收會一套）。
_Avoid_: Fields, Model, 格式

**Markdown Template**:
把 Minutes Record 渲染成 markdown Deliverable 的骨架。
_Avoid_: Output template

**Docx Template**:
一份已標上 Jinja2 變數、可直接渲染的 .docx。
_Avoid_: Doc template, Word template

**Docx Source**:
客戶或公司提供的原始 .docx 範例，尚未標上變數。是 Docx Template 的素材，本身不能拿來渲染。
_Avoid_: Doc template rawdata, Raw template

### 動作

**Ingest**:
把 Raw Material 轉成 Note。純機械轉檔，不涉及理解。
_Avoid_: Import, Convert

**Extract**:
讀 Note 產生 Minutes Record。唯一會呼叫模型的步驟。每筆決議與待辦都必須帶 source 指回 Note；抓不到的欄位一律留空，不推測。
_Avoid_: Analyze, Summarize, 生成

**Render**:
把 Minutes Record 套模板變成 Deliverable。不呼叫模型，可重複執行。
_Avoid_: Generate, Build, 輸出

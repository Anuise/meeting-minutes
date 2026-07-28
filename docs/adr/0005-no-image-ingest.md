# 不收圖片，Ingest 遇到圖片就明確拒絕

Ingest 不轉圖片。`.jpg` / `.jpeg` / `.png` / `.gif` / `.bmp` / `.webp` / `.tif` / `.tiff` / `.heic`，以及任何 mimetype 為 `image/*` 的檔案，都會進 `unsupported` 並附一句「照片上的內容需要進會議記錄的話，請自行補一份文字說明放進 `rawdata/`」。

## 為什麼要記下來

spec 的 user story 8 把圖片列進 Ingest 要處理的格式，markitdown 也真的有 `ImageConverter`，所以未來讀者看到我們拒絕圖片，合理會認為是漏做。實際查證後，那個 converter 在本專案的組態下產出的是**空字串**：

- 它的內容只有兩個來源：exiftool 的 metadata，與 `llm_client` 的圖片描述。
- 容器基底是 `python:3.13-slim`，**沒有安裝 exiftool**。
- CLI 依 ADR-0004 是純確定性的，**不接模型**——呼叫模型是 agent 端的事。

也就是說：圖片走完 Ingest 會得到一份 0 byte 的 Note。而空的 Note 比沒有 Note 更糟——它出現在 `notes/<meeting>/` 裡，看起來像處理過了，Extract 卻讀不到任何東西，白板照上的決議就這樣安靜消失。

## Considered Options

**裝 exiftool。** 拿到的是相機型號、解析度、GPS，不是白板上寫的字。對會議記錄沒有用。

**在 Ingest 接視覺模型。** 效果才是使用者真正想要的，但這會讓 Ingest 從「純機械轉檔」變成「會呼叫模型」，違反 CONTEXT.md 對 Ingest 的定義，也違反 ADR-0004 對 CLI 的紀律（容器只做確定性的事）。真要做，該做成 agent 端的一個步驟，並另開一份 ADR 推翻這份。

## Consequences

- 白板照的內容進不了會議記錄，除非使用者自己補一份文字說明放進 `rawdata/`。`mm-ingest` 的回報必須明確講出這件事，不能安靜跳過。
- 判定用「寫死的副檔名清單 + `mimetypes` 補漏」兩層。清單是地板，才不會隨基底映像的 mime 表版本漂移。同一個機制也用在音訊（ADR-0003）。

# 用 docxtpl 產出 Docx Deliverable，不用 docx2tex

原始構想是把 Docx Source 交給 [docx2tex](https://github.com/transpect/docx2tex) 轉成 LaTeX 當模板。實際評估後改用 [docxtpl](https://github.com/elapouya/python-docx-template)：Docx Template 直接就是一份標了 Jinja2 變數的 .docx，渲染後仍是 .docx。

## Considered Options

**docx2tex**。三個問題讓它不划算：

1. **依賴太重。** 需要 Java 1.7–1.15（Java 11 有 file URI bug 必須避開），輸出的 LaTeX 還需要完整 TeX 發行版才能編譯。交付檔是繁體中文，等於再加上 XeLaTeX/LuaLaTeX + ctex/xeCJK + 中文字型，docx2tex 的預設 conf 不處理這塊。
2. **輸出的東西不是模板。** docx2tex 把「一份範例文件」轉成「那份文件的 .tex」，內文是寫死的範例文字，沒有任何填充點。要拿它當模板，仍得自己動手把內文換成變數 —— 那正是我們最後選擇直接對 .docx 做的事，中間繞 LaTeX 這一圈沒有帶來任何東西。
3. **格式退化。** 客戶模板的價值在頁首頁尾、logo、表格樣式；經過 docx → LaTeX → PDF 兩次轉換必然走樣，而這正是「要交付正式文件」的初衷。

**docxtpl** 保留原始 .docx 的全部樣式（因為它從頭到尾就是那份 .docx），且宿主端零額外依賴。

## Consequences

- 交付檔是 `.docx`，**沒有 PDF**。需要 PDF 時另行決定（LibreOffice headless 或 Word 匯出）。
- Docx Source → Docx Template 這一步不再是檔案格式轉換，而是「幫原始 .docx 標上變數」的語意動作，需要人參與確認哪些段落是變動欄位，無法純機械完成。
- 「只支援 docx」從外部工具的限制變成本質限制 —— docxtpl 本來就只吃 docx。

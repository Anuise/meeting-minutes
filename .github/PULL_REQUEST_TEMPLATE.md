# 這個 PR 做什麼

<!-- 一到兩句。用 CONTEXT.md 的詞彙。 -->

## 為什麼

<!-- 解決的問題，或指回 spec / issue。 -->

## 相關文件

- Spec / issue：<!-- .scratch/<feature-slug>/spec.md 或 .scratch/<feature-slug>/issues/NN-<slug>.md，無則寫「無」 -->
- ADR：<!-- 新增或修改的 docs/adr/ 檔名；若牴觸既有 ADR 請明確指出，無則寫「無」 -->

## 怎麼驗證

<!-- 實際跑過的指令與結果。沒跑過的不要列。 -->

```
uv run pytest
```

## 檢查項

- [ ] 每一行改動都能對應到上面的目的，沒有順手改的鄰近程式碼與格式
- [ ] 新行為有測試；修 bug 的話有一個能重現該 bug 的測試
- [ ] `uv run pytest` 全綠
- [ ] 用語符合 `CONTEXT.md`，沒有用到 _Avoid_ 清單裡的同義詞
- [ ] 改到 Minutes Record 結構時，`records/` 既有檔案仍可 Render（ADR-0002）

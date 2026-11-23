# 跨頁表頭與合併營收列核對

先導 4/4 配對，現版、新版、純 Astra 都是 3/4 全對。保留集 8/8 配對，本輪依封存規則達到改善與領先門檻。

| 保留集 | 全對 | 數值與方向全對 | 正例全對 | 負例全對 | 誤暫緩 | 封存誤調 |
|---|---:|---:|---:|---:|---:|---:|
| 現版 Harness（98e9139） | 6/8 | 6/8 | 2/4 | 4/4 | 2 | 0 |
| 新版 Harness | 8/8 | 8/8 | 4/4 | 4/4 | 0 | 0 |
| 純 Astra | 4/8 | 5/8 | 3/4 | 1/4 | 0 | 3 |

Backblaze 的表名與倍率在前一頁，營收資料在下一頁。Okta 的營收美元以百萬計，股數另以千計。新版補齊這兩案的累計營收欄位。14 次離線回歸數值及方向全對，涵蓋 monday.com、JFrog、GitLab、Pure Storage、Sprinklr、Best Buy。工作區測試 200 項通過。

先導的 Salesforce 仍會因同名百分比表缺乏美元倍率而誤拒有效的合併營收表。純 Astra 在 Walmart、Snowflake 填入無法支持的差額和方向。UiPath 只提供可單獨計算的前次金額，差額及方向留待查。Okta 數值正確，引用涵蓋整列。UiPath 和 Okta 依封存規則失分，若事後兩案都計入，純 Astra 為 6/8。

封存前人工查看公告以建立獨立答案，Okta 的表頭也用來核對股數與美元倍率分開處理。八案都在封存後首次執行模型推論。

兩組使用相同的 Astra medium、當時可用的完整公告、每案各一次呼叫、停用搜尋、單工及單次 180 秒。現版和新版重播同一份擷取，沿用 v2 擷取提示、Decimal 算式與原計分容差。24 次正式呼叫全數完成。共享擷取輸入／輸出 382,149／6,026 詞元，累計 209.8 秒。純 Astra 385,851／9,040 詞元，累計 275.6 秒。分析師盲評 0 案，前瞻實績 0 案。

## 產物

- [評測 PDF](report.pdf) · [逐案 QA PDF](qa-records.pdf)
- [逐案評分](case-scores.csv) · [欄位定位](provenance.json) · [執行帳本](execution.csv)
- [正式原始回覆](raw/formal/) · [回歸原始回覆](raw/regression/) · [封存規則](protocol.json) · [公告來源](source-ledger.json)
- [ASML 多立場劇本實測](scenario-draft.pdf) · [結構化輸出](scenario-draft.json)

完整執行包 `output/guidance-table/benchmark-artifacts.zip` 存於本機，包含封存公告與 CLI 紀錄。備妥本機封存結果後，可從 repo 根目錄重建評分表。

```bash
python -m benchmarks.guidance_table_run --phase report
```

ASML 實測以 2024 年 10 月當時可用的既有來源摘要建稿，單次 Astra 產出多方、基準、空方、觀望各一條。工作台驗證了四立場顯示、點擊引文及追問。這份實測的分析師盲評與實際預測結果各 0 案。

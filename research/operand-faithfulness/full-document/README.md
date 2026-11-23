# 完整公告的取值忠實度

同一場財季更新可能同時改變前後兩個隱含營收數字。這項研究分開核對兩個絕對值、差額及原始欄位，並量測逐欄發布能否保留整組核對會擋下的可答結果。

先導與保留集共完成 32/32 次呼叫。保留集上，兩個模型的逐欄核對均保留 5/5 個有證據的可答欄位，整組核對均為 4/5，兩種政策都零誤發布。純 Astra 也完成 5/5。逐欄核對達本批政策比較的描述性增益門檻，低風險及錯取值掩蓋率仍須更多發行人驗證。

| 文件 | 內容 |
|---|---|
| [結果](results.md) · [可支持的結論](interpretation.md) · [一頁論文摘要 PDF](abstract.pdf) | 兩個模型家族的結果、主張及限制 |
| [新穎性表](novelty.md) · [補查](novelty-followup.md) | 最接近的原始論文、可區分的貢獻及反證 |
| [標註規格](annotation.md) · [預註冊](protocol.md) · [機器封存](results/protocol.json) | 任務口徑、模型與預算、停止條件、案例與每次請求雜湊 |
| [逐案原文](evidence.md) · [封存完整文件](results/cases.json) · [來源清單](sources/manifest.json) · [選取紀錄](sources/selection-notes.md) | 兩期完整公告文字、頁列、數值及原文支撐 |
| [逐案回傳與評分](case-scores.md) · [執行帳本](results/execution.json) · [失分 JSON](results/failures.json) · [格式敏感度](serialization-sensitivity.md) | 個別政策輸出、服務失敗、詞元與耗時 |
| [評測程式](study.py) · [版面核對](layout.py) · [離線檢查](test_study.py) | 執行、政策重播、欄位定位與輸出 |

## 重播

從本資料夾以 repo 的 Python 環境執行。無須重新取得 PDF 或連線即可重播已封存的原文與回傳。執行帳本和逐次 JSON 保存模型的結構化回覆。供應商 CLI 的原生輸出和錯誤記錄保存在本機 `results/jobs/`。

```bash
python study.py report
python render.py
```

若要檢查 PDF 版面的生成過程，將 [來源表](sources/urls.tsv) 中案例對應的 14 個 PDF 下載至 `sources/`，核對 `results/cases.json` 的雜湊，再執行 `python -m unittest -v test_study.py`。原始模型批次分 `pilot` 與 `holdout`；它們只派發已封存且未啟動的工作，保留集中止條件由執行程式判斷。

## 可解讀範圍

- 完整文件是發行人發布的 PDF 和 `pdftotext -layout` 頁列，不含圖像通道。兩版文件只依公開日期截斷。
- 四家保留發行人未參與先導或既有專案評測，亦在推論前封存。案例來自歷史公告，模型訓練資料未知。
- 這批有真實拆行表頭、季度與累計並列、相鄰欄百萬與十億，以及僅一側可重建。跨實體頁的欄頭延續只在受控程式測試中有已裁定正解。跨幣別欄、獨立雙人裁定及跨領域外部效度仍待測。
- 歷史比較、真實文件、人工欄位診斷和控制擾動各有分母。兩個受控實驗只對一家公司做資料干預；受控結果不計入真實錯誤率。

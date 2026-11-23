# 可追溯的跨公告數值推理

**研究問題**　最終差額正確時，模型選到的期別、口徑及金額有多常錯誤？當只有一側證據可靠時，能否逐欄保留可驗證的數字？

[先導結果](report.md) · [預註冊](artifacts/preregistration.json) · [完整輸入](artifacts/inputs.json) · [逐次回傳與評分](artifacts/live-rows.json)

**後續研究**　[完整公告評測](full-document/README.md) 封存未見發行人的完整兩期公告，分開比較兩個模型家族、整組與逐欄發布，以及給定人工定位時的結果。

**新發行人評分審計**　[差額誤差抵消](prevalence/README.md) 在兩側均可計算的完整公告上，比較差額給分與有證據的完整答案給分，並量出各類掩蓋錯誤。

**研究待辦**　[同公告對照與投稿待辦](TODO.md) 排定舊版 Harness 重播、累計欄替換、發生率估計與逐欄發布比較。

## 設計

1. **舊回傳診斷。** 從已封存的跨公告算術 v2 逐題評分重建新舊金額與差額的聯合分布。分母為原本可計算的回傳，每三次來自同一發行人；保留原容差，按發行人及重跑次數列出。沒有用答案鍵重寫原回覆。
2. **控制條件。** 將 GitLab 及 Sprinklr 的原文 operands 轉成有來源定位的結構化資料卡。各有四種輸入，原值、兩個累計值同增 1,100 萬美元、只增加最新累計值 600 萬美元、移除最新累計欄。各組加入較早年度的干擾卡。經人工構造的版本用於測量證據依賴。真實公告裡沒有這些改動。表面排版與完整公告檢索另行評測。
3. **對照。** 每份模型回覆同時評三種處理方式，直接採用回覆、證據全齊才發布、逐欄核對及重算。兩種驗證器用同一份證據、同一份候選及相同的運算與範圍檢查。離線故障注入測試資料缺欄、錯年引用、倍數錯誤、兩個 operand 同時錯誤及算錯。故障比例由設計決定。
4. **評分。** 有效覆蓋率是正確且證據鏈可重算的欄位數除以可答欄位數。發布風險是錯誤或無法依引文重算的欄位占已發布欄位的比例。另列純數值的精確比對、模型呼叫完成率與成對擾動反應。新測試使用整數美元等價的 Decimal 精確比對，歷史診斷沿用原先評分標準。

## 執行

從 repo 根目錄用已裝依賴的 Python 執行。只有 `run` 會呼叫模型。`seal` 讀取原有 `output/guidance-arithmetic-v2` 的公開歷史公告封存及評分。依封存後的產物重建 `report` 可直接使用新資料夾中的 JSON、CSV 和回傳。

```bash
python research/operand-faithfulness/pilot.py seal
python research/operand-faithfulness/pilot.py report
python research/operand-faithfulness/pilot.py run
```

新案用同一 Astra，每種條件一次、單工、停用搜尋、每次 90 秒。封存後程式碼、輸入及提示須與雜湊一致。保存實際詞元、耗時及失敗狀態。遇到容量錯誤或限流即停派，開始的呼叫保留在原預算。命令預設輸出至 `artifacts/`，另開批次可用 `--out`。

此輪使用已知發行人及規整的資料卡，適合測出錯誤抵消機制和驗證器的選擇行為。要評估長 PDF 的真實覆蓋率、模型間差異與泛化能力，後續需要獨立發行人、完整公告、由分析師標註的部分可答欄及其他文件領域。

相關工作包括 [FinQA](https://aclanthology.org/2021.emnlp-main.300/) 的終值與執行程式評分，[MultiHiertt](https://aclanthology.org/2022.acl-long.454/) 的多階層表格及證據標註，以及 [Conformal Language Modeling](https://proceedings.iclr.cc/paper_files/paper/2024/hash/31421b112e5f7faf4fc577b74e45dab2-Abstract-Conference.html) 的部分組件驗證與風險校準。本先導使用確定性核對，觀測到的發布風險以試驗樣本描述。

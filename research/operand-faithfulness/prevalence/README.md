# 完整公告差額誤差抵消審計

這批比較只評最終差額與同時核對新舊金額、方向及來源時，同一批模型答案會得到多少不同的分數。使用七家新的可計算發行人，沿用先前跨公告 Q4 任務與兩個模型家族。

完成 14/14 次推論。Astra 與 Claude 各有 7/7 案同時通過精確差額與完整證據評分，排名維持並列。兩家族的精確抵消都是 0/7，各家族 Wilson 95% 區間為 0–35.4%。本批未達在兩家發行人看到錯值掩蓋的擴大門檻。

- [結果與詞元帳本](report.md) · [比較主圖 PDF](scoring-gap.pdf)
- [預註冊](protocol.md) · [來源篩選](sources/screening.md) · [逐案原文定位](evidence.md)
- [逐案回傳與評分](case-results.md) · [評分 CSV](results/scores.csv) · [失敗紀錄](results/failures.json)
- [封存完整輸入](results/requests.json) · [執行帳本](results/execution.json) · [機器摘要](results/summary.json)

已封存資料可離線重播。從本資料夾使用 repo 的 Python 環境評分，再用有 Matplotlib 的 Python 產出報告與圖。

```bash
python audit.py report
python render.py
```

一次性執行入口為 `mkdir -p results/calls && python audit.py run`。評測保留所有已啟動呼叫，重啟只會派發未開跑的工作。原 PDF／HTML 保存於本機 `sources/`，各來源雜湊與全文轉寫已列入封存資料。供應商原生 CLI 傳輸紀錄保存於 `results/jobs/`。每個結構化原始回覆在 `results/calls/` 有單獨檔案。

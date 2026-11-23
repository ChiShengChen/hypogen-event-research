---
name: hypogen-earnings
description: 用 Hypogen 檢視盈利預測、匯入封存共識、修改財務情境、登記可驗證預測與實績，或記錄分析師覆核。適用於既有研究報告。
---

1. 用 `report_find` 定位報告，再用 `earnings_get` 讀取正確版次。用 `report_get` 的 `full` 檢視確認必要的報告期間、證據 ID 和 earnings plan。
2. `consensus_import` 透過 `attachment_add` 匯入使用者提供的 CSV，保存供應者、來源與實際擷取時間。歷史重播使用 `historical_replay`。`earnings_branch` 依使用者指定的假設計算並保存子版。新匯入或新分支使用新的 `request_id`，傳輸重送沿用原 ID。
3. 用 `forecast_register` 登記假說的指標、口徑、期限與引文。實績用 `forecast_resolve`，沿用登記版次與工具回傳的 `forecast_id`。用 `review_record` 儲存人類實際提供的覆核決定、紀錄與耗時；每次新覆核使用新的 `request_id`。
4. 說明本次變動、財務差額與新版本。對歷史回放、已登記待觀測和已收到實績的預測分別標示。

---
name: hypogen-guidance
description: 用 Hypogen 核對營收指引、財季、幣別、倍率和原文位置，計算相對封存現估的差額，或重播跨公告隱含營收案例。
---

1. 查既有現估和單公告時，用 `report_find` 與 `earnings_get` 確認報告版次和季度。`guidance_check` 使用已定位的 `quotes`，或透過 `attachment_add` 註冊使用者指定的完整 HTML，再用 `filing` 傳附件 ID、公告 URL、公開時間與取得時間。每個新檢查用新的 `request_id`；傳輸重送沿用原 ID。
2. 找封存的跨公告案例時，用 `guidance_cases` 依公司或代號查找，再呼叫 `guidance_replay`。預設 `extract`，指定對照時才用 `astra` 或本機已備妥的 `veto`。回覆清楚標記是否為封存重播。
3. 呈現可確認的新舊金額、差額、幣別、倍率、期間及原文鏈接。沿用驗證器的暫緩或 `unknown`，說明缺哪個欄位。將隱含營收變動與相對現估的剩餘差額分開呈現。

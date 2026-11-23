---
name: hypogen-branch
description: 在 Hypogen 假說樹沿上一則假說追問、展開多立場或加入自訂立場。可加入新聞連結、使用者觀點、PDF 或其他研究附件。
---

1. 使用 Hypogen MCP 的 `report_find` 與 `tree_get` 定位報告版本及父節點。若對話已有對應的 ID，直接沿用。多個合理父節點時，列出簡短標題讓使用者指定。
2. 呼叫 `tree_branch`。展開多立場用 `fanout`，沿指定假說追問用 `followup`，自訂立場用 `custom` 並填 `stance`。每個新分支用新的 `request_id`，傳輸重送沿用原 ID。
3. 資料可選填。新聞用 `kind: news` 與公開 HTTPS 網址，個人觀點用 `kind: opinion`。附件用 `capabilities` 回報的本機收件目錄，僅將使用者指定的檔案放入，再用 `attachment_add` 取得 ID。傳 `kind: file`、`attachment_id`，有可驗證可得日期時才填 `available_on`。根據返回的 `usable`、`context`、`excluded` 說明每項資料的用途。
4. 回覆新假說、將變動的財務指標、反證和來源。沿用原研究截止時點。下輪追一條假說時，保存其 `hypothesis_node_ids` 中對應的 ID；`selected_id` 指向本次提問群組。沒有通過證據核對的假說時，回報 `gaps`。

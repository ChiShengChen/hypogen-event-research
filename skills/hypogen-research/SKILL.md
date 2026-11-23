---
name: hypogen-research
description: 用 Hypogen 建立或查找事件研究稿，追問已存報告，產出多立場劇本及未點名供應鏈公司的交易假說。適用於指定公司、事件、點時截點或既有研究問題。
---

1. 使用 Hypogen MCP。查既有報告時先呼叫 `report_find`，再用 `report_get` 取得指定 `report_id` 及 `revision`。遇到多個合理候選，列出公司、事件與截止日供選擇。
2. 建稿前用 `capabilities` 取得實際模型與搜尋模式。`report_create` 需要事件和帶時區的研究截止時間。使用已提供的點時文件，或依需求啟用可用的搜尋模式並填原始來源網域。沿用文件的真實公開與取得時間。歷史日期代理須標為 `replay_day_end`。
3. 回答以儲存的多立場劇本、跨業務因果與 `assessment.trade_opportunities` 為準。列出傳導、財務方向、公開查核點與失效條件；待確認的第三方曝險沿用觀察或證據缺口。保留來源 URL 和引用 ID。
4. 一般追問用 `report_ask`；若使用者要求凍結證據，傳 `evidence_search: off`。若回傳 `child_revision`，下一輪使用新版。指定假說節點、多立場展開或加入假說附件時，使用假說樹工具。

每個新建稿或追問使用新的 `request_id`。傳輸重送沿用原 ID。如工具顯示已送出，先查儲存的報告。

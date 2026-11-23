---
name: hypogen-benchmark
description: 查詢 Hypogen 對純 Astra 的封存 benchmark、重播指引驗證器，或依明確要求啟動或續跑已封存的 V9 四案評測。
---

1. 問進度或結果時用 `benchmark_status` 讀封存摘要或指定 `job_id`。要比較同案原始 Astra 回覆與現有驗證器時，先用 `guidance_cases` 找案例，再用 `benchmark_replay`。重播不發新模型呼叫，樣本維持原先的先導或保留集身份。
2. 使用者明確要求新推論時，先用 `capabilities` 確認有可用的封存方案，再用 `benchmark_start`。目前方案 `v9_equal_recovery` 使用四案、每案最多雙組各兩次、單工、每次 180 秒、停用搜尋。傳 32 位小寫十六進位 UUID 作為 `request_id`，也是回查的 `job_id`。待執行的長任務用 `benchmark_status` 查進度。
3. 中斷後沿用 ID，只有使用者要續跑時傳 `resume: true`。原帳本計入已啟動呼叫。保留失敗、逾時、詞元、耗時和案例數。
4. 呈現首次及復原後配對、逐案品質與工件路徑。程式核對、模型評分、實際收到的人工盲評及前瞻實績各自呈現，維持原封存門檻。

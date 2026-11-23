# 額外診斷 · 金額字串多一層引號

這份敏感度分析在發現格式問題後建立。只去除 JSON 金額多包的一層引號，保留相同標註、取證、金額精度、政策和原始回傳。正式結果保留原格式評分。

| 呼叫 | 套用修正的欄位 | 數值正確增加 | 有證據正確增加 |
|---|---|---:|---:|
| rpd-oracle-claude | prior_q4, latest_q4, change | 3 | 3 |
| yelp-full-claude | prior_q4, latest_q4, change | 3 | 0 |
| zd-oracle-claude | latest_q4 | 1 | 1 |
| rblx-full-claude | prior_q4, latest_q4, change | 3 | 3 |

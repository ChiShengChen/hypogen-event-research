# V9 限流後成對復原逐案 QA

逐次保存所有已啟動呼叫。分析師覆核使用獨立的匿名資料。

## V-01 · UPS 客戶量縮與網路重整

**採用輪次**　復原。

**研究題目**　UPS 宣布計畫削減最大客戶的包裹量，並重新配置美國配送網路。
**截止時間**　2025-01-30T23:59:59+00:00。**研究期間**　2026-03-31。

- **ups-q4:guidance**　UPS 預估 2025 全年合併營收約 890 億美元，營業利益率約 10.8%。 [原始來源](https://investors.ups.com/news-events/press-releases/detail/2135/ups-releases-4q-2024-earnings-and-provides-2025-guidance)
- **ups-q4:network**　UPS 宣布重整美國網路，並計畫透過多年流程重設創造約 10 億美元節省。 [原始來源](https://investors.ups.com/news-events/press-releases/detail/2135/ups-releases-4q-2024-earnings-and-provides-2025-guidance)
- **ups-q4:volume**　UPS 與最大客戶原則上達成協議，計畫至 2026 年下半年將該客戶包裹量減少逾 50%。2025 年 1 月 1 日起 UPS 將 SurePost 全數改為自行配送。 [原始來源](https://investors.ups.com/news-events/press-releases/detail/2135/ups-releases-4q-2024-earnings-and-provides-2025-guidance)
  - 原文短節錄：lower its volume by more than 50% by the second half of 2026

### 首次 · 純 Astra

**狀態**　失敗。

**執行原因**　限流／用量上限。

[逐次回傳](raw/first/calls/V-01-astra.json) · [CLI 事件](raw/first/jobs/V-01-astra/events.jsonl) · [CLI 診斷](raw/first/jobs/V-01-astra/stderr.log)

### 首次 · V9 Harness

**狀態**　排隊未開始。

### 復原 · 純 Astra

**狀態**　完成。

[逐次回傳](raw/recovery/calls/V-01-astra.json) · [CLI 事件](raw/recovery/jobs/V-01-astra/events.jsonl) · [模型原始 JSON](raw/recovery/jobs/V-01-astra/answer.json) · [CLI 診斷](raw/recovery/jobs/V-01-astra/stderr.log)

**假說 1**

- **公司**　UPS
- **傳導**　若最大客戶的包裹量在 2025 年開始下降，其他客戶新增的包裹收入與價格調整可能不足以補回缺口，使全年合併營收低於公司指引。
- **催化劑**　觀察 UPS 在分季財報中揭露的最大客戶減量進度。減量逾 50% 的計畫目標落在 2026 年下半年，研究期內可檢驗的是初期減量對 2025 年營收的影響。
- **可查核預測**　截至 2026 年 3 月 31 日，預期 UPS 公布的 2025 年合併營收低於指引中心值 890 億美元，且公司將最大客戶減量列為營收承壓的原因之一。
- **失效條件**　若全年合併營收達到或超過 890 億美元，營收預測即失效。若營收低於該水準，但公司披露最大客戶的包裹量並未下降，則減量機制失效。
- **影響規模**　以 890 億美元為基準，營收每低於指引中心值 1%，即相差約 8.9 億美元，可據此衡量初期減量對營收預估的重要性。
- **證據**　ups-q4:volume、ups-q4:guidance

**假說 2**

- **公司**　UPS
- **傳導**　SurePost 改由 UPS 自行配送後，若新增包裹能併入既有路線，便可分攤末端配送成本。若美國網路重整也能隨最大客戶減量同步縮減閒置運能，兩者可支撐合併營業利益率。
- **催化劑**　SurePost 自 2025 年 1 月 1 日起全面改為自行配送。2025 年各季財報可用來追蹤路線整併與成本節省進度，約 10 億美元的節省目標涵蓋多年。
- **可查核預測**　截至 2026 年 3 月 31 日，預期 UPS 公布的 2025 年合併營業利益率按指引口徑達到或超過 10.8%，且公司披露美國網路調整已在年內帶來成本節省。
- **失效條件**　若 2025 年合併營業利益率按指引口徑低於 10.8%，則利益率預測失效。若達標但公司披露網路調整的節省均在 2025 年後才實現，則當年節省支撐利益率的解釋失效。
- **影響規模**　按全年營收指引 890 億美元估算，合併營業利益率每變動 0.1 個百分點，全年營業利益約相差 8,900 萬美元。
- **證據**　ups-q4:volume、ups-q4:network、ups-q4:guidance

### 復原 · V9 Harness

**狀態**　完成。

[逐次回傳](raw/recovery/calls/V-01-v9.json) · [CLI 事件](raw/recovery/jobs/V-01-v9/events.jsonl) · [模型原始 JSON](raw/recovery/jobs/V-01-v9/answer.json) · [CLI 診斷](raw/recovery/jobs/V-01-v9/stderr.log)

**假說 1**

- **公司**　UPS
- **傳導**　若 UPS 配合最大客戶減量整併美國分揀班次與配送路線，相較維持原網路，可減少閒置工時與運能成本，支撐營業利益率。約 10 億美元是多年節省目標，2025 年可實現多少節省仍未知。
- **催化劑**　UPS 於 2025 年 1 月 30 日宣布重整美國網路。營運催化因素是其後實際調整班次與路線，全年指引提供比較基準。
- **可查核預測**　截至 2026 年 3 月 31 日，查核 UPS 第四季暨全年業績公告，預期 2025 全年合併營業利益率按指引同口徑達 10.8% 或以上。此為獲利代理指標，無法單獨辨識美國網路節省的貢獻。
- **失效條件**　同一查核期限內，若 UPS 公布的 2025 全年同口徑合併營業利益率低於 10.8%，則獲利預測失效。若未揭露同口徑數字，結果待驗。
- **影響規模**　—
- **證據**　ups-q4:network、ups-q4:volume、ups-q4:guidance

**假說 2**

- **公司**　UPS
- **傳導**　若最大客戶在 2025 年縮量快於指引所隱含的進度，相較維持原配送量，UPS 可計費的配送件數會更少。若其他業務新增營收不足以填補缺口，全年營收可能低於指引。客戶減量時程與每件收入均未揭露，無法估算缺口。
- **催化劑**　2025 年 1 月 30 日披露的原則協議以 2026 年下半年為減量目標期。研究期內的催化因素是客戶若提前減少實際交運件數，協議本身尚未造成可核實的營收流失。
- **可查核預測**　截至 2026 年 3 月 31 日，查核 UPS 第四季暨全年業績公告，預期 2025 全年合併營收低於指引中心值 890 億美元。此為總營收代理指標，無法據以歸因於單一客戶。
- **失效條件**　同一查核期限內，若 UPS 公布的 2025 全年合併營收達 890 億美元或以上，則營收預測失效。若尚未公布，結果待驗。
- **影響規模**　—
- **證據**　ups-q4:volume、ups-q4:guidance

## V-02 · Disney 串流與分部指引

**採用輪次**　首次。

**研究題目**　Disney 公布 2024 財年第四季財報，並發布下一財年串流和體驗部門指引。
**截止時間**　2024-11-14T23:59:59+00:00。**研究期間**　2025-12-31。

- **dis-fy24:experiences**　FY2024 Q4 Experiences 營業利益 17 億美元，年減 6%。公司預計 FY2025 該部門營業利益年增 6% 至 8%，成長偏向下半財年。 [原始來源](https://investors.thewaltdisneycompany.com/news/news-details/2024/The-Walt-Disney-Company-Reports-Fourth-Quarter-and-Full-Year-Earnings-for-Fiscal-2024-11-14-2024/)
- **dis-fy24:fy25**　管理層預期 FY2025 Entertainment DTC 營業利益年增約 8.75 億美元。比較基期包含印度 DTC 約 2 億美元負面影響。管理層同時預期 FY2025 Q1 Disney+ Core 訂戶季減。 [原始來源](https://investors.thewaltdisneycompany.com/news/news-details/2024/The-Walt-Disney-Company-Reports-Fourth-Quarter-and-Full-Year-Earnings-for-Fiscal-2024-11-14-2024/)
  - 原文短節錄：Entertainment DTC operating income increase of approximately $875 million versus fiscal 2024
- **dis-fy24:streaming**　Disney FY2024 Q4 Entertainment DTC 廣告收入年增 14%，營業利益 2.53 億美元。合併 DTC 串流業務營業利益 3.21 億美元，兩者口徑不同。Disney+ Core 季末付費訂戶逾 1.2 億，較上一季增加 440 萬。 [原始來源](https://investors.thewaltdisneycompany.com/news/news-details/2024/The-Walt-Disney-Company-Reports-Fourth-Quarter-and-Full-Year-Earnings-for-Fiscal-2024-11-14-2024/)

### 首次 · 純 Astra

**狀態**　完成。

[逐次回傳](raw/first/calls/V-02-astra.json) · [CLI 事件](raw/first/jobs/V-02-astra/events.jsonl) · [模型原始 JSON](raw/first/jobs/V-02-astra/answer.json) · [CLI 診斷](raw/first/jobs/V-02-astra/stderr.log)

**假說 1**

- **公司**　Disney
- **傳導**　若娛樂部門直營串流業務（Entertainment DTC）的廣告收入持續成長，即使 Disney+ Core 訂戶短期回落，串流營業利益仍可能增加。2024 財年第四季該業務廣告收入年增 14%，營業利益為 2.53 億美元。
- **催化劑**　2025 財年第一季財報可檢驗 Disney+ Core 訂戶是否如管理層預期季減，並觀察同期廣告收入與營業利益。全年財報可檢驗獲利改善幅度。
- **可查核預測**　預期 2025 財年第一季 Disney+ Core 付費訂戶季減，但 Entertainment DTC 廣告收入仍年增。預期該業務全年營業利益較 2024 財年增加約 8.75 億美元。
- **失效條件**　若第一季訂戶季減且廣告收入也年減，則廣告支撐獲利的機制欠缺當季佐證。若全年 Entertainment DTC 營業利益年增額明顯低於 8.75 億美元，則全年預測失準。
- **影響規模**　8.75 億美元是娛樂部門直營串流業務對年度營業利益的預期增量。比較基期含印度 DTC 約 2 億美元的負面影響，評估廣告對獲利改善的貢獻時，須考量這項基期因素。
- **證據**　dis-fy24:streaming、dis-fy24:fy25

**假說 2**

- **公司**　Disney
- **傳導**　體驗部門營業利益在 2024 財年第四季仍年減 6%，降至 17 億美元。這使該季成為次年第四季較低的比較基期，有利於 2025 財年下半年的營業利益年增額回升。
- **催化劑**　2025 財年第二季財報可用來計算上半年營業利益年增額。全年財報公布後，即可推算下半年年增額，檢驗成長是否集中於下半年。
- **可查核預測**　預期體驗部門 2025 財年營業利益較 2024 財年成長 6% 至 8%，且下半年相較上年同期增加的營業利益金額將高於上半年。
- **失效條件**　若全年營業利益年增率落在 6% 至 8% 之外，則成長幅度預測失準。即使全年達標，若下半年年增額低於或等於上半年，則成長偏向下半年的判斷失準。
- **影響規模**　若假說成立，僅依上半年營業利益年增額推算全年，會低估體驗部門對 Disney 全年營業利益成長的貢獻。
- **證據**　dis-fy24:experiences

### 首次 · V9 Harness

**狀態**　完成。

[逐次回傳](raw/first/calls/V-02-v9.json) · [CLI 事件](raw/first/jobs/V-02-v9/events.jsonl) · [模型原始 JSON](raw/first/jobs/V-02-v9/answer.json) · [CLI 診斷](raw/first/jobs/V-02-v9/stderr.log)

**假說 1**

- **公司**　Disney
- **傳導**　FY2024 Q4 Entertainment DTC 廣告收入年增 14%。若這股成長延續，且新增廣告收入高於相關增量成本，相較廣告收入持平的情境，Disney 可在訂戶成長放緩時仍提高串流營業利益。管理層預期 FY2025 營業利益年增約 8.75 億美元，但廣告對增額的貢獻尚未量化。
- **催化劑**　2024-11-14 財報同時揭露廣告成長實績與 FY2025 Q1 Disney+ Core 訂戶季減預期。先看 Disney 的 Q1 財報是否顯示廣告收入續增，再以全年財報核對獲利。
- **可查核預測**　截至 2025-12-31，預期 Disney 的 FY2025 Q1 財報顯示 Entertainment DTC 廣告收入較上年同期增加，且全年財報顯示 FY2025 Entertainment DTC 營業利益高於 FY2024。後者是獲利結果，廣告貢獻仍須另行歸因。
- **失效條件**　同一截止日前，若 Disney 揭露 FY2025 Q1 Entertainment DTC 廣告收入較上年同期持平或下降，廣告續增假設即失效。若廣告續增，但 FY2025 全年同口徑營業利益較 FY2024 持平或下降，則獲利預測失效。未揭露廣告增幅時，該環節仍待驗證。
- **影響規模**　—
- **證據**　dis-fy24:streaming、dis-fy24:fy25

**假說 2**

- **公司**　Disney
- **傳導**　FY2024 Q4 Experiences 營業利益年減 6%，而 FY2025 指引將主要成長寄望於下半財年。若獲利回升較指引假設晚一季，部分改善可能遞延至 FY2026，使 FY2025 部門營業利益增幅低於指引下緣。延遲屬情境假設，財報未量化單季遞延的金額。
- **催化劑**　2024-11-14 發布的 Experiences 指引預期 FY2025 營業利益年增 6% 至 8%，成長偏向下半年。FY2025 Q3 是下半財年首季，可先從 Disney 季報觀察回升時點。
- **可查核預測**　截至 2025-12-31，預期 Disney 財報顯示 FY2025 Q3 Experiences 營業利益較上年同期持平或下降，且 FY2025 全年部門營業利益較 FY2024 增幅低於 6%。
- **失效條件**　同一截止日前，若 Disney 揭露 FY2025 Q3 Experiences 營業利益高於上年同期，則推翻該季尚未恢復年增的預測。若 FY2025 全年同部門營業利益較 FY2024 年增至少 6%，則推翻全年低於指引下緣的預測。
- **影響規模**　—
- **證據**　dis-fy24:experiences

### 復原 · 純 Astra

**狀態**　未排入。

### 復原 · V9 Harness

**狀態**　未排入。

## V-03 · Novo Nordisk 製造據點交易

**採用輪次**　復原。

**研究題目**　Novo Nordisk 宣布簽約收購三座藥品充填及成品製造廠。
**截止時間**　2024-02-05T23:59:59+00:00。**研究期間**　2025-06-30。

- **novo-sites:acquisition**　Novo Nordisk 同意以約 110 億美元預付款向 Novo Holdings 購買三座充填及成品製造廠。該購買與 Novo Holdings 收購 Catalent 的交易相關。 [原始來源](https://www.novonordisk.com/content/nncorp/global/en/news-and-media/news-and-ir-materials/news-details.html?id=167017&stream=top)
- **novo-sites:capacity**　三座廠當時已與 Novo Nordisk 合作。管理層預期自 2026 年起逐步增加充填產能。 [原始來源](https://www.novonordisk.com/content/nncorp/global/en/news-and-media/news-and-ir-materials/news-details.html?id=167017&stream=top)
  - 原文短節錄：The acquisition is expected to gradually increase Novo Nordisk’s filling capacity from 2026 and onwards.

### 首次 · 純 Astra

**狀態**　完成。

[逐次回傳](raw/first/calls/V-03-astra.json) · [CLI 事件](raw/first/jobs/V-03-astra/events.jsonl) · [模型原始 JSON](raw/first/jobs/V-03-astra/answer.json) · [CLI 診斷](raw/first/jobs/V-03-astra/stderr.log)

**假說 1**

- **公司**　Novo Nordisk
- **傳導**　三座廠在簽約前已為 Novo Nordisk 提供服務。即使廠房易主，原已供應公司的充填量仍屬既有產能。管理層預期自 2026 年起才逐步增加充填產能。
- **催化劑**　截至 2025 年 6 月 30 日，公司發布的供應展望或產能更新，可用來檢驗新增產能的時程是否提前。
- **可查核預測**　預期截至 2025 年 6 月 30 日，公司仍將三廠新增充填產能的起點列在 2026 年或之後，期間內出貨成長主要仍須依靠其他來源或既有產能的利用率提升。
- **失效條件**　若公司在研究期內宣布三廠新增充填產能提前至 2025 年投入，或明確將當期出貨增量歸因於收購帶來的額外產能，即推翻此假說。
- **影響規模**　估算至 2025 年上半年的營收時，若把三廠原已供應公司的充填量再次列為收購增量，將高估可出貨量及營收。
- **證據**　novo-sites:capacity

**假說 2**

- **公司**　Novo Nordisk
- **傳導**　約 110 億美元的預付款使交易進度直接影響資金需求。由於購廠案與 Novo Holdings 收購 Catalent 的交易相關，付款時點是評估 Novo Nordisk 期末淨負債的重要變數。
- **催化劑**　截至 2025 年 6 月 30 日，觀察兩案的交割公告，以及 Novo Nordisk 財報中購廠對價的實際支付金額與時點。
- **可查核預測**　若兩案在研究期內完成交割，預期 Novo Nordisk 屆時已支付接近 110 億美元的購廠款。在其他現金流相同下，期末淨負債將較未交割情境增加約當金額。
- **失效條件**　若交割時揭露大部分對價遞延支付，或 Novo Nordisk 在 Novo Holdings 完成收購 Catalent 前即已支付大部分購廠款，則以兩案交割估計現金流出時點的假說失效。若期內尚未交割，此項條件式預測仍待驗證。
- **影響規模**　將約 110 億美元支出列入正確期間，會直接影響期末淨現金或淨負債估算，以及由企業價值推算的股權價值。
- **證據**　novo-sites:acquisition

### 首次 · V9 Harness

**狀態**　失敗。

**執行原因**　限流／用量上限。

[逐次回傳](raw/first/calls/V-03-v9.json) · [CLI 事件](raw/first/jobs/V-03-v9/events.jsonl) · [CLI 診斷](raw/first/jobs/V-03-v9/stderr.log)

### 復原 · 純 Astra

**狀態**　完成。

[逐次回傳](raw/recovery/calls/V-03-astra.json) · [CLI 事件](raw/recovery/jobs/V-03-astra/events.jsonl) · [模型原始 JSON](raw/recovery/jobs/V-03-astra/answer.json) · [CLI 診斷](raw/recovery/jobs/V-03-astra/stderr.log)

**假說 1**

- **公司**　Novo Nordisk
- **傳導**　三座廠在簽約前已替公司生產。收購可改變產能調度權，但管理層預期自 2026 年起才逐步增加充填產能。
- **催化劑**　截至 2025 年 6 月 30 日，公司在業績公告或產能更新中說明三座廠的新增產能何時可用。
- **可查核預測**　預期截至研究期末，公司仍將三座廠因收購而增加的充填產能列為未來供給，期間營收成長主要來自其他因素。
- **失效條件**　公司在研究期內明確揭露，三座廠因收購而新增的充填產能已投產，並對當期出貨或營收成長有重大貢獻。
- **影響規模**　估算截至 2025 年上半年的營收時，若將三座廠原已承作的產量列為收購增量，會重複計算可銷售數量。
- **證據**　novo-sites:capacity

**假說 2**

- **公司**　Novo Nordisk
- **傳導**　約 110 億美元的預付款使現金需求集中於付款時點。購廠安排與 Novo Holdings 收購 Catalent 的交易相連，相關交易進度因而影響資金需求落在哪個報告期。
- **催化劑**　截至 2025 年 6 月 30 日，關聯交易的交割進度，以及 Novo Nordisk 對購廠付款時點與金額的披露。
- **可查核預測**　若購廠交易在研究期內依公告條件交割，預期 Novo Nordisk 將在交割時支付約 110 億美元，形成大額投資現金流出，時間早於管理層預期的新增產能。
- **失效條件**　若公司披露已在期內交割，但實際付款大幅低於約定預付款，或主要價款改為跨年度分期支付，則資金需求集中於交割時點的假說失效。若期末仍未交割，則期內無法驗證。
- **影響規模**　交割時點會顯著影響上半年收購支出與期末資金部位。既有現金與新增融資各承擔多少，仍須以公司披露判定。
- **證據**　novo-sites:acquisition、novo-sites:capacity

### 復原 · V9 Harness

**狀態**　完成。

[逐次回傳](raw/recovery/calls/V-03-v9.json) · [CLI 事件](raw/recovery/jobs/V-03-v9/events.jsonl) · [模型原始 JSON](raw/recovery/jobs/V-03-v9/answer.json) · [CLI 診斷](raw/recovery/jobs/V-03-v9/stderr.log)

**假說 1**

- **公司**　Novo Nordisk
- **傳導**　三廠原已與 Novo Nordisk 合作。若收購交割，Novo Nordisk 可直接規劃廠區投資與擴產時程，較維持委外合作多一層控制權。期內可驗證的是取得控制權。管理層預期自 2026 年起逐步增產，每年可增加多少充填量及獲利仍待量化。
- **催化劑**　2024-02-05 簽約後，觀察 Novo Nordisk 就三廠交割發布的投資人公告。
- **可查核預測**　以簽約日三廠仍為合作廠為基準，至 2025-06-30，Novo Nordisk 公告已完成三廠收購並取得控制權。
- **失效條件**　Novo Nordisk 在 2025-06-30 前公告交易終止，或確認截至該日仍有廠區未完成交割。若屆時只有簽約公告，結果待定。
- **影響規模**　—
- **證據**　novo-sites:acquisition、novo-sites:capacity

**假說 2**

- **公司**　Novo Nordisk
- **傳導**　即使順利交割，約 110 億美元預付款也可能早於新增產能。相較維持原合作安排，若 Novo Nordisk 期內支付購置款，將先動用資金，縮小可供其他投資運用的金額。購置付款屬現金流出，利息及損益影響取決於融資方式。
- **催化劑**　簽約後的價款結算。觀察 Novo Nordisk 交割公告及截至 2025-06-30 已發布的年報或季報收購附註。
- **可查核預測**　以未收購時三廠購置付款為零作情境基準，自簽約至 2025-06-30，Novo Nordisk 公開確認已就本案支付購置款，早於管理層預期自 2026 年起逐步增產的時點。
- **失效條件**　Novo Nordisk 於同一期內公告取消交易且未支付購置款，或確認全部購置款延至 2025-06-30 後支付。僅揭露約定對價或未單列付款，均無法判定實付結果。
- **影響規模**　—
- **證據**　novo-sites:acquisition、novo-sites:capacity

## V-04 · Ford 電動車投資重整

**採用輪次**　首次。

**研究題目**　Ford 宣布取消原計畫的純電三排座 SUV，並重排電動車投資。
**截止時間**　2024-08-21T23:59:59+00:00。**研究期間**　2025-10-31。

- **ford-ev-8k:charges**　Ford 估計 2024 Q3 將就原計畫純電三排座 SUV 的製造及供應商模具資產認列約 4 億美元減記。另可能產生最多約 15 億美元額外費用及現金支出。 [原始來源](https://www.sec.gov/Archives/edgar/data/37996/000003799624000150/f-20240819.htm)
- **ford-ev-strategy:plans**　Ford 計畫在 2026 年於俄亥俄州開始生產新款純電商用廂型車，隨後於 2027 年推出兩款電動皮卡。公司計畫把純電車相關資本支出占年度資本支出的比例從約 40% 下調至約 30%。 [原始來源](https://www.sec.gov/Archives/edgar/data/37996/000003799624000150/exhibit99toaugust2120248.htm)
  - 原文短節錄：an all-new commercial van that will begin production in 2026 in Ohio

### 首次 · 純 Astra

**狀態**　完成。

[逐次回傳](raw/first/calls/V-04-astra.json) · [CLI 事件](raw/first/jobs/V-04-astra/events.jsonl) · [模型原始 JSON](raw/first/jobs/V-04-astra/answer.json) · [CLI 診斷](raw/first/jobs/V-04-astra/stderr.log)

**假說 1**

- **公司**　Ford
- **傳導**　取消純電三排座 SUV 將降低專用製造設備與供應商模具的價值。資產減記會壓低認列當季的稅前盈餘，減記本身不涉及當期現金支付。
- **催化劑**　Ford 公布 2024 年第三季財報，揭露該專案的實際減記金額。
- **可查核預測**　預期 Ford 將在 2024 年第三季就該專案認列約 4 億美元資產減記，使當季稅前盈餘相應減少。
- **失效條件**　若第三季財報顯示 Ford 將減記延至後續季度，或實際金額明顯偏離 4 億美元，則該預測失效。
- **影響規模**　約 4 億美元是評估第三季盈餘影響的基準。Ford 另估計可能產生最多約 15 億美元的額外費用及現金支出，實際金額與支付時點仍待確認。
- **證據**　ford-ev-8k:charges

**假說 2**

- **公司**　Ford
- **傳導**　取消三排座純電 SUV 後，Ford 將後續純電商用廂型車與皮卡的投產或上市時程排在 2026 至 2027 年，因而有空間降低近期年度資本預算中分配給純電車的比重。
- **催化劑**　截至 2025 年 10 月 31 日，Ford 對 2025 年度資本支出配置的更新可用於檢驗投資重排進度。
- **可查核預測**　預期截至研究期末，Ford 對 2025 年度純電車資本支出占比的最新預估將低於原先約 40%，並更接近約 30% 的規劃水準。
- **失效條件**　若期內可比口徑的 2025 年度預估仍接近或高於 40%，或 Ford 撤回調降計畫，則假說失效。若僅披露總資本支出，則無法判定。
- **影響規模**　若年度總資本支出相同，占比從 40% 降至 30% 意味著每 100 美元資本支出中，純電車投入約少 10 美元。純電車投入的實際美元變化仍取決於總預算規模。
- **證據**　ford-ev-strategy:plans

### 首次 · V9 Harness

**狀態**　完成。

[逐次回傳](raw/first/calls/V-04-v9.json) · [CLI 事件](raw/first/jobs/V-04-v9/events.jsonl) · [模型原始 JSON](raw/first/jobs/V-04-v9/answer.json) · [CLI 診斷](raw/first/jobs/V-04-v9/stderr.log)

**假說 1**

- **公司**　Ford
- **傳導**　若原案續行，三排座純電 SUV 仍需後續製造與模具投資。取消原案可讓 Ford 將資金轉作其他用途。此情境假設純電車投資比重實際下降；現金節省額仍取決於總資本支出及替代專案用款。
- **催化劑**　2024-08-21 公告重排投資後，於 2024 年度結束至 2025-10-31 間，查 Ford 年報或投資人簡報是否更新純電車資本支出占比。
- **可查核預測**　若調整已於 2024 年度開始落實，Ford 同口徑全年實際純電車資本支出占比應低於公告所述約 40% 的原配置水準，朝約 30% 的計畫靠攏。該占比是投資重排的代理指標，無法歸因單一車款。
- **失效條件**　若 Ford 截至 2025-10-31 披露的 2024 全年同口徑實際占比仍約為 40% 或更高，則推翻當年已降低比重的假設。僅重申目標或未披露實績，結果仍待驗證。
- **影響規模**　—
- **證據**　ford-ev-strategy:plans

**假說 2**

- **公司**　Ford
- **傳導**　取消原案使原定投入生產的製造與供應商模具資產失去預期用途。相較續行原案，若 Ford 因取消而減記，將直接壓低當季稅前獲利。公司估計減記約 4 億美元，實際現金支出另待核實。
- **催化劑**　Ford 預估於 2024 年第三季認列減記，首個核對時點為該季結束後公布的 Ford 季報及財報說明。
- **可查核預測**　截至 2025-10-31，Ford 財報應可核對 2024 年第三季就該 SUV 製造與供應商模具資產認列正額減記，並以公告估計的約 4 億美元衡量實際獲利衝擊。
- **失效條件**　若 Ford 截至 2025-10-31 明確披露該批資產在 2024 年第三季的減記為零，即推翻當季獲利受此項目拖累的假設。財報未單列金額仍無法判定。
- **影響規模**　—
- **證據**　ford-ev-8k:charges

### 復原 · 純 Astra

**狀態**　未排入。

### 復原 · V9 Harness

**狀態**　未排入。

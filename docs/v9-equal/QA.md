# V9 等預算逐案問答

此紀錄供結果查核。匿名人評應使用獨立的匿名 PDF 和空白表。下列為生成時點可見的封存摘要，並附原文摘錄與可開啟的原始公告。

## V-01 · UPS 客戶量縮與網路重整

**分組**　pilot

**研究題目**　UPS 宣布計畫削減最大客戶的包裹量，並重新配置美國配送網路。
**截止時間**　2025-01-30T23:59:59+00:00。**研究期間**　2026-03-31。

- **ups-q4:guidance**　UPS 預估 2025 全年合併營收約 890 億美元，營業利益率約 10.8%。 [原始來源](https://investors.ups.com/news-events/press-releases/detail/2135/ups-releases-4q-2024-earnings-and-provides-2025-guidance)
- **ups-q4:network**　UPS 宣布重整美國網路，並計畫透過多年流程重設創造約 10 億美元節省。 [原始來源](https://investors.ups.com/news-events/press-releases/detail/2135/ups-releases-4q-2024-earnings-and-provides-2025-guidance)
- **ups-q4:volume**　UPS 與最大客戶原則上達成協議，計畫至 2026 年下半年將該客戶包裹量減少逾 50%。2025 年 1 月 1 日起 UPS 將 SurePost 全數改為自行配送。 [原始來源](https://investors.ups.com/news-events/press-releases/detail/2135/ups-releases-4q-2024-earnings-and-provides-2025-guidance)
  - 原文短節錄：lower its volume by more than 50% by the second half of 2026

### 純 Astra

**執行狀態**　逾時。

[正式回傳](raw/calls/V-01-astra.json) · [CLI 事件](raw/jobs/V-01-astra/events.jsonl) · [CLI 診斷](raw/jobs/V-01-astra/stderr.log)

### V9 Harness

**執行狀態**　完成。

[正式回傳](raw/calls/V-01-v9.json) · [CLI 事件](raw/jobs/V-01-v9/events.jsonl) · [模型原始 JSON](raw/jobs/V-01-v9/answer.json) · [CLI 診斷](raw/jobs/V-01-v9/stderr.log)

**假說 1**

- **公司**　UPS
- **傳導**　若 UPS 隨最大客戶減量同步整併美國配送路線，相較於減量後仍維持原網路，可減少低載運量班次的營運支出。若當年節省足以抵銷轉型成本，便可支撐合併營業利益率。約 10 億美元是多年節省目標，2025 年可實現的淨額未知。
- **催化劑**　UPS 於 2025 年 1 月 30 日宣布重整美國網路。觀察其後季度業績公告是否披露已完成的整併或已實現的節省，再以全年業績檢驗獲利結果。
- **可查核預測**　截至 2026-03-31，UPS 全年業績公告顯示，2025 年合併營業利益率按指引相同口徑達 10.8% 或以上。以指引中心值作為情境門檻；該指標是獲利代理，無法單獨歸因於美國網路重整。
- **失效條件**　截至 2026-03-31，UPS 公布的 2025 年同口徑合併營業利益率低於 10.8%，即推翻此獲利預測。個別路線仍可能已產生節省。
- **影響規模**　—
- **證據**　ups-q4:network、ups-q4:volume、ups-q4:guidance

**假說 2**

- **公司**　UPS
- **傳導**　若最大客戶於 2025 年實際交運的包裹較維持原安排時減少，UPS 可完成配送並認列收入的件數也會減少。若減量快於編製指引時的假設，且其他客戶新增收入不足以填補缺口，全年合併營收可能低於指引中心值。客戶減量時程、每件收入及指引內含的減量幅度均未披露。
- **催化劑**　2025 年 1 月 30 日公布的是原則協議。觀察 UPS 隨後在 2025 年季度業績中是否確認實際減量，以及是否因此調降全年營收展望。逾 50% 的減量目標落在研究期後的 2026 年下半年。
- **可查核預測**　截至 2026-03-31，UPS 全年業績公告顯示，2025 年合併營收低於原指引中心值 890 億美元。合併營收是代理指標，須有 UPS 對減量影響的說明，才能將落差連結至該客戶。
- **失效條件**　截至 2026-03-31，UPS 公布的 2025 年合併營收達 890 億美元或以上，即推翻此營收預測。其他業務可能已抵銷客戶減量。
- **影響規模**　—
- **證據**　ups-q4:volume、ups-q4:guidance

## V-02 · Disney 串流與分部指引

**分組**　pilot

**研究題目**　Disney 公布 2024 財年第四季財報，並發布下一財年串流和體驗部門指引。
**截止時間**　2024-11-14T23:59:59+00:00。**研究期間**　2025-12-31。

- **dis-fy24:experiences**　FY2024 Q4 Experiences 營業利益 17 億美元，年減 6%。公司預計 FY2025 該部門營業利益年增 6% 至 8%，成長偏向下半財年。 [原始來源](https://investors.thewaltdisneycompany.com/news/news-details/2024/The-Walt-Disney-Company-Reports-Fourth-Quarter-and-Full-Year-Earnings-for-Fiscal-2024-11-14-2024/)
- **dis-fy24:fy25**　管理層預期 FY2025 Entertainment DTC 營業利益年增約 8.75 億美元。比較基期包含印度 DTC 約 2 億美元負面影響。管理層同時預期 FY2025 Q1 Disney+ Core 訂戶季減。 [原始來源](https://investors.thewaltdisneycompany.com/news/news-details/2024/The-Walt-Disney-Company-Reports-Fourth-Quarter-and-Full-Year-Earnings-for-Fiscal-2024-11-14-2024/)
  - 原文短節錄：Entertainment DTC operating income increase of approximately $875 million versus fiscal 2024
- **dis-fy24:streaming**　Disney FY2024 Q4 Entertainment DTC 廣告收入年增 14%，營業利益 2.53 億美元。合併 DTC 串流業務營業利益 3.21 億美元，兩者口徑不同。Disney+ Core 季末付費訂戶逾 1.2 億，較上一季增加 440 萬。 [原始來源](https://investors.thewaltdisneycompany.com/news/news-details/2024/The-Walt-Disney-Company-Reports-Fourth-Quarter-and-Full-Year-Earnings-for-Fiscal-2024-11-14-2024/)

### 純 Astra

**執行狀態**　完成。

[正式回傳](raw/calls/V-02-astra.json) · [CLI 事件](raw/jobs/V-02-astra/events.jsonl) · [模型原始 JSON](raw/jobs/V-02-astra/answer.json) · [CLI 診斷](raw/jobs/V-02-astra/stderr.log)

**假說 1**

- **公司**　Disney
- **傳導**　FY2024 第四季娛樂部門直接面向消費者業務（Entertainment DTC）的廣告收入年增 14%，營業利益達 2.53 億美元。若廣告收入持續成長，且增收未被成本上升抵銷，即使 Disney+ Core 訂戶短期回落，Entertainment DTC 全年營業利益仍可提高。
- **催化劑**　FY2025 第一季財報可檢驗 Disney+ Core 訂戶是否如管理層預期季減，並觀察同期廣告收入。FY2025 全年財報可驗證營業利益增幅。
- **可查核預測**　預期 FY2025 第一季 Disney+ Core 訂戶季減，但 Entertainment DTC 廣告收入仍年增，全年該業務營業利益較 FY2024 增加約 8.75 億美元。
- **失效條件**　若第一季訂戶季減時廣告收入也較上年同期下滑，短期廣告支撐的預測即失準。若全年 Entertainment DTC 營業利益持平或下降，則全年獲利改善假說失效。
- **影響規模**　約 8.75 億美元是 Entertainment DTC 對年度營業利益的預期增量。FY2024 比較基期含印度 DTC 約 2 億美元的負面影響，評估可持續的獲利改善時，須辨別低基期與廣告增收各自的貢獻。
- **證據**　dis-fy24:streaming、dis-fy24:fy25

**假說 2**

- **公司**　Disney
- **傳導**　體驗部門 FY2024 第四季營業利益為 17 億美元，年減 6%。該季為次年同期提供較低的比較基期。若 FY2025 第四季營業利益回升，該季的年增金額可帶動下半財年的獲利成長。
- **催化劑**　FY2025 第二季財報可確立上半財年的營業利益年增金額。待第四季財報公布，即可比較上下半財年各自對全年增量的貢獻。
- **可查核預測**　預期 FY2025 體驗部門全年營業利益年增 6% 至 8%，且下半財年營業利益較上年同期增加的金額將大於上半財年的年增金額。
- **失效條件**　若下半財年的營業利益年增金額小於或等於上半財年，成長集中於下半年的判斷即失效。若全年增幅落在 6% 至 8% 以外，則全年幅度預測失準。
- **影響規模**　上下半年的增量分布決定達成全年指引所需的復甦幅度。上半年貢獻愈少，全年達標就愈依賴下半年，屆時可用實際營業利益衡量體驗部門對 Disney 全年獲利成長的貢獻。
- **證據**　dis-fy24:experiences

### V9 Harness

**執行狀態**　完成。

[正式回傳](raw/calls/V-02-v9.json) · [CLI 事件](raw/jobs/V-02-v9/events.jsonl) · [模型原始 JSON](raw/jobs/V-02-v9/answer.json) · [CLI 診斷](raw/jobs/V-02-v9/stderr.log)

**假說 1**

- **公司**　Disney
- **傳導**　FY2024 Q4 Entertainment DTC 廣告收入年增 14%，營業利益達 2.53 億美元。11 月 14 日公布的指引反映管理層對獲利改善的預期。多方假設是廣告成長延續，且新增收入高於相關增量成本。相較廣告收入持平的情境，即使 Disney+ Core 首季訂戶如預期季減，廣告仍可推升全年串流營業利益。印度 DTC 壓低比較基期，全年利益增額中可歸因於廣告的金額待查。
- **催化劑**　在 Disney 公布 FY2025 Q1 財報時，先看 Entertainment DTC 廣告收入是否延續年增，再用全年財報核對營業利益。
- **可查核預測**　Disney FY2025 全年財報顯示，Entertainment DTC 營業利益較 FY2024 增加，於 2025-12-31 前核對。管理層指引約增 8.75 億美元，可作增幅參照。
- **失效條件**　截至 2025-12-31，Disney 已公布的 FY2025 全年 Entertainment DTC 營業利益相較 FY2024 持平或下降。
- **影響規模**　—
- **證據**　dis-fy24:streaming、dis-fy24:fy25

**假說 2**

- **公司**　Disney
- **傳導**　FY2024 Q4 Experiences 營業利益年減 6%。11 月 14 日公布的指引將 FY2025 成長重心放在下半財年。空方假設是第四季的獲利疲弱延續至下半年，使全年少了指引仰賴的利益增量。相較下半年如期回升的情境，Experiences 對 Disney 的全年獲利貢獻將低於管理層預期。公司未量化下半年須貢獻多少增額。
- **催化劑**　Disney 公布 FY2025 Q3 財報時，可首次從下半財年的部門實績檢查回升進度，全年財報則可檢驗回升幅度是否足夠。
- **可查核預測**　Disney FY2025 全年財報顯示，Experiences 營業利益相較 FY2024 的增幅低於指引下限 6%，於 2025-12-31 前核對。
- **失效條件**　截至 2025-12-31，Disney 已公布的 FY2025 全年 Experiences 營業利益較 FY2024 成長至少 6%。
- **影響規模**　—
- **證據**　dis-fy24:experiences

## V-03 · Novo Nordisk 製造據點交易

**分組**　pilot

**研究題目**　Novo Nordisk 宣布簽約收購三座藥品充填及成品製造廠。
**截止時間**　2024-02-05T23:59:59+00:00。**研究期間**　2025-06-30。

- **novo-sites:acquisition**　Novo Nordisk 同意以約 110 億美元預付款向 Novo Holdings 購買三座充填及成品製造廠。該購買與 Novo Holdings 收購 Catalent 的交易相關。 [原始來源](https://www.novonordisk.com/content/nncorp/global/en/news-and-media/news-and-ir-materials/news-details.html?id=167017&stream=top)
- **novo-sites:capacity**　三座廠當時已與 Novo Nordisk 合作。管理層預期自 2026 年起逐步增加充填產能。 [原始來源](https://www.novonordisk.com/content/nncorp/global/en/news-and-media/news-and-ir-materials/news-details.html?id=167017&stream=top)
  - 原文短節錄：The acquisition is expected to gradually increase Novo Nordisk’s filling capacity from 2026 and onwards.

### 純 Astra

**執行狀態**　完成。

[正式回傳](raw/calls/V-03-astra.json) · [CLI 事件](raw/jobs/V-03-astra/events.jsonl) · [模型原始 JSON](raw/jobs/V-03-astra/answer.json) · [CLI 診斷](raw/jobs/V-03-astra/stderr.log)

**假說 1**

- **公司**　Novo Nordisk
- **傳導**　三座廠在簽約前已替公司生產。取得廠房所有權本身不會增加充填量，管理層預期新增產能自 2026 年起才逐步釋出。
- **催化劑**　截至 2025 年 6 月 30 日，公司更新三座廠的投產時程或產品供應指引。
- **可查核預測**　研究期內，公司對三座廠的展望仍將新增充填產能列為 2026 年起的貢獻，2025 年上半年的供應指引不會因這筆收購帶來的新增產能而上修。
- **失效條件**　若公司在研究期內明確表示收購已使三座廠的可用充填產能高於原合作安排，並據此上修 2025 年上半年的供應指引，則假說失效。
- **影響規模**　估算 2025 年上半年營收時，應將三座廠原已承接的產量計入基準，避免把同一批產量再次列為收購帶來的銷量成長。
- **證據**　novo-sites:capacity

**假說 2**

- **公司**　Novo Nordisk
- **傳導**　約 110 億美元的預付款使收購對現金的影響集中於付款時點。購廠安排與 Novo Holdings 收購 Catalent 的交易相關，因此兩筆交易的進度會影響資金需求何時顯現。
- **催化劑**　截至 2025 年 6 月 30 日，Novo Holdings 收購 Catalent 的進度，以及 Novo Nordisk 對購廠交割與付款的披露。
- **可查核預測**　若購廠交易在研究期內按公告條款交割，預期 Novo Nordisk 會在交割時支付約 110 億美元，收購現金支出將早於管理層預期自 2026 年起出現的新增產能。
- **失效條件**　若交易在研究期內交割，但披露顯示交割時的現金支付額顯著低於約 110 億美元，例如大部分對價改為遞延支付，則假說失效。若期末仍未交割，付款預測尚待驗證。
- **影響規模**　約 110 億美元的付款時點會影響期末流動性估算。研究期內的資金需求取決於交割進度，新增產能的預期貢獻則落在研究期之後。
- **證據**　novo-sites:acquisition、novo-sites:capacity

### V9 Harness

**執行狀態**　中斷。

[正式回傳](raw/calls/V-03-v9.json) · [CLI 事件](raw/jobs/V-03-v9/events.jsonl) · [CLI 診斷](raw/jobs/V-03-v9/stderr.log)

## V-04 · Ford 電動車投資重整

**分組**　pilot

**研究題目**　Ford 宣布取消原計畫的純電三排座 SUV，並重排電動車投資。
**截止時間**　2024-08-21T23:59:59+00:00。**研究期間**　2025-10-31。

- **ford-ev-8k:charges**　Ford 估計 2024 Q3 將就原計畫純電三排座 SUV 的製造及供應商模具資產認列約 4 億美元減記。另可能產生最多約 15 億美元額外費用及現金支出。 [原始來源](https://www.sec.gov/Archives/edgar/data/37996/000003799624000150/f-20240819.htm)
- **ford-ev-strategy:plans**　Ford 計畫在 2026 年於俄亥俄州開始生產新款純電商用廂型車，隨後於 2027 年推出兩款電動皮卡。公司計畫把純電車相關資本支出占年度資本支出的比例從約 40% 下調至約 30%。 [原始來源](https://www.sec.gov/Archives/edgar/data/37996/000003799624000150/exhibit99toaugust2120248.htm)
  - 原文短節錄：an all-new commercial van that will begin production in 2026 in Ohio

### 純 Astra

**執行狀態**　排隊未開始。

### V9 Harness

**執行狀態**　排隊未開始。

## E-01 · Adobe｜監管與併購終止

**分組**　holdout

**研究題目**　Adobe 與 Figma 宣布終止原收購協議。這個事件對 Adobe 的營運可能有哪些不同影響？
**截止時間**　2023-12-18T23:59:59+00:00。**研究期間**　2024-12-31。

- **adbe-termination:fee**　Adobe 公布雙方在 12 月 17 日簽署終止協議。Adobe 須在三個營業日內向 Figma 支付 10 億美元現金。 [原始來源](https://www.sec.gov/Archives/edgar/data/796343/000079634323000254/adbe-20231217.htm)
  - 原文短節錄：a cash payment to Figma in the previously agreed amount of one billion dollars
- **adbe-joint-release:regulation**　雙方表示無法看到取得英國競爭及市場管理局與歐盟執委會所需批准的明確途徑。原協議擬以現金與股票收購 Figma。 [原始來源](https://www.sec.gov/Archives/edgar/data/796343/000079634323000254/adbedecember182023pressrel.htm)
  - 原文短節錄：there is no clear path to receive necessary regulatory approvals

### 純 Astra

**執行狀態**　未排入。

### V9 Harness

**執行狀態**　未排入。

## E-02 · ExxonMobil｜資產整併

**分組**　holdout

**研究題目**　ExxonMobil 宣布完成收購 Pioneer Natural Resources。分析其營運傳導。
**截止時間**　2024-05-03T23:59:59+00:00。**研究期間**　2025-12-31。

- **xom-pioneer:acreage**　公告把相鄰探勘資產、技術與營運能力結合，列為交易可提高資源回收的依據。 [原始來源](https://corporate.exxonmobil.com/news/news-releases/2024/0503_exxonmobil-completes-acquisition-of-pioneer-natural-resources)
- **xom-pioneer:output**　公司以 2023 年產量估算，交易使二疊紀盆地日產量增逾一倍至 130 萬桶油當量，初估 2027 年達約 200 萬桶油當量。 [原始來源](https://corporate.exxonmobil.com/news/news-releases/2024/0503_exxonmobil-completes-acquisition-of-pioneer-natural-resources)
  - 原文短節錄：will more than double to 1.3 million barrels of oil equivalent per day

### 純 Astra

**執行狀態**　未排入。

### V9 Harness

**執行狀態**　未排入。

## E-03 · Starbucks｜營運重整與指引撤回

**分組**　holdout

**研究題目**　Starbucks 公布初步第四季數字並暫停下一財年指引。分析重整可能如何影響營運。
**截止時間**　2024-10-22T23:59:59+00:00。**研究期間**　2025-12-31。

- **sbux-prelim:drivers**　公司將表現歸因於客流走弱、加碼投入未改善顧客行為，以及中國景氣與競爭壓力。 [原始來源](https://about.starbucks.com/press/2024/starbucks-reports-preliminary-q4-and-full-fiscal-year-2024-results/)
- **sbux-prelim:guidance**　公司因執行長交接與目前營運情況，暫停整個 2025 財年的指引。 [原始來源](https://about.starbucks.com/press/2024/starbucks-reports-preliminary-q4-and-full-fiscal-year-2024-results/)
  - 原文短節錄：guidance will be suspended for the full fiscal year 2025
- **sbux-prelim:sales**　第四季全球同店銷售年減 7%，美國同店銷售年減 6%，中國同店銷售年減 14%。 [原始來源](https://about.starbucks.com/press/2024/starbucks-reports-preliminary-q4-and-full-fiscal-year-2024-results/)

### 純 Astra

**執行狀態**　未排入。

### V9 Harness

**執行狀態**　未排入。

## E-04 · Visa｜競爭執法

**分組**　holdout

**研究題目**　美國司法部對 Visa 的扣帳卡網路業務提起民事反壟斷訴訟。分析這項事件可能如何影響 Visa。
**截止時間**　2024-09-24T23:59:59+00:00。**研究期間**　2025-12-31。

- **visa-doj:allegation**　司法部提出民事訴訟，指控 Visa 在扣帳卡網路市場壟斷及有其他違法行為。 [原始來源](https://www.justice.gov/archives/opa/pr/justice-department-sues-visa-monopolizing-debit-markets)
  - 原文短節錄：filed a civil antitrust lawsuit today against Visa
- **visa-doj:contracts**　起訴指稱 Visa 以交易量承諾約束商戶、收單機構與發卡機構。這些是司法部指控。 [原始來源](https://www.justice.gov/archives/opa/pr/justice-department-sues-visa-monopolizing-debit-markets)
- **visa-q3:baseline**　Visa 第三財季合併淨營收 89 億美元，年增 10%；資料處理收入 45 億美元，年增 9%。這些是全球口徑。 [原始來源](https://www.sec.gov/Archives/edgar/data/1403161/000140316124000040/q32024earningsrelease.htm)
  - 原文短節錄：Data processing revenue rose 9% over the prior year to $4.5 billion.

### 純 Astra

**執行狀態**　未排入。

### V9 Harness

**執行狀態**　未排入。

## E-05 · Johnson & Johnson｜新技術整併

**分組**　holdout

**研究題目**　Johnson & Johnson 完成收購 Shockwave Medical。分析其醫療器材業務可能出現的不同變化。
**截止時間**　2024-05-31T23:59:59+00:00。**研究期間**　2025-12-31。

- **jnj-shockwave-close:portfolio**　Johnson & Johnson 公布完成交易，Shockwave 的血管內震波碎石（IVL）技術補充其心血管介入器材組合。 [原始來源](https://www.investor.jnj.com/investor-news/news-details/2024/Johnson--Johnson-Completes-Acquisition-of-Shockwave-Medical/default.aspx)
  - 原文短節錄：Completes Acquisition of Shockwave Medical
- **jnj-shockwave-terms:terms**　交易對價為每股 335 美元現金。包含取得的現金，企業價值約 131 億美元。 [原始來源](https://www.investor.jnj.com/investor-news/news-details/2024/Johnson--Johnson-to-Acquire-Shockwave-Medical/default.aspx)
  - 原文短節錄：corresponding to an enterprise value of approximately $13.1 billion including cash acquired

### 純 Astra

**執行狀態**　未排入。

### V9 Harness

**執行狀態**　未排入。

## E-06 · Spotify｜訂閱定價

**分組**　holdout

**研究題目**　Spotify 公布美國 Premium 套餐調價。分析調價可能如何影響訂閱業務。
**截止時間**　2024-06-03T23:59:59+00:00。**研究期間**　2025-06-30。

- **spot-us-prices:prices**　美國新訂戶的 Individual、Duo、Family、Student 價格分別為 11.99、16.99、19.99、5.99 美元。 [原始來源](https://newsroom.spotify.com/2024-06-03/adjusting-spotify-premium-prices-in-the-us/)
- **spot-us-prices:rollout**　Spotify 說未來一個月會以電子郵件通知美國現有訂戶。 [原始來源](https://newsroom.spotify.com/2024-06-03/adjusting-spotify-premium-prices-in-the-us/)
  - 原文短節錄：Over the next month, subscribers in the U.S. will receive an email
- **spot-prior-prices:comparison**　2023 年公告的同四種美國套餐價格分別為 10.99、14.99、16.99、5.99 美元。 [原始來源](https://newsroom.spotify.com/2023-07-24/adjusting-our-spotify-premium-prices/)
  - 原文短節錄：$10.99 $14.99 $16.99 $5.99

### 純 Astra

**執行狀態**　未排入。

### V9 Harness

**執行狀態**　未排入。

## E-07 · Delta Air Lines｜營運中斷

**分組**　holdout

**研究題目**　Delta Air Lines 公布 7 月資訊系統中斷的估計財務影響。分析這項事件可能如何傳導。
**截止時間**　2024-08-08T23:59:59+00:00。**研究期間**　2025-06-30。

- **dal-outage:cancellations**　Delta 報告 7 月 19 日起受到 CrowdStrike 相關故障影響，約 7,000 個航班在五天內取消。 [原始來源](https://www.sec.gov/Archives/edgar/data/27904/000168316824005369/delta_8k.htm)
- **dal-outage:costs**　公司估計新增約 1.7 億美元非燃油支出，部分由取消航班減少燃油成本抵減。 [原始來源](https://www.sec.gov/Archives/edgar/data/27904/000168316824005369/delta_8k.htm)
- **dal-outage:revenue**　公司估計 9 月季度有 3.8 億美元直接營收影響，主要來自退款及現金或 SkyMiles 補償。 [原始來源](https://www.sec.gov/Archives/edgar/data/27904/000168316824005369/delta_8k.htm)
  - 原文短節錄：the direct revenue impact of the incident is estimated to be $380 million

### 純 Astra

**執行狀態**　未排入。

### V9 Harness

**執行狀態**　未排入。

## E-08 · Ørsted｜專案取消與資本配置

**分組**　holdout

**研究題目**　Ørsted 宣布終止兩個美國離岸風電案，並對另一個專案做出最終投資決策。分析專案組合變更。
**截止時間**　2023-10-31T23:59:59+00:00。**研究期間**　2024-12-31。

- **orsted-us-wind:impairment**　首九個月總減損為 284 億丹麥克朗，其中 199 億與 Ocean Wind 1 有關。 [原始來源](https://orsted.com/en/company-announcement-list/2023/10/oersted-ceases-development-of-its-us-offshore-wind-73751)
- **orsted-us-wind:portfolio**　董事會決議停止 Ocean Wind 1 和 2，並對 Revolution Wind 做出最終投資決策。 [原始來源](https://orsted.com/en/company-announcement-list/2023/10/oersted-ceases-development-of-its-us-offshore-wind-73751)
  - 原文短節錄：has taken final investment decision on the Revolution Wind project
- **orsted-us-wind:provision**　Ocean Wind 1 的潛在解約成本準備估計約 80 至 110 億丹麥克朗，影響第四季 EBITDA。 [原始來源](https://orsted.com/en/company-announcement-list/2023/10/oersted-ceases-development-of-its-us-offshore-wind-73751)

### 純 Astra

**執行狀態**　未排入。

### V9 Harness

**執行狀態**　未排入。

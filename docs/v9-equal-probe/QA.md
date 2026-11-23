# V9 等預算逐案問答

此紀錄供結果查核。匿名人評應使用獨立的匿名 PDF 和空白表。下列為生成時點可見的封存摘要，並附原文摘錄與可開啟的原始公告。

## 服務探針 · IBM

探針的回傳與帳本獨立保存，供判斷本輪正式評測可否開跑。

**研究題目**　IBM 公布完成收購 HashiCorp。分析這筆交易如何影響 IBM 的混合雲與自動化軟體營運。
**截止時間**　2025-02-27T23:59:59+00:00。**研究期間**　2026-06-30。

- **ibm-hashicorp-close:closing**　IBM 完成收購 HashiCorp 全部流通普通股，每股現金 35 美元，企業價值約 64 億美元。 [原始來源](https://newsroom.ibm.com/2025-02-27-ibm-completes-acquisition-of-hashicorp%2C-creates-comprehensive%2C-end-to-end-hybrid-cloud-platform)
  - 原文短節錄：representing an enterprise value of $6.4 billion
- **ibm-hashicorp-close:distribution**　IBM 把 Red Hat、watsonx、資料安全、IT 自動化與顧問服務列為可能出現綜效的領域。 [原始來源](https://newsroom.ibm.com/2025-02-27-ibm-completes-acquisition-of-hashicorp%2C-creates-comprehensive%2C-end-to-end-hybrid-cloud-platform)
- **ibm-hashicorp-close:integration**　IBM 宣布 Terraform、Vault 及其他 HashiCorp 產品當時已納入 IBM 自動化軟體組合。IBM 以 Terraform 與 Red Hat Ansible 的結合為例：前者供應跨雲基礎設施，後者管理其上的應用設定及中介軟體部署。 [原始來源](https://newsroom.ibm.com/2025-02-27-ibm-completes-acquisition-of-hashicorp%2C-creates-comprehensive%2C-end-to-end-hybrid-cloud-platform)

### P-01 · 完成

[探針回傳](raw/service-probe/calls/P-01-v9.json) · [CLI 事件](raw/service-probe/jobs/P-01-v9/events.jsonl) · [模型原始 JSON](raw/service-probe/jobs/P-01-v9/answer.json) · [CLI 診斷](raw/service-probe/jobs/P-01-v9/stderr.log)

**假說 1**

- **公司**　IBM
- **傳導**　交割後，IBM 可把 Terraform 的跨雲資源佈建與 Red Hat Ansible 的應用設定納入同一支援流程。相較兩套工具由客戶自行串接，若 IBM 承接跨產品支援，可降低導入成本，增加既有客戶加購自動化軟體的機會。客戶仍須決定採用並簽約，IBM 才可能隨履約認列收入。加購戶數、合約金額及增量毛利未知。
- **催化劑**　2025-02-27 交割公告已確認產品納入組合，並舉出 Terraform 與 Ansible 的分工。交割後的產品發行與支援政策更新可檢驗兩者是否進一步整合。
- **可查核預測**　以交割公告僅描述兩套工具分工為基準，至 2026-06-30，IBM 或 Red Hat 的公開產品文件將列出至少一項交割後新增、正式支援且涵蓋兩個步驟的流程。這是交付能力的代理指標，無法證明客戶已下單、採用或貢獻營收。
- **失效條件**　若截至 2026-06-30 的 IBM 或 Red Hat 官方支援範圍明確顯示，交割以來正式支援的新增雙步驟流程為零，則推翻此項交付預測。若文件未交代支援範圍或新增時間，結果仍待查。
- **影響規模**　—
- **證據**　ibm-hashicorp-close:integration、ibm-hashicorp-close:distribution

**假說 2**

- **公司**　IBM
- **傳導**　收購可能使 IBM 在購價分攤時認列有年限的軟體技術或客戶關係無形資產，並自交割後提列攤銷。若交易未發生，IBM 不會承擔本案新增的攤銷費用。即使整合產品順利交付，這項非現金費用仍會壓低 IBM 的 GAAP 稅前利益。約 64 億美元企業價值不足以推算費用規模。
- **催化劑**　2025-02-27 完成交割後，IBM 須進行收購會計處理。可在 2025 年度 Form 10-K 公布後、2026-06-30 前查閱企業合併及無形資產附註。
- **可查核預測**　相較未交易時本案攤銷為零，預期 IBM 對交割日至 2025 年底的購價分攤會列出正額、已開始攤銷的本案無形資產。資產類別、金額及起攤時點可驗證費用機制，實際稅前利益影響仍取決於耐用年限與攤銷方式。
- **失效條件**　若截至 2026-06-30 可取得的 IBM 附註明示，交割日至 2025 年底本案已起攤的收購無形資產金額為零，則推翻該期間的攤銷假設。僅有 IBM 合計攤銷、未拆出本案時，結論仍未定。
- **影響規模**　—
- **證據**　ibm-hashicorp-close:closing

## V-01 · UPS 客戶量縮與網路重整

**分組**　pilot

**研究題目**　UPS 宣布計畫削減最大客戶的包裹量，並重新配置美國配送網路。
**截止時間**　2025-01-30T23:59:59+00:00。**研究期間**　2026-03-31。

- **ups-q4:guidance**　UPS 預估 2025 全年合併營收約 890 億美元，營業利益率約 10.8%。 [原始來源](https://investors.ups.com/news-events/press-releases/detail/2135/ups-releases-4q-2024-earnings-and-provides-2025-guidance)
- **ups-q4:network**　UPS 宣布重整美國網路，並計畫透過多年流程重設創造約 10 億美元節省。 [原始來源](https://investors.ups.com/news-events/press-releases/detail/2135/ups-releases-4q-2024-earnings-and-provides-2025-guidance)
- **ups-q4:volume**　UPS 與最大客戶原則上達成協議，計畫至 2026 年下半年將該客戶包裹量減少逾 50%。2025 年 1 月 1 日起 UPS 將 SurePost 全數改為自行配送。 [原始來源](https://investors.ups.com/news-events/press-releases/detail/2135/ups-releases-4q-2024-earnings-and-provides-2025-guidance)
  - 原文短節錄：lower its volume by more than 50% by the second half of 2026

### 純 Astra

**執行狀態**　完成。

[正式回傳](raw/calls/V-01-astra.json) · [CLI 事件](raw/jobs/V-01-astra/events.jsonl) · [模型原始 JSON](raw/jobs/V-01-astra/answer.json) · [CLI 診斷](raw/jobs/V-01-astra/stderr.log)

**假說 1**

- **公司**　UPS
- **傳導**　若最大客戶的包裹量在 2025 年開始下降，而 UPS 調整美國配送網路的速度落後於減量速度，每件包裹須分攤的固定成本將上升，壓低營業利益率。
- **催化劑**　追蹤 UPS 在 2025 年揭露的最大客戶減量進度與美國網路調整時程，並於 2026 年 3 月 31 日前以全年業績檢驗。
- **可查核預測**　2025 年合併營業利益率將低於公司指引中值 10.8%，且 UPS 對美國配送業務的說明將指出，包裹量下降使固定成本更難攤薄。
- **失效條件**　若 2025 年合併營業利益率達到或超過 10.8%，則財務預測失準。若利益率低於 10.8%，但 UPS 揭露網路成本已隨減量同步下降，則利益率落差本身不足以支持此機制。
- **影響規模**　以公司預估的 890 億美元全年營收計算，合併營業利益率每低於指引 0.1 個百分點，約對應 8,900 萬美元營業利益差額。
- **證據**　ups-q4:volume、ups-q4:network、ups-q4:guidance

**假說 2**

- **公司**　UPS
- **傳導**　SurePost 改由 UPS 全數自行配送後，若新增包裹能併入既有路線，UPS 可提高每條路線的投遞量，並以省下的委外配送費抵銷新增工時與里程成本。
- **催化劑**　SurePost 自 2025 年 1 月 1 日起全面轉為自行配送。2025 年第四季是轉換後首個可與前一年同期比較的年終旺季，可用截至 2026 年 3 月 31 日已揭露的第四季資料檢驗。
- **可查核預測**　相較 2024 年第四季，2025 年第四季 SurePost 每件包裹的最終配送成本將下降。若 UPS 提供成本拆解，應可見每件節省的委外費用高於新增的內部配送成本。
- **失效條件**　若 UPS 揭露同期 SurePost 每件最終配送成本持平或上升，或指出新增內部配送成本已抵銷全部委外費用節省，則假說失效。若僅揭露整體網路節省額，則此假說仍待驗證。
- **影響規模**　全面自配使每件成本差額作用於全部 SurePost 包裹。估算其營業利益影響需要件量與單件成本差額，兩者在截止時點均未提供。公司約 10 億美元的節省目標涵蓋多年流程重設，不能直接歸因於 SurePost。
- **證據**　ups-q4:volume、ups-q4:network

### V9 Harness

**執行狀態**　完成。

[正式回傳](raw/calls/V-01-v9.json) · [CLI 事件](raw/jobs/V-01-v9/events.jsonl) · [模型原始 JSON](raw/jobs/V-01-v9/answer.json) · [CLI 診斷](raw/jobs/V-01-v9/stderr.log)

**假說 1**

- **公司**　UPS
- **傳導**　若 UPS 隨最大客戶逐步減量而合併分揀班次及配送路線，相較減量後仍維持原網路，可少付閒置產能的成本。若當年節省超過重整費用，將支撐營業利益率。約 10 億美元是多年節省目標，2025 年淨節省額待查。
- **催化劑**　UPS 於 2025 年 1 月 30 日宣布重整美國網路。觀察 2025 年內流程調整進度，並於 2026 年 3 月 31 日前核對 UPS 全年業績公告。
- **可查核預測**　UPS 2025 全年合併營業利益率按原指引口徑達 10.8% 或以上。以指引中心值作情境門檻，此合併指標只能檢驗獲利表現，網路重整的貢獻仍須看成本說明。
- **失效條件**　截至 2026 年 3 月 31 日，UPS 公布的 2025 全年同口徑合併營業利益率低於 10.8%，即推翻此獲利預測。若公司另有節省，仍可能被其他成本抵銷。
- **影響規模**　—
- **證據**　ups-q4:network、ups-q4:volume、ups-q4:guidance

**假說 2**

- **公司**　UPS
- **傳導**　若最大客戶減量早於 UPS 編製指引時的假設，相較維持原承運量，UPS 完成的收費配送將減少。若其他客戶的包裹量或單件收入不足以填補缺口，全年營收可能低於指引中心值。客戶實際減量時程與單件收入均未揭露。
- **催化劑**　2025 年 1 月 30 日公布原則協議後，觀察減量是否已影響 2025 年配送業務，並於 2026 年 3 月 31 日前核對 UPS 全年業績公告。減量逾半的計畫期限在 2026 年下半年。
- **可查核預測**　UPS 2025 全年合併營收低於原指引中心值 890 億美元。合併營收是淨影響的代理指標，須搭配 UPS 對美國業務包裹量的說明，才能判斷減量是否為原因。
- **失效條件**　截至 2026 年 3 月 31 日，UPS 公布的 2025 全年合併營收達 890 億美元或以上，即推翻此營收預測，即使最大客戶已開始減量。
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
- **傳導**　2024 財年第四季，Entertainment DTC 廣告收入年增 14%，營業利益達 2.53 億美元。若廣告收入持續成長，即使 Disney+ Core 訂戶如管理層預期在 2025 財年第一季季減，廣告仍可支撐全年獲利改善。2024 財年比較基期亦包含印度 DTC 約 2 億美元的負面影響。
- **催化劑**　2025 財年第一季財報可初步檢驗訂戶變動時廣告收入與營業利益的走勢，全年財報則可檢驗獲利增額。
- **可查核預測**　預期 2025 財年 Entertainment DTC 廣告收入高於上年，全年營業利益年增約 8.75 億美元，增額接近管理層指引。
- **失效條件**　若全年廣告收入持平或下滑，廣告成長支撐獲利的機制即失去依據。若全年營業利益增額僅約 2 億美元或更低，則獲利改善幅度明顯低於預測。
- **影響規模**　8.75 億美元的預期利益增額遠高於印度 DTC 對比較基期約 2 億美元的負面影響。兩者的差距是判斷串流業務獲利改善幅度的重要尺度。
- **證據**　dis-fy24:streaming、dis-fy24:fy25

**假說 2**

- **公司**　Disney
- **傳導**　2024 財年第四季體驗部門營業利益為 17 億美元，年減 6%，使次年同期的比較基期較低。若第四季獲利回升，該季的年增額可帶動下半財年貢獻較多的全年利益增量，符合管理層對成長時點的預期。
- **催化劑**　2025 財年第二季財報可確立上半年營業利益年增額，第四季及全年財報可用相同口徑比較兩個半年度的貢獻。
- **可查核預測**　預期 2025 財年體驗部門全年營業利益年增 6% 至 8%，且下半年相較上年同期的營業利益增額高於上半年。
- **失效條件**　若全年營業利益增幅落在 6% 至 8% 以外，全年幅度預測即告失準。即使全年增幅達標，若下半年年增額等於或低於上半年，成長集中於下半年的判斷仍告失準。
- **影響規模**　體驗部門單季營業利益達 17 億美元。若全年利益增量主要來自下半年，依上半年增速推估全年，會低估該部門對 Disney 營業利益成長的貢獻。
- **證據**　dis-fy24:experiences

### V9 Harness

**執行狀態**　完成。

[正式回傳](raw/calls/V-02-v9.json) · [CLI 事件](raw/jobs/V-02-v9/events.jsonl) · [模型原始 JSON](raw/jobs/V-02-v9/answer.json) · [CLI 診斷](raw/jobs/V-02-v9/stderr.log)

**假說 1**

- **公司**　Disney
- **傳導**　FY2024 Q4 Entertainment DTC 廣告收入年增 14%，營業利益達 2.53 億美元。若 FY2025 廣告收入持續成長，且新增收入高於相關增量成本，則相較廣告收入持平的情境，串流可為 Disney 貢獻更多營業利益。財測傳達管理層預期，廣告增量利益仍待驗證。
- **催化劑**　2024-11-14 財測預期 FY2025 Entertainment DTC 營業利益年增約 8.75 億美元，同時預期 Q1 Disney+ Core 訂戶季減。FY2025 Q1 財報是檢查廣告收入能否延續成長的首個窗口。
- **可查核預測**　截至 2025-12-31，預期 Disney 的 FY2025 Q1 財報顯示 Entertainment DTC 廣告收入高於上年同期，全年財報顯示同口徑營業利益高於 FY2024。另以約 8.75 億美元指引衡量改善幅度。
- **失效條件**　若 Disney 公布 FY2025 Q1 Entertainment DTC 廣告收入持平或年減，則廣告成長的首季預測失效。若 FY2025 全年同口徑營業利益持平或年減，則全年獲利預測失效。未揭露的項目仍待驗證。
- **影響規模**　—
- **證據**　dis-fy24:streaming、dis-fy24:fy25

**假說 2**

- **公司**　Disney
- **傳導**　FY2024 Q4 Experiences 營業利益年減 6%，管理層預期 FY2025 成長偏向下半年。若上半年留下的獲利缺口較大，下半年即使恢復年增，也可能來不及補足全年所需增量。相較下半年如期回升的情境，Disney 來自體驗部門的營業利益將低於指引隱含水準。上半年缺口大小屬情境假設。
- **催化劑**　2024-11-14 公布的 FY2025 Experiences 營業利益指引為年增 6% 至 8%。FY2025 Q2 財報可先量出上半年增減額，Q4 暨全年財報可核對下半年回升是否足夠。
- **可查核預測**　預期 Disney 的 FY2025 全年財報顯示 Experiences 營業利益較 FY2024 成長低於 6%，於 2025-12-31 前核對。以兩個半年度各自的年增減額檢查缺口形成的時間。
- **失效條件**　若 Disney 於 2025-12-31 前公布 FY2025 全年 Experiences 營業利益較 FY2024 成長達 6% 或以上，則全年低於指引下緣的預測失效。
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

**執行狀態**　失敗。

[正式回傳](raw/calls/V-03-astra.json) · [CLI 事件](raw/jobs/V-03-astra/events.jsonl) · [CLI 診斷](raw/jobs/V-03-astra/stderr.log)

**失敗原因**　CLI 回報限流或用量上限

### V9 Harness

**執行狀態**　排隊未開始。

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

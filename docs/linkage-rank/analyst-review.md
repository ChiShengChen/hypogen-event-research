# 主要財務傳導 · 匿名分析師覆核

每案三份研究稿採相同點時證據。依稿內順序，核對兩端引文、必要因果條件、財務歸因、以及能區別至少一種其他解釋的公開查核。請指出最值得查核的傳導，以及稿件將它排在第幾位。若因果尚未建立，請核對稿件是否指出具體缺項並保留歸因。

每份稿件記錄能否進入分析師覆核、重大錯誤、必要修稿時間（秒）及理由。所有二元項填 1 或 0，無適用項目請留白並說明。每案三份全部回收才計為一案完成。請在填表前獨立閱讀本 PDF。

## P-01 · Cisco

**研究題目**　Cisco 公布完成一項收購。請提出可供研究員覆核的繁體中文研究首稿。

**截止**　2024-03-18T23:59:59+00:00　**研究期限**　2025-12-31

- `cisco-release:deal`　Cisco 完成收購 Splunk，每股現金 157 美元，總股權價值約 280 億美元。 [官方來源](https://newsroom.cisco.com/c/r/newsroom/en/us/a/y2024/m03/cisco-completes-acquisition-of-splunk.html)
- `cisco-release:forecasts`　公司預期收購在 FY2025 對現金流有正貢獻（扣除若干收購相關及其他項目）並提高非 GAAP 毛利率，FY2026 提高非 GAAP EPS。未披露組合產品的客戶轉換、價格或營收。 [官方來源](https://newsroom.cisco.com/c/r/newsroom/en/us/a/y2024/m03/cisco-completes-acquisition-of-splunk.html)
- `cisco-release:operations`　公告把 Splunk 的資料能力與 Cisco Security 及 Observability 放在同一平台策略中，目標是改善威脅辨識及應用可視性。 [官方來源](https://newsroom.cisco.com/c/r/newsroom/en/us/a/y2024/m03/cisco-completes-acquisition-of-splunk.html)
- `cisco-release:original`　公告開頭及財務展望段落原文：non-GAAP gross margin accretive in Cisco’s fiscal year 2025 [官方來源](https://newsroom.cisco.com/c/r/newsroom/en/us/a/y2024/m03/cisco-completes-acquisition-of-splunk.html)

### 研究稿 D-07C499EC

**1. Splunk 的資料能力 → Cisco · Observability**

- 起點引文　cisco-release:deal、cisco-release:operations
- 受影響業務引文　cisco-release:operations
- 傳導機制　交割後，若 Cisco 決定把 Splunk 資料接入 Observability 的應用可視性功能，工程團隊就需完成接入和驗證。若驗證延誤，相關支出可能先於新增收款，增加整合拖累現金流的可能。
- 比較基準　未收購情境下，原有 Observability 產品可沿既有路線開發。交割公告只列出平台目標，未提供整合功能的上市基準日。
- 必要條件　Cisco 實際啟動該項整合，且資料接入或驗證成為延後正式推出的原因。
- 財務影響　開發投入先行、可銷售時間延後，可能壓低 Observability 的增量現金流。專案支出、收費方式及付費採用規模均未知。
- 其他解釋　分階段推出也可能是原定產品策略。可比對 Cisco 公布的上市範圍及時程修訂理由，辨別是否因整合受阻。
- 查核指標　具名整合功能是否依 Cisco 首次公開的時程正式推出，作為執行進度代理指標。
- 觀察期間　交割日至 2025-12-31，限原訂於此期間正式推出的功能。
- 公開查核來源　Cisco Newsroom 的 Observability 產品公告及正式上市更新。
- 截止日　2025-12-31
- 預測　Cisco 公開確認同一功能因資料接入或驗證問題遲於原訂時程推出。
- 推翻條件　Cisco 公開確認同一功能在原訂時程內正式推出。若缺少公開時程或進度說明，延誤原因仍待查。

**待查**　公告未交代 Cisco Security 與 Observability 的人力、預算或銷售資源分配，無從判定一方是否排擠另一方。功能上市也無法驗證付費採用或回收期。

### 研究稿 D-DC481AD3

**1. Splunk 的資料能力 → Cisco · Observability**

- 起點引文　cisco-release:operations、cisco-release:deal
- 受影響業務引文　cisco-release:operations
- 傳導機制　交割後，若 Cisco 將 Splunk 資料接入 Observability 的正式產品，客戶可用該資料分析應用表現。若客戶因此付費擴充，毛利上行便多了一項來自既有業務的來源。
- 比較基準　交割公告提出共同平台策略，當時可核實的是整合目標，付費功能及採用規模仍待確認。
- 必要條件　Cisco 須推出正式可用的整合功能，客戶也須因該功能增加支出，增量收入才可能轉為毛利。
- 財務影響　付費擴充可增加 Observability 營收；增量毛利取決於付費用量、實收價格及資料處理成本，三者均未披露。
- 其他解釋　既有產品更新也可能改善應用可視性。產品說明須具名指出 Splunk 資料在功能中的用途，才能辨別收購的技術貢獻；辨別收入貢獻另需付費擴充資料。
- 查核指標　Cisco 公開文件所列、使用 Splunk 資料的 Observability 功能供應狀態，作為技術整合的代理指標。
- 觀察期間　2024-03-18 交割公告至 2025-12-31
- 公開查核來源　Cisco Newsroom 產品公告及 Observability 公開版本說明
- 截止日　2025-12-31
- 預測　截至覆核日，Cisco 公開確認至少一項使用 Splunk 資料的 Observability 功能已正式可用。
- 推翻條件　截至同一覆核日，Cisco 公開確認相關 Observability 整合功能全數仍處於預覽、延後或取消狀態。未更新狀態則保留判斷。

**待查**　約 280 億美元是收購股權對價，無從據此推算 Cisco Security 或 Observability 的預算。公告也未給出業務間的人力調撥、通路承諾或具名客戶採購決定。Cisco Security 與 Observability 共用同一平台策略，另列一條相同路徑無法增加辨識力。

### 研究稿 D-DF70BA16

**1. Splunk 的資料分析能力 → Cisco · Cisco Security 的威脅辨識產品**

- 起點引文　cisco-release:operations
- 受影響業務引文　cisco-release:operations、cisco-release:forecasts
- 傳導機制　若 Splunk 的資料能改善威脅辨識，既有 Cisco Security 客戶可能在續約時加購整合功能。
- 比較基準　截至 2024 年 3 月 18 日，Cisco 已公布平台整合方向，但未披露組合產品的客戶轉換率、成交價格或營收。
- 必要條件　Cisco 須推出可收費的整合功能，且客戶加購金額須高於原合約折讓或被取代的授權收入。
- 財務影響　符合條件的加購可提高 Cisco Security 每次續約的合約金額，並隨履約增加營收。現有資料不足以估算規模。
- 其他解釋　Cisco 的合併營收也可能因納入 Splunk 原有合約而增加，即使既有 Cisco Security 客戶的支出沒有變化。
- 查核指標　既有 Cisco Security 客戶加購整合功能所帶來的淨新增合約金額，扣除折讓及被取代的授權金額。
- 觀察期間　自交易完成至 2025 年 12 月 31 日，以期間內公開揭露的續約批次為準。
- 公開查核來源　Cisco 季度業績公告、法說會或投資人簡報中對既有客戶加購的量化說明。
- 截止日　2025-12-31
- 預測　若整合產生交叉銷售，採用整合功能的既有客戶在可比期間、相同合約年期下，續約淨新增合約金額應為正。
- 推翻條件　若可比續約資料顯示，折讓及被取代的授權金額已抵銷全部加購金額，則該批次不支持此假設。若只披露合併營收，假設仍待驗證。

**待查**　公告也把 Cisco Observability 列入平台策略，但僅說明改善應用可視性的目標。要獨立評估該業務，仍需客戶採用、付費轉換或可歸屬的營收資料。

## P-02 · Procter & Gamble

**研究題目**　Procter & Gamble 公布 2025 財年第一季結果。請提出可供研究員覆核的繁體中文研究首稿。

**截止**　2024-10-18T23:59:59+00:00　**研究期限**　2025-10-31

- `procter-release:beauty`　Beauty 有機銷售年減 2%。公司指出 Hair Care 及 Personal Care 成長，Skin Care 衰退。 [官方來源](https://d18rn0p25nwr6d.cloudfront.net/CIK-0000080424/59da93f7-916a-4c2f-b94c-60180850c7ac.html)
- `procter-release:grooming`　Grooming 有機銷售年增 3%，有機銷量年增 5%；銷售表另列外匯、價格和組合。 [官方來源](https://d18rn0p25nwr6d.cloudfront.net/CIK-0000080424/59da93f7-916a-4c2f-b94c-60180850c7ac.html)
- `procter-release:original`　Exhibit 99.1，Net Sales Drivers，Beauty 及 Grooming 列原文：Beauty segment organic sales decreased two percent versus year ago. [官方來源](https://d18rn0p25nwr6d.cloudfront.net/CIK-0000080424/59da93f7-916a-4c2f-b94c-60180850c7ac.html)
- `procter-release:outlook`　維持 FY2025 稀釋後 EPS 年增 10% 至 12% 指引。 [官方來源](https://d18rn0p25nwr6d.cloudfront.net/CIK-0000080424/59da93f7-916a-4c2f-b94c-60180850c7ac.html)

### 研究稿 D-BBEF2E01

**待查**　公司揭露了 Skin Care、Hair Care 與 Personal Care 各自的成長方向，但缺少品類權重與銷售貢獻，無法量化三者對 Beauty 的影響。資料也未揭露 Beauty 與 Grooming 之間的客戶移轉、通路連動或成本分攤，兩個部門的成長差異不足以建立跨業務因果關係。

### 研究稿 D-29DFC3EF

**待查**　同份季報揭露了各品類表現，但未指出 Skin Care 走弱後，公司曾將行銷預算或貨架空間轉給 Hair Care、Personal Care 或 Grooming。要檢驗跨品類影響，需有具名資源移轉或通路配置紀錄、實施期間，以及受影響品類的銷售變化。資料也未揭露具名交易對手或支出承諾。

### 研究稿 D-136B2FA9

**待查**　Hair Care、Personal Care 與 Skin Care 的成長方向分歧，但公司未揭露三者之間的通路陳列、促銷預算或產能移轉。要檢驗跨品類影響，需有公司指明資源從哪個品類移往哪個品類，並能追蹤受影響品類同期的銷量或銷售變化。

## P-03 · T-Mobile

**研究題目**　T-Mobile 公布一項無線業務收購協議。請提出可供研究員覆核的繁體中文研究首稿。

**截止**　2024-05-28T23:59:59+00:00　**研究期限**　2025-12-31

- `t-mobile-release:deal`　T-Mobile 同意以約 44 億美元（含至多 20 億美元承接債務）收購 UScellular Wireless Operations，包括客戶與特定頻譜。交易須滿足交割條件。 [官方來源](https://www.t-mobile.com/news/business/uscellular-acquisition-operations-assets)
- `t-mobile-release:original`　交易範圍、租賃及成本協同段落原文：lease space on at least 2,100 additional towers being retained [官方來源](https://www.t-mobile.com/news/business/uscellular-acquisition-operations-assets)
- `t-mobile-release:other`　T-Mobile 預期整合後每年約 10 億美元的合計營運支出及資本支出節省，整合成本估 22 至 26 億美元；公司未將成本節省分配至各項安排。 [官方來源](https://www.t-mobile.com/news/business/uscellular-acquisition-operations-assets)
- `t-mobile-release:towers`　UScellular 保留鐵塔業務及其他頻譜；交割後 T-Mobile 長期租用其額外至少 2,100 座鐵塔空間。 [官方來源](https://www.t-mobile.com/news/business/uscellular-acquisition-operations-assets)

### 研究稿 D-18EA784E

**1. UScellular Wireless Operations → UScellular · 鐵塔業務**

- 起點引文　t-mobile-release:deal
- 受影響業務引文　t-mobile-release:towers、t-mobile-release:original
- 傳導機制　UScellular 出售無線營運後保留鐵塔。若 T-Mobile 依約起租，UScellular 便可從新增站點取得長期租金，同一筆租金也是 T-Mobile 的網路成本。
- 比較基準　若無交易，UScellular 沒有本協議帶來的新增租賃承諾。至少 2,100 座是約定新增租用的鐵塔數。
- 必要條件　交易完成，且至少部分新增站點在觀察期內開始計租。
- 財務影響　已起租站點可增加 UScellular 鐵塔租金收入。估算金額仍需各期起租座數、單站租金及計租期間，估算獲利另需維運成本。
- 其他解釋　其他租戶擴租或既有租約調價也可推升鐵塔收入。可用雙方具名確認本協議新增站點開始計租的公告辨別。
- 查核指標　本協議至少部分新增站點是否已開始計租。
- 觀察期間　自交割日至 2025-12-31，以期內已公開的交易更新或定期報告覆核。
- 公開查核來源　UScellular 投資人公告及定期報告，並與 T-Mobile 交割公告或交易進度更新核對。
- 截止日　2025-12-31
- 預測　若期內交割，至少部分新增站點於期限前開始計租，可從具名披露確認租金來源。
- 推翻條件　若已交割，雙方任一方明確披露截至期限，本協議新增站點仍全數未開始計租，即推翻期內租金傳導。僅披露鐵塔總收入則無法判定。

**待查**　公司未說明頻譜、資本預算或人力將轉入哪項其他業務，也未按安排拆分節省額，因此無法建立可覆核的第二條傳導路徑。

### 研究稿 D-99CA6C0F

**1. T-Mobile 收購 UScellular 無線營運業務後的站址租用需求 → UScellular · 交易後保留的鐵塔空間出租業務**

- 起點引文　t-mobile-release:deal、t-mobile-release:towers
- 受影響業務引文　t-mobile-release:original、t-mobile-release:towers
- 傳導機制　T-Mobile 約定於交割後長期租用 UScellular 保留的額外至少 2,100 座鐵塔空間。各站起租後，UScellular 可從 T-Mobile 取得租金收入。
- 比較基準　以交割前 T-Mobile 向 UScellular 租用的鐵塔為比較基準。「額外至少 2,100 座」是新增租用範圍的下限，公告未列原有租用座數或租金。
- 必要條件　交易完成交割，且新增站址在觀察期內開始計租。
- 財務影響　已起租的站址可增加來自 T-Mobile 的租金收入。每站租金、起租時程及相關成本均待確認，無法估算截至期限的收入或獲利增量。
- 其他解釋　其他租戶增租或既有租約調價也可能推升鐵塔收入，須以 T-Mobile 新增站址或租金揭露核對歸因。
- 查核指標　分別追蹤交割後新增約定租用座數、其中已起租座數，以及可歸屬於新增租約的租金收入。
- 觀察期間　自 2024 年 5 月 28 日公告起追蹤交割，交割後追蹤起租情況至 2025 年 12 月 31 日。
- 公開查核來源　兩家公司交割公告、UScellular 定期財報及鐵塔業務說明。
- 截止日　2025-12-31
- 預測　若按公告條款交割，新增長租範圍應涵蓋至少 2,100 座鐵塔。若期內已有站址起租，應可在後續揭露中查核新增租用活動或相關租金收入。
- 推翻條件　若交易終止，或最終條款取消新增租用安排或將規模降至 2,100 座以下，原租用規模假設失效。若截至期限仍未交割或未起租，期內租金貢獻缺乏實現條件。

**待查**　新增長租的交易雙方與座數下限已有揭露，但起租時程、租金及成本尚待確認。T-Mobile 未將整合節省分配至鐵塔安排，無法據此估算該安排對買方的淨效益。

### 研究稿 D-18CE6A59

**1. UScellular Wireless Operations → UScellular · 鐵塔業務**

- 起點引文　t-mobile-release:deal
- 受影響業務引文　t-mobile-release:towers、t-mobile-release:original
- 傳導機制　UScellular 出售無線業務並保留鐵塔。若交割後 T-Mobile 依約起租，T-Mobile 增加租賃負擔，UScellular 的鐵塔業務則取得長期租金來源。
- 比較基準　以簽約前雙方既有租用範圍為基準。無此交易時，原有租約仍可能產生租金，但沒有本案新增租約的貢獻。
- 必要條件　交易交割，且本案新增站點的租賃開始生效。至少 2,100 座是公告的安排，實際起租範圍與時程待確認。
- 財務影響　起租可增加 UScellular 鐵塔租賃收入。缺少單站租金、起租日及履約成本，無法估算期內收入或利潤增幅。
- 其他解釋　其他租戶增租或既有租約調價也能推升鐵塔收入。須由交易更新或財報明指 T-Mobile 本案新增租約已起租，才能辨別來源。
- 查核指標　UScellular 本案保留鐵塔是否已有新增租約起租，屬租金收入的營運代理指標。
- 觀察期間　2024-05-28 簽約公告後至 2025-12-31，以截止日前已公開且載明生效狀態的資料覆核。
- 公開查核來源　T-Mobile 或 UScellular 的交割公告、租約生效公告或交易更新。
- 截止日　2025-12-31
- 預測　截至期限，UScellular 至少部分保留鐵塔已依本案向 T-Mobile 起租。
- 推翻條件　公開資料明確顯示，截至同一期限，UScellular 本案新增鐵塔租約均未起租，例如交易已終止且租約未生效。未更新起租狀態則待核。

**待查**　公告未說明新增租用既有鐵塔可替代哪些 T-Mobile 建設項目，也未分配節省額。判斷租塔能否降低淨支出，仍缺受影響項目的原建設預算、可避免支出與新增租金。

## P-04 · Costco

**研究題目**　Costco 公布 2025 財年第一季業績。請提出可供研究員覆核的繁體中文研究首稿。

**截止**　2024-12-12T23:59:59+00:00　**研究期限**　2025-12-31

- `costco-release:adjusted`　排除油價與匯率影響後，公司調整後可比銷售成長 7.1%，電子商務成長 13.2%。 [官方來源](https://investor.costco.com/news/news-details/2024/Costco-Wholesale-Corporation-Reports-First-Quarter-Fiscal-Year-2025-Operating-Results/default.aspx)
- `costco-release:comps`　可比銷售年增率為美國 5.2%、加拿大 5.8%、Other International 4.7%、全公司 5.2%；另列 E-commerce 13.0%。 [官方來源](https://investor.costco.com/news/news-details/2024/Costco-Wholesale-Corporation-Reports-First-Quarter-Fiscal-Year-2025-Operating-Results/default.aspx)
- `costco-release:footprint`　Costco 營運 897 個倉庫，在美國、加拿大等八個市場設有電子商務網站。 [官方來源](https://investor.costco.com/news/news-details/2024/Costco-Wholesale-Corporation-Reports-First-Quarter-Fiscal-Year-2025-Operating-Results/default.aspx)
- `costco-release:original`　Comparable sales 表和倉庫數段落原文：Costco currently operates 897 warehouses [官方來源](https://investor.costco.com/news/news-details/2024/Costco-Wholesale-Corporation-Reports-First-Quarter-Fiscal-Year-2025-Operating-Results/default.aspx)

### 研究稿 D-83BA6AF7

**待查**　Costco 披露電商與倉庫並行營運，但未揭露線上訂單由哪些倉庫履約、是否排擠店內銷售，或兩個通路之間有何資本與人力調度。電商與全公司增速差無法檢驗這些傳導，需有通路銷售移轉或履約配置的公開資料。

### 研究稿 D-996BF2D6

**待查**　Costco 在八個市場設有電商網站，但公告只提供全公司與電商的可比銷售增速，缺少電商銷售占比、會員跨通路消費及純倉庫通路數據。現階段無法判定電商成長帶來多少新增消費、多少來自通路移轉，也無法將成長歸因於特定交易對手。

### 研究稿 D-323D9AAC

**待查**　Costco 同時經營電商與倉庫，但全公司可比銷售已包含電商，兩者的增速差無法識別倉庫銷售是否移往線上。要檢驗通路排擠，至少需要可比口徑的倉庫銷售及通路移轉資料。現有資料也未具名可追蹤的交易對手。

## H-01 · Corning

**研究題目**　Corning 公布擴大一項製造合作。請提出可供研究員覆核的繁體中文研究首稿。

**截止**　2025-08-06T23:59:59+00:00　**研究期限**　2026-12-31

- `corning-release:commitment`　Apple 宣布新的 25 億美元承諾，與 Corning 合作在肯塔基州 Harrodsburg 工廠生產全球銷售的 iPhone 和 Apple Watch 所有 cover glass。 [官方來源](https://www.apple.com/newsroom/2025/08/apple-corning-to-manufacture-all-iphone-apple-watch-cover-glass-in-kentucky/)
- `corning-release:original`　公告開頭三段，承諾、工廠用途及研發安排原文：Corning will now dedicate this entire facility to manufacturing for Apple [官方來源](https://www.apple.com/newsroom/2025/08/apple-corning-to-manufacture-all-iphone-apple-watch-cover-glass-in-kentucky/)
- `corning-release:other`　雙方將在同廠設立 Apple-Corning Innovation Center，研發先進材料。此案屬 Apple 較大的美國投資計畫，公告未列採購單價、出貨節奏或承諾金額如何拆分。 [官方來源](https://www.apple.com/newsroom/2025/08/apple-corning-to-manufacture-all-iphone-apple-watch-cover-glass-in-kentucky/)
- `corning-release:plant`　Corning 會建立新的智慧手機玻璃生產線，整個 Harrodsburg 工廠專供 Apple，預期 Corning 在肯塔基州的製造及工程人力增加 50%。 [官方來源](https://www.apple.com/newsroom/2025/08/apple-corning-to-manufacture-all-iphone-apple-watch-cover-glass-in-kentucky/)

### 研究稿 D-2680AF68

**1. 智慧手機玻璃生產線 → Corning · Apple-Corning Innovation Center**

- 起點引文　corning-release:plant
- 受影響業務引文　corning-release:other
- 傳導機制　新線與研發中心規劃設於同廠。若雙方將新線的製程問題交由中心驗證，中心便有具體的先進材料研發專案，可強化合作從製造延伸至共同開發的判斷。
- 比較基準　截至 2025-08-06，雙方已宣布設立中心，尚未披露中心承接新線驗證工作。維持原有合作也可能持續一般材料研發。
- 必要條件　雙方須實際指派與新線相關的驗證專案，且 Corning 須投入新增研發人力或設備。
- 財務影響　若 Corning 自付新增研發支出，中心啟動初期將增加現金流出。專案預算、Apple 分攤比例及後續商業化收益均未知。
- 其他解釋　中心也可能執行既有材料研究。須由雙方公開說明專案使用新線試製，或處理該線的具體製程問題，才能區分。
- 查核指標　中心是否已啟動明確連結新線的材料驗證專案。
- 觀察期間　2025-08-06 公告後至 2026-12-31
- 公開查核來源　Apple Newsroom 或 Corning 對 Harrodsburg 新線及中心的專案進度公告。
- 截止日　2026-12-31
- 預測　期內至少一方公開確認中心已開始為新線進行材料驗證，可確認研發連結已運作，金額仍待查。
- 推翻條件　期末公開進度明確指出，中心針對該新線的首項材料驗證仍待啟動，或已取消。

**待查**　同廠設址無法判定製造與研發是否共用工程人力，也無法判定新線是否排擠其他專案。尚缺人力調配、專案時程及資金分攤資料。

### 研究稿 D-FD3E090B

**1. Apple 將全球銷售的 iPhone 與 Apple Watch 所需蓋板玻璃集中至 Harrodsburg 生產。 → Corning · Harrodsburg 工廠的蓋板玻璃製造，尤其是規劃新增的智慧型手機玻璃產線。**

- 起點引文　corning-release:commitment
- 受影響業務引文　corning-release:original、corning-release:plant
- 傳導機制　若 Apple 導入的訂單足以讓新線穩定量產，Corning 可將產線固定成本分攤至更多合格出貨件數。
- 比較基準　截至 2025 年 8 月 6 日，Apple 已公布整廠專供安排。資料未提供擴產前的產量、利用率或單位製造成本。
- 必要條件　新線達到客戶要求的良率，且實際訂單足以吸收新增產能。
- 財務影響　相較於新線投產初期，穩定量產可降低每件合格產品負擔的固定成本。對合併獲利的貢獻仍取決於售價、增量成本與其他廠區的產量變化。
- 其他解釋　Harrodsburg 出貨增加也可能來自既有訂單移轉。若其他廠區因此閒置，單廠效率改善可能伴隨其他廠區固定成本負擔上升。
- 查核指標　新線量產狀態、合格出貨量，以及管理層對利用率或單位成本變化的說明。
- 觀察期間　2025 年 8 月 7 日至 2026 年 12 月 31 日公開的進度，相較於投產初期。
- 公開查核來源　Corning 財報、法說會資料及 Apple 或 Corning 的 Harrodsburg 工廠進度公告。
- 截止日　2026-12-31
- 預測　若上述條件成立，預期截至期限可見新線持續出貨，並有利用率提高或單位成本下降的公開佐證。此期限採用研究觀察期。
- 推翻條件　若公司確認新線延後至觀察期後投產，或已穩定出貨但低良率使單位成本持續高於投產初期，則期間內的成本改善假設失效。缺少成本揭露時，該效果仍待驗證。

**待查**　可辨識 Apple 的採購安排與 Corning 的製造業務，仍缺原有供貨地點、移轉量及新增量。創新中心的研發項目、商業化時程與外部供應商亦待揭露。

### 研究稿 D-DB95A586

**1. cover glass → Apple · iPhone**

- 起點引文　corning-release:commitment、corning-release:plant
- 受影響業務引文　corning-release:commitment、corning-release:original
- 傳導機制　25 億美元承諾與整廠專供安排，讓 Apple 有條件將全球 iPhone 的蓋板玻璃採購集中至 Harrodsburg。若 Apple 實際分配採購量並採用該廠交付的玻璃，便可驗證 Corning 新產能已有下游客戶使用。
- 比較基準　若未擴大合作，沿用原採購配置。公告未揭露原有 Harrodsburg 供應占比。
- 必要條件　Corning 交付合格玻璃，Apple 將實際採購量分配至該廠，並用於商業銷售的 iPhone。
- 財務影響　相較維持原配置，Apple 用於 Harrodsburg 來源玻璃的採購支出可增加，其他來源的支出可能同步減少。缺少 iPhone 分攤金額、數量、單價與付款條款，無法推算總採購成本或現金流變化。
- 其他解釋　原有產線也可能隨 iPhone 銷量增加而提高出貨。Apple 若指明已銷售產品採用新線玻璃，才能辨識此次擴線的貢獻。
- 查核指標　Apple 商售 iPhone 是否已採用 Harrodsburg 新線生產的蓋板玻璃
- 觀察期間　2025-08-06 公告後至 2026-12-31
- 公開查核來源　Apple Newsroom 的美國製造進度或 iPhone 產品更新
- 截止日　2026-12-31
- 預測　截至覆核日，Apple 已有商售 iPhone 採用該新線玻璃，以 Apple 點名新線及實際採用的更新驗證。
- 推翻條件　Apple 明確確認截至同一覆核日，其商售 iPhone 仍全數使用其他產線的玻璃。

**2. 智慧手機玻璃生產線 → Corning · Apple-Corning Innovation Center**

- 起點引文　corning-release:plant
- 受影響業務引文　corning-release:other
- 傳導機制　新線與研發中心設於同廠。若量產爬坡占用原訂投入中心的工程人員，中心啟動先進材料研發的時間可能延後。
- 比較基準　若新線無須抽調研發人力，中心可依雙方原訂時程啟動。公告未列啟動日期。
- 必要條件　兩項計畫實際共用關鍵工程人員，且 Corning 優先將這些人員配置到新線，未能及時補足研發人力。
- 財務影響　若中心已投入設備卻延後使用，研發資產閒置時間將拉長。影響規模取決於已投入金額、延後期間及雙方分攤比例。
- 其他解釋　中心也可能因場地或設備未就緒而延後，須由雙方公開說明人員調度及其對原訂時程的影響。
- 查核指標　中心實際或更新後的研發啟動時程，相對雙方原訂時程是否因新線抽調人員而延後
- 觀察期間　2025-08-06 公告後至 2026-12-31 的建置及啟動進度
- 公開查核來源　Apple Newsroom 或 Corning 對 Harrodsburg 研發中心的公開進度更新
- 截止日　2026-12-31
- 預測　若發生人力排擠，兩家公司至覆核日可確認中心較原訂時程延後，並將延後歸因於新線用人。
- 推翻條件　雙方在同一期間確認中心依原訂時程或提前啟動研發。

**待查**　25 億美元在產品採購、產線與研發中心間的分配仍待揭露。整廠專供也可能影響其他業務，但資料未指明原有非 Apple 產品、客戶或轉廠決定。

## H-02 · HP Inc.

**研究題目**　HP Inc. 在平台發布活動展示新款電腦。請提出可供研究員覆核的繁體中文研究首稿。

**截止**　2024-05-20T23:59:59+00:00　**研究期限**　2025-06-30

- `hp-release:channel`　發表列有 Microsoft.com 與主要製造商及零售商的預購通路，沒有 OEM 層級的實際預購量。 [官方來源](https://blogs.microsoft.com/blog/2024/05/20/introducing-copilot-pcs/)
- `hp-release:hp`　平台公告列出 HP 的兩個 Copilot+ PCs 機型 HP OmniBook X AI PC 和 HP EliteBook Ultra G1q AI PC，使用 Snapdragon X Elite。 [官方來源](https://blogs.microsoft.com/blog/2024/05/20/introducing-copilot-pcs/)
- `hp-release:original`　OEM 合作夥伴列表及 AI innovation across the Windows ecosystem原文：HP’s OmniBook X AI PC and HP EliteBook Ultra G1q AI PC with Snapdragon X Elite [官方來源](https://blogs.microsoft.com/blog/2024/05/20/introducing-copilot-pcs/)
- `hp-release:rival`　同場列出 Lenovo 的 Yoga Slim 7x、ThinkPad T14s Gen 6 與其他 OEM；首批機型採用 Qualcomm Snapdragon X Series 的 X Elite 或 X Plus。 [官方來源](https://blogs.microsoft.com/blog/2024/05/20/introducing-copilot-pcs/)

### 研究稿 D-23BD7F51

**1. HP OmniBook X AI PC 與 HP EliteBook Ultra G1q AI PC → Qualcomm · 用於筆電的 Snapdragon X Elite 處理器**

- 起點引文　hp-release:hp
- 受影響業務引文　hp-release:original、hp-release:rival
- 傳導機制　兩款 HP 筆電均採用 X Elite。若終端銷售帶動 HP 追加生產，且先前備料不足以支應，新增處理器採購可帶動 Qualcomm 營收。
- 比較基準　截至 2024-05-20，公告確認兩款機型採用 X Elite。HP 的初期備料量、實際預購量與晶片採購金額均未知。
- 必要條件　HP 因這兩款機型的終端需求而追加生產，並為此新增 X Elite 採購。
- 財務影響　相對於僅供應首批備貨的情境，Qualcomm 對 HP 的 X Elite 銷售收入可望增加。現有資料無法估計金額或對整體獲利的影響。
- 其他解釋　即使 Qualcomm 的 X 系列銷售成長，也可能來自 Lenovo 等其他製造商，或來自首批備貨。
- 查核指標　可歸屬於這兩款 HP 機型的 X Elite 追加採購量或金額
- 觀察期間　2024-05-21 至 2025-06-30
- 公開查核來源　追蹤 HP 與 Qualcomm 的財報、法說會及產品業務公告，查找明確指向這兩款機型的補單說明。
- 截止日　2025-06-30
- 預測　若上述條件成立，至研究期限可望看到至少一次可歸屬於 HP 這兩款機型的 X Elite 補單跡象。
- 推翻條件　若公司確認初期備料足以支應整段期間的生產，則追加採購假說失效。若僅有 X 系列總銷售數據，則歸因仍待驗證。

**待查**　平台公告可連結 HP 機型與 Qualcomm 處理器，但缺少分機型銷量、處理器採購量及單價，無法估算雙方營收影響。資料也未揭露 HP 其他業務與這兩款電腦的連帶收入。

### 研究稿 D-7CC8183C

**1. HP OmniBook X AI PC → Qualcomm · Qualcomm Snapdragon X Series**

- 起點引文　hp-release:hp
- 受影響業務引文　hp-release:hp、hp-release:rival
- 傳導機制　HP 已公布此機採用 Snapdragon X Elite。若 HP 實際投產並交貨，Qualcomm 的晶片便隨整機進入市場。若 HP 因新增需求而追加採購，才可能進一步增加 Qualcomm 晶片收入。
- 比較基準　以 5 月 20 日已公布搭載、尚無實際交貨證據為觀察起點。若 HP 維持原採購計畫，即使首批電腦交貨，也可能只消化已購晶片。
- 必要條件　HP 須實際交付搭載該晶片的量產機。收入增量另須 HP 將新增採購分配給 Qualcomm，且 Qualcomm 完成交付及收入認列。
- 財務影響　新增晶片銷售可提高 Qualcomm 收入，規模取決於增購顆數、單價及認列期間，三者均未披露。
- 其他解釋　Lenovo 等品牌也採用同系列晶片。Qualcomm 的平台進展可能由其他品牌帶動，須以明列 HP 型號與晶片的交貨公告辨別 HP 是否參與。
- 查核指標　HP OmniBook X AI PC 搭載 Snapdragon X Elite 的實際交貨狀態，僅作晶片商用部署代理。
- 觀察期間　2024-05-20 發表後至 2025-06-30
- 公開查核來源　HP 產品上市或交貨公告，並以 Microsoft 平台產品更新核對型號及晶片。
- 截止日　2025-06-30
- 預測　覆核日前，HP 或平台公告確認搭載 Snapdragon X Elite 的 HP OmniBook X AI PC 已開始交貨。
- 推翻條件　同期 HP 或平台公告明確確認該配置已在交貨前取消，或首次交貨已延至 2025-06-30 之後。僅缺少更新則仍待查。

**待查**　公告只列平台預購入口。要把上架連到 Microsoft 的通路收入，仍缺 HP 指定機型的銷售安排、成交量及分潤條款。也缺 HP 將產能或預算從既有產品移至新機的證據，無法評估其他產品的損益。

### 研究稿 D-95EBFBD1

**待查**　平台公告確認兩款 HP 電腦採用 Snapdragon X Elite。零售頁可覆核整機是否開賣，但要檢驗開賣是否帶動 Qualcomm 新增晶片營收，仍需 HP 追加採購及 Qualcomm 交付的證據。現有資料也未指出 HP 為新品調整了哪一條既有產品線的預算、產能或通路配置。

## H-03 · United Airlines

**研究題目**　United Airlines 公布一項機上服務協議。請提出可供研究員覆核的繁體中文研究首稿。

**截止**　2024-09-13T23:59:59+00:00　**研究期限**　2025-12-31

- `united-release:contract`　United Airlines 與 SpaceX 簽約在主線及區域機隊部署 Starlink Wi-Fi，免費提供旅客，計畫涵蓋逾 1,000 架飛機。預計 2025 年測試及首批飛行。 [官方來源](https://united.mediaroom.com/2024-09-13-The-Inflight-Wi-Fi-Revolution-Now-Arriving-United-Signs-Starlink-Deal-to-Provide-Industry-Leading-Connectivity-in-the-Sky-For-Free)
- `united-release:cost`　公告未列服務、設備或安裝價格，未承諾機上媒體或票價溢價金額。 [官方來源](https://united.mediaroom.com/2024-09-13-The-Inflight-Wi-Fi-Revolution-Now-Arriving-United-Signs-Starlink-Deal-to-Provide-Industry-Leading-Connectivity-in-the-Sky-For-Free)
- `united-release:entertainment`　公告點名機上座椅螢幕與個人裝置的影音串流、直播、購物與遊戲等用途；另提及員工資訊工具及已規劃的客艙升級。 [官方來源](https://united.mediaroom.com/2024-09-13-The-Inflight-Wi-Fi-Revolution-Now-Arriving-United-Signs-Starlink-Deal-to-Provide-Industry-Leading-Connectivity-in-the-Sky-For-Free)
- `united-release:original`　開頭合約範圍、導入與機上娛樂段落原文：Industry's largest agreement includes more than 1,000 aircraft [官方來源](https://united.mediaroom.com/2024-09-13-The-Inflight-Wi-Fi-Revolution-Now-Arriving-United-Signs-Starlink-Deal-to-Provide-Industry-Leading-Connectivity-in-the-Sky-For-Free)

### 研究稿 D-53092048

**1. 主線及區域機隊 → SpaceX · Starlink Wi-Fi**

- 起點引文　united-release:contract、united-release:original
- 受影響業務引文　united-release:contract、united-release:cost
- 傳導機制　United Airlines 已簽約部署，讓 SpaceX 的 Starlink Wi-Fi 取得通往聯航旅客的服務通路。若首架飛機從測試轉為載客營運，便可確認供應商已開始向該通路提供服務。
- 比較基準　截至 2024-09-13，公告確認簽約及逾 1,000 架的計畫範圍，首批飛行仍屬預期。無此協議的基準情境沒有這份合約帶來的服務收入。
- 必要條件　聯航須完成裝機、開通載客服務，且達成合約約定的計費或驗收條件。
- 財務影響　若服務開通觸發計費，SpaceX 可增加服務收入。金額取決於付費架數、單價及服務期間，收入認列時點取決於履約條款。
- 其他解釋　展示機或測試飛行也能證明設備可用。聯航公告若指明一般旅客已可在營運航班使用，才能區別測試與實際供應。是否開始計費仍須合約或財務揭露。
- 查核指標　聯航公開確認已提供 Starlink Wi-Fi 的載客航班，作為 SpaceX 實際提供服務的代理指標。
- 觀察期間　2025 年測試啟動至年底
- 公開查核來源　United Airlines 新聞室的 Starlink 測試及首航更新
- 截止日　2025-12-31
- 預測　截至年底，聯航公開確認 2025 年至少一班載客航班已向旅客開通 Starlink Wi-Fi。
- 推翻條件　聯航截至年底明確確認 2025 年全年開通該服務的載客航班為零。

**待查**　影音串流、直播及購物有具名用途，但缺內容授權、廣告或購物分潤安排及使用量。員工資訊工具與既定客艙升級也缺專案時程、預算或機務工時因本協議而改變的證據。

### 研究稿 D-ADE4E0A4

**1. United 免費機上 Wi-Fi → United Airlines · 機上娛樂與購物服務**

- 起點引文　united-release:contract
- 受影響業務引文　united-release:entertainment
- 傳導機制　旅客若能在座椅螢幕或個人裝置上免費連線，使用影音或購物服務的機會便可能增加。其中，購物使用量能否轉為 United 收入，取決於交易安排。
- 比較基準　截至 2024-09-13，公告已列出串流、直播與購物用途，未提供各項服務原有的使用率或收入。
- 必要條件　United 在 2025 年推出旅客可用的 Starlink 航班，並在機上開放相關服務。
- 財務影響　若購物交易增加且 United 可取得分潤，每旅客附加收入可能提高。分潤條款、交易額及新增連線成本均待確認。
- 其他解釋　同期已規劃的客艙升級也可能提高娛樂使用率。比較時應選取客艙配置及航程相近的航班。
- 查核指標　每百名旅客中使用串流或購物服務的人數，以及每名旅客為 United 帶來的購物分潤。
- 觀察期間　首批載客航班啟用後至 2025 年底，與可比航班同期比較。
- 公開查核來源　United 的服務上線公告、營運更新，以及財報或法說會中對機上服務使用量與收入的說明。
- 截止日　2025-12-31
- 預測　已開放相關功能的航班，其串流或購物使用率高於可比航班。若有交易分潤，預期每旅客購物分潤亦提高。
- 推翻條件　若可比資料顯示兩項服務的使用率均未提高，使用量假說即失去支持。若 United 未取得分潤，購物收入假說即不成立。缺少揭露時，兩者均保留為待驗證。

**2. United 主線及區域機隊的機上連線部署 → SpaceX · Starlink 航空連線服務**

- 起點引文　united-release:contract
- 受影響業務引文　united-release:contract
- 傳導機制　United 將飛機投入載客服務後，Starlink 可增加實際提供航空連線的飛機數。收入何時增加取決於合約的付費條件。
- 比較基準　公告披露的逾 1,000 架為協議規劃範圍，首批飛行預計在 2025 年。公告未列已啟用架數。
- 必要條件　首批飛機完成測試並啟用旅客服務，且達到合約約定的付款條件。
- 財務影響　若服務費隨啟用架數或服務期累計，部署進度將帶動 SpaceX 的航空連線收入。單價、計費方式及毛利均未知。
- 其他解釋　若採固定總價或分階段付款，當期收入可能與啟用架數變動不同步。
- 查核指標　United 已啟用 Starlink 載客服務的飛機數，以及雙方若有披露的服務費和計費起點。
- 觀察期間　2025 年首批測試至 2025 年底。
- 公開查核來源　United 或 SpaceX 對 United 機隊商用啟用及合約條款的公開更新。
- 截止日　2025-12-31
- 預測　依公告時程，至 2025 年底至少一架 United 飛機在載客航班提供 Starlink。若按啟用數收費，後續增加啟用架數將提高服務收入。
- 推翻條件　若雙方確認商用啟用延至 2026 年或以後，2025 年部署預測即落空。若合約採與架數無關的固定收費，按架數推估收入的假設即不適用。

**待查**　可核實的外部交易對手為 SpaceX。公告未點名設備分包商、內容商或購物合作方，也未披露 United 的媒體銷售或交易分潤安排。

### 研究稿 D-C7C1E686

**1. Starlink Wi-Fi → United Airlines · 購物**

- 起點引文　united-release:contract
- 受影響業務引文　united-release:entertainment、united-release:cost
- 傳導機制　公告列出購物用途。若聯航另行決定在已啟用連線的航班開放購物結帳，免費連線就可能成為聯航取得交易收入的通路。
- 比較基準　簽約時僅列出購物用途。若只開通網路，旅客即使自行上網消費，聯航也未必取得收入。
- 必要條件　聯航須推出可完成交易的購物服務，且對成交享有銷售收入或分潤權。
- 財務影響　成交可增加附加收入。可用航班數、成交率、聯航實收金額及營運成本均待查。
- 其他解釋　購物功能也可能隨既定客艙升級推出。應查聯航服務說明是否明列結帳須使用 Starlink 連線，以及哪些航班適用。
- 查核指標　聯航是否公開確認已在 Starlink 客運航班開放其購物服務的機上結帳。此里程碑僅檢驗通路是否啟用。
- 觀察期間　2025 年首批客運服務啟用後至年底
- 公開查核來源　United Airlines 新聞室的機上購物服務公告或對旅客服務說明
- 截止日　2025-12-31
- 預測　若聯航採用此銷售通路，年底前可在至少一班已啟用 Starlink 的客運航班完成聯航購物結帳。
- 推翻條件　聯航明確確認截至年底，所有已啟用 Starlink 的客運航班均未開放聯航購物結帳。若未披露，則保留判斷。

**待查**　購物上線後仍須查交易歸屬與分潤。公告也提及員工資訊工具及既定客艙升級，但缺少工具上線前後的作業指標，以及原定改裝排程與實際資源調度資料。

## H-04 · 3M

**研究題目**　3M 公布完成一項分拆。請提出可供研究員覆核的繁體中文研究首稿。

**截止**　2024-04-01T23:59:59+00:00　**研究期限**　2025-06-30

- `3m-release:capital`　公告說兩家公司可各自採用不同成長與資本配置策略，未就這筆持股未來變現指明金額、日期或用途。 [官方來源](https://investors.3m.com/news-events/press-releases/detail/1835/3m-completes-spin-off-of-solventum)
- `3m-release:holding`　3M 持有 Solventum 流通普通股 19.9%，公告表示將於分拆後五年內變現。 [官方來源](https://investors.3m.com/news-events/press-releases/detail/1835/3m-completes-spin-off-of-solventum)
- `3m-release:original`　公告前三段與持股處置說明原文：will be monetized within five years following the spin-off [官方來源](https://investors.3m.com/news-events/press-releases/detail/1835/3m-completes-spin-off-of-solventum)
- `3m-release:spin`　3M 完成將醫療保健業務分拆為 Solventum；3M 股東每持四股 3M 取得一股 Solventum。 [官方來源](https://investors.3m.com/news-events/press-releases/detail/1835/3m-completes-spin-off-of-solventum)

### 研究稿 D-48BF4E7E

**待查**　公告確認醫療保健業務已分拆，並揭露 3M 的保留持股。要把影響追到另一項具名業務，仍需 3M 揭露變現所得的實際配置、具名業務承接的人員或成本，或雙方供應與服務合約的品項及對價。

### 研究稿 D-B1CD550B

**待查**　公告確認分拆後的持股關係，但未揭露 Solventum 與 3M 其餘事業之間的供貨、採購或服務條款，也未指定持股變現所得將投入哪項業務。現有資料僅足以追蹤 3M 的財務影響。

### 研究稿 D-05FD9B1B

**待查**　公告未指明 3M 哪項業務會取得變現資金，也未揭露 Solventum 與 3M 分拆後的產品供銷關係。要檢驗第二層影響，需有具名業務的資金配置決議與實際支出，或雙方披露的產品合約與交易額。

## H-05 · CVS Health

**研究題目**　CVS Health 公布完成一項醫療服務收購。請提出可供研究員覆核的繁體中文研究首稿。

**截止**　2023-05-02T23:59:59+00:00　**研究期限**　2024-12-31

- `cvs-release:deal`　CVS Health 完成收購 Oak Street Health，交易企業價值約 106 億美元，透過 50 億美元定期貸款及既有現金和資源籌資。 [官方來源](https://www.cvshealth.com/news/company-news/cvs-health-completes-acquisition-of-oak-street-health.html)
- `cvs-release:original`　交割公告開頭與交割後營運安排原文：Oak Street Health will continue to operate as a multi-payor primary care provider [官方來源](https://www.cvshealth.com/news/company-news/cvs-health-completes-acquisition-of-oak-street-health.html)
- `cvs-release:service`　CVS Health 表示交易擴大其 value-based primary care platform，Oak Street Health 將在 CVS Health 旗下繼續作為多保險方的初級照護服務商營運。 [官方來源](https://www.cvshealth.com/news/company-news/cvs-health-completes-acquisition-of-oak-street-health.html)
- `cvs-release:strategy`　CVS Health 說明整合目的為改善照護可及性、成效與成本。交割公告未給中心計費、病患歸戶量或專門導流保證。 [官方來源](https://www.cvshealth.com/news/company-news/cvs-health-completes-acquisition-of-oak-street-health.html)

### 研究稿 D-CFB1B579

**1. Oak Street Health 的多保險方初級照護中心 → CVS Health · 價值導向初級照護業務**

- 起點引文　cvs-release:original、cvs-release:service
- 受影響業務引文　cvs-release:service、cvs-release:strategy
- 傳導機制　若既有中心能以現有人力與設施照護更多歸戶病患，且新增照護收入高於新增成本，每家中心的營業貢獻就可能提高，進而改善 CVS 初級照護業務的獲利。
- 比較基準　交割時已確認 Oak Street 將繼續服務多家保險方。公告未揭露既有中心的歸戶病患數、計費條件或營業貢獻。
- 必要條件　既有中心有餘裕承接病患，保險方合約能將新增服務轉為收入，且相關照護與人力成本增幅低於收入增幅。
- 財務影響　既有中心的營業貢獻增加。對 CVS 合併盈餘的影響仍取決於整合費用及融資成本。
- 其他解釋　初級照護業務總收入也可能因新增中心或併表月數增加而成長，即使既有中心的經濟效益持平。
- 查核指標　追蹤同一批交割時已營運中心的平均歸戶病患數及每家中心營業貢獻。兩者均採相同期間長度與計算口徑。
- 觀察期間　以交割後首個具可比數據的季度為基期，追蹤至 2024 年 12 月 31 日前已公開的最近可比季度。
- 公開查核來源　CVS Health 季報、法說會資料或 Oak Street 營運更新，以有揭露既有中心數據者為準。
- 截止日　2024-12-31
- 預測　若營運條件成立，最近可比季度的每中心歸戶病患數與營業貢獻均高於基期。
- 推翻條件　若歸戶病患數增加，但同批中心的營業貢獻持平或下降，則新增病患改善獲利的預測失效。若僅揭露業務總收入，則此假說仍待驗證。

**待查**　資料未指明個別保險方、合約支付方式或轉介承諾，因此無法將 Oak Street 的業務增減歸因於特定保險方，也無法估算該保險方可保留多少照護成本節省。

### 研究稿 D-D0065AD5

**待查**　公告未點名與 Oak Street Health 有轉介或支付安排的其他 CVS Health 業務或外部保險方。要檢驗跨業務效益，仍需具名業務、交割前比較基準，以及該業務實際轉介、承保或支付成本變化的公開揭露。

### 研究稿 D-BCDCEF5E

**待查**　50 億美元定期貸款是已知金額最大的資金承諾，可檢驗集團利息負擔，但公告未指出哪項其他業務因此調整投資。多保險方安排則保留既有就醫管道，公告未具名其他承保業務、轉介協議或新增病患分配。要建立第二層傳導，仍需具名業務的資本支出調整，或具名保險方的網絡與歸戶變化。

## H-06 · Coca-Cola

**研究題目**　Coca-Cola 公布第三季財報與更新指引。請提出可供研究員覆核的繁體中文研究首稿。

**截止**　2024-10-23T23:59:59+00:00　**研究期限**　2025-12-31

- `coca-cola-release:latam`　Latin America 有機營收年增 24%，價格與組合貢獻 21%，箱量持平。 [官方來源](https://investors.coca-colacompany.com/news-events/press-releases/detail/1121/coca-cola-reports-third-quarter-2024-results-and-provides-updated-guidance)
- `coca-cola-release:na`　North America 有機營收年增 12%，價格與組合貢獻 11%，箱量持平。 [官方來源](https://investors.coca-colacompany.com/news-events/press-releases/detail/1121/coca-cola-reports-third-quarter-2024-results-and-provides-updated-guidance)
- `coca-cola-release:original`　Operating Review，Revenues and Volume，地區列原文：Operating Review – Three Months Ended September 27, 2024 [官方來源](https://investors.coca-colacompany.com/news-events/press-releases/detail/1121/coca-cola-reports-third-quarter-2024-results-and-provides-updated-guidance)
- `coca-cola-release:outlook`　有機營收及報表營收受不同的價格、匯率及組合影響；另列集團全年展望。 [官方來源](https://investors.coca-colacompany.com/news-events/press-releases/detail/1121/coca-cola-reports-third-quarter-2024-results-and-provides-updated-guidance)

### 研究稿 D-914C1CC8

**待查**　財報分列 Latin America 與 North America 的營運數據，但未揭露兩區之間的預算、產能或通路調度，也未具名供應商或客戶。建立第二層假設仍需公司揭露具體調度決策及受影響業務的可追蹤指標。

### 研究稿 D-BAF37073

**待查**　Latin America 與 North America 各自揭露價格與組合及箱量。要建立跨區傳導，仍需公司指出哪項人力、預算或通路資源從一區轉往另一區，並揭露接收業務的部署時點與營運指標。資料亦未具名交易對手或列出採購承諾。

### 研究稿 D-8B7AF50B

**待查**　拉美與北美都呈現箱量持平、價格與組合支撐營收成長的現象，但兩地數據未顯示一地業務如何影響另一地。資料也未具名揭露裝瓶商或通路商的交易條件，無法估算對特定交易對手獲利的影響。

## H-07 · Sony Group

**研究題目**　Sony Group 公布簽署一項新事業協議。請提出可供研究員覆核的繁體中文研究首稿。

**截止**　2022-06-16T23:59:59+00:00　**研究期限**　2025-12-31

- `sony-release:allocation`　擬定合資資本為 100 億日圓，Sony Group 與 Honda Motor Co., Ltd. 各持 50%。預計 2022 年成立、2025 年開始銷售及供應服務，仍需核准。 [官方來源](https://global.honda/en/newsroom/news/2022/c220616eng.html)
- `sony-release:deal`　Sony Group 與 Honda Motor Co., Ltd. 簽署合資協議，擬成立 Sony Honda Mobility Inc.，開發並銷售電動車及移動服務。 [官方來源](https://global.honda/en/newsroom/news/2022/c220616eng.html)
- `sony-release:operations`　擬結合 Sony 的影像、感測、網路及娛樂技術與 Honda 車體製造、車輛開發及售後服務能力。 [官方來源](https://global.honda/en/newsroom/news/2022/c220616eng.html)
- `sony-release:original`　產品與分工段落、New Company Overview原文：Sony Group Corporation 50%, Honda Motor Co., Ltd. 50% [官方來源](https://global.honda/en/newsroom/news/2022/c220616eng.html)

### 研究稿 D-1F00C06F

**1. 電動車及移動服務 → Honda Motor Co., Ltd. · 車體製造**

- 起點引文　sony-release:deal
- 受影響業務引文　sony-release:operations、sony-release:deal
- 傳導機制　協議列出 Honda 的製造能力。若合資公司將量產工作交給 Honda，且 Honda 實際投產，Sony 的電動車計畫便跨過製造關卡，Honda 也取得新增生產活動。
- 比較基準　截至簽約日，僅披露擬結合雙方能力。無此合資案時，Honda 原有車型仍可照常生產。
- 必要條件　合資公司須實際指定 Honda 承製，Honda 並須啟動該合資車款的量產。
- 財務影響　若利用既有閒置產能且製造對價足以覆蓋增量成本，Honda 的製造利益可增加。若須先投入專用設備，則前期現金流承壓。產量、對價及資本支出均未披露。
- 其他解釋　Honda 自有車款也可能帶動工廠增產。須由官方投產公告同時指明合資車款及承製方，才能辨認本案貢獻。
- 查核指標　Honda 是否已為合資車款啟動量產。此里程碑僅代理製造進度，無法衡量獲利或交車量。
- 觀察期間　2022-06-16 簽約後至 2025 年底
- 公開查核來源　Honda Motor Co., Ltd. 新聞室或合資公司成立後的官方投產公告
- 截止日　2025-12-31
- 預測　截至覆核日，官方已確認 Honda 開始量產該合資車款。
- 推翻條件　官方明確確認截至同日 Honda 仍未開始量產該合資車款。若僅缺少公告，結果待查。

**待查**　Sony 提及影像、感測、網路及娛樂技術，但未指定採用的產品、供貨單位或收費方式。須有具名產品的採用及商業條款，才能檢驗對 Sony 其他業務的收益。

### 研究稿 D-301A67C9

**1. Sony 擬透過合資公司開發及銷售電動車與移動服務。 → Sony Group · 影像與感測技術業務**

- 起點引文　sony-release:deal、sony-release:allocation
- 受影響業務引文　sony-release:operations
- 傳導機制　若合資車款採用 Sony 的影像或感測技術，且由 Sony 有償供貨或授權，車款上市可為該業務帶來零組件銷售或授權收入。
- 比較基準　截至 2022 年 6 月 16 日，雙方僅披露擬結合相關技術，供應商、採用項目與計價方式均待確認。
- 必要條件　首款車須進入商業銷售，且 Sony 須取得可辨識的供貨或授權對價。
- 財務影響　有償供應可增加 Sony 相關業務收入。獲利幅度取決於交付量、單位對價及開發成本。
- 其他解釋　Sony 可能以技術投入換取合資事業的長期利益，車款採用其技術也可能沒有單獨支付授權費。
- 查核指標　已開售車款中，獲公開確認採用 Sony 影像或感測技術且由 Sony 有償供應的車款數。
- 觀察期間　2022 年 6 月 17 日至 2025 年 12 月 31 日
- 公開查核來源　Sony 與合資公司的車款規格、供應或授權公告，以及 Sony 財報。
- 截止日　2025-12-31
- 預測　若有償供應路徑成立，預期至少一款已開售車型可對應至 Sony 的供貨或授權安排。
- 推翻條件　若官方確認首款車延至期限後開售，或 Sony 確認相關技術僅作無償投入，則期限內首款車帶動有償供應的假設失效。若僅欠缺條款披露，則維持未驗證。

**待查**　同一份公告列出雙方預計投入的能力，未交代合資公司向母公司採購、授權或支付服務費的條件。研究員須分別驗證技術採用、對價歸屬與合資損益。

### 研究稿 D-EE3EBC6C

**1. 電動車及移動服務 → Honda Motor Co., Ltd. · Sony Honda Mobility Inc.**

- 起點引文　sony-release:deal
- 受影響業務引文　sony-release:deal、sony-release:allocation、sony-release:original
- 傳導機制　合資案若獲核准並按原案出資，Honda 對合資公司的投資資本將增加。Honda 實際出資也是雙方開始承擔本案資本需求的直接證據。
- 比較基準　簽約時合資公司仍待成立。若無此案，Honda 無須為本案投入成立資本。
- 必要條件　雙方完成設立，Honda 按擬定資本額與持股比例實際出資。
- 財務影響　100 億日圓擬定資本乘以 50% 持股，對應 Honda 擬出資 50 億日圓。現金流出取決於繳付方式與時點，投資損益另取決於合資營運。
- 其他解釋　Honda 整體投資支出也會隨其他車輛專案變動。須以點名合資公司的實繳金額辨識本案。
- 查核指標　Honda 對 Sony Honda Mobility Inc. 的成立出資實繳額（日圓）
- 觀察期間　2022-06-16 簽約後至 2025-12-31，追蹤設立及成立出資公告。
- 公開查核來源　Honda 官方新聞室的合資設立或出資完成公告，以及 Honda 已公布的合資投資附註。
- 截止日　2025-12-31
- 預測　若按原案執行，期限內可核實 Honda 成立出資實繳額達 50 億日圓。
- 推翻條件　同期公開文件確認 Honda 最終成立出資實繳額低於 50 億日圓，或確認撤案且實繳為零。僅重述持股比例則仍待核實。

**2. 電動車 → Honda Motor Co., Ltd. · 售後服務**

- 起點引文　sony-release:deal
- 受影響業務引文　sony-release:operations、sony-release:deal
- 傳導機制　若合資公司推出電動車並指定 Honda 承接售後服務，Honda 可取得原本不存在的合資車款服務客源，也能為 Sony 的商業化路徑補上交車後支援。
- 比較基準　簽約時僅提出運用 Honda 售後服務能力。無此案時，Honda 沒有該合資車款的服務客源。
- 必要條件　合資公司須實際選定 Honda，並開放車主使用其服務。服務收入另須有可收費案件或合約給付。
- 財務影響　承接服務可增加 Honda 售後收入機會。缺交車量、服務單價、保固給付條款及據點成本，無法估算利潤。
- 其他解釋　Honda 既有車款也可帶動服務據點擴張。辨識依據是服務公告同時列出合資車款、Honda 承辦角色與啟用範圍。
- 查核指標　合資車款已啟用售後服務的範圍中，是否至少有一個市場由 Honda 承辦
- 觀察期間　2025 年預定開售窗口至 2025-12-31，查閱已公布的車主服務安排。
- 公開查核來源　Honda 官方新聞室及合資公司公開的上市與車主服務說明。
- 截止日　2025-12-31
- 預測　至少一個市場公開啟用由 Honda 承辦的合資車款售後服務。
- 推翻條件　截至期限，公開服務安排確認所有已啟用市場均由其他業者承辦，或官方確認所有市場的售後服務均延至 2026 年以後啟用。

**待查**　Sony 的影像、感測、網路及娛樂技術尚缺具名採用項目、資源移轉、授權價格或分部歸屬。現有資料無法判定哪個既有事業取得增量收入或承擔排擠成本。

## H-08 · Home Depot

**研究題目**　Home Depot 公布第三季財報與更新指引。請提出可供研究員覆核的繁體中文研究首稿。

**截止**　2024-11-12T23:59:59+00:00　**研究期限**　2025-10-31

- `home-release:baseline`　公告並列收購併表和可比銷售口徑，並未給收購前後的同一客戶名冊、商店交易或銷售渠道遷移。 [官方來源](https://ir.homedepot.com/news-releases/2024/11-12-2024-110156861)
- `home-release:guidance`　全年銷售預計增約 4%（含第 53 週及 SRS Distribution），含 SRS 約 64 億美元的當年增量銷售；可比銷售預計降約 2.5%。 [官方來源](https://ir.homedepot.com/news-releases/2024/11-12-2024-110156861)
- `home-release:original`　財報開頭及 fiscal 2024 guidance 條列原文：Comparable sales for the third quarter of fiscal 2024 decreased 1.3% [官方來源](https://ir.homedepot.com/news-releases/2024/11-12-2024-110156861)
- `home-release:quarter`　Home Depot 第三季銷售年增 6.6%，可比銷售年減 1.3%，美國可比銷售年減 1.2%。 [官方來源](https://ir.homedepot.com/news-releases/2024/11-12-2024-110156861)

### 研究稿 D-44F9B45B

**待查**　SRS Distribution 併表會改變集團營收口徑，但公告未揭露原有門市客戶是否轉向 SRS、是否透過 SRS 增購，或兩者是否各自服務不同需求。要檢驗通路移轉或交叉銷售，需有收購前後同一批客戶的分通路銷售及毛利，或公司公開量化兩者的影響。總銷售與可比銷售的差距無法區分這些情境。

### 研究稿 D-3CEB468A

**待查**　公告列出 SRS 的併表貢獻與 Home Depot 的可比銷售，但缺少收購前後同一批客戶在兩個通路的交易資料。即使 SRS 銷售增加、門市可比銷售下降，也無法據此判定 SRS 分流門市訂單，或為門市帶來交叉銷售。

### 研究稿 D-31EBB6A8

**待查**　SRS Distribution 併表與 Home Depot 可比銷售下滑同時出現，兩者的落差無法識別客戶是否轉移採購。要檢驗通路排擠，需公司揭露原有客戶轉向 SRS 的銷售額及原通路銷售變化，或取得非公開的跨通路配對交易紀錄。現有資料也未具名可追蹤的外部供應商或客戶。

# 主要財務傳導排序 · 完整逐案 QA

此份紀錄含評分與組別。匿名人工覆核使用獨立 PDF。模型收取的完整輸入與回傳可在各案連結下載。

## P-01 · Cisco · 先導

**研究題目**　Cisco 公布完成一項收購。請提出可供研究員覆核的繁體中文研究首稿。

**截止**　2024-03-18T23:59:59+00:00　**研究期限**　2025-12-31

- `cisco-release:deal`　Cisco 完成收購 Splunk，每股現金 157 美元，總股權價值約 280 億美元。 [官方來源](https://newsroom.cisco.com/c/r/newsroom/en/us/a/y2024/m03/cisco-completes-acquisition-of-splunk.html)
- `cisco-release:forecasts`　公司預期收購在 FY2025 對現金流有正貢獻（扣除若干收購相關及其他項目）並提高非 GAAP 毛利率，FY2026 提高非 GAAP EPS。未披露組合產品的客戶轉換、價格或營收。 [官方來源](https://newsroom.cisco.com/c/r/newsroom/en/us/a/y2024/m03/cisco-completes-acquisition-of-splunk.html)
- `cisco-release:operations`　公告把 Splunk 的資料能力與 Cisco Security 及 Observability 放在同一平台策略中，目標是改善威脅辨識及應用可視性。 [官方來源](https://newsroom.cisco.com/c/r/newsroom/en/us/a/y2024/m03/cisco-completes-acquisition-of-splunk.html)
- `cisco-release:original`　公告開頭及財務展望段落原文：non-GAAP gross margin accretive in Cisco’s fiscal year 2025 [官方來源](https://newsroom.cisco.com/c/r/newsroom/en/us/a/y2024/m03/cisco-completes-acquisition-of-splunk.html)

**預註冊標準**　主要路徑是 Splunk 資料能力經具名技術整合或銷售搭售，影響 Cisco 的 Security／Observability 產品用量、訂閱收入或毛利。產品採用、具名整合部署或聯合銷售指標需能區別單純將 Splunk 業績併表；交易價格或整體財務預期不能當成單一產品貢獻。

### 新版 Harness V11 · 完成

[逐次回傳](raw/calls/P-01-ranked.json) · [CLI 事件](raw/jobs/P-01-ranked/events.jsonl) · [模型原始 JSON](raw/jobs/P-01-ranked/answer.json) · [CLI 診斷](raw/jobs/P-01-ranked/stderr.log) · [完整請求](raw/jobs/P-01-ranked/request.json)

**研究首稿 · 多方**

- 傳導機制　2024-03-18 交割使 Splunk 納入 Cisco。若 FY2025 已認列的 Splunk 業務毛利率高於未收購時的 Cisco 業務，合併組合即可推升非 GAAP 毛利率，無須先假定交叉銷售成功。公司已給出增厚方向，未披露兩者的毛利率差及營收權重。
- 標的　Cisco
- 研究期限　2025-12-31
- 催化劑　交割後首個完整財年 FY2025 結束，於 2025-12-31 前覆核 Cisco 全年業績公告及法說資料。
- 預測　若 Cisco 披露收購影響，FY2025 全年非 GAAP 毛利率相對同年度未收購口徑的貢獻應為正。合併毛利率可先行觀察，但其年增減也包含原有業務的價格及組合變化。
- 推翻條件　Cisco 披露 FY2025 全年收購對非 GAAP 毛利率相對同年度未收購口徑的貢獻為零或負。若只公布合併毛利率，歸因仍待查。
- 模型引文　fact:cisco-release:deal、fact:cisco-release:forecasts、fact:cisco-release:original

**研究首稿 · 空方**

- 傳導機制　交割後推動共同平台，可能使 Cisco 在客戶付費擴充前，先承擔資料處理、支援及並行維運的經常性現金支出。若這些未被調整剔除的支出吃掉併入業務帶來的現金，FY2025 現金流增益可能落空，即使產品組合已提高毛利率。成本與收款差額尚未披露。
- 標的　Cisco
- 研究期限　2025-12-31
- 催化劑　FY2025 共同平台投入與收款進入全年結果，於 2025-12-31 前查 Cisco 全年業績及法說對交割時現金流指引的回顧。
- 預測　按原指引扣除若干收購相關及其他項目後，收購對 Cisco FY2025 全年現金流相對同年度未收購情境的貢獻為零或負。需查公司有否說明經常性維運支出與收款的影響。
- 推翻條件　Cisco 確認按原指引調整口徑，收購對 FY2025 全年現金流相對同年度未收購情境的貢獻為正。合併現金流的年增減或公司未回顧指引，均無法判定該項貢獻。
- 模型引文　fact:cisco-release:deal、fact:cisco-release:operations、fact:cisco-release:forecasts

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

- 第 1 條排序理由　公告同時指名資料來源及受影響業務，產品文件可檢驗整合是否落地，但財務規模仍取決於付費採用。

**模型判讀**　全對。缺口將交易對價與業務預算分開，並指出資源、通路承諾和客戶採購仍缺乏證據。

主要傳導位置　1。全項通過位置　1。

- 候選 1　四項語義均通過。公告支持 Splunk 資料接入 Cisco Observability 的策略方向。正式部署與客戶付費擴充是增收條件，增量毛利仍取決於用量、價格與成本。Cisco 在同一覆核期內公開確認具名功能正式可用，或確認相關功能全數仍在預覽、延後或取消，可檢驗技術整合並區分一般產品更新。財務貢獻仍需付費資料。

### 現版 Harness V10 · 完成

[逐次回傳](raw/calls/P-01-current.json) · [CLI 事件](raw/jobs/P-01-current/events.jsonl) · [模型原始 JSON](raw/jobs/P-01-current/answer.json) · [CLI 診斷](raw/jobs/P-01-current/stderr.log) · [完整請求](raw/jobs/P-01-current/request.json)

**研究首稿 · 多方**

- 傳導機制　交割使 Splunk 業務納入 Cisco。若其 FY2025 收入的非 GAAP 毛利率高於 Cisco 未收購時的水準，收入組合改變即可拉高合併毛利率，無須先假設組合產品取得訂單。缺少可比毛利率與收入權重，無法估算增厚幅度。
- 標的　Cisco
- 研究期限　2025-12-31
- 催化劑　2024-03-18 完成交割。Cisco 同日預期收購將增厚 FY2025 非 GAAP 毛利率，可於 FY2025 全年業績發布後核對。
- 預測　截至 2025-12-31，若 Cisco 全年業績資料或法說明確量化或定性說明收購影響，預期 FY2025 合併非 GAAP 毛利率高於同年度未收購基準。
- 推翻條件　Cisco 在相同覆核期限內明示，收購對 FY2025 非 GAAP 毛利率的影響為零或負值。僅見合併毛利率年增或年減，均無法判定收購貢獻。
- 模型引文　fact:cisco-release:deal、fact:cisco-release:forecasts、fact:cisco-release:original

**研究首稿 · 空方**

- 傳導機制　相較未收購情境，整合 Splunk 資料與 Cisco 平台可能增加持續性的工程與支援現金支出。若這些支出計入公司指引口徑，且超過併入業務帶來的增量現金，FY2025 現金流貢獻可能落空，即使毛利率受惠。支出金額及排除項目明細待查。
- 標的　Cisco
- 研究期限　2025-12-31
- 催化劑　交割後的平台整合進入執行期。FY2025 全年業績及法說是覆核公司交割日現金流指引的窗口。
- 預測　截至 2025-12-31，若 Cisco 披露 FY2025 收購現金流貢獻，預期依原指引扣除指定項目後，相對同年度未收購基準的貢獻為零或負值。整合支出是否為原因，另需管理層說明。
- 推翻條件　Cisco 在相同覆核期限內確認，依原指引口徑計算的 FY2025 收購現金流貢獻為正。合併現金流變化或未更新指引，皆不足以判定。
- 模型引文　fact:cisco-release:deal、fact:cisco-release:operations、fact:cisco-release:forecasts

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

**模型判讀**　未全對。缺口明確保留資源排擠的歸因，也指出上市里程碑無法驗證付費採用或回收期。

主要傳導位置　未選入。全項通過位置　無。

- 候選 1　四項語義均通過。公告支持雙方的整合方向。此路徑檢驗 Splunk 資料接入或驗證是否延後 Cisco Observability 上市，使支出早於收款並可能壓低增量現金流，規模未知。Cisco 同期間的原訂時程、上市結果與修訂理由可區分整合延誤和原定分階段推出。所衡量的是現金流時點，未涵蓋標準指定的產品用量、訂閱收入或毛利。

### 純 Astra · 完成

[逐次回傳](raw/calls/P-01-astra.json) · [CLI 事件](raw/jobs/P-01-astra/events.jsonl) · [模型原始 JSON](raw/jobs/P-01-astra/answer.json) · [CLI 診斷](raw/jobs/P-01-astra/stderr.log) · [完整請求](raw/jobs/P-01-astra/request.json)

**研究首稿 · 多方**

- 傳導機制　Splunk 併入後，若其帶入的毛利相對營收足夠高，交易即可提高 Cisco 的非 GAAP 毛利率。這項效果可在交叉銷售產生前出現。
- 標的　Cisco FY2025 非 GAAP 毛利率
- 研究期限　FY2025 全年，覆核截至 2025 年 12 月 31 日的公開資料。
- 催化劑　Cisco 公布 FY2025 全年業績並說明 Splunk 對毛利率的影響。
- 預測　以相同非 GAAP 調整口徑比較，含 Splunk 的 FY2025 毛利率高於排除交易影響的同期估計值。
- 推翻條件　若 Cisco 揭露交易對 FY2025 非 GAAP 毛利率的貢獻為零或負值，則假設失效。單看合併毛利率年增或年減，均無法判定交易貢獻。
- 模型引文　cisco-release:forecasts、cisco-release:original

**研究首稿 · 觀望**

- 傳導機制　管理層預期交易在 FY2025 對現金流有正貢獻，但計算時扣除若干收購相關及其他項目。排除項目的實際現金支出會影響股東在當期看到的現金效果。
- 標的　Cisco FY2025 可歸屬於收購的現金流貢獻
- 研究期限　FY2025 全年，覆核期限為 2025 年 12 月 31 日。
- 催化劑　Cisco 揭露交易的現金流貢獻、排除項目及相應的現金支出。
- 預測　依管理層預測口徑，FY2025 的交易現金流貢獻應為正。計入排除項目後的金額與正負方向仍待核對。
- 推翻條件　若同口徑交易貢獻為零或負值，即推翻正貢獻預測。若只公布集團現金流，則維持觀望。
- 模型引文　cisco-release:forecasts

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

**模型判讀**　全對。缺口指出 Observability 仍需採用、付費轉換或可歸屬營收資料。

主要傳導位置　1。全項通過位置　1。

- 候選 1　四項語義均通過。公告支持 Splunk 資料用於 Cisco Security 威脅辨識的策略方向。路徑以可收費功能和續約淨加購為條件，合理指向 Security 營收上升，金額仍未知。同期間 Cisco 公開的可比續約資料若顯示折讓與替代授權完全抵銷加購，即可否證該批次的淨增收，並區分單純併表。

[逐次回傳](raw/calls/P-01-judge.json) · [CLI 事件](raw/jobs/P-01-judge/events.jsonl) · [模型原始 JSON](raw/jobs/P-01-judge/answer.json) · [CLI 診斷](raw/jobs/P-01-judge/stderr.log) · [完整請求](raw/jobs/P-01-judge/request.json)

## P-02 · Procter & Gamble · 先導

**研究題目**　Procter & Gamble 公布 2025 財年第一季結果。請提出可供研究員覆核的繁體中文研究首稿。

**截止**　2024-10-18T23:59:59+00:00　**研究期限**　2025-10-31

- `procter-release:beauty`　Beauty 有機銷售年減 2%。公司指出 Hair Care 及 Personal Care 成長，Skin Care 衰退。 [官方來源](https://d18rn0p25nwr6d.cloudfront.net/CIK-0000080424/59da93f7-916a-4c2f-b94c-60180850c7ac.html)
- `procter-release:grooming`　Grooming 有機銷售年增 3%，有機銷量年增 5%；銷售表另列外匯、價格和組合。 [官方來源](https://d18rn0p25nwr6d.cloudfront.net/CIK-0000080424/59da93f7-916a-4c2f-b94c-60180850c7ac.html)
- `procter-release:original`　Exhibit 99.1，Net Sales Drivers，Beauty 及 Grooming 列原文：Beauty segment organic sales decreased two percent versus year ago. [官方來源](https://d18rn0p25nwr6d.cloudfront.net/CIK-0000080424/59da93f7-916a-4c2f-b94c-60180850c7ac.html)
- `procter-release:outlook`　維持 FY2025 稀釋後 EPS 年增 10% 至 12% 指引。 [官方來源](https://d18rn0p25nwr6d.cloudfront.net/CIK-0000080424/59da93f7-916a-4c2f-b94c-60180850c7ac.html)

**預註冊標準**　Beauty 下滑與 Grooming 成長不能推出預算、人力、貨架或顧客移轉。需指出缺少共同配置決策、通路或顧客流向資料；接受有條件查核與清楚保留歸因。

### 新版 Harness V11 · 完成

[逐次回傳](raw/calls/P-02-ranked.json) · [CLI 事件](raw/jobs/P-02-ranked/events.jsonl) · [模型原始 JSON](raw/jobs/P-02-ranked/answer.json) · [CLI 診斷](raw/jobs/P-02-ranked/stderr.log) · [完整請求](raw/jobs/P-02-ranked/request.json)

**研究首稿 · 多方**

- 傳導機制　首季 Grooming 有機銷量年增 5%、有機銷售年增 3%。若新增銷量延續，且價格與組合未抵銷其貢獻，相較於銷量持平，Grooming 將持續拉動公司有機銷售。新增銷量的單位貢獻與部門權重未知，獲利增量待估。
- 標的　Procter & Gamble
- 研究期限　2025-10-31
- 催化劑　2024-10-18 首季公告揭露量增動能。於公司下一份 FY2025 第二季業績公告覆核該季 Grooming 銷售拆解表，研究截止日為 2025-10-31。
- 預測　FY2025 第二季 Grooming 有機銷量與有機銷售均較上年同期成長，顯示量增仍伴隨部門銷售成長。
- 推翻條件　若公司披露 FY2025 第二季 Grooming 有機銷量或有機銷售任一項較上年同期持平或下降，則該季量增帶動銷售成長的預測不成立。
- 模型引文　fact:procter-release:grooming

**研究首稿 · 空方**

- 傳導機制　首季 Hair Care 與 Personal Care 成長，但 Skin Care 衰退，Beauty 有機銷售仍年減 2%。若 Skin Care 跌勢延續且足以抵銷其他品類成長，相較於 Skin Care 銷售持平，Beauty 對公司有機銷售的拖累將延續。缺少品類銷售權重與毛利率，無法量化 EPS 影響。
- 標的　Procter & Gamble
- 研究期限　2025-10-31
- 催化劑　2024-10-18 首季公告揭露 Beauty 品類走勢分歧。於公司下一份 FY2025 第二季業績公告比對品類評論與部門有機銷售，研究截止日為 2025-10-31。
- 預測　FY2025 第二季 Skin Care 銷售較上年同期下降，Hair Care 與 Personal Care 仍成長，而 Beauty 有機銷售仍年減。
- 推翻條件　若公司披露 FY2025 第二季 Skin Care 銷售或 Beauty 有機銷售較上年同期持平或成長，或 Hair Care、Personal Care 任一品類持平或衰退，則預測的品類組合未重現。若只披露部門年減，品類歸因仍待查。
- 模型引文　fact:procter-release:beauty、fact:procter-release:original

**待查**　同份季報揭露了各品類表現，但未指出 Skin Care 走弱後，公司曾將行銷預算或貨架空間轉給 Hair Care、Personal Care 或 Grooming。要檢驗跨品類影響，需有具名資源移轉或通路配置紀錄、實施期間，以及受影響品類的銷售變化。資料也未揭露具名交易對手或支出承諾。

**模型判讀**　全對。明確保留 Skin Care 走弱後資源是否轉往 Grooming 的歸因，並指出須查核配置紀錄、實施期間與受影響品類的銷售變化。


### 現版 Harness V10 · 完成

[逐次回傳](raw/calls/P-02-current.json) · [CLI 事件](raw/jobs/P-02-current/events.jsonl) · [模型原始 JSON](raw/jobs/P-02-current/answer.json) · [CLI 診斷](raw/jobs/P-02-current/stderr.log) · [完整請求](raw/jobs/P-02-current/request.json)

**研究首稿 · 多方**

- 傳導機制　FY2025 第一季 Grooming 有機銷量年增 5%，有機銷售年增 3%。季報揭示的營運變化是銷量擴張。相較於銷量持平，若增量延續，且價格與組合未抵銷其貢獻，Grooming 可繼續帶動公司有機銷售。增量產品的毛利未揭露，獲利貢獻仍待量化。
- 標的　Procter & Gamble
- 研究期限　2025-10-31
- 催化劑　2024-10-18 公布第一季實績後，於公司發布 FY2025 第二季業績時核對 Grooming 銷售分解表，最遲於 2025-10-31 覆核。
- 預測　FY2025 第二季 Grooming 有機銷量與有機銷售均較上年同期成長，顯示銷量擴張持續且反映在部門銷售。
- 推翻條件　公司揭露 FY2025 第二季 Grooming 有機銷量或有機銷售至少一項較上年同期持平或下滑。
- 模型引文　fact:procter-release:grooming

**研究首稿 · 空方**

- 傳導機制　FY2025 第一季 Skin Care 衰退，Hair Care 與 Personal Care 雖成長，Beauty 有機銷售仍年減 2%。相較於 Skin Care 止跌，若其銷售持續收縮且其他品類增量不足，Beauty 將繼續拖累公司有機銷售。各品類權重與利潤率未揭露，無法換算 EPS 影響。
- 標的　Procter & Gamble
- 研究期限　2025-10-31
- 催化劑　2024-10-18 公布第一季品類表現後，於公司發布 FY2025 第二季業績時，比對 Beauty 部門有機銷售與 Skin Care 品類說明，最遲於 2025-10-31 覆核。
- 預測　FY2025 第二季 Beauty 有機銷售較上年同期下滑，且公司說明 Skin Care 同期銷售仍衰退。部門數字可檢驗銷售壓力，品類說明可檢驗壓力來源。
- 推翻條件　公司揭露 FY2025 第二季 Beauty 有機銷售較上年同期持平或成長，或明示 Skin Care 同期銷售持平或成長。若僅揭露 Beauty 下滑，Skin Care 歸因仍待查。
- 模型引文　fact:procter-release:beauty、fact:procter-release:original

**待查**　Hair Care、Personal Care 與 Skin Care 的成長方向分歧，但公司未揭露三者之間的通路陳列、促銷預算或產能移轉。要檢驗跨品類影響，需有公司指明資源從哪個品類移往哪個品類，並能追蹤受影響品類同期的銷量或銷售變化。

**模型判讀**　未全對。指出 Beauty 內部品類之間缺少資源移轉證據，但未處理 Beauty 下滑與 Grooming 成長之間的歸因。


### 純 Astra · 完成

[逐次回傳](raw/calls/P-02-astra.json) · [CLI 事件](raw/jobs/P-02-astra/events.jsonl) · [模型原始 JSON](raw/jobs/P-02-astra/answer.json) · [CLI 診斷](raw/jobs/P-02-astra/stderr.log) · [完整請求](raw/jobs/P-02-astra/request.json)

**研究首稿 · 空方**

- 傳導機制　Beauty 第一季有機銷售年減 2%。Hair Care 與 Personal Care 均成長，Skin Care 是公司點名衰退的品類。如果 Skin Care 的拖累持續，其他兩個品類的成長可能仍不足以讓部門恢復成長。
- 標的　Procter & Gamble 的 Beauty 部門
- 研究期限　FY2025 第二季
- 催化劑　第二季財報揭露 Beauty 有機銷售年增率與 Skin Care 表現。
- 預測　第二季 Beauty 有機銷售仍較上年同期下滑，且公司仍指出 Skin Care 銷售衰退。
- 推翻條件　若第二季 Beauty 有機銷售持平或成長，則部門預測失效。若 Skin Care 已恢復成長而 Beauty 仍下滑，則須重新判定拖累來源。
- 模型引文　procter-release:beauty

**研究首稿 · 多方**

- 傳導機制　Grooming 第一季有機銷量年增 5%，帶動有機銷售年增 3%。若銷量延續成長，且價格與組合的合計影響未抵銷銷量貢獻，部門有機銷售可望續增。
- 標的　Procter & Gamble 的 Grooming 部門
- 研究期限　FY2025 第二季
- 催化劑　第二季財報更新 Grooming 的有機銷量、價格、組合及有機銷售。
- 預測　第二季 Grooming 有機銷量與有機銷售均較上年同期成長。
- 推翻條件　有機銷量持平或下滑，即推翻銷量續增的假設。若銷量增加而有機銷售持平或下滑，則銷量對銷售的支撐弱於預期。
- 模型引文　procter-release:grooming

**研究首稿 · 觀望**

- 傳導機制　公司維持 FY2025 稀釋後每股盈餘年增 10% 至 12% 的指引。現有資料只有部分業務的銷售表現，缺少從部門銷售、利潤到集團每股盈餘的調節，因此暫以公司指引為待驗證的基準情境。
- 標的　Procter & Gamble 集團 FY2025 稀釋後每股盈餘
- 研究期限　FY2025 全年，最遲於 2025-10-31 覆核
- 催化劑　後續季度的全年指引更新，以及 FY2025 全年實績。
- 預測　基準情境為 FY2025 全年稀釋後每股盈餘較 FY2024 成長 10% 至 12%。
- 推翻條件　若公司調整指引，應即更新基準情境。全年稀釋後每股盈餘實際年增率落在原區間之外，即推翻原預測。
- 模型引文　procter-release:outlook

**待查**　公司揭露了 Skin Care、Hair Care 與 Personal Care 各自的成長方向，但缺少品類權重與銷售貢獻，無法量化三者對 Beauty 的影響。資料也未揭露 Beauty 與 Grooming 之間的客戶移轉、通路連動或成本分攤，兩個部門的成長差異不足以建立跨業務因果關係。

**模型判讀**　全對。指出缺少 Beauty 與 Grooming 之間的顧客流向及通路連動資料，明確保留跨部門因果歸因。


[逐次回傳](raw/calls/P-02-judge.json) · [CLI 事件](raw/jobs/P-02-judge/events.jsonl) · [模型原始 JSON](raw/jobs/P-02-judge/answer.json) · [CLI 診斷](raw/jobs/P-02-judge/stderr.log) · [完整請求](raw/jobs/P-02-judge/request.json)

## P-03 · T-Mobile · 先導

**研究題目**　T-Mobile 公布一項無線業務收購協議。請提出可供研究員覆核的繁體中文研究首稿。

**截止**　2024-05-28T23:59:59+00:00　**研究期限**　2025-12-31

- `t-mobile-release:deal`　T-Mobile 同意以約 44 億美元（含至多 20 億美元承接債務）收購 UScellular Wireless Operations，包括客戶與特定頻譜。交易須滿足交割條件。 [官方來源](https://www.t-mobile.com/news/business/uscellular-acquisition-operations-assets)
- `t-mobile-release:original`　交易範圍、租賃及成本協同段落原文：lease space on at least 2,100 additional towers being retained [官方來源](https://www.t-mobile.com/news/business/uscellular-acquisition-operations-assets)
- `t-mobile-release:other`　T-Mobile 預期整合後每年約 10 億美元的合計營運支出及資本支出節省，整合成本估 22 至 26 億美元；公司未將成本節省分配至各項安排。 [官方來源](https://www.t-mobile.com/news/business/uscellular-acquisition-operations-assets)
- `t-mobile-release:towers`　UScellular 保留鐵塔業務及其他頻譜；交割後 T-Mobile 長期租用其額外至少 2,100 座鐵塔空間。 [官方來源](https://www.t-mobile.com/news/business/uscellular-acquisition-operations-assets)

**預註冊標準**　主要路徑是交易交割觸發至少 2,100 座增量站點租約，增加 UScellular 的鐵塔出租現金流或 T-Mobile 的塔租承諾，不能等同淨網路成本必然上升。以交割時的租約、增量站點及租賃或鐵塔報告區分純收購客戶或原租約續租，列出租率／上線節奏等缺項。

### 新版 Harness V11 · 完成

[逐次回傳](raw/calls/P-03-ranked.json) · [CLI 事件](raw/jobs/P-03-ranked/events.jsonl) · [模型原始 JSON](raw/jobs/P-03-ranked/answer.json) · [CLI 診斷](raw/jobs/P-03-ranked/stderr.log) · [完整請求](raw/jobs/P-03-ranked/request.json)

**研究首稿 · 多方**

- 傳導機制　若完成收購，T-Mobile 可直接承接 UScellular 的無線客戶及特定頻譜。相較未交易情境，承接的客戶可擴大後續服務收入基礎。實際增益取決於留存客戶數、服務期間及每戶收入。
- 標的　T-Mobile
- 研究期限　2025-12-31
- 催化劑　2024-05-28 簽約後，觀察交割條件是否滿足，以及 T-Mobile 是否在研究期限內公告已接手客戶營運。
- 預測　截至 2025-12-31，T-Mobile 的交割公告或定期報告確認已承接協議涵蓋的無線客戶營運。這是營運範圍擴大的里程碑，收入須隨後續服務提供而認列。
- 推翻條件　T-Mobile 明確公告協議終止，或確認截至 2025-12-31 仍未承接該批客戶營運。欠缺交割更新時，結果待查。
- 模型引文　fact:t-mobile-release:deal

**研究首稿 · 空方**

- 傳導機制　交割後，T-Mobile 須向 UScellular 長租額外鐵塔空間。相較未交易情境，站點起租會增加租金負擔。若相關網路節省較晚實現，初期現金效益會受壓。租金、付款時程及對應節省額均未披露。
- 標的　T-Mobile
- 研究期限　2025-12-31
- 催化劑　以交割後新增站點開始計租為催化點，至 2025-12-31 核對雙方已公布的交割文件、交易更新及定期報告。
- 預測　若期內完成交割，至少部分新增站點在期限前開始計租，使 T-Mobile 承擔本協議新增的租金。此里程碑可驗證成本開始發生，淨現金影響仍須比對實際租金付款與同期節省額。
- 推翻條件　若已交割，T-Mobile 或 UScellular 明確確認截至 2025-12-31，本協議新增站點仍全數未開始計租。未交割表示前提未成立，未披露起租進度則仍待驗證。
- 模型引文　fact:t-mobile-release:towers、fact:t-mobile-release:original、fact:t-mobile-release:other

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

- 第 1 條排序理由　這項具名長租承諾有明確的最低站數，起租可同時驗證賣方的收入來源與買方的成本負擔。

**模型判讀**　全對。缺口保留第二條路徑待證，主要路徑也列明估算租金所需的起租座數、單站租金及計租期間。

主要傳導位置　1。全項通過位置　1。

- 候選 1　四項語義均通過。公告支持交割後 T-Mobile 新增租用 UScellular 保留的至少 2,100 座鐵塔。開始計租才增加賣方塔租收入，買方承擔相應租金。若交割後雙方任一方明確披露期末全數未計租，即可推翻期內傳導，並排除以鐵塔總收入變動歸因。

### 現版 Harness V10 · 完成

[逐次回傳](raw/calls/P-03-current.json) · [CLI 事件](raw/jobs/P-03-current/events.jsonl) · [模型原始 JSON](raw/jobs/P-03-current/answer.json) · [CLI 診斷](raw/jobs/P-03-current/stderr.log) · [完整請求](raw/jobs/P-03-current/request.json)

**研究首稿 · 多方**

- 傳導機制　若收購交割並移轉客戶，T-Mobile 可直接擴大提供無線服務的客戶基礎。相較未交易情境，留存客戶的後續服務費可帶來增量收入。移轉人數、留存率及服務收入均未揭露。
- 標的　T-Mobile
- 研究期限　2025-12-31
- 催化劑　2024-05-28 簽約後，追蹤交割條件達成及客戶業務移轉，以 T-Mobile 公開的交割公告或交易更新覆核。
- 預測　從簽約至 2025-12-31，T-Mobile 完成本案至少部分客戶業務承接，相對於簽約時本案已承接客戶為零。公告確認客戶移轉即可驗證營運機制，實際服務收入仍須另查。
- 推翻條件　T-Mobile 公開確認截至 2025-12-31 本案承接客戶仍為零，例如協議終止且客戶未移轉。若只有簽約公告，結果待核。
- 模型引文　fact:t-mobile-release:deal

**研究首稿 · 空方**

- 傳導機制　若交割觸發保留鐵塔的新增長租，T-Mobile 將比未交易時多承擔站點租金，降低其他條件相同時的營運現金流。即使順利承接客戶，租金仍可能先於整合節省發生。缺租率、付款時程及可避免的網路成本，無法判斷淨影響。
- 標的　T-Mobile
- 研究期限　2025-12-31
- 催化劑　交割後查 T-Mobile 或 UScellular 的交易更新，核對 2024-05-28 公告所列額外至少 2,100 座鐵塔之中，是否已有站點開始計租。
- 預測　從簽約至 2025-12-31，T-Mobile 至少有部分本案新增鐵塔開始計租，高於簽約時本案已起租站點為零的基準。起租可驗證成本來源，尚不足以量化租金或確認付款。
- 推翻條件　任一方公開確認截至 2025-12-31，T-Mobile 本案新增站點開始計租數仍為零。若只重述長租安排而未交代生效情況，結果待核。
- 模型引文　fact:t-mobile-release:towers、fact:t-mobile-release:original、fact:t-mobile-release:other

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

**模型判讀**　全對。缺口指出估算 T-Mobile 淨支出仍需可避免的建設支出及新增租金。

主要傳導位置　1。全項通過位置　1。

- 候選 1　四項語義均通過。無線業務交易交割後，T-Mobile 依約新增租用 UScellular 保留的至少 2,100 座鐵塔。實際起租才增加 UScellular 塔租收入，金額仍待確認。雙方交易公告可區分本案起租與其他租戶增租，並可用期末全數未起租的明確披露推翻期內預測。

### 純 Astra · 完成

[逐次回傳](raw/calls/P-03-astra.json) · [CLI 事件](raw/jobs/P-03-astra/events.jsonl) · [模型原始 JSON](raw/jobs/P-03-astra/answer.json) · [CLI 診斷](raw/jobs/P-03-astra/stderr.log) · [完整請求](raw/jobs/P-03-astra/request.json)

**研究首稿 · 觀望**

- 傳導機制　T-Mobile 擬以約 44 億美元取得 UScellular 的客戶及特定頻譜，對價已含至多 20 億美元承接債務。公司預期整合後每年合計節省約 10 億美元營運支出及資本支出，另估整合成本為 22 至 26 億美元。營運支出節省可改善營業利益，資本支出節省主要減少投資現金流出。
- 標的　T-Mobile 的交易相關營業利益及現金流
- 研究期限　截至 2025 年 12 月 31 日
- 催化劑　交割結果，以及交割後對已實現節省、整合成本和實現時程的首次量化揭露。
- 預測　若於期內交割並開始整合，T-Mobile 的交易相關現金流將同時取決於已實現的支出節省及已支付的整合成本。現有資料不足以判定 2025 年底前的累計淨效益為正。
- 推翻條件　若交易終止，交易帶來的整合效益假設失效。若公司在期限前量化同期已實現節省及整合現金支出，足以判定淨額方向，即可重評觀望立場。
- 模型引文　t-mobile-release:deal、t-mobile-release:other

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

**模型判讀**　全對。缺口列出起租時程、租金、成本及買方綜效拆分等待確認項目。

主要傳導位置　1。全項通過位置　1。

- 候選 1　四項語義均通過。公告支持 T-Mobile 交割後新增長租 UScellular 保留的至少 2,100 座鐵塔。逐站起租才增加 UScellular 塔租收入。交割公告和鐵塔財報可核對具名新增租用，最終條款低於門檻或期末確認全數未起租，可分別推翻座數或期內租金假設。

[逐次回傳](raw/calls/P-03-judge.json) · [CLI 事件](raw/jobs/P-03-judge/events.jsonl) · [模型原始 JSON](raw/jobs/P-03-judge/answer.json) · [CLI 診斷](raw/jobs/P-03-judge/stderr.log) · [完整請求](raw/jobs/P-03-judge/request.json)

## P-04 · Costco · 先導

**研究題目**　Costco 公布 2025 財年第一季業績。請提出可供研究員覆核的繁體中文研究首稿。

**截止**　2024-12-12T23:59:59+00:00　**研究期限**　2025-12-31

- `costco-release:adjusted`　排除油價與匯率影響後，公司調整後可比銷售成長 7.1%，電子商務成長 13.2%。 [官方來源](https://investor.costco.com/news/news-details/2024/Costco-Wholesale-Corporation-Reports-First-Quarter-Fiscal-Year-2025-Operating-Results/default.aspx)
- `costco-release:comps`　可比銷售年增率為美國 5.2%、加拿大 5.8%、Other International 4.7%、全公司 5.2%；另列 E-commerce 13.0%。 [官方來源](https://investor.costco.com/news/news-details/2024/Costco-Wholesale-Corporation-Reports-First-Quarter-Fiscal-Year-2025-Operating-Results/default.aspx)
- `costco-release:footprint`　Costco 營運 897 個倉庫，在美國、加拿大等八個市場設有電子商務網站。 [官方來源](https://investor.costco.com/news/news-details/2024/Costco-Wholesale-Corporation-Reports-First-Quarter-Fiscal-Year-2025-Operating-Results/default.aspx)
- `costco-release:original`　Comparable sales 表和倉庫數段落原文：Costco currently operates 897 warehouses [官方來源](https://investor.costco.com/news/news-details/2024/Costco-Wholesale-Corporation-Reports-First-Quarter-Fiscal-Year-2025-Operating-Results/default.aspx)

**預註冊標準**　未揭露會員或訂單在線上與倉庫間移轉。不可由全公司電商可比增速高於地區指標推出實體被侵蝕或獲導流；需要同店、同會員或訂單分流及重疊口徑。

### 新版 Harness V11 · 完成

[逐次回傳](raw/calls/P-04-ranked.json) · [CLI 事件](raw/jobs/P-04-ranked/events.jsonl) · [模型原始 JSON](raw/jobs/P-04-ranked/answer.json) · [CLI 診斷](raw/jobs/P-04-ranked/stderr.log) · [完整請求](raw/jobs/P-04-ranked/request.json)

**研究首稿 · 多方**

- 傳導機制　首季業績顯示，排除油價與匯率後，電商可比銷售年增 13.2%，高於全公司的 7.1%。若八個市場的既有電商網站持續帶來新增消費，相較於線上銷售僅隨公司整體成長的基準，電商可拉高整體銷售增速。電商銷售占比、來自倉庫通路的移轉額及履約成本均未知，無法估算增量獲利。
- 標的　Costco
- 研究期限　2025-12-31
- 催化劑　2024-12-12 公布首季實績後，以 Costco 投資人關係網站的 2025 財年第二季業績公告檢驗電商領先幅度，最遲於 2025-12-31 覆核。
- 預測　第二季調整後電商可比銷售年增率高於全公司同口徑年增率，差距至少維持首季的 6.1 個百分點。此指標可檢驗電商相對動能，無法辨認新增消費。
- 推翻條件　Costco 公布的第二季調整後電商可比銷售年增率減全公司同口徑年增率，低於 6.1 個百分點。
- 模型引文　fact:costco-release:adjusted、fact:costco-release:footprint

**研究首稿 · 空方**

- 傳導機制　首季全公司可比銷售年增 5.2%，較排除油價與匯率後的 7.1% 低 1.9 個百分點。若油價或匯率的合計拖累加深，即使調整後增速持平，較低的加油站售價或海外銷售換算金額仍會壓低美元計價的可比銷售增速。財報揭示這項曝險，未提供兩因素各自的金額或毛利效果。
- 標的　Costco
- 研究期限　2025-12-31
- 催化劑　以 2024-12-12 公布的首季差距為基準，於 Costco 投資人關係網站公布 2025 財年第二季業績後比對兩種口徑，最遲於 2025-12-31 覆核。
- 預測　第二季全公司調整後可比銷售年增率減未調整年增率，大於首季的 1.9 個百分點，顯示油價與匯率對公布增速的合計拖累擴大。
- 推翻條件　Costco 公布的第二季全公司調整後可比銷售年增率減未調整年增率，小於或等於 1.9 個百分點。
- 模型引文　fact:costco-release:adjusted、fact:costco-release:comps

**待查**　Costco 披露電商與倉庫並行營運，但未揭露線上訂單由哪些倉庫履約、是否排擠店內銷售，或兩個通路之間有何資本與人力調度。電商與全公司增速差無法檢驗這些傳導，需有通路銷售移轉或履約配置的公開資料。

**模型判讀**　全對。指出缺少通路銷售移轉資料，並明確保留電商排擠店內銷售的歸因。倉庫履約與資源調度也僅列為待查事項。


### 現版 Harness V10 · 完成

[逐次回傳](raw/calls/P-04-current.json) · [CLI 事件](raw/jobs/P-04-current/events.jsonl) · [模型原始 JSON](raw/jobs/P-04-current/answer.json) · [CLI 診斷](raw/jobs/P-04-current/stderr.log) · [完整請求](raw/jobs/P-04-current/request.json)

**研究首稿 · 多方**

- 傳導機制　第一季調整後電商可比銷售年增 13.2%，快於全公司 7.1%。若線上通路持續帶來原本不會在倉庫發生的消費，相較於僅將既有消費移往線上的情境，Costco 整體銷售會更高。通路增速差可檢驗電商動能，增量營收與獲利仍取決於電商銷售占比、通路移轉率及履約成本。
- 標的　Costco
- 研究期限　2025-12-31
- 催化劑　2024-12-12 第一季業績公布後，以下一期 Costco 季度業績公告的可比銷售表覆核 2025 財年第二季，研究截止日為 2025-12-31。
- 預測　第二季 Costco 調整後電商可比銷售年增率仍高於全公司同口徑年增率，延續第一季領先 6.1 個百分點的方向。
- 推翻條件　若第二季 Costco 調整後電商可比銷售年增率等於或低於全公司同口徑年增率，電商持續領先的預測即失效。
- 模型引文　fact:costco-release:adjusted

**研究首稿 · 空方**

- 傳導機制　第一季全公司可比銷售年增 5.2%，低於排除油價與匯率影響後的 7.1%。若油價與匯率的合計拖累延續，相較於兩項因素合計影響為零的情境，即使調整後需求維持，報表口徑的可比銷售增幅仍會較低。此差距可觀察名目銷售壓力，兩項因素各自的貢獻及對營業利益的影響尚無法量化。
- 標的　Costco
- 研究期限　2025-12-31
- 催化劑　2024-12-12 公布的第一季數字顯示兩種口徑相差 1.9 個百分點。於 Costco 下一期季度業績公告核對 2025 財年第二季兩種口徑，研究截止日為 2025-12-31。
- 預測　第二季 Costco 全公司未調整可比銷售年增率仍低於排除油價與匯率後的年增率。
- 推翻條件　若第二季 Costco 全公司未調整可比銷售年增率等於或高於同季排除油價與匯率後的年增率，合計拖累延續的預測即失效。
- 模型引文　fact:costco-release:comps、fact:costco-release:adjusted

**待查**　Costco 同時經營電商與倉庫，但全公司可比銷售已包含電商，兩者的增速差無法識別倉庫銷售是否移往線上。要檢驗通路排擠，至少需要可比口徑的倉庫銷售及通路移轉資料。現有資料也未具名可追蹤的交易對手。

**模型判讀**　全對。明確保留倉庫銷售移往線上的歸因，並指出缺少同口徑倉庫銷售與通路移轉資料。所附摘要未明示全公司可比銷售涵蓋電商。


### 純 Astra · 完成

[逐次回傳](raw/calls/P-04-astra.json) · [CLI 事件](raw/jobs/P-04-astra/events.jsonl) · [模型原始 JSON](raw/jobs/P-04-astra/answer.json) · [CLI 診斷](raw/jobs/P-04-astra/stderr.log) · [完整請求](raw/jobs/P-04-astra/request.json)

**研究首稿 · 多方**

- 傳導機制　若既有營運據點與電商的整體銷售動能延續，即使油價與匯率壓低公告增速，排除兩項影響後的可比銷售仍應維持成長。
- 標的　Costco 全公司調整後可比銷售
- 研究期限　2025 財年第二季至第三季
- 催化劑　Costco 公布後續兩季同口徑的可比銷售數據。
- 預測　後續兩季全公司調整後可比銷售年增率均達 5%。此門檻用於檢驗第一季 7.1% 的增速能否大致延續。
- 推翻條件　任一季低於 5%，即未達本假設設定的延續門檻。
- 模型引文　costco-release:adjusted、costco-release:comps

**研究首稿 · 觀望**

- 傳導機制　電商增速持續領先，可能提高其在可比銷售中的占比。對營業利益的影響則取決於電商銷售規模、商品毛利及履約成本。
- 標的　Costco 電商的相對增速與獲利貢獻
- 研究期限　截至 2025-12-31，優先檢驗 2025 財年第二季與第三季
- 催化劑　後續季報揭露電商與全公司調整後可比銷售，或補充通路營收及成本資料。
- 預測　後續兩季電商調整後可比銷售年增率均高於全公司同口徑增速。
- 推翻條件　若任一季電商增速持平或落後，連續領先的預測即失效。若公司量化電商新增銷售及相關營業利益，則可重估獲利貢獻。
- 模型引文　costco-release:adjusted、costco-release:footprint

**待查**　Costco 在八個市場設有電商網站，但公告只提供全公司與電商的可比銷售增速，缺少電商銷售占比、會員跨通路消費及純倉庫通路數據。現階段無法判定電商成長帶來多少新增消費、多少來自通路移轉，也無法將成長歸因於特定交易對手。

**模型判讀**　未全對。指出缺少會員跨通路消費與純倉庫銷售資料，並保留通路移轉歸因。但聲稱公告只列全公司與電商增速，與公告另列美國、加拿大及其他國際市場可比銷售增速的事實相牴觸。


[逐次回傳](raw/calls/P-04-judge.json) · [CLI 事件](raw/jobs/P-04-judge/events.jsonl) · [模型原始 JSON](raw/jobs/P-04-judge/answer.json) · [CLI 診斷](raw/jobs/P-04-judge/stderr.log) · [完整請求](raw/jobs/P-04-judge/request.json)

## H-01 · Corning · 保留集

**研究題目**　Corning 公布擴大一項製造合作。請提出可供研究員覆核的繁體中文研究首稿。

**截止**　2025-08-06T23:59:59+00:00　**研究期限**　2026-12-31

- `corning-release:commitment`　Apple 宣布新的 25 億美元承諾，與 Corning 合作在肯塔基州 Harrodsburg 工廠生產全球銷售的 iPhone 和 Apple Watch 所有 cover glass。 [官方來源](https://www.apple.com/newsroom/2025/08/apple-corning-to-manufacture-all-iphone-apple-watch-cover-glass-in-kentucky/)
- `corning-release:original`　公告開頭三段，承諾、工廠用途及研發安排原文：Corning will now dedicate this entire facility to manufacturing for Apple [官方來源](https://www.apple.com/newsroom/2025/08/apple-corning-to-manufacture-all-iphone-apple-watch-cover-glass-in-kentucky/)
- `corning-release:other`　雙方將在同廠設立 Apple-Corning Innovation Center，研發先進材料。此案屬 Apple 較大的美國投資計畫，公告未列採購單價、出貨節奏或承諾金額如何拆分。 [官方來源](https://www.apple.com/newsroom/2025/08/apple-corning-to-manufacture-all-iphone-apple-watch-cover-glass-in-kentucky/)
- `corning-release:plant`　Corning 會建立新的智慧手機玻璃生產線，整個 Harrodsburg 工廠專供 Apple，預期 Corning 在肯塔基州的製造及工程人力增加 50%。 [官方來源](https://www.apple.com/newsroom/2025/08/apple-corning-to-manufacture-all-iphone-apple-watch-cover-glass-in-kentucky/)

**預註冊標準**　主要路徑為 Apple 具名承諾與 Harrodsburg 全廠專供，透過量產、認證及實際出貨影響 Corning 玻璃線利用率、玻璃產品營收或固定成本／毛利。以生產線啟用、供應範圍與新增出貨區分既有外地訂單轉產或僅設研發中心；25 億美元不得視為已實現收入或保證採購額。

### 新版 Harness V11 · 完成

[逐次回傳](raw/calls/H-01-ranked.json) · [CLI 事件](raw/jobs/H-01-ranked/events.jsonl) · [模型原始 JSON](raw/jobs/H-01-ranked/answer.json) · [CLI 診斷](raw/jobs/H-01-ranked/stderr.log) · [完整請求](raw/jobs/H-01-ranked/request.json)

**研究首稿 · 多方**

- 傳導機制　Apple 於 2025-08-06 宣布擴大合作。相較維持既有產線，若新線完成投產、Apple 實際分配採購量且 Corning 開始商業交付，Harrodsburg 可增加可售產出並攤薄固定成本。若僅移轉 Corning 其他廠的產量，集團增益將較小。
- 標的　Corning
- 研究期限　2026-12-31
- 催化劑　公告後 Harrodsburg 智慧手機玻璃新線由建置轉入商業供貨，於 2026-12-31 覆核 Apple Newsroom 或 Corning 的工廠進度公告。
- 預測　從公告時的新線建置計畫，進展到截至覆核日已有該新線向 Apple 商業交付的公開確認。此里程碑可驗證供貨機制，營收認列仍取決於交易條款。
- 推翻條件　Apple 或 Corning 明確表示，截至 2026-12-31 該新線仍在建置或試產，尚未向 Apple 商業交付。
- 模型引文　fact:corning-release:commitment、fact:corning-release:plant、fact:corning-release:other

**研究首稿 · 空方**

- 傳導機制　建置 Apple 專線需要製造及工程人力。相較維持原配置，若 Corning 先擴編再商業供貨，新增人力成本會先於新線銷售產生，形成爬坡期成本負擔。人力增加 50% 是預期，實際薪資、資本化比例及 Apple 分攤額均未知。
- 標的　Corning
- 研究期限　2026-12-31
- 催化劑　公告後首輪擴編與首批商業交付的先後次序，於 2026-12-31 前以 Apple Newsroom 或 Corning 肯塔基州製造進度更新覆核。
- 預測　2025-08-06 至覆核日期間，Corning 肯塔基州製造及工程實際人力較公告前增加，且公開更新可確認合作案新增人員在新線首批商業交付前已到職。職缺數只能反映招聘意向。
- 推翻條件　同期間的公開更新確認，Corning 肯塔基州製造及工程人力截至新線首批商業交付時仍持平或低於公告前水準，合作案擴編始於交付當日或之後。
- 模型引文　fact:corning-release:plant、fact:corning-release:original、fact:corning-release:other

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

- 第 1 條排序理由　此路徑有具名客戶、金額承諾與專廠安排，商售產品採用可直接驗證新產能是否進入 Apple 供應體系。

- 第 2 條排序理由　同廠研發安排有公告可查，但人力共用、原訂時程及資金投入均待證實，故列第二。

**模型判讀**　未全對。缺口保留對承諾金額用途及整廠專供是否影響其他客戶或業務的判斷。

主要傳導位置　未選入。全項通過位置　無。

- 候選 1　四項語義均通過。公告支持 Apple 承諾與 Corning 整廠專供。合格交付及採購配置可增加 Apple 對該來源的採購支出。Apple Newsroom 若於期內確認商售 iPhone 採用新線玻璃，可區分舊線增產。財務傳導落在 Apple 的採購支出，未連至 Corning 的利用率、營收或成本。
- 候選 2　財務歸因。公告支持同廠規劃，抽調工程人員及研發延誤均列為條件性假設。期內公開進度若交代延誤源於人員調度，可區分場地或設備問題，按期啟動則可推翻延誤預測。設備閒置時間屬營運指標，尚未連至財務指標或其變動方向。

### 現版 Harness V10 · 完成

[逐次回傳](raw/calls/H-01-current.json) · [CLI 事件](raw/jobs/H-01-current/events.jsonl) · [模型原始 JSON](raw/jobs/H-01-current/answer.json) · [CLI 診斷](raw/jobs/H-01-current/stderr.log) · [完整請求](raw/jobs/H-01-current/request.json)

**研究首稿 · 多方**

- 傳導機制　相較維持原生產配置，Apple 規劃將兩類產品的蓋板玻璃集中至 Harrodsburg，可為 Corning 新線提供生產負荷。若新線進入持續商業供貨，在地產出可增加，固定成本可由更多良品分攤。若僅移轉既有產量，集團營收增幅仍可能有限。
- 標的　Corning
- 研究期限　2026-12-31
- 催化劑　2025-08-06 公告後，追蹤 Apple Newsroom 或 Corning 廠務公告是否確認新線首次商業供貨。覆核截止日為 2026-12-31。
- 預測　公告日至截止日，Harrodsburg 新設智慧手機玻璃線由規劃轉為實際供應 iPhone 蓋板玻璃。以企業公開確認商業出貨為門檻，動工、試產及 Apple 承諾金額均不足以跨過門檻。出貨量、良率及收入認列金額仍待查。
- 推翻條件　截至同一截止日，Apple 或 Corning 明確確認該新線仍處建置或試產階段，首批 iPhone 蓋板玻璃商業出貨尚待開始。
- 模型引文　fact:corning-release:commitment、fact:corning-release:plant、fact:corning-release:original

**研究首稿 · 空方**

- 傳導機制　相較維持原人力配置，專廠擴線需要招募及訓練製造與工程人員。若關鍵職位補實落後於設備就緒時間，即使新線能出貨，也可能延後增開班次，使產出受限、單位固定成本偏高。公告所稱人力預增 50% 是展望，實際缺額與成本影響未知。
- 標的　Corning
- 研究期限　2026-12-31
- 催化劑　自 2025-08-06 擴線公告至 2026-12-31，在新線設備就緒後的爬坡階段，覆核 Corning 或 Apple 對 Harrodsburg 人力到位及開班進度的公開更新。
- 預測　期內至少一次進度更新明確指出，Harrodsburg 新線因製造或工程人員未到位，實際開班晚於廠方原排程。單看徵才人數或全州人力增幅，無法辨識開班瓶頸。
- 推翻條件　同期間 Corning 或 Apple 明確確認，Harrodsburg 新線爬坡所需人員按期到位，該階段各預定班次均如期開出。若僅更新全州人數，開班假說仍未決。
- 模型引文　fact:corning-release:plant、fact:corning-release:original

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

**模型判讀**　未全對。缺口指出人力調度、專案時程與資金分攤待查，並保留對資源共用及排擠的判斷。

主要傳導位置　未選入。全項通過位置　無。

- 候選 1　四項語義均通過。公告支持新線與研發中心同廠規劃。新線驗證須有實際指派與資源投入，Corning 自付時才會增加現金流出。Apple 或 Corning 的期內進度可確認中心是否啟動新線專案，區分一般材料研究。此路徑未追蹤 Apple 承諾對 Corning 玻璃量產與出貨的影響。

### 純 Astra · 完成

[逐次回傳](raw/calls/H-01-astra.json) · [CLI 事件](raw/jobs/H-01-astra/events.jsonl) · [模型原始 JSON](raw/jobs/H-01-astra/answer.json) · [CLI 診斷](raw/jobs/H-01-astra/stderr.log) · [完整請求](raw/jobs/H-01-astra/request.json)

**研究首稿 · 觀望**

- 傳導機制　Apple 的承諾確立了產品與生產地點，但由承諾金額推算 Corning 收益，仍需知道款項用途、採購條件及認列期間。
- 標的　Corning 合併營收與營業利益
- 研究期限　截至 2026 年 12 月 31 日
- 催化劑　Corning 首次說明量產進度，並揭露本案帶來的新增訂單、成本變化或獲利貢獻。
- 預測　預期新線投產或出貨進度將先於本案可歸屬的合併獲利數字得到公開確認。在能區分移轉訂單與新增訂單前，維持原有獲利估計。
- 推翻條件　若公司先提供足以估算 2026 年增量營業利益的金額、期間與成本口徑，應立即依揭露重估。
- 模型引文　corning-release:commitment、corning-release:plant、corning-release:other

**研究首稿 · 空方**

- 傳導機制　若 Corning 先擴編製造與工程人力，客戶拉貨或良率提升卻落後，初期較少的合格出貨件數將負擔較高的人事與製造成本。
- 標的　Corning 在 Harrodsburg 生產蓋板玻璃的毛利
- 研究期限　投產準備期至 2026 年 12 月 31 日
- 催化劑　公司確認已增加人力，同時下修量產進度或揭露額外投產成本。
- 預測　若擴編先於出貨且成本由 Corning 負擔，預期公司將提及投產費用或低利用率拖累當期毛利。
- 推翻條件　若出貨與擴編同步，且公司確認新增成本已由訂單毛利或客戶補償吸收，則此項下行假設失效。
- 模型引文　corning-release:plant、corning-release:original、corning-release:other

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

**模型判讀**　全對。單廠成本改善仍可能伴隨既有訂單轉產。原供貨地、移轉量與新增量待查，合併獲利效果仍待驗證。

主要傳導位置　1。全項通過位置　1。

- 候選 1　四項語義均通過。公告支持 Apple 蓋板玻璃供應集中至 Corning 專供工廠及新線規劃。訂單吸收產能且良率達標時，合格出貨增加可降低新線每件固定成本。期內財報、法說或工廠公告可用投產與持續出貨區分僅推進研發，也可用低良率及單位成本偏高推翻成本改善。

[逐次回傳](raw/calls/H-01-judge.json) · [CLI 事件](raw/jobs/H-01-judge/events.jsonl) · [模型原始 JSON](raw/jobs/H-01-judge/answer.json) · [CLI 診斷](raw/jobs/H-01-judge/stderr.log) · [完整請求](raw/jobs/H-01-judge/request.json)

## H-02 · HP Inc. · 保留集

**研究題目**　HP Inc. 在平台發布活動展示新款電腦。請提出可供研究員覆核的繁體中文研究首稿。

**截止**　2024-05-20T23:59:59+00:00　**研究期限**　2025-06-30

- `hp-release:channel`　發表列有 Microsoft.com 與主要製造商及零售商的預購通路，沒有 OEM 層級的實際預購量。 [官方來源](https://blogs.microsoft.com/blog/2024/05/20/introducing-copilot-pcs/)
- `hp-release:hp`　平台公告列出 HP 的兩個 Copilot+ PCs 機型 HP OmniBook X AI PC 和 HP EliteBook Ultra G1q AI PC，使用 Snapdragon X Elite。 [官方來源](https://blogs.microsoft.com/blog/2024/05/20/introducing-copilot-pcs/)
- `hp-release:original`　OEM 合作夥伴列表及 AI innovation across the Windows ecosystem原文：HP’s OmniBook X AI PC and HP EliteBook Ultra G1q AI PC with Snapdragon X Elite [官方來源](https://blogs.microsoft.com/blog/2024/05/20/introducing-copilot-pcs/)
- `hp-release:rival`　同場列出 Lenovo 的 Yoga Slim 7x、ThinkPad T14s Gen 6 與其他 OEM；首批機型採用 Qualcomm Snapdragon X Series 的 X Elite 或 X Plus。 [官方來源](https://blogs.microsoft.com/blog/2024/05/20/introducing-copilot-pcs/)

**預註冊標準**　指出共用 Qualcomm 或 Windows 及並列上市沒有證明 Lenovo 與 HP 間的晶片配額、通路訂單或企業客戶移轉。需要供應配額或庫存分配、企業得標/失標或同通路 sell-through 資料，保留歸因；有明示的共同平台上市可以另述。

### 新版 Harness V11 · 完成

[逐次回傳](raw/calls/H-02-ranked.json) · [CLI 事件](raw/jobs/H-02-ranked/events.jsonl) · [模型原始 JSON](raw/jobs/H-02-ranked/answer.json) · [CLI 診斷](raw/jobs/H-02-ranked/stderr.log) · [完整請求](raw/jobs/H-02-ranked/request.json)

**研究首稿 · 多方**

- 傳導機制　若未推出兩款新機，HP 無法以這兩款產品承接此次平台需求。若兩款均由預購轉為可交貨，HP 便多了可實際銷售的產品。營收增量取決於成交、交付及認列，並須扣除對既有 HP 機型的替代。
- 標的　HP Inc.
- 研究期限　2025-06-30
- 催化劑　2024-05-20 Microsoft 公布 HP 兩款 Copilot+ PCs 及平台預購通路。後續催化點是兩款新機各自開始供貨。
- 預測　自發表至 2025-06-30，HP 上市公告或具名官方商店頁可確認兩款機型均曾開始交貨或提供現貨。基準是發表日僅確認兩款列名；現貨狀態僅代理供貨能力。
- 推翻條件　同一期間，HP 明確確認至少一款已取消上市，或首次供貨延至 2025-06-30 之後，即推翻兩款均已供貨的預測。單日缺貨或頁面消失不足以判定。
- 模型引文　fact:hp-release:hp、fact:hp-release:original、fact:hp-release:channel

**研究首稿 · 空方**

- 傳導機制　同場推出的 Lenovo 機型讓買家可在首批同平台產品間比價。相較於 HP 上市時沒有這批競品的情境，若 HP 須先行折價以爭取買家，即使順利供貨，每台收入及毛利仍可能承壓。實際影響取決於成交量、折讓負擔及成本。
- 標的　HP Inc.
- 研究期限　2025-06-30
- 催化劑　5 月 20 日兩家同場發表後，以 HP OmniBook X AI PC 與 Lenovo Yoga Slim 7x 在同一市場、同一零售通路首次同時有現貨且公開售價為比價起點。
- 預測　若起點距 2025-06-30 至少八週，記錄起點及第八週的公開單機售價，各固定同一配置。預期 HP 第八週售價低於起點，且相對起點的跌幅大於 Lenovo。此為競爭折價代理，無法歸因至特定競品或確認 HP 實收價。
- 推翻條件　同一通路、配置及八週比較中，若 HP 售價持平或上升，或其跌幅小於或等於 Lenovo，即推翻相對折價預測。缺少配對報價或觀察期不足則無法判定。
- 模型引文　fact:hp-release:hp、fact:hp-release:rival、fact:hp-release:channel

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

- 第 1 條排序理由　此連結優先，因具名機型與晶片配置可逐一核對，且量產交貨直接關係到晶片部署，追加採購金額則仍待證實。

**模型判讀**　未全對。缺口聚焦 Microsoft 通路收入與 HP 內部資源配置，未指出辨識 Lenovo 與 HP 之間晶片配額、通路訂單或企業客戶移轉所需的證據，也未明示保留該項歸因。

- 候選 1　四項語義均通過。公告支持 HP OmniBook 搭載 Qualcomm X Elite。整機交貨可驗證 HP 的商用部署，Qualcomm 晶片收入增量另取決於追加採購、交付與認列，金額未知。期限內的 HP 或 Microsoft 公告若確認取消或延後交貨，可否定 HP 部署里程碑，即使其他品牌仍有進展。此路徑未處理 Lenovo 與 HP 之間的移轉歸因。

### 現版 Harness V10 · 完成

[逐次回傳](raw/calls/H-02-current.json) · [CLI 事件](raw/jobs/H-02-current/events.jsonl) · [模型原始 JSON](raw/jobs/H-02-current/answer.json) · [CLI 診斷](raw/jobs/H-02-current/stderr.log) · [完整請求](raw/jobs/H-02-current/request.json)

**研究首稿 · 多方**

- 傳導機制　5 月 20 日展示及預購安排讓買方可選擇兩款 HP 新機。相較未推出新品，若 HP 備貨後轉為現貨銷售，便新增可即時購買的產品，有機會承接原本會流向其他品牌的需求。現貨狀態只驗證銷售條件；營收增量仍取決於成交量、交付及對既有 HP 機型的排擠。
- 標的　HP Inc.
- 研究期限　2025-06-30
- 催化劑　以 2024 年 5 月 20 日平台公告列出兩款機型及預購通路為起點，追蹤上市後的供貨狀態。
- 預測　自公告日至 2025-06-30，HP 官方商店或公告所指主要零售商至少一次將兩款中的一款標為有現貨，且提供下單與配送選項。這是通路可供貨的代理指標。
- 推翻條件　若同一市場的兩款商品頁在整個觀察期均明示僅接受預購、尚未供貨或已取消上市，則推翻現貨銷售假設。頁面缺失或觀察紀錄中斷時，結果待定。
- 模型引文　fact:hp-release:hp、fact:hp-release:original、fact:hp-release:channel

**研究首稿 · 空方**

- 傳導機制　同場發布的 Lenovo 筆電讓買方在首波 Copilot+ PCs 中就有其他選擇。相較 HP 新機未面臨同期同平台競品，若通路為爭取買方而促銷 HP 新機，且折讓由 HP 分攤，HP 的單台實收與毛利便會承壓。零售價格可檢查促銷是否出現，折讓由誰負擔及涉及多少台仍未知。
- 標的　HP Inc.
- 研究期限　2025-06-30
- 催化劑　2024 年 5 月 20 日平台同步列出 HP 與 Lenovo 機型。以至少一款所列 Lenovo 機型和一款 HP 新機在同一市場、同一零售商同時有貨為比較起點。
- 預測　自兩品牌首次同時有貨至 2025-06-30，至少一款 HP 新機在該零售商的同配置、無綁約公開售價，低於該機型首次有貨時的同口徑售價。同步記錄 Lenovo 售價與全店促銷，以判斷是否屬普遍折扣。
- 推翻條件　若具備完整可比報價的同期在售 HP 新機，在該零售商至 2025-06-30 的同配置售價均維持或高於各自首次有貨價，則推翻降價預測。若未形成同期在售或缺少起始報價，無法檢驗。
- 模型引文　fact:hp-release:rival、fact:hp-release:hp、fact:hp-release:channel

**待查**　平台公告確認兩款 HP 電腦採用 Snapdragon X Elite。零售頁可覆核整機是否開賣，但要檢驗開賣是否帶動 Qualcomm 新增晶片營收，仍需 HP 追加採購及 Qualcomm 交付的證據。現有資料也未指出 HP 為新品調整了哪一條既有產品線的預算、產能或通路配置。

**模型判讀**　未全對。未提交連結。缺口說明指出仍需 HP 追加採購及 Qualcomm 交付證據，但未指明判斷 Lenovo 與 HP 之間移轉所需的配額、訂單或客戶資料，也未明示保留該項歸因。


### 純 Astra · 完成

[逐次回傳](raw/calls/H-02-astra.json) · [CLI 事件](raw/jobs/H-02-astra/events.jsonl) · [模型原始 JSON](raw/jobs/H-02-astra/answer.json) · [CLI 診斷](raw/jobs/H-02-astra/stderr.log) · [完整請求](raw/jobs/H-02-astra/request.json)

**研究首稿 · 多方**

- 傳導機制　若兩款新品吸引原本不會購買 HP 筆電的客戶，新增銷量可提高 HP 筆電營收。若主要由既有客戶轉購，營收增益則取決於新舊機型的實際成交價差。
- 標的　HP Inc. 筆電營收
- 研究期限　2025-06-30
- 催化劑　HP 公布分機型銷售及新增客戶資料，或說明新品對筆電銷量與平均售價的貢獻。
- 預測　至研究期限，若新品帶來增量需求，HP 的公開說明應可將部分筆電銷量或營收增幅歸因於這兩款機型。
- 推翻條件　若 HP 確認新品銷售僅取代既有機型，且實際成交價未提高，則此營收增益假說失效。
- 模型引文　hp-release:hp、hp-release:channel

**研究首稿 · 空方**

- 傳導機制　Lenovo 同場提供 Yoga Slim 7x 與 ThinkPad T14s Gen 6。若通路折價使 HP 兩款新品的實際成交價下降，且成本降幅不足以抵銷價差，HP 的單機毛利將受壓。
- 標的　HP Inc. 兩款 Copilot+ 筆電的單機毛利
- 研究期限　2025-06-30
- 催化劑　同市場、相近規格的 HP 與 Lenovo 機型出現持續性價差，且 HP 說明促銷對獲利的影響。
- 預測　若價格競爭成立，HP 新品在首批促銷結束後仍需折價，並可在公司揭露中找到折價侵蝕單機毛利的證據。
- 推翻條件　若 HP 維持成交價，或成本下降足以抵銷折價且單機毛利持穩，則此毛利下行情境失效。
- 模型引文　hp-release:hp、hp-release:rival

**研究首稿 · 觀望**

- 傳導機制　公告確認 HP 取得首批產品席位，但預購通路沒有揭露各品牌的實際訂單，且消費者可選擇其他品牌。現階段缺乏調整 HP 獲利預估的依據。
- 標的　HP Inc. 筆電業務獲利預估
- 研究期限　2025-06-30
- 催化劑　HP 首次提供可將終端銷售、成交價或毛利變化歸因於兩款新品的公開資料。
- 預測　若後續仍僅披露上架通路或整體平台出貨，至研究期限仍無法可靠判定事件對 HP 獲利的方向。
- 推翻條件　若可核對的銷售及獲利資料足以辨識新品對 HP 的淨貢獻，即可結束觀望並重估。
- 模型引文　hp-release:hp、hp-release:channel、hp-release:rival

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

**模型判讀**　未全對。缺口說明指出估算 HP 與 Qualcomm 營收所欠的資料，但未指出檢驗 Lenovo 與 HP 之間配額、訂單或客戶移轉所需的證據，也未明示保留該項歸因。

- 候選 1　四項語義均通過。公告支持兩款 HP 筆電搭載 Qualcomm X Elite。終端需求若促成增產且首批備料不足，補單可提高 Qualcomm 對 HP 的晶片銷售收入，金額未知。同期 HP 或 Qualcomm 若公開確認首批備料足以支應全期生產，可否定因備料不足而補單的機制。此路徑未處理 Lenovo 與 HP 之間的移轉歸因。

[逐次回傳](raw/calls/H-02-judge.json) · [CLI 事件](raw/jobs/H-02-judge/events.jsonl) · [模型原始 JSON](raw/jobs/H-02-judge/answer.json) · [CLI 診斷](raw/jobs/H-02-judge/stderr.log) · [完整請求](raw/jobs/H-02-judge/request.json)

## H-03 · United Airlines · 保留集

**研究題目**　United Airlines 公布一項機上服務協議。請提出可供研究員覆核的繁體中文研究首稿。

**截止**　2024-09-13T23:59:59+00:00　**研究期限**　2025-12-31

- `united-release:contract`　United Airlines 與 SpaceX 簽約在主線及區域機隊部署 Starlink Wi-Fi，免費提供旅客，計畫涵蓋逾 1,000 架飛機。預計 2025 年測試及首批飛行。 [官方來源](https://united.mediaroom.com/2024-09-13-The-Inflight-Wi-Fi-Revolution-Now-Arriving-United-Signs-Starlink-Deal-to-Provide-Industry-Leading-Connectivity-in-the-Sky-For-Free)
- `united-release:cost`　公告未列服務、設備或安裝價格，未承諾機上媒體或票價溢價金額。 [官方來源](https://united.mediaroom.com/2024-09-13-The-Inflight-Wi-Fi-Revolution-Now-Arriving-United-Signs-Starlink-Deal-to-Provide-Industry-Leading-Connectivity-in-the-Sky-For-Free)
- `united-release:entertainment`　公告點名機上座椅螢幕與個人裝置的影音串流、直播、購物與遊戲等用途；另提及員工資訊工具及已規劃的客艙升級。 [官方來源](https://united.mediaroom.com/2024-09-13-The-Inflight-Wi-Fi-Revolution-Now-Arriving-United-Signs-Starlink-Deal-to-Provide-Industry-Leading-Connectivity-in-the-Sky-For-Free)
- `united-release:original`　開頭合約範圍、導入與機上娛樂段落原文：Industry's largest agreement includes more than 1,000 aircraft [官方來源](https://united.mediaroom.com/2024-09-13-The-Inflight-Wi-Fi-Revolution-Now-Arriving-United-Signs-Starlink-Deal-to-Provide-Industry-Leading-Connectivity-in-the-Sky-For-Free)

**預註冊標準**　主要路徑是逾千架的具名部署，於認證與上線後帶來 SpaceX Starlink 航空設備或連線服務需求，也可用 United 免費 Wi-Fi 分批部署帶來該機隊連線成本與可觀測的付費 Wi-Fi 遷移作等價。以特定機型認證、實際啟用、或計費政策區分既有機上娛樂更新或其他航司的衛星成長，不能把計畫飛機數直接認作收入。

### 新版 Harness V11 · 完成

[逐次回傳](raw/calls/H-03-ranked.json) · [CLI 事件](raw/jobs/H-03-ranked/events.jsonl) · [模型原始 JSON](raw/jobs/H-03-ranked/answer.json) · [CLI 診斷](raw/jobs/H-03-ranked/stderr.log) · [完整請求](raw/jobs/H-03-ranked/request.json)

**研究首稿 · 多方**

- 傳導機制　免費開放降低旅客使用門檻。若 2025 年首批航班同步開放個人裝置影音串流，相較未部署本協議的情境，聯航便增加一項旅客在航程中可實際使用的服務。對選乘及客收的影響仍取決於覆蓋航班、使用率與旅客選擇。
- 標的　United Airlines
- 研究期限　2025-12-31
- 催化劑　聯航於 2024-09-13 預告 2025 年測試及首批飛行。首航開放哪些旅客功能屬待驗證情境。
- 預測　至 2025-12-31，聯航新聞室的首航或服務說明確認，2025 年至少一班載客航班已允許旅客透過免費 Starlink Wi-Fi 在個人裝置上串流影音。
- 推翻條件　聯航在同一期限內明確確認，2025 年全年可使用上述免費串流服務的載客航班為零，例如已開通連線但全年均限制影音串流。
- 模型引文　fact:united-release:contract、fact:united-release:entertainment、fact:united-release:cost

**研究首稿 · 空方**

- 傳導機制　主線與區域機隊部署涉及機上設備安裝及測試。若首批改裝需追加機務工時或測試，聯航可能因本案新增的工作而延後原訂裝機批次；即使已有航班提供免費串流，後續覆蓋仍會放慢。增量成本取決於受影響架數、工時及停場天數。
- 標的　United Airlines
- 研究期限　2025-12-31
- 催化劑　觀察聯航於 2025 年啟動測試後，是否公布具原訂完成時點的裝機批次，以及是否因安裝或測試問題修訂時程。
- 預測　若聯航公布原訂於 2025 年內完成的裝機批次，至 2025-12-31，其新聞室或機隊更新將確認至少一批因本案追加安裝或測試工作而較原訂時點延後。
- 推翻條件　聯航於同一期限內確認，所有已公開、原訂於 2025 年內完成的批次均如期或提前完成。若僅公布首航，或缺原訂批次時程與延誤原因，此風險仍無法判定。
- 模型引文　fact:united-release:contract、fact:united-release:cost

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

- 第 1 條排序理由　具名合約直接建立供應關係，且載客首航可驗證實際供應，優先於尚待另行決定的客艙應用。

**模型判讀**　全對。缺口具體指出影音、廣告及購物變現所需的證據，也交代員工工具與客艙升級尚缺資源變動資料。

主要傳導位置　1。全項通過位置　1。

- 候選 1　四項語義均通過。聯航逾千架的部署計畫指向 SpaceX 的 Starlink 航空連線服務。聯航新聞室可用 2025 年載客航班是否實際開通區分測試與營運。開通可驗證供應，收入仍取決於計費及履約條款。

### 現版 Harness V10 · 完成

[逐次回傳](raw/calls/H-03-current.json) · [CLI 事件](raw/jobs/H-03-current/events.jsonl) · [模型原始 JSON](raw/jobs/H-03-current/answer.json) · [CLI 診斷](raw/jobs/H-03-current/stderr.log) · [完整請求](raw/jobs/H-03-current/request.json)

**研究首稿 · 多方**

- 傳導機制　協議使聯航可向旅客免費提供 Starlink Wi-Fi。若測試後投入定期客運，旅客將首次能在聯航實際使用這項服務。相較未部署的情境，聯航多了一項可供旅客選擇航班時考量的服務。對客收的影響取決於覆蓋航班、使用率及訂位反應。
- 標的　United Airlines
- 研究期限　2025-12-31
- 催化劑　聯航於 2024-09-13 簽約，當時預期 2025 年測試及首批飛行。觀察測試後的首班旅客服務公告。
- 預測　截至 2025-12-31，United Airlines 新聞室或旅客服務說明確認至少一班已執飛的定期客運航班向旅客開放免費 Starlink Wi-Fi。該指標衡量服務可用性，使用人數及收入仍待查。
- 推翻條件　聯航明確確認截至 2025-12-31，已執飛且向旅客開放免費 Starlink Wi-Fi 的定期客運航班為零，例如公告首次旅客服務已延至 2026 年。僅有測試消息時，結果待定。
- 模型引文　fact:united-release:contract、fact:united-release:cost

**研究首稿 · 空方**

- 傳導機制　逾 1,000 架的計畫橫跨主線與區域機隊。即使首班服務如期啟用，若後續安裝超出原定維修停場時間，聯航可投入營運的機日就會少於未加裝設備的情境。損益幅度取決於額外停場日數、備機及受影響班次。
- 標的　United Airlines
- 研究期限　2025-12-31
- 催化劑　2025 年測試與首批安裝開始後，檢視已完成改裝的飛機是否因安裝工作延後復飛。
- 預測　截至 2025-12-31，聯航至少一架於 2025 年完成 Starlink 安裝的飛機，因安裝而晚於原排維修窗口復飛。檢查 United Airlines 新聞室的部署更新或營運說明是否指明原因。若只公布裝機數，須取得原排與實際復飛紀錄才能檢驗。
- 推翻條件　聯航確認 2025 年內所有已完成 Starlink 安裝的飛機均在原排維修窗口內復飛，因安裝延後復飛者為零。缺少逐機排程或公司說明時，不能判定。
- 模型引文　fact:united-release:contract、fact:united-release:original、fact:united-release:cost

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

**模型判讀**　未全對。缺口指出交易歸屬、分潤及改裝資源調度仍待查證。唯一提交的路徑未涵蓋 SpaceX 航空連線需求或聯航機隊連線成本與付費服務遷移。

主要傳導位置　未選入。全項通過位置　無。

- 候選 1　四項語義均通過。公告支持購物用途。聯航須開放結帳並享有銷售收入或分潤，才可能增加附加收入。聯航 2025 年旅客服務說明可查結帳是否依賴 Starlink，以區分獨立的客艙升級。此路徑指向購物收入。

### 純 Astra · 完成

[逐次回傳](raw/calls/H-03-astra.json) · [CLI 事件](raw/jobs/H-03-astra/events.jsonl) · [模型原始 JSON](raw/jobs/H-03-astra/answer.json) · [CLI 診斷](raw/jobs/H-03-astra/stderr.log) · [完整請求](raw/jobs/H-03-astra/request.json)

**研究首稿 · 觀望**

- 傳導機制　United 承諾向旅客免費提供服務。即使按期上線，獲利效果仍取決於新增收入或營運節省能否覆蓋設備、安裝及服務成本。
- 標的　United Airlines 的增量營業利益
- 研究期限　2025-12-31
- 催化劑　首批載客航班啟用，以及首份涵蓋商用期的成本或收入說明。
- 預測　依截至 2024-09-13 的計畫，2025 年可先檢驗首批航班是否上線。若屆時只公布啟用架數，仍無從判定對營業利益的淨影響。
- 推翻條件　若 United 公布可歸因於此服務的增量營業利益，或披露足以比較同期間收益與成本的資料，即可據以調整觀望判斷。
- 模型引文　united-release:contract、united-release:cost、united-release:entertainment

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

**模型判讀**　全對。第二條符合指定傳導。缺口交代分包商、內容及購物合作方和相關變現條款的披露限制。

主要傳導位置　2。全項通過位置　2。

- 候選 1　四項語義均通過。公告支持免費連線及影音、購物用途。聯航每旅客購物分潤須有增量交易及分潤權，同期比較客艙配置與航程相近的航班可檢驗使用量並處理客艙升級因素。此路徑衡量聯航附加收入。
- 候選 2　四項語義均通過。聯航主線及區域機隊開通載客服務後，SpaceX 實際供應連線的飛機數可增加。雙方公開更新可驗證 2025 年商用啟用，固定收費條款可推翻按啟用架數推估收入的假設。

[逐次回傳](raw/calls/H-03-judge.json) · [CLI 事件](raw/jobs/H-03-judge/events.jsonl) · [模型原始 JSON](raw/jobs/H-03-judge/answer.json) · [CLI 診斷](raw/jobs/H-03-judge/stderr.log) · [完整請求](raw/jobs/H-03-judge/request.json)

## H-04 · 3M · 保留集

**研究題目**　3M 公布完成一項分拆。請提出可供研究員覆核的繁體中文研究首稿。

**截止**　2024-04-01T23:59:59+00:00　**研究期限**　2025-06-30

- `3m-release:capital`　公告說兩家公司可各自採用不同成長與資本配置策略，未就這筆持股未來變現指明金額、日期或用途。 [官方來源](https://investors.3m.com/news-events/press-releases/detail/1835/3m-completes-spin-off-of-solventum)
- `3m-release:holding`　3M 持有 Solventum 流通普通股 19.9%，公告表示將於分拆後五年內變現。 [官方來源](https://investors.3m.com/news-events/press-releases/detail/1835/3m-completes-spin-off-of-solventum)
- `3m-release:original`　公告前三段與持股處置說明原文：will be monetized within five years following the spin-off [官方來源](https://investors.3m.com/news-events/press-releases/detail/1835/3m-completes-spin-off-of-solventum)
- `3m-release:spin`　3M 完成將醫療保健業務分拆為 Solventum；3M 股東每持四股 3M 取得一股 Solventum。 [官方來源](https://investors.3m.com/news-events/press-releases/detail/1835/3m-completes-spin-off-of-solventum)

**預註冊標準**　區分持股、預計變現與實際配置。不可把 retained stake 當成已收現金，或聲稱其資金已指定投資其他部門、回購或還債。指出需持股處置與資金用途/董事會配置披露才能確證。

### 新版 Harness V11 · 完成

[逐次回傳](raw/calls/H-04-ranked.json) · [CLI 事件](raw/jobs/H-04-ranked/events.jsonl) · [模型原始 JSON](raw/jobs/H-04-ranked/answer.json) · [CLI 診斷](raw/jobs/H-04-ranked/stderr.log) · [完整請求](raw/jobs/H-04-ranked/request.json)

**研究首稿 · 多方**

- 傳導機制　若未分拆，醫療保健業務將繼續留在 3M 集團內。分拆後，3M 持有可單獨變現的 Solventum 股權。多頭情境假設 3M 在研究期內出售部分持股並收現，可增加可供調度的現金。金額取決於出售股數、價格、稅費及交易形式，款項用途與營業利益增量均待證。
- 標的　3M
- 研究期限　2025-06-30
- 催化劑　2024-04-01 完成分拆後，觀察 3M 首次揭露保留持股處分及其對價。五年內變現是公司前瞻計畫，研究期內現金出售是分析情境。
- 預測　以分拆時持股 19.9% 為起點，預期 3M 自分拆日至 2025 年第一季末累計因出售該持股取得的現金對價大於零。於 2025-06-30 前覆核 3M 涵蓋該期間的年報、季報投資附註及現金流量表。
- 推翻條件　若同期間 3M 的持股與交易揭露可確認累計出售收現為零，即推翻此短期現金情境。持股下降本身無法證明收現，未單列對價則保留判斷。
- 模型引文　fact:3m-release:spin、fact:3m-release:holding、fact:3m-release:original、fact:3m-release:capital

**研究首稿 · 空方**

- 傳導機制　若未分拆，兩項業務可繼續共用企業職能。空頭情境假設拆分系統及職能需要額外支出，且部分費用由 3M 持續營業承擔，因而壓低當期營業利益。公告未揭露責任歸屬、費用金額或持續時間。
- 標的　3M
- 研究期限　2025-06-30
- 催化劑　以 2024-04-01 完成分拆為起點，觀察 3M 在分拆後首份涵蓋完整分拆後季度的財報及後續定期報告如何列報分拆執行費用。
- 預測　預期自分拆日至 2025 年第一季末，3M 持續營業累計認列、可明確歸屬本次分拆的新增執行費用大於零。於 2025-06-30 前查閱 3M 年報、季報的分拆附註與管理層討論。明列費用可確認機制，金額及其占營業利益比重才可衡量重要性。
- 推翻條件　若 3M 揭露足以確認同期間持續營業累計認列的本次分拆新增執行費用為零，即推翻此情境。若僅揭露合併費用或整體利潤率，則仍無法判定。
- 模型引文　fact:3m-release:spin

**待查**　公告確認醫療保健業務已分拆，並揭露 3M 的保留持股。要把影響追到另一項具名業務，仍需 3M 揭露變現所得的實際配置、具名業務承接的人員或成本，或雙方供應與服務合約的品項及對價。

**模型判讀**　全對。將保留持股與實際配置分開，明示須揭露變現所得的實際去向，才可歸因至具名業務。


### 現版 Harness V10 · 完成

[逐次回傳](raw/calls/H-04-current.json) · [CLI 事件](raw/jobs/H-04-current/events.jsonl) · [模型原始 JSON](raw/jobs/H-04-current/answer.json) · [CLI 診斷](raw/jobs/H-04-current/stderr.log) · [完整請求](raw/jobs/H-04-current/request.json)

**研究首稿 · 多方**

- 傳導機制　分拆使 3M 取得可單獨處分的 Solventum 持股。相較於維持原有業務架構，若 3M 提前出售部分持股並收現，即可增加可配置資金。出售規模、淨收款與用途均未知，現階段只能檢驗流動性效益。
- 標的　3M
- 研究期限　2025-06-30
- 催化劑　2024-04-01 分拆完成後，3M 可處分所保留的 19.9% 持股。五年內變現是公司前瞻表述，2024 年內出售收現是研究情境。
- 預測　截至 2025-06-30 覆核 3M 的 2024 年 Form 10-K 持股處分附註與現金流資料，預測自分拆日至 2024 年底，出售 Solventum 持股的現金收入大於零。配發給股東的股份不計入。
- 推翻條件　若 3M 的 2024 年申報確認，自分拆日至年底出售該持股的現金收入為零，即推翻此情境。若只披露持股比例下降，收現情形仍待查。
- 模型引文　fact:3m-release:spin、fact:3m-release:holding、fact:3m-release:original、fact:3m-release:capital

**研究首稿 · 空方**

- 傳導機制　若 3M 在完成分拆後仍需付費拆分共用系統或職能，持續營業業務便可能承擔維持原架構時可避免的執行費用，壓低當期營業利益。這是執行情境，公告未披露費用項目、金額或歸屬。
- 標的　3M
- 研究期限　2025-06-30
- 催化劑　2024-04-01 醫療保健業務完成分拆，隨後的第一個完整季度可用來觀察母公司是否仍認列分拆費用。
- 預測　截至 2025-06-30 覆核 3M 的 2024 年第二季業績公告及 Form 10-Q，預測該季 3M 持續營業業務認列的 Solventum 分拆相關營業費用大於零。須由公司明確歸因，整體營業利益率變動不足以驗證。
- 推翻條件　若 3M 明確揭露 2024 年第二季持續營業業務認列的 Solventum 分拆相關營業費用為零，即推翻此情境。若僅揭露合併費用或未分項，結果待定。
- 模型引文　fact:3m-release:spin

**待查**　公告未指明 3M 哪項業務會取得變現資金，也未揭露 Solventum 與 3M 分拆後的產品供銷關係。要檢驗第二層影響，需有具名業務的資金配置決議與實際支出，或雙方披露的產品合約與交易額。

**模型判讀**　全對。未將變現資金歸給任何業務，並具體要求具名業務的配置決議與實際支出作為佐證。


### 純 Astra · 完成

[逐次回傳](raw/calls/H-04-astra.json) · [CLI 事件](raw/jobs/H-04-astra/events.jsonl) · [模型原始 JSON](raw/jobs/H-04-astra/answer.json) · [CLI 診斷](raw/jobs/H-04-astra/stderr.log) · [完整請求](raw/jobs/H-04-astra/request.json)

**研究首稿 · 觀望**

- 傳導機制　3M 股東已按每持有四股 3M 取得一股 Solventum 的比例獲配股份。3M 本身另持有 Solventum 流通普通股的 19.9%。若 3M 以現金出售部分持股，可取得處分款。若再以所得償還有息負債，後續利息費用才可能下降。
- 標的　3M 的資金來源與利息費用
- 研究期限　截至 2025-06-30
- 催化劑　3M 首次揭露持股處分已成交、取得的對價及所得用途。
- 預測　若研究期內出現現金出售，3M 的揭露應可核對處分股數與所得金額。若同時確認償債，可依償還金額、利率與日期估算節息幅度。
- 推翻條件　若交易採非現金對價，現金流入的推估即失效。若所得另有用途，則應撤除該筆處分帶來的節息估算。研究期內未見處分仍符合五年內變現的公告時程。
- 模型引文　3m-release:spin、3m-release:holding、3m-release:original、3m-release:capital

**待查**　公告確認分拆後的持股關係，但未揭露 Solventum 與 3M 其餘事業之間的供貨、採購或服務條款，也未指定持股變現所得將投入哪項業務。現有資料僅足以追蹤 3M 的財務影響。

**模型判讀**　未全對。指出公告未指定資金去向，也未聲稱已收現或已配置，但未說明須以實際持股處置及所得用途的披露核實。


[逐次回傳](raw/calls/H-04-judge.json) · [CLI 事件](raw/jobs/H-04-judge/events.jsonl) · [模型原始 JSON](raw/jobs/H-04-judge/answer.json) · [CLI 診斷](raw/jobs/H-04-judge/stderr.log) · [完整請求](raw/jobs/H-04-judge/request.json)

## H-05 · CVS Health · 保留集

**研究題目**　CVS Health 公布完成一項醫療服務收購。請提出可供研究員覆核的繁體中文研究首稿。

**截止**　2023-05-02T23:59:59+00:00　**研究期限**　2024-12-31

- `cvs-release:deal`　CVS Health 完成收購 Oak Street Health，交易企業價值約 106 億美元，透過 50 億美元定期貸款及既有現金和資源籌資。 [官方來源](https://www.cvshealth.com/news/company-news/cvs-health-completes-acquisition-of-oak-street-health.html)
- `cvs-release:original`　交割公告開頭與交割後營運安排原文：Oak Street Health will continue to operate as a multi-payor primary care provider [官方來源](https://www.cvshealth.com/news/company-news/cvs-health-completes-acquisition-of-oak-street-health.html)
- `cvs-release:service`　CVS Health 表示交易擴大其 value-based primary care platform，Oak Street Health 將在 CVS Health 旗下繼續作為多保險方的初級照護服務商營運。 [官方來源](https://www.cvshealth.com/news/company-news/cvs-health-completes-acquisition-of-oak-street-health.html)
- `cvs-release:strategy`　CVS Health 說明整合目的為改善照護可及性、成效與成本。交割公告未給中心計費、病患歸戶量或專門導流保證。 [官方來源](https://www.cvshealth.com/news/company-news/cvs-health-completes-acquisition-of-oak-street-health.html)

**預註冊標準**　主要路徑為納入 Oak Street Health 已有的多付款方、價值導向初級照護據點，增加 CVS Health care delivery 的承作量與風險承擔收入/醫療支出曝險。或採 Aetna Medicare Advantage 的條件性病患歸戶與醫療成本路徑，須明說合作及歸戶未披露。以新據點、具名歸戶或按反映培育期的病患數／成本資料區分純收購併表、額外 Signify 活動或保費定價。

### 新版 Harness V11 · 完成

[逐次回傳](raw/calls/H-05-ranked.json) · [CLI 事件](raw/jobs/H-05-ranked/events.jsonl) · [模型原始 JSON](raw/jobs/H-05-ranked/answer.json) · [CLI 診斷](raw/jobs/H-05-ranked/stderr.log) · [完整請求](raw/jobs/H-05-ranked/request.json)

**研究首稿 · 多方**

- 傳導機制　若未收購，Oak Street Health 即使持續看診，其服務收入也在 CVS Health 合併範圍之外。5 月 2 日交割後，若原有保險方安排持續且 Oak Street Health 依約提供照護，相關收入即可納入 CVS Health。這條收入路徑無須假設新增轉介，獲利貢獻仍取決於支付條款與照護成本。
- 標的　CVS Health
- 研究期限　2024-12-31
- 催化劑　以 2023 年 5 月 2 日交割為起點，在 2024 年 12 月 31 日前覆核 CVS Health 2023 年 Form 10-K 的企業合併附註，查找交割日至 2023 年底 Oak Street Health 已納入合併的實際收入。
- 預測　相對未收購時貢獻為零，CVS Health 揭露上述期間來自 Oak Street Health 的合併收入為正。這可確認收購帶入營收，無法單獨證明新增病患、保險方組合或獲利改善。
- 推翻條件　若 CVS Health 明示交割日至 2023 年底來自 Oak Street Health 的實際合併收入為零或負值，則推翻預測。若只列備考收入或整體部門收入，結果仍待查。
- 模型引文　fact:cvs-release:deal、fact:cvs-release:original、fact:cvs-release:service

**研究首稿 · 空方**

- 傳導機制　若未收購，CVS Health 無須為此交易承擔 50 億美元定期貸款。若交割後的新增借款利息超過其他債務償還或降息所節省的金額，集團利息費用將上升，壓低稅前盈餘，即使照護收入如期併入亦然。貸款本金已知，實際利率與未償期間仍待查。
- 標的　CVS Health
- 研究期限　2024-12-31
- 催化劑　2023 年 5 月 2 日交割並揭露融資安排後，以首個完整九個月同期比較，在 2024 年 12 月 31 日前覆核 CVS Health 2024 年第三季 Form 10-Q 的利息費用及借款附註。
- 預測　CVS Health 2024 年前九個月利息費用高於 2023 年同期，後者僅部分期間承受該筆融資。集團利息費用是代理指標，須以貸款餘額及利率揭露區分本案與其他融資的影響。
- 推翻條件　若 CVS Health 2024 年前九個月利息費用持平或低於 2023 年同期，則推翻集團費用上升的預測。若費用上升但缺少逐筆借款資訊，本案的貢獻仍未確定。
- 模型引文　fact:cvs-release:deal

**待查**　50 億美元定期貸款是已知金額最大的資金承諾，可檢驗集團利息負擔，但公告未指出哪項其他業務因此調整投資。多保險方安排則保留既有就醫管道，公告未具名其他承保業務、轉介協議或新增病患分配。要建立第二層傳導，仍需具名業務的資本支出調整，或具名保險方的網絡與歸戶變化。

**模型判讀**　未全對。未提交連結。缺口以已披露的 50 億美元定期貸款討論集團利息負擔，並指出把融資歸因到其他業務的投資變動，或把交易歸因到特定保險方的新增歸戶，仍需具名資料。

主要傳導位置　未選入。全項通過位置　無。


### 現版 Harness V10 · 完成

[逐次回傳](raw/calls/H-05-current.json) · [CLI 事件](raw/jobs/H-05-current/events.jsonl) · [模型原始 JSON](raw/jobs/H-05-current/answer.json) · [CLI 診斷](raw/jobs/H-05-current/stderr.log) · [完整請求](raw/jobs/H-05-current/request.json)

**研究首稿 · 多方**

- 傳導機制　未收購時，Oak Street Health 的照護服務由其獨立經營。交割後，若多家保險方持續透過 Oak Street Health 為會員取得照護，CVS Health 即取得服務多個付款方的營運基礎。交割本身未證實新增病患、已提供的服務量或已認列收入，各付款方的服務量與照護成本也決定獲利幅度。
- 標的　CVS Health
- 研究期限　2024-12-31
- 催化劑　2023-05-02 交割後，以 2024 年內可取得的 CVS Health 季報、法說或 Oak Street Health 營運公告，覆核公司所述多保險方模式是否持續運作。
- 預測　截至 2024-12-31，公開資料顯示 Oak Street Health 在 2024 年第三季仍實際向至少兩家保險方的會員提供初級照護，符合交割時宣示的多保險方模式。這是營運範圍指標，無法據以估算收入。
- 推翻條件　若公開資料確認 Oak Street Health 在同一季實際服務的保險方僅一家或為零，則推翻此預測。僅有可受理保險名單或缺少服務揭露時，結果待定。
- 模型引文　fact:cvs-release:deal、fact:cvs-release:original、fact:cvs-release:service、fact:cvs-release:strategy

**研究首稿 · 空方**

- 傳導機制　相較未交易時毋須為這筆收購借款，CVS Health 動用 50 億美元定期貸款。若貸款持續計息且其他債務的利息節省不足抵銷，集團利息費用將增加，壓低稅前盈餘。公告未提供適用利率、後續本金餘額或可抵銷成本的營運收益。
- 標的　CVS Health
- 研究期限　2024-12-31
- 催化劑　2023-05-02 公布交割及融資後，2024 年前三季涵蓋完整九個月的交割後期間，可與僅部分期間受交易影響的 2023 年同期比較。
- 預測　至 2024-12-31 查閱 CVS Health 2024 年第三季 Form 10-Q，預期前九個月合併利息費用高於 2023 年同期。此為集團代理指標，須對照債務附註中的貸款餘額與償還情形，才能判斷收購融資的貢獻。
- 推翻條件　若 CVS Health 2024 年前九個月合併利息費用持平或低於 2023 年同期，則集團利息負擔上升的預測失效。個別貸款仍可能產生利息。
- 模型引文　fact:cvs-release:deal

**待查**　公告未點名與 Oak Street Health 有轉介或支付安排的其他 CVS Health 業務或外部保險方。要檢驗跨業務效益，仍需具名業務、交割前比較基準，以及該業務實際轉介、承保或支付成本變化的公開揭露。

**模型判讀**　未全對。未提交連結。缺口指出跨業務歸因仍需具名安排、交割前基準及實際轉介、承保或支付成本資料。

主要傳導位置　未選入。全項通過位置　無。


### 純 Astra · 完成

[逐次回傳](raw/calls/H-05-astra.json) · [CLI 事件](raw/jobs/H-05-astra/events.jsonl) · [模型原始 JSON](raw/jobs/H-05-astra/answer.json) · [CLI 診斷](raw/jobs/H-05-astra/stderr.log) · [完整請求](raw/jobs/H-05-astra/request.json)

**研究首稿 · 多方**

- 傳導機制　維持多保險方營運，讓 Oak Street 有機會從既有合作範圍增加歸戶病患。若中心尚有容量，新增收入可分攤既有營運成本。
- 標的　CVS Health 旗下 Oak Street 既有中心的營業貢獻
- 研究期限　2024-12-31
- 催化劑　CVS 首次揭露可比較的既有中心歸戶病患數與獲利資料。
- 預測　同一批中心的平均歸戶病患數上升，且每家中心的營業貢獻同步增加。
- 推翻條件　若可比資料顯示病患數上升但中心營業貢獻未改善，則固定成本分攤帶動獲利的預期落空。
- 模型引文　cvs-release:original、cvs-release:service、cvs-release:strategy

**研究首稿 · 空方**

- 傳導機制　CVS 以 50 億美元定期貸款支應部分交易資金。若 Oak Street 的新增營業利益不足以吸收交易相關利息及整合費用，收購初期將拖累合併稅前盈餘。
- 標的　收購對 CVS Health 稅前盈餘的增量影響
- 研究期限　2024-12-31
- 催化劑　CVS 揭露 Oak Street 營業損益、交易相關利息及整合費用。
- 預測　在可單獨辨識的可比期間，Oak Street 營業利益扣除尚未計入該利益的整合費用及交易相關利息後為負值。
- 推翻條件　若同期間、同口徑的收購相關稅前貢獻達損益兩平或轉正，則該期間的盈餘拖累假說失效。
- 模型引文　cvs-release:deal、cvs-release:strategy

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

**模型判讀**　未全對。缺口指出個別保險方、支付條款與轉介承諾未揭露，並明確保留對特定保險方的歸因。

主要傳導位置　未選入。全項通過位置　無。

- 候選 1　四項語義均通過。公告支持 Oak Street 持續多保險方營運及 CVS 擴大初級照護平台。此路徑檢驗既有中心在有餘裕、可計費且增量收入高於成本時，歸戶增加能否提升單中心營業貢獻。CVS 季報或法說若顯示同批中心歸戶增加而貢獻持平或下降，即可推翻預測。同批比較可排除新增據點與併表月數差異。路徑未交代收購如何增加 CVS 的承作容量與風險承擔曝險。

[逐次回傳](raw/calls/H-05-judge.json) · [CLI 事件](raw/jobs/H-05-judge/events.jsonl) · [模型原始 JSON](raw/jobs/H-05-judge/answer.json) · [CLI 診斷](raw/jobs/H-05-judge/stderr.log) · [完整請求](raw/jobs/H-05-judge/request.json)

## H-06 · Coca-Cola · 保留集

**研究題目**　Coca-Cola 公布第三季財報與更新指引。請提出可供研究員覆核的繁體中文研究首稿。

**截止**　2024-10-23T23:59:59+00:00　**研究期限**　2025-12-31

- `coca-cola-release:latam`　Latin America 有機營收年增 24%，價格與組合貢獻 21%，箱量持平。 [官方來源](https://investors.coca-colacompany.com/news-events/press-releases/detail/1121/coca-cola-reports-third-quarter-2024-results-and-provides-updated-guidance)
- `coca-cola-release:na`　North America 有機營收年增 12%，價格與組合貢獻 11%，箱量持平。 [官方來源](https://investors.coca-colacompany.com/news-events/press-releases/detail/1121/coca-cola-reports-third-quarter-2024-results-and-provides-updated-guidance)
- `coca-cola-release:original`　Operating Review，Revenues and Volume，地區列原文：Operating Review – Three Months Ended September 27, 2024 [官方來源](https://investors.coca-colacompany.com/news-events/press-releases/detail/1121/coca-cola-reports-third-quarter-2024-results-and-provides-updated-guidance)
- `coca-cola-release:outlook`　有機營收及報表營收受不同的價格、匯率及組合影響；另列集團全年展望。 [官方來源](https://investors.coca-colacompany.com/news-events/press-releases/detail/1121/coca-cola-reports-third-quarter-2024-results-and-provides-updated-guidance)

**預註冊標準**　北美與拉美的價格組合、箱量及有機收入差異不能證明跨區的配置、供應或品牌/顧客轉移。需要具名數量流向、配額、品牌/通路批次或資源決策。

### 新版 Harness V11 · 完成

[逐次回傳](raw/calls/H-06-ranked.json) · [CLI 事件](raw/jobs/H-06-ranked/events.jsonl) · [模型原始 JSON](raw/jobs/H-06-ranked/answer.json) · [CLI 診斷](raw/jobs/H-06-ranked/stderr.log) · [完整請求](raw/jobs/H-06-ranked/request.json)

**研究首稿 · 多方**

- 傳導機制　若第三季拉美較有利的定價或銷售組合延續，即使箱量仍持平，價格與組合也可推升區域有機營收。相較於該項貢獻歸零的基準，拉美對集團營收成長的貢獻較高。區域營收權重與增量毛利率待查。
- 標的　Coca-Cola
- 研究期限　2025-12-31
- 催化劑　2024-10-23 第三季財報揭露拉美有機營收年增 24%、價格與組合貢獻 21%、箱量持平。下一次可用第四季財報檢驗這項貢獻能否延續。
- 預測　以 2025-12-31 為覆核期限，查 Coca-Cola 第四季財報的 Latin America 營運回顧。預期 2024 年第四季價格與組合對年增率的貢獻仍大於零，且區域有機營收仍年增。
- 推翻條件　若同份回顧顯示 Latin America 於 2024 年第四季的價格與組合貢獻為零或負值，或有機營收年增率為零或負值，即推翻上述預測。
- 模型引文　fact:coca-cola-release:latam

**研究首稿 · 空方**

- 傳導機制　北美第三季箱量已持平。若價格與組合的正貢獻部分來自提價，且消費者延後購買，箱量可能由持平轉為年減。相較於購買頻率維持的基準，銷量減少會壓低北美營收，並可能削弱固定成本吸收。實際提價幅度、需求彈性與單箱利潤均未知。
- 標的　Coca-Cola
- 研究期限　2025-12-31
- 催化劑　2024-10-23 第三季財報揭露北美價格與組合貢獻 11%、有機營收年增 12%，箱量持平。第四季箱量可作為提價後需求反應的代理指標。
- 預測　以 2025-12-31 為覆核期限，查 Coca-Cola 第四季財報的 North America 營運回顧。預期 2024 年第四季箱量年增率低於零，弱於第三季持平的基準。箱量下降僅支持需求轉弱，無法單獨歸因於提價。
- 推翻條件　若 Coca-Cola 揭露 North America 於 2024 年第四季箱量較上年同期持平或增加，即推翻箱量轉跌的預測。
- 模型引文　fact:coca-cola-release:na

**待查**　Latin America 與 North America 各自揭露價格與組合及箱量。要建立跨區傳導，仍需公司指出哪項人力、預算或通路資源從一區轉往另一區，並揭露接收業務的部署時點與營運指標。資料亦未具名交易對手或列出採購承諾。

**模型判讀**　全對。將跨區歸因留待公司確認資源移轉的項目與方向，並要求接收業務的部署時點及營運指標。


### 現版 Harness V10 · 完成

[逐次回傳](raw/calls/H-06-current.json) · [CLI 事件](raw/jobs/H-06-current/events.jsonl) · [模型原始 JSON](raw/jobs/H-06-current/answer.json) · [CLI 診斷](raw/jobs/H-06-current/stderr.log) · [完整請求](raw/jobs/H-06-current/request.json)

**研究首稿 · 多方**

- 傳導機制　Latin America 第三季箱量持平，價格與組合仍貢獻 21% 成長。若此效應延續，相較於箱量相同、價格與組合貢獻歸零的情境，該區即使未擴量，也能為集團提供有機營收增量。區域營收權重、匯率與成本影響未明，無法量化集團獲利增幅。
- 標的　Coca-Cola
- 研究期限　2025-12-31
- 催化劑　2024-10-23 第三季財報揭露區域成長來源。以 Coca-Cola 投資人關係網站的 2025 年第一季業績新聞稿覆核其延續性，研究截止日為 2025-12-31。
- 預測　2025 年第一季 Latin America 的價格與組合對年增率貢獻仍為正，且區域有機營收年增率為正。兩項門檻均為零，無須重現第三季的 21% 與 24%。
- 推翻條件　同一季 Coca-Cola 揭露 Latin America 價格與組合貢獻為零或負值，或該區有機營收年增率為零或負值，即推翻此預測。
- 模型引文　fact:coca-cola-release:latam、fact:coca-cola-release:outlook

**研究首稿 · 空方**

- 傳導機制　North America 第三季價格與組合貢獻 11%，箱量持平。若部分貢獻來自消費者實付價格上升，且消費者延後減少購買，相較於實付價格未升、箱量維持持平的情境，區域銷量將轉弱，削弱銷量對獲利的貢獻。實付價格變化、每箱增量利潤及集團曝險均未揭露。
- 標的　Coca-Cola
- 研究期限　2025-12-31
- 催化劑　2024-10-23 財報顯示 North America 收入成長時箱量已停滯。檢視 Coca-Cola 投資人關係網站的 2025 年第一季業績新聞稿，於 2025-12-31 前覆核後續銷量反應。
- 預測　2025 年第一季 North America 箱量年增率低於零。區域箱量是購買反應的代理指標，單憑下降無法將原因歸於漲價。
- 推翻條件　Coca-Cola 揭露 2025 年第一季 North America 箱量較上年同期持平或增加，即推翻該季銷量收縮預測。
- 模型引文　fact:coca-cola-release:na

**待查**　財報分列 Latin America 與 North America 的營運數據，但未揭露兩區之間的預算、產能或通路調度，也未具名供應商或客戶。建立第二層假設仍需公司揭露具體調度決策及受影響業務的可追蹤指標。

**模型判讀**　全對。指出兩區間的預算、產能或通路調度證據缺失，並將跨區歸因留待具體決策及受影響業務的可追蹤指標。


### 純 Astra · 完成

[逐次回傳](raw/calls/H-06-astra.json) · [CLI 事件](raw/jobs/H-06-astra/events.jsonl) · [模型原始 JSON](raw/jobs/H-06-astra/answer.json) · [CLI 診斷](raw/jobs/H-06-astra/stderr.log) · [完整請求](raw/jobs/H-06-astra/request.json)

**研究首稿 · 多方**

- 傳導機制　若拉美與北美能維持有利的售價或銷售組合，且箱量守穩，兩區即使沒有銷量成長，仍有條件維持有機營收成長。
- 標的　Coca-Cola 拉美與北美的有機營收
- 研究期限　先以 2024 年第四季驗證，再逐季追蹤至 2025 年 12 月 31 日。
- 催化劑　下一份分區營運回顧揭露箱量、價格與組合貢獻及有機營收年增率。
- 預測　下一季兩區箱量均持平或成長，價格與組合貢獻及有機營收年增率均為正。
- 推翻條件　若任一區箱量年減，該區守住銷量的前提即告失效。若箱量守穩但有機營收未成長，則該區的營收預測失準。
- 模型引文　coca-cola-release:latam、coca-cola-release:na

**研究首稿 · 空方**

- 傳導機制　拉美第三季箱量持平。若後續價格與組合貢獻回落，而箱量仍未成長，拉美有機營收增速可能放緩，拉美相對北美的成長領先幅度也可能縮小。
- 標的　Coca-Cola 拉美有機營收增速及其相對北美的差距
- 研究期限　以 2024 年第四季對照第三季。
- 催化劑　第四季拉美與北美同口徑分區數據公布。
- 預測　若拉美價格與組合貢獻低於第三季的 21%，且箱量持平或年減，預期其有機營收年增率低於 24%，對北美的增速差也低於第三季的 12 個百分點。
- 推翻條件　在上述條件成立時，若拉美有機營收年增率仍達 24%，則放緩預測失準。若兩區增速差仍達 12 個百分點，則差距收窄的預測失準。
- 模型引文　coca-cola-release:latam、coca-cola-release:na

**研究首稿 · 觀望**

- 傳導機制　分區有機營收成長要轉化為集團報表營收與獲利，仍取決於各區營收權重、匯率及利潤率。現有展望摘要不足以量化這些影響。
- 標的　Coca-Cola 集團報表營收與獲利
- 研究期限　截至 2025 年 12 月 31 日，以屆時已公開的報告覆核。
- 催化劑　核得本次與前次全年指引的具體數值，並取得集團營收調節及利潤率資料。
- 預測　若匯率折算產生負貢獻，且其他調節項未抵銷，集團報表營收年增率將低於集團有機營收年增率。
- 推翻條件　若營收調節顯示匯率影響為零、為正或已被其他項目抵銷，匯率拖累的情境即不適用。若指引及利潤率資料足以量化獲利影響，則可重新評估觀望立場。
- 模型引文　coca-cola-release:outlook、coca-cola-release:latam、coca-cola-release:na

**待查**　拉美與北美都呈現箱量持平、價格與組合支撐營收成長的現象，但兩地數據未顯示一地業務如何影響另一地。資料也未具名揭露裝瓶商或通路商的交易條件，無法估算對特定交易對手獲利的影響。

**模型判讀**　未全對。保留跨區歸因，但未指明需補足的跨區流向或配置決策證據。裝瓶商與通路商的交易條件缺口只關乎交易對手獲利估算。


[逐次回傳](raw/calls/H-06-judge.json) · [CLI 事件](raw/jobs/H-06-judge/events.jsonl) · [模型原始 JSON](raw/jobs/H-06-judge/answer.json) · [CLI 診斷](raw/jobs/H-06-judge/stderr.log) · [完整請求](raw/jobs/H-06-judge/request.json)

## H-07 · Sony Group · 保留集

**研究題目**　Sony Group 公布簽署一項新事業協議。請提出可供研究員覆核的繁體中文研究首稿。

**截止**　2022-06-16T23:59:59+00:00　**研究期限**　2025-12-31

- `sony-release:allocation`　擬定合資資本為 100 億日圓，Sony Group 與 Honda Motor Co., Ltd. 各持 50%。預計 2022 年成立、2025 年開始銷售及供應服務，仍需核准。 [官方來源](https://global.honda/en/newsroom/news/2022/c220616eng.html)
- `sony-release:deal`　Sony Group 與 Honda Motor Co., Ltd. 簽署合資協議，擬成立 Sony Honda Mobility Inc.，開發並銷售電動車及移動服務。 [官方來源](https://global.honda/en/newsroom/news/2022/c220616eng.html)
- `sony-release:operations`　擬結合 Sony 的影像、感測、網路及娛樂技術與 Honda 車體製造、車輛開發及售後服務能力。 [官方來源](https://global.honda/en/newsroom/news/2022/c220616eng.html)
- `sony-release:original`　產品與分工段落、New Company Overview原文：Sony Group Corporation 50%, Honda Motor Co., Ltd. 50% [官方來源](https://global.honda/en/newsroom/news/2022/c220616eng.html)

**預註冊標準**　主要路徑為 50/50 資本承諾與 Sony 技術整合到 Sony Honda Mobility 電動車，帶來 Sony 初期投資現金需求及取決於核准/車型上市的合資收益曝險；Honda 具名開發與製造的資源/產能也可成立。公開核對合資成立、資本及車型產品里程碑，區分一般 Sony 感測器對車廠收入或不合資的技術合作；不得把規劃資本當作本期已付款或整車收入。

### 新版 Harness V11 · 完成

[逐次回傳](raw/calls/H-07-ranked.json) · [CLI 事件](raw/jobs/H-07-ranked/events.jsonl) · [模型原始 JSON](raw/jobs/H-07-ranked/answer.json) · [CLI 診斷](raw/jobs/H-07-ranked/stderr.log) · [完整請求](raw/jobs/H-07-ranked/request.json)

**研究首稿 · 多方**

- 傳導機制　簽約使 Sony 有機會透過合資公司結合自身技術與 Honda 的車輛開發、製造能力。若完成整合並開售，相較無此案，Sony 將取得一條透過合資公司銷售電動車的管道。集團獲利幅度仍缺交車量、單車經濟效益及會計認列依據。
- 標的　Sony Group
- 研究期限　2025-12-31
- 催化劑　雙方在 2022-06-16 簽約公告中預計 2025 年開始銷售。於該年度追蹤 Sony、Honda 或合資公司的正式開售公告。
- 預測　截至 2025-12-31，至少一個市場正式開放合資電動車銷售，較簽約時仍待設立與開售的狀態前進。概念車展示或預約登記不足以驗證開售，開售也須與訂單、交車及收入認列分別核對。
- 推翻條件　Sony、Honda 或合資公司於同一窗口確認所有市場的首次正式銷售延至 2025-12-31 之後，或確認取消上市。
- 模型引文　fact:sony-release:deal、fact:sony-release:operations、fact:sony-release:allocation

**研究首稿 · 空方**

- 傳導機制　即使電動車如期開售，Sony 仍可能先承擔成立出資。相較無此案，按原案繳資將使約 50 億日圓資本投入合資事業，至回收前占用資金。出資本身不構成當期費用，現金影響取決於出資形式。
- 標的　Sony Group
- 研究期限　2025-12-31
- 催化劑　2022-06-16 簽約後的核准、設立及繳資是資本占用的觸發點。自原預計 2022 年設立窗口起，查雙方具名出資公告與 Sony 已公布的投資附註。
- 預測　截至 2025-12-31，若依原案完成繳資，Sony 對本案的成立出資實繳額將達 50 億日圓，基準為擬定資本 100 億日圓的 50%。
- 推翻條件　同期間具名披露確認 Sony 最終成立出資實繳額低於 50 億日圓，或確認撤案且實繳為零。若僅披露設立或股比，實繳額仍待查。
- 模型引文　fact:sony-release:deal、fact:sony-release:allocation、fact:sony-release:original

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

- 第 1 條排序理由　雙方已簽約，原案可推算各方出資規模，具名實繳披露也最能排除 Honda 其他投資的影響。

- 第 2 條排序理由　公告明列 Honda 的售後能力，車主服務安排可驗證實際分工，但收入仍取決於交車與收費條件，故列第二。

**模型判讀**　未全對。兩條鏈結分別驗證 Honda 出資及售後服務。缺口清楚說明 Sony 技術採用、資源移轉及分部收益仍待確認。

主要傳導位置　未選入。全項通過位置　無。

- 候選 1　四項語義均通過。公告支持由擬定資本與持股比例推算 Honda 擬出資 50 億日圓，現金流取決於繳付方式及時點。期限內具名的實繳披露可區分本案與 Honda 其他投資。鏈結落在 Honda 的出資，未建立 Sony 的現金需求及合資收益曝險。
- 候選 2　四項語義均通過。公告支持擬運用 Honda 售後能力。指定承辦、服務啟用及給付可帶來 Honda 售後收入，規模仍待驗。期限內官方公布各啟用市場均由其他業者承辦可推翻假設。此路徑落在售後服務，未涉及指定的開發或製造資源。

### 現版 Harness V10 · 完成

[逐次回傳](raw/calls/H-07-current.json) · [CLI 事件](raw/jobs/H-07-current/events.jsonl) · [模型原始 JSON](raw/jobs/H-07-current/answer.json) · [CLI 診斷](raw/jobs/H-07-current/stderr.log) · [完整請求](raw/jobs/H-07-current/request.json)

**研究首稿 · 多方**

- 傳導機制　若合資案獲准，Sony 可透過合資公司把網路及娛樂技術用於對外提供移動服務，取得無此協議時原本欠缺的服務通路。正式上線可驗證通路已建立，付費採用、分成及 Sony 可認列的收益仍待查。
- 標的　Sony Group
- 研究期限　2025-12-31
- 催化劑　雙方於 2022-06-16 簽約時預計在 2025 年開始供應服務。於該年度追蹤 Sony 或 Honda 新聞室的正式開通公告。
- 預測　以簽約時服務尚在規劃為基準，至 2025-12-31，官方確認至少一項合資移動服務已向目標用戶開放使用。展示、預約或接受車輛訂單均不足以確認服務上線。
- 推翻條件　Sony 或 Honda 明確確認截至 2025-12-31，合資移動服務仍全數處於測試或待推出階段。未更新時程則無法判定。
- 模型引文　fact:sony-release:deal、fact:sony-release:operations、fact:sony-release:allocation

**研究首稿 · 空方**

- 傳導機制　相較無此合資案，Sony 須為共同開發承擔新增資金需求。若整車與技術整合所需資金超出初始規劃，且雙方決定增資、Sony 實際跟投，Sony 的投資現金流出會高於原案。出資本身不等於當期費用，額外金額及對集團現金流的重要性待查。
- 標的　Sony Group
- 研究期限　2025-12-31
- 催化劑　以 2022-06-16 公布的擬定資本 100 億日圓及 Sony 持股 50% 為起點，在公司成立及開發期間追蹤雙方官方增資公告與 Sony 已公開的投資附註。
- 預測　若按原案成立，從成立日至 2025-12-31，Sony 對合資公司的累計實繳股本超過按原案推算的 50 億日圓。以期限內公布的實繳金額或已完成出資公告覆核，增資承諾不足以證明付款。
- 推翻條件　若按原案成立，且公開資料明確顯示截至 2025-12-31，Sony 累計實繳股本仍為 50 億日圓或以下，即推翻追加股本情境。若資料未涵蓋期末或僅列總資本，結果待查。
- 模型引文　fact:sony-release:allocation、fact:sony-release:operations、fact:sony-release:deal

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

**模型判讀**　全對。符合標準所列的 Honda 製造路徑。缺口點明 Sony 技術採用與收費條款仍待確認。

主要傳導位置　1。全項通過位置　1。

- 候選 1　四項語義均通過。公告支持擬運用 Honda 製造能力。合資公司指定 Honda 承製並實際量產，才會增加 Honda 的生產活動。製造利益與前期現金流均按條件表述。期限內的官方投產結果可區分合資車與 Honda 自有車增產，僅能驗證量產進度。

### 純 Astra · 完成

[逐次回傳](raw/calls/H-07-astra.json) · [CLI 事件](raw/jobs/H-07-astra/events.jsonl) · [模型原始 JSON](raw/jobs/H-07-astra/answer.json) · [CLI 診斷](raw/jobs/H-07-astra/stderr.log) · [完整請求](raw/jobs/H-07-astra/request.json)

**研究首稿 · 多方**

- 傳導機制　Honda 的車輛開發、製造與售後能力若能支援 Sony 技術導入量產車，合資公司可從開發階段進入商業營運。
- 標的　Sony Group 的電動車與移動服務合資投資
- 研究期限　2025-12-31
- 催化劑　取得核准並成立合資公司，隨後公布正式開售與服務啟用日期。
- 預測　截至 2025 年底，合資公司已開始銷售電動車並提供移動服務。
- 推翻條件　任一項的正式啟動日延至 2026 年或之後，即未完整達成公告時程。
- 模型引文　sony-release:deal、sony-release:allocation、sony-release:operations

**研究首稿 · 空方**

- 傳導機制　若核准、車輛開發或技術整合延誤，合資公司可能已承擔開發費用，銷售收入卻延後出現，拉長 Sony 的投資回收期。
- 標的　Sony Group 合資投資的回收時程
- 研究期限　2025-12-31
- 催化劑　公司下修上市時程，或披露首批商業交付延後。
- 預測　截至 2025 年底，合資公司仍在開發車款，尚未開始正式銷售。
- 推翻條件　合資公司在 2025 年底前確認已正式開售，即推翻銷售延後假設。
- 模型引文　sony-release:allocation、sony-release:operations

**研究首稿 · 觀望**

- 傳導機制　各持股 50% 可確定 Sony 擬取得的權益比例。估算 Sony 的獲利貢獻，仍需合資公司的收入、成本與 Sony 的會計處理。
- 標的　Sony Group 盈餘估計
- 研究期限　2025-12-31
- 催化劑　Sony 在財報中披露合資投資的認列方式、損益或可量化的營運資料。
- 預測　若後續僅確認設立或開售日期，研究員可更新時程判斷，仍難據此估算 Sony 每股盈餘變動。
- 推翻條件　Sony 直接量化合資案的盈餘影響，或提供足以推算該影響的財務資料。
- 模型引文　sony-release:allocation、sony-release:original、sony-release:deal

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

**模型判讀**　未全對。主張檢驗 Sony 分部的供貨或授權收入，未建立 Sony 的合資出資現金需求及合資收益曝險。缺口保留對價歸屬及合資損益待驗。

主要傳導位置　未選入。全項通過位置　無。

- 候選 1　四項語義均通過。公告支持合資開發電動車及擬整合 Sony 影像與感測技術。有償供貨或授權列為增加 Sony 相關業務收入的必要條件，利益幅度仍取決於量價及成本。期限內 Sony 確認無償投入可排除有償供應假設。

[逐次回傳](raw/calls/H-07-judge.json) · [CLI 事件](raw/jobs/H-07-judge/events.jsonl) · [模型原始 JSON](raw/jobs/H-07-judge/answer.json) · [CLI 診斷](raw/jobs/H-07-judge/stderr.log) · [完整請求](raw/jobs/H-07-judge/request.json)

## H-08 · Home Depot · 保留集

**研究題目**　Home Depot 公布第三季財報與更新指引。請提出可供研究員覆核的繁體中文研究首稿。

**截止**　2024-11-12T23:59:59+00:00　**研究期限**　2025-10-31

- `home-release:baseline`　公告並列收購併表和可比銷售口徑，並未給收購前後的同一客戶名冊、商店交易或銷售渠道遷移。 [官方來源](https://ir.homedepot.com/news-releases/2024/11-12-2024-110156861)
- `home-release:guidance`　全年銷售預計增約 4%（含第 53 週及 SRS Distribution），含 SRS 約 64 億美元的當年增量銷售；可比銷售預計降約 2.5%。 [官方來源](https://ir.homedepot.com/news-releases/2024/11-12-2024-110156861)
- `home-release:original`　財報開頭及 fiscal 2024 guidance 條列原文：Comparable sales for the third quarter of fiscal 2024 decreased 1.3% [官方來源](https://ir.homedepot.com/news-releases/2024/11-12-2024-110156861)
- `home-release:quarter`　Home Depot 第三季銷售年增 6.6%，可比銷售年減 1.3%，美國可比銷售年減 1.2%。 [官方來源](https://ir.homedepot.com/news-releases/2024/11-12-2024-110156861)

**預註冊標準**　可承認明示的 SRS 併表貢獻，但不能把舊有門市同店走弱解讀為既有 Pro 或 DIY 客戶把訂單轉給 SRS。需同客戶採購、訂單、供應區域或有無 SRS 的比較，明確保留該通路歸因。

### 新版 Harness V11 · 完成

[逐次回傳](raw/calls/H-08-ranked.json) · [CLI 事件](raw/jobs/H-08-ranked/events.jsonl) · [模型原始 JSON](raw/jobs/H-08-ranked/answer.json) · [CLI 診斷](raw/jobs/H-08-ranked/stderr.log) · [完整請求](raw/jobs/H-08-ranked/request.json)

**研究首稿 · 多方**

- 傳導機制　11 月 12 日更新的指引反映 SRS Distribution 納入合併報表。相較於未收購情境，SRS 在併表期間認列的銷售可直接增加 Home Depot 營收，即使既有業務可比銷售下滑。公司估計全年增量約 64 億美元，尚缺 SRS 利潤率及整合費用，無法換算獲利貢獻。
- 標的　Home Depot
- 研究期限　2025-10-31
- 催化劑　待 Home Depot 公布 2024 財年全年業績及年報，於 2025-10-31 前核對 SRS 併表期間的實際營收貢獻。
- 預測　以指引的 64 億美元中心值作為研究門檻，預期 Home Depot 揭露的 2024 財年 SRS 增量銷售達 64 億美元。
- 推翻條件　若 Home Depot 揭露同一財年、同一併表口徑的 SRS 增量銷售低於 64 億美元，則未達研究門檻。若僅披露集團總銷售，此項檢驗仍待確認。
- 模型引文　fact:home-release:guidance、fact:home-release:baseline

**研究首稿 · 空方**

- 傳導機制　11 月 12 日財報顯示第三季可比銷售年減 1.3%，全年指引亦指向負成長。若這項疲弱延續至第四季，相較於可比銷售持平的情境，既有業務可用來吸收固定營運費用的銷售額將減少。公告未拆分交易量、售價及固定費用，獲利敏感度待估。
- 標的　Home Depot
- 研究期限　2025-10-31
- 催化劑　Home Depot 公布 2024 財年第四季業績時，於 2025-10-31 前檢查公司整體單季可比銷售年增率，判斷第三季的疲弱是否延續。
- 預測　預期 Home Depot 2024 財年第四季整體可比銷售年增率低於零。全年約減 2.5% 是公司指引，第四季續跌是研究假設。
- 推翻條件　若 Home Depot 公布 2024 財年第四季整體可比銷售年增率持平或轉正，則第三季跌勢延續的假設失效。
- 模型引文　fact:home-release:quarter、fact:home-release:original、fact:home-release:guidance

**待查**　SRS Distribution 併表會改變集團營收口徑，但公告未揭露原有門市客戶是否轉向 SRS、是否透過 SRS 增購，或兩者是否各自服務不同需求。要檢驗通路移轉或交叉銷售，需有收購前後同一批客戶的分通路銷售及毛利，或公司公開量化兩者的影響。總銷售與可比銷售的差距無法區分這些情境。

**模型判讀**　全對。未提交連結。要求收購前後同一批客戶的分通路資料，並保留客戶移轉與交叉銷售歸因。


### 現版 Harness V10 · 完成

[逐次回傳](raw/calls/H-08-current.json) · [CLI 事件](raw/jobs/H-08-current/events.jsonl) · [模型原始 JSON](raw/jobs/H-08-current/answer.json) · [CLI 診斷](raw/jobs/H-08-current/stderr.log) · [完整請求](raw/jobs/H-08-current/request.json)

**研究首稿 · 多方**

- 傳導機制　11 月 12 日更新的指引反映 SRS Distribution 併表後可認列的銷售。相較未收購情境，若併表期間的 SRS 銷售足以抵銷原有業務疲弱，集團全年銷售仍可成長。約 64 億美元是管理層預估的增量銷售，實際獲利貢獻仍取決於未揭露的利潤率與整合成本。
- 標的　Home Depot
- 研究期限　2025-10-31
- 催化劑　11 月 12 日公司將 SRS 增量銷售納入全年展望，待 2024 財年結束後，以 Home Depot 全年業績公告覆核。
- 預測　截至 2025-10-31，預期全年業績公告顯示 2024 財年合併銷售高於上年。此為集團層級代理指標，第 53 週也貢獻銷售。若公司拆列 SRS 實績，可另與約 64 億美元指引核對。
- 推翻條件　Home Depot 公布的 2024 財年合併銷售持平或低於上年，即推翻集團銷售成長預測，即使 SRS 本身仍有正貢獻。
- 模型引文　fact:home-release:guidance、fact:home-release:baseline、fact:home-release:quarter

**研究首稿 · 空方**

- 傳導機制　第三季可比銷售年減 1.3%，全年指引仍預期年減約 2.5%。若可比業務的銷售缺口延續，相較可比銷售持平情境，既有營運費用將由較少銷售額分攤，可能壓低營業利益率。財報揭示的是銷售壓力，費用調整幅度與利潤率影響仍屬情境假設。
- 標的　Home Depot
- 研究期限　2025-10-31
- 催化劑　11 月 12 日公布的第三季實績與全年指引，使緊接的 2024 財年第四季成為檢驗可比業務是否仍承壓的窗口。
- 預測　截至 2025-10-31，預期 Home Depot 第四季業績公告顯示 2024 財年第四季全公司可比銷售較上年同期下降。此指標可驗證銷售壓力是否延續，無法單獨量出費用分攤或獲利影響。
- 推翻條件　Home Depot 公布的 2024 財年第四季全公司可比銷售較上年同期持平或成長，即推翻該季銷售壓力延續的預測。
- 模型引文　fact:home-release:original、fact:home-release:quarter、fact:home-release:guidance

**待查**　SRS Distribution 併表與 Home Depot 可比銷售下滑同時出現，兩者的落差無法識別客戶是否轉移採購。要檢驗通路排擠，需公司揭露原有客戶轉向 SRS 的銷售額及原通路銷售變化，或取得非公開的跨通路配對交易紀錄。現有資料也未具名可追蹤的外部供應商或客戶。

**模型判讀**　全對。未提交連結。指出須比對原有客戶在 SRS 與 Home Depot 原通路的交易，並保留訂單移轉歸因。


### 純 Astra · 完成

[逐次回傳](raw/calls/H-08-astra.json) · [CLI 事件](raw/jobs/H-08-astra/events.jsonl) · [模型原始 JSON](raw/jobs/H-08-astra/answer.json) · [CLI 診斷](raw/jobs/H-08-astra/stderr.log) · [完整請求](raw/jobs/H-08-astra/request.json)

**研究首稿 · 觀望**

- 傳導機制　SRS 併表與第 53 週可推升全年合併銷售，即使可比銷售仍低於上年。第三季兩項指標已呈現相反方向，因此判斷既有業務是否回升，應追蹤後續季度的可比銷售。
- 標的　Home Depot 合併銷售與可比銷售
- 研究期限　先以 2024 財年全年實績檢驗，再追蹤至 2025-10-31 前已公告的季度。
- 催化劑　2024 財年全年業績，以及其後的季度可比銷售公告。
- 預測　預期 2024 財年合併銷售年增、可比銷售年減。公司指引分別為約增 4% 與約減 2.5%。
- 推翻條件　若全年合併銷售持平或下降，或全年可比銷售持平或上升，即推翻兩者走勢背離的預測。若全年預測成立，但其後可比銷售連續兩季年增，則應重新評估對既有業務復甦的觀望立場。
- 模型引文　home-release:quarter、home-release:guidance、home-release:baseline

**待查**　公告列出 SRS 的併表貢獻與 Home Depot 的可比銷售，但缺少收購前後同一批客戶在兩個通路的交易資料。即使 SRS 銷售增加、門市可比銷售下降，也無法據此判定 SRS 分流門市訂單，或為門市帶來交叉銷售。

**模型判讀**　全對。未提交連結。指出缺少收購前後同一批客戶的跨通路交易資料，並明確保留門市訂單分流歸因。


[逐次回傳](raw/calls/H-08-judge.json) · [CLI 事件](raw/jobs/H-08-judge/events.jsonl) · [模型原始 JSON](raw/jobs/H-08-judge/answer.json) · [CLI 診斷](raw/jobs/H-08-judge/stderr.log) · [完整請求](raw/jobs/H-08-judge/request.json)

## R-01 · Microsoft · 回歸

**研究題目**　Microsoft 公布多年期策略合作。請提出可供研究員覆核的首稿。

**截止**　2022-12-12T23:59:59+00:00　**研究期限**　2024-12-31

- `ms-lseg:contract`　London Stock Exchange Group（LSEG）與 Microsoft 簽十年合作。LSEG 對 Microsoft 的最低雲端相關支出承諾為十年合計 28 億美元。 [官方來源](https://news.microsoft.com/source/2022/12/12/lseg-and-microsoft-launch-10-year-strategic-partnership-for-next-generation-data-and-analytics-and-cloud-infrastructure-solutions-microsoft-to-make-equity-investment-in-lseg-through-acquisition-of-sh/)
- `ms-lseg:equity`　Microsoft 還擬取得 LSEG 約 4% 股份；持股交易與雲端服務使用是不同項目。 [官方來源](https://news.microsoft.com/source/2022/12/12/lseg-and-microsoft-launch-10-year-strategic-partnership-for-next-generation-data-and-analytics-and-cloud-infrastructure-solutions-microsoft-to-make-equity-investment-in-lseg-through-acquisition-of-sh/)
- `ms-lseg:migration`　LSEG 的資料平台與其他關鍵科技基礎設施會遷移至 Microsoft Azure。Workspace 與 Teams／Microsoft 365 另有整合計畫。 [官方來源](https://news.microsoft.com/source/2022/12/12/lseg-and-microsoft-launch-10-year-strategic-partnership-for-next-generation-data-and-analytics-and-cloud-infrastructure-solutions-microsoft-to-make-equity-investment-in-lseg-through-acquisition-of-sh/)
- `ms-lseg:original`　公告條列合約支出及雲端遷移原文：Contractual commitment by LSEG for minimum cloud-related spend with Microsoft [官方來源](https://news.microsoft.com/source/2022/12/12/lseg-and-microsoft-launch-10-year-strategic-partnership-for-next-generation-data-and-analytics-and-cloud-infrastructure-solutions-microsoft-to-make-equity-investment-in-lseg-through-acquisition-of-sh/)

**預註冊標準**　LSEG 遷移計畫和最低雲端支出契約連至 Azure／雲端服務需求。追蹤遷移、工作負載上線或合約履約，區分入股與一般 Azure 增長。28 億為十年最低支出，不能按年平均當成已認列收入。

### 新版 Harness V11 · 完成

[逐次回傳](raw/calls/R-01-ranked.json) · [CLI 事件](raw/jobs/R-01-ranked/events.jsonl) · [模型原始 JSON](raw/jobs/R-01-ranked/answer.json) · [CLI 診斷](raw/jobs/R-01-ranked/stderr.log) · [完整請求](raw/jobs/R-01-ranked/request.json)

**研究首稿 · 多方**

- 傳導機制　2022-12-12 簽署的十年最低支出承諾，配合指定遷往 Azure 的工作負載，為 Microsoft 帶來原環境延用時沒有的服務機會。正式上線並提供計費服務後，才可能認列相關收入。28 億美元涵蓋十年雲端相關支出，期間內 Azure 用量、單價及收入占比均未知。
- 標的　Microsoft
- 研究期限　2024-12-31
- 催化劑　簽約後首批 LSEG 資料平台或關鍵基礎設施切換至 Azure 正式環境。於 2024-12-31 前覆核雙方已發布的合作公告或 LSEG 業績資料。
- 預測　2022-12-12 至 2024-12-31，至少一項具名的 LSEG 資料平台或關鍵基礎設施工作負載在 Azure 正式運行，進度超過公告時的遷移計畫。
- 推翻條件　同一期間的雙方公告或 LSEG 業績資料明確確認，截至覆核日上述範圍的 Azure 正式工作負載仍為零。僅披露測試或欠缺更新，結果未定。
- 模型引文　fact:ms-lseg:contract、fact:ms-lseg:original、fact:ms-lseg:migration

**研究首稿 · 空方**

- 傳導機制　合作另為 Microsoft 新增 Workspace 與 Teams 的跨產品整合工作。若正式推出前的驗證延長，Microsoft 須持續投入整合資源，可供客戶使用的新功能則延後。相較維持既有產品，增加的工程投入與延後的商業效益均缺工時、定價及席次可供估算。
- 標的　Microsoft
- 研究期限　2024-12-31
- 催化劑　簽約後首次對外展示或試用 Workspace 與 Teams 整合功能時，追蹤同一功能的正式供應狀態，至 2024-12-31 覆核 Microsoft 或 LSEG 的產品公告。
- 預測　在 2022-12-12 至 2024-12-31 的公開產品更新中，首項具名展示或試用的 Workspace 與 Teams 整合功能，到覆核時仍明列為測試、預覽或限受邀試用。
- 推翻條件　Microsoft 或 LSEG 在同一期間確認該首項功能已正式供應符合資格的客戶。未見具名功能或最新供應狀態，則無法判定。
- 模型引文　fact:ms-lseg:migration

**1. Microsoft Azure → LSEG · 資料平台**

- 起點引文　ms-lseg:migration、ms-lseg:contract
- 受影響業務引文　ms-lseg:migration、ms-lseg:contract
- 傳導機制　LSEG 已承諾十年最低雲端相關支出。若資料平台遷移時仍須維持舊環境，Microsoft 取得正式工作負載的同時，LSEG 可能開始負擔新舊平台並行成本。
- 比較基準　若未遷移，LSEG 延續原平台營運，沒有本案新增的 Azure 並行環境。
- 必要條件　同一批正式工作負載在 Azure 上線後，舊環境仍為遷移或驗證而運作並發生成本。
- 財務影響　並行期可能推高 LSEG 資料平台營運成本。28 億美元是十年總支出下限，估算增量成本仍缺平台分攤額、並行期間及舊環境可節省的費用。
- 其他解釋　LSEG 科技支出也可能因其他基礎設施投資增加。須由 LSEG 指明同一批工作負載的新舊環境運作期間，才能辨別本案影響。
- 查核指標　LSEG 資料平台已遷移工作負載的新舊正式環境是否有並行期。
- 觀察期間　2022-12-12 至 2024-12-31 之間已公開的切換進度。
- 公開查核來源　LSEG 期間內已發布的業績簡報、年報或與 Microsoft 的遷移進度公告。
- 截止日　2024-12-31
- 預測　若資料平台已有正式工作負載切換，LSEG 披露其中至少一批曾在新舊環境並行。
- 推翻條件　LSEG 明確披露期間內所有已切換批次均在 Azure 正式啟用時或之前停用對應舊環境。尚未切換或未說明停用時間，則仍待驗證。

**待查**　Workspace 與 Teams／Microsoft 365 的整合已有計畫，尚缺授權條款、付費席次或通路分成，無法另立可驗證的收入傳導。約 4% 持股仍屬擬議交易，缺成交對價及與業務配置連動的證據。

- 第 1 條排序理由　列首位因最低支出與遷移對象均已具名，LSEG 的切換紀錄可同時檢驗 Azure 採用及客戶端成本風險。

**模型判讀**　未全對。缺口指出整合授權、付費席次、分成及持股與業務配置連動的證據仍待補足。

主要傳導位置　未選入。全項通過位置　無。

- 候選 1　四項語義均通過。公告支持 LSEG 遷移至 Azure 與十年最低支出承諾。此連結衡量 LSEG 資料平台的並行成本，主路徑要求衡量遷移帶來的 Azure 需求。並行成本以同批工作負載新舊環境同時運作並產生成本為條件。若 LSEG 期內確認所有已切換批次的舊環境均於 Azure 上線時或之前停用，即可排除這項並行成本機制。

### 現版 Harness V10 · 完成

[逐次回傳](../linkage-depth/raw/calls/H-01-harness.json) · [CLI 事件](../linkage-depth/raw/jobs/H-01-harness/events.jsonl) · [模型原始 JSON](../linkage-depth/raw/jobs/H-01-harness/answer.json) · [CLI 診斷](../linkage-depth/raw/jobs/H-01-harness/stderr.log) · [完整請求](../linkage-depth/raw/jobs/H-01-harness/request.json)

**研究首稿 · 多方**

- 傳導機制　若依約將原先未在 Azure 運行的 LSEG 正式工作負載遷入，Microsoft 可較無此遷移時增加雲端服務用量，並隨服務履行認列收入。十年最低雲端相關支出涵蓋的服務、年度分布及既有支出均未拆分，無法估算期內新增 Azure 營收。
- 標的　Microsoft
- 研究期限　2024-12-31
- 催化劑　2022-12-12 公布遷移計畫後，首項 LSEG 資料平台或其他關鍵基礎設施在 Azure 進入正式運行。
- 預測　於 2024-12-31 前查核 Microsoft 或 LSEG 自簽約以來的合作更新，預期至少一項上述工作負載獲確認已在 Azure 正式運行。這可驗證交付進度，無法量出新增用量或已認列收入。
- 推翻條件　若雙方任一方公開確認截至 2024-12-31，上述工作負載全數仍在測試或尚待遷移，或首次正式運行已排至期後，即推翻期內上線判斷。未披露進度則未決。
- 模型引文　fact:ms-lseg:contract、fact:ms-lseg:original、fact:ms-lseg:migration

**研究首稿 · 空方**

- 傳導機制　合作另增加 Workspace 與 Teams 的整合開發及支援工作。若 Microsoft 已投入工程資源，而整合功能長期停留在試用階段，相較無此專案時，Microsoft 會先承擔執行成本，能藉正式產品擴大使用的時間則後移。工程投入、收費安排及原定時程均未揭露，無法估算利潤影響或認定違約延誤。
- 標的　Microsoft
- 研究期限　2024-12-31
- 催化劑　2022-12-12 公布整合計畫後，Workspace 與 Teams 整合功能進入試用，面臨是否正式開放的交付關卡。
- 預測　以 2024-12-31 為覆核期限，預期 Microsoft 或 LSEG 的產品公告可確認期內已有試用，但截至期末，該整合仍僅限試用。產品狀態可檢驗執行風險，專案成本仍須另查。
- 推翻條件　若 Microsoft 或 LSEG 的產品公告確認，至少一項同一整合功能已於 2024-12-31 前結束僅限試用的狀態，正式開放外部客戶使用，即推翻期末仍僅限試用的判斷。公告沉默無法判定。
- 模型引文　fact:ms-lseg:migration

**1. Teams → LSEG · Workspace**

- 起點引文　ms-lseg:migration
- 受影響業務引文　ms-lseg:migration
- 傳導機制　雙方已公布整合計畫。若 LSEG 將 Workspace 功能透過 Teams 正式交付給外部客戶，合作便在 Azure 遷移之外，另為 LSEG 增加一個產品使用入口。
- 比較基準　截至 2022-12-12，公告僅列整合計畫。若未推進整合，Workspace 客戶仍循既有入口使用服務。
- 必要條件　雙方須完成整合並開放外部客戶使用。客戶還須因此新增付費席位或續約，才有營收效益。
- 財務影響　若新入口帶來原本不會發生的付費或續約，LSEG 的 Workspace 營收可增加。缺少可使用席位、付費轉換及定價資料，無法估算金額。
- 其他解釋　既有客戶也可能只把相同用量移至 Teams。可由 LSEG 對新增付費席位或續約原因的公開說明區分，單憑功能上線無法判定。
- 查核指標　LSEG 的 Workspace 發布說明中，Teams 整合功能的對外開放狀態。這是通路交付的代理指標，無法歸因席位或營收。
- 觀察期間　2022-12-12 公告後至 2024-12-31，以期內最後一次明確說明功能狀態的更新覆核。
- 公開查核來源　LSEG 的 Workspace 產品公告或雙方合作進度公告。
- 截止日　2024-12-31
- 預測　期內公告確認至少一項 Workspace 整合功能已透過 Teams 正式提供給外部客戶，支持合作已延伸至產品通路。
- 推翻條件　涵蓋期末狀態的公開更新確認同一整合仍全數限於試用、已取消，或首次正式開放時間落在期後。缺少更新則維持未決。

**待查**　Azure 遷移與 Workspace 整合同列於公告，但未揭露共用工程人力、預算或資源調度，無法判定一案是否排擠另一案。亦缺 Teams 或 Microsoft 365 因整合而新增付費的資料。

**模型判讀**　未全對。缺口具體指出缺少共用人力、預算、資源調度及新增付費證據，並保留對資源排擠的判斷。

主要傳導位置　未選入。全項通過位置　無。

- 候選 1　四項語義均通過。公告支持 Teams 與 LSEG Workspace 的整合計畫。此連結追蹤 Teams 對外提供 Workspace 功能及其對 LSEG 營收的可能影響，主路徑要求追蹤 Azure 需求。LSEG 產品公告若確認期末仍全數限於試用，即可推翻期內正式交付。正式上線只能驗證通路，增收仍須有因整合而新增的付費或續約。

### 純 Astra · 完成

[逐次回傳](../linkage-depth/raw/calls/H-01-astra.json) · [CLI 事件](../linkage-depth/raw/jobs/H-01-astra/events.jsonl) · [模型原始 JSON](../linkage-depth/raw/jobs/H-01-astra/answer.json) · [CLI 診斷](../linkage-depth/raw/jobs/H-01-astra/stderr.log) · [完整請求](../linkage-depth/raw/jobs/H-01-astra/request.json)

**研究首稿 · 觀望**

- 傳導機制　LSEG 的十年支出承諾提高 Microsoft 對該客戶長期需求的可見度。要上修截至 2024 年底的獲利預估，仍須知道期內交付多少服務、其中多少屬新增採購，以及交付成本。
- 標的　Microsoft 截至 2024 年底的雲端營收與營業利益預估
- 研究期限　2024-12-31
- 催化劑　LSEG 揭露首批正式遷移的時間、範圍與相關支出，或 Microsoft 量化合作帶來的當期財務貢獻。
- 預測　預期到 2024 年底，研究員較能從公開資料核實遷移里程碑，仍難單憑十年承諾推算期內營業利益。
- 推翻條件　若雙方揭露足以區分原有採購與新增用量的分期金額，且提供相應成本或利潤貢獻，便可量化期內影響並重新評估觀望立場。
- 模型引文　ms-lseg:contract、ms-lseg:original、ms-lseg:migration

**1. LSEG 資料平台與關鍵科技基礎設施 → Microsoft · Azure 雲端基礎設施服務**

- 起點引文　ms-lseg:migration、ms-lseg:contract
- 受影響業務引文　ms-lseg:migration、ms-lseg:original
- 傳導機制　LSEG 將正式營運的工作負載遷至 Azure 後，持續運作所需的運算與儲存服務可帶動 Microsoft 的計費用量。
- 比較基準　截至 2022 年 12 月 12 日，公告揭露遷移計畫及十年最低雲端相關支出承諾。LSEG 原有 Azure 用量與已上線工作負載數量均未知。
- 必要條件　至少一項資料平台或關鍵基礎設施在觀察期內進入正式營運，且帶來超過原有水準的 Azure 計費用量。
- 財務影響　新增用量可隨服務交付貢獻 Microsoft 雲端營收。貢獻金額取決於實際用量與定價，對營業利益的影響還取決於服務成本。
- 其他解釋　LSEG 原有的 Microsoft 雲端採購若可計入最低承諾，即使履約支出增加，新增 Azure 營收仍可能遠低於承諾總額。
- 查核指標　LSEG 或 Microsoft 公開確認已在 Azure 正式營運的具名工作負載數，以及雙方若有揭露的相關用量或支出變化。
- 觀察期間　2022 年 12 月 13 日至 2024 年 12 月 31 日
- 公開查核來源　LSEG 與 Microsoft 的合作進度公告、財報及業績簡報
- 截止日　2024-12-31
- 預測　預期截至 2024 年底，至少一方會確認一項具名工作負載已在 Azure 正式營運。這可驗證遷移進度，營收增量仍須用量或支出資料佐證。
- 推翻條件　若雙方明確表示全部正式遷移已延至 2024 年後，或揭露遷移後相關計費用量未增加，則期內帶動新增用量的假設失效。單純缺乏披露只能列為未驗證。

**待查**　Workspace 與 Teams／Microsoft 365 的整合仍屬計畫。付費方式、採用基準與收入歸屬均待揭露，因此無法估算這項整合對任一方的新增營收。

**模型判讀**　全對。履約承諾與營收增量的區分恰當。整合缺口具體指出付費方式、採用基準及收入歸屬待揭露。

主要傳導位置　1。全項通過位置　1。

- 候選 1　四項語義均通過。LSEG 資料平台或關鍵基礎設施遷入 Azure 正式營運後，若計費用量高於原有水準，可隨服務交付增加 Microsoft 雲端營收。雙方期內公告可用具名負載驗證上線。若披露上線後計費用量持平，即可區分遷移落地與新增用量。

[逐次回傳](raw/calls/R-01-judge.json) · [CLI 事件](raw/jobs/R-01-judge/events.jsonl) · [模型原始 JSON](raw/jobs/R-01-judge/answer.json) · [CLI 診斷](raw/jobs/R-01-judge/stderr.log) · [完整請求](raw/jobs/R-01-judge/request.json)

## R-02 · lululemon · 回歸

**研究題目**　lululemon 公布新的多年合作。請提出可供研究員覆核的首稿。

**截止**　2023-09-27T23:59:59+00:00　**研究期限**　2024-12-31

- `lulu-pton:original`　聯合公告的合作交換與會員段落原文：Peloton will become the exclusive digital fitness content provider for lululemon [官方來源](https://corporate.lululemon.com/newsroom/press-releases/2023/09-27-2023-211026323)
- `lulu-pton:sales`　聯合公告描述以 Peloton 通路推出共同品牌服飾與相關計畫。此屬通路與供應安排。 [官方來源](https://corporate.lululemon.com/newsroom/press-releases/2023/09-27-2023-211026323)
- `lulu-pton:subscription`　從 2023 年 11 月 1 日起，lululemon Studio All-Access 會員會按當時同價取得 Peloton 課程。 [官方來源](https://corporate.lululemon.com/newsroom/press-releases/2023/09-27-2023-211026323)
- `lulu-pton:terms`　lululemon 與 Peloton 公布五年合作。Peloton 成為 lululemon 的獨家數位健身內容供應商，lululemon 成為 Peloton 主要運動服飾合作夥伴。 [官方來源](https://corporate.lululemon.com/newsroom/press-releases/2023/09-27-2023-211026323)

**預註冊標準**　可選 Peloton 內容導入 Studio 與內容成本或會員留存，或 Peloton 的具名服飾通路連到 lululemon 增量銷售。查同價上線／可購服飾／新通路銷售，區分其他會員變動、季節折扣或原有服飾通路移轉；缺分潤或成本時只主張條件影響。

### 新版 Harness V11 · 完成

[逐次回傳](raw/calls/R-02-ranked.json) · [CLI 事件](raw/jobs/R-02-ranked/events.jsonl) · [模型原始 JSON](raw/jobs/R-02-ranked/answer.json) · [CLI 診斷](raw/jobs/R-02-ranked/stderr.log) · [完整請求](raw/jobs/R-02-ranked/request.json)

**研究首稿 · 多方**

- 傳導機制　相較維持原通路，主要運動服飾夥伴安排可讓 lululemon 透過 Peloton 接觸購衣者。若共同品牌服飾上架並產生增量購買，才有服飾收入上行空間。上架可驗證通路開通，訂單、交付、銷量及收入認列仍各需證據。
- 標的　lululemon
- 研究期限　2024-12-31
- 催化劑　2023 年 9 月 27 日聯合公告後，觀察 Peloton 首次公開販售共同品牌服飾。
- 預測　自公告日至 2024 年 12 月 31 日，Peloton 官方商店或雙方上市公告至少一次顯示共同品牌服飾已開賣，達成公告前尚待推出的通路里程碑。
- 推翻條件　截至同一截止日，雙方公開確認該服飾計畫在觀察期內尚未開賣，或已於開賣前取消。單次查無商品無法判定。
- 模型引文　fact:lulu-pton:sales、fact:lulu-pton:terms

**研究首稿 · 空方**

- 傳導機制　維持原會員方案無須接入新的獨家內容供應商。此次合作須讓既有會員按原價取得 Peloton 課程，若接入延後，lululemon 將無法如期提供新增權益，可能增加客服負擔及續訂風險。受影響會員數與續訂率未披露。
- 標的　lululemon
- 研究期限　2024-12-31
- 催化劑　公告排定 2023 年 11 月 1 日向 lululemon Studio All-Access 會員提供同價課程權益。
- 預測　以 2023 年 11 月 1 日為基準，至 2024 年 12 月 31 日查核 lululemon 或 Peloton 的會員說明及公告，預期可確認既有會員按原價取得課程的實際接入日晚於排定日。
- 推翻條件　雙方任一方的具日期說明確認，既有 All-Access 會員在 2023 年 11 月 1 日已可按原價取得 Peloton 課程。缺少上線紀錄時，結果仍待查。
- 模型引文　fact:lulu-pton:original、fact:lulu-pton:subscription、fact:lulu-pton:terms

**1. lululemon Studio All-Access → Peloton · Peloton 課程**

- 起點引文　lulu-pton:subscription
- 受影響業務引文　lulu-pton:subscription、lulu-pton:terms
- 傳導機制　五年獨家安排讓 Peloton 課程可透過 lululemon 接觸既有付費會員。若接入延後，lululemon 的會員方案會出現執行落差，Peloton 也會延後取得這個分發通路。
- 比較基準　無合作時，既有方案沒有公告所述的 Peloton 課程權益。合作排定的接入日為 2023 年 11 月 1 日。
- 必要條件　雙方須完成方案接入，既有會員才可按原價取得課程。Peloton 的收入是否隨接入增加，另取決於合約計價方式。
- 財務影響　若 Peloton 按服務上線或使用量收費，延期會推遲相關收入。五年是合作期限，授權費、付費會員數及最低付款額均未披露。
- 其他解釋　部分會員可能自行訂閱 Peloton。查核雙方會員說明是否明載既有方案已包含課程，可區分合作接入與會員自行購買。
- 查核指標　截至排定日期，既有 All-Access 會員能否按原價透過該方案取得 Peloton 課程。
- 觀察期間　2023 年 11 月 1 日的服務狀態，並追查其後公布的實際接入日。
- 公開查核來源　lululemon 與 Peloton 的會員服務說明、上線或延期公告。
- 截止日　2024-12-31
- 預測　若主案的接入延遲成立，雙方服務說明或後續公告可確認實際接入日晚於 2023 年 11 月 1 日。
- 推翻條件　任一方具日期的會員說明確認，既有 All-Access 會員於 2023 年 11 月 1 日已可按原價取得課程。

**待查**　服飾合作直接涉及 Peloton 的零售通路，但商品上架已是主案觀察項。若要另判斷 Peloton 的零售獲利或既有服飾遭排擠，仍缺進貨或分潤條款、銷量及品類組合。公告亦未指明 lululemon 將人力或預算移往哪個業務。

- 第 1 條排序理由　此項居首，因獨家供應安排直接指定會員群、價格條件與接入日，公開服務狀態可檢驗雙方是否履約。

**模型判讀**　未全對。缺口誤稱主案已追蹤服飾上架，所列獲利缺口也落在 Peloton 零售端。

主要傳導位置　未選入。全項通過位置　無。

- 候選 1　四項語義均通過。公告支持 Studio 會員預定同價取得 Peloton 課程。若接入延後且 Peloton 按上線或用量收費，其收入可能遞延。具日期的官方會員說明可驗證是否如期接入，並區分方案權益與自行訂閱。財務終點在 Peloton，未觸及 lululemon 的內容成本、留存或服飾增量銷售。

### 現版 Harness V10 · 完成

[逐次回傳](../linkage-depth/raw/calls/H-07-harness.json) · [CLI 事件](../linkage-depth/raw/jobs/H-07-harness/events.jsonl) · [模型原始 JSON](../linkage-depth/raw/jobs/H-07-harness/answer.json) · [CLI 診斷](../linkage-depth/raw/jobs/H-07-harness/stderr.log) · [完整請求](../linkage-depth/raw/jobs/H-07-harness/request.json)

**研究首稿 · 多方**

- 傳導機制　相較未簽約情境，聯名安排可讓 lululemon 在 Peloton 通路新增可購買的服飾。若帶來增量銷售且毛利足以覆蓋通路費用，才會增加獲利。上架僅驗證通路落地，訂單、交貨、終端成交與 lululemon 認列收入仍須分別查證。
- 標的　lululemon
- 研究期限　2024-12-31
- 催化劑　2023-09-27 聯合公告提出由 Peloton 通路推出共同品牌服飾，未載明上架日。自公告後至研究截止日查核 Peloton 官方商店及雙方上市公告。
- 預測　截至 2024-12-31，至少一款本次合作的 lululemon 聯名服飾曾在 Peloton 官方通路開放購買，以有日期的可購商品頁或官方開賣說明驗證。
- 推翻條件　若 lululemon 或 Peloton 明確確認截至 2024-12-31 該通路實際開賣款數為零，則推翻。單次查無商品頁無法排除先前曾經開賣。
- 模型引文　fact:lulu-pton:sales、fact:lulu-pton:terms

**研究首稿 · 空方**

- 傳導機制　獨家內容安排使 lululemon 對會員新增一項有起始日、須由 Peloton 配合交付的服務承諾。若課程接入延後，會員將無法如期取得公告權益，可能增加客服負擔及續訂風險。未簽約時並無這次接入期限，受影響人數及續訂損失未知。
- 標的　lululemon
- 研究期限　2024-12-31
- 催化劑　公告訂於 2023-11-01 起讓 Studio All-Access 會員按當時同價取得 Peloton 課程。查核生效日前後的 lululemon 官方會員公告及後續合作更新。
- 預測　預期 All-Access 會員正式取得公告所述課程的生效日晚於 2023-11-01。以 lululemon 公開延後通知或載有實際啟用日的會員說明核對，最遲於 2024-12-31 覆核。
- 推翻條件　若 lululemon 的會員服務說明或合作更新確認同一批 All-Access 會員已於 2023-11-01 或更早取得該課程權益，即推翻延誤假設。重述預定日期或未發布更新均不足以判定。
- 模型引文　fact:lulu-pton:original、fact:lulu-pton:subscription、fact:lulu-pton:terms

**1. digital fitness content → lululemon · lululemon Studio All-Access**

- 起點引文　lulu-pton:original
- 受影響業務引文　lulu-pton:subscription
- 傳導機制　若獨家課程接入延誤，且 lululemon 因此向受影響會員提供帳單抵免，內容交付問題就會傳至訂閱收費。
- 比較基準　公告安排自 2023-11-01 起按當時同價提供課程。若如期接入，便沒有因這次延誤而補償的理由。
- 必要條件　須先確認接入延誤，再確認 lululemon 決定就該延誤抵免會費。延誤本身不會自動降低收費。
- 財務影響　抵免會降低適用會員當期應付會費。總額取決於抵免金額、適用人數及期數，三者均未披露。
- 其他解釋　一般促銷也可能降低會費。核對會員通知是否把抵免事由及適用對象明訂為受轉換延誤影響的會員。
- 查核指標　受影響 All-Access 會員在延誤所涉帳期，公開收費條款所列的延誤抵免額是否大於零。
- 觀察期間　2023-11-01 至 2024-12-31，查核期間內已出具公開收費說明的受影響帳期。
- 公開查核來源　lululemon 官方 Studio 會員服務公告、公開收費條款或合作更新。
- 截止日　2024-12-31
- 預測　若出現接入延誤，預期 lululemon 公開列明至少一個受影響帳期有正額延誤抵免。
- 推翻條件　若已確認延誤，且 lululemon 公開說明同批會員在所涉帳期均照原額收費、延誤抵免為零，則推翻收費傳導。若無公開帳務說明，結果待查。

**待查**　公告沒有揭露獨家內容費用、自製內容成本或預算去向，無法檢驗節省的資源是否轉投服飾。會員抵免也只是條件情境，公開條款最多可驗證收費安排，實際入帳總額仍需公司披露或非公開帳務紀錄。

**模型判讀**　未全對。缺口指出內容成本及預算去向未披露，並保留對資源轉投服飾及實際抵免總額的判斷。

主要傳導位置　未選入。全項通過位置　無。

- 候選 1　四項語義均通過。公告支持 Peloton 獨家供應與 Studio 預定同價接入。延誤及抵免均為條件，抵免會降低適用會員當期應付會費。官方同帳期條款可區分延誤抵免與一般促銷。帳單抵免未觸及指定的留存、內容成本或服飾增量銷售。

### 純 Astra · 完成

[逐次回傳](../linkage-depth/raw/calls/H-07-astra.json) · [CLI 事件](../linkage-depth/raw/jobs/H-07-astra/events.jsonl) · [模型原始 JSON](../linkage-depth/raw/jobs/H-07-astra/answer.json) · [CLI 診斷](../linkage-depth/raw/jobs/H-07-astra/stderr.log) · [完整請求](../linkage-depth/raw/jobs/H-07-astra/request.json)

**研究首稿 · 觀望**

- 傳導機制　五年合作同時改變服飾銷售通路與會員課程供應。前者的獲利取決於新增訂單及毛利，後者取決於留存改善能否覆蓋內容成本。
- 標的　lululemon 的合作相關營業利益
- 研究期限　2024-12-31
- 催化劑　2023 年 11 月 1 日預定導入 Peloton 課程、共同品牌服飾首批上市，以及其後對續訂與補單的揭露。
- 預測　若合作按計畫推進，應先看到既有會員同價取得課程及共同品牌服飾上架。單憑這兩項進度，仍不足以調高 lululemon 獲利估計。
- 推翻條件　若公司揭露可歸因於合作的重大營業利益增益或拖累，並說明計算涵蓋的收入與成本，即可結束觀望並依方向修正估計。
- 模型引文　lulu-pton:terms、lulu-pton:sales、lulu-pton:subscription

**1. Peloton 的服飾銷售通路 → lululemon · 共同品牌運動服飾的銷售與毛利**

- 起點引文　lulu-pton:sales
- 受影響業務引文　lulu-pton:terms、lulu-pton:sales
- 傳導機制　Peloton 通路若能觸及原先不會向 lululemon 購買服飾的消費者，首批商品售出後的補單可為 lululemon 帶來新增收入。
- 比較基準　公告確認 lululemon 將成為 Peloton 的主要運動服飾合作夥伴，並揭露上市計畫。首批訂單、售價及毛利率均待查證。
- 必要條件　Peloton 通路須帶來新增需求，且新增毛利足以抵銷既有通路因訂單轉移而減少的毛利。
- 財務影響　若條件成立，lululemon 服飾毛利額可增加。供貨價格、銷售規模及通路移轉幅度未知，無法估算金額。
- 其他解釋　既有 lululemon 顧客可能改在 Peloton 購買。即使聯名商品補貨，公司整體服飾毛利也可能持平或下降。
- 查核指標　首批上市後的補貨或追加訂單，以及公司可歸因於此合作的新增銷售與毛利。
- 觀察期間　2023 年 9 月 27 日公告後至 2024 年 12 月 31 日
- 公開查核來源　Peloton 官方商品頁、雙方後續合作公告及 lululemon 財報說明會。
- 截止日　2024-12-31
- 預測　若新增需求持續，首批上市後應能觀察到補貨或追加訂單。若公司另行揭露合作帶來的新增毛利為正，即可支持獲利假說。
- 推翻條件　若雙方確認取消上市，或 lululemon 揭露通路移轉造成的毛利減少已抵銷合作貢獻，則此增益假說失效。僅有上架紀錄時，獲利效果仍待驗證。

**2. Peloton 數位健身課程供應 → lululemon · lululemon Studio All-Access 會員訂閱**

- 起點引文　lulu-pton:original、lulu-pton:terms
- 受影響業務引文　lulu-pton:subscription
- 傳導機制　既有會員若認為同價可取得的 Peloton 課程值得續訂，lululemon 可藉由延長付費月份保留訂閱收入。
- 比較基準　公告預定自 2023 年 11 月 1 日起按當時同價提供課程。供應資料未列出導入前的續訂率。
- 必要條件　新增課程須能留住原本會退訂的會員，且保留收入須高於新增內容及履約成本，才會改善獲利。
- 財務影響　同價條件下，既有會員收入的改善來自付費月份增加。淨利方向仍取決於支付給 Peloton 的費用及其他履約成本。
- 其他解釋　續訂率也可能隨會員年資或季節變動。單看導入前後的整體會員數，無法辨認課程效果。
- 查核指標　可比年資 All-Access 會員的續訂率、付費月份，以及每名會員的內容成本。
- 觀察期間　以 2023 年 11 月 1 日預定導入日為界，比較導入前後可比期間，追蹤至 2024 年 12 月 31 日。
- 公開查核來源　lululemon Studio 會員公告、lululemon 定期財報及財報說明會。
- 截止日　2024-12-31
- 預測　若課程提升留存，可比會員導入後的續訂率應高於導入前，並帶來較多付費月份。
- 推翻條件　若可比會員續訂率及付費月份均未改善，則留存假說缺乏支持。若新增成本超過保留收入，則獲利改善假說失效。

**待查**　兩條業務連結均來自同一份公告。服飾端缺少訂單與通路別毛利，訂閱端缺少可比會員留存與內容費用，尚無法判斷哪一端對 lululemon 獲利較重要。

**模型判讀**　全對。缺口指出服飾訂單與通路毛利、可比會員留存及內容費用均待查，未判定哪一端的獲利貢獻較大。

主要傳導位置　1。全項通過位置　1。

- 候選 1　四項語義均通過。公告支持 Peloton 通路推出 lululemon 聯名服飾。新增需求可帶動追加訂單與銷售，毛利增益須扣除既有通路移轉的影響。期內官方公告確認取消上市或 lululemon 揭露移轉已抵銷毛利，均可推翻增益假說。補貨僅能驗證通路進展。
- 候選 2　四項語義均通過。公告支持 Peloton 課程預定同價導入 Studio。若留住原本會退訂的會員，lululemon 可增加付費月份，獲利仍取決於成本。期內財報或法說若揭露可比年資會員的續訂率與付費月份均未改善，可反駁留存假說，並排除年資組合差異這項解釋。

[逐次回傳](raw/calls/R-02-judge.json) · [CLI 事件](raw/jobs/R-02-judge/events.jsonl) · [模型原始 JSON](raw/jobs/R-02-judge/answer.json) · [CLI 診斷](raw/jobs/R-02-judge/stderr.log) · [完整請求](raw/jobs/R-02-judge/request.json)

## R-03 · FedEx · 回歸

**研究題目**　FedEx 董事會公告事業組合決定。請提出可供研究員覆核的首稿。

**截止**　2024-12-19T23:59:59+00:00　**研究期限**　2025-12-31

- `fdx-sep:capital`　公告描述以資本市場方式推動分離，預期符合美國聯邦所得稅免稅分離資格，未量化母公司實收款或指定其用途。 [官方來源](https://newsroom.fedex.com/newsroom/global-english/fedex-announces-intent-to-separate-fedex-freight-creating-two-industry-leading-public-companies)
- `fdx-sep:decision`　FedEx 董事會擬分拆 FedEx Freight，使其成為獨立上市公司。當時目標為 18 個月內完成，須待後續條件及核准。 [官方來源](https://newsroom.fedex.com/newsroom/global-english/fedex-announces-intent-to-separate-fedex-freight-creating-two-industry-leading-public-companies)
- `fdx-sep:original`　Transaction Process 段落原文：expected to qualify as a tax-free separation [官方來源](https://newsroom.fedex.com/newsroom/global-english/fedex-announces-intent-to-separate-fedex-freight-creating-two-industry-leading-public-companies)
- `fdx-q2:original`　同期財報標題重點原文：$1 Billion Share Repurchases Completed During Quarter [官方來源](https://newsroom.fedex.com/newsroom/global-english/fedex-reports-second-quarter-diluted-eps-of-3-03-and-adjusted-diluted-eps-of-4-05)
- `fdx-q2:repurchases`　同期財報說本季已完成 10 億美元回購。該數字是本季已發生事項。 [官方來源](https://newsroom.fedex.com/newsroom/global-english/fedex-reports-second-quarter-diluted-eps-of-3-03-and-adjusted-diluted-eps-of-4-05)

**預註冊標準**　分拆計畫並不確立實收現金或回購、航空／其他業務資金去向。需要分拆資本結構、現金或分配條款、董事會用途與流量日期。已完成回購不得歸因於未完成交易。

### 新版 Harness V11 · 完成

[逐次回傳](raw/calls/R-03-ranked.json) · [CLI 事件](raw/jobs/R-03-ranked/events.jsonl) · [模型原始 JSON](raw/jobs/R-03-ranked/answer.json) · [CLI 診斷](raw/jobs/R-03-ranked/stderr.log) · [完整請求](raw/jobs/R-03-ranked/request.json)

**研究首稿 · 多方**

- 傳導機制　若董事會推進分拆並將 FedEx Freight 的投資決策權交由專責管理層，相較維持母公司原有審批方式，貨運業務可自行依營運需求排序投資。權責移轉是可檢驗的營運結果，節省的審批時間與投資報酬仍缺基準。
- 標的　FedEx
- 研究期限　2025-12-31
- 催化劑　2024-12-19 董事會公布分拆意向後，觀察 FedEx 在籌備期發布的治理安排。18 個月是完成目標，期內移轉權責是研究假設。
- 預測　截至 2025-12-31，FedEx 的分拆進度公告或公開申報將顯示，FedEx Freight 管理層已取得至少一項原由母公司核定的投資決策權。僅公布未來職稱或規劃，仍待驗證。
- 推翻條件　若 FedEx 公告或申報明示，截至 2025-12-31，FedEx Freight 的投資核准權仍全數維持公告前安排，即否證期內移轉假設。未披露權限歸屬則無法判定。
- 模型引文　fact:fdx-sep:decision、unverified_impact

**研究首稿 · 空方**

- 傳導機制　若 FedEx 為籌備獨立上市而新增法律、會計等費用，相較不啟動分拆，當期認列的增量費用會壓低合併營業利益。公告未提供費用預算、認列時點或抵銷金額。
- 標的　FedEx
- 研究期限　2025-12-31
- 催化劑　2024-12-19 公告後若啟動分拆準備，於其後至 2025-12-31 已發布的 FedEx 季報、年報及財報附註核對費用認列。
- 預測　就公告後至 2025-12-31 前已公布財報涵蓋的期間，FedEx 將揭露至少一期認列正額、明確歸屬 FedEx Freight 分拆的營業費用。總部費用增加不足以單獨歸因。
- 推翻條件　若 FedEx 明示同一組已公布報告期間內，歸屬該分拆的合併營業費用累計為零，即否證期內費用假設。未單列金額則維持未決。
- 模型引文　fact:fdx-sep:decision、unverified_impact

**待查**　同期已完成的 10 億美元回購有財報可核，但分拆公告未量化 FedEx 可收取的現金，也未指定用途。要連結分拆與後續回購或其他業務投資，須見分拆文件列出母公司可得款項，以及董事會或財報揭露相應配置。現有資料亦未指明其他業務承接人員、資產或客戶的安排。

**模型判讀**　全對。確認 10 億美元回購已完成，並以分拆文件載明母公司可得款項及後續公開披露資金配置，作為歸因於分拆的前提。


### 現版 Harness V10 · 完成

[逐次回傳](../linkage-depth/raw/calls/H-06-harness.json) · [CLI 事件](../linkage-depth/raw/jobs/H-06-harness/events.jsonl) · [模型原始 JSON](../linkage-depth/raw/jobs/H-06-harness/answer.json) · [CLI 診斷](../linkage-depth/raw/jobs/H-06-harness/stderr.log) · [完整請求](../linkage-depth/raw/jobs/H-06-harness/request.json)

**研究首稿 · 多方**

- 傳導機制　若董事會的分拆決定促使 FedEx 在交易完成前把投資決策權下放給 FedEx Freight，貨運業務即可自行安排投資優先順序。相對於維持公告前的授權安排，營運改善在於決策自主性提高。原有權限、審批時間及投資報酬均未揭露，獲利改善幅度仍待驗證。
- 標的　FedEx
- 研究期限　2025-12-31
- 催化劑　2024-12-19 董事會宣布擬分拆後，觀察 FedEx 在研究期內公布的過渡治理安排。18 個月是附條件的完成目標，超出本研究期。
- 預測　截至 2025-12-31，FedEx 的分拆進度公告或監管申報將確認，FedEx Freight 已取得至少一項原須母公司核准的資本支出決策權。可覆核的里程碑是授權範圍與生效時間，單憑主管任命不足以判定。
- 推翻條件　若 FedEx 公開確認，自公告日至 2025-12-31，FedEx Freight 的資本支出仍全數沿用公告前的核准權限，則期內授權假設失效。若只披露未來治理規劃，結果待定。
- 模型引文　fact:fdx-sep:decision

**研究首稿 · 空方**

- 傳導機制　推動獨立上市可能使 FedEx 在分拆前先行負擔法律、會計或系統拆分費用。相對於維持原架構，若新增支出列為當期營業費用，即會壓低集團營業利益。預期符合免稅資格僅涉及交易稅務，公告未估計執行費用。
- 標的　FedEx
- 研究期限　2025-12-31
- 催化劑　2024-12-19 宣布啟動分拆籌備後，檢查公告後首個完整財季起、截至 2025-12-31 已發布的 FedEx 季度業績及監管申報。
- 預測　在上述已報告財季中，FedEx 至少一季確認已將可歸因於 FedEx Freight 分拆的正額費用計入集團營業利益。若只列合併重整費用，無法辨識分拆的影響金額。
- 推翻條件　若 FedEx 明確確認上述同一組已報告財季的分拆相關營業費用合計為零，則期內費用假設失效。未單列費用時，歸因仍待查。
- 模型引文　fact:fdx-sep:decision、fact:fdx-sep:capital

**待查**　分拆公告未揭露 FedEx 母公司可取得的現金、資本支出重配金額或承接資源的具名業務。第二季已完成的 10 億美元回購也無法證明分拆資金流向。要檢驗跨業務影響，需有 FedEx 公開指明資源由哪項業務移往哪項業務，以及重配前後的金額或產能。

**模型判讀**　全對。指出母公司可得現金、重配金額及承接業務均未披露，並明確指出已完成的 10 億美元回購無法證明分拆資金流向。


### 純 Astra · 完成

[逐次回傳](../linkage-depth/raw/calls/H-06-astra.json) · [CLI 事件](../linkage-depth/raw/jobs/H-06-astra/events.jsonl) · [模型原始 JSON](../linkage-depth/raw/jobs/H-06-astra/answer.json) · [CLI 診斷](../linkage-depth/raw/jobs/H-06-astra/stderr.log) · [完整請求](../linkage-depth/raw/jobs/H-06-astra/request.json)

**研究首稿 · 觀望**

- 傳導機制　分拆須滿足後續條件並取得核准，董事會提出的 18 個月目標涵蓋 2025 年底之後。研究期內可先用執行進度檢驗時程假設。
- 標的　FedEx Freight 分拆進度
- 研究期限　2025-12-31
- 催化劑　FedEx 公布分拆條件、核准進度或修訂時程。
- 預測　基準情境為截至 2025 年底，FedEx Freight 仍處於分拆準備階段。屆時若尚未完成，仍可能符合原訂時程。
- 推翻條件　FedEx 在期限內宣布完成或終止分拆，即推翻年底仍在準備階段的預測。若公司未更新進度，則只能列為待驗證。
- 模型引文　fdx-sep:decision

**研究首稿 · 觀望**

- 傳導機制　預期符合美國聯邦所得稅免稅分離資格，無從據此推算母公司可收取的現金。已完成的 10 億美元回購也只提供歷史基準。
- 標的　FedEx 母公司因分拆而新增的回購
- 研究期限　2025-12-31
- 催化劑　交易文件量化母公司可收取的款項，且資本配置公告說明其用途。
- 預測　基準情境不計入分拆款項帶來的額外回購或每股盈餘增益。即使後續財報再列回購，仍需核對其資金來源。
- 推翻條件　若公司量化分拆款項並明示用於新增回購，應修正回購假設，再依實際執行時間及股數估算每股盈餘影響。
- 模型引文　fdx-sep:capital、fdx-sep:original、fdx-q2:repurchases、fdx-q2:original

**待查**　現有資料只揭露分拆意向與集團層級的歷史回購。要判斷分拆對留存業務的獲利影響，仍需共享成本、分拆後費用負擔或雙方服務協議的資料。公告也未具名揭露受影響的供應商或客戶。

**模型判讀**　未全對。指出歷史回購及留存業務的成本資訊缺口，但未指出分拆實收款及用途的證據缺口，也未明確保留對回購資金來源的歸因。


[逐次回傳](raw/calls/R-03-judge.json) · [CLI 事件](raw/jobs/R-03-judge/events.jsonl) · [模型原始 JSON](raw/jobs/R-03-judge/answer.json) · [CLI 診斷](raw/jobs/R-03-judge/stderr.log) · [完整請求](raw/jobs/R-03-judge/request.json)

## R-04 · NIKE · 回歸

**研究題目**　NIKE 公布季度財報。請提出可供研究員覆核的首稿。

**截止**　2024-12-19T23:59:59+00:00　**研究期限**　2025-06-30

- `nike-q2:direct`　第二財季 NIKE Direct 營收 50 億美元，按報告口徑年減 13%。NIKE Brand Digital 銷售年減 21%，自營門市銷售年減 2%。 [官方來源](https://investors.nike.com/sec-filings/all-sec-filings/content/0000320187-24-000069/q2fy25exhibit991er.htm)
- `nike-q2:margin`　集團毛利率下滑 1 個百分點至 43.6%。公告同時列出通路和合併財務表現。 [官方來源](https://investors.nike.com/sec-filings/all-sec-filings/content/0000320187-24-000069/q2fy25exhibit991er.htm)
- `nike-q2:original`　Second Quarter Income Statement Review原文：NIKE Direct revenues were $5.0 billion [官方來源](https://investors.nike.com/sec-filings/all-sec-filings/content/0000320187-24-000069/q2fy25exhibit991er.htm)
- `nike-q2:wholesale`　批發營收 69 億美元，按報告口徑年減 3%。 [官方來源](https://investors.nike.com/sec-filings/all-sec-filings/content/0000320187-24-000069/q2fy25exhibit991er.htm)

**預註冊標準**　通路跌幅差異不證明相同顧客從 Direct 轉到批發。缺同款同市場銷量或庫存、通路配置或消費者遷移，保留替代效應與特定通路造成合併毛利變動的大小。

### 新版 Harness V11 · 完成

[逐次回傳](raw/calls/R-04-ranked.json) · [CLI 事件](raw/jobs/R-04-ranked/events.jsonl) · [模型原始 JSON](raw/jobs/R-04-ranked/answer.json) · [CLI 診斷](raw/jobs/R-04-ranked/stderr.log) · [完整請求](raw/jobs/R-04-ranked/request.json)

**研究首稿 · 多方**

- 傳導機制　第二財季 NIKE Brand Digital 銷售年減21%，弱於自營門市的年減2%。若數位銷售降幅收窄，相較兩通路延續原降幅，NIKE Direct 的營收拖累可減輕。數位營收權重及增量毛利未披露，獲利改善幅度待估。
- 標的　NIKE
- 研究期限　2025-06-30
- 催化劑　12月19日財報揭露直營通路分化。下一次可用 NIKE 第三財季業績公告檢查數位銷售是否回穩，覆核期限為2025年6月30日。
- 預測　2025財年第三財季，NIKE Brand Digital 銷售年增率高於−21%，且 NIKE Direct 按報告口徑的營收年增率高於−13%。
- 推翻條件　同季數位銷售年增率等於或低於−21%，或 NIKE Direct 按報告口徑的營收年增率等於或低於−13%，即推翻數位回穩並帶動直營改善的聯合預測。
- 模型引文　fact:nike-q2:direct、fact:nike-q2:original

**研究首稿 · 空方**

- 傳導機制　第二財季批發營收年減3%，直營年減13%。若批發持續相對抗跌，且每元批發營收的毛利低於直營，通路組合相較占比持平情境會壓低集團毛利率，即使數位降幅收窄亦可能發生。兩通路毛利差未披露。
- 標的　NIKE
- 研究期限　2025-06-30
- 催化劑　12月19日財報同時揭露兩通路營收與集團毛利率。於2025年6月30日前覆核 NIKE 第三財季業績公告，檢查通路組合及毛利率年變動。
- 預測　2025財年第三財季，批發按報告口徑的營收年增率高於 NIKE Direct，且集團毛利率低於上年同期。前者代表批發占兩通路合計營收的比重上升。
- 推翻條件　同季批發營收年增率等於或低於 NIKE Direct，或集團毛利率持平或高於上年同期，即推翻組合變動與毛利率下滑並存的預測。
- 模型引文　fact:nike-q2:wholesale、fact:nike-q2:direct、fact:nike-q2:margin

**1. NIKE Brand Digital → NIKE · 自營門市**

- 起點引文　nike-q2:direct
- 受影響業務引文　nike-q2:direct
- 傳導機制　第二財季數位銷售年減21%，門市僅年減2%。若部分消費者改到門市完成購買，門市可承接原本可能流失的銷售，使 NIKE Direct 在數位仍弱時也有改善空間。
- 比較基準　以第二財季自營門市銷售年減2%為未進一步承接需求的比較基準。
- 必要條件　消費者須實際轉往 NIKE 自營門市並成交。兩通路降幅不同，本身不足以證明轉購。
- 財務影響　相對於顧客放棄購買，轉購可保住部分直營營收。估算金額仍缺轉購筆數與實收客單價。
- 其他解釋　門市自身客流回升也能縮小降幅。可核對 NIKE 業績說明是否把門市改善歸因於數位顧客轉購，或歸因於門市自身表現。
- 查核指標　NIKE 自營門市銷售年增率，以 NIKE Brand Digital 銷售年增率檢查數位需求是否仍弱。兩者均為轉購的代理指標。
- 觀察期間　2025財年第三財季，兩通路各與上年同期比較。
- 公開查核來源　NIKE 投資人關係季度業績公告及同期公開業績說明。
- 截止日　2025-06-30
- 預測　在第三財季數位銷售仍年減的條件下，門市銷售年增率高於−2%。若公司亦確認轉購，才提高對此機制的信心。
- 推翻條件　在同一季數位銷售仍年減的條件下，門市銷售年增率等於或低於−2%，即推翻門市表現改善的預測。

**待查**　公告未揭露跨通路轉購、庫存調撥、支出承諾或批發商新增配貨。若公司未公開說明，辨識轉購須用非公開交易紀錄。批發營收亦無法辨識特定零售商或證明訂單移轉。

- 第 1 條排序理由　列第一，因兩端同屬直營通路且可逐季觀察銷售，門市能否承接需求會影響對直營復甦來源的判斷。

**模型判讀**　全對。缺口指出欠缺跨通路轉購紀錄及批發增配證據，並明確保留批發營收能否歸因於訂單移轉。

- 候選 1　四項語義均通過。數位及自營門市跌幅有據。數位顧客須實際到店成交，才可能保住部分直營營收。NIKE 同季若把門市改善歸因於自身客流回升，可與轉購解釋區分。承接端是自營門市，仍屬直營。

### 現版 Harness V10 · 完成

[逐次回傳](../linkage-depth/raw/calls/H-08-harness.json) · [CLI 事件](../linkage-depth/raw/jobs/H-08-harness/events.jsonl) · [模型原始 JSON](../linkage-depth/raw/jobs/H-08-harness/answer.json) · [CLI 診斷](../linkage-depth/raw/jobs/H-08-harness/stderr.log) · [完整請求](../linkage-depth/raw/jobs/H-08-harness/request.json)

**研究首稿 · 多方**

- 傳導機制　第二財季 NIKE Brand Digital 銷售年減 21%，自營門市僅年減 2%。若第三季數位銷售跌幅收窄且門市表現穩定，相較兩通路延續原跌勢，NIKE Direct 營收所受拖累應減輕。數位營收占比及增量毛利未揭露，獲利幅度待核。
- 標的　NIKE
- 研究期限　2025-06-30
- 催化劑　2024-12-19 財報揭露直營通路內的銷售落差。以其後首份 NIKE 季度財報檢驗數位銷售是否回穩。
- 預測　截至 2025-06-30 覆核第三財季數字：NIKE Brand Digital 銷售年增率高於 −21%，且 NIKE Direct 營收按報告口徑的年增率高於 −13%。
- 推翻條件　同一季 NIKE Brand Digital 銷售年增率為 −21% 或更低，或 NIKE Direct 營收按報告口徑的年增率為 −13% 或更低，則數位回穩帶動直營改善的聯合預測失效。
- 模型引文　fact:nike-q2:direct、fact:nike-q2:original

**研究首稿 · 空方**

- 傳導機制　第二財季集團毛利率年減 1 個百分點至 43.6%。若 NIKE 為消化直營通路滯銷商品而加深折扣，在銷量與成本相同下，每件商品的毛利會低於維持原售價的情境。即使銷售回穩，集團毛利率仍可能承壓。滯銷庫存、折扣深度與受影響銷量均待證實。
- 標的　NIKE
- 研究期限　2025-06-30
- 催化劑　2024-12-19 公布的毛利率降幅提供比較基準。於下一次 NIKE 季度財報檢視第三財季毛利率及公司對折扣的說明。
- 預測　截至 2025-06-30 覆核第三財季集團毛利率，預期年減超過 1 個百分點。若 NIKE 同時指出折扣加深拖累毛利率，才可提高對定價機制的信心。
- 推翻條件　第三財季集團毛利率年減 1 個百分點或更少、持平或上升，均否定毛利率年減幅擴大的預測。缺少折扣說明只會令歸因未決。
- 模型引文　fact:nike-q2:margin、fact:nike-q2:direct

**1. NIKE Brand Digital → NIKE · 批發**

- 起點引文　nike-q2:direct
- 受影響業務引文　nike-q2:wholesale
- 傳導機制　第二財季數位銷售年減 21%，批發營收僅年減 3%。若數位銷售疲弱促使 NIKE 將部分商品改配批發，且通路商決定增購，NIKE 交貨並符合認列條件後，批發可抵銷部分直營營收壓力。
- 比較基準　若配貨維持原狀，批發不會因這項調整取得增量。第二財季批發營收為 69 億美元，按報告口徑年減 3%。
- 必要條件　NIKE 實際調整配貨，通路商選擇增購，且 NIKE 在第三財季認列增量營收。通路商也可能延後採購、消化庫存或採購其他品牌。
- 財務影響　若條件成立，批發營收高於維持原配貨時的水準。增購量、批發實現價格及被取代的直營銷售額未揭露，無法估算集團淨收益。
- 其他解釋　通路商按原計畫補貨也可能帶動批發回升。須比對 NIKE 對配貨調整及通路商實際承接的公開說明，才能區分兩者。
- 查核指標　NIKE 批發營收按報告口徑的年增率，作為通路承接需求的代理指標，無法識別轉單量或終端零售銷量。
- 觀察期間　2025 財年第三季，相對第二季的年增率
- 公開查核來源　NIKE 投資人關係網站公布的季度財報及通路說明
- 截止日　2025-06-30
- 預測　第三財季批發營收年增率高於 −3%。若公司亦確認改配與通路商承接，可提高對批發抵銷直營壓力的信心。
- 推翻條件　第三財季批發營收年增率為 −3% 或更低，否定預期的通路層級改善。若僅缺少配貨說明，則改配原因仍待確認。

**待查**　公開數字未揭露數位與批發之間的商品配額、通路商增購量或各通路毛利率。即使批發回升，也無法據此量化配貨對集團獲利的貢獻。資料亦未具名供應商、批發客戶或同業。

**模型判讀**　全對。缺口點明配額、增購量及通路毛利率未揭露。草稿把改配與承接列為待驗條件，批發回升本身不足以證明改配或顧客轉購。

- 候選 1　四項語義均通過。數位及批發跌幅有據。NIKE 須將商品由數位通路改配批發，並由通路商增購、NIKE 交貨認列，才會帶來批發增量。NIKE 同季若確認改配及實際承接，可與例行補貨區分。批發增速門檻單獨只能檢驗表現，集團淨效應仍無法估算。

### 純 Astra · 完成

[逐次回傳](../linkage-depth/raw/calls/H-08-astra.json) · [CLI 事件](../linkage-depth/raw/jobs/H-08-astra/events.jsonl) · [模型原始 JSON](../linkage-depth/raw/jobs/H-08-astra/answer.json) · [CLI 診斷](../linkage-depth/raw/jobs/H-08-astra/stderr.log) · [完整請求](../linkage-depth/raw/jobs/H-08-astra/request.json)

**研究首稿 · 空方**

- 傳導機制　第二季數位銷售年減 21%，自營門市年減 2%，兩者降幅相差 19 個百分點。若差距延續，數位業務將持續拖累直營營收。
- 標的　NIKE Direct 營收
- 研究期限　以 2025 財年第三季為首次驗證，追蹤至 2025-06-30。
- 催化劑　下一次季報公布數位、自營門市與整體直營通路表現。
- 預測　第三季數位銷售年增率仍低於自營門市，且 NIKE Direct 營收仍年減。
- 推翻條件　第三季數位銷售年增率追平或高於自營門市，或直營營收恢復年增或持平。
- 模型引文　nike-q2:direct

**研究首稿 · 多方**

- 傳導機制　批發營收基期為 69 億美元，規模大於直營。若批發率先恢復年增，其新增營收可抵銷部分直營營收損失。
- 標的　NIKE 批發與直營兩通路合計營收
- 研究期限　截至 2025-06-30 已公布的後續季度。
- 催化劑　季報揭露批發營收及可比上年同期金額。
- 預測　至少一季出現批發營收年增、直營營收仍年減，使兩通路合計的同比營收損失小於直營單一通路的損失，或使合計營收轉增。
- 推翻條件　觀察期內沒有季度同時出現批發營收年增及直營營收年減。
- 模型引文　nike-q2:wholesale、nike-q2:direct

**1. NIKE Direct，尤其是 NIKE Brand Digital → NIKE · 集團毛利**

- 起點引文　nike-q2:direct
- 受影響業務引文　nike-q2:wholesale、nike-q2:margin
- 傳導機制　若直營通路的毛利率高於批發，直營營收降幅持續大於批發，就會降低高毛利通路的營收占比，對集團毛利率形成壓力。資料未揭露兩個通路的毛利率差距。
- 比較基準　2025 財年第二季，NIKE Direct 營收為 50 億美元，年減 13%，批發營收為 69 億美元，年減 3%。以兩者營收合計為分母，直營占比約為 42.0%。同期集團毛利率為 43.6%，年減 1 個百分點。
- 必要條件　後續季度直營營收年增率仍低於批發，且直營毛利率較高。
- 財務影響　在各通路毛利率及其他業務表現相同的情況下，直營占比下降會壓低集團毛利率。現有資料無法估算影響的基點數。
- 其他解釋　折扣加深、產品組合改變或單位成本上升，也可能使集團毛利率下降。第二季通路營收與毛利率同步變動，無法區分各因素的貢獻。
- 查核指標　按報告口徑比較直營與批發營收年增率，並核對集團毛利率的年變動及公司對變動原因的說明。
- 觀察期間　2025 財年第三季，以及截至 2025 年 6 月 30 日已公布的第四季資料。
- 公開查核來源　NIKE 投資人關係網站公布的季度業績公告及隨附財務說明。
- 截止日　2025-06-30
- 預測　下一個公布季度，直營營收年增率仍低於批發，集團毛利率仍低於去年同期。若公司另指出通路組合對毛利率有負面貢獻，才有直接的歸因依據。
- 推翻條件　若下一季直營營收年增率追平或超過批發，或集團毛利率持平或上升，該季聯合預測即失準。若公司明示通路組合對毛利率貢獻為零或為正，則推翻該季的機制判斷。

**待查**　公告未提供分通路毛利率、通路組合對毛利率的量化貢獻，或具名批發客戶與供應商的訂單資料。批發營收也無法直接衡量零售商對消費者的銷售。

**模型判讀**　未全對。缺口保留了毛利歸因，並指出批發營收無法衡量終端銷售，但未具體保留直營與批發跌幅差異是否來自顧客轉購或商品改配。

- 候選 1　四項語義均通過。直營、批發及集團毛利率讀數有據。若直營毛利率較高，直營占比下降會壓低集團毛利率，幅度仍待確認。NIKE 同季若披露通路組合貢獻為零或為正，可推翻該季判斷。此路徑追蹤毛利組合，未檢驗需求是否由直營移往批發。

[逐次回傳](raw/calls/R-04-judge.json) · [CLI 事件](raw/jobs/R-04-judge/events.jsonl) · [模型原始 JSON](raw/jobs/R-04-judge/answer.json) · [CLI 診斷](raw/jobs/R-04-judge/stderr.log) · [完整請求](raw/jobs/R-04-judge/request.json)

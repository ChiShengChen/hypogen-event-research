# 跨業務假說深度逐案 QA

每個案例保留下列點時資料、兩組交付的連動、評分及原始 JSON 連結。原始模型 JSON 含完整首稿。

## P-01 · General Motors

**研究題目**　General Motors 宣布調整自動駕駛事業策略。請提出可供研究員覆核的首稿。

**截止**　2024-12-10T23:59:59+00:00　**研究期限**　2025-12-31

- `gm-av:business`　GM 表示會以 Super Cruise 既有進展為基礎，推進個人用車的駕駛輔助技術。公告時 Super Cruise 已提供給逾 20 款車。 [官方來源](https://news.gm.com/home.detail.html/Pages/news/us/en/2024/dec/1210-gm.html)
- `gm-av:cost`　若重整按計畫完成，GM 預期每年減少逾 10 億美元支出。公司當時預期計畫於 2025 年上半年完成。 [官方來源](https://news.gm.com/home.detail.html/Pages/news/us/en/2024/dec/1210-gm.html)
- `gm-av:event`　GM 宣布將停止資助 Cruise 的 robotaxi 開發，並擬整合 Cruise LLC 與 GM 技術團隊，開發自動與輔助駕駛。 [官方來源](https://news.gm.com/home.detail.html/Pages/news/us/en/2024/dec/1210-gm.html)
- `gm-av:original`　公告策略與資本配置段落原文：GM intends to combine the majority-owned Cruise LLC and GM technical teams [官方來源](https://news.gm.com/home.detail.html/Pages/news/us/en/2024/dec/1210-gm.html)

**封存裁定**　辨識 Cruise 專案資源整併與 Super Cruise／個人用車開發的條件式連動。用團隊整合、產品技術採用等公開訊號區分單純裁撤成本。逾 10 億美元屬公司預估重整後年化支出節省，不能當作 Super Cruise 專案所得預算或已實現毛利。

### 純 Astra · 完成

[逐次回傳](raw/calls/P-01-astra.json) · [CLI 事件](raw/jobs/P-01-astra/events.jsonl) · [模型原始 JSON](raw/jobs/P-01-astra/answer.json) · [CLI 診斷](raw/jobs/P-01-astra/stderr.log)

**1. Cruise 的 robotaxi 開發 → General Motors · 以 Super Cruise 為基礎的個人用車駕駛輔助業務**

- 起點引文　gm-av:event、gm-av:original
- 受影響業務引文　gm-av:business
- 傳導機制　停止資助 robotaxi 開發後，GM 擬整合兩支技術團隊。若 Cruise 人員投入個人用車專案，Super Cruise 可利用既有車款平台，將研發成果推向更多量產車款。
- 比較基準　截至 2024 年 12 月 10 日，Super Cruise 已提供給逾 20 款車。公告未列出確切款數或完整名單。
- 必要條件　整合團隊須實際參與 Super Cruise 的車款導入，且新增車款須在觀察期內開放客戶選用。
- 財務影響　新增車款可擴大能夠選用 Super Cruise 的客群。營收增量取決於相關車款銷量、選用率及實收價格，現有資料不足以估算。
- 其他解釋　新增車款也可能源自整合前已排定的產品計畫。若只有上市公告，仍需另查整合團隊的貢獻。
- 查核指標　公告後首次提供 Super Cruise 的量產車款數，以及 GM 是否說明整合團隊參與該車款導入。
- 觀察期間　2024 年 12 月 11 日至 2025 年 12 月 31 日
- 公開查核來源　GM 車款上市公告、Super Cruise 適用車款資訊及法說會對團隊分工的說明
- 截止日　2025-12-31
- 預測　截至 2025 年底，至少一款先前未提供 Super Cruise 的量產車款開放選用，且 GM 公開說明整合團隊參與其導入。
- 推翻條件　若截至年底沒有新增車款，或 GM 確認新增車款均由整合前的原團隊獨立完成，則此項預測失效。若僅缺少分工揭露，則因果關係仍待驗證。

**待查**　公告交代了兩支團隊的整合意向，但未披露 Cruise 人員將投入哪些 Super Cruise 專案、相關預算或原定上市時程。現有資料也未指認受影響的外部供應商或客戶。

**模型評分**　全對。缺口指出人員配置、預算與原定時程尚未披露，保留對實際調度及財務貢獻的判斷。

- 候選 1　四項語義均通過。公告支持停止資助與擬議整併，也支持 Super Cruise 已覆蓋逾 20 款車。若 GM 確認新增車款全由原團隊獨立完成，即可推翻整合團隊參與導入的預測。參與導入可驗證資源連動，增量營收仍取決於銷量、選用率與實收價格。

### Harness V10 · 完成

[逐次回傳](raw/calls/P-01-harness.json) · [CLI 事件](raw/jobs/P-01-harness/events.jsonl) · [模型原始 JSON](raw/jobs/P-01-harness/answer.json) · [CLI 診斷](raw/jobs/P-01-harness/stderr.log)

**1. robotaxi 開發 → General Motors · Super Cruise**

- 起點引文　gm-av:event
- 受影響業務引文　gm-av:business
- 傳導機制　停止資助 robotaxi 開發後，若 GM 將具備適用技能的工程人員調入 Super Cruise 車型導入專案，便可能在削減總支出的同時擴大可搭載車款。
- 比較基準　2024-12-10 公告時已有逾 20 款車提供 Super Cruise。即使維持原策略，既有車型計畫也可能帶來新增車款。
- 必要條件　GM 實際將 Cruise 人員配置到 Super Cruise，且這項調度促成至少一款原計畫以外的車型導入，或使既定導入提前。
- 財務影響　新增可搭載車款可擴大潛在收入來源。實際收入貢獻取決於車輛交付、消費者選配、定價與收入認列，現有資料無法估算。
- 其他解釋　新車款可能依重整前的產品計畫如期推出。須比對 GM 對原定時程的說明，以及產品更新是否明確將新增或提前導入歸因於團隊調度。
- 查核指標　GM 明確歸因於團隊調度、且已新增或提前提供 Super Cruise 的車款數。公開車款名單僅是供應範圍的代理指標。
- 觀察期間　2024-12-10 公告後至 2025-12-31，以期間內已公開的車型上市及重整更新為準。
- 公開查核來源　GM Newsroom 的 Super Cruise 車型公告及 GM 財報說明會的工程團隊配置說明。
- 截止日　2025-12-31
- 預測　期間內至少一款車已提供 Super Cruise，且 GM 確認團隊調度使該款新增或提前導入。
- 推翻條件　GM 確認截至覆核日，團隊調度促成的新增或提前導入車款數為零。若只公布車款而未解釋調度影響，歸因仍待查。

**待查**　GM 未披露 Super Cruise 承接的人力、原定車型時程或各車款的收益。若公司未公開說明調度成效，判斷是否加快導入需要非公開的人力配置與專案時程紀錄。材料也未指名承受訂單變動的外部供應商或客戶。

**模型評分**　全對。缺口指出人力配置、原定車型時程與各車款收益尚未披露，保留對導入加速的歸因。

- 候選 1　四項語義均通過。公告支持兩端業務及擬議整併，實際調度仍列為條件。以 GM 車型公告和財報說明會查核期內是否有因調度而新增或提前的導入，可區分既定上市計畫。營收上行空間取決於交付、選配、定價及認列，金額尚無法估算。

[判讀原始 JSON](raw/calls/P-01-judge.json) · [CLI 事件](raw/jobs/P-01-judge/events.jsonl) · [模型原始 JSON](raw/jobs/P-01-judge/answer.json) · [CLI 診斷](raw/jobs/P-01-judge/stderr.log)

## P-02 · Unilever

**研究題目**　Unilever 公布第一季交易更新與策略進展。請提出可供研究員覆核的首稿。

**截止**　2024-04-25T23:59:59+00:00　**研究期限**　2025-12-31

- `ul-q1:beauty`　Beauty & Wellbeing 的基礎銷售成長為 7.4%，銷量成長 5.6%，由 Health & Wellbeing 和 Prestige Beauty 持續雙位數成長帶動。 [官方來源](https://www.unilever.com/news/press-and-media/press-releases/2024/improved-volume-growth-led-by-power-brands/)
- `ul-q1:original`　Beauty & Wellbeing 段落及 Ice Cream 分拆更新原文：Beauty & Wellbeing grew underlying sales by 7.4% [官方來源](https://www.unilever.com/news/press-and-media/press-releases/2024/improved-volume-growth-led-by-power-brands/)
- `ul-q1:portfolio`　Unilever 說計畫於 2025 年底前完成 Ice Cream 分拆。另啟動集團生產力計畫，三年目標節省約 8 億歐元，預期可抵銷分拆造成的營運協同損失。 [官方來源](https://www.unilever.com/news/press-and-media/press-releases/2024/improved-volume-growth-led-by-power-brands/)

**封存裁定**　區分集團生產力節省與 Ice Cream 分拆的成本抵銷，以及 Beauty & Wellbeing 本身成長。缺少撥款、支出移轉或資本配置明細，不能說分拆款項或節省支出流入 Beauty & Wellbeing 並造成既見財務成長。

### 純 Astra · 完成

[逐次回傳](raw/calls/P-02-astra.json) · [CLI 事件](raw/jobs/P-02-astra/events.jsonl) · [模型原始 JSON](raw/jobs/P-02-astra/answer.json) · [CLI 診斷](raw/jobs/P-02-astra/stderr.log)

**1. Ice Cream 分拆 → Unilever · 分拆後保留業務的營運成本**

- 起點引文　ul-q1:portfolio
- 受影響業務引文　ul-q1:portfolio
- 傳導機制　Ice Cream 分拆會使集團失去部分營運協同效益。若生產力計畫及時降低保留業務的經常性成本，就能減輕分拆對營業利益的壓力。
- 比較基準　截至 2024 年 4 月 25 日，公司預期三年節省約 8 億歐元，並預期可抵銷分拆造成的營運協同損失。協同損失金額及節省額的年度分布仍待揭露。
- 必要條件　分拆於研究期內完成，且可歸屬保留業務的經常性節省在協同損失發生時已生效。
- 財務影響　相較於僅承受協同損失的情境，保留業務的經常性營業利益較高。一次性分拆與重組費用另行核算。
- 其他解釋　即使集團利潤率上升，也可能源於分拆後業務組合改變，單一利潤率數字無法辨認節省額。
- 查核指標　以相同業務範圍及期間計算，保留業務已實現的經常性節省額減去已發生的營運協同損失，單位為歐元。
- 觀察期間　2024 年 4 月 25 日至 2025 年 12 月 31 日間已公開的分拆及財務進度更新
- 公開查核來源　Unilever 業績公告、生產力計畫進度及 Ice Cream 分拆公告
- 截止日　2025-12-31
- 預測　若分拆按期完成，預期截至分拆時已生效的節省至少可部分抵銷同期協同損失。完全抵銷仍取決於三年計畫的執行進度。
- 推翻條件　若公司披露分拆時協同損失已發生，而保留業務尚未實現任何相關節省，則同期部分抵銷的預測失效。若公司未提供可比數據，結論維持待驗證。

**待查**　公司僅揭露集團層級的節省目標。保留業務可分得多少節省、何時入帳，以及分拆會損失多少協同效益，均無法由現有資料量化。

**模型評分**　未全對。缺口指出保留業務的節省分攤與金額未明，但未指出流向 Beauty & Wellbeing 的撥款或支出證據缺失，也未明確排除對該事業既有成長的歸因。

- 候選 1　四項語義均通過。公告支持集團的抵銷預期。保留業務須在協同損失發生時已實現經常性節省，營業利益才會高於僅承受損失的情境。若公司公告顯示同期間已有協同損失但相關節省為零，即可推翻部分抵銷的預測，即使業務組合變動推高集團利潤率。

### Harness V10 · 完成

[逐次回傳](raw/calls/P-02-harness.json) · [CLI 事件](raw/jobs/P-02-harness/events.jsonl) · [模型原始 JSON](raw/jobs/P-02-harness/answer.json) · [CLI 診斷](raw/jobs/P-02-harness/stderr.log)

**1. Ice Cream → Unilever · 集團生產力計畫**

- 起點引文　ul-q1:portfolio
- 受影響業務引文　ul-q1:portfolio
- 傳導機制　公司預期生產力節省可抵銷分拆造成的營運協同損失。若共用作業先行拆開、節省較晚實現，集團須先承擔成本，即使分拆最終如期完成也一樣。
- 比較基準　若維持原有共用作業，集團無須以生產力節省填補此次分拆新增的協同損失。
- 必要條件　分拆已造成持續性協同損失，且同期間實現的生產力節省不足以抵銷。
- 財務影響　兩者淨額為負會壓低集團營業利益。三年約 8 億歐元是節省目標，當期節省與協同損失均缺金額。
- 其他解釋　一次性分拆費用也可能壓低利益。須查公司是否分列一次性費用與持續性協同損失，再與同期已實現節省比較。
- 查核指標　同期間已實現生產力節省減持續性分拆協同損失，或公司明示兩者是否已相抵。
- 觀察期間　2025 年上半年
- 公開查核來源　Unilever 半年度業績中的分拆與生產力進度說明。若僅更新三年目標，淨額仍待查。
- 截止日　2025-12-31
- 預測　Unilever 揭露 2025 年上半年實現的節省低於同期持續性分拆協同損失。
- 推翻條件　Unilever 揭露 2025 年上半年實現的節省等於或高於同期持續性分拆協同損失。

**待查**　公司已說明節省的抵銷用途，但未揭露實現時程、協同損失金額或各事業分攤。若公開資料缺乏同口徑比較，須取得內部成本調節表。也無資料顯示節省會轉投 Beauty & Wellbeing。

**模型評分**　全對。缺口指出缺少事業分攤及節省轉投 Beauty & Wellbeing 的證據，因此未把該事業既有成長歸因於分拆或節省。

- 候選 1　四項語義均通過。公告支持分拆計畫及集團預期以節省抵銷協同損失。若同期節省落後於持續性協同損失，集團營業利益承壓。約 8 億歐元是三年目標。若半年報分列一次性費用，並顯示同期節省已足以抵銷持續性損失，即可推翻預測。

[判讀原始 JSON](raw/calls/P-02-judge.json) · [CLI 事件](raw/jobs/P-02-judge/events.jsonl) · [模型原始 JSON](raw/jobs/P-02-judge/answer.json) · [CLI 診斷](raw/jobs/P-02-judge/stderr.log)

## P-03 · Amazon

**研究題目**　Amazon 宣布增加一筆策略投資並深化既有合作。請提出可供研究員覆核的首稿。

**截止**　2024-11-22T23:59:59+00:00　**研究期限**　2025-12-31

- `amzn-ai:channel`　Amazon Bedrock 提供 Anthropic Claude 模型給 AWS 客戶。公告未列 Anthropic 的保證雲端用量、單價或 AWS 由此認列的營收。 [官方來源](https://www.aboutamazon.com/news/aws/amazon-invests-additional-4-billion-anthropic-ai)
- `amzn-ai:compute`　Anthropic 表示將使用 AWS Trainium 與 Inferentia 訓練及部署未來基礎模型，雙方會共同推進 Trainium 的硬體及軟體能力。 [官方來源](https://www.aboutamazon.com/news/aws/amazon-invests-additional-4-billion-anthropic-ai)
- `amzn-ai:event`　Amazon 宣布再對 Anthropic 投資 40 億美元。Anthropic 將 AWS 列為主要訓練合作夥伴，且 AWS 繼續是主要雲端供應商。 [官方來源](https://www.aboutamazon.com/news/aws/amazon-invests-additional-4-billion-anthropic-ai)
- `amzn-ai:original`　公告標題後的合作條款及技術部署段落原文：Anthropic is now naming AWS its primary training partner [官方來源](https://www.aboutamazon.com/news/aws/amazon-invests-additional-4-billion-anthropic-ai)

**封存裁定**　辨識 Anthropic 實際訓練或部署專案帶來 AWS Trainium／AWS 運算需求，或 Anthropic 模型供應帶來 Bedrock 使用。以具名訓練、模型部署或 AWS 使用事證區分投資金額與一般雲端需求。股權投資不能視為 AWS 營收，請指出用量／單價條件。

### 純 Astra · 完成

[逐次回傳](raw/calls/P-03-astra.json) · [CLI 事件](raw/jobs/P-03-astra/events.jsonl) · [模型原始 JSON](raw/jobs/P-03-astra/answer.json) · [CLI 診斷](raw/jobs/P-03-astra/stderr.log)

**1. Anthropic 的基礎模型訓練 → Amazon · AWS 的 Trainium 訓練運算服務**

- 起點引文　amzn-ai:event、amzn-ai:compute
- 受影響業務引文　amzn-ai:compute、amzn-ai:original
- 傳導機制　Anthropic 若將新增的模型訓練工作交由 AWS 的 Trainium 執行，且按用量付費，AWS 可從這批工作取得額外運算收入。
- 比較基準　截至 2024 年 11 月 22 日，AWS 已是 Anthropic 的主要雲端供應商，此次再獲指定為主要訓練合作夥伴。公告未提供既有付費用量。
- 必要條件　後續訓練須實際使用 Trainium，且相較既有安排增加 Anthropic 在 AWS 的付費運算支出。
- 財務影響　新增付費支出可帶動 AWS 營收。營業利益貢獻另取決於實收價格、硬體折舊及營運成本，現有資料無法估算。
- 其他解釋　Anthropic 可能把原已付費的 AWS 訓練工作移至 Trainium。如此即使 Trainium 用量上升，AWS 從 Anthropic 取得的總收入仍可能持平。
- 查核指標　Anthropic 實際以 Trainium 訓練的模型或工作負載，以及該公司在 AWS 的付費訓練支出相較公告前的變化。
- 觀察期間　2024 年 11 月 23 日至 2025 年 12 月 31 日
- 公開查核來源　Amazon、AWS 或 Anthropic 的技術公告，以及 Amazon 財報或法說會對相關付費用量的說明。
- 截止日　2025-12-31
- 預測　期限內至少有一項公開揭露可辨識 Anthropic 已以 Trainium 執行具體訓練工作。若另有可比較的付費支出增量，才支持 AWS 營收受益。
- 推翻條件　若雙方揭露相關訓練已取消或延至期限之後，期間內落地的預測即失效。若確認僅替換既有 AWS 運算且支出未增，則新增營收的推論失效。

**待查**　訓練端缺少公告前後可比較的付費支出。通路端僅知 AWS 客戶已可經 Bedrock 使用 Claude，缺少推論用量、計價及收入分配，兩端對 AWS 營收的貢獻均待核實。

**模型評分**　全對。缺口涵蓋訓練支出基準及 Bedrock 用量與計價，兩端的 AWS 營收貢獻均待驗證。

- 候選 1　四項語義均通過。公告支持 Anthropic 擬採用 AWS Trainium。具名訓練可驗證落地，AWS 營收增量另需可比的付費支出。期內若公開確認工作取消、延後，或僅替換既有 AWS 算力且支出持平，即可推翻相應推論。

### Harness V10 · 完成

[逐次回傳](raw/calls/P-03-harness.json) · [CLI 事件](raw/jobs/P-03-harness/events.jsonl) · [模型原始 JSON](raw/jobs/P-03-harness/answer.json) · [CLI 診斷](raw/jobs/P-03-harness/stderr.log)

**1. AWS Trainium → Amazon · Amazon Bedrock**

- 起點引文　amzn-ai:compute、amzn-ai:event
- 受影響業務引文　amzn-ai:channel
- 傳導機制　若 Anthropic 將新一代 Claude 的實際訓練工作交給 Trainium，並選擇透過 Bedrock 發行該模型，AWS 就能在訓練之外，向使用該模型的客戶收取推論費用。
- 比較基準　投資公告前已有 Claude 的 Bedrock 通路。沿用既有合作也可能有新版上架。
- 必要條件　須能核對同一模型確實使用 Trainium 訓練、Anthropic 決定透過 Bedrock 發行，且 AWS 客戶的付費使用相對既有版本有淨增加。
- 財務影響　新增付費推論可增加 Bedrock 營收。淨貢獻取決於用量、價格、模型分潤及舊版用量被替代的程度，公告均未量化。
- 其他解釋　依既有發行安排推出新版，也會使 Bedrock 型錄增加。對照同一版本的訓練說明與上架公告，可辨識訓練合作是否延伸至通路；增量需求仍須用量資料。
- 查核指標　公開確認以 Trainium 訓練、且在 Bedrock 正式開放付費使用的新增 Claude 版本數，作為通路延伸的代理指標。
- 觀察期間　2024-11-22 公告後至 2025-12-31，以同一模型版本核對兩端。
- 公開查核來源　Anthropic 模型發布說明、Amazon／AWS 合作進度與 Amazon Bedrock 模型上市公告。
- 截止日　2025-12-31
- 預測　至少一個新版本同時符合兩項條件，支持訓練合作延伸至 Bedrock 的判斷。上架本身無法歸因付費用量或營收增幅。
- 推翻條件　若雙方對期內符合訓練條件的版本有完整公開交代，且可核實截至期限均未在 Bedrock 正式開放付費使用，則該版本數為零，推翻期內通路延伸預測。

**待查**　即使同一版本完成訓練並上架，仍缺少既有通路下的用量基準、客戶新增付費用量與分潤條款，無法估計合作為 Bedrock 增加多少毛利。亦無資料可追蹤共同開發是否排擠 AWS 其他專案。

**模型評分**　未全對。缺口指出用量基準、增量付費用量及分潤條款仍未確認，合作的毛利貢獻無法估算。

- 候選 1　反證設計。公告支持 Trainium 訓練計畫及既有 Claude 通路。新版供應須帶來淨新增付費推論，才支持 Bedrock 營收增加。公開核對同版訓練與上架可檢驗里程碑，但沿用既有發行安排也可能產生同一結果，無法據此辨別上架原因。

[判讀原始 JSON](raw/calls/P-03-judge.json) · [CLI 事件](raw/jobs/P-03-judge/events.jsonl) · [模型原始 JSON](raw/jobs/P-03-judge/answer.json) · [CLI 診斷](raw/jobs/P-03-judge/stderr.log)

## P-04 · PepsiCo

**研究題目**　PepsiCo 公布第三季財報並更新展望。請提出可供研究員覆核的首稿。

**截止**　2024-10-08T23:59:59+00:00　**研究期限**　2025-06-30

- `pep-q3:flna`　PepsiCo 第三季 Frito-Lay North America 的 GAAP 營收年減 1%，核心固定匯率營業利益年減 9%。 [官方來源](https://investor.pepsico.com/docs/default-source/investors/q3-2024/q3-2024-earnings-release_3zjmhjkr4wdt37ko.pdf)
- `pep-q3:original`　第三季部門營運比較表原文：Frito-Lay North America [官方來源](https://investor.pepsico.com/docs/default-source/investors/q3-2024/q3-2024-earnings-release_3zjmhjkr4wdt37ko.pdf)
- `pep-q3:outlook`　公司更新的是集團全年展望。部門表各自列示分部數字及可比性調整。 [官方來源](https://investor.pepsico.com/docs/default-source/investors/q3-2024/q3-2024-earnings-release_3zjmhjkr4wdt37ko.pdf)
- `pep-q3:pbna`　同一季 PepsiCo Beverages North America 的 GAAP 營收約持平，有機營收年增 1%，核心固定匯率營業利益年增 7%。 [官方來源](https://investor.pepsico.com/docs/default-source/investors/q3-2024/q3-2024-earnings-release_3zjmhjkr4wdt37ko.pdf)

**封存裁定**　零食與飲料有各自部門表，缺共同促銷／同客群或資源移轉、以及可歸因的數量或費用資料。不能說 Frito-Lay 的衰退直接導致飲料部門改善，或把 GAAP 與核心固定匯率混作同口徑成長。

### 純 Astra · 完成

[逐次回傳](raw/calls/P-04-astra.json) · [CLI 事件](raw/jobs/P-04-astra/events.jsonl) · [模型原始 JSON](raw/jobs/P-04-astra/answer.json) · [CLI 診斷](raw/jobs/P-04-astra/stderr.log)

**待查**　兩個北美分部同季的營業利益走勢相反，但現有資料未揭露共同客戶的採購變化、跨品類促銷或資源移轉，無從判定零食業務的變化是否影響飲料業務。

**模型評分**　全對。指出缺少共同客戶採購、跨品類促銷或資源移轉的證據，並明確保留歸因。


### Harness V10 · 完成

[逐次回傳](raw/calls/P-04-harness.json) · [CLI 事件](raw/jobs/P-04-harness/events.jsonl) · [模型原始 JSON](raw/jobs/P-04-harness/answer.json) · [CLI 診斷](raw/jobs/P-04-harness/stderr.log)

**待查**　Frito-Lay North America 與 PepsiCo Beverages North America 的分部表可核對各自表現，但要判斷一方是否因另一方承壓而受益，仍缺管理層對預算或產能實際移轉方向、時點及受影響分部的說明。兩部門利益增速一升一降，無法辨識資源移轉。

**模型評分**　全對。指出缺少預算或產能移轉的方向、時點與受影響分部，並明確保留歸因。


[判讀原始 JSON](raw/calls/P-04-judge.json) · [CLI 事件](raw/jobs/P-04-judge/events.jsonl) · [模型原始 JSON](raw/jobs/P-04-judge/answer.json) · [CLI 診斷](raw/jobs/P-04-judge/stderr.log)

## H-01 · Microsoft

**研究題目**　Microsoft 公布多年期策略合作。請提出可供研究員覆核的首稿。

**截止**　2022-12-12T23:59:59+00:00　**研究期限**　2024-12-31

- `ms-lseg:contract`　London Stock Exchange Group（LSEG）與 Microsoft 簽十年合作。LSEG 對 Microsoft 的最低雲端相關支出承諾為十年合計 28 億美元。 [官方來源](https://news.microsoft.com/source/2022/12/12/lseg-and-microsoft-launch-10-year-strategic-partnership-for-next-generation-data-and-analytics-and-cloud-infrastructure-solutions-microsoft-to-make-equity-investment-in-lseg-through-acquisition-of-sh/)
- `ms-lseg:equity`　Microsoft 還擬取得 LSEG 約 4% 股份；持股交易與雲端服務使用是不同項目。 [官方來源](https://news.microsoft.com/source/2022/12/12/lseg-and-microsoft-launch-10-year-strategic-partnership-for-next-generation-data-and-analytics-and-cloud-infrastructure-solutions-microsoft-to-make-equity-investment-in-lseg-through-acquisition-of-sh/)
- `ms-lseg:migration`　LSEG 的資料平台與其他關鍵科技基礎設施會遷移至 Microsoft Azure。Workspace 與 Teams／Microsoft 365 另有整合計畫。 [官方來源](https://news.microsoft.com/source/2022/12/12/lseg-and-microsoft-launch-10-year-strategic-partnership-for-next-generation-data-and-analytics-and-cloud-infrastructure-solutions-microsoft-to-make-equity-investment-in-lseg-through-acquisition-of-sh/)
- `ms-lseg:original`　公告條列合約支出及雲端遷移原文：Contractual commitment by LSEG for minimum cloud-related spend with Microsoft [官方來源](https://news.microsoft.com/source/2022/12/12/lseg-and-microsoft-launch-10-year-strategic-partnership-for-next-generation-data-and-analytics-and-cloud-infrastructure-solutions-microsoft-to-make-equity-investment-in-lseg-through-acquisition-of-sh/)

**封存裁定**　LSEG 遷移計畫和最低雲端支出契約連至 Azure／雲端服務需求。追蹤遷移、工作負載上線或合約履約，區分入股與一般 Azure 增長。28 億為十年最低支出，不能按年平均當成已認列收入。

### 純 Astra · 完成

[逐次回傳](raw/calls/H-01-astra.json) · [CLI 事件](raw/jobs/H-01-astra/events.jsonl) · [模型原始 JSON](raw/jobs/H-01-astra/answer.json) · [CLI 診斷](raw/jobs/H-01-astra/stderr.log)

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

**模型評分**　全對。符合指定路徑，且未將十年最低支出均攤為已認列營收。缺口說明整合的付費方式、採用基準與收入歸屬仍待揭露。

- 候選 1　四項語義均通過。公告支持 LSEG 遷移至 Azure 及十年最低支出承諾。正式上線可驗證遷移，新增雲端營收仍須新增計費用量佐證。期內公開確認遷移延後或計費用量持平，均可推翻期內新增用量假設。

### Harness V10 · 完成

[逐次回傳](raw/calls/H-01-harness.json) · [CLI 事件](raw/jobs/H-01-harness/events.jsonl) · [模型原始 JSON](raw/jobs/H-01-harness/answer.json) · [CLI 診斷](raw/jobs/H-01-harness/stderr.log)

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

**模型評分**　未全對。缺口指出缺少共用人力、預算與資源調度證據，並明確保留對兩案是否互相排擠的判斷。

- 候選 1　未命中主要傳導。公告支持 Teams 與 Workspace 的整合計畫。LSEG 產品公告可區分正式對外開放與僅限試用，驗證新增入口。Workspace 營收增量取決於可歸因的付費或續約。此路徑未涵蓋 Azure 遷移與雲端需求。

[判讀原始 JSON](raw/calls/H-01-judge.json) · [CLI 事件](raw/jobs/H-01-judge/events.jsonl) · [模型原始 JSON](raw/jobs/H-01-judge/answer.json) · [CLI 診斷](raw/jobs/H-01-judge/stderr.log)

## H-02 · Dell Technologies

**研究題目**　Dell Technologies 被列入產業平台更新。請提出可供研究員覆核的首稿。

**截止**　2024-06-02T23:59:59+00:00　**研究期限**　2025-06-30

- `nv-system:dell`　NVIDIA 公開提到 Dell Technologies、Hewlett Packard Enterprise 和 Lenovo 的伺服器可使用相關資料中心技術。 [官方來源](https://nvidianews.nvidia.com/news/computer-industry-ai-factories-data-centers/)
- `nv-system:original`　Computex 公告與合作夥伴段落原文：Dell Technologies, Hewlett Packard Enterprise and Lenovo [官方來源](https://nvidianews.nvidia.com/news/computer-industry-ai-factories-data-centers/)
- `nv-system:peer`　同一公布列出 Supermicro 等不同系統廠商供應以 NVIDIA GPU 與網路為基礎的產品。 [官方來源](https://nvidianews.nvidia.com/news/computer-industry-ai-factories-data-centers/)
- `nv-system:platform`　公告描述 NVIDIA Blackwell 與系統設計平台的產業採用情形，未列各 OEM 的同一批客戶訂單或可分配晶片數。 [官方來源](https://nvidianews.nvidia.com/news/computer-industry-ai-factories-data-centers/)

**封存裁定**　辨識共用平台可說明設備相容或供應選項。缺少配額、訂單或客戶改單，保留 Dell 與 Supermicro／其他 OEM 相對增量方向。不能主張供應、訂單或份額已由一方流往另一方。

### 純 Astra · 完成

[逐次回傳](raw/calls/H-02-astra.json) · [CLI 事件](raw/jobs/H-02-astra/events.jsonl) · [模型原始 JSON](raw/jobs/H-02-astra/answer.json) · [CLI 診斷](raw/jobs/H-02-astra/stderr.log)

**待查**　公告可確認 Dell、HPE、Lenovo 與 Supermicro 均參與 NVIDIA 相關系統市場。要判斷 Dell 接單是否排擠同業，仍需同一客戶採購案的得失標紀錄，或同一批次晶片在各廠間的配額變動。現有資料也缺少 Dell 的產品別出貨與毛利基準，無法估算對其他業務的影響。

**模型評分**　全對。未提交連結。將同一客戶採購案的得失標紀錄或同批晶片的配額變動列為判斷條件，保留 Dell 接單排擠同業的歸因。


### Harness V10 · 完成

[逐次回傳](raw/calls/H-02-harness.json) · [CLI 事件](raw/jobs/H-02-harness/events.jsonl) · [模型原始 JSON](raw/jobs/H-02-harness/answer.json) · [CLI 診斷](raw/jobs/H-02-harness/stderr.log)

**待查**　公告列出多家系統廠，但未指出 Dell 哪項既有產品會因 Blackwell 導入而讓出產能或預算，也未揭露客戶在 Dell 與同業間的採購分配。要檢驗第二層影響，需有 Dell 指明受影響產品與資源調整，或客戶公開具名的採購轉向、產品及期間。

**模型評分**　全對。未提交連結。指出公告未揭露 Dell 與同業間的採購分配，並要求具名客戶、產品與期間的改單證據，保留訂單轉移歸因。


[判讀原始 JSON](raw/calls/H-02-judge.json) · [CLI 事件](raw/jobs/H-02-judge/events.jsonl) · [模型原始 JSON](raw/jobs/H-02-judge/answer.json) · [CLI 診斷](raw/jobs/H-02-judge/stderr.log)

## H-03 · Walmart

**研究題目**　Walmart 公告完成一筆收購。請提出可供研究員覆核的首稿。

**截止**　2024-12-03T23:59:59+00:00　**研究期限**　2025-12-31

- `wmt-vizio:agency`　管理層預期收購有助 Walmart Connect 廣告業務成長。完成交易與廣告技術整合是不同進度。 [官方來源](https://corporate.walmart.com/news/2024/12/03/walmart-completes-acquisition-of-vizio)
- `wmt-vizio:event`　Walmart 公告完成收購 VIZIO。VIZIO 提供 SmartCast 連網電視作業系統。 [官方來源](https://corporate.walmart.com/news/2024/12/03/walmart-completes-acquisition-of-vizio)
- `wmt-vizio:original`　公告的 SmartCast 與廣告業務段落原文：accelerate growth at Walmart Connect, the company’s advertising business [官方來源](https://corporate.walmart.com/news/2024/12/03/walmart-completes-acquisition-of-vizio)
- `wmt-vizio:platform`　VIZIO 的 Platform+ 主要由廣告業務組成，公告時占 VIZIO 全部毛利。這是 VIZIO 的口徑。 [官方來源](https://corporate.walmart.com/news/2024/12/03/walmart-completes-acquisition-of-vizio)

**封存裁定**　SmartCast／Platform+ 的廣告庫存或廣告主與 Walmart Connect 的廣告規模連動。條件要涉及廣告整合、可購庫存、銷售或衡量能力。用共同產品推廣／具名串流庫存採用分離 Walmart Connect 既有成長或併表基期效應，勿套用 VIZIO 的毛利為 Walmart 結果。

### 純 Astra · 完成

[逐次回傳](raw/calls/H-03-astra.json) · [CLI 事件](raw/jobs/H-03-astra/events.jsonl) · [模型原始 JSON](raw/jobs/H-03-astra/answer.json) · [CLI 診斷](raw/jobs/H-03-astra/stderr.log)

**1. VIZIO 的 SmartCast 連網電視作業系統與以廣告為主的 Platform+ 業務 → Walmart · Walmart Connect 廣告業務**

- 起點引文　wmt-vizio:event、wmt-vizio:platform
- 受影響業務引文　wmt-vizio:agency、wmt-vizio:original
- 傳導機制　若 Walmart Connect 能讓客戶透過既有投放流程購買 SmartCast 廣告版位，客戶可能將額外的連網電視廣告預算交給 Walmart Connect。
- 比較基準　截至 2024 年 12 月 3 日，Walmart 已完成收購。Platform+ 在收購前已有廣告業務，評估整合效益時須扣除這部分既有收入。
- 必要條件　SmartCast 版位透過 Walmart Connect 開放付費投放，且客戶增加總支出。
- 財務影響　新增投放可帶動 Walmart Connect 廣告收入。對 Walmart 營業利益的貢獻取決於新增收入的毛利及整合成本。
- 其他解釋　若客戶只是把原先投在 Platform+ 或 Walmart Connect 其他版位的預算移至新方案，方案可以有銷售額，而 Walmart 的廣告總收入仍可能沒有增量。
- 查核指標　已開放購買的 SmartCast 版位、實際付費投放，以及公司可歸因於整合的新增廣告收入。
- 觀察期間　2024 年 12 月 4 日至 2025 年 12 月 31 日期間公開的資料
- 公開查核來源　Walmart Connect 廣告產品公告、Walmart 季度業績資料及法說會說明
- 截止日　2025-12-31
- 預測　若整合帶來額外需求，期限內應能找到客戶透過 Walmart Connect 購買 SmartCast 廣告的公開案例，並在可比口徑的收入說明中看到新增支出的證據。
- 推翻條件　若公司確認至期限仍未開放投放，則期限內由此管道帶動收入的假設失效。若已開放，但公司確認相關支出全數來自既有預算移轉，則新增收入假設失效。

**待查**　公告交代了兩項業務的關係與管理層目標。研究員仍需取得共同投放方案的上線日期、實際採用情況，以及區分既有 Platform+ 收入與新增支出的資料。

**模型評分**　全對。缺口具體指出仍需確認上線、採用及可比口徑的新增支出。

- 候選 1　四項語義均通過。公告支持兩端業務及管理層目標。以 SmartCast 版位可購和客戶追加支出為條件，推估 Walmart Connect 廣告收入方向。若 Walmart 在期限內確認尚未開放投放或支出全來自既有預算移轉，即可推翻相應假設。

### Harness V10 · 完成

[逐次回傳](raw/calls/H-03-harness.json) · [CLI 事件](raw/jobs/H-03-harness/events.jsonl) · [模型原始 JSON](raw/jobs/H-03-harness/answer.json) · [CLI 診斷](raw/jobs/H-03-harness/stderr.log)

**1. SmartCast → Walmart · Walmart Connect**

- 起點引文　wmt-vizio:event
- 受影響業務引文　wmt-vizio:agency、wmt-vizio:original
- 傳導機制　收購把 SmartCast 納入集團。若 Walmart Connect 取得可銷售的電視廣告版位，且廣告主決定投放，Walmart Connect 可增加一個實際交付廣告的通路。
- 比較基準　若交易未改變銷售安排，SmartCast 可沿用原通路銷售。公告未交代交割前兩平台的合作範圍。
- 必要條件　Walmart Connect 須取得版位並完成投放，廣告主也須選用該通路。集團收入要有增量，還需新增預算或原本無法售出的版位。
- 財務影響　新增付費投放可提高廣告收入。缺少新增支出、成交價格、原通路收入及收入歸屬，無法估計淨增額。
- 其他解釋　既有 VIZIO 廣告改由 Walmart Connect 銷售，也可能產生投放案例。可查 Walmart 是否說明該活動帶來追加預算。
- 查核指標　由 Walmart Connect 銷售、已在 SmartCast 實際投放的公開案例，作為通路採用代理指標。
- 觀察期間　2024-12-03 交割公告後至 2025-12-31
- 公開查核來源　Walmart 公司新聞稿或 Walmart Connect 公開廣告主案例。
- 截止日　2025-12-31
- 預測　期內可見至少一例由 Walmart Connect 銷售且已在 SmartCast 投放的廣告。
- 推翻條件　Walmart 明確確認截至同一期末，經 Walmart Connect 銷售並在 SmartCast 實際投放的廣告仍為零。

**待查**　Platform+ 在公告時貢獻 VIZIO 全部毛利。要判斷新通路是否排擠其原有廣告，需有同口徑的原通路與新增通路收入及毛利。資料未顯示 Walmart 會公開此拆分。

**模型評分**　全對。缺口將毛利歸於 VIZIO，並指出判斷原通路是否遭排擠所需的可比資料。

- 候選 1　四項語義均通過。公告支持 SmartCast 與 Walmart Connect 兩端，可售版位及付費投放列為條件。Walmart 同期公布的具名投放案例可區分通路採用與單純併表，確認零投放則可推翻採用預測。收入淨增額仍須釐清預算來源、價格及收入歸屬。

[判讀原始 JSON](raw/calls/H-03-judge.json) · [CLI 事件](raw/jobs/H-03-judge/events.jsonl) · [模型原始 JSON](raw/jobs/H-03-judge/answer.json) · [CLI 診斷](raw/jobs/H-03-judge/stderr.log)

## H-04 · Target

**研究題目**　Target 公布第三季業績。請提出可供研究員覆核的首稿。

**截止**　2024-11-20T23:59:59+00:00　**研究期限**　2025-06-30

- `tgt-q3:beauty`　Target 的 Beauty 可比銷售增逾 6%。Food & Beverage 和 Essentials 的增幅為低個位數。 [官方來源](https://corporate.target.com/press/release/2024/11/target-corporation-reports-third-quarter-earnings)
- `tgt-q3:margin`　合併第三季毛利率較上年低 0.2 個百分點。 [官方來源](https://corporate.target.com/press/release/2024/11/target-corporation-reports-third-quarter-earnings)
- `tgt-q3:original`　財報重點的品類分項原文：Beauty comparable sales grew more than 6 percent. [官方來源](https://corporate.target.com/press/release/2024/11/target-corporation-reports-third-quarter-earnings)
- `tgt-q3:overall`　合併可比銷售增 0.3%，客流增 2.4%。公告列示的是各品類及全店的業績。 [官方來源](https://corporate.target.com/press/release/2024/11/target-corporation-reports-third-quarter-earnings)

**封存裁定**　缺同店同客戶的購物籃、跨品類轉換或促銷歸因資料。可說 Beauty 與 Food & Beverage 並行成長，須保留 Beauty 為食品引流或貢獻該品類毛利的判斷。

### 純 Astra · 完成

[逐次回傳](raw/calls/H-04-astra.json) · [CLI 事件](raw/jobs/H-04-astra/events.jsonl) · [模型原始 JSON](raw/jobs/H-04-astra/answer.json) · [CLI 診斷](raw/jobs/H-04-astra/stderr.log)

**待查**　公告僅列品類及合併業績。要驗證美妝是否帶動食品飲料或民生必需品銷售，需要同筆交易的跨品類購買率及比較基期。資料也未具名供應商或揭露採購額，無法將美妝成長連結至特定交易對手的獲利。

**模型評分**　全對。將美妝是否帶動食品飲料或必需品銷售留待驗證，並指出需要同筆交易的跨品類購買率及比較基期。


### Harness V10 · 完成

[逐次回傳](raw/calls/H-04-harness.json) · [CLI 事件](raw/jobs/H-04-harness/events.jsonl) · [模型原始 JSON](raw/jobs/H-04-harness/answer.json) · [CLI 診斷](raw/jobs/H-04-harness/stderr.log)

**待查**　Beauty、Food & Beverage 與 Essentials 的可比銷售均有成長，但品類增幅無法辨識美妝客是否順帶購買食品或日用品，也無法辨識預算排擠。驗證需有 Target 披露同店跨品類購物籃變化，或取得非公開的交易明細並比較相似客群。

**模型評分**　全對。指出同店跨品類購物籃資料缺口，明確保留美妝是否帶動食品或日用品購買的判斷。


[判讀原始 JSON](raw/calls/H-04-judge.json) · [CLI 事件](raw/jobs/H-04-judge/events.jsonl) · [模型原始 JSON](raw/jobs/H-04-judge/answer.json) · [CLI 診斷](raw/jobs/H-04-judge/stderr.log)

## H-05 · Uber

**研究題目**　Uber 公布擴大既有合作。請提出可供研究員覆核的首稿。

**截止**　2024-09-13T23:59:59+00:00　**研究期限**　2025-12-31

- `uber-av:fleet`　Uber 將提供車隊管理，包含清潔、維修及車庫營運，Waymo 負責 Waymo Driver 的測試及操作。 [官方來源](https://investor.uber.com/news-events/news/press-release-details/2024/Uber-and-Waymo-Expand-Partnership-to-Bring-Autonomous-Ride-Hailing-to-Austin-and-Atlanta/default.aspx)
- `uber-av:network`　Uber 與 Waymo 公布擴大合作。Austin 和 Atlanta 規劃自 2025 年起以 Uber app 獨家提供 Waymo 自動駕駛叫車。 [官方來源](https://investor.uber.com/news-events/news/press-release-details/2024/Uber-and-Waymo-Expand-Partnership-to-Bring-Autonomous-Ride-Hailing-to-Austin-and-Atlanta/default.aspx)
- `uber-av:original`　合作城市、營運職責和車隊段落原文：Uber will provide fleet management services [官方來源](https://investor.uber.com/news-events/news/press-release-details/2024/Uber-and-Waymo-Expand-Partnership-to-Bring-Autonomous-Ride-Hailing-to-Austin-and-Atlanta/default.aspx)
- `uber-av:scale`　合作計畫讓車隊日後擴大至數百輛。公告未列實際總行程數、雙方費率或單趟貢獻。 [官方來源](https://investor.uber.com/news-events/news/press-release-details/2024/Uber-and-Waymo-Expand-Partnership-to-Bring-Autonomous-Ride-Hailing-to-Austin-and-Atlanta/default.aspx)

**封存裁定**　Waymo 車隊實際上線可把額外可叫車供給或營運職責導入 Uber 平台。驗證特定城市上線、可用車、行程或獨家通路，區分平台一般成長／既有司機替代。量化仍須單趟經濟與新增/替代需求。

### 純 Astra · 完成

[逐次回傳](raw/calls/H-05-astra.json) · [CLI 事件](raw/jobs/H-05-astra/events.jsonl) · [模型原始 JSON](raw/jobs/H-05-astra/answer.json) · [CLI 診斷](raw/jobs/H-05-astra/stderr.log)

**1. Uber 在 Austin 與 Atlanta 的車隊管理服務 → Uber · 兩市的 Uber app 叫車業務**

- 起點引文　uber-av:fleet
- 受影響業務引文　uber-av:network、uber-av:scale
- 傳導機制　Uber 負責清潔、維修與車庫營運。若這些工作能讓更多車輛在需求高峰可供派遣，Uber app 就有機會承接原本因缺車而無法完成的行程。
- 比較基準　截至 2024 年 9 月 13 日，兩市服務仍屬規劃。公告未提供上線前兩市的 Uber 總行程、候車時間或未能派車的訂單數。
- 必要條件　Waymo 完成測試並投入服務，新增車輛在供給不足的時段接單，且新增行程帶給 Uber 的收益足以覆蓋追加營運成本。
- 財務影響　若上述條件成立，新增行程可提高當地叫車業務的貢獻。僅憑自駕行程數，無法估計 Uber 的增量收益。
- 其他解釋　乘客可能從人類駕駛轉搭 Waymo。即使全市總行程增加，也可能來自同期需求成長。
- 查核指標　按城市比較上線前後尖峰時段的 Waymo 完成行程、Uber 全平台完成行程及候車時間。若有可比資料，再對照尚未提供服務的區域。
- 觀察期間　各市實際上線前後的可比期間，追蹤至 2025 年底
- 公開查核來源　Uber 與 Waymo 的城市上線公告、營運更新及 Uber 財報說明會，以實際揭露的城市資料為準。
- 截止日　2025-12-31
- 預測　若自駕車確實補足尖峰供給，服務區的候車時間應縮短，全平台完成行程相對可比區域也應增加。
- 推翻條件　若可比資料顯示 Waymo 增加的行程由人類駕駛行程等量轉出，且尖峰候車時間未改善，則補足供給的解釋失去支持。若缺少城市資料，則此項仍待驗證。

**待查**　公告未交代車隊管理報酬、成本分攤方式或訂單替代率，無法把車隊規模換算為 Uber 的獲利。

**模型評分**　全對。缺口指出管理報酬、成本分攤與訂單替代率仍未知，因此無法由車隊規模推算 Uber 獲利。

- 候選 1　四項語義均通過。公告支持 Uber 的車隊管理職責及兩市獨家叫車計畫。若車輛上線後填補尖峰缺口，且新增行程收益覆蓋追加成本，當地叫車業務貢獻可提高。可用具名營運更新及財報說明會查核同期間資料。若人類駕駛行程等量減少且候車時間未改善，則削弱補足供給的解釋。

### Harness V10 · 完成

[逐次回傳](raw/calls/H-05-harness.json) · [CLI 事件](raw/jobs/H-05-harness/events.jsonl) · [模型原始 JSON](raw/jobs/H-05-harness/answer.json) · [CLI 診斷](raw/jobs/H-05-harness/stderr.log)

**1. Uber app → Uber · fleet management services**

- 起點引文　uber-av:network
- 受影響業務引文　uber-av:original、uber-av:fleet
- 傳導機制　兩城獨家叫車計畫使 Uber 承接當地車隊管理。若車庫須先於乘客服務啟用，即使叫車日後順利上線，車庫仍可能先產生營運支出。
- 比較基準　未擴大合作時，Uber 無須為本案在兩城新增車庫作業。
- 必要條件　Uber 須實際開始營運至少一城的車庫，且在該城開放乘客叫車前即承擔未獲補償的支出。
- 財務影響　若條件成立，前置支出將壓低車隊管理業務初期的營業現金流。公告未揭露成本分攤、管理費或收款時點。
- 其他解釋　Waymo 可能支付建置費或最低管理費。車庫啟用公告可確認作業時序，只有雙方披露付款責任與時點，才能區分 Uber 墊款與已獲補償兩種情形。
- 查核指標　Austin、Atlanta 各自的 Uber 車庫實際啟用日與 Uber app 開放乘客叫車日之先後，作為前置支出期間的代理指標。
- 觀察期間　自 2024-09-13 公告至 2025 年底，逐城比較。
- 公開查核來源　Uber 投資人關係網站及 Uber、Waymo 的城市營運更新，查核有無載明實際啟用日期。
- 截止日　2025-12-31
- 預測　至少一城可觀察到 Uber 車庫早於當地乘客叫車服務啟用，支持先承接作業的機制。現金流影響仍取決於補償條款。
- 推翻條件　若兩城均有可核實的日期，且 Uber 車庫皆於當地乘客叫車服務開放當日或之後才啟用，即推翻前置營運期間的預測。

**待查**　車庫啟用日期可能未單獨公開。即使確認作業先行，仍缺雙方成本分攤與管理費收款資料。亦無證據顯示 Uber 從其他業務調撥人員或資本。

**模型評分**　全對。缺口點明啟用日期可能未公開，並保留成本分攤及收款時點的不確定性，也明確保留跨業務資源調撥的歸因。

- 候選 1　四項語義均通過。公告支持兩市獨家叫車計畫與 Uber 的車庫營運職責。若車庫先啟用且 Uber 在開放叫車前承擔未獲補償的支出，車隊管理初期營業現金流將受壓。若具名城市營運更新顯示兩市車庫均於叫車開放當日或之後啟用，即推翻前置營運預測。現金流仍須以付款責任與時點驗證。

[判讀原始 JSON](raw/calls/H-05-judge.json) · [CLI 事件](raw/jobs/H-05-judge/events.jsonl) · [模型原始 JSON](raw/jobs/H-05-judge/answer.json) · [CLI 診斷](raw/jobs/H-05-judge/stderr.log)

## H-06 · FedEx

**研究題目**　FedEx 董事會公告事業組合決定。請提出可供研究員覆核的首稿。

**截止**　2024-12-19T23:59:59+00:00　**研究期限**　2025-12-31

- `fdx-sep:capital`　公告描述以資本市場方式推動分離，預期符合美國聯邦所得稅免稅分離資格，未量化母公司實收款或指定其用途。 [官方來源](https://newsroom.fedex.com/newsroom/global-english/fedex-announces-intent-to-separate-fedex-freight-creating-two-industry-leading-public-companies)
- `fdx-sep:decision`　FedEx 董事會擬分拆 FedEx Freight，使其成為獨立上市公司。當時目標為 18 個月內完成，須待後續條件及核准。 [官方來源](https://newsroom.fedex.com/newsroom/global-english/fedex-announces-intent-to-separate-fedex-freight-creating-two-industry-leading-public-companies)
- `fdx-sep:original`　Transaction Process 段落原文：expected to qualify as a tax-free separation [官方來源](https://newsroom.fedex.com/newsroom/global-english/fedex-announces-intent-to-separate-fedex-freight-creating-two-industry-leading-public-companies)
- `fdx-q2:original`　同期財報標題重點原文：$1 Billion Share Repurchases Completed During Quarter [官方來源](https://newsroom.fedex.com/newsroom/global-english/fedex-reports-second-quarter-diluted-eps-of-3-03-and-adjusted-diluted-eps-of-4-05)
- `fdx-q2:repurchases`　同期財報說本季已完成 10 億美元回購。該數字是本季已發生事項。 [官方來源](https://newsroom.fedex.com/newsroom/global-english/fedex-reports-second-quarter-diluted-eps-of-3-03-and-adjusted-diluted-eps-of-4-05)

**封存裁定**　分拆計畫並不確立實收現金或回購、航空／其他業務資金去向。需要分拆資本結構、現金或分配條款、董事會用途與流量日期。已完成回購不得歸因於未完成交易。

### 純 Astra · 完成

[逐次回傳](raw/calls/H-06-astra.json) · [CLI 事件](raw/jobs/H-06-astra/events.jsonl) · [模型原始 JSON](raw/jobs/H-06-astra/answer.json) · [CLI 診斷](raw/jobs/H-06-astra/stderr.log)

**待查**　現有資料只揭露分拆意向與集團層級的歷史回購。要判斷分拆對留存業務的獲利影響，仍需共享成本、分拆後費用負擔或雙方服務協議的資料。公告也未具名揭露受影響的供應商或客戶。

**模型評分**　未全對。正確將回購描述為歷史事項，但所列缺口集中於共享成本與服務協議，未指出實收款、分配條款或資金用途缺口，也未明確排除將回購歸因於分拆。


### Harness V10 · 完成

[逐次回傳](raw/calls/H-06-harness.json) · [CLI 事件](raw/jobs/H-06-harness/events.jsonl) · [模型原始 JSON](raw/jobs/H-06-harness/answer.json) · [CLI 診斷](raw/jobs/H-06-harness/stderr.log)

**待查**　分拆公告未揭露 FedEx 母公司可取得的現金、資本支出重配金額或承接資源的具名業務。第二季已完成的 10 億美元回購也無法證明分拆資金流向。要檢驗跨業務影響，需有 FedEx 公開指明資源由哪項業務移往哪項業務，以及重配前後的金額或產能。

**模型評分**　全對。指出母公司實收現金、資源重配金額及承接業務均未披露，並明確拒絕用已完成的 10 億美元回購推定分拆資金流向。


[判讀原始 JSON](raw/calls/H-06-judge.json) · [CLI 事件](raw/jobs/H-06-judge/events.jsonl) · [模型原始 JSON](raw/jobs/H-06-judge/answer.json) · [CLI 診斷](raw/jobs/H-06-judge/stderr.log)

## H-07 · lululemon

**研究題目**　lululemon 公布新的多年合作。請提出可供研究員覆核的首稿。

**截止**　2023-09-27T23:59:59+00:00　**研究期限**　2024-12-31

- `lulu-pton:original`　聯合公告的合作交換與會員段落原文：Peloton will become the exclusive digital fitness content provider for lululemon [官方來源](https://corporate.lululemon.com/newsroom/press-releases/2023/09-27-2023-211026323)
- `lulu-pton:sales`　聯合公告描述以 Peloton 通路推出共同品牌服飾與相關計畫。此屬通路與供應安排。 [官方來源](https://corporate.lululemon.com/newsroom/press-releases/2023/09-27-2023-211026323)
- `lulu-pton:subscription`　從 2023 年 11 月 1 日起，lululemon Studio All-Access 會員會按當時同價取得 Peloton 課程。 [官方來源](https://corporate.lululemon.com/newsroom/press-releases/2023/09-27-2023-211026323)
- `lulu-pton:terms`　lululemon 與 Peloton 公布五年合作。Peloton 成為 lululemon 的獨家數位健身內容供應商，lululemon 成為 Peloton 主要運動服飾合作夥伴。 [官方來源](https://corporate.lululemon.com/newsroom/press-releases/2023/09-27-2023-211026323)

**封存裁定**　可選 Peloton 內容導入 Studio 與內容成本或會員留存，或 Peloton 的具名服飾通路連到 lululemon 增量銷售。查同價上線／可購服飾／新通路銷售，區分其他會員變動、季節折扣或原有服飾通路移轉；缺分潤或成本時只主張條件影響。

### 純 Astra · 完成

[逐次回傳](raw/calls/H-07-astra.json) · [CLI 事件](raw/jobs/H-07-astra/events.jsonl) · [模型原始 JSON](raw/jobs/H-07-astra/answer.json) · [CLI 診斷](raw/jobs/H-07-astra/stderr.log)

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

**模型評分**　全對。兩條路徑均符合標準。缺口指出通路毛利、可比會員留存及內容成本仍待披露，因此保留對獲利重要性的判斷。

- 候選 1　四項語義均通過。公告支持 Peloton 通路與聯名服飾上市計畫。補貨可驗證後續需求，增量毛利仍須扣除既有通路移轉的損失。若 lululemon 在財報說明會揭露同期移轉損失已抵銷合作貢獻，即推翻毛利增益。
- 候選 2　四項語義均通過。公告支持獨家供應與同價導入計畫。若課程留住原會退訂的會員，付費月份與訂閱收入可增加，獲利則取決於新增成本。財報或法說若顯示可比年資會員在導入後的續訂率及付費月份均未改善，即削弱留存假說。

### Harness V10 · 完成

[逐次回傳](raw/calls/H-07-harness.json) · [CLI 事件](raw/jobs/H-07-harness/events.jsonl) · [模型原始 JSON](raw/jobs/H-07-harness/answer.json) · [CLI 診斷](raw/jobs/H-07-harness/stderr.log)

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

**模型評分**　未全對。缺口指出內容成本與預算去向均未披露，保留對資源轉投服飾的歸因，也明確限制了公開收費條款可驗證的範圍。

- 候選 1　未命中主要傳導。公告支持獨家內容供應與同價接入計畫。延誤和抵免均為未確認的條件，未建立標準所指的內容成本或留存路徑。若因延誤抵免，受影響會員當期應付會費將降低，金額未明。官方同期條款可區分延誤補償與一般促銷，確認照原額收費即可推翻收費傳導。

[判讀原始 JSON](raw/calls/H-07-judge.json) · [CLI 事件](raw/jobs/H-07-judge/events.jsonl) · [模型原始 JSON](raw/jobs/H-07-judge/answer.json) · [CLI 診斷](raw/jobs/H-07-judge/stderr.log)

## H-08 · NIKE

**研究題目**　NIKE 公布季度財報。請提出可供研究員覆核的首稿。

**截止**　2024-12-19T23:59:59+00:00　**研究期限**　2025-06-30

- `nike-q2:direct`　第二財季 NIKE Direct 營收 50 億美元，按報告口徑年減 13%。NIKE Brand Digital 銷售年減 21%，自營門市銷售年減 2%。 [官方來源](https://investors.nike.com/sec-filings/all-sec-filings/content/0000320187-24-000069/q2fy25exhibit991er.htm)
- `nike-q2:margin`　集團毛利率下滑 1 個百分點至 43.6%。公告同時列出通路和合併財務表現。 [官方來源](https://investors.nike.com/sec-filings/all-sec-filings/content/0000320187-24-000069/q2fy25exhibit991er.htm)
- `nike-q2:original`　Second Quarter Income Statement Review原文：NIKE Direct revenues were $5.0 billion [官方來源](https://investors.nike.com/sec-filings/all-sec-filings/content/0000320187-24-000069/q2fy25exhibit991er.htm)
- `nike-q2:wholesale`　批發營收 69 億美元，按報告口徑年減 3%。 [官方來源](https://investors.nike.com/sec-filings/all-sec-filings/content/0000320187-24-000069/q2fy25exhibit991er.htm)

**封存裁定**　通路跌幅差異不證明相同顧客從 Direct 轉到批發。缺同款同市場銷量或庫存、通路配置或消費者遷移，保留替代效應與特定通路造成合併毛利變動的大小。

### 純 Astra · 完成

[逐次回傳](raw/calls/H-08-astra.json) · [CLI 事件](raw/jobs/H-08-astra/events.jsonl) · [模型原始 JSON](raw/jobs/H-08-astra/answer.json) · [CLI 診斷](raw/jobs/H-08-astra/stderr.log)

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

**模型評分**　未全對。已保留毛利歸因，但未點明缺少同款同市場、通路配置或顧客遷移證據，也未明確保留相同顧客轉往批發的歸因。

- 候選 1　四項語義均通過。公告支持通路營收與集團毛利率讀數，直營占兩通路營收約 42%。直營毛利率較高時，占比下降會對集團毛利率形成壓力，幅度仍未知。若 NIKE 同季公告明示通路組合貢獻為零或為正，即可排除該季由此機制拖累毛利率。

### Harness V10 · 完成

[逐次回傳](raw/calls/H-08-harness.json) · [CLI 事件](raw/jobs/H-08-harness/events.jsonl) · [模型原始 JSON](raw/jobs/H-08-harness/answer.json) · [CLI 診斷](raw/jobs/H-08-harness/stderr.log)

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

**模型評分**　全對。指出缺少通路配額與實際增購量，並明確保留改配歸因。

- 候選 1　四項語義均通過。公告支持數位銷售年減 21% 與批發營收年減 3%。改配、增購及認列均列為條件，批發營收增量方向明確，集團淨影響仍無法量化。NIKE 第三季若公開確認改配及通路商實際承接，可區分改配與例行補貨。單看批發年增率只能檢驗整體改善。

[判讀原始 JSON](raw/calls/H-08-judge.json) · [CLI 事件](raw/jobs/H-08-judge/events.jsonl) · [模型原始 JSON](raw/jobs/H-08-judge/answer.json) · [CLI 診斷](raw/jobs/H-08-judge/stderr.log)

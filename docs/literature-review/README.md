# 文獻綜述：與 hypogen 事件研究 Harness 相同難題的論文

截至 2026-11-23。本文只根據機械驗證過的證據卡撰寫，句末的 `[Pxx-cy]` 指向 [cards-verified.jsonl](cards-verified.jsonl) 中的卡片，每張卡都附論文原文的逐字引文。卡片的 `lines` 欄是抽取文字檔的行號，對照 PDF 時請用引文內容搜尋。論文清單見 [papers.csv](papers.csv)，查詢紀錄見 [search-log.md](search-log.md)，依本綜述整理的專案建議見 [project-recommendations.md](../project-recommendations.md)。P45 與 P563 只取得摘要，對應卡片標為 ABSTRACT_ONLY。

## 結論先講

這不是冷門問題。2025–2026 年有大量論文在處理本專案遇到的同一組困難，而且多數結論和你的觀察一致：

1. **Harness 對前沿模型的數字準確度幫助有限，優勢多半出現在結構、格式或評審偏好的面向。**
2. **用歷史回放評估前沿模型的預測能力，在方法上無法成立。**提示時點、匿名化和搜尋日期過濾都擋不住洩漏。
3. **LLM 評審不穩定**：換提示、換順序或換場次都會改變判決，而且和人類專家的一致率偏低。
4. **前瞻、以實際結果評分的評測是公認的黃金標準**，代價是要等待，樣本也少。
5. **反覆修改版本再評分，本身就會製造假發現。**

## 1. Harness 與裸模型：效果取決於模型強弱與評分方式

### 數字預測：harness 幾乎不改變誤差

- 和本專案最接近的是 **EPSBench**（149 個公司季度的 EPS 預測）。更換 harness 或提高推理強度，對點預測誤差的影響只有 −0.004 到 +0.001，所有配對差異的信賴區間都包含零 [P378-c2]。對 GPT-5.5 而言，最精簡的 vanilla 工具迴圈中位誤差 0.110，與 OpenCode harness 的配對差為 −0.003，90% 信賴區間跨零 [P378-c3]。同一案例三次重跑的中位離散是 0.057 [P378-c7]，比 harness 造成的差異還大。作者提醒，信賴區間跨零代表這個樣本量下無法分辨，不代表兩者等價 [P378-c8]。
- 領先模型的價格平減誤差 0.113–0.131%，與分析師共識的 0.111% 相當 [P378-c1]。80% 預測區間的實際涵蓋率只有 37–70% [P378-c4]。
- **FinDeepForecast**（每週更新的前瞻金融預測）：專門的深度研究 agent 只比內建搜尋的前沿模型高 3-4 個百分點 [P125-c6]。同一模型拿掉搜尋則掉 11.0 到 14.2 個百分點 [P125-c7]，可見關鍵在取得外部資訊，而不是流程架構。EPS 這類定期數字任務，最佳方法只有 25.5% [P125-c8]。
- **kw-bench** 固定模型比較不同 harness：在便宜模型上 harness 決定成敗（0.542、0.528 對 0.00）[P671-c1]；換成前沿模型後差異消失（0.9986 對 1.000）[P671-c2]。部分得分主要來自格式與分類，需要精確歐元數字的元件幾乎沒有貢獻（0.07、0.03）[P671-c4]。

- **Finance Agent Benchmark**：最佳的 o3 只有 46.8% [P77-c1]。這個基準有要求引用，但沒有檢查引用是否正確 [P77-c6]，使用的 harness 也只是簡單的 ReAct 迴圈 [P77-c7]。本專案的引用與時點驗證，正好補在這個缺口上。

### 被評審打分的產出：harness 看似大勝，但評審本身是主要變因

- **Better Deck or Different Judge?**（投行簡報）和你的情況最像。固定 27B 模型時，harness 比直接生成高 20.4 到 33.6 分（滿分 95）[P1183-c1]。但對上直接使用 Opus 的強模型，只差 −4.7 到 +0.8，大約打平 [P1183-c2]。內容項目的差距接近零，剩下的優勢主要來自視覺呈現 [P1183-c6]。分數變異有 59% 來自評審，只有 14% 來自簡報本身 [P1183-c3]。同一評審五天後重評同一批未改動的簡報，分數低了 13.0 [P1183-c4]。作者也承認，harness 是依 Opus 評審的回饋反覆調出來的，基準組卻只有單次樣本 [P1183-c7]。他們的建議是固定評審設定、重複評分，再來解讀小差異 [P1183-c8]。
- **FrontierFinance** 則是反方證據。in-house harness 得 56.0%，開源 harness 上的最強前沿模型得 49.2% [P682-c1]。Opus 4.8 只用網搜時是 33.0 [P682-c3]，接上 Finance Agent v2 工具 harness 後是 45.0 [P682-c4]。不過這是由專家 rubric 加上三個 LLM 評審多數決來評分，沒有人類評分 [P682-c5]。只有 in-house harness 真的在檢索層強制截止日期 [P682-c6]，而 A/B 順序互換會翻轉 7% 的共識結果 [P682-c8]。
- **FinSkillBench**（投資管理）：整理好的領域技能把平均分從 0.366 提高到 0.528 [P1270-c1]。但在基本面分析只多 +0.054 [P1270-c3]，而且越強的模型增益越小，例如 gpt-5.4 只有 +0.091 [P1270-c4]。同一處理在另一個 harness 下的增益是 +32.5，在自家 harness 下是 +16.2 [P1270-c5]。

### Harness 與模型會交互作用，應作為實驗條件揭露

- 換 harness 可能讓模型排名反轉。例如 Claude 在 OpenHands 領先 GPT 7.94 分，在 PI 卻落後 30.16 分 [P1323-c1]。66 種組合中，排名、最佳 harness 和原廠搭配的表現都依任務而定 [P1323-c7]。agent 失敗時的自我驗證也不能取代外部驗收標準 [P1323-c5]。
- 一篇立場論文主張，harness 應列為實驗條件的一部分：跨模型比較時要嘛鎖定 harness，要嘛把它當受控因子 [P1312-c7]。在他們的受控網格裡，harness 造成的變異是模型的 7.80× [P1312-c4]，但作者明說這個比例不具普遍性 [P1312-c5]。
- 銀行合規研究：固定模型時，harness 造成最多 11.5 個百分點的落差 [P1188-c1]，但交互作用檢定在 5% 水準不顯著 [P1188-c2]。對日期窗口、累計額度這類算術規則，作者主張在 harness 裡用確定性程式碼控制，而不是再加一次模型呼叫 [P1188-c6]。

### 分段呼叫與加入更多輸入

在財報前後的交易事件中，把決策拆成多段呼叫幾乎不改變報酬；加入同業、放空、內部人申報等資料，alpha 也只動了幾個基點 [P575-c5]。

## 2. 歷史回放的前視偏差：提示與匿名化都擋不住

- **核心論證**：模型如果看過實際結果，真實預測能力和記憶在觀測上無法區分，量到的記憶只是下限 [P386-c1]。在截止點前取大樣本、截止點後取小樣本做穩健性檢查，也無法分開兩者 [P386-c6]。建議只用模型訓練截止後的資料評估 [P386-c8]。
- **提示假裝截止無效。**要求 GPT-4o 忽略 2010 年以後的資訊，假截止點前後的 GDP 方向準確率仍是 97.6% 對 98.0%，真正截止後只有 40% [P386-c2]。即使提示讓準確率下降，模型也可能只是在扮演較差的預測者 [P386-c5]。提示對直接事實的「遺忘」成功率約 82.5%，對因果相關的事件只有 19.2% [P392-c1]。Simulated Ignorance 研究涵蓋 477 題、9 個模型，仍留下 52% 的落差，連鎖推理也壓不掉 [P137-c1]。推理模型的推理軌跡看起來比較乾淨，落差反而更大 [P137-c4]。作者建議用表現落差偵測洩漏，不要用推理軌跡審查 [P137-c7]。
- **匿名化也無效。**從遮名後的財報電話會議逐字稿，GPT-4o 認出 Apple、Meta、Microsoft 的比例是 100%，七大科技股都超過 85%，猜對 Apple 季度與年份的比例是 93.2% [P386-c7]。在交易事件研究中，只給 ticker 與日期的記憶探針，在截止前猜對 59.2% 的財報方向，截止後是 53.3% [P575-c2]。具名執行在截止前比匿名執行多賺 +30.3 bp，截止後反轉為 −22.0 bp [P575-c3]。作者建議：在舊事件上的具名結果，必須在匿名且截止後的事件上重現，才能報告為獲利 [P575-c6]。
- **相互衝突的證據。**以 GPT-4 分析標準化、匿名化的財務報表，作者宣稱方向預測勝過分析師，且不是來自訓練記憶 [P45-c1, P45-c3]（僅取得摘要）。這與上述匿名化失效的結果 [P386-c7] 方向相反，兩者使用的輸入不同：報表數字對比電話會議逐字稿。
- **搜尋日期過濾會漏。**Google 的 before: 過濾有 71.0% 的問題至少一頁含重大截止後資訊，DuckDuckGo 是 81.2%；直接透露答案的比例是 41.0% 與 54.8% [P872-c1]。洩漏文件會把 Brier 從 0.24 拉低到 0.10，膨脹量到的能力 [P872-c2]。頁面標示的更新日期不可靠，例如標 2020 年更新的頁面含 2023 年的事實 [P872-c3]。越舊的截止點漏得越多，2021–2022 年的題目超過 >46% 的網址含截止後資訊 [P872-c5]。建議改用凍結、帶時間戳的網頁快照 [P872-c7]。另一篇也有同類例子：限定 2024 年 1–9 月的搜尋，回傳了一個標 14 January 2024 卻已提到 October 2024 諾貝爾和平獎的頁面 [P17-c5]。
- **財務資料會被重述。**Enron 在 2002 年改寫了 1998-2001 的盈餘，許多資料庫不再保留原值 [P17-c6]。實際知識截止點可能比公告晚幾個月，回測時應留緩衝 [P17-c7]。
- **前後截止比較不是有效的洩漏檢查。**在所有題目都晚於截止點的情況下，四個旗艦模型仍被誤判有洩漏 [P585-c1]，光是時間越近就會產生 +0.044 到 +0.061 的假落差 [P585-c2]。反過來，前後表現持平也不能證明乾淨 [P585-c3]。建議改用已知截止點的斷點迴歸，或以匹配的乾淨對照模型做差異中的差異，並報告調整後分數 [P585-c5]。
- **工作流程本身的時點錯誤。**BuySideFlow 中，結果正確的執行有 193 of 380（50.8%）仍違反時點規則 [P667-c1]。最常見的錯誤是把報告期間當成公開日期，例如在 12 月的決策中使用隔年 3 月才公布的年報 [P667-c3]。規則式檢查器的召回率只有 34.9% [P667-c5]。把時點規範寫進提示後，違規率從 66% 降到 54%，但沒有消除 [P667-c7]。
- **洩漏的規模。**把熱門 LLM 交易 agent 移到截止後的資料，最佳 agent 的報酬減半（50%）[P94-c1]。用反事實擾動輸入（改掉財報等關鍵事件）測試，FinMem 有 82% 的預測不變 [P94-c5]。
- **領域的證據標準。**一篇預註冊的審計涵蓋 91 篇 LLM 交易論文：在截止點可能與測試期重疊的 51 篇裡，有 50 篇（98%）沒有任何控制措施 [P627-c6, P627-c2]；測試期中位數只有 12 個月 [P627-c1]。作者提出最低報告標準，包括測試期間、模型訓練截止點與測試是否在其後、成本模型，以及嘗試過的策略或提示數量 [P627-c7]。
- 其他：有研究提出以事前不可預測事件做前視偏差的直接檢定，並建議使用只以分析期之前文本預訓練的模型 [P563-c1, P563-c2]（僅摘要）。點時模型在交易流程中沒有 alpha 衰減，一般模型則衰減超過 -15 個百分點 [P01-c1]，但只測了五檔大型科技股 [P01-c8]，點時模型也只來自單一商業供應商 [P01-c6]。

## 3. LLM 評審：不穩定、會偏袒、和金融專家不一致

- **提示措辭就會翻轉判決。**一個合理的措辭改動，改變了超過一半相同配對的判決 [P343-c1]；比較兩個系統時，翻轉了四分之一到三分之一的判決，較強系統的勝率最多移動 29 個百分點 [P343-c4]。
- **順序偏誤。**GPT-4 的位置一致性只有 0.82 與 0.83 [P313-c4]，品質接近的配對最容易受影響 [P313-c5]。把順序不一致記成平手可以用上所有判決，但並沒有消除偏誤 [P313-c7]。同家族的評審彼此高度一致，不能當成獨立評分者 [P313-c6]。
- **自我偏好與同源洩漏。**GPT-4 有顯著的自我偏好 [P309-c2]，來源可能是對熟悉文字（低困惑度）的偏好 [P309-c5]。評審與生成資料的模型同家族同系列時，偏好洩漏約 8.9%，換成不同系列降到 2.8% [P320-c3]；主觀題目的洩漏更大 [P320-c4]。只叫評審保持公正沒有效果（18.3 對基準 17.8），用保留的人類標註集做情境校準效果最好（7.3）[P320-c7]。
- **評審分數和實際結果脫節。**HindSight 用真實的後續論文來評研究構想：LLM 評審給兩組系統的分數幾乎相同（7.44 對 7.40），結果分數卻是 0.297 對 0.119 [P341-c4]。評審甚至更喜歡較弱的基準組 [P341-c5]，評審給的新穎性和實際結果呈負相關 [P341-c6]。作者警告，對評審分數做優化，可能把系統推向聽起來厲害但空洞的輸出 [P341-c7]。在研究構想上，最好的 LLM 評審和專家的一致率是 53.3%，專家彼此之間也只有 56.1% [P334-c7, P334-c6]。構想階段的分數和執行後的分數相關很弱 [P335-c6]；AI 構想執行後在興奮度與有效性上分別下降 1.760 與 1.879 [P335-c4]。
- **金融文本的證據。**
  - 葡萄牙文財經評論：LLM 評審與人類的逐項一致率平均 27.2% [P1197-c1]。被評審選為勝出的評論，事實性分數反而較低 [P1197-c6]。金融專家的首選模型沒有拿到任何 LLM 評審的票 [P1197-c4]。
  - 股價因果機制解釋：完整性與人類的相關係數 r 為 0.679-0.775，相關性為 0.557-0.664 [P1343-c2]；經濟合理性的 kappa 在 0.326 到 0.591 之間 [P1343-c3]；加入 few-shot 範例後一致性反而下降 [P1343-c6]。該研究只有一位人工標註者 [P1343-c7]。
  - 金融論文審稿：GPT-4o 只有正確性與表達的評分具預測力，原創性與重要性沒有 [P10-c1]。作者建議技術查核交給模型，貢獻判斷留給人 [P10-c7]。
  - 投資研究 agent 評估框架：兩個 LLM 評審有 48.8% 的配對評估需要轉交專家裁決 [P665-c8]，專家覆核後三個 agent 的分數都下降 [P665-c6]。

### 需要多少人工評分

- Alternative Annotator Test 需要至少三位人類標註者、50-100 個例子 [P1334-c1]。以 epsilon = 0.2 而言，LLM 通常在 100 例內通過，一半的資料集不到 50 例就通過 [P1334-c2]；ε 取 0.1 則約需要加倍，三個資料集始終無法通過 [P1334-c3]。比較對象是可信賴的專家時，作者建議 ε 取 0.2 [P1334-c5]。
- 理論上限：評審不比被評模型準確時，任何去偏方法都無法把所需的真實標註減少超過一半 [P1352-c1]。在前沿模型上，LLM 評審改變不了所需人工標註的數量級 [P1352-c7]。

## 4. 前瞻評測和歷史回放的取捨

- 黃金標準是對尚未揭曉的問題作答，等結果出來再評分；回測只是求快的替代方案 [P17-c1]。ForecastBench 只收作答時答案未知的未來事件題 [P116-c1]，作者並指出靜態基準會因為截止點只是估計而被污染 [P116-c2]。最佳 LLM 的 Brier 是 0.122，和一般大眾的 0.121 相當，超級預測者是 0.096 [P116-c3]。加入檢索到的新聞並沒有改善 [P116-c5]。
- FinDeepForecast 每週出新題，等真實結果揭露後才評分 [P125-c2]；數字題用固定容差做確定性評分，不用 LLM 評審 [P125-c4]。
- 折衷做法是用凍結語料的「pastcasting」[P132-c1]。它和前瞻結果大致一致，但作者說需要更大樣本驗證 [P132-c5]。同一題重跑時，答案可能從低於 20% 跳到高於 80% [P132-c6]，而且新模型懂得比較多新近事件，這個干擾沒有被控制 [P132-c8]。
- 另一種不會洩漏的設計：由分析師撰寫虛構但合理的事件，混入真實新聞，用專家標籤做精確比對評分 [P692-c2, P692-c3]。這個基準中，所有 agent 都跟著年增的利多標題走，沒有算出數字所隱含的負向季度指引修正 [P692-c6]。
- 實際上線的多 agent 系統以即時訊號評估 [P34-c3]，主要的顯著結果只靠 19 個月度觀測 [P34-c6]。
- 一個 BTC 永續合約研究在等候選預算下，agent 和隨機搜尋各得 39 個合格候選，作者因此拒絕「agent 搜尋較優」的說法 [P1224-c5, P1224-c6]。研究協定是在資料期間結束後才鎖定，所以作者稱之為一次性歷史保留集，而不是前瞻測試 [P1224-c8]。

## 5. 反覆改版本身就會製造假發現

- 在交易研究中，「提出修改、跑實驗、指標變好就保留」的迴圈預設就是假發現機器 [P304-c1]。一個在發現期與驗證期 Sharpe 接近 3 的規則，在只開一次的保留集掉到 0.26 [P304-c2]。他們的防護措施：保留集只能開一次，而且開之前必須先寫下收據 [P304-c4]；候選要通過所有門檻才算數 [P304-c5]；重複或只調一個參數的變體不計，讓試驗數反映真實的想法數 [P304-c6]。
- 一個出貨中的金融 agent：用自動優化迴圈改提示，開發集的 +14 到了保留題只剩 +1.5，信賴區間 −5.3 到 +7.2 [P84-c3]。結構性修改能推廣到新題目，依開發題寫的個案規則則不能 [P84-c4]。同樣的七次執行，通過的 rubric 條目在 149 項中介於 105 到 123 [P84-c1]。
- 在提示裡叫 LLM 避免前視偏差，是很弱的防護 [P26-c4]。單一預註冊假說幾乎不受多重檢定折減，廣泛搜尋則要付出更高的門檻 [P26-c5]。一個真實 Sharpe 0.6 的策略，大約需要十一年的樣本外資料才能達到 t≈2 [P26-c6]。
- 預註冊審計本身的檢定也因樣本太少而缺乏檢定力 [P627-c5]。

## 對本專案的對照與建議

以下是作者（本綜述）的推論，論文證據附在括號內。

1. **你的結果模式是文獻中的常態，不是個別失敗。**數字預測上 harness 打平或輸給同一個前沿模型 [P378-c2, P125-c6, P671-c2]；評審分數上的勝利很容易來自呈現方式或評審變異 [P1183-c3, P1183-c6]。V8 到 V9 的分數從 4.58 跳到 9.80，與提示措辭翻轉判決的現象 [P343-c4] 相符。
2. **歷史回放無法證明預測能力。**`as_of` 提示與匿名化屬於已被證明無效的做法 [P386-c2, P386-c7, P137-c1]。`historical_replay` 以公告日期當可得時點代理，正是搜尋日期過濾研究所警告的情形 [P872-c1, P872-c3]。2019–2024 的回放落在洩漏較多的年代 [P872-c5]。可行的補救：
   - 加入只給 ticker 與日期的記憶探針 [P575-c2]；
   - 加入擾動輸入測試 [P94-c4]；
   - 改用斷點迴歸或匹配對照做差異中的差異 [P585-c5]；
   - 建立凍結網頁快照 [P872-c7]；
   - 主要結論改用截止後或前瞻資料 [P386-c8, P137-c7]。
   你已經在做前瞻佇列，方向是對的。
3. **評審。**Sol 若與 Astra 同源，有同家族一致性與偏好洩漏的風險 [P313-c6, P320-c3]；交換順序不能消除位置偏誤 [P313-c7]。人工評分可以照 alt-test 規劃：至少 3 位專家評 50-100 份假說，各評分維度分開檢定 [P1334-c1, P1334-c2]。用少量人工標註校準評審，效果遠勝要求評審保持公正 [P320-c7]。也可以把評審限縮在可查核的維度，例如證據支持與邏輯，原創性與重要性交給人判斷 [P10-c1, P10-c7]。
4. **迭代紀律。**每個版本都要算進試驗數 [P26-c5, P304-c6]，保留集只開一次 [P304-c4]。驗證器逐案修規則（例如複數 revenues、多層表頭、單位左欄）屬於個案規則，文獻顯示這類修改難以推廣到新題目 [P84-c4]。
5. **文獻支持 harness 有實際價值的地方**，可以考慮作為定位：
   - 算術與規則交給確定性程式碼 [P1188-c6]，對應你的 Decimal 財務橋接；
   - 時點約束在資料層強制執行，不靠提示 [P26-c4, P667-c7]；
   - 稽核實際執行的步驟，而不只看輸出 [P667-c1, P1188-c7]；
   - 前沿 agent 普遍算錯季度指引修正 [P692-c6]，這是能用確定性評分驗證你指引核對功能的具體題型。

## 參考文獻（本綜述精讀的 44 篇）

| 編號 | 年 | 論文 | 來源 | 主題 |
|---|---|---|---|---|
| P378 | 2026 | EPSBench: Benchmarking LLM Agents for Earnings Forecasting | arXiv:2610.38293 | Harness 與數字預測 |
| P1183 | 2026 | Better Deck or Different Judge? Evaluating Agentic Harness Gains in Corporate and Investment Banking | arXiv:2609.39958 | Harness 增益與評審變異 |
| P671 | 2026 | kw-bench: Breaking Frontier Harnesses on Real-World Tasks | arXiv:2610.36405 | Harness 比較 |
| P682 | 2026 | FrontierFinance: A Challenging Benchmark for Measuring Frontier Intelligence of Finance Agents | arXiv:2608.11683 | 金融 agent 基準 |
| P1270 | 2026 | FinSkillBench: Evaluating AI Agents and Domain Skills for Investment Management | arXiv:2608.18099 | 領域技能與 harness |
| P1323 | 2026 | Finding the Right Fit: Model-Harness Interactions across Agent Tasks | doi:10.48550/arxiv.2610.00917 | 模型與 harness 交互 |
| P1312 | 2026 | Stop Comparing LLM Agents Without Disclosing the Harness | doi:10.20944/preprints202605.0711.v1 | Harness 揭露 |
| P1188 | 2026 | The Harness Is the Model: Agent Scaffolding Changes a Fixed LLM's Compliance with Banking Conduct Rules | arXiv:2611.06116 | Harness 效果 |
| P84 | 2026 | Can You Trust Your Finance Agent? Drift, Diagnosis and Auditable Intervention on One Shipped Financial Research Agent | arXiv:2611.17939 | 執行變異與迭代 |
| P665 | 2026 | Reliable Evaluation of AI Agents for Investment Research | arXiv:2611.22338 | 研究 agent 評估 |
| P77 | 2025 | Finance Agent Benchmark: Benchmarking LLMs on Real-world Financial Research Tasks | arXiv:2508.00828 | 金融 agent 基準 |
| P692 | 2026 | Frontier Financial Judgement: Can agents tell what might move a stock? | arXiv:2607.20645 | 事件判斷與防洩漏設計 |
| P125 | 2026 | FinDeepForecast: A Live Multi-Agent System for Benchmarking Deep Research Agents in Financial Forecasting | arXiv:2601.05039 | 前瞻金融預測 |
| P34 | 2026 | Signal or Noise in Multi-Agent LLM-based Stock Recommendations? | arXiv:2604.17327 | 即時評估 |
| P386 | 2025 | The Memorization Problem: Can We Trust LLMs' Economic Forecasts? | arXiv:2504.14765 | 記憶與前視偏差 |
| P392 | 2025 | Can Prompts Rewind Time for LLMs? | doi:10.18653/v1/2025.emnlp-main.1049 | 提示截止點 |
| P137 | 2026 | Simulated Ignorance Fails | arXiv:2601.13717 | 提示截止點 |
| P872 | 2026 | Temporal Leakage in Search-Engine Date-Filtered Web Retrieval | arXiv:2602.00758 | 搜尋日期洩漏 |
| P585 | 2026 | Temporal Leakage in LLM Backtesting: Measurement, Validation, and Adjusted Scores | arXiv:2608.02985 | 洩漏檢定 |
| P17 | 2025 | Pitfalls in Evaluating Language Model Forecasters | arXiv:2506.00723 | 預測評估陷阱 |
| P575 | 2026 | The Only Edge Was Memorized in Training: LLM Trading Agents Around Earnings and Bad News | arXiv:2611.22177 | 財報事件與記憶 |
| P94 | 2025 | Profit Mirage: Revisiting Information Leakage in LLM-based Financial Agents | arXiv:2510.07920 | 交易 agent 洩漏 |
| P667 | 2026 | BuySideFlow: A Point-in-Time Benchmark for LLM Agents in Investment Research | arXiv:2611.12966 | 流程時點錯誤 |
| P627 | 2026 | Short Windows, Unmodelled Costs, Unknown Cutoffs: A Pre-Registered Evidence Audit of 91 LLM Trading Papers | arXiv:2611.18934 | 證據標準審計 |
| P01 | 2026 | Look-Ahead-Bench | arXiv:2601.13770 | 點時模型 |
| P45 | 2024 | Financial Statement Analysis with Large Language Models（僅摘要） | arXiv:2407.17866 | 財報分析 |
| P563 | 2024 | Lookahead Bias in Pretrained Language Models（僅摘要） | doi:10.2139/ssrn.4754678 | 前視偏差檢定 |
| P343 | 2026 | Old Ideas, Novel Problems: The Instability of LLM-Based Novelty Evaluation | doi:10.48550/arxiv.2610.02022 | 評審不穩定 |
| P313 | 2025 | Judging the Judges: A Systematic Study of Position Bias in LLM-as-a-Judge | doi:10.18653/v1/2025.ijcnlp-long.18 | 順序偏誤 |
| P309 | 2024 | Self-Preference Bias in LLM-as-a-Judge | doi:10.48550/arxiv.2410.21819 | 自我偏好 |
| P320 | 2026 | Preference Leakage: A Contamination Problem in LLM-as-a-judge | doi:10.48550/arxiv.2502.01534 | 同源偏好 |
| P341 | 2026 | HindSight: Evaluating LLM-Generated Research Ideas via Future Impact | doi:10.48550/arxiv.2603.15164 | 結果評分與評審 |
| P334 | 2025 | Can LLMs Generate Novel Research Ideas? | arXiv:2409.04109 | 人類盲評 |
| P335 | 2026 | The Ideation-Execution Gap | arXiv:2506.20803 | 構想與執行落差 |
| P1197 | 2026 | Do LLM Judges Agree with Humans? Evaluating Financial Commentaries from Material Facts | doi:10.5753/stil.2026.26484 | 金融評審一致性 |
| P1343 | 2026 | Preliminary Study on LLM-as-a-Judge Evaluation of Causal Mechanism Explanations in Financial News | doi:10.18653/2026.finnlp-1.39 | 因果機制評審 |
| P10 | 2026 | How Well Do LLMs Perform in Peer Review? Evidence from Finance and Accounting | arXiv:2610.18435 | 金融審稿 |
| P1334 | 2025 | The Alternative Annotator Test for LLM-as-a-Judge | doi:10.18653/v1/2025.acl-long.782 | 人工標註需求 |
| P1352 | 2025 | Limits to scalable evaluation at the frontier: LLM as Judge won't beat twice the data | doi:10.48550/arxiv.2410.13341 | 評審理論上限 |
| P116 | 2024 | ForecastBench: A Dynamic Benchmark of AI Forecasting Capabilities | arXiv:2409.19839 | 前瞻基準 |
| P132 | 2025 | Bench to the Future: A Pastcasting Benchmark for Forecasting Agents | arXiv:2506.21558 | 凍結語料回放 |
| P304 | 2026 | Hard to Fool: A Bounded LLM Research Loop for Quantitative Finance | arXiv:2611.06607 | 研究迴圈假發現 |
| P26 | 2026 | What survives honest evaluation? | arXiv:2608.27734 | 搜尋折減與前視偏差 |
| P1224 | 2026 | Point-in-Time Audit Before Alpha | doi:10.48550/arxiv.2608.25348 | 等預算比較 |

## 搜尋方法與限制

- **查詢**：33 組查詢加一輪引用追蹤（8 篇種子論文，往前、往後各追），來源為 arXiv、Semantic Scholar 和 OpenAlex。去重後共 1,358 篇，依標題與摘要篩選出 44 篇精讀：42 篇全文，2 篇只取得摘要。
- **證據卡**：341 張全部通過逐字比對。其中 59 張的引文原本把 PDF 換行斷字寫成「字- 字」，已依原文改為連寫後重新驗證。
- **回收率稽核**：拿兩篇綜述性論文的參考文獻比對（91 篇 LLM 交易論文審計，以及一篇金融多 agent 系統評估綜述），48 筆中已收錄 39 筆。漏掉的 9 筆多是多 agent 交易系統的設計論文，不在本次核心範圍；唯一和評測方法相關的是 *When Agents Trade: Live Multi-Market Trading Benchmark for LLM Agents*。
- **未達飽和**：最後三組以「harness」為關鍵字的查詢仍各帶來 33、28、25 篇新論文，所以不能保證沒有遺漏。Semantic Scholar 有三組查詢因 HTTP 429 限流沒有結果，那是失敗，不代表沒有相關論文。
- **未精讀但高度相關的候選**（只依標題列出，未讀內文）：Model or Harness? An Interaction-Centric Taxonomy for Localizing Agent Failures；Harness Leverage Across Model Size；Meta-Harness: End-to-End Optimization of Model Harnesses；Rethinking the Evaluation of Harness Evolution for Agents；FinanceHarness: Autonomous Financial Deep Research Framework；DeepFinance: Can AI Diligence a $100MM Deal?；FinAutoRubric；Deep FinResearch Bench；FinCutBench；Reading or Remembering? Measuring Temporal Contamination in Language Models；Does Autonomous Quant Research Improve? Leakage, Evidence Scarcity and Forward Tests。
- **年代提醒**：多數論文是 2026 年的預印本，尚未經同儕審查。部分結論來自小樣本，例如 19 個月、5 檔股票、單一標註者，各卡片已註明。

"""Primary-source snapshots selected before inference for the V9 first-draft holdout."""

from benchmarks.hypothesis_cases import archived, load_cases
from research_app.schema import Event


PILOT_ANCHORS = {
    "V-01": {"ups-q4:volume": "lower its volume by more than 50% by the second half of 2026"},
    "V-02": {"dis-fy24:fy25": "Entertainment DTC operating income increase of approximately $875 million versus fiscal 2024"},
    "V-03": {"novo-sites:capacity": "The acquisition is expected to gradually increase Novo Nordisk’s filling capacity from 2026 and onwards."},
    "V-04": {"ford-ev-strategy:plans": "an all-new commercial van that will begin production in 2026 in Ohio"},
}

# These Chinese summaries are point-in-time data. Short original anchors are exported for review only.
HOLDOUT = [
    ("Adobe", "軟體", "監管與併購終止", "2023-12-18", "2024-12-31",
     "Adobe 與 Figma 宣布終止原收購協議。這個事件對 Adobe 的營運可能有哪些不同影響？",
     [
         (archived("adbe-termination", "2023-12-18",
                   "https://www.sec.gov/Archives/edgar/data/796343/000079634323000254/adbe-20231217.htm",
                   fee="Adobe 公布雙方在 12 月 17 日簽署終止協議。Adobe 須在三個營業日內向 Figma 支付 10 億美元現金。"),
          {"fee": "a cash payment to Figma in the previously agreed amount of one billion dollars"}),
         (archived("adbe-joint-release", "2023-12-18",
                   "https://www.sec.gov/Archives/edgar/data/796343/000079634323000254/adbedecember182023pressrel.htm",
                   regulation="雙方表示無法看到取得英國競爭及市場管理局與歐盟執委會所需批准的明確途徑。原協議擬以現金與股票收購 Figma。"),
          {"regulation": "there is no clear path to receive necessary regulatory approvals"}),
     ]),
    ("ExxonMobil", "石油與天然氣", "資產整併", "2024-05-03", "2025-12-31",
     "ExxonMobil 宣布完成收購 Pioneer Natural Resources。分析其營運傳導。",
     [(archived("xom-pioneer", "2024-05-03",
                "https://corporate.exxonmobil.com/news/news-releases/2024/0503_exxonmobil-completes-acquisition-of-pioneer-natural-resources",
                output="公司以 2023 年產量估算，交易使二疊紀盆地日產量增逾一倍至 130 萬桶油當量，初估 2027 年達約 200 萬桶油當量。",
                acreage="公告把相鄰探勘資產、技術與營運能力結合，列為交易可提高資源回收的依據。"),
       {"output": "will more than double to 1.3 million barrels of oil equivalent per day"})]),
    ("Starbucks", "餐飲零售", "營運重整與指引撤回", "2024-10-22", "2025-12-31",
     "Starbucks 公布初步第四季數字並暫停下一財年指引。分析重整可能如何影響營運。",
     [(archived("sbux-prelim", "2024-10-22",
                "https://about.starbucks.com/press/2024/starbucks-reports-preliminary-q4-and-full-fiscal-year-2024-results/",
                sales="第四季全球同店銷售年減 7%，美國同店銷售年減 6%，中國同店銷售年減 14%。",
                drivers="公司將表現歸因於客流走弱、加碼投入未改善顧客行為，以及中國景氣與競爭壓力。",
                guidance="公司因執行長交接與目前營運情況，暫停整個 2025 財年的指引。"),
       {"guidance": "guidance will be suspended for the full fiscal year 2025"})]),
    ("Visa", "支付網路", "競爭執法", "2024-09-24", "2025-12-31",
     "美國司法部對 Visa 的扣帳卡網路業務提起民事反壟斷訴訟。分析這項事件可能如何影響 Visa。",
     [
         (archived("visa-doj", "2024-09-24",
                   "https://www.justice.gov/archives/opa/pr/justice-department-sues-visa-monopolizing-debit-markets",
                   allegation="司法部提出民事訴訟，指控 Visa 在扣帳卡網路市場壟斷及有其他違法行為。",
                   contracts="起訴指稱 Visa 以交易量承諾約束商戶、收單機構與發卡機構。這些是司法部指控。"),
          {"allegation": "filed a civil antitrust lawsuit today against Visa"}),
         (archived("visa-q3", "2024-07-23",
                   "https://www.sec.gov/Archives/edgar/data/1403161/000140316124000040/q32024earningsrelease.htm",
                   baseline="Visa 第三財季合併淨營收 89 億美元，年增 10%；資料處理收入 45 億美元，年增 9%。這些是全球口徑。"),
          {"baseline": "Data processing revenue rose 9% over the prior year to $4.5 billion."}),
     ]),
    ("Johnson & Johnson", "醫療器材", "新技術整併", "2024-05-31", "2025-12-31",
     "Johnson & Johnson 完成收購 Shockwave Medical。分析其醫療器材業務可能出現的不同變化。",
     [
         (archived("jnj-shockwave-close", "2024-05-31",
                   "https://www.investor.jnj.com/investor-news/news-details/2024/Johnson--Johnson-Completes-Acquisition-of-Shockwave-Medical/default.aspx",
                   portfolio="Johnson & Johnson 公布完成交易，Shockwave 的血管內震波碎石（IVL）技術補充其心血管介入器材組合。"),
          {"portfolio": "Completes Acquisition of Shockwave Medical"}),
         (archived("jnj-shockwave-terms", "2024-04-05",
                   "https://www.investor.jnj.com/investor-news/news-details/2024/Johnson--Johnson-to-Acquire-Shockwave-Medical/default.aspx",
                   terms="交易對價為每股 335 美元現金。包含取得的現金，企業價值約 131 億美元。"),
          {"terms": "corresponding to an enterprise value of approximately $13.1 billion including cash acquired"}),
     ]),
    ("Spotify", "音訊串流", "訂閱定價", "2024-06-03", "2025-06-30",
     "Spotify 公布美國 Premium 套餐調價。分析調價可能如何影響訂閱業務。",
     [
         (archived("spot-us-prices", "2024-06-03",
                   "https://newsroom.spotify.com/2024-06-03/adjusting-spotify-premium-prices-in-the-us/",
                   prices="美國新訂戶的 Individual、Duo、Family、Student 價格分別為 11.99、16.99、19.99、5.99 美元。",
                   rollout="Spotify 說未來一個月會以電子郵件通知美國現有訂戶。"),
          {"rollout": "Over the next month, subscribers in the U.S. will receive an email"}),
         (archived("spot-prior-prices", "2023-07-24",
                   "https://newsroom.spotify.com/2023-07-24/adjusting-our-spotify-premium-prices/",
                   comparison="2023 年公告的同四種美國套餐價格分別為 10.99、14.99、16.99、5.99 美元。"),
          {"comparison": "$10.99 $14.99 $16.99 $5.99"}),
     ]),
    ("Delta Air Lines", "航空", "營運中斷", "2024-08-08", "2025-06-30",
     "Delta Air Lines 公布 7 月資訊系統中斷的估計財務影響。分析這項事件可能如何傳導。",
     [(archived("dal-outage", "2024-08-08",
                "https://www.sec.gov/Archives/edgar/data/27904/000168316824005369/delta_8k.htm",
                cancellations="Delta 報告 7 月 19 日起受到 CrowdStrike 相關故障影響，約 7,000 個航班在五天內取消。",
                revenue="公司估計 9 月季度有 3.8 億美元直接營收影響，主要來自退款及現金或 SkyMiles 補償。",
                costs="公司估計新增約 1.7 億美元非燃油支出，部分由取消航班減少燃油成本抵減。"),
       {"revenue": "the direct revenue impact of the incident is estimated to be $380 million"})]),
    ("Ørsted", "再生能源", "專案取消與資本配置", "2023-10-31", "2024-12-31",
     "Ørsted 宣布終止兩個美國離岸風電案，並對另一個專案做出最終投資決策。分析專案組合變更。",
     [(archived("orsted-us-wind", "2023-10-31",
                "https://orsted.com/en/company-announcement-list/2023/10/oersted-ceases-development-of-its-us-offshore-wind-73751",
                portfolio="董事會決議停止 Ocean Wind 1 和 2，並對 Revolution Wind 做出最終投資決策。",
                impairment="首九個月總減損為 284 億丹麥克朗，其中 199 億與 Ocean Wind 1 有關。",
                provision="Ocean Wind 1 的潛在解約成本準備估計約 80 至 110 億丹麥克朗，影響第四季 EBITDA。"),
       {"portfolio": "has taken final investment decision on the Revolution Wind project"})]),
]


def profiles():
    rows = {
        case_id: {"name": name, "split": "pilot", "event": event, "anchors": PILOT_ANCHORS[case_id]}
        for case_id, (name, event) in load_cases(holdout=True).items()
    }
    for index, (issuer, sector, event_type, day, horizon, question, documents) in enumerate(HOLDOUT, 1):
        event = Event.model_validate({
            "event_text": question, "as_of": f"{day}T23:59:59Z", "research_target": issuer,
            "research_horizon": horizon, "documents": [document for document, _ in documents],
        })
        anchors = {f"{document['id']}:{key}": quote
                   for document, excerpts in documents for key, quote in excerpts.items()}
        rows[f"E-{index:02d}"] = {
            "name": f"{issuer}｜{event_type}", "split": "holdout", "event": event, "anchors": anchors, "sector": sector,
        }
    used = {event.research_target for _, event in load_cases().values()}
    targets = [row["event"].research_target for row in rows.values()]
    if len(set(targets)) != len(targets) or used.intersection(targets):
        raise ValueError("同一發行人曾參與 V9 開發、先導或保留集")
    return rows

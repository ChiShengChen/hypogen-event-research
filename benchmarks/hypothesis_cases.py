"""Financial event snapshots for the hypothesis-generation benchmark."""

from pathlib import Path

from research_app.research import build_context, document_evidence
from research_app.schema import Event

EXAMPLES = Path(__file__).resolve().parents[1] / "research_app" / "examples"
EXAMPLE_CASES = {
    "ASML 2024 Q3": ("asml-q3", "2025-12-31"),
    "Intel High-NA": ("intel-high-na", "2025-12-31"),
    "NVIDIA H20": ("nvidia-h20", "2025-08-31"),
}


def archived(source_id, published, url, **paragraphs):
    timestamp = f"{published}T23:59:59Z"
    return {
        "id": source_id,
        "source": url,
        "kind": "disclosure",
        "text_format": "summary",
        "availability_basis": "replay_day_end",
        "published_at": timestamp,
        "obtained_at": timestamp,
        "paragraphs": paragraphs,
    }


# Paragraphs paraphrase the linked releases. Their dates refer to the disclosures.
ADDITIONAL_CASES = {
    "NVIDIA Blackwell": {
        "event_text": "NVIDIA 於 2024 年 3 月發布 Blackwell 資料中心 GPU 平台。",
        "as_of": "2024-03-31T23:59:59Z",
        "research_target": "NVIDIA",
        "research_horizon": "2025-03-31",
        "documents": [
            archived(
                "blackwell", "2024-03-18",
                "https://investor.nvidia.com/news/press-release-details/2024/NVIDIA-Blackwell-Platform-Arrives-to-Power-a-New-Era-of-Computing/",
                production="Blackwell GPU 採 TSMC 客製 4NP 製程。GB200 由 Grace CPU 與兩顆 Blackwell GPU 組成。",
                partners="AWS 等雲端業者規劃於 2024 年推出 Grace Blackwell 執行個體。Dell、Supermicro 和其他系統商預計推出 Blackwell 伺服器。",
            ),
            archived(
                "nvda-fy24", "2024-02-21",
                "https://investor.nvidia.com/news/press-release-details/2024/NVIDIA-Announces-Financial-Results-for-Fourth-Quarter-and-Fiscal-2024/",
                earnings="NVIDIA FY2024 Q4 營收 221 億美元，其中資料中心 184 億美元，資料中心營收季增 27%。",
            ),
        ],
    },
    "AMD MI300": {
        "event_text": "AMD 於 2023 年 12 月發布 Instinct MI300 系列資料中心加速器。",
        "as_of": "2023-12-15T23:59:59Z",
        "research_target": "AMD",
        "research_horizon": "2024-12-15",
        "documents": [
            archived(
                "mi300-launch", "2023-12-06",
                "https://www.amd.com/en/newsroom/press-releases/2023-12-6-amd-showcases-growing-momentum-for-amd-powered-ai-.html",
                deployments="Microsoft 正將 MI300X 用於 Azure ND MI300x v5 虛擬機。Oracle 規劃提供搭載 MI300X 的 OCI 裸機；Dell 宣布將 MI300X 整合到 PowerEdge XE9680。",
            ),
            archived(
                "amd-q3", "2023-10-31",
                "https://ir.amd.com/financial-information/sec-filings/content/0000002488-23-000192/q32023991.htm",
                earnings="AMD 2023 Q3 營收 58 億美元，GAAP 毛利率 47%。資料中心部門營收 16 億美元，年增約持平。EPYC 營收增加由自適應 SoC 資料中心產品下滑抵銷。",
                outlook="AMD 對 2023 Q4 的營收指引為 61 億美元上下 3 億美元，非 GAAP 毛利率指引約 51%。",
            ),
        ],
    },
    "Boeing 737-9 MAX": {
        "event_text": "FAA 於 2024 年 1 月暫停波音 737 MAX 擴產，並要求停飛的 737-9 通過檢查程序才能復飛。",
        "as_of": "2024-01-26T23:59:59Z",
        "research_target": "Boeing",
        "research_horizon": "2024-12-31",
        "documents": [
            archived(
                "faa-max", "2024-01-24",
                "https://www.faa.gov/newsroom/faa-halts-boeing-max-production-expansion-improve-quality-control-also-lays-out-extensive",
                inspections="FAA 暫停 737 MAX 生產擴張，並公布對停飛的 171 架 737-9 進行檢查與維護的程序。完成程序且確認適航才可復飛。",
            ),
            archived(
                "alaska-max", "2024-01-10",
                "https://news.alaskaair.com/emergency-response/as-1282/",
                cancellations="Alaska Airlines 先前預防性停飛 65 架 737-9。1 月 10 日更新表示取消至 1 月 13 日使用該機型的航班，每日約 110–150 班。",
            ),
            archived(
                "ual-max", "2024-01-22",
                "https://www.sec.gov/Archives/edgar/data/100517/000010051724000016/ual_12312023erex992.htm",
                outlook="United 的投資人更新將 737 MAX 9 停飛持續至 1 月底納入第一季指引假設，並預期 MAX 9 停飛將使第一季單位成本增幅較高。",
            ),
        ],
    },
}


HOLDOUT_CASES = {
    "UPS 客戶量縮與網路重整": {
        "event_text": "UPS 宣布計畫削減最大客戶的包裹量，並重新配置美國配送網路。",
        "as_of": "2025-01-30T23:59:59Z",
        "research_target": "UPS",
        "research_horizon": "2026-03-31",
        "documents": [
            archived(
                "ups-q4", "2025-01-30",
                "https://investors.ups.com/news-events/press-releases/detail/2135/ups-releases-4q-2024-earnings-and-provides-2025-guidance",
                volume="UPS 與最大客戶原則上達成協議，計畫至 2026 年下半年將該客戶包裹量減少逾 50%。2025 年 1 月 1 日起 UPS 將 SurePost 全數改為自行配送。",
                network="UPS 宣布重整美國網路，並計畫透過多年流程重設創造約 10 億美元節省。",
                guidance="UPS 預估 2025 全年合併營收約 890 億美元，營業利益率約 10.8%。",
            ),
        ],
    },
    "Disney 串流與分部指引": {
        "event_text": "Disney 公布 2024 財年第四季財報，並發布下一財年串流和體驗部門指引。",
        "as_of": "2024-11-14T23:59:59Z",
        "research_target": "Disney",
        "research_horizon": "2025-12-31",
        "documents": [
            archived(
                "dis-fy24", "2024-11-14",
                "https://investors.thewaltdisneycompany.com/news/news-details/2024/The-Walt-Disney-Company-Reports-Fourth-Quarter-and-Full-Year-Earnings-for-Fiscal-2024-11-14-2024/",
                streaming="Disney FY2024 Q4 Entertainment DTC 廣告收入年增 14%，營業利益 2.53 億美元。合併 DTC 串流業務營業利益 3.21 億美元，兩者口徑不同。Disney+ Core 季末付費訂戶逾 1.2 億，較上一季增加 440 萬。",
                fy25="管理層預期 FY2025 Entertainment DTC 營業利益年增約 8.75 億美元。比較基期包含印度 DTC 約 2 億美元負面影響。管理層同時預期 FY2025 Q1 Disney+ Core 訂戶季減。",
                experiences="FY2024 Q4 Experiences 營業利益 17 億美元，年減 6%。公司預計 FY2025 該部門營業利益年增 6% 至 8%，成長偏向下半財年。",
            ),
        ],
    },
    "Novo Nordisk 製造據點交易": {
        "event_text": "Novo Nordisk 宣布簽約收購三座藥品充填及成品製造廠。",
        "as_of": "2024-02-05T23:59:59Z",
        "research_target": "Novo Nordisk",
        "research_horizon": "2025-06-30",
        "documents": [
            archived(
                "novo-sites", "2024-02-05",
                "https://www.novonordisk.com/content/nncorp/global/en/news-and-media/news-and-ir-materials/news-details.html?id=167017&stream=top",
                acquisition="Novo Nordisk 同意以約 110 億美元預付款向 Novo Holdings 購買三座充填及成品製造廠。該購買與 Novo Holdings 收購 Catalent 的交易相關。",
                capacity="三座廠當時已與 Novo Nordisk 合作。管理層預期自 2026 年起逐步增加充填產能。",
            ),
            archived(
                "novo-cleared", "2024-12-14",
                "https://www.novonordisk.com/news-and-media/news-and-ir-materials/news-details.html?id=915078",
                update="Novo Nordisk 後續公告相關交易已取得完成所需批准，並把三座廠的收購價更新為 117 億美元。",
            ),
        ],
    },
    "Ford 電動車投資重整": {
        "event_text": "Ford 宣布取消原計畫的純電三排座 SUV，並重排電動車投資。",
        "as_of": "2024-08-21T23:59:59Z",
        "research_target": "Ford",
        "research_horizon": "2025-10-31",
        "documents": [
            archived(
                "ford-ev-8k", "2024-08-21",
                "https://www.sec.gov/Archives/edgar/data/37996/000003799624000150/f-20240819.htm",
                charges="Ford 估計 2024 Q3 將就原計畫純電三排座 SUV 的製造及供應商模具資產認列約 4 億美元減記。另可能產生最多約 15 億美元額外費用及現金支出。",
            ),
            archived(
                "ford-ev-strategy", "2024-08-21",
                "https://www.sec.gov/Archives/edgar/data/37996/000003799624000150/exhibit99toaugust2120248.htm",
                plans="Ford 計畫在 2026 年於俄亥俄州開始生產新款純電商用廂型車，隨後於 2027 年推出兩款電動皮卡。公司計畫把純電車相關資本支出占年度資本支出的比例從約 40% 下調至約 30%。",
            ),
        ],
    },
}


def load_cases(*, holdout=False):
    if holdout:
        return {f"V-{index:02d}": (name, Event.model_validate(profile))
                for index, (name, profile) in enumerate(HOLDOUT_CASES.items(), 1)}
    profiles = {
        name: Event.model_validate_json((EXAMPLES / f"{filename}.json").read_text(encoding="utf-8"))
        .model_copy(update={"research_horizon": horizon})
        for name, (filename, horizon) in EXAMPLE_CASES.items()
    }
    profiles.update({name: Event.model_validate(profile) for name, profile in ADDITIONAL_CASES.items()})
    return {f"H-{index:02d}": (name, event) for index, (name, event) in enumerate(profiles.items(), 1)}


def freeze(event):
    report = build_context(event)
    return {
        key: report[key] for key in ("event_text", "as_of", "target", "horizon")
    } | {
        "evidence": [
            row for row in report["evidence"] if not row["synthetic"] and row["kind"] == "disclosure"
        ],
    }


def future_disclosures(event):
    # Available to judges only. Missing a resolution record doesn't establish that a claim leaked.
    return [
        item for doc in event.documents if doc.published_at > event.as_of
        and not doc.synthetic and doc.kind == "disclosure"
        for item in document_evidence(doc)
    ]

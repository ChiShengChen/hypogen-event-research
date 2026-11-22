"""Fixed, stratified pilot selection. Reference answers stay in local grading inputs."""

import hashlib
import json

from research_app.schema import Document

FINANCEBENCH_IDS = (
    "03029", "02987", "07507", "10420", "08135", "01079",
    "00917", "01351", "05718", "02608", "03838", "00517",
)
FINSEARCH_DOMAINS = {
    "201": ("bea.gov", "stlouisfed.org", "census.gov"),
    "205": ("amd.com", "intel.com", "sec.gov"),
    "213": ("walmart.com", "sec.gov"),
    "214": ("amazon.com", "sec.gov"),
    "215": ("exxonmobil.com", "sec.gov"),
    "238": ("lseg.com", "ftserussell.com", "londonstockexchange.com"),
    "b004": ("sec.gov", "tesla.com", "nvidia.com", "wellsfargo.com", "meta.com", "apple.com"),
    "b013": ("oracle.com", "sec.gov"),
}
GYM_SELECTION = {
    0: ("Air France-KLM", ("airfranceklm.com", "flysas.com", "europa.eu", "portugal.gov.pt", "flytap.com")),
    5: ("Panasonic", ("panasonic.com", "panasonic-holdings.com", "panasonic-energy.com", "kansas.gov", "tesla.com")),
    17: ("Intel", ("intel.com", "altera.com", "silverlake.com", "sec.gov", "nvidia.com")),
    31: ("Eisai", ("eisai.com", "biogen.com", "ema.europa.eu", "europa.eu", "sec.gov")),
    52: ("Capri Holdings", ("capriholdings.com", "tapestry.com", "ftc.gov", "sec.gov", "pradagroup.com")),
}
SUPPLY = (
    {
        "id": "SC-01", "target": "NVIDIA", "cutoff": "2024-03-31",
        "question": "NVIDIA announced the Blackwell platform on March 18, 2024. Assess the event's implications over the next 12 months.",
        "domains": ("nvidia.com", "tsmc.com", "dell.com", "amazon.com", "cloud.google.com", "supermicro.com", "sec.gov"),
        "reference": [
            ["TSMC", "upstream foundry; custom 4NP process, not announced wafer volumes",
             "https://investor.nvidia.com/news/press-release-details/2024/NVIDIA-Blackwell-Platform-Arrives-to-Power-a-New-Era-of-Computing/"],
            ["Dell", "downstream systems integration; expected to deliver Blackwell servers, not recognized sales",
             "https://investor.nvidia.com/news/press-release-details/2024/NVIDIA-Blackwell-Platform-Arrives-to-Power-a-New-Era-of-Computing/"],
            ["Amazon", "downstream cloud; AWS planned Grace Blackwell instances, not proved economics",
             "https://investor.nvidia.com/news/press-release-details/2024/NVIDIA-Blackwell-Platform-Arrives-to-Power-a-New-Era-of-Computing/"],
        ],
    },
    {
        "id": "SC-02", "target": "AMD", "cutoff": "2023-12-15",
        "question": "AMD launched its Instinct MI300 series data-center accelerators on December 6, 2023. Assess the event's implications over the next 12 months.",
        "domains": ("amd.com", "microsoft.com", "oracle.com", "dell.com", "hpe.com", "supermicro.com", "sec.gov"),
        "reference": [
            ["Microsoft", "downstream cloud; Azure ND MI300X v5 deployments; scope and pricing unconfirmed",
             "https://www.amd.com/en/newsroom/press-releases/2023-12-6-amd-delivers-leadership-portfolio-of-data-center-a.html"],
            ["Oracle", "downstream cloud; planned OCI MI300X bare-metal instances, not completed rollout",
             "https://www.amd.com/en/newsroom/press-releases/2023-12-6-amd-delivers-leadership-portfolio-of-data-center-a.html"],
            ["Dell", "downstream OEM; PowerEdge XE9680 plans, not recognized sales",
             "https://www.amd.com/en/newsroom/press-releases/2023-12-6-amd-showcases-growing-momentum-for-amd-powered-ai-.html"],
        ],
    },
    {
        "id": "SC-03", "target": "Apple", "cutoff": "2023-09-22",
        "question": "Apple announced the iPhone 15 Pro and Pro Max on September 12, 2023. Assess the event's implications over the next 12 months.",
        "domains": ("apple.com", "qualcomm.com", "broadcom.com", "tsmc.com", "sec.gov"),
        "reference": [
            ["Qualcomm", "upstream modem-RF supplier; September 2023 agreement covers 2024–2026 launches, not proof of iPhone 15 Pro design win or units",
             "https://investor.qualcomm.com/news-events/press-releases/news-details/2023/Qualcomm-Announces-Agreement-with-Apple-for-Chip-Supply-09-11-2023/default.aspx"],
            ["Broadcom", "upstream RF/connectivity relationship; May 2023 multi-year agreement, not direct proof of this model's bill of materials",
             "https://www.apple.com/newsroom/2023/05/apple-announces-multibillion-dollar-deal-with-broadcom/"],
        ],
    },
    {
        "id": "SC-04", "target": "Boeing", "cutoff": "2024-02-07",
        "question": "The FAA ordered temporary grounding of certain Boeing 737-9 MAX aircraft on January 6, 2024. Assess the event's implications over the next 12 months.",
        "domains": ("faa.gov", "ntsb.gov", "boeing.com", "alaskaair.com", "united.com", "spiritaero.com", "sec.gov"),
        "reference": [
            ["Alaska Air Group", "downstream 737-9 operator; grounded 65 aircraft and interrupted service",
             "https://news.alaskaair.com/emergency-response/as-1282/"],
            ["Spirit AeroSystems", "upstream Boeing manufacturing subcontractor under FAA scrutiny; not proof of accident liability",
             "https://www.faa.gov/newsroom/updates-boeing-737-9-max-aircraft"],
            ["United Airlines", "downstream exposure to grounded MAX 9s; contemporaneous investor update projected January impact",
             "https://www.sec.gov/Archives/edgar/data/100517/000010051724000016/ual-20240122.htm"],
        ],
    },
    {
        "id": "SC-05", "target": "Intel", "cutoff": "2024-04-30",
        "question": "Intel announced completion of initial assembly for its first commercial High-NA EUV scanner on April 18, 2024. Assess the milestone's implications over the next 12 months.",
        "domains": ("intel.com", "asml.com", "zeiss.com", "sec.gov", "tsmc.com", "samsung.com"),
        "reference": [
            ["ASML", "upstream tool maker; assembly/calibration is not high-volume manufacturing or a new order",
             "https://www.intel.com/content/www/us/en/newsroom/news/intel-foundry-opens-new-frontier-chipmaking.html"],
            ["ZEISS SMT", "upstream optics via ASML; can count for relationship coverage only, not a standalone listed equity or identified Intel direct purchase",
             "https://www.intel.com/content/www/us/en/newsroom/news/intel-foundry-opens-new-frontier-chipmaking.html"],
        ],
    },
)


def read_rows(path):
    data = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.loads(data)
    return [json.loads(line) for line in data.splitlines() if line.strip()]


def load_cases(inputs):
    cases = []
    financebench = {row["financebench_id"]: row for row in read_rows(inputs / "financebench.jsonl")}
    for index, item in enumerate(FINANCEBENCH_IDS, 1):
        row = financebench[f"financebench_id_{item}"]
        grouped = {}
        for evidence in row["evidence"]:
            name = evidence["doc_name"]
            excerpts = grouped.setdefault(name, {})
            excerpts[f"p{evidence['evidence_page_num']}-{len(excerpts) + 1}"] = evidence["evidence_text"]
        docs = [
            Document(
                id=f"filing-{position}", source=f"FinanceBench PDF {name}", kind="disclosure",
                published_at="2025-12-31T23:59:59Z", obtained_at="2025-12-31T23:59:59Z",
                text_format="excerpt", availability_basis="replay_day_end", paragraphs=excerpts,
            )
            for position, (name, excerpts) in enumerate(grouped.items(), 1)
        ]
        cases.append({
            "id": f"FB-{index:02}", "suite": "FinanceBench", "source_id": row["financebench_id"],
            "target": row["company"], "question": row["question"], "cutoff": None,
            "docs": docs, "domains": (), "reference": [row["answer"], row["justification"]],
        })

    finsearch = {
        row["prompt_id"].removeprefix("(T3)Complex_Historical_Investigation_"): row
        for row in read_rows(inputs / "finsearchcomp.json")
        if row["label"] == "Complex_Historical_Investigation(Global)"
    }
    for index, (item, domains) in enumerate(FINSEARCH_DOMAINS.items(), 1):
        row = finsearch[item]
        cases.append({
            "id": f"FS-{index:02}", "suite": "FinSearchComp T3", "source_id": row["prompt_id"],
            "target": None, "question": row["prompt"], "cutoff": None,
            "docs": [], "domains": domains, "reference": row["response_reference"],
        })

    gym = read_rows(inputs / "financegym.jsonl")
    for index, (position, (target, domains)) in enumerate(GYM_SELECTION.items(), 1):
        row = gym[position]
        cases.append({
            "id": f"FG-{index:02}", "suite": "FinanceGym", "source_id": row["task_id"],
            "target": target, "question": row["question"], "cutoff": row["cutoff"],
            "docs": [], "domains": domains, "reference": None,
        })
    return cases + [
        {**row, "suite": "Supply chain", "source_id": row["id"], "docs": []} for row in SUPPLY
    ]


def input_checksums(inputs):
    filenames = ("financebench.jsonl", "finsearchcomp.json", "financegym.jsonl")
    return {name: hashlib.sha256((inputs / name).read_bytes()).hexdigest() for name in filenames}

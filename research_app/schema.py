from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Schema(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, str_strip_whitespace=True)


Nonempty = Annotated[str, Field(min_length=1)]
Lots = Annotated[int, Field(ge=0, strict=True)]
Money = Annotated[Decimal, Field(ge=0)]


class Document(Schema):
    id: Nonempty
    source: Nonempty
    kind: Literal["disclosure", "scenario", "unspecified"] = "unspecified"
    text_format: Literal["excerpt", "summary"] = "excerpt"
    availability_basis: Literal["recorded", "replay_day_end", "search_observed"] = "recorded"
    synthetic: bool = False
    published_at: AwareDatetime
    obtained_at: AwareDatetime
    paragraphs: dict[Nonempty, Nonempty] = Field(min_length=1)

    @model_validator(mode="after")
    def check_times(self):
        if self.obtained_at < self.published_at:
            raise ValueError("obtained_at must be at or after published_at")
        return self


class SupplyEdge(Schema):
    supplier: Nonempty
    customer: Nonempty
    product: Nonempty
    evidence_id: Nonempty
    valid_from: AwareDatetime | None = None
    valid_until: AwareDatetime | None = None

    @model_validator(mode="after")
    def check_interval(self):
        if self.valid_from and self.valid_until and self.valid_from >= self.valid_until:
            raise ValueError("valid_until must be later than valid_from")
        return self


class FinancialInputs(Schema):
    target: Nonempty
    quarter: Nonempty
    evidence_id: Nonempty
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
    unit: Literal["currency_per_lot"]
    lots: Lots
    price_per_lot: Money
    variable_cost_per_lot: Money
    fixed_cost: Money
    tax_rate: Annotated[Decimal, Field(ge=0, le=1)]
    diluted_shares: Annotated[int, Field(gt=0, strict=True)]
    full_tax_shield: bool


class Event(Schema):
    event_text: Nonempty
    as_of: AwareDatetime
    research_target: Nonempty | None = None
    research_horizon: Nonempty | None = None
    search_mode: Literal["off", "live", "historical_replay"] = "off"
    search_domains: list[Annotated[str, Field(pattern=r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")]] = Field(
        default_factory=list, max_length=8
    )
    documents: list[Document] = Field(default_factory=list)
    supply_edges: list[SupplyEdge] = Field(default_factory=list)
    financial_inputs: FinancialInputs | None = None

    @model_validator(mode="after")
    def check_documents(self):
        if self.search_mode != "off" and not self.search_domains:
            raise ValueError("自動搜尋須指定原始來源的 search_domains")
        ids = [d.id for d in self.documents]
        if len(ids) != len(set(ids)):
            raise ValueError("document IDs must be unique")
        if any(":" in value for value in ids):
            raise ValueError("document IDs cannot contain a colon")
        return self


class Hypothesis(Schema):
    stance: Literal["bull", "bear", "wait"]
    mechanism: Nonempty
    target: Nonempty
    horizon: Nonempty
    catalyst: Nonempty
    prediction: Nonempty
    invalidation: Nonempty
    claim_ids: list[Nonempty] = Field(min_length=1)


class EvidenceLimit(Schema):
    evidence_id: Nonempty
    limit: Nonempty


class PublicCheck(Schema):
    metric: Nonempty
    source_to_watch: Nonempty
    window: Nonempty
    impact_on_thesis: Nonempty
    evidence_ids: list[Nonempty] = Field(min_length=1)


class CompanyExposure(Schema):
    company: Nonempty
    role: Literal["upstream", "downstream", "alternative"]
    status: Literal["disclosed_relationship", "candidate", "comparable_only"]
    product_scope: Nonempty
    relationship: Nonempty
    transmission: Nonempty
    materiality: Nonempty
    public_check: Nonempty
    gap: Nonempty
    evidence_ids: list[Nonempty] = Field(min_length=1)


class TradeOpportunity(Schema):
    company: Nonempty
    direction: Literal["long_if", "short_if", "watch"]
    earnings_path: Nonempty
    catalyst: Nonempty
    trigger: Nonempty
    invalidation: Nonempty
    evidence_gap: Nonempty
    ticker: Nonempty | None
    listing_evidence_id: Nonempty | None
    evidence_ids: list[Nonempty] = Field(min_length=1)


class Assessment(Schema):
    thesis: Nonempty
    key_gap: Nonempty
    next_check: Nonempty
    evidence_limits: list[EvidenceLimit]
    public_checks: list[PublicCheck] = Field(max_length=3)
    supply_chain: list[CompanyExposure] = Field(max_length=6)
    trade_opportunities: list[TradeOpportunity] = Field(max_length=4)


class Hypotheses(Schema):
    hypotheses: list[Hypothesis]
    assessment: Assessment


class Answer(Schema):
    answer: Nonempty
    evidence_ids: list[Nonempty]
    gaps: list[Nonempty]


class Overrides(Schema):
    lots: Lots


class Question(Schema):
    parent_revision: Annotated[int, Field(ge=1, strict=True)]
    question: Nonempty
    overrides: Overrides | None = None
    evidence_search: Literal["auto", "off"] = "auto"

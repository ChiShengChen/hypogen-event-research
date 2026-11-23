from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_serializer, model_validator


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
    availability_basis: Literal["recorded", "replay_day_end", "search_observed", "vendor_point_in_time"] = "recorded"
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


class ReportedNumber(Schema):
    label: Nonempty
    value: Annotated[Decimal, Field(max_digits=24, decimal_places=8)]
    unit: Nonempty
    evidence_id: Nonempty
    approximate: bool = False


class ReportedCalculation(Schema):
    id: Nonempty
    label: Nonempty
    operation: Literal["share", "change", "difference"]
    value: ReportedNumber
    baseline: ReportedNumber


Amount = Annotated[Decimal, Field(max_digits=24, decimal_places=8)]
DecimalText = Annotated[str, Field(pattern=r"^-?[0-9]{1,24}(\.[0-9]{1,8})?$")]
Rate = Annotated[Decimal, Field(ge=0, le=1, decimal_places=8)]
Scenario = Literal["bear", "base", "bull"]
Metric = Literal["revenue", "gross_margin", "operating_income", "eps"]
Currency = Annotated[str, Field(pattern=r"^[A-Z]{3}$")]


class MetricKey(Schema):
    metric: Metric
    period_end: date
    duration: Literal["quarter", "year"]
    scope: Nonempty
    basis: Literal["US_GAAP", "IFRS", "adjusted"]
    currency: Currency


class EstimateReference(Schema):
    key: MetricKey
    kind: Literal["issuer_guidance", "issuer_outlook", "consensus", "internal", "reported_actual"]
    label: Nonempty
    available_at: AwareDatetime
    low: Amount
    high: Amount
    evidence_ids: list[Nonempty] = Field(min_length=1)
    provider: Nonempty | None = None

    @model_validator(mode="after")
    def check_range(self):
        if self.low > self.high:
            raise ValueError("基準下限不得高於上限")
        return self


class SourcedAssumption(Schema):
    value: Amount
    available_at: AwareDatetime
    evidence_ids: list[Nonempty] = Field(min_length=1)
    method: Nonempty


class OneOffAssumption(SourcedAssumption):
    label: Nonempty
    treatment: Literal["pretax_nonoperating", "income_tax_expense"]


class EPSAssumptions(Schema):
    period_end: date
    tax_rate: SourcedAssumption
    diluted_shares: SourcedAssumption
    recurring_nonoperating: SourcedAssumption
    one_offs: list[OneOffAssumption] = Field(default_factory=list, max_length=10)
    recognize_loss_tax_benefit: bool = False

    @model_validator(mode="after")
    def check_inputs(self):
        if not 0 <= self.tax_rate.value <= 1 or self.diluted_shares.value <= 0:
            raise ValueError("常態稅率須介於零與一之間，且稀釋股數須為正")
        if len({row.label for row in self.one_offs}) != len(self.one_offs):
            raise ValueError("一次性項目不可重複列入")
        return self


class RevenueObservation(SourcedAssumption):
    period_end: date
    fiscal_quarter: Annotated[int, Field(ge=1, le=4)]
    value: Annotated[Amount, Field(gt=0)]


class RevenueAdjustment(SourcedAssumption):
    id: Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]+$", max_length=64)]
    segment: Nonempty
    driver: Literal["volume", "price", "mix", "recognition", "scope"]
    public_check: Nonempty
    falsifier: Nonempty


class RevenueTurnSignal(Schema):
    driver: Literal["volume", "price", "mix", "capacity", "recognition"]
    direction: Literal["up", "down"]
    available_at: AwareDatetime
    evidence_ids: list[Nonempty] = Field(min_length=1)
    observation: Nonempty


class RevenueResidualInput(Schema):
    id: Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]+$", max_length=64)]
    segment: Nonempty
    driver: Literal["volume", "price", "mix", "capacity", "recognition", "scope"]
    period_end: date | None = None
    incremental_revenue: Amount
    incremental_gross_margin: Annotated[Amount, Field(ge=-1, le=1)] | None = None
    incremental_opex: Amount = Decimal(0)
    basis_incremental_to_incumbent: bool
    source_family: Nonempty
    mechanism: Nonempty
    available_at: AwareDatetime
    evidence_ids: list[Nonempty] = Field(min_length=1)
    rationale: Nonempty
    public_check: Nonempty
    falsifier: Nonempty

    @model_validator(mode="after")
    def check_change(self):
        if not self.incremental_revenue:
            raise ValueError("T+2 分部營收增減項須量化非零營收差額")
        return self


class RevenueBridge(Schema):
    period_end: date
    currency: Currency
    basis: Literal["US_GAAP", "IFRS", "adjusted"]
    near_fiscal_quarter: Annotated[int, Field(ge=1, le=4)]
    far_fiscal_quarter: Annotated[int, Field(ge=1, le=4)]
    method: Literal[
        "seasonal_prior", "latest_run_rate", "guided_seasonal", "guided_absolute", "year_on_year",
        "confirmed_turn", "residual_a", "residual_b",
    ]
    history: list[RevenueObservation] = Field(min_length=1, max_length=24)
    adjustments: list[RevenueAdjustment] = Field(default_factory=list, max_length=12)
    operating_signals: list[RevenueTurnSignal] = Field(default_factory=list, max_length=4)
    residual_inputs: list[RevenueResidualInput] = Field(default_factory=list, max_length=12)

    @model_serializer(mode="wrap")
    def keep_existing_snapshots(self, handler):
        value = handler(self)
        if not self.operating_signals:
            value.pop("operating_signals", None)
        if not self.residual_inputs:
            value.pop("residual_inputs", None)
        return value

    @model_validator(mode="after")
    def check_bridge(self):
        if self.far_fiscal_quarter != self.near_fiscal_quarter % 4 + 1:
            raise ValueError("營收橋接須使用連續財年季度")
        if len({row.period_end for row in self.history}) != len(self.history):
            raise ValueError("季營收歷史不得重複")
        if len({row.id for row in self.adjustments}) != len(self.adjustments):
            raise ValueError("營收調整 ID 不可重複")
        if len({row.id for row in self.residual_inputs}) != len(self.residual_inputs):
            raise ValueError("T+2 分部增減項 ID 不可重複")
        if any(row.period_end and row.period_end != self.period_end for row in self.residual_inputs):
            raise ValueError("T+2 分部增減項須落在第二預測季")
        if self.method == "residual_b" and self.adjustments:
            raise ValueError("殘差方案 B 只接受標為相對既有預測增量的分部資料")
        if self.method == "residual_a" and self.adjustments:
            raise ValueError("殘差方案 A 以已公布營收與歷史季節基準重算")
        return self


class OperatingBaseline(Schema):
    """Amounts are unscaled currency, and margins and tax rates are fractions."""

    period_end: date
    available_at: AwareDatetime
    segment_revenue: dict[Nonempty, Annotated[Amount, Field(ge=0)]] = Field(min_length=1)
    gross_margin: Annotated[Amount, Field(le=1)]
    opex: Annotated[Amount, Field(ge=0)]
    tax_rate: Rate
    other_after_tax: Amount = Decimal(0)
    diluted_shares: Annotated[Amount, Field(gt=0)]
    evidence_ids: list[Nonempty] = Field(min_length=1)
    method: Nonempty


class ShipmentChange(Schema):
    incremental_recognized_units: int
    revenue_per_unit: Annotated[Amount, Field(gt=0)]
    recognition_basis: Nonempty


class DriverBase(Schema):
    period_end: date
    scenario: Scenario
    gross_margin_delta: Annotated[Amount, Field(ge=-1, le=1)]
    opex_delta: Amount
    rationale: Nonempty
    evidence_ids: list[Nonempty] = Field(min_length=1)


class EstimateDriver(DriverBase):
    segment_revenue_delta: dict[Nonempty, Amount]
    shipment_changes: dict[Nonempty, ShipmentChange]


class DriverImpact(Schema):
    period_end: date
    metric: Literal["segment_revenue", "gross_margin", "opex"]
    segment: Nonempty | None = None
    delta: Amount

    @model_validator(mode="after")
    def check_impact(self):
        if (self.metric == "segment_revenue") != (self.segment is not None):
            raise ValueError("只有分部營收影響須指定分部")
        if not self.delta or (self.metric == "gross_margin" and abs(self.delta) > 1):
            raise ValueError("驅動差額為零或毛利率變動超出比例範圍")
        return self


class RecognitionShift(Schema):
    from_period: date
    to_period: date
    segment: Nonempty
    units: Annotated[int, Field(gt=0, strict=True)]
    revenue_per_unit: Annotated[Amount, Field(gt=0)]
    recognition_basis: Nonempty

    @model_validator(mode="after")
    def check_periods(self):
        if self.from_period == self.to_period:
            raise ValueError("遞延或提前認列須橫跨兩個季度")
        return self


class HypothesisDriverLink(Schema):
    id: Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]+$", max_length=64)]
    hypothesis_stance: Literal["bull", "bear"]
    scenario: Scenario
    hypothesis_summary: Nonempty
    evidence_ids: list[Nonempty] = Field(min_length=1)
    assumption: Nonempty
    public_check: Nonempty
    falsifier: Nonempty
    origin: Literal["analyst_input", "model_draft"] = "analyst_input"
    impacts: list[DriverImpact] = Field(default_factory=list, max_length=6)
    recognition_shift: RecognitionShift | None = None

    @model_validator(mode="after")
    def check_changes(self):
        if bool(self.impacts) == bool(self.recognition_shift):
            raise ValueError("每條連結須選跨季認列，或一組明列的財務影響")
        keys = {(row.period_end, row.metric, row.segment) for row in self.impacts}
        if len(keys) != len(self.impacts):
            raise ValueError("同一假說不可重複調整同一欄位")
        return self


class ConsensusImport(Schema):
    parent_revision: Annotated[int, Field(ge=1, strict=True)]
    target: Nonempty
    provider: Nonempty
    source_url: Nonempty
    captured_at: AwareDatetime
    purpose: Literal["live", "historical_replay"]
    csv_text: Annotated[str, Field(min_length=1, max_length=100_000)]


class DraftShipment(Schema):
    incremental_recognized_units: int
    revenue_per_unit: DecimalText
    recognition_basis: Nonempty


class DraftSegment(Schema):
    segment: Nonempty
    revenue_delta: DecimalText
    shipment: DraftShipment | None


class DraftDriver(Schema):
    period_end: date
    scenario: Scenario
    gross_margin_delta: DecimalText
    opex_delta: DecimalText
    rationale: Nonempty
    evidence_ids: list[Nonempty] = Field(min_length=1)
    segments: list[DraftSegment]

    @model_validator(mode="after")
    def check_segments(self):
        if len({entry.segment for entry in self.segments}) != len(self.segments):
            raise ValueError("模型驅動不可重複列出同一分部")
        return self

    def to_driver(self):
        return EstimateDriver(
            **self.model_dump(exclude={"segments"}),
            segment_revenue_delta={entry.segment: entry.revenue_delta for entry in self.segments},
            shipment_changes={entry.segment: entry.shipment.model_dump()
                              for entry in self.segments if entry.shipment is not None},
        )


class DriverDraft(Schema):
    drivers: list[DraftDriver]


class PEValuation(Schema):
    fiscal_year_end: date
    annual_base_eps: EstimateReference
    annual_diluted_shares: Annotated[Amount, Field(gt=0)]
    old_multiple: Annotated[Amount, Field(gt=0)]
    scenario_multiples: dict[Scenario, Annotated[Amount, Field(gt=0)]]
    multiple_basis: Nonempty
    market_price: Annotated[Amount, Field(gt=0)] | None = None
    price_at: AwareDatetime | None = None
    price_evidence_id: Nonempty | None = None

    @model_validator(mode="after")
    def check_inputs(self):
        if set(self.scenario_multiples) != {"bear", "base", "bull"}:
            raise ValueError("須提供空、基準、多三個情境的本益比")
        quoted = (self.market_price, self.price_at, self.price_evidence_id)
        if any(value is not None for value in quoted) and any(value is None for value in quoted):
            raise ValueError("現價、時間與來源須同時提供")
        return self


class EarningsPlan(Schema):
    event_at: AwareDatetime
    currency: Currency
    basis: Literal["US_GAAP", "IFRS", "adjusted"]
    references: list[EstimateReference] = Field(default_factory=list, max_length=40)
    event_values: list[EstimateReference] = Field(default_factory=list, max_length=20)
    quarters: list[OperatingBaseline] = Field(default_factory=list, max_length=2)
    drivers: list[EstimateDriver] = Field(default_factory=list, max_length=6)
    generate_drivers: bool = False
    valuation: PEValuation | None = None
    driver_links: list[HypothesisDriverLink] = Field(default_factory=list, max_length=20)
    eps_assumptions: list[EPSAssumptions] = Field(default_factory=list, max_length=2)
    calibrate_guidance: bool | None = None
    revenue_bridge: RevenueBridge | None = None

    @model_validator(mode="after")
    def check_periods(self):
        periods = {quarter.period_end for quarter in self.quarters}
        if len(periods) != len(self.quarters):
            raise ValueError("預測季度不可重複")
        keys = {(driver.period_end, driver.scenario) for driver in self.drivers}
        if len(keys) != len(self.drivers) or any(period not in periods for period, _ in keys):
            raise ValueError("情境須對應既有預測季度且不可重複")
        if self.generate_drivers and (not periods or self.drivers):
            raise ValueError("模型草擬需要季度基準，且不能同時提供手動驅動")
        if len({row.id for row in self.driver_links}) != len(self.driver_links):
            raise ValueError("假說驅動連結 ID 不可重複")
        eps_periods = {row.period_end for row in self.eps_assumptions}
        if not eps_periods <= periods or len(eps_periods) != len(self.eps_assumptions):
            raise ValueError("EPS 假設須對應既有預測季度且不可重複")
        if self.revenue_bridge and (len(periods) != 2 or self.revenue_bridge.period_end != max(periods)):
            raise ValueError("營收橋接須對應第二個預測季度")
        return self


class EarningsBranch(Schema):
    parent_revision: Annotated[int, Field(ge=1, strict=True)]
    drivers: list[EstimateDriver] = Field(default_factory=list, max_length=6)
    driver_links: list[HypothesisDriverLink] = Field(default_factory=list, max_length=20)
    eps_assumptions: list[EPSAssumptions] = Field(default_factory=list, max_length=2)
    calibrate_guidance: bool | None = None
    issuer_guidance: list[EstimateReference] = Field(default_factory=list, max_length=8)
    revenue_bridge: RevenueBridge | None = None

    @model_validator(mode="after")
    def check_changes(self):
        if not (self.drivers or self.driver_links or self.eps_assumptions or self.issuer_guidance or self.revenue_bridge
                or self.calibrate_guidance is not None):
            raise ValueError("須提供要修改的盈利模型輸入")
        if len({row.id for row in self.driver_links}) != len(self.driver_links):
            raise ValueError("假說驅動連結 ID 不可重複")
        if len({row.period_end for row in self.eps_assumptions}) != len(self.eps_assumptions):
            raise ValueError("EPS 假設季度不可重複")
        if any(row.kind != "issuer_guidance" for row in self.issuer_guidance):
            raise ValueError("校準只接受來源標記為公司指引的資料")
        return self


class ForecastRegistration(Schema):
    key: MetricKey
    low: Amount
    high: Amount
    deadline: AwareDatetime
    resolution_source: Nonempty
    probability: Rate | None = None
    evidence_ids: list[Nonempty] = Field(min_length=1)
    purpose: Literal["live", "historical_replay"] = "live"

    @model_validator(mode="after")
    def check_range(self):
        if self.low > self.high or self.deadline.date() < self.key.period_end:
            raise ValueError("預測區間或判定截止日無效")
        return self


class ForecastResolution(Schema):
    status: Literal["reported", "not_disclosed", "redefined"]
    document: Document
    paragraph_id: Nonempty
    key: MetricKey | None = None
    value: Amount | None = None
    note: Nonempty

    @model_validator(mode="after")
    def check_resolution(self):
        if self.document.kind != "disclosure" or self.document.synthetic or self.paragraph_id not in self.document.paragraphs:
            raise ValueError("核對須附可定位的真實公開披露")
        if self.status == "reported" and (self.key is None or self.value is None):
            raise ValueError("已披露的結果須提供原口徑與數值")
        if self.status != "reported" and (self.key is not None or self.value is not None):
            raise ValueError("未披露或口徑變更不可填入可比較數值")
        if self.status == "reported" and self.document.published_at.date() < self.key.period_end:
            raise ValueError("實績不能提前於觀測期末發布")
        return self


class ResearchReview(Schema):
    reviewer: Nonempty
    decision: Literal["approved", "changes_requested"]
    note: Nonempty
    duration_seconds: Annotated[Amount, Field(ge=0)] | None = None


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
    reported_calculations: list[ReportedCalculation] = Field(default_factory=list, max_length=12)
    earnings_plan: EarningsPlan | None = None

    @model_validator(mode="after")
    def check_documents(self):
        if self.search_mode != "off" and not self.search_domains:
            raise ValueError("自動搜尋須指定原始來源的 search_domains")
        ids = [d.id for d in self.documents]
        if len(ids) != len(set(ids)):
            raise ValueError("document IDs must be unique")
        if any(":" in value for value in ids):
            raise ValueError("document IDs cannot contain a colon")
        calc_ids = {item.id for item in self.reported_calculations}
        if len(calc_ids) != len(self.reported_calculations):
            raise ValueError("reported calculation IDs must be unique")
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


class AnswerPart(Schema):
    requirement: Nonempty
    status: Literal["answered", "unavailable", "missing"]


class DetailedAnswer(Answer):
    coverage: list[AnswerPart] = Field(min_length=1, max_length=12)
    calculation_ids: list[Nonempty] = Field(max_length=12)


class Overrides(Schema):
    lots: Lots


class Question(Schema):
    parent_revision: Annotated[int, Field(ge=1, strict=True)]
    question: Nonempty
    overrides: Overrides | None = None
    evidence_search: Literal["auto", "off"] = "auto"

"""Import user-supplied, licensed point-in-time consensus snapshots."""
import csv
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
from hashlib import sha256
from io import StringIO
from urllib.parse import urlsplit

from pydantic import ValidationError

from .earnings import EarningsError
from .schema import Document, EstimateReference, MetricKey

COLUMNS = ("metric", "period_end", "duration", "scope", "basis", "currency", "unit", "low", "high", "available_at")
SCALES = {
    "revenue": {"currency": 1, "currency_millions": 1_000_000},
    "operating_income": {"currency": 1, "currency_millions": 1_000_000},
    "gross_margin": {"fraction": 1, "percent": Decimal("0.01")},
    "eps": {"currency_per_share": 1},
}


def parse_consensus(request, plan, target, now):
    if request.target != target:
        raise EarningsError("共識標的和報告標的不符")
    try:
        source = urlsplit(request.source_url)
    except ValueError as exc:
        raise EarningsError("共識來源網址無效") from exc
    if source.scheme != "https" or not source.hostname or source.username or source.password:
        raise EarningsError("共識須提供無憑證的 HTTPS 來源網址")
    if request.captured_at >= plan.event_at or request.captured_at > now:
        raise EarningsError("共識快照須在事件前擷取")
    content = request.csv_text.lstrip("\ufeff")
    identity = sha256(content.encode()).hexdigest()
    metadata = "|".join((request.target, request.provider, request.source_url, request.captured_at.isoformat()))
    document_id = "consensus-" + sha256((metadata + identity).encode()).hexdigest()[:24]
    reader = csv.DictReader(StringIO(content), strict=True)
    try:
        fields = reader.fieldnames or ()
        if set(fields) != set(COLUMNS) or len(fields) != len(COLUMNS):
            raise EarningsError("共識 CSV 欄位須符合匯入契約")
        rows = list(reader)
    except csv.Error as exc:
        raise EarningsError("共識 CSV 格式無效") from exc
    references, paragraphs, observed_keys = [], {}, set()
    for number, row in enumerate(rows, 1):
        try:
            if number > 40 or None in row or any(not value or not value.strip() for value in row.values()):
                raise ValueError("欄位缺漏或超出四十列")
            key = MetricKey.model_validate({field: row[field] for field in
                                           ("metric", "period_end", "duration", "scope", "basis", "currency")})
            signature = tuple(key.model_dump().values())
            if signature in observed_keys:
                raise ValueError("快照含重複財務口徑")
            observed_keys.add(signature)
            published = datetime.fromisoformat(row["available_at"])
            if published.utcoffset() is None or published > request.captured_at:
                raise ValueError("資料可得時間須有時區且不晚於擷取時點")
            scale = SCALES[key.metric][row["unit"]]
            with localcontext() as ctx:
                ctx.prec = 60
                low, high = Decimal(row["low"]) * scale, Decimal(row["high"]) * scale
            if (not low.is_finite() or not high.is_finite()
                    or key.metric == "revenue" and low < 0 or key.metric == "gross_margin" and high > 1):
                raise ValueError("非有限數字，或營收／毛利率超出可用範圍")
            paragraph = f"row-{number}"
            # The document uses the dated captured vintage as the replay availability proxy.
            reference = EstimateReference(
                key=key, kind="consensus", label=f"{request.provider} 共識快照", provider=request.provider,
                available_at=request.captured_at, low=low, high=high, evidence_ids=[f"{document_id}:{paragraph}"],
            )
        except (ValueError, InvalidOperation, KeyError, ValidationError) as exc:
            raise EarningsError(f"共識 CSV 第 {number + 1} 列無效：{exc}") from exc
        references.append(reference)
        paragraphs[paragraph] = (
            f"{request.target}｜{key.period_end} {key.duration} {key.scope}｜{key.metric} {key.basis} "
            f"{key.currency}｜標準化區間 {low} 至 {high}。"
            f"提供者標記可得 {published.astimezone(timezone.utc).isoformat()}。"
        )
    if not references:
        raise EarningsError("共識快照沒有資料列")
    doc = Document(
        id=document_id, source=request.source_url, kind="disclosure", text_format="summary",
        availability_basis="vendor_point_in_time",
        published_at=request.captured_at, obtained_at=request.captured_at, paragraphs=paragraphs,
    )
    return doc, references, {
        "provider": request.provider, "purpose": request.purpose, "captured_at": request.captured_at.isoformat(),
        "imported_at": now.isoformat(), "document_id": document_id, "csv_sha256": identity, "rows": len(references),
    }

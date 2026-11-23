"""Arithmetic for the second forecast quarter and its research audit."""

from decimal import Decimal
from statistics import median

GUIDANCE_THRESHOLD = Decimal("0.12")
MOMENTUM_THRESHOLD = Decimal("0.08")
TURN_PASS_THROUGH = Decimal("0.5")
TURN_CAP = Decimal("0.15")
RESIDUAL_METHODS = {"residual_a", "residual_b"}
RESIDUAL_STEP_RETENTION = Decimal("0.5")
RESIDUAL_GAP_WEIGHT = Decimal("0.5")
RESIDUAL_CAP = Decimal("0.10")
RESIDUAL_MIN_CHANGE = Decimal("0.01")


def nearby(earlier, later):
    return 70 <= (later.period_end - earlier.period_end).days <= 115


def seasonal_ratio(history, start_quarter, target_quarter, before_period):
    """Use up to three reported, same-fiscal-transition pairs before the anchor."""
    prior = [(before, after) for before, after in zip(history, history[1:])
             if before.fiscal_quarter == start_quarter and after.fiscal_quarter == target_quarter
             and after.period_end < before_period and nearby(before, after)][-3:]
    if len(prior) < 2:
        return None
    ratio = median(after.value / before.value for before, after in prior)
    evidence = list(dict.fromkeys(ref for pair in prior for row in pair for ref in row.evidence_ids))
    return ratio, evidence


def seasonal_expected(history, anchor, target_quarter):
    """Project a single transition from up to three earlier instances of that fiscal sequence."""
    result = seasonal_ratio(history, anchor.fiscal_quarter, target_quarter, anchor.period_end)
    if result is None:
        return None
    ratio, evidence = result
    return anchor.value * ratio, list(dict.fromkeys([*anchor.evidence_ids, *evidence]))


def residual_persistence(bridge, guide, baseline, *, direct_guide=None):
    """Compare a decayed recent shock with what the original two-quarter estimate already reflects."""
    history = sorted(bridge.history, key=lambda row: row.period_end)
    audit = {
        "method": bridge.method, "status": "missing_history", "reason": "缺少連續季度與可比的歷史季節轉換。",
        "baseline": format(baseline, "f"), "estimate": format(baseline, "f"), "delta": "0",
        "normal_far": None, "recent_far": None, "reference_far": None, "persistence": None,
        "latest_reported": None, "normal_latest": None, "near_guidance": None, "evidence_ids": [],
        "public_check": "下一次披露時核對合併營收與事件相關分部的量、價或收入認列。",
        "falsifier": "若營收回到原季節水準，或已知分部未在目標季度認列，撤回延續假設。",
    }
    if direct_guide is not None:
        audit.update(status="issuer_guidance", reason="第二預測季已有同口徑公司營收指引。",
                     evidence_ids=direct_guide.evidence_ids)
        return Decimal(0), audit
    if baseline <= 0:
        audit.update(status="missing_baseline", reason="既有第二預測季營收欠缺正值基準。")
        return Decimal(0), audit
    if len(history) < 2:
        return Decimal(0), audit
    previous, latest = history[-2:]
    if (not nearby(previous, latest) or previous.fiscal_quarter % 4 + 1 != latest.fiscal_quarter
            or latest.fiscal_quarter % 4 + 1 != bridge.near_fiscal_quarter
            or not 140 <= (bridge.period_end - latest.period_end).days <= 230):
        return Decimal(0), audit
    expected = seasonal_expected(history, previous, latest.fiscal_quarter)
    near = seasonal_ratio(history, latest.fiscal_quarter, bridge.near_fiscal_quarter, latest.period_end)
    far = seasonal_ratio(history, bridge.near_fiscal_quarter, bridge.far_fiscal_quarter, latest.period_end)
    if expected is None or near is None or far is None:
        return Decimal(0), audit
    normal, expected_evidence = expected
    near_ratio, near_evidence = near
    far_ratio, far_evidence = far
    path_ratio = near_ratio * far_ratio
    normal_far = normal * path_ratio
    recent_far = latest.value * path_ratio
    shock = recent_far - normal_far
    retention = RESIDUAL_STEP_RETENTION ** 2
    evidence = [*latest.evidence_ids, *expected_evidence, *near_evidence, *far_evidence]
    if guide is not None:
        guide_mid = (guide.low + guide.high) / 2
        audit["near_guidance"] = format(guide_mid, "f")
        if shock:
            near_shock = (latest.value - normal) * near_ratio
            corroboration = min(Decimal(1), max(Decimal(0), (guide_mid - normal * near_ratio) / near_shock))
            retention *= Decimal("0.5") + corroboration
            evidence.extend(guide.evidence_ids)
    reference = normal_far + shock * retention
    gap = reference - baseline
    proposed = RESIDUAL_GAP_WEIGHT * gap if gap * shock > 0 else Decimal(0)
    cap = min(baseline * RESIDUAL_CAP, abs(shock * retention))
    proposal = max(-cap, min(cap, proposed))
    audit.update(normal_far=format(normal_far, "f"), recent_far=format(recent_far, "f"),
                 reference_far=format(reference, "f"), persistence=format(retention, "f"),
                 latest_reported=format(latest.value, "f"), normal_latest=format(normal, "f"),
                 evidence_ids=list(dict.fromkeys(evidence)))
    if abs(proposal) < baseline * RESIDUAL_MIN_CHANGE:
        audit.update(status="no_adjustment", reason="既有預測已涵蓋同向延續幅度，或剩餘修正低於基準營收的 1%。")
        return Decimal(0), audit
    audit.update(status="applied", reason="依近期偏離的延續幅度，修正既有預測尚未涵蓋的部分。",
                 delta=format(proposal, "f"), estimate=format(baseline + proposal, "f"))
    return proposal, audit


def turn_forecast(bridge, guide, baseline):
    """Use the scheduled guidance and two observed reporting periods without changing quiet cases."""
    history = sorted(bridge.history, key=lambda row: row.period_end)
    audit = {"status": "missing_signal", "reason": "缺少同口徑下一季營收指引或可比較歷史季度。",
             "guidance_surprise": None, "reported_surprise": None,
             "delta": "0", "evidence_ids": [],
             "public_check": "核對下一份同口徑公司指引與單季合併營收。",
             "falsifier": "更新指引回到季節基準，或新的合併營收與預估方向背離時撤回調整。"}
    if guide is None or len(history) < 2:
        return baseline, audit
    previous, latest = history[-2:]
    if (not nearby(previous, latest) or previous.fiscal_quarter % 4 + 1 != latest.fiscal_quarter
            or latest.fiscal_quarter % 4 + 1 != bridge.near_fiscal_quarter):
        return baseline, audit
    near = seasonal_expected(history, latest, bridge.near_fiscal_quarter)
    reported = seasonal_expected(history, previous, latest.fiscal_quarter)
    if near is None or reported is None:
        return baseline, audit
    midpoint = (guide.low + guide.high) / 2
    guidance_surprise = midpoint / near[0] - 1
    observed_surprise = latest.value / reported[0] - 1
    audit.update(guidance_surprise=format(guidance_surprise, "f"),
                 reported_surprise=format(observed_surprise, "f"),
                 seasonal_guidance=format(near[0], "f"), seasonal_reported=format(reported[0], "f"),
                 evidence_ids=list(dict.fromkeys([*guide.evidence_ids, *near[1], *reported[1], *latest.evidence_ids])))
    signals = [item for item in bridge.operating_signals if set(item.evidence_ids).isdisjoint(guide.evidence_ids)]
    directions = {item.direction for item in signals}
    if observed_surprise >= MOMENTUM_THRESHOLD:
        directions.add("up")
    elif observed_surprise <= -MOMENTUM_THRESHOLD:
        directions.add("down")
    audit["operating_signals"] = [item.model_dump(mode="json") for item in signals]
    audit["evidence_ids"] = list(dict.fromkeys([*audit["evidence_ids"],
                                               *(ref for item in signals for ref in item.evidence_ids)]))
    if guidance_surprise >= GUIDANCE_THRESHOLD and directions == {"up"}:
        status = "up"
    elif guidance_surprise <= -GUIDANCE_THRESHOLD and directions == {"down"}:
        status = "down"
    else:
        audit["status"] = "unconfirmed"
        if abs(guidance_surprise) < GUIDANCE_THRESHOLD:
            audit["reason"] = "公司指引偏離季節基準的幅度低於 12%。"
        elif len(directions) > 1:
            audit["reason"] = "當期營收與營運訊號方向互相衝突。"
        else:
            audit["reason"] = "沒有與指引同向且足夠強的營收或營運訊號。"
        return baseline, audit
    change = (midpoint - near[0]) * TURN_PASS_THROUGH
    limit = baseline * TURN_CAP
    delta = max(-limit, min(limit, change))
    audit.update(status=status, delta=format(delta, "f"),
                 reason="公司指引與已公布的營收或營運訊號達門檻且同向。")
    return baseline + delta, audit


def anchors(bridge, guide):
    history = sorted(bridge.history, key=lambda row: row.period_end)
    latest = history[-1]
    previous = [row for row in history if row.fiscal_quarter == bridge.far_fiscal_quarter]
    result = {"latest_run_rate": (latest.value, latest.evidence_ids)}
    if previous:
        result["seasonal_prior"] = (previous[-1].value, previous[-1].evidence_ids)
    pairs = [(near, far) for near, far in zip(history, history[1:])
             if near.fiscal_quarter == bridge.near_fiscal_quarter and far.fiscal_quarter == bridge.far_fiscal_quarter
             and nearby(near, far)]
    if guide and pairs:
        samples = pairs[-3:]
        rate = median(far.value / near.value for near, far in samples)
        midpoint = (guide.low + guide.high) / 2
        cites = [ref for pair in samples for row in pair for ref in row.evidence_ids]
        result["guided_seasonal"] = (midpoint * rate, list(dict.fromkeys([*guide.evidence_ids, *cites])))
        changes = median(far.value - near.value for near, far in samples)
        if midpoint + changes > 0:
            result["guided_absolute"] = (midpoint + changes, list(dict.fromkeys([*guide.evidence_ids, *cites])))
    if previous:
        comparable = [row for row in history[:-1] if row.fiscal_quarter == latest.fiscal_quarter]
        if comparable:
            lag = (latest.period_end - comparable[-1].period_end).days
            if 340 <= lag <= 395:
                prior = previous[-1]
                result["year_on_year"] = (prior.value * latest.value / comparable[-1].value,
                                         list(dict.fromkeys(prior.evidence_ids + latest.evidence_ids
                                                            + comparable[-1].evidence_ids)))
    return result


def chosen_anchor(options, method):
    for key in (method, "seasonal_prior", "latest_run_rate"):
        if key in options:
            return key, options[key]
    raise ValueError("缺少第二預測季營收基準")


def bridge_forecast(bridge, guide, baseline=None):
    options = anchors(bridge, guide)
    turn = None
    if bridge.method == "confirmed_turn":
        if baseline is None:
            raise ValueError("轉折調整需要既有第二預測季營收草擬值")
        anchor, turn = turn_forecast(bridge, guide, baseline)
        method, anchor_evidence = bridge.method, turn["evidence_ids"]
    else:
        method, (anchor, anchor_evidence) = chosen_anchor(options, bridge.method)
    adjustments = []
    total = Decimal(0)
    manual = bridge.adjustments if not turn or turn["status"] in {"up", "down"} else ()
    for row in manual:
        delta = row.value
        total += delta
        adjustments.append(row.model_dump(mode="json"))
    revenue = anchor + total
    if revenue <= 0:
        raise ValueError("營收橋接調整後須為正值")
    return revenue, {
        "period_end": bridge.period_end.isoformat(),
        "method": method,
        "requested_method": bridge.method,
        "anchor": format(anchor, "f"),
        "anchor_evidence_ids": anchor_evidence,
        "alternatives": {key: {"value": format(value, "f"), "evidence_ids": refs} for key, (value, refs) in options.items()},
        "adjustments": adjustments,
        "before_hypothesis_links": format(revenue, "f"),
        **({"turn": turn} if turn else {}),
    }

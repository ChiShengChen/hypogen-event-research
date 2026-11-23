import { exampleLabels, questionBank } from "./question-bank.js";
import { disposeHypothesisTree, renderHypothesisTree } from "./hypothesis-tree.js";

const $ = (selector) => document.querySelector(selector);
const all = (selector) => [...document.querySelectorAll(selector)];
const historyKey = "hypogen-workbench-v1";

function readHistory() {
  try {
    const value = JSON.parse(localStorage.getItem(historyKey) || "[]");
    return Array.isArray(value) ? value.filter((entry) => entry && entry.id && entry.revision) : [];
  } catch {
    return [];
  }
}

const state = { report: null, tab: "overview", action: "question", busy: false, history: readHistory(), config: {} };
let pendingExercise = null;
let previewSelection = null;
const modes = { fixture: "公開資料預覽", codex: "Codex CLI", live: "模型 API" };
const directions = { long_if: "條件式偏多", short_if: "條件式偏空", watch: "觀察" };
const stances = { bull: "多方", bear: "空方", wait: "觀望" };
const roles = { upstream: "上游", downstream: "下游", alternative: "替代與同業" };
const money = new Intl.NumberFormat("zh-TW", { maximumFractionDigits: 8 });

function node(tag, value, className) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (value !== undefined && value !== null) element.textContent = value;
  return element;
}

function dateText(value) {
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? (value || "—") : new Intl.DateTimeFormat("zh-TW", {
    year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", timeZoneName: "short",
  }).format(date);
}

function numberText(value, signed = false) {
  if (value === null || value === undefined) return "—";
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return String(value);
  return (signed && numeric > 0 ? "+" : "") + money.format(numeric);
}

async function request(path, body) {
  const options = body === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  };
  const response = await fetch(path, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = Array.isArray(data.detail)
      ? data.detail.map((item) => `${item.loc?.slice(1).join(".")}: ${item.msg}`).join("；")
      : data.detail;
    throw new Error(error || `伺服器回傳 HTTP ${response.status}`);
  }
  return data;
}

function status(message = "", error = false) {
  $("#status").textContent = message;
  $("#status").classList.toggle("error", error);
}

async function perform(task, loading, onError = (error) => status(error.message, true)) {
  if (state.busy) return;
  state.busy = true;
  all("button[type=submit], [data-example]").forEach((button) => { button.disabled = true; });
  status(loading);
  try {
    await task();
    status();
  } catch (error) {
    status();
    onError(error);
  } finally {
    state.busy = false;
    all("button[type=submit], [data-example]").forEach((button) => { button.disabled = false; });
  }
}

function switchPage(view) {
  $("#research").hidden = view !== "report";
  $("#empty").hidden = view !== "empty";
  $("#history").hidden = view !== "history";
  $("#example-preview").hidden = view !== "preview";
  $("#go-home").classList.toggle("selected", view !== "history");
  $("#go-history").classList.toggle("selected", view === "history");
}

function keepReport(report) {
  const entry = {
    id: report.report_id, revision: report.revision, target: report.target,
    kind: report.revision_kind, asOf: report.as_of,
  };
  state.history = [entry, ...state.history.filter((item) => item.id !== entry.id || item.revision !== entry.revision)].slice(0, 50);
  try {
    localStorage.setItem(historyKey, JSON.stringify(state.history));
  } catch {
    // The current page still retains history when browser storage is unavailable.
  }
}

function versionName(entry) {
  if (entry.revision === 1) return "原稿";
  return { earnings_scenario: "盈利重算", earnings_consensus: "共識快照", scenario: "情境重算",
    evidence_follow_up: "補搜證據", linkage_follow_up: "業務連動追問" }[entry.kind] || "研究版本";
}

function versionButton(entry, includeTarget) {
  const button = node("button", null, "version-row");
  button.type = "button";
  button.append(node("span", (includeTarget ? `${entry.target} · ` : "") + versionName(entry)),
    node("span", `v${entry.revision}`, "badge"));
  if (state.report?.report_id === entry.id && state.report?.revision === entry.revision) button.setAttribute("aria-current", "page");
  button.addEventListener("click", () => perform(() => loadReport(entry.id, entry.revision), "正在開啟版本…"));
  return button;
}

function renderHistory() {
  const entries = state.history;
  $("#history-list").replaceChildren(...(entries.length
    ? entries.map((entry) => versionButton(entry, true))
    : [node("p", "尚未開啟任何報告。", "notice")]));
  const matching = entries.filter((entry) => entry.id === state.report?.report_id).sort((a, b) => a.revision - b.revision);
  if (state.report && !matching.some((entry) => entry.revision === 1)) {
    matching.unshift({ id: state.report.report_id, target: state.report.target, revision: 1 });
  }
  $("#versions").replaceChildren(...matching.map((entry) => versionButton(entry, false)));
}

function metric(label, value, unit) {
  const box = node("article", null, "metric");
  box.append(node("div", label, "metric-label"),
    node("div", value, "metric-value" + (String(value).startsWith("-") ? " negative" : "")),
    node("div", unit, "metric-unit"));
  return box;
}

function heading(title, hint) {
  const element = node("div", null, "section-title");
  element.append(node("h2", title));
  if (hint) element.append(node("span", hint));
  return element;
}

function fields(rows) {
  const result = node("dl", null, "details");
  for (const [label, value] of rows) {
    if (!value) continue;
    const group = node("div");
    group.append(node("dt", label), node("dd", value));
    result.append(group);
  }
  return result;
}

function evidenceLinks(refs = []) {
  const links = node("p", null, "small");
  for (const ref of refs) {
    const link = node("a", ref);
    link.href = `#evidence-${encodeURIComponent(ref)}`;
    link.addEventListener("click", (event) => {
      event.preventDefault();
      selectTab("evidence");
      const evidence = document.getElementById(`evidence-${ref}`);
      if (evidence) {
        evidence.open = true;
        evidence.scrollIntoView({ block: "center" });
        evidence.querySelector("summary").focus({ preventScroll: true });
      }
    });
    if (links.childNodes.length) links.append(" · ");
    links.append(link);
  }
  return links;
}

function opportunityBlock(report) {
  const { trade_opportunities: ideas = [], trade_opportunities_gap: gap } = report.assessment || {};
  const fragment = document.createDocumentFragment();
  fragment.append(heading("延伸交易機會", `${ideas.length} 項`));
  if (!ideas.length) {
    fragment.append(node("p", gap || "本版本沒有可列名的延伸標的。", "notice"));
    return fragment;
  }
  const items = node("div", null, "cards");
  for (const idea of ideas) {
    const item = node("article", null, "item");
    const head = node("div", null, "item-header");
    head.append(node("h3", idea.company), node("span", directions[idea.direction] || "觀察", "badge"));
    item.append(head, fields([
      ["交易標的", idea.ticker || "待確認"], ["財務傳導", idea.earnings_path], ["催化劑", idea.catalyst],
      ["觸發條件", idea.trigger], ["失效條件", idea.invalidation], ["交易前待查", idea.evidence_gap],
    ]), evidenceLinks(idea.evidence_ids));
    items.append(item);
  }
  fragment.append(items);
  return fragment;
}

function businessLinkageBlock(report, scope = null) {
  const fragment = document.createDocumentFragment();
  if (!report.business_linkages) return fragment;
  const paths = scope ? report.business_linkages.filter(path => path.scope === scope) : report.business_linkages;
  if (scope && !paths.length) return fragment;
  fragment.append(heading("連動業務假說"));
  const items = node("div", null, "cards");
  for (const path of paths) {
    const item = node("article", null, "item");
    const head = node("div", null, "item-header");
    const scopeLabel = path.scope === "internal" ? "公司內部" : "其他公司";
    head.append(node("h3", `${path.origin_business} → ${path.affected_company} · ${path.affected_business}`),
      node("span", `${scopeLabel} · ${stances[path.linked_stance]}`, "badge"));
    item.append(head, fields([
      ["排序理由", path.ranking_reason],
      ["傳導機制", path.mechanism], ["必要條件", path.condition], ["比較基準", path.baseline],
      ["財務影響", path.financial_effect], ["其他解釋", path.alternative_explanation],
      ["公開查核", `${path.public_source} · ${path.observation_period} · ${path.metric}`],
      ["可驗證預測", path.prediction], ["推翻條件", path.invalidation], ["覆核期限", path.deadline],
    ]), node("p", "起點證據", "small"), evidenceLinks(path.origin_evidence_ids),
    node("p", "受影響業務證據", "small"), evidenceLinks(path.affected_evidence_ids));
    items.append(item);
  }
  if (items.childNodes.length) fragment.append(items);
  if (report.business_linkage_gap) fragment.append(node("p", report.business_linkage_gap, "notice"));
  return fragment;
}

function scenarioBlock(report) {
  const fragment = document.createDocumentFragment();
  if (!report.stance_cases) return fragment;
  const labels = { bull: "多方", base: "基準", bear: "空方", wait: "觀望" };
  const directions = { up: "增加", down: "減少", flat: "持平", unknown: "待查" };
  fragment.append(heading("多立場情境與劇本"));
  for (const group of report.stance_cases) {
    fragment.append(node("h3", labels[group.stance]));
    for (const scenario of group.cases) {
      const item = node("details", null, "item");
      item.append(node("summary", scenario.title), fields([
        ["驅動因素", scenario.driver], ["成立條件", scenario.conditions.join("、")],
        ["傳導機制", scenario.mechanism], ["比較基準", scenario.baseline],
        ["財務影響", `${scenario.financial_metric}${directions[scenario.direction]}。${scenario.scale_basis_or_gap}`],
        ["公開查核", `${scenario.public_source} · ${scenario.observation_period} · ${scenario.public_metric}`],
        ["覆核日", scenario.review_by], ["可驗證預測", scenario.prediction], ["推翻條件", scenario.falsifier],
      ]), evidenceLinks(scenario.evidence_ids));
      fragment.append(item);
    }
    if (group.evidence_gap) fragment.append(node("p", group.evidence_gap, "notice"));
  }
  return fragment;
}

function renderOverview(body, report) {
  const assessment = report.assessment || {};
  const intro = node("div", null, "thesis");
  intro.append(node("h2", "核心判斷"), node("p", assessment.thesis || "查閱報告全文以取得原始研究結論。"));
  body.append(intro, fields([["首要待查", assessment.key_gap], ["下一步", assessment.next_check]]));
  if (report.hypotheses?.length) {
    body.append(heading("多空假說"));
    const items = node("div", null, "cards");
    for (const hypothesis of report.hypotheses) {
      const item = node("details", null, "item");
      item.append(node("summary", stances[hypothesis.stance] || hypothesis.stance),
        fields([["傳導機制", hypothesis.mechanism], ["催化劑", hypothesis.catalyst],
          ["可驗證預測", hypothesis.prediction], ["失效條件", hypothesis.invalidation]]));
      items.append(item);
    }
    body.append(items);
  }
  body.append(businessLinkageBlock(report), scenarioBlock(report), opportunityBlock(report));
}

function renderSupply(body, report) {
  body.append(opportunityBlock(report));
  body.append(businessLinkageBlock(report, "counterparty"));
  const companies = report.assessment?.supply_chain || [];
  body.append(heading("供應鏈公司", `${companies.length} 家`));
  if (!companies.length) body.append(node("p", "本版本沒有可列名的公司關係。", "notice"));
  const items = node("div", null, "cards");
  for (const company of companies) {
    const item = node("article", null, "item");
    const head = node("div", null, "item-header");
    head.append(node("h3", company.company), node("span", roles[company.role] || company.role, "badge"));
    item.append(head, fields([
      ["覆蓋產品", company.product_scope], ["關係", company.relationship], ["事件傳導", company.transmission],
      ["重要性", company.materiality], ["公開查核", company.public_check], ["缺口", company.gap],
    ]), evidenceLinks(company.evidence_ids));
    items.append(item);
  }
  body.append(items);
}

function renderEvidence(body, report) {
  const records = report.evidence || [];
  body.append(heading("時點可見的證據", `${records.length} 筆`));
  if (!records.length) body.append(node("p", "本版本沒有可見文件。", "notice"));
  const items = node("div", null, "cards");
  for (const evidence of records) {
    const item = node("details", null, "item");
    item.id = `evidence-${evidence.id}`;
    let link;
    try {
      const source = new URL(evidence.source);
      if (source.protocol === "https:" || source.protocol === "http:") {
        link = node("a", "開啟來源");
        link.href = source.href;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
      }
    } catch {
      // Some fixture sources are titles rather than URLs.
    }
    item.append(node("summary", evidence.id), fields([
      ["來源", evidence.source], ["公開時點", dateText(evidence.published_at)],
      [evidence.availability_basis === "replay_day_end" ? "回放時點" : "取得時點", dateText(evidence.obtained_at)],
      [evidence.text_format === "summary" ? "來源摘要" : "原文", evidence.quote],
    ]));
    if (link) item.append(link);
    items.append(item);
  }
  body.append(items);
}

const financialMetric = { revenue: "營收", gross_margin: "毛利率", operating_income: "營業利益", eps: "稀釋 EPS" };

function jsonAction(title, value, handler) {
  const details = node("details", null, "item");
  const form = node("form");
  const label = node("label", "JSON");
  const input = node("textarea");
  input.rows = 8;
  input.spellcheck = false;
  input.required = true;
  input.value = JSON.stringify(value, null, 2);
  label.append(input);
  const button = node("button", title, "button primary");
  button.type = "submit";
  form.append(label, button);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    perform(() => handler(JSON.parse(input.value)), "正在更新盈利研究…");
  });
  details.append(node("summary", title), form);
  return details;
}

function fullFilingAction(path, quarter, report) {
  const details = node("details", null, "item");
  const title = `從完整公告覆核 ${quarter.period_end}`;
  const form = node("form");
  const fieldsForUpload = [
    ["html", "公司公告 HTML", "file", ""],
    ["source_url", "公告來源網址", "url", ""],
    ["published_at", "公開時間（ISO 8601）", "text", ""],
    ["obtained_at", "當時取得時間（ISO 8601）", "text", ""],
    ["event_at", "事件時間（ISO 8601）", "text", report.earnings.inputs.event_at],
    ["fiscal_label", "公告內的財季名稱（選填）", "text", ""],
  ];
  const controls = {};
  for (const [key, labelText, type, value] of fieldsForUpload) {
    const label = node("label", labelText);
    const input = node("input");
    input.type = type;
    input.required = key !== "fiscal_label";
    input.value = value;
    if (type === "file") input.accept = ".html,.htm,text/html";
    controls[key] = input;
    label.append(input);
    form.append(label);
  }
  const button = node("button", "覆核公告", "button primary");
  button.type = "submit";
  form.append(button);
  const result = node("div");
  result.setAttribute("aria-live", "polite");
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    perform(async () => {
      const file = controls.html.files[0];
      if (file.size > 2000000) throw new Error("請選擇 2 MB 以內的 HTML 公告。");
      const payload = Object.fromEntries(Object.entries(controls).map(([key, input]) => [key, input.value || null]));
      payload.period_end = quarter.period_end;
      payload.html = await file.text();
      result.replaceChildren();
      const { audit, incumbent } = await request(`${path}/earnings/full-revision-check`, payload);
      const fmt = (value) => value === null ? "—" : numberText(Number(value) / 1e6);
      const statuses = { eligible: "可試算剩餘差額", noop: "維持現估", blocked: "暫緩調整" };
      const { column } = audit.location || {};
      result.append(fields([
        ["核對結果", statuses[audit.status]], ["說明", audit.reason], ["封存現估（百萬美元）", fmt(incumbent)],
        ["新指引區間（百萬美元）", audit.new_low === null ? "—" : `${fmt(audit.new_low)}–${fmt(audit.new_high)}`],
        ["剩餘差額（百萬美元）", fmt(audit.remaining_delta)],
        ["表格數值欄", Number.isInteger(column) ? `第 ${column + 1} 欄` : null],
      ]));
      const proof = audit.unit_proof;
      if (proof) {
        const multipliers = [...new Set(proof.multipliers)].map((value) => `×${numberText(value)}`);
        result.append(fields([
          ["金額原文", proof.raw_text], ["核對幣別", proof.currency], ["金額倍率", multipliers.join("、")],
          ["換算後區間（美元）", proof.normalized_low !== null
            ? `${numberText(proof.normalized_low)}–${numberText(proof.normalized_high)}` : null],
        ]));
        const labels = { inline: "金額原文", shared_left_label: "共用列標籤", column_header: "欄位表頭",
          table_title: "表格標題", row_label: "營收列標籤" };
        for (const source of proof.sources) {
          const link = node("a", `${labels[source.scope]} · ${source.quote}`);
          link.href = source.link;
          link.target = "_blank";
          link.rel = "noopener noreferrer";
          const row = node("p");
          row.append(link);
          result.append(row);
        }
      }
      for (const citation of audit.citations) {
        const evidence = node("details", null, "item");
        const link = node("a", "開啟公告中的原文");
        link.href = citation.link;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        evidence.append(node("summary", citation.id), node("blockquote", citation.quote), link);
        result.append(evidence);
      }
    }, "正在定位公告和試算營收…");
  });
  details.append(node("summary", title), node("p", "試驗版。覆核時請比對原文的財季、表頭及金額單位。"), form, result);
  return details;
}

function renderEarnings(body, report) {
  const { earnings } = report;
  const currency = earnings.inputs.currency;
  const path = `/reports/${encodeURIComponent(report.report_id)}/revisions/${report.revision}`;
  const earningsBranch = async (payload) => {
    const child = await request(`/reports/${encodeURIComponent(report.report_id)}/earnings/branches`,
      { ...payload, parent_revision: report.revision });
    renderReport(child);
  };
  body.append(heading("盈利預估", `${currency} 百萬／EPS 為每股`));
  body.append(businessLinkageBlock(report), scenarioBlock(report));
  for (const quarter of earnings.quarters) {
    body.append(node("h3", quarter.period_end));
    const table = node("table", null, "compare");
    const head = node("thead");
    const header = node("tr");
    for (const title of ["指標", "舊預估", "空方", "基準", "多方"]) header.append(node("th", title));
    head.append(header);
    const rows = node("tbody");
    const format = (value, key) => value === undefined ? "—" : key === "gross_margin"
      ? `${(Number(value) * 100).toFixed(2)}%` : numberText(key === "eps" ? Number(value).toFixed(2) : Number(value) / 1e6);
    for (const [key, label] of Object.entries(financialMetric)) {
      const row = node("tr");
      row.append(node("th", label), node("td", format(quarter.baseline[key], key)));
      for (const name of ["bear", "base", "bull"]) row.append(node("td", format(quarter.scenarios[name]?.revised[key], key)));
      rows.append(row);
    }
    table.append(head, rows);
    const wrapper = node("div", null, "scroll-table");
    wrapper.append(table);
    body.append(wrapper);
    const expectation = quarter.revenue_expectations;
    if (expectation?.before !== undefined) {
      const view = node("div", null, "item");
      view.append(fields([
        [expectation.before_label, format(expectation.before, "revenue")],
        ["事件後營收基準", format(expectation.after, "revenue")],
      ]), evidenceLinks(expectation.before_evidence_ids));
      for (const item of expectation.consensus) {
        const ref = item.reference;
        view.append(fields([[ref.label, `${format(ref.low, "revenue")}–${format(ref.high, "revenue")}｜與中點差 ${format(item.delta, "revenue")}`]]),
          evidenceLinks(ref.evidence_ids));
      }
      if (!expectation.consensus.length) view.append(node("p", "這一季未取得同口徑點時市場共識。"));
      body.append(view);
    }
    const bridge = earnings.revenue_bridge;
    if (bridge?.period_end === quarter.period_end) {
      const item = node("details", null, "item");
      const labels = {
        latest_run_rate: "最近單季營收", seasonal_prior: "去年同季營收", guided_seasonal: "指引中點乘歷史季節比率",
        guided_absolute: "指引中點加歷史季節差額", year_on_year: "以最新年增率調整去年同季",
        confirmed_turn: "雙訊號轉折調整", residual_a: "A · 近期衝擊延續", residual_b: "B · 衝擊延續與分部調整",
      };
      item.append(node("summary", "第二預測季營收橋接"), fields([
        ["模型草擬", format(bridge.original_draft, "revenue")],
        [labels[bridge.method], format(bridge.anchor, "revenue")],
        ["最後營收", format(bridge.after_hypothesis_links, "revenue")],
      ]), evidenceLinks(bridge.anchor_evidence_ids));
      if (bridge.turn) {
        const turn = bridge.turn;
        const states = { up: "上行", down: "下行", unconfirmed: "訊號未達門檻", missing_signal: "缺少可比訊號" };
        item.append(fields([
          ["轉折判定", states[turn.status]],
          ["指引偏離", format(turn.guidance_surprise ?? undefined, "gross_margin")],
          ["已公布營收偏離", format(turn.reported_surprise ?? undefined, "gross_margin")],
          ["自動調整", format(turn.delta, "revenue")],
          ["公開查核", turn.public_check], ["撤回條件", turn.falsifier],
        ]));
        if (turn.reason) item.append(node("p", turn.reason));
        for (const signal of turn.operating_signals || []) {
          item.append(node("p", signal.observation), evidenceLinks(signal.evidence_ids));
        }
      }
      if (bridge.residual) {
        const trial = bridge.residual;
        const statuses = {
          applied: "採用", no_adjustment: "沿用基準", missing_history: "缺少可比歷史",
          issuer_guidance: "已有當季公司指引", missing_baseline: "缺少基準", infeasible: "財務假設無法對帳",
        };
        item.append(fields([
          ["修正狀態", statuses[trial.status]],
          ["現版基準", format(trial.baseline ?? undefined, "revenue")],
          ["營收修正", format(trial.delta ?? undefined, "revenue")],
          ["修正後營收", format(trial.estimate ?? undefined, "revenue")],
        ]), evidenceLinks(trial.evidence_ids || []));
        if (trial.reason) item.append(node("p", trial.reason));
        if (trial.public_check && trial.falsifier) {
          item.append(fields([["下一個公開查核", trial.public_check], ["撤回條件", trial.falsifier]]));
        }
        for (const part of trial.components || []) {
          const name = part.segment || "近期衝擊";
          const details = [[name, format(part.delta ?? undefined, "revenue")]];
          if (part.reason || part.rationale) details.push(["依據", part.reason || part.rationale]);
          if (part.public_check && part.falsifier) details.push(["公開查核", part.public_check], ["撤回條件", part.falsifier]);
          item.append(fields(details), evidenceLinks(part.evidence_ids || []));
        }
        if (trial.method === "residual_b" && !(trial.components || []).some((part) =>
          part.kind === "segment" && part.status === "applied")) {
          item.append(node("p", "尚無確認為現版未納入的分部調整。"));
        }
        for (const part of trial.ablation || []) {
          if (part.without) {
            item.append(fields([[
              `移除 ${part.id}`,
              `營收 ${format(part.without.revenue, "revenue")} 百萬，EPS ${format(part.without.eps, "eps")}`,
            ]]));
          }
        }
      }
      for (const adjustment of bridge.residual ? [] : bridge.adjustments) {
        item.append(fields([
          [adjustment.segment, format(adjustment.value, "revenue")],
          ["依據", adjustment.method], ["公開查核", adjustment.public_check], ["反證", adjustment.falsifier],
        ]), evidenceLinks(adjustment.evidence_ids));
      }
      if (!bridge.adjustments.length && !bridge.residual) item.append(node("p", "本季沒有可單列且可量化的分部增減項。"));
      body.append(item);
    }
    for (const entry of (earnings.guidance_calibration || []).filter((row) => row.period_end === quarter.period_end)) {
      const record = node("div", null, "item");
      record.append(fields([[
        `公司指引校準 · ${financialMetric[entry.metric]}`,
        `${format(entry.draft_base, entry.metric)} → ${format(entry.calibrated_base, entry.metric)}`,
      ]]), evidenceLinks(entry.reference.evidence_ids));
      body.append(record);
    }
    if (quarter.scenarios.base) {
      const key = { metric: "revenue", period_end: quarter.period_end, duration: "quarter", scope: "consolidated",
        basis: earnings.inputs.basis, currency };
      const guidance = (entries) => {
        const ref = entries.find(({ kind, key: scope }) => kind === "issuer_guidance" &&
          Object.keys(key).every((field) => key[field] === scope[field]));
        return ref ? { key, available_at: ref.available_at, low: ref.low, high: ref.high, evidence_ids: ref.evidence_ids } : null;
      };
      const result = node("div");
      result.setAttribute("aria-live", "polite");
      const check = jsonAction(`核對 ${quarter.period_end} 新披露`, {
        period_end: quarter.period_end, event_at: earnings.inputs.event_at, fiscal_label: null,
        original: guidance(earnings.inputs.references || []),
        disclosure: guidance(earnings.inputs.event_values || []),
      }, async (payload) => {
        result.replaceChildren();
        const { audit, financial_impact } = await request(`${path}/earnings/revision-check`, payload);
        const status = { eligible: "可試算剩餘差額", noop: "維持現估", blocked: "暫緩調整" };
        const range = (quote) => quote ? `${format(quote.low, "revenue")}–${format(quote.high, "revenue")}` : "—";
        result.append(fields([
          ["核對結果", status[audit.status]],
          ["說明", audit.reason],
          ["公告使用的財季名稱", audit.fiscal_label],
          ["事件前指引區間", range(audit.original)],
          ["公告指引中點變動", format(audit.event_change?.midpoint_delta ?? undefined, "revenue")],
          ["現版營收", format(audit.incumbent.low, "revenue")],
          ["新指引區間", range(audit.disclosure)],
          ["剩餘差額", format(audit.remaining_delta ?? undefined, "revenue")],
        ]), evidenceLinks(audit.evidence_ids));
        if (financial_impact) {
          result.append(fields(Object.entries(financial_impact).map(([metric, values]) =>
            [financialMetric[metric], `${format(values.before, metric)} → ${format(values.after, metric)}`])));
        }
      });
      check.querySelector("summary").after(node("p", "使用此版已封存的證據。引文跨段時，填入公告的財季名稱和原文定位；表格依原欄順序填欄位。"));
      check.append(result);
      body.append(check);
      if (key.currency === "USD" && key.basis === "US_GAAP") body.append(fullFilingAction(path, quarter, report));
    }
    const profile = (earnings.inputs.eps_assumptions || []).find((row) => row.period_end === quarter.period_end);
    if (profile) {
      const item = node("details", null, "item");
      item.append(node("summary", "EPS 假設與來源"));
      const inputs = [
        ["常態有效稅率", profile.tax_rate, "gross_margin"],
        ["稀釋股數（百萬股）", profile.diluted_shares, "revenue"],
        ["經常性營業外損益", profile.recurring_nonoperating, "revenue"],
        ...profile.one_offs.map((entry) => [entry.label, entry, "revenue"]),
      ];
      for (const [label, entry, kind] of inputs) {
        item.append(fields([[label, `${format(entry.value, kind)}。${entry.method}`]]), evidenceLinks(entry.evidence_ids));
      }
      if (!profile.one_offs.length) item.append(node("p", "預估未單列一次性項目。"));
      if (!profile.recognize_loss_tax_benefit) item.append(node("p", "稅前虧損情境未假設可認列稅務利益。"));
      body.append(item);
    }
  }
  if (earnings.valuation) {
    body.append(heading("每股情境價值", currency));
    body.append(fields(Object.entries(earnings.valuation.scenarios).map(([scenario, value]) =>
      [({ bear: "空方", base: "基準", bull: "多方" })[scenario], value.value ? Number(value.value).toFixed(2) : "年度 EPS 非正"])));
  }
  if (earnings.driver_audit?.length || earnings.unlinked_driver_inputs?.length) {
    body.append(heading("假說與驅動追溯"));
    for (const link of earnings.driver_audit || []) {
      const item = node("details", null, "item");
      const impacts = link.effects.map((row) => [
        row.period_end, `營收 ${numberText(Number(row.revenue) / 1e6, true)} 百萬，EPS ${Number(row.eps).toFixed(2)}`,
      ]);
      item.append(node("summary", link.hypothesis_summary), fields([
        ["模型條件", link.assumption], ["公開查核", link.public_check], ["反證", link.falsifier], ...impacts,
      ]), evidenceLinks(link.evidence_ids));
      if (!link.source_overlap.length) item.append(node("p", "與原假說引文無交集，待覆核。", "notice"));
      for (const path of link.related_business_linkages || []) {
        item.append(node("p", `共用連動證據 · ${path.affected_company} · ${path.affected_business}`, "small"),
          evidenceLinks(path.evidence_ids));
      }
      body.append(item);
    }
    if (earnings.unlinked_driver_inputs?.length) {
      body.append(node("p", `另有 ${earnings.unlinked_driver_inputs.length} 個季度情境含未連結調整。`, "notice"));
    }
  }
  const driver = earnings.inputs.drivers[0];
  if (driver) {
    body.append(jsonAction("建立盈利重算子版", { drivers: [driver] }, earningsBranch));
  }
  if (earnings.quarters.length === 2 && earnings.inputs.quarters[0].segment_revenue) {
    const [firstQuarter, secondQuarter] = earnings.quarters;
    const segment = Object.keys(firstQuarter.baseline.segment_revenue)[0];
    body.append(jsonAction("新增跨季認列假說", { driver_links: [{
      id: "recognition-shift", hypothesis_stance: "bear", scenario: "bear", hypothesis_summary: "",
      evidence_ids: [], assumption: "", public_check: "", falsifier: "", impacts: [],
      recognition_shift: { from_period: firstQuarter.period_end, to_period: secondQuarter.period_end,
        segment, units: 1, revenue_per_unit: "", recognition_basis: "" },
    }] }, earningsBranch));
  }
  if (earnings.inputs.quarters.length && driver) {
    const [first] = earnings.inputs.quarters;
    const sourced = (value) => ({ value, available_at: first.available_at, evidence_ids: first.evidence_ids, method: "" });
    const profiles = (earnings.inputs.eps_assumptions || []).length ? earnings.inputs.eps_assumptions : [{
      period_end: first.period_end, tax_rate: sourced(first.tax_rate), diluted_shares: sourced(first.diluted_shares),
      recurring_nonoperating: sourced("0"), one_offs: [], recognize_loss_tax_benefit: false,
    }];
    body.append(jsonAction("修改 EPS 假設與一次性項目", { eps_assumptions: profiles }, earningsBranch));
    body.append(jsonAction("用公司指引校準", { calibrate_guidance: true, issuer_guidance: [{
      key: { metric: "revenue", period_end: first.period_end, duration: "quarter", scope: "consolidated",
        basis: earnings.inputs.basis, currency },
      kind: "issuer_guidance", label: "", available_at: report.as_of, low: "", high: "", evidence_ids: [],
    }] }, earningsBranch));
    if (earnings.inputs.quarters.length === 2) {
      const [, far] = earnings.quarters;
      const bridge = earnings.inputs.revenue_bridge || {
        period_end: far.period_end, currency, basis: earnings.inputs.basis,
        near_fiscal_quarter: null, far_fiscal_quarter: null, method: "guided_absolute", history: [{
          period_end: "", fiscal_quarter: null, value: "", available_at: first.available_at, evidence_ids: [], method: "",
        }], adjustments: [],
      };
      body.append(jsonAction("編輯第二預測季營收橋接", { revenue_bridge: bridge }, earningsBranch));
      if (earnings.inputs.revenue_bridge && bridge.method !== "confirmed_turn") {
        body.append(jsonAction("套用 T+2 轉折偵測", { revenue_bridge: { ...bridge, method: "confirmed_turn" } }, earningsBranch));
      }
      if (earnings.inputs.revenue_bridge && !bridge.adjustments.length) {
        if (bridge.method !== "residual_a") {
          body.append(jsonAction("試算 T+2 修正 A", { revenue_bridge: { ...bridge, method: "residual_a", residual_inputs: [] } },
            earningsBranch));
        }
        if (bridge.method !== "residual_b") {
          body.append(jsonAction("試算 T+2 修正 B", { revenue_bridge: { ...bridge, method: "residual_b" } }, earningsBranch));
        }
      }
    }
  }
  body.append(jsonAction("匯入點時共識 CSV", {
    target: report.target, provider: "", source_url: "", captured_at: "",
    purpose: "historical_replay", csv_text: "metric,period_end,duration,scope,basis,currency,unit,low,high,available_at\n",
  }, async (payload) => {
    const child = await request(`/reports/${encodeURIComponent(report.report_id)}/earnings/consensus`,
      { ...payload, parent_revision: report.revision });
    renderReport(child);
  }));
  const first = earnings.quarters[0];
  const refresh = async (action, value) => {
    await request(`${path}/${action}`, value);
    selectTab("earnings");
  };
  if (first) {
    const deadline = new Date(`${first.period_end}T23:59:59Z`);
    deadline.setUTCDate(deadline.getUTCDate() + 60);
    const point = first.scenarios.base?.revised.revenue ?? first.baseline.revenue;
    const evidence = earnings.inputs.quarters.find((entry) => entry.period_end === first.period_end);
    body.append(jsonAction("登記預測", {
      key: { metric: "revenue", period_end: first.period_end, duration: "quarter",
        scope: "consolidated", basis: earnings.inputs.basis, currency },
      low: point, high: point, deadline: deadline.toISOString(), resolution_source: "公司同期間財報",
      probability: null, evidence_ids: evidence.evidence_ids,
      purpose: deadline < new Date() ? "historical_replay" : "live",
    }, (value) => refresh("forecasts", value)));
  }
  body.append(jsonAction("記錄研究員覆核", { reviewer: "", decision: "changes_requested", note: "" },
    (value) => refresh("reviews", value)));
  const records = node("div", null, "cards");
  body.append(heading("預測核對與覆核紀錄"), records);
  request(`${path}/earnings`).then((data) => {
    for (const forecast of data.forecasts) {
      const label = { pending: "待核對", overdue: "已到期", hit: "命中", miss: "落空",
        late: "逾期披露", not_disclosed: "未披露", redefined: "口徑變更" }[forecast.status];
      records.append(node("p", `${forecast.key.period_end} ${financialMetric[forecast.key.metric]} · ${label} · ${forecast.purpose}`, "notice"));
      if (!forecast.resolution) {
        records.append(jsonAction("核對實績", {
          status: "reported", key: forecast.key, value: "", paragraph_id: "actual", note: "",
          document: { id: "actual", source: "", kind: "disclosure", published_at: "", obtained_at: "",
            paragraphs: { actual: "" } },
        }, (value) => refresh(`forecasts/${encodeURIComponent(forecast.id)}/resolve`, value)));
      }
    }
    for (const review of data.reviews) {
      records.append(node("p", `${review.reviewer} · ${review.decision === "approved" ? "通過" : "需修改"} · ${review.note}`, "notice"));
    }
    if (!data.forecasts.length && !data.reviews.length) records.append(node("p", "本版尚無登記或覆核。", "notice"));
  }).catch((error) => records.append(node("p", error.message, "error-text")));
}

function selectTab(name) {
  if (name === "earnings" && !state.report?.earnings) name = "overview";
  state.tab = name;
  all("[data-tab]").forEach((button) => {
    if (button.dataset.tab === name) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  const body = $("#tab-body");
  disposeHypothesisTree(body);
  body.replaceChildren();
  body.closest(".content-grid").dataset.view = name;
  $("#research").dataset.view = name;
  const report = state.report;
  if (!report) return;
  if (name === "overview") renderOverview(body, report);
  if (name === "tree") renderHypothesisTree(body, {
    report, request, node, fields, evidenceLinks, enabled: ["codex", "live"].includes(state.config.mode),
  });
  if (name === "opportunities") renderSupply(body, report);
  if (name === "earnings") renderEarnings(body, report);
  if (name === "evidence") renderEvidence(body, report);
  if (name === "source") body.append(node("pre", report.markdown || ""));
}

function selectAction(name) {
  state.action = name;
  all("[data-action]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.action === name));
  });
  $("#question-form").hidden = name !== "question";
  $("#scenario-form").hidden = name !== "scenario";
}

function renderReport(report) {
  state.report = report;
  $("[data-tab=earnings]").hidden = !report.earnings;
  keepReport(report);
  switchPage("report");
  const synthetic = report.evidence?.some((item) => item.synthetic);
  $("#report-label").textContent = synthetic ? "虛構示範" : "事件研究";
  $("#report-title").textContent = report.target === "由事件與可見證據識別" ? "事件研究報告" : report.target;
  $("#event-text").textContent = report.event_text;
  $("#report-date").textContent = `截止 ${dateText(report.as_of)}`;
  $("#report-horizon").textContent = report.horizon;
  $("#report-revision").textContent = `版本 v${report.revision}`;
  const outputs = report.model_outputs;
  const inputs = report.model_inputs;
  $("#metrics").replaceChildren(...(inputs && outputs ? [
    metric("稀釋 EPS 增量", numberText(outputs.incremental_eps, true), `${inputs.currency}／股`),
    metric("增量營業利益", numberText(outputs.incremental_operating_profit, true), inputs.currency),
    metric("認列批量", numberText(inputs.lots), `批 · 損益兩平 ${numberText(outputs.break_even_lots)} 批`),
  ] : [
    metric("供應鏈公司", report.assessment?.supply_chain?.length || 0, "家"),
    metric("延伸交易機會", report.assessment?.trade_opportunities?.length || 0, "項"),
    metric("時點可見證據", report.evidence?.length || 0, "筆"),
  ]));
  const scenario = $("[data-action=scenario]");
  scenario.disabled = !inputs;
  scenario.title = inputs ? "" : "此報告未提供財務情境參數";
  $("#scenario-note").textContent = inputs ? `目前為 ${numberText(inputs.lots)} 批。重算將另存子版。` : "";
  const searchable = state.config.mode === "codex" && Boolean(report.discovery);
  $("#auto-search").disabled = !searchable;
  $("#search-label").textContent = searchable ? "必要時補搜證據" : "此版本使用既有證據";
  if (!inputs) selectAction("question");
  $("#answer").replaceChildren();
  $("#answer").hidden = true;
  renderHistory();
  selectTab(state.tab);
}

async function loadReport(id, revision) {
  renderReport(await request(`/reports/${encodeURIComponent(id)}/revisions/${revision}`));
}

async function submitEvent(payload, exercise = null) {
  const result = await request("/events", payload);
  state.tab = payload.earnings_plan ? "earnings" : "overview";
  await loadReport(result.report_id, result.revision);
  if (exercise) {
    selectAction("question");
    if (exercise.tab) selectTab(exercise.tab);
    $("#question").value = exercise.question;
    $("#question").focus();
  }
}

function showAnswer(result) {
  const panel = $("#answer");
  panel.hidden = false;
  panel.replaceChildren(node("h3", result.child_revision ? `已建立子版 v${result.child_revision}` : "追問結果"),
    node("p", result.answer));
  if (result.evidence_ids?.length) panel.append(evidenceLinks(result.evidence_ids));
  if (result.gaps?.length) {
    const gaps = node("ul", null, "small");
    result.gaps.forEach((gap) => gaps.append(node("li", gap)));
    panel.append(gaps);
  }
  panel.append(businessLinkageBlock(result), scenarioBlock(result));
  const messages = {
    no_new_sources: "補搜未取得可納入的新來源。",
    unresolved: "找到其他來源，仍無法回答此問題。",
    failed: "補搜執行失敗，顯示原版本的回答。",
  };
  if (messages[result.evidence_search?.status]) {
    panel.append(node("p", messages[result.evidence_search.status], "small"));
  }
  if (result.incremental_eps_delta !== undefined) {
    panel.append(node("p", `相對母版 EPS 差額 ${numberText(result.incremental_eps_delta, true)}`, "small"));
    const comparable = {
      "model_inputs.lots": "認列批量",
      "model_outputs.incremental_operating_profit": "營業利益增量",
      "model_outputs.incremental_eps": "稀釋 EPS 增量",
    };
    const changes = (result.changes || []).filter((entry) => comparable[entry.field]);
    if (changes.length) {
      const table = node("table", null, "compare");
      const header = node("tr");
      for (const title of ["指標", "母版", "子版"]) header.append(node("th", title));
      const head = node("thead");
      head.append(header);
      const body = node("tbody");
      for (const change of changes) {
        const row = node("tr");
        row.append(node("th", comparable[change.field]), node("td", numberText(change.before)),
          node("td", numberText(change.after)));
        body.append(row);
      }
      const container = node("div", null, "scroll-table");
      table.append(head, body);
      container.append(table);
      panel.append(container);
    }
  }
}

async function ask(body) {
  const report = state.report;
  const result = await request(`/reports/${encodeURIComponent(report.report_id)}/questions`, {
    parent_revision: report.revision, ...body,
  });
  if (result.child_revision) await loadReport(report.report_id, result.child_revision);
  showAnswer(result);
}

function selectInput(name) {
  all("[data-input]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.input === name));
  });
  const simple = name === "simple";
  $("#simple-input").hidden = !simple;
  $("#json-input").hidden = simple;
  $("#intake").disabled = !simple;
  $("#cutoff").disabled = !simple;
  $("#event-json").disabled = simple;
}

function showDialog(payload, exercise = null) {
  pendingExercise = exercise;
  $("#event-error").textContent = "";
  $("#event-form").reset();
  const localNow = new Date(Date.now() - new Date().getTimezoneOffset() * 60_000);
  $("#cutoff").value = localNow.toISOString().slice(0, 19);
  $("#domains-row").hidden = true;
  $("#event-json").value = payload ? JSON.stringify(payload, null, 2) : "";
  selectInput(payload ? "json" : "simple");
  $("#search-mode").disabled = state.config.mode !== "codex";
  $("#event-dialog").showModal();
}

function eventInput() {
  if (!$("#json-input").hidden) return JSON.parse($("#event-json").value);
  const payload = { event_text: $("#intake").value.trim(), as_of: new Date($("#cutoff").value).toISOString() };
  const target = $("#target").value.trim();
  const horizon = $("#horizon").value.trim();
  const mode = $("#search-mode").value;
  if (target) payload.research_target = target;
  if (horizon) payload.research_horizon = horizon;
  if (mode) payload.search_mode = mode;
  if (mode && mode !== "off") {
    payload.search_domains = $("#domains").value.split(",").map((value) => value.trim()).filter(Boolean);
  }
  return payload;
}

function previewExample(name, payload, exercise) {
  previewSelection = { payload, exercise };
  switchPage("preview");
  $("#preview-title").textContent = exampleLabels[name];
  $("#preview-event").textContent = payload.event_text;
  $("#preview-note").textContent = `截止 ${dateText(payload.as_of)}。來源日期以 UTC 日末作為回放代理。`;
  const params = new URLSearchParams({ example: name });
  if (exercise) params.set("question", String(questionBank.indexOf(exercise) + 1));
  const button = $("#preview-run");
  button.href = state.config.mode === "fixture" ? `http://127.0.0.1:8000/?${params}` : `?${params}`;
  button.textContent = state.config.mode === "fixture" ? "在 Codex 工作台分析" : "使用這個案例";
  const sources = $("#preview-evidence");
  sources.replaceChildren();
  if (exercise) sources.append(node("p", exercise.question, "notice"));
  const cutoff = Date.parse(payload.as_of);
  const evidence = payload.documents
    .filter((doc) => Math.max(Date.parse(doc.published_at), Date.parse(doc.obtained_at)) <= cutoff)
    .flatMap((doc) => Object.entries(doc.paragraphs).map(([paragraph, quote]) => ({
      ...doc, id: `${doc.id}:${paragraph}`, quote,
    })));
  renderEvidence(sources, { evidence });
}

async function loadExample(name, exercise = null, preview = false) {
  const payload = await request(`/workbench/examples/${name}`);
  if (exercise?.asOf) payload.as_of = exercise.asOf;
  if (preview || state.config.mode === "fixture") previewExample(name, payload, exercise);
  else showDialog(payload, exercise);
}

function showQuestionBank() {
  $("#bank-list").replaceChildren(...questionBank.map((exercise, index) => {
    const item = node("article", null, "item bank-item");
    const title = node("div", null, "item-header");
    title.append(node("h3", `${index + 1}. ${exercise.title}`),
      node("span", exampleLabels[exercise.example], "badge"));
    const button = node("button", "載入此題", "button quiet");
    button.type = "button";
    button.addEventListener("click", () => {
      $("#question-bank").close();
      perform(() => loadExample(exercise.example, exercise), "正在載入題目與案例…");
    });
    item.append(title, node("p", exercise.question), button);
    return item;
  }));
  $("#question-bank").showModal();
}

all("[data-tab]").forEach((button) => button.addEventListener("click", () => selectTab(button.dataset.tab)));
all("[data-action]").forEach((button) => button.addEventListener("click", () => selectAction(button.dataset.action)));
all("[data-input]").forEach((button) => button.addEventListener("click", () => selectInput(button.dataset.input)));
all("[data-example]").forEach((button) => button.addEventListener("click", () =>
  perform(() => loadExample(button.dataset.example, null, true), "正在載入公開案例…")));
$("#go-home").addEventListener("click", () => switchPage(state.report ? "report" : previewSelection ? "preview" : "empty"));
$("#go-history").addEventListener("click", () => { renderHistory(); switchPage("history"); });
$("#new-analysis").addEventListener("click", () => showDialog());
$("#open-question-bank").addEventListener("click", showQuestionBank);
$("#close-question-bank").addEventListener("click", () => $("#question-bank").close());
$("#preview-run").addEventListener("click", (event) => {
  if (state.config.mode === "fixture" || !previewSelection) return;
  event.preventDefault();
  showDialog(previewSelection.payload, previewSelection.exercise);
});
$("#close-dialog").addEventListener("click", () => $("#event-dialog").close());
$("#cancel-dialog").addEventListener("click", () => $("#event-dialog").close());
$("#search-mode").addEventListener("change", (event) => {
  const mode = event.target.value;
  $("#domains-row").hidden = !mode || mode === "off";
  $("#search-help").textContent = mode === "live"
    ? "請保留搜尋時間。截止後才取得的文件會被排除。"
    : "以公告日期的 UTC 日末作為歷史可得時點代理。";
});
$("#event-form").addEventListener("submit", (event) => {
  event.preventDefault();
  $("#event-error").textContent = "";
  perform(async () => {
    const exercise = pendingExercise;
    await submitEvent(eventInput(), exercise);
    $("#event-dialog").close();
    if (exercise) $("#question").focus();
  }, "正在建立分析…", (error) => { $("#event-error").textContent = error.message; });
});
$("#question-form").addEventListener("submit", (event) => {
  event.preventDefault();
  perform(() => ask({
    question: $("#question").value.trim(),
    evidence_search: $("#auto-search").checked ? "auto" : "off",
  }), "正在查閱證據與回答…");
});
$("#scenario-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const lots = $("#lots").valueAsNumber;
  perform(() => ask({ question: `若本季認列 ${lots} 批，結果如何？`, overrides: { lots } }), "正在重算情境…");
});
$("#download").addEventListener("click", () => {
  const report = state.report;
  const url = URL.createObjectURL(new Blob([report.markdown], { type: "text/markdown;charset=utf-8" }));
  const link = node("a");
  link.href = url;
  link.download = `hypogen-${report.report_id}-v${report.revision}.md`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});

async function boot() {
  await perform(async () => {
    state.config = await request("/workbench/config");
    const { mode, model } = state.config;
    $("#mode-label").textContent = `${modes[mode] || mode}${model ? ` · ${model}` : ""}`;
    $("#new-analysis").disabled = mode === "fixture";
    const params = new URLSearchParams(location.search);
    const requestedReport = params.get("report") || "";
    if (/^[a-f0-9]{32}$/.test(requestedReport)) {
      if (params.get("view") === "tree") state.tab = "tree";
      const revision = Number(params.get("revision") || "1");
      if (Number.isSafeInteger(revision) && revision > 0) {
        await loadReport(requestedReport, revision);
        return;
      }
    }
    const selected = params.get("example");
    if (Object.hasOwn(exampleLabels, selected)) {
      const exercise = questionBank[Number(params.get("question")) - 1];
      await loadExample(selected, exercise?.example === selected ? exercise : null, true);
      return;
    }
    const latest = state.history[0];
    if (latest) {
      try {
        const report = await request(`/reports/${encodeURIComponent(latest.id)}/revisions/${latest.revision}`);
        if (!report.evidence?.some((item) => item.synthetic)) {
          renderReport(report);
          return;
        }
      } catch {
        // A different local database may not have the last opened report.
      }
    }
    await loadExample("asml-q3", null, true);
  }, "正在連線研究服務…", (error) => {
    $("#mode-dot").classList.add("error");
    $("#mode-label").textContent = "連線失敗";
    switchPage("empty");
    status(error.message, true);
  });
}

boot();

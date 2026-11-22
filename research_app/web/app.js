import { exampleLabels, questionBank } from "./question-bank.js";

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
  if (entry.kind === "earnings_scenario") return "盈利重算";
  return entry.kind === "scenario" ? "情境重算" : entry.kind === "evidence_follow_up" ? "補搜證據" : "研究版本";
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

function renderOverview(body, report) {
  const assessment = report.assessment || {};
  const intro = node("div", null, "thesis");
  intro.append(node("h2", "核心判斷"), node("p", assessment.thesis || "查閱報告全文以取得原始研究結論。"));
  body.append(intro, fields([["首要待查", assessment.key_gap], ["下一步", assessment.next_check]]), opportunityBlock(report));
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
}

function renderSupply(body, report) {
  body.append(opportunityBlock(report));
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

function renderEarnings(body, report) {
  const { earnings } = report;
  const currency = earnings.inputs.currency;
  const path = `/reports/${encodeURIComponent(report.report_id)}/revisions/${report.revision}`;
  body.append(heading("盈利預估", `${currency} 百萬／EPS 為每股`));
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
  }
  if (earnings.valuation) {
    body.append(heading("每股情境價值", currency));
    body.append(fields(Object.entries(earnings.valuation.scenarios).map(([scenario, value]) =>
      [({ bear: "空方", base: "基準", bull: "多方" })[scenario], value.value ? Number(value.value).toFixed(2) : "年度 EPS 非正"])));
  }
  const driver = earnings.inputs.drivers[0];
  if (driver) {
    body.append(jsonAction("建立盈利重算子版", { drivers: [driver] }, async (payload) => {
      const child = await request(`/reports/${encodeURIComponent(report.report_id)}/earnings/branches`,
        { ...payload, parent_revision: report.revision });
      renderReport(child);
    }));
  }
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
  body.replaceChildren();
  const report = state.report;
  if (!report) return;
  if (name === "overview") renderOverview(body, report);
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

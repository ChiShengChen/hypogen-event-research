const expandedByRevision = new Map();
const selectionByRevision = new Map();
const pendingByRevision = new Map();
const modes = { followup: "延伸追問", fanout: "展開多立場", custom: "自訂立場" };
const directions = { up: "增加", down: "減少", flat: "持平", unknown: "待查" };

export async function renderHypothesisTree(body, { report, request, node, fields, evidenceLinks, enabled }) {
  const key = `${report.report_id}/${report.revision}`;
  const url = `/reports/${encodeURIComponent(report.report_id)}/revisions/${report.revision}/hypothesis-tree`;
  const panel = node("section", null, "hypothesis-tree");
  const status = node("p", "正在讀取假說樹…", "form-note");
  status.setAttribute("role", "status");
  panel.append(status);
  body.append(panel);

  let nodes;
  try {
    await pendingByRevision.get(key)?.catch(() => {});
    ({ nodes } = await request(url));
  } catch (error) {
    const retry = node("button", "重新載入", "button quiet");
    retry.type = "button";
    retry.addEventListener("click", () => {
      panel.remove();
      renderHypothesisTree(body, { report, request, node, fields, evidenceLinks, enabled });
    });
    status.textContent = error.message;
    status.classList.add("error-text");
    panel.append(retry);
    return;
  }
  if (!panel.isConnected) return;

  const grid = node("div", null, "hypothesis-tree-grid");
  const outline = node("nav", null, "hypothesis-outline");
  outline.setAttribute("aria-label", "假說樹分支");
  const detail = node("section", null, "hypothesis-detail");
  detail.setAttribute("aria-label", "所選節點");
  grid.append(outline, detail);
  panel.replaceChildren(grid);
  const expanded = expandedByRevision.get(key) || new Set(["root", ...nodes.filter(item => item.kind === "stance").map(item => item.id)]);
  expandedByRevision.set(key, expanded);
  let selected = selectionByRevision.get(key) || "root";

  function redraw(focusId = null) {
    const byId = new Map(nodes.map(item => [item.id, item]));
    const children = new Map();
    for (const item of nodes) {
      if (!children.has(item.parent_id)) children.set(item.parent_id, []);
      children.get(item.parent_id).push(item);
    }
    if (!byId.has(selected)) selected = "root";
    const top = node("ul", null, "hypothesis-branches");
    const stack = [[byId.get("root"), top]];
    let focusTarget;
    while (stack.length) {
      const [item, list] = stack.pop();
      const li = node("li");
      const row = node("div", null, "hypothesis-node-row");
      const descendants = children.get(item.id) || [];
      if (descendants.length) {
        const open = expanded.has(item.id);
        const disclosure = node("button", open ? "−" : "+", "hypothesis-toggle");
        disclosure.type = "button";
        disclosure.setAttribute("aria-label", `${open ? "收合" : "展開"} ${item.title}`);
        disclosure.setAttribute("aria-expanded", String(open));
        disclosure.addEventListener("click", () => {
          if (expanded.has(item.id)) expanded.delete(item.id);
          else expanded.add(item.id);
          redraw(`toggle:${item.id}`);
        });
        if (focusId === `toggle:${item.id}`) focusTarget = disclosure;
        row.append(disclosure);
      } else {
        row.append(node("span", "•", "hypothesis-leaf"));
      }
      const select = node("button", null, "hypothesis-node");
      select.type = "button";
      select.title = item.title;
      if (selected === item.id) select.setAttribute("aria-current", "true");
      select.append(node("span", item.title, "hypothesis-node-title"));
      if (item.kind === "hypothesis" && item.stance_code) select.dataset.stance = item.stance_code;
      if (item.kind === "custom") select.append(node("span", "自訂", "badge"));
      if (byId.get(item.parent_id)?.kind === "fanout") select.append(node("span", item.stance, "badge"));
      select.addEventListener("click", () => {
        selected = item.id;
        selectionByRevision.set(key, selected);
        redraw(selected);
      });
      if (focusId === item.id) focusTarget = select;
      row.append(select);
      li.append(row);
      list.append(li);
      if (descendants.length && expanded.has(item.id)) {
        const nested = node("ul", null, "hypothesis-branches");
        li.append(nested);
        for (let i = descendants.length - 1; i >= 0; i--) stack.push([descendants[i], nested]);
      }
    }
    const scrollTop = outline.scrollTop;
    outline.replaceChildren(top);
    outline.scrollTop = scrollTop;
    renderDetail(byId.get(selected), children.get(selected) || [], byId);
    focusTarget?.focus();
  }

  function renderDetail(item, children, byId) {
    const title = node("h2", item.title);
    title.tabIndex = -1;
    detail.replaceChildren(title);
    if (item.stance && item.title !== item.stance) detail.append(node("p", item.stance, "small hypothesis-stance"));
    if (item.question && item.question !== item.title) detail.append(node("p", item.question, "hypothesis-question"));
    if (item.case) {
      const c = item.case;
      detail.append(fields([
        ["驅動因素", c.driver], ["成立條件", c.conditions.join("、")], ["傳導機制", c.mechanism],
        ["財務影響", `${c.financial_metric}${directions[c.direction]}。${c.scale_basis_or_gap}`],
        ["比較基準", c.baseline], ["公開查核", `${c.public_source} · ${c.observation_period} · ${c.public_metric}`],
        ["可驗證預測", c.prediction], ["推翻條件", c.falsifier], ["覆核日", c.review_by],
      ]), evidenceLinks(c.evidence_ids));
    } else if (children.length) {
      const list = node("ul", null, "hypothesis-child-links");
      for (const child of children) {
        const label = item.kind === "fanout" ? `${child.stance} · ${child.title}` : child.title;
        const action = node("button", label, "button quiet");
        action.type = "button";
        action.addEventListener("click", () => {
          expanded.add(item.id);
          selected = child.id;
          selectionByRevision.set(key, selected);
          redraw(selected);
        });
        const li = node("li");
        li.append(action);
        list.append(li);
      }
      detail.append(list);
    }
    for (const gap of item.gaps || []) detail.append(node("p", gap, "notice"));
    if (!enabled) {
      detail.append(node("p", "使用 Codex CLI 或模型 API 模式即可產生新分支。", "notice"));
      return;
    }

    const form = node("form", null, "hypothesis-form");
    const modeLabel = node("label", "分支方式");
    const mode = node("select");
    modeLabel.htmlFor = "hypothesis-mode";
    mode.id = "hypothesis-mode";
    for (const [value, label] of Object.entries(modes)) {
      const option = node("option", label);
      option.value = value;
      mode.append(option);
    }
    mode.value = item.kind === "root" ? "fanout" : "followup";
    const custom = node("div");
    const stanceLabel = node("label", "立場名稱");
    const stance = node("input");
    stance.id = "hypothesis-stance";
    stanceLabel.htmlFor = stance.id;
    stance.maxLength = 80;
    stance.placeholder = "例如：客戶延後驗收";
    custom.append(stanceLabel, stance);
    const questionLabel = node("label", "你想檢驗什麼？");
    const question = node("textarea");
    question.id = "hypothesis-question";
    questionLabel.htmlFor = question.id;
    question.rows = 3;
    question.maxLength = 2400;
    question.required = true;
    const submit = node("button", "生成分支", "button primary");
    submit.type = "submit";
    const feedback = node("p", "", "form-note");
    feedback.setAttribute("role", "status");
    function showMode() {
      custom.hidden = mode.value !== "custom";
      stance.required = !custom.hidden;
      question.placeholder = mode.value === "custom" ? "輸入你的假設，並寫出希望驗證的條件。" :
        "例如：若驗收延後一季，哪些公開指標能區分出貨延後與需求下修？";
    }
    const busy = pendingByRevision.has(key);
    submit.disabled = busy;
    feedback.textContent = busy ? "正在產生此版本的分支…" : "";
    showMode();
    mode.addEventListener("change", showMode);
    form.append(modeLabel, mode, custom, questionLabel, question, submit, feedback);
    detail.append(form);
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (pendingByRevision.has(key)) return;
      if (!question.value.trim() || (!custom.hidden && !stance.value.trim())) {
        feedback.textContent = "請填寫要檢驗的問題與自訂立場。";
        feedback.classList.add("error-text");
        return;
      }
      submit.disabled = true;
      feedback.classList.remove("error-text");
      feedback.textContent = "正在依本版證據產生分支…";
      const pending = request(url, {
        parent_id: item.id, mode: mode.value, question: question.value.trim(),
        ...(mode.value === "custom" ? { stance: stance.value.trim() } : {}),
      });
      pendingByRevision.set(key, pending);
      let result;
      try {
        result = await pending;
      } catch (error) {
        feedback.textContent = error.message;
        feedback.classList.add("error-text");
      } finally {
        pendingByRevision.delete(key);
        submit.disabled = false;
      }
      if (result) {
        nodes.push(...result.nodes);
        for (let ancestor = item; ancestor; ancestor = byId.get(ancestor.parent_id)) expanded.add(ancestor.id);
        expanded.add(result.selected_id);
        selected = result.selected_id;
        selectionByRevision.set(key, selected);
      }
      if (panel.isConnected && (result || !form.isConnected)) redraw(result ? selected : null);
    });
  }
  redraw();
}

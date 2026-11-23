const CARD_WIDTH = 206;
const CARD_HEIGHT = 78;
const COLUMN_STEP = 259;
const ROW_STEP = 104;
const LABELS = { root: "研究事件", stance: "立場", fanout: "多立場分支", custom: "自訂立場", followup: "延伸追問" };

export function layoutHypotheses(nodes, expanded) {
  const children = new Map();
  for (const item of nodes) {
    if (!children.has(item.parent_id)) children.set(item.parent_id, []);
    children.get(item.parent_id).push(item);
  }
  const points = new Map();
  const visible = [];
  const stack = (children.get(null) || []).map(item => [item, 0]).reverse();
  let nextRow = 0;
  while (stack.length) {
    const [item, depth] = stack.pop();
    const descendants = expanded.has(item.id) ? children.get(item.id) || [] : [];
    visible.push(item);
    points.set(item.id, { x: depth * COLUMN_STEP, y: descendants.length ? null : nextRow++ * ROW_STEP });
    for (let i = descendants.length - 1; i >= 0; i--) stack.push([descendants[i], depth + 1]);
  }
  for (let i = visible.length - 1; i >= 0; i--) {
    const item = visible[i];
    const point = points.get(item.id);
    if (point.y !== null) continue;
    const first = points.get(children.get(item.id)[0].id);
    const last = points.get(children.get(item.id).at(-1).id);
    point.y = (first.y + last.y) / 2;
  }
  return { visible, points, children };
}

function loadOffsets(key) {
  try {
    const entries = JSON.parse(localStorage.getItem(key) || "[]");
    return new Map(entries.filter(([id, p]) => typeof id === "string" &&
      Number.isFinite(p?.x) && Number.isFinite(p?.y)));
  } catch {
    return new Map();
  }
}

export function createHypothesisCanvas({ key, node, enabled, select, toggle }) {
  const storageKey = `hypogen-hypothesis-layout-v1:${key}`;
  const offsets = loadOffsets(storageKey);
  const element = node("section", null, "hypothesis-graph");
  const toolbar = node("div", null, "graph-toolbar");
  const tools = node("div", null, "graph-tools");
  const zoomLevel = node("output", "100%", "graph-scale");
  zoomLevel.setAttribute("aria-label", "畫布縮放比例");
  const viewport = node("div", null, "graph-viewport");
  viewport.tabIndex = 0;
  viewport.setAttribute("aria-label", "假說節點畫布。拖曳空白處平移，滾輪縮放。");
  const canvas = node("canvas", null, "graph-wires");
  canvas.setAttribute("aria-hidden", "true");
  const plane = node("div", null, "graph-plane");
  viewport.append(canvas, plane);
  toolbar.append(node("h2", "分支畫布"), tools);
  element.append(toolbar, viewport);

  const pen = canvas.getContext("2d");
  const cards = new Map();
  let locations = new Map();
  let visible = [];
  let byId = new Map();
  let selected;
  let view;
  let fitting = true;
  let gesture;
  let pinch;
  const touches = new Map();
  let spacePan = false;
  let frame = 0;

  function saveOffsets() {
    try {
      localStorage.setItem(storageKey, JSON.stringify([...offsets]));
    } catch {
      // The current session can still move nodes when browser storage is unavailable.
    }
  }

  function button(label, name, action) {
    const control = node("button", label);
    control.type = "button";
    control.setAttribute("aria-label", name);
    control.title = name;
    control.addEventListener("click", action);
    return control;
  }

  function draw() {
    frame = 0;
    if (!view) return;
    const { clientWidth: width, clientHeight: height } = viewport;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const pixelWidth = Math.round(width * dpr);
    const pixelHeight = Math.round(height * dpr);
    if (canvas.width !== pixelWidth || canvas.height !== pixelHeight) {
      canvas.width = pixelWidth;
      canvas.height = pixelHeight;
    }
    plane.style.transform = `translate(${view.x}px, ${view.y}px) scale(${view.scale})`;
    viewport.style.backgroundPosition = `${view.x % 24}px ${view.y % 24}px`;
    zoomLevel.value = `${Math.round(view.scale * 100)}%`;
    if (!pen) return;
    pen.setTransform(dpr, 0, 0, dpr, 0, 0);
    pen.clearRect(0, 0, width, height);
    pen.lineCap = "round";
    const path = new Set();
    for (let item = byId.get(selected); item; item = byId.get(item.parent_id)) path.add(item.id);
    for (const item of visible) {
      const parent = locations.get(item.parent_id);
      if (!parent) continue;
      const child = locations.get(item.id);
      const startX = view.x + (parent.x + CARD_WIDTH) * view.scale;
      const endX = view.x + child.x * view.scale;
      const startY = view.y + (parent.y + CARD_HEIGHT / 2) * view.scale;
      const endY = view.y + (child.y + CARD_HEIGHT / 2) * view.scale;
      const bend = Math.max(24, Math.abs(endX - startX) / 2);
      const highlight = path.has(item.id) || item.parent_id === selected;
      const isInput = item.kind === "input";
      pen.setLineDash(isInput ? [4, 5] : []);
      pen.strokeStyle = highlight ? "#9bd4a9" : "#657971";
      pen.lineWidth = highlight ? 2.5 : 1.5;
      pen.beginPath();
      pen.moveTo(startX, startY);
      pen.bezierCurveTo(startX + bend, startY, endX - bend, endY, endX, endY);
      pen.stroke();
      if (isInput) {
        pen.fillStyle = pen.strokeStyle;
        pen.beginPath();
        pen.moveTo(startX + 4, startY);
        pen.lineTo(startX + 11, startY - 4);
        pen.lineTo(startX + 11, startY + 4);
        pen.fill();
      }
    }
  }

  function paint() {
    if (!frame) frame = requestAnimationFrame(draw);
  }

  function fit() {
    if (!locations.size) return;
    let left = Infinity, right = -Infinity, top = Infinity, bottom = -Infinity;
    for (const p of locations.values()) {
      left = Math.min(left, p.x);
      right = Math.max(right, p.x + CARD_WIDTH);
      top = Math.min(top, p.y);
      bottom = Math.max(bottom, p.y + CARD_HEIGHT);
    }
    const width = viewport.clientWidth;
    const height = viewport.clientHeight;
    if (!width || !height) return;
    const scale = Math.min(1, Math.max(0.045, Math.min((width - 46) / (right - left), (height - 46) / (bottom - top))));
    view = { scale, x: (width - (right + left) * scale) / 2, y: (height - (bottom + top) * scale) / 2 };
    fitting = true;
    paint();
  }

  function zoom(factor, x = viewport.clientWidth / 2, y = viewport.clientHeight / 2) {
    if (!view) return;
    const scale = Math.max(0.045, Math.min(2, view.scale * factor));
    const ratio = scale / view.scale;
    view = { scale, x: x - (x - view.x) * ratio, y: y - (y - view.y) * ratio };
    fitting = false;
    paint();
  }

  function centerSelected(scale) {
    const p = locations.get(selected);
    const { clientWidth: width, clientHeight: height } = viewport;
    if (!p || !width || !height) return;
    const visibleScale = Math.max(0.045, Math.min(scale, (width - 28) / CARD_WIDTH, (height - 28) / CARD_HEIGHT));
    view = { scale: visibleScale, x: width / 2 - (p.x + CARD_WIDTH / 2) * visibleScale,
      y: height / 2 - (p.y + CARD_HEIGHT / 2) * visibleScale };
    fitting = false;
    paint();
  }

  function focusSelected() {
    centerSelected(Math.max(0.9, view?.scale ?? 0));
  }

  function initialView() {
    const width = viewport.clientWidth;
    if (!width) return;
    fit();
    if (width <= 520 || (view && view.scale < 0.65)) centerSelected(0.9);
  }

  function reveal(id) {
    const p = locations.get(id);
    if (!view || !p) return;
    const { scale } = view;
    const x = p.x * scale + view.x;
    const y = p.y * scale + view.y;
    if (x < 12 || x + CARD_WIDTH * scale > viewport.clientWidth - 12) {
      view.x = viewport.clientWidth / 2 - (p.x + CARD_WIDTH / 2) * scale;
    }
    if (y < 12 || y + CARD_HEIGHT * scale > viewport.clientHeight - 12) {
      view.y = viewport.clientHeight / 2 - (p.y + CARD_HEIGHT / 2) * scale;
    }
    paint();
  }

  function place(card, point) {
    card.style.left = `${point.x}px`;
    card.style.top = `${point.y}px`;
  }

  function update(nodes, expanded, active, focusId) {
    selected = active;
    byId = new Map(nodes.map(item => [item.id, item]));
    const graph = layoutHypotheses(nodes, expanded);
    visible = graph.visible;
    locations = graph.points;
    cards.clear();
    const fragment = document.createDocumentFragment();
    let focusTarget;
    for (const item of visible) {
      const point = locations.get(item.id);
      const offset = offsets.get(item.id);
      if (offset) {
        point.x += offset.x;
        point.y += offset.y;
      }
      const card = node("article", null, "graph-node");
      card.dataset.nodeId = item.id;
      card.dataset.kind = item.kind;
      if (item.stance_code) card.dataset.stance = item.stance_code;
      if (item.id === selected) card.classList.add("graph-node-active");
      if (item.parent_id !== null) card.append(node("span", null, "graph-port graph-port-in"));
      if ((graph.children.get(item.id) || []).length || (enabled && !item.input)) card.append(node("span", null, "graph-port graph-port-out"));
      const header = node("div", null, "graph-node-header");
      header.append(node("span", item.input ?
        (item.input.status === "excluded" ? "輸入泡泡 · 未納入" : "輸入泡泡") :
        LABELS[item.kind] || item.stance || "假說"));
      const actions = node("div", null, "graph-node-controls");
      if (graph.children.has(item.id)) {
        const open = expanded.has(item.id);
        const control = button(open ? "−" : "+", `${open ? "收合" : "展開"} ${item.title}`, () => toggle(item.id));
        control.dataset.graphAction = "toggle";
        control.setAttribute("aria-expanded", String(open));
        if (focusId === `toggle:${item.id}`) focusTarget = control;
        actions.append(control);
      }
      if (enabled && !item.input) {
        const add = button("↗", `在 ${item.title} 開分支`, () => select(item.id, true));
        add.dataset.graphAction = "branch";
        actions.append(add);
      }
      header.append(actions);
      const entry = button(item.title, item.title, () => select(item.id));
      entry.className = "graph-node-title";
      if (item.id === selected) entry.setAttribute("aria-current", "true");
      if (item.id === focusId) focusTarget = entry;
      card.append(header, entry);
      place(card, point);
      cards.set(item.id, card);
      fragment.append(card);
    }
    plane.replaceChildren(fragment);
    if (!view) initialView();
    if (focusId) reveal(locations.has(focusId) ? focusId : selected);
    focusTarget?.focus({ preventScroll: true });
    paint();
  }

  function touchGeometry(ids) {
    const [first, second] = ids.map(id => touches.get(id));
    const rect = viewport.getBoundingClientRect();
    return {
      x: (first.x + second.x) / 2 - rect.left,
      y: (first.y + second.y) / 2 - rect.top,
      distance: Math.max(1, Math.hypot(first.x - second.x, first.y - second.y)),
    };
  }

  viewport.addEventListener("pointerdown", event => {
    if (!view || (event.button !== 0 && event.button !== 1)) return;
    if (event.button === 0 && !spacePan && !touches.size && event.target.closest("[data-graph-action]")) return;
    if (event.pointerType === "touch") {
      touches.set(event.pointerId, { x: event.clientX, y: event.clientY });
      if (touches.size > 1) {
        viewport.setPointerCapture(event.pointerId);
        if (!pinch) {
          const ids = [...touches.keys()].slice(0, 2);
          if (gesture?.id && gesture.moved) saveOffsets();
          gesture = null;
          pinch = { ids, at: touchGeometry(ids), start: { ...view } };
          viewport.classList.add("graph-panning");
        }
        event.preventDefault();
        return;
      }
    }
    if (gesture || pinch) return;
    const id = event.button === 0 && !spacePan ? event.target.closest("[data-node-id]")?.dataset.nodeId : null;
    gesture = { pointer: event.pointerId, x: event.clientX, y: event.clientY, id, moved: false,
      start: { ...view }, offset: offsets.get(id) || { x: 0, y: 0 }, point: locations.get(id) };
    viewport.setPointerCapture(event.pointerId);
    if (!id) viewport.focus({ preventScroll: true });
    event.preventDefault();
  });
  viewport.addEventListener("pointermove", event => {
    if (touches.has(event.pointerId)) {
      touches.set(event.pointerId, { x: event.clientX, y: event.clientY });
      if (pinch?.ids.includes(event.pointerId)) {
        const next = touchGeometry(pinch.ids);
        const { start, at } = pinch;
        const scale = Math.max(0.045, Math.min(2, start.scale * next.distance / at.distance));
        const ratio = scale / start.scale;
        view = { scale, x: next.x - (at.x - start.x) * ratio, y: next.y - (at.y - start.y) * ratio };
        fitting = false;
        paint();
        return;
      }
    }
    if (gesture?.pointer !== event.pointerId) return;
    const dx = event.clientX - gesture.x;
    const dy = event.clientY - gesture.y;
    if (!gesture.moved && Math.hypot(dx, dy) < 4) return;
    gesture.moved = true;
    fitting = false;
    viewport.classList.toggle("graph-panning", !gesture.id);
    if (gesture.id) {
      const x = dx / view.scale, y = dy / view.scale;
      const point = { x: gesture.point.x + x, y: gesture.point.y + y };
      offsets.set(gesture.id, { x: gesture.offset.x + x, y: gesture.offset.y + y });
      locations.set(gesture.id, point);
      place(cards.get(gesture.id), point);
    } else {
      view.x = gesture.start.x + dx;
      view.y = gesture.start.y + dy;
    }
    paint();
  });
  function endGesture(event) {
    touches.delete(event.pointerId);
    if (pinch?.ids.includes(event.pointerId)) {
      pinch = null;
      viewport.classList.remove("graph-panning");
    }
    if (gesture?.pointer !== event.pointerId) return;
    const { id, moved } = gesture;
    gesture = null;
    viewport.classList.remove("graph-panning");
    if (id && moved) saveOffsets();
    if (id && !moved && event.type === "pointerup") select(id);
  }
  viewport.addEventListener("pointerup", endGesture);
  viewport.addEventListener("pointercancel", endGesture);
  viewport.addEventListener("lostpointercapture", endGesture);
  viewport.addEventListener("wheel", event => {
    event.preventDefault();
    const rect = viewport.getBoundingClientRect();
    zoom(Math.exp(-event.deltaY * (event.deltaMode === 1 ? 0.037 : 0.0015)),
      event.clientX - rect.left, event.clientY - rect.top);
  }, { passive: false });
  viewport.addEventListener("keydown", event => {
    if (event.target !== viewport || !view) return;
    const arrows = { ArrowLeft: [48, 0], ArrowRight: [-48, 0], ArrowUp: [0, 48], ArrowDown: [0, -48] };
    if (event.key in arrows) {
      view.x += arrows[event.key][0];
      view.y += arrows[event.key][1];
      fitting = false;
      paint();
    } else if (event.key === " ") spacePan = true;
    else if (event.key === "+" || event.key === "=") zoom(1.25);
    else if (event.key === "-") zoom(0.8);
    else if (event.key.toLowerCase() === "f") fit();
    else if (event.key === ".") focusSelected();
    else return;
    event.preventDefault();
  });
  viewport.addEventListener("keyup", event => { if (event.key === " ") spacePan = false; });
  viewport.addEventListener("blur", () => { spacePan = false; });

  let lastUpdate;
  tools.append(button("−", "縮小", () => zoom(0.8)), zoomLevel, button("+", "放大", () => zoom(1.25)),
    button("全覽", "縮放至全覽", fit),
    button("聚焦", "聚焦所選節點", focusSelected),
    button("排版", "恢復自動排版", () => {
      offsets.clear();
      saveOffsets();
      if (lastUpdate) update(...lastUpdate);
      fit();
    }));
  const resize = () => !view ? initialView() : fitting ? fit() : paint();
  const observer = typeof ResizeObserver === "function" ? new ResizeObserver(resize) : null;
  if (observer) observer.observe(viewport);
  else window.addEventListener("resize", resize);
  return {
    element,
    update(...args) {
      lastUpdate = args;
      update(...args);
    },
    destroy() {
      observer?.disconnect();
      if (!observer) window.removeEventListener("resize", resize);
      cancelAnimationFrame(frame);
    },
  };
}

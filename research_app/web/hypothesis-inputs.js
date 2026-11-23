export const inputLabels = { news: "新聞連結", file: "上傳資料", opinion: "我的觀點" };
const statuses = { usable: "可引用", context: "條件推演", excluded: "未納入" };

function encodeFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1]);
    reader.onerror = () => reject(new Error("無法讀取檔案。"));
    reader.readAsDataURL(file);
  });
}

export function inputDetail(node, input) {
  const section = node("div", null, "bubble-detail");
  section.append(node("p", [inputLabels[input.kind], statuses[input.status] || "待送出"].join(" · "), "small"));
  if (input.url) {
    const link = node("a", input.url);
    link.href = input.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    section.append(link);
  }
  const day = input.available_on;
  if (day) section.append(node("p", day, "small"));
  if (input.note) section.append(node("p", input.note, "notice"));
  if (input.text) section.append(node("p", input.text, "bubble-text"));
  return section;
}

export function inputComposer(node, items, changed) {
  const box = node("div", null, "bubble-composer");
  const list = node("ul", null, "bubble-chips");
  list.setAttribute("aria-label", "本次輸入");
  const editor = node("details", null, "bubble-editor");
  editor.append(node("summary", "＋ 新增資料泡泡"));
  const type = node("select");
  type.setAttribute("aria-label", "泡泡類型");
  for (const [value, label] of Object.entries(inputLabels)) {
    const item = node("option", label);
    item.value = value;
    type.append(item);
  }
  const controls = node("div");
  const feedback = node("p", "", "form-note");
  feedback.setAttribute("role", "status");
  const add = node("button", "加入泡泡", "button quiet");
  add.type = "button";
  editor.append(type, controls, add, feedback);
  box.append(list, editor);
  let input, available;

  function drawList() {
    list.replaceChildren();
    for (const item of items) {
      const line = node("li");
      const remove = node("button", "×");
      remove.type = "button";
      remove.setAttribute("aria-label", `移除 ${item.title}`);
      remove.addEventListener("click", () => {
        items.splice(items.indexOf(item), 1);
        drawList();
        changed();
      });
      line.append(node("span", item.title), remove);
      list.append(line);
    }
    add.disabled = items.length >= 6;
  }

  function labelInput(label, element) {
    const wrapper = node("label", label);
    wrapper.append(element);
    controls.append(wrapper);
  }

  function drawFields() {
    controls.replaceChildren();
    feedback.textContent = "";
    const kind = type.value;
    input = node(kind === "opinion" ? "textarea" : "input");
    available = null;
    if (kind === "news") {
      input.type = "text";
      input.inputMode = "url";
      input.placeholder = "https://";
      input.maxLength = 2000;
      labelInput("新聞網址", input);
    } else if (kind === "file") {
      input.type = "file";
      input.accept = ".pdf,.txt,.md,.csv,.json";
      labelInput("PDF、TXT、CSV、JSON 或 Markdown · 2 MB 內", input);
      available = node("input");
      available.type = "date";
      labelInput("資料可得日期（選填）", available);
    } else {
      input.rows = 3;
      input.maxLength = 2400;
      labelInput("想一起檢驗的觀點", input);
    }
  }

  add.addEventListener("click", async () => {
    if (items.length >= 6) return;
    const kind = type.value;
    const item = { id: `draft:${crypto.randomUUID()}`, kind };
    add.disabled = true;
    feedback.textContent = "";
    try {
      if (kind === "news") {
        const url = new URL(input.value.trim());
        if (url.protocol !== "https:" || url.username || url.password || !url.hostname.includes(".")) {
          throw new Error("請輸入公開的 HTTPS 新聞網址。");
        }
        Object.assign(item, { title: url.hostname, url: url.href });
      } else if (kind === "file") {
        const file = input.files[0];
        if (!file?.size || file.size > 2 * 1024 * 1024 || !/\.(pdf|txt|md|csv|json)$/i.test(file.name)) {
          throw new Error("請選擇支援的檔案，大小不超過 2 MB。");
        }
        const day = available.value || null;
        Object.assign(item, { title: file.name, filename: file.name, data: await encodeFile(file), available_on: day });
      } else {
        const text = input.value.trim();
        if (!text) throw new Error("請輸入想一起檢驗的觀點。");
        Object.assign(item, { title: inputLabels.opinion, text });
      }
      items.push(item);
      editor.open = false;
      drawFields();
      changed();
    } catch (error) {
      feedback.textContent = error instanceof TypeError ? "請輸入有效的 HTTPS 新聞網址。" : error.message;
    } finally {
      drawList();
    }
  });
  type.addEventListener("change", drawFields);
  drawFields();
  drawList();
  return box;
}

export function inputPayload(items) {
  return items.map(({ id, title, ...payload }) => payload);
}

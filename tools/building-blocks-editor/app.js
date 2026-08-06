const DEFAULT_URL = "../../docs/personality_building_blocks.json";

const GROUPS = [
  { id: "mbti_poles", label: "MBTI poles", path: ["mbti_poles"] },
  { id: "elements", label: "Astrology · elements", path: ["astrology", "elements"] },
  { id: "modalities", label: "Astrology · modalities", path: ["astrology", "modalities"] },
  { id: "sign_tweaks", label: "Astrology · sign tweaks", path: ["astrology", "sign_tweaks"] },
];

const state = {
  doc: null,
  fileHandle: null,
  fileName: null,
  dirty: false,
  groupId: "mbti_poles",
  componentId: null,
};

const el = {
  status: document.getElementById("status"),
  workspace: document.getElementById("workspace"),
  groupSelect: document.getElementById("groupSelect"),
  componentSelect: document.getElementById("componentSelect"),
  scalarsTable: document.getElementById("scalarsTable"),
  baselineTable: document.getElementById("baselineTable"),
  moodTable: document.getElementById("moodTable"),
  matrixTable: document.getElementById("matrixTable"),
  fileInput: document.getElementById("fileInput"),
  btnLoadDefault: document.getElementById("btnLoadDefault"),
  btnOpen: document.getElementById("btnOpen"),
  btnSave: document.getElementById("btnSave"),
  btnDownload: document.getElementById("btnDownload"),
};

function setStatus(message, kind = "") {
  el.status.textContent = message;
  el.status.className = `status ${kind}`.trim();
}

function markDirty(dirty = true) {
  state.dirty = dirty;
  el.btnSave.disabled = !state.doc || !state.fileHandle || !state.dirty;
  el.btnDownload.disabled = !state.doc;
  if (!state.doc) return;
  const name = state.fileName || "unsaved.json";
  setStatus(
    dirty ? `${name} · unsaved changes` : `${name} · in sync`,
    dirty ? "dirty" : "ok",
  );
}

function groupDef(id = state.groupId) {
  return GROUPS.find((g) => g.id === id);
}

function componentsForGroup() {
  const g = groupDef();
  let node = state.doc;
  for (const key of g.path) node = node[key];
  return Object.keys(node);
}

function currentBlock() {
  const g = groupDef();
  let node = state.doc;
  for (const key of g.path) node = node[key];
  return node[state.componentId];
}

function validateDoc(doc) {
  if (!doc || doc.format !== "animus.building_blocks" || doc.version !== 1) {
    throw new Error("Expected animus.building_blocks JSON (version 1)");
  }
  if (!doc.mbti_poles || !doc.astrology) {
    throw new Error("JSON missing mbti_poles / astrology sections");
  }
}

async function loadObject(doc, { fileName = "personality_building_blocks.json", fileHandle = null } = {}) {
  validateDoc(doc);
  state.doc = doc;
  state.fileName = fileName;
  state.fileHandle = fileHandle;
  state.groupId = "mbti_poles";
  populateGroupSelect();
  populateComponentSelect();
  el.workspace.classList.remove("hidden");
  renderEditor();
  markDirty(false);
}

function populateGroupSelect() {
  el.groupSelect.innerHTML = GROUPS.map(
    (g) => `<option value="${g.id}">${g.label}</option>`,
  ).join("");
  el.groupSelect.value = state.groupId;
}

function populateComponentSelect() {
  const ids = componentsForGroup();
  if (!ids.includes(state.componentId)) state.componentId = ids[0];
  el.componentSelect.innerHTML = ids.map((id) => `<option value="${id}">${id}</option>`).join("");
  el.componentSelect.value = state.componentId;
}

function numberInput(value, onChange) {
  const input = document.createElement("input");
  input.type = "number";
  input.step = "0.01";
  input.value = Number(value);
  input.addEventListener("change", () => {
    const next = Number(input.value);
    if (Number.isNaN(next)) {
      input.value = value;
      return;
    }
    onChange(next);
    markDirty(true);
  });
  return input;
}

function renderKeyValueTable(container, entries, labels, onEdit) {
  const table = document.createElement("table");
  table.innerHTML = "<thead><tr><th>Field</th><th>Value</th></tr></thead>";
  const tbody = document.createElement("tbody");
  entries.forEach((value, index) => {
    const tr = document.createElement("tr");
    const label = document.createElement("td");
    label.className = "label";
    label.textContent = labels[index] || String(index);
    const cell = document.createElement("td");
    cell.appendChild(numberInput(value, (v) => onEdit(index, v)));
    tr.append(label, cell);
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  container.replaceChildren(table);
}

function renderScalars() {
  const block = currentBlock();
  const keys = state.doc.dimensions?.scalars || Object.keys(block.scalars);
  const table = document.createElement("table");
  table.innerHTML = "<thead><tr><th>Scalar</th><th>Value</th></tr></thead>";
  const tbody = document.createElement("tbody");
  for (const key of keys) {
    const tr = document.createElement("tr");
    const label = document.createElement("td");
    label.className = "label";
    label.textContent = key;
    const cell = document.createElement("td");
    cell.appendChild(
      numberInput(block.scalars[key], (v) => {
        block.scalars[key] = v;
      }),
    );
    tr.append(label, cell);
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);
  el.scalarsTable.replaceChildren(table);
}

function renderMatrix() {
  const block = currentBlock();
  const rows = state.doc.dimensions?.matrix_rows || ["r0", "r1", "r2", "r3", "r4"];
  const cols = state.doc.dimensions?.matrix_cols || ["c0", "c1", "c2", "c3", "c4"];
  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  headRow.appendChild(document.createElement("th"));
  cols.forEach((c) => {
    const th = document.createElement("th");
    th.textContent = c.replaceAll("_", " ");
    headRow.appendChild(th);
  });
  thead.appendChild(headRow);
  const tbody = document.createElement("tbody");
  block.matrix.forEach((row, i) => {
    const tr = document.createElement("tr");
    const label = document.createElement("td");
    label.className = "label";
    label.textContent = rows[i] || String(i);
    tr.appendChild(label);
    row.forEach((value, j) => {
      const td = document.createElement("td");
      td.appendChild(
        numberInput(value, (v) => {
          block.matrix[i][j] = v;
        }),
      );
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.append(thead, tbody);
  el.matrixTable.replaceChildren(table);
}

function renderEditor() {
  if (!state.doc) return;
  const behavioral = state.doc.dimensions?.behavioral || ["0", "1", "2", "3", "4"];
  const mood = state.doc.dimensions?.mood || ["0", "1", "2", "3", "4"];
  const block = currentBlock();
  renderScalars();
  renderKeyValueTable(
    el.baselineTable,
    block.behavioral_baseline,
    behavioral,
    (index, value) => {
      block.behavioral_baseline[index] = value;
    },
  );
  renderKeyValueTable(
    el.moodTable,
    block.resting_mood,
    mood,
    (index, value) => {
      block.resting_mood[index] = value;
    },
  );
  renderMatrix();
}

function serialize() {
  return `${JSON.stringify(state.doc, null, 2)}\n`;
}

async function loadDefault() {
  try {
    const res = await fetch(DEFAULT_URL, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const doc = await res.json();
    await loadObject(doc, { fileName: "personality_building_blocks.json" });
    setStatus("Loaded default JSON via HTTP. Use Download/Save to write an override.", "ok");
    markDirty(false);
  } catch (err) {
    setStatus(
      `Could not fetch default (${err.message}). From repo root run: python -m http.server 5178 — then open /tools/building-blocks-editor/`,
      "dirty",
    );
  }
}

async function openWithPicker() {
  if (window.showOpenFilePicker) {
    try {
      const [handle] = await window.showOpenFilePicker({
        types: [{ description: "Animus building blocks", accept: { "application/json": [".json"] } }],
        multiple: false,
      });
      const file = await handle.getFile();
      const doc = JSON.parse(await file.text());
      await loadObject(doc, { fileName: file.name, fileHandle: handle });
      return;
    } catch (err) {
      if (err?.name === "AbortError") return;
      // fall through to input
    }
  }
  el.fileInput.click();
}

async function onFileInputChange(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  const doc = JSON.parse(await file.text());
  await loadObject(doc, { fileName: file.name, fileHandle: null });
  event.target.value = "";
}

async function save() {
  if (!state.doc) return;
  const text = serialize();
  if (state.fileHandle && state.fileHandle.createWritable) {
    const writable = await state.fileHandle.createWritable();
    await writable.write(text);
    await writable.close();
    markDirty(false);
    setStatus(`Saved ${state.fileName}`, "ok");
    return;
  }
  download();
}

function download() {
  if (!state.doc) return;
  const blob = new Blob([serialize()], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = state.fileName || "personality_building_blocks.json";
  a.click();
  URL.revokeObjectURL(a.href);
  setStatus(`Downloaded ${a.download}. Point Animus at this file as an override.`, "ok");
}

el.btnLoadDefault.addEventListener("click", loadDefault);
el.btnOpen.addEventListener("click", openWithPicker);
el.btnSave.addEventListener("click", () => save().catch((e) => setStatus(e.message, "dirty")));
el.btnDownload.addEventListener("click", download);
el.fileInput.addEventListener("change", (e) => onFileInputChange(e).catch((err) => setStatus(err.message, "dirty")));
el.groupSelect.addEventListener("change", () => {
  state.groupId = el.groupSelect.value;
  populateComponentSelect();
  renderEditor();
});
el.componentSelect.addEventListener("change", () => {
  state.componentId = el.componentSelect.value;
  renderEditor();
});

setStatus("Open a building-blocks JSON file, or serve the repo and Load default.");

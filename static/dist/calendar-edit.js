const SERVER_DATA = JSON.parse(
  document.getElementById("server-data")?.textContent || '{"hasData":false}'
);
const UPDATE_URL = window.UPDATE_URL || "/update_month/";

const MONTH_NAMES = [
  "Baishakh","Jestha","Ashadh","Shrawan","Bhadra","Ashwin",
  "Kartik","Mangsir","Poush","Magh","Falgun","Chaitra",
];
const WEEKDAYS = ["S","M","T","W","T","F","S"];
const EXTRA_STORE = "schoolCalendarExtras";
const EXTRA = loadExtras();

function loadExtras() {
  try { const r = localStorage.getItem(EXTRA_STORE); return r ? JSON.parse(r) : {}; } catch { return {}; }
}
function saveExtras() {
  try { localStorage.setItem(EXTRA_STORE, JSON.stringify(EXTRA)); } catch {}
}
function monthId(idx, name) { return idx !== -1 ? "i:"+idx : "n:"+(name||"").toLowerCase(); }
function monthIndexFromName(n) { const norm = (n||"").trim().toLowerCase(); return MONTH_NAMES.findIndex(m => m.toLowerCase() === norm); }

function readFormValues() {
  return {
    name: document.getElementById("month-name").value.trim() || "Mangsir",
    days: parseInt(document.getElementById("day-count").value, 10) || 31,
    start: parseInt(document.getElementById("start-day").value, 10) || 0,
  };
}
function mergeEvents(name) {
  const s = SERVER_DATA.hasData && name === SERVER_DATA.monthName ? (SERVER_DATA.events || {}) : {};
  return Object.assign({}, s, EXTRA[currentMonthId] || {});
}

function renderMonth(monthName, daysInMonth, firstDay, extraByDay) {
  const extra = extraByDay || {};
  const weekendDays = new Set();
  for (let d = 1; d <= daysInMonth; d++) { const wd = (firstDay + d - 1) % 7; if (wd === 0 || wd === 6) weekendDays.add(d); }
  const eventFor = (day) => {
    const ex = extra[day];
    return ex ? ex : (weekendDays.has(day) ? {label:"Weekend", type:"holiday"} : null);
  };
  const cells = [];
  for (let i = 0; i < firstDay; i++) cells.push('<div class="aspect-square"></div>');
  for (let d = 1; d <= daysInMonth; d++) {
    const ev = eventFor(d);
    const isWeekend = weekendDays.has(d);
    // Weekends always stay red; an event placed on a weekend does not
    // override the weekend highlight.
    const tone = isWeekend
      ? "bg-red-100 text-red-700 rounded-full"
      : (ev ? (ev.type === "holiday" ? "bg-red-100 text-red-700 rounded-full" : "bg-blue-100 text-blue-700 rounded-full") : "text-ink/70");
    const title = ev ? ev.label : "Click to add an event";
    cells.push(`<div data-day="${d}" title="${title}" class="day-cell flex aspect-square cursor-pointer items-center justify-center rounded-lg text-sm ${tone} transition hover:bg-canary/20">`+d+`</div>`);
  }
  const combined = [];
  for (const d of weekendDays.keys()) combined.push({day:d, label:"Weekend", type:"holiday"});
  Object.entries(extra).forEach(([ds, ev]) => { const day = Number(ds); const idx = combined.findIndex(e => e.day === day); if (idx!=-1) combined.splice(idx,1); combined.push({day, label: ev.label, type: ev.type}); });
  combined.sort((a,b)=>a.day-b.day);
  const legendEvents = combined.filter(e => e.label !== "Weekend");
  let list = "";
  if (legendEvents.length) {
    list = `<ul class="mt-4 space-y-2 border-t border-ink/10 pt-4 text-sm">` + legendEvents.map(e => `
      <li class="flex items-start gap-3"><span class="mt-1.5 h-2 w-2 shrink-0 rounded-full ${e.type==="holiday"?"bg-red-500":"bg-blue-500"}"></span>
      <span><span class="font-mono text-xs uppercase tracking-widest text-ink-light">${e.day}</span><br/>${e.label}</span></li>`).join("") + `</ul>`;
  }
  return `<div class="rounded-3xl border-2 border-black bg-white p-6 shadow-xl"><h3 class="font-bold text-xl tracking-tight">${monthName}</h3>
    <div class="mt-3 grid grid-cols-7 text-[10px] font-bold text-ink-light mb-1 pl-1">${WEEKDAYS.map(d=>'<span class="w-6 h-6 flex items-center justify-center mx-auto">'+d+'</span>').join('')}</div>
    <div class="grid grid-cols-7 text-sm gap-y-1">${cells.join('')}</div>` + list + `</div>`;
}

const form = document.getElementById("month-form");
const out = document.getElementById("month");
const legend = document.getElementById("legend");
const editor = document.getElementById("editor");
const editorForm = document.getElementById("editor-form");
const editorDay = document.getElementById("editor-day");
const editorLabel = document.getElementById("editor-label");
const editorType = document.getElementById("editor-type");
const editorRemove = document.getElementById("editor-remove");
const editorCancel = document.getElementById("editor-cancel");
const createBtn = document.getElementById("create-calender");
const createBtnText = document.getElementById("create-calender-text");
const createBtnSpinner = document.getElementById("create-calender-spinner");
const saveMessage = document.getElementById("save-message");
let currentMonthId = null, currentEditDay = null;

function renderFromInputs() {
  const {name, days, start} = readFormValues();
  const idx = monthIndexFromName(name);
  currentMonthId = monthId(idx, name);
  out.innerHTML = renderMonth(name, days, start, mergeEvents(name));
  legend.classList.remove("hidden");
}
function getCookie(n) { const v = "; "+document.cookie; const p = v.split("; "+n+"="); return p.length===2 ? p.pop().split(";").shift() : null; }
function showSaveMessage(t, err) { saveMessage.textContent = t; saveMessage.className = "pt-2 text-center text-sm font-bold "+(err?"text-red-600":"text-green-700"); saveMessage.classList.remove("hidden"); }
function hideSaveMessage() { saveMessage.classList.add("hidden"); }

async function update_month() {
  const {name, days, start} = readFormValues();
  createBtn.disabled = true; createBtnText.textContent = "Updating..."; hideSaveMessage();
  const allEvents = mergeEvents(name);
  // Drop events outside the current day count so shrinking a month
  // (e.g. 31 -> 28) doesn't leave stale events on days 29-31.
  const inRange = {};
  for (const [day, ev] of Object.entries(allEvents)) {
    const d = Number(day);
    if (d >= 1 && d <= days) inRange[day] = ev;
  }
  if (EXTRA[currentMonthId]) {
    for (const k of Object.keys(EXTRA[currentMonthId])) {
      if (Number(k) < 1 || Number(k) > days) delete EXTRA[currentMonthId][k];
    }
    if (Object.keys(EXTRA[currentMonthId]).length === 0) delete EXTRA[currentMonthId];
  }
  saveExtras();
  const eventsList = Object.entries(inRange).map(([day, ev]) => ({event_date: Number(day), event_name: ev.label, event_type: ev.type}));
  try {
    const resp = await fetch(UPDATE_URL, {method:"POST", headers:{"Content-Type":"application/json","X-CSRFToken":getCookie("csrftoken")||""}, body:JSON.stringify({monthName:name, daysInMonth:days, startDay:start, events:eventsList})});
    const data = await resp.json();
    createBtn.disabled = false; createBtnText.textContent = "Update calendar"; createBtnSpinner.classList.add("hidden");
    if (data.success) { showSaveMessage(data.message, false); setTimeout(()=>location.reload(), 4700); } else { showSaveMessage("Error: "+data.message, true); }
  } catch (e) { console.error("Failed to save calendar:", e); createBtn.disabled = false; createBtnText.textContent = "Update calendar"; createBtnSpinner.classList.add("hidden"); showSaveMessage("Failed to save calendar.", true); }
}

function openEditor(day) { currentEditDay = day; editorDay.textContent = day; const {name} = readFormValues(); const s = SERVER_DATA.hasData && name===SERVER_DATA.monthName ? (SERVER_DATA.events||{}) : {}; const ex = EXTRA[currentMonthId]||{}; const existing = ex[day] || s[day]; editorLabel.value = existing ? existing.label : ""; editorType.value = existing ? existing.type : "event"; editorRemove.classList.toggle("hidden", !existing); editor.classList.remove("hidden"); editor.style.display = "flex"; editorLabel.focus(); }
function closeEditor() { editor.style.display = "none"; editor.classList.add("hidden"); currentEditDay = null; }
function saveEditor() { const label = editorLabel.value.trim(); if (!label) return; if (!EXTRA[currentMonthId]) EXTRA[currentMonthId] = {}; EXTRA[currentMonthId][currentEditDay] = {label, type: editorType.value}; saveExtras(); closeEditor(); renderFromInputs(); }
function removeEditor() { if (EXTRA[currentMonthId]) { delete EXTRA[currentMonthId][currentEditDay]; if (Object.keys(EXTRA[currentMonthId]).length === 0) delete EXTRA[currentMonthId]; } const {name} = readFormValues(); if (SERVER_DATA.hasData && name === SERVER_DATA.monthName && SERVER_DATA.events) delete SERVER_DATA.events[currentEditDay]; saveExtras(); closeEditor(); renderFromInputs(); }

if (SERVER_DATA.hasData) {
  document.getElementById("month-name").value = SERVER_DATA.monthName;
  document.getElementById("day-count").value = String(SERVER_DATA.daysInMonth);
  document.getElementById("start-day").value = String(SERVER_DATA.firstDay);
  document.getElementById("month-name").disabled = true;
  renderFromInputs();
}
form.addEventListener("submit", (e) => { e.preventDefault(); renderFromInputs(); });
createBtn.addEventListener("click", update_month);
out.addEventListener("click", (e) => { const cell = e.target.closest("[data-day]"); if (cell) openEditor(Number(cell.getAttribute("data-day"))); });
editorForm.addEventListener("submit", (e) => { e.preventDefault(); saveEditor(); });
editorRemove.addEventListener("click", removeEditor);
editorCancel.addEventListener("click", closeEditor);
editor.addEventListener("click", (e) => { if (e.target === editor) closeEditor(); });
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !editor.classList.contains("hidden")) closeEditor(); });

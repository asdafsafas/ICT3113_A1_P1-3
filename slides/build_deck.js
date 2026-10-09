const pptxgen = require("pptxgenjs");
const { applyTheme } = require("C:/Users/iikod/.claude/skills/synced/a9b550bf-9ea6-4b20-9351-1741b38019b3_70716eb3-0b9e-4213-924d-6a144a6c2af4/pptx/scripts/apply_theme.js");

const OUT = process.argv[2] || "Group03.pptx";

const THEME = {
  name: "Triage Ledger",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B2A30", lt1: "FFFFFF", dk2: "12343B", lt2: "EEF3F2",
    accent1: "0F6E6E", accent2: "D9962B", accent3: "2E7D4F", accent4: "B83A2E",
    accent5: "5F747B", accent6: "9BC1BC", hlink: "0F6E6E", folHlink: "5F747B",
  },
};
const HEX = THEME.colors;
const MODEL_HEX = { q05: "9BC1BC", l1: "5F747B", q7: "0F6E6E" };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Ticket Triage on CPU-only Hardware";
pres.author = "Group P1-3";
const C = pres.SchemeColor;

const W = 13.333, MX = 0.6, CW = W - 2 * MX;

// ---------- layouts ----------
pres.defineSlideMaster({
  title: "COVER",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: MX, y: 1.2, w: 7.6, h: 1.9, fontSize: 40, bold: true, color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: MX, y: 3.25, w: 7.4, h: 0.9, fontSize: 18, color: "CADDDA", valign: "top", align: "left", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background1 },
  margin: [0.5, 0.6, 0.6, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.35, w: CW, h: 0.85, fontSize: 30, bold: true, color: C.text2, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: "ICT3113 Assignment 1  ·  Group P1-3  ·  Ticket triage on CPU", options: { x: MX, y: 7.02, w: 8, h: 0.3, fontSize: 10, color: C.accent5, margin: 0 } } },
  ],
  slideNumber: { x: 12.2, y: 7.02, w: 0.55, h: 0.3, fontSize: 10, color: C.accent5, align: "right" },
});

// ---------- helpers ----------
const shadow = () => ({ type: "outer", color: "1B2A30", blur: 6, offset: 1.5, angle: 90, opacity: 0.12 });
function card(s, x, y, w, h, opts = {}) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, rectRadius: 0.08,
    fill: { color: opts.fill || C.background2 },
    line: opts.line ? { color: opts.line, width: 1 } : { type: "none" },
    shadow: opts.shadow ? shadow() : undefined,
    objectName: opts.name,
  });
}
function txt(s, text, x, y, w, h, o = {}) {
  s.addText(text, Object.assign({ x, y, w, h, isTextBox: true, fontSize: 14, color: C.text1, margin: 0, valign: "top" }, o));
}
function pill(s, label, ok, x, y, w = 0.85) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.3, rectRadius: 0.15, fill: { color: ok === null ? C.accent2 : ok ? C.accent3 : C.accent4 }, line: { type: "none" } });
  txt(s, label, x, y, w, 0.3, { fontSize: 11, bold: true, color: C.background1, align: "center", valign: "middle" });
}
function badge(s, n, x, y, d = 0.42, fill = C.accent1) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { type: "none" } });
  txt(s, String(n), x, y, d, d, { fontSize: 14, bold: true, color: C.background1, align: "center", valign: "middle" });
}
function bullets(items, o = {}) {
  return items.map((t, i) => {
    const runOpts = { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: o.gap ?? 4 };
    if (typeof t === "string") return { text: t, options: runOpts };
    return { text: t.text, options: Object.assign(runOpts, t.options || {}) };
  });
}
function arrow(s, x, y, w, h, color = C.accent5) {
  s.addShape(pres.shapes.LINE, { x, y, w, h, line: { color, width: 1.75, endArrowType: "triangle" } });
}
const H = (t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.text2 } } });
function content(section, title, notes) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  if (notes) s.addNotes(notes);
  return s;
}

// =====================================================================
// 1. Cover
pres.addSection({ title: "Introduction" });
{
  const s = pres.addSlide({ masterName: "COVER", sectionTitle: "Introduction" });
  s.addText("Ticket Triage on CPU-only Hardware: What to Deploy, and What We Can Promise", { placeholder: "title" });
  s.addText("Can an AI model running on a bank's own computers sort complaint tickets quickly and accurately enough? We tested three to find out.", { placeholder: "body" });

  txt(s, "GROUP P1-3  ·  TEAM 3  ·  DATA ROWS 3000–3999", MX, 4.45, 7.4, 0.3, { fontSize: 12, bold: true, color: HEX.accent6, charSpacing: 1 });
  const members = [["Chia ShuXian Natalie", "2403237"], ["Chng Zong Han", "2401892"], ["Kannan S/O Rajamohan", "2401517"], ["Muhammad Ridwan Putra Jasni", "2401684"], ["Tan Tze Han", "2301483"]];
  members.forEach(([n, id], i) => {
    const col = i < 3 ? 0 : 1, row = i < 3 ? i : i - 3;
    txt(s, [{ text: n, options: { bold: true, color: C.background1 } }, { text: "   " + id, options: { color: "CADDDA" } }], MX + col * 4.05, 4.85 + row * 0.38, 4.0, 0.34, { fontSize: 14 });
  });
  txt(s, [
    { text: "Repository (rebuild with docker compose up -d --build):  ", options: { color: "CADDDA" } },
    { text: "github.com/asdafsafas/ICT3113_A1_P1-3", options: { color: C.background1, bold: true, hyperlink: { url: "https://github.com/asdafsafas/ICT3113_A1_P1-3" } } },
  ], MX, 6.15, 9, 0.35, { fontSize: 13 });

  // headline stat panel
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.75, y: 1.2, w: 3.95, h: 4.6, rectRadius: 0.1, fill: { color: "1B4A50" }, line: { type: "none" } });
  txt(s, "RECOMMENDATION", 9.1, 1.5, 3.3, 0.3, { fontSize: 12, bold: true, color: HEX.accent6, charSpacing: 1 });
  txt(s, "qwen2.5:7b", 9.1, 1.85, 3.3, 0.5, { fontSize: 24, bold: true, color: C.background1, fontFace: "Cambria" });
  txt(s, "82.6%", 9.1, 2.45, 3.3, 1.0, { fontSize: 60, bold: true, color: C.accent2, fontFace: "Cambria" });
  txt(s, "sorted correctly (161 of 195 tickets)", 9.1, 3.45, 3.3, 0.3, { fontSize: 13, color: "CADDDA" });
  txt(s, "6.1 s", 9.1, 3.85, 3.3, 0.6, { fontSize: 32, bold: true, color: C.background1, fontFace: "Cambria" });
  txt(s, "95% of tickets sorted within this, in the busiest hour (target 30 s)", 9.1, 4.45, 3.3, 0.55, { fontSize: 13, color: "CADDDA" });
  txt(s, "Falls just short on one target: 66.7% of money-transfer tickets right (target 70%)", 9.1, 5.1, 3.3, 0.6, { fontSize: 12, italic: true, color: HEX.accent6 });
  s.addNotes("Cover. Headline figures: results/accuracy/comparison.md (82.6%), results/load/qwen2.5-7b/1.73rpm_s3.5_run*.jtl (p95 6.06 s mean of 3 runs).");
}

// =====================================================================
// 2. Architecture
pres.addSection({ title: "System and workload" });
{
  const s = content("System and workload", "Each ticket goes through one web service to one AI model",
    "Source: docs/architecture.md, docker-compose.yml, service/app/. Baseline settings from .env.example: OLLAMA_NUM_PARALLEL=1, uvicorn --workers 1.");
  // LG box
  card(s, MX, 1.75, 2.45, 2.4, { fill: C.background2 });
  txt(s, "TEST TRAFFIC", MX + 0.2, 1.9, 2.1, 0.3, { fontSize: 11, bold: true, color: C.accent1, charSpacing: 1 });
  txt(s, "Separate Mac", MX + 0.2, 2.2, 2.1, 0.35, { fontSize: 16, bold: true, color: C.text2 });
  txt(s, "Apache JMeter 5.6.3 [2] plays the bank: new complaints arriving, and staff searching past tickets", MX + 0.2, 2.6, 2.1, 1.4, { fontSize: 12, color: C.text1 });
  arrow(s, MX + 2.5, 2.95, 0.75, 0);
  txt(s, "HTTP, Wi-Fi", MX + 2.45, 2.55, 0.9, 0.3, { fontSize: 10, color: C.accent5, align: "center" });

  // SUT frame
  const sx = 3.9, sy = 1.45, sw = 4.25, sh = 5.3;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: sx, y: sy, w: sw, h: sh, rectRadius: 0.08, fill: { color: C.background1 }, line: { color: C.accent6, width: 1.25, dashType: "dash" } });
  txt(s, "THE SYSTEM WE TESTED · MacBook Pro M5", sx + 0.2, sy + 0.12, sw - 0.4, 0.3, { fontSize: 11, bold: true, color: C.accent1, charSpacing: 1 });
  // triage
  card(s, sx + 0.25, sy + 0.55, sw - 0.5, 1.15, { fill: C.text2 });
  txt(s, "Triage web service (FastAPI)", sx + 0.45, sy + 0.65, sw - 0.9, 0.35, { fontSize: 14, bold: true, color: C.background1 });
  txt(s, "Receives each ticket, waits for the model's answer, and logs every request", sx + 0.45, sy + 1.0, sw - 0.9, 0.6, { fontSize: 11, color: "CADDDA" });
  // ollama
  arrow(s, sx + 1.15, sy + 1.72, 0, 0.55);
  card(s, sx + 0.25, sy + 2.3, 2.95, 1.15, { fill: C.accent1 });
  txt(s, "AI model server (Ollama) [1]", sx + 0.45, sy + 2.4, 2.6, 0.35, { fontSize: 14, bold: true, color: C.background1 });
  txt(s, "Runs on the processor, no graphics card; one ticket at a time", sx + 0.45, sy + 2.75, 2.6, 0.6, { fontSize: 11, color: C.background1 });
  // sqlite + logs
  arrow(s, sx + 3.6, sy + 1.72, 0, 2.05);
  card(s, sx + 2.25, sy + 3.8, 1.75, 1.25, { fill: C.background2 });
  txt(s, "Database", sx + 2.4, sy + 3.9, 1.5, 0.3, { fontSize: 13, bold: true, color: C.text2 });
  txt(s, "Sorted tickets; starts empty each run", sx + 2.4, sy + 4.25, 1.5, 0.7, { fontSize: 11 });
  card(s, sx + 0.25, sy + 3.8, 1.75, 1.25, { fill: C.background2 });
  txt(s, "Request log", sx + 0.4, sy + 3.9, 1.5, 0.3, { fontSize: 13, bold: true, color: C.text2 });
  txt(s, "One line per request, kept as evidence", sx + 0.4, sy + 4.25, 1.5, 0.7, { fontSize: 11 });

  // endpoints
  const ex = 8.55, ew = W - MX - ex;
  txt(s, "What the service offers", ex, 1.45, ew, 0.4, { fontSize: 18, bold: true, color: C.text2, fontFace: "Cambria" });
  const eps = [
    ["POST /tickets", "Send in one complaint; the model picks 1 of 7 categories; the ticket is saved and its category returned"],
    ["GET /search?q=", "Find saved tickets that contain a word, newest first"],
    ["GET /stats", "How many saved tickets are in each category"],
  ];
  eps.forEach(([e, d], i) => {
    const y = 1.95 + i * 0.95;
    card(s, ex, y, ew, 0.82, { fill: C.background2 });
    txt(s, e, ex + 0.15, y + 0.08, ew - 0.3, 0.3, { fontSize: 13, bold: true, color: C.accent1, fontFace: "Courier New" });
    txt(s, d, ex + 0.15, y + 0.38, ew - 0.3, 0.42, { fontSize: 11 });
  });
  txt(s, "Kept deliberately simple", ex, 4.85, ew, 0.35, { fontSize: 16, bold: true, color: C.text2, fontFace: "Cambria" });
  s.addText(bullets([
    "The sender waits until the model has answered",
    "No shortcuts: a repeated ticket is sorted again",
    "No waiting line in our code; the model server has its own",
    "Search reads through every saved ticket (no index)",
  ], { gap: 3 }), { x: ex, y: 5.25, w: ew, h: 1.55, isTextBox: true, fontSize: 12, color: C.text1, margin: 0, valign: "top" });
}

// =====================================================================
// 3. Workload model
{
  const s = content("System and workload", "The desk peaks at 1.73 tickets per minute, all in business hours",
    "Source: planning/workload-model.md. Ticket lengths reproduced with python scripts/ticket_lengths.py over rows 3000-3999.");
  const stats = [
    ["86,719", "complaints in 6 months at a large UK bank (Bank of Scotland, Jul–Dec 2025)", "SOURCED [3]"],
    ["≈ 694", "per working day: 86,719 × 2 = 173,438 a year, ÷ 250 working days", "EST. FROM [4]"],
    ["1.45/min", "on average: 694 spread over an 8-hour working day", "ESTIMATED"],
    ["1.73/min", "in the busiest hour, which gets 15% of the day (104 tickets)", "EST. FROM [5], [6]"],
  ];
  const cw = 1.75, gap = 0.12;
  stats.forEach(([n, l, tag], i) => {
    const x = MX + i * (cw + gap);
    card(s, x, 1.45, cw, 2.05, { fill: i === 3 ? C.text2 : C.background2 });
    const fg = i === 3 ? C.background1 : C.text2;
    txt(s, n, x + 0.15, 1.58, cw - 0.3, 0.55, { fontSize: 22, bold: true, color: fg, fontFace: "Cambria" });
    txt(s, l, x + 0.15, 2.15, cw - 0.3, 0.95, { fontSize: 11, color: i === 3 ? "CADDDA" : C.text1 });
    txt(s, tag, x + 0.15, 3.12, cw - 0.3, 0.25, { fontSize: 10, bold: true, color: i === 3 ? HEX.accent6 : C.accent1 });
  });

  // load levels table
  txt(s, "Traffic levels we tested", MX, 3.75, 7.4, 0.35, { fontSize: 15, bold: true, color: C.text2, fontFace: "Cambria" });
  const rows = [
    [H("Level"), H("Tickets /min"), H("Searches /min"), H("Why")],
    ["Average", "1.45", "2.9", "A normal hour"],
    [{ text: "Peak", options: { bold: true } }, { text: "1.73", options: { bold: true } }, { text: "3.5", options: { bold: true } }, { text: "Busiest hour: targets must be met here", options: { bold: true } }],
    ["Beyond peak", "3.5", "7", "Double the peak: room for busy seasons"],
  ];
  s.addTable(rows, { x: MX, y: 4.15, w: 7.35, colW: [1.45, 1.35, 1.45, 3.1], fontSize: 12, color: C.text1, border: { type: "solid", pt: 0.75, color: "D5DFDD" }, rowH: 0.36, valign: "middle" });
  s.addText(bullets([
    "Searches: we assume staff search twice per ticket (the customer's past complaints, similar cases). An estimate: no published figure exists",
    "We count phone complaints as tickets too, and move out-of-hours ones into office hours. Both make our test harder than reality [7]",
  ], { gap: 3 }), { x: MX, y: 5.75, w: 7.35, h: 1.1, isTextBox: true, fontSize: 12, color: C.text1, margin: 0, valign: "top" });

  // ticket length chart
  const chx = 8.3, chw = W - MX - chx;
  s.addChart(pres.charts.BAR, [{ name: "Characters", labels: ["5%", "25%", "50%", "75%", "95%", "99%", "Longest"], values: [263, 512, 797, 1214, 1780, 1938, 2000] }], {
    x: chx, y: 1.4, w: chw, h: 3.75, barDir: "col",
    chartColors: [HEX.accent1], showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10, dataLabelColor: HEX.dk1, dataLabelFontFace: "+mn-lt",
    showTitle: true, title: "Ticket length in characters (our 1,000) [8]", titleFontSize: 13, titleColor: HEX.dk2, titleFontFace: "+mn-lt",
    catAxisLabelColor: HEX.accent5, valAxisLabelColor: HEX.accent5, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", catAxisLabelFontSize: 11, valAxisLabelFontSize: 10,
    valGridLine: { color: "E2E8E7", size: 0.5 }, catGridLine: { style: "none" }, showLegend: false, valAxisMaxVal: 2400, valAxisMinVal: 0,
  });
  s.addText(bullets([
    "Each bar is the length that share of tickets stays under: half are under 797 characters (~144 words), 95% under 1,780",
    "Even the longest (2,000 characters) plus our instructions fits in what the model reads at once, so no ticket is cut short",
  ], { gap: 3 }), { x: chx, y: 5.3, w: chw, h: 1.5, isTextBox: true, fontSize: 12, color: C.text1, margin: 0, valign: "top" });
}

// =====================================================================
// 4. Requirements
pres.addSection({ title: "Requirements and candidates" });
{
  const s = content("Requirements and candidates", "As accurate as a trained human, fast enough for the peak",
    "Source: planning/requirements.md (frozen with tag prediction-freeze).");
  card(s, MX, 1.4, CW, 0.9, { fill: C.text2 });
  txt(s, [
    { text: "Our position: ", options: { bold: true, color: C.accent2 } },
    { text: "sending a ticket to the wrong team costs more than sorting it slowly. A wrong ticket must be spotted, re-read and passed on by another team. Waiting 30 seconds instead of 5 makes no difference to a complaint a person answers over hours or days.", options: { color: C.background1 } },
  ], MX + 0.25, 1.45, CW - 0.5, 0.8, { fontSize: 13, valign: "middle" });

  const R = (id) => ({ text: id, options: { bold: true, color: C.accent1 } });
  const rows = [
    [H("ID"), H("Target"), H("Tested under"), H("Why this number")],
    [R("R1"), "95% of tickets sorted within 30 s", "Busiest hour: 1.73 tickets/min for 10 min, 3 runs", "At peak a ticket arrives about every 35 s. Sorting slower than that means tickets pile up"],
    [R("R2"), "95% of searches answered within 1 s", "Busiest hour plus 3.5 searches/min, 10 min", "Staff wait at the screen; about 1 s keeps their train of thought [9]"],
    [R("R3"), "Keeps up: ≥ 104 tickets sorted an hour, ≤ 1% failures, delays not growing", "Busiest hour, 10 min, 3 runs", "104 is the busiest hour's volume; sorting fewer means a growing backlog"],
    [R("R4"), "At least 80% of tickets sorted correctly", "Our 195 hand-checked tickets, once each", "Our own team agreed with each other on 78–85% of tickets: the model should do as well as one trained person"],
    [R("R5"), "At least 70% correct in every category", "Each category of the 195", "Small categories have only 17–18 tickets, so one wrong ticket costs ~6 points. A lower bar avoids failing a model over 1–2 tickets"],
  ];
  s.addTable(rows, { x: MX, y: 2.5, w: CW, colW: [0.6, 3.55, 3.1, 4.88], fontSize: 12, color: C.text1, border: { type: "solid", pt: 0.75, color: "D5DFDD" }, valign: "middle", rowH: [0.36, 0.66, 0.66, 0.66, 0.66, 0.66] });
  card(s, MX, 6.35, CW, 0.5, { fill: C.background2 });
  txt(s, [
    { text: "Client rules.  C1: ", options: { bold: true, color: C.text2 } },
    { text: "the model runs on the bank's own computers, without graphics cards; no outside AI service.   " },
    { text: "C2: ", options: { bold: true, color: C.text2 } },
    { text: "the model's licence must allow commercial use." },
  ], MX + 0.25, 6.35, CW - 0.5, 0.5, { fontSize: 12, valign: "middle" });
}

// =====================================================================
// 5. Candidate models
{
  const s = content("Requirements and candidates", "We tested three models, from small and fast to 15 times larger",
    "Source: models/models.lock.json, docs/models.md.");
  const cands = [
    ["SMALL", "qwen2.5:0.5b", "0.5 billion parameters · 398 MB", "Apache 2.0 [11]", "Fastest. Same maker as the large one [10], so only size differs", MODEL_HEX.q05],
    ["SMALL", "llama3.2:1b-instruct-q4_K_M", "1.2 billion parameters · 808 MB", "Llama 3.2 Community [12]", "A small model from a different maker: does how it was trained matter as much as size?", MODEL_HEX.l1],
    ["LARGE", "qwen2.5:7b", "7.6 billion parameters · 4.7 GB", "Apache 2.0 [11]", "The largest that fits our test machine's memory; expected to be most accurate", MODEL_HEX.q7],
  ];
  const cw = (CW - 2 * 0.3) / 3;
  cands.forEach(([cls, tag, spec, lic, role, col], i) => {
    const x = MX + i * (cw + 0.3);
    card(s, x, 1.45, cw, 2.75, { fill: C.background2 });
    s.addShape(pres.shapes.OVAL, { x: x + 0.25, y: 1.65, w: 0.32, h: 0.32, fill: { color: col }, line: { type: "none" } });
    txt(s, cls, x + 0.7, 1.67, cw - 0.9, 0.3, { fontSize: 11, bold: true, color: C.accent1, charSpacing: 1, valign: "middle" });
    txt(s, tag, x + 0.25, 2.1, cw - 0.5, 0.4, { fontSize: 13, bold: true, color: C.text2, fontFace: "Courier New" });
    txt(s, spec, x + 0.25, 2.55, cw - 0.5, 0.3, { fontSize: 12 });
    txt(s, [{ text: "Licence: ", options: { bold: true } }, { text: lic }], x + 0.25, 2.88, cw - 0.5, 0.3, { fontSize: 12 });
    txt(s, role, x + 0.25, 3.25, cw - 0.5, 0.85, { fontSize: 12, italic: true, color: C.accent5 });
  });
  txt(s, "Exact versions tested: each model's unique fingerprint (digest), checked before every test session", MX, 4.45, CW, 0.3, { fontSize: 13, bold: true, color: C.text2 });
  const mono = (t) => ({ text: t, options: { fontFace: "Courier New", fontSize: 10.5 } });
  s.addTable([
    [H("Tag"), H("Digest")],
    [mono("qwen2.5:0.5b"), mono("a8b0c51577010a279d933d14c2a8ab4b268079d44c5c8830c0a93900f1827c67")],
    [mono("llama3.2:1b-instruct-q4_K_M"), mono("22bc6b92eb0160c4629782fca05a9032c59d306ab2058b7dacc8a4644fbafa02")],
    [mono("qwen2.5:7b"), mono("845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e")],
    [mono("ollama/ollama:0.35.1 (image)"), mono("sha256:292ee7945dfc3d5840a181f3ab86fedb1e66703e02c8af98b50f4da56b7e278c")],
  ], { x: MX, y: 4.8, w: CW, colW: [3.6, 8.53], fontSize: 11, color: C.text1, border: { type: "solid", pt: 0.75, color: "D5DFDD" }, rowH: 0.3, valign: "middle" });
  txt(s, "All three are compressed the same way (Q4_K_M), so size is the only difference.", MX, 6.4, CW, 0.5, { fontSize: 12, italic: true, color: C.accent5 });
}

// =====================================================================
// 6. Golden set
pres.addSection({ title: "Golden set and testing" });
{
  const s = content("Golden set and testing", "195 tickets labelled twice by hand, then locked",
    "Sources: golden/PROTOCOL.md, golden/agreement_summary.md, golden/SUMMARY.md, golden/pairs/*.csv. Label sheets committed in 39d4cc2; golden set frozen in 653a98e; tag prediction-freeze 2026-10-06 15:36 SGT; first official benchmark run 17:13 SGT the same day.");
  const st = [
    ["κ = 0.735", "Group A agreement (2 people)", "Cohen's kappa: 0 = chance, 1 = perfect. Same label on 78% of tickets"],
    ["κ = 0.778", "Group B agreement (3 people)", "Fleiss' kappa. Both groups count as substantial agreement"],
    ["49", "disagreements, each discussed", "44 settled on a category · 5 dropped: no product named"],
  ];
  const cw = (CW - 0.6) / 3;
  st.forEach(([n, a, b], i) => {
    const x = MX + i * (cw + 0.3);
    card(s, x, 1.4, cw, 1.45, { fill: C.background2 });
    txt(s, n, x + 0.25, 1.5, cw - 0.5, 0.6, { fontSize: 28, bold: true, color: C.text2, fontFace: "Cambria" });
    txt(s, a, x + 0.25, 2.08, cw - 0.5, 0.3, { fontSize: 13, bold: true, color: C.accent1 });
    txt(s, b, x + 0.25, 2.38, cw - 0.5, 0.4, { fontSize: 11 });
  });

  // protocol timeline
  txt(s, "How our labelling rules changed", MX, 3.05, 4, 0.35, { fontSize: 15, bold: true, color: C.text2, fontFace: "Cambria" });
  const tl = [
    ["v0.1", "First rules: a definition per category; if unsure, pick the product the complaint is mainly about"],
    ["v0.2", "After 16 disputed tickets: credit report vs debt collector decided by who the complaint is against; student loans count as Consumer loan"],
    ["v0.3", "After 12 more: prepaid cards and crypto count as Money transfer; scams go with where the money left from; when to drop a ticket"],
  ];
  const tw = (CW - 0.6) / 3;
  s.addShape(pres.shapes.LINE, { x: MX + 0.2, y: 3.71, w: CW - 0.4, h: 0, line: { color: C.accent6, width: 2 } });
  tl.forEach(([v, d], i) => {
    const x = MX + i * (tw + 0.3);
    badge(s, v, x, 3.5, 0.42, i === 0 ? C.accent5 : C.accent1);
    txt(s, d, x, 4.02, tw - 0.1, 0.9, { fontSize: 11 });
  });

  // examples
  const exs = [
    ["Same problem, two answers (tickets 3025 and 3072)", "Both are about a debt showing on a credit report. 3025 asks the credit agency (TransUnion) to remove it → Credit reporting. 3072 says the debt collector (Midland) never proved the debt → Debt collection."],
    ["A rule overruling the majority (ticket 3141)", "2 of 3 labellers chose Credit reporting: the person wants a car repossession off their report. But they are asking the car lender (Ally Financial), not a credit agency, so the rule makes it Consumer loan."],
  ];
  const ew = (CW - 0.3) / 2;
  exs.forEach(([h, b], i) => {
    const x = MX + i * (ew + 0.3);
    card(s, x, 5.05, ew, 1.8, { fill: C.background1, line: "D5DFDD" });
    txt(s, h, x + 0.25, 5.15, ew - 0.5, 0.35, { fontSize: 13, bold: true, color: C.accent1 });
    txt(s, b, x + 0.25, 5.52, ew - 0.5, 1.25, { fontSize: 12 });
  });
}

// =====================================================================
// 7. Test environment
{
  const s = content("Golden set and testing", "Our test set-up, and how it carries over to the bank",
    "Sources: evidence/smoke-prototype/env/service_machine.txt (SUT), results/load/*/..._jmeter.log (LG: os.name, java.version, JMeter version), service logs for search latency, *_stats.csv for docker stats.");
  const mw = (CW - 1.0) / 2;
  card(s, MX, 1.4, mw, 2.95, { fill: C.text2 });
  txt(s, "MACHINE RUNNING THE SYSTEM", MX + 0.25, 1.52, mw - 0.5, 0.3, { fontSize: 11, bold: true, color: HEX.accent6, charSpacing: 1 });
  s.addText(bullets([
    "MacBook Pro, Apple M5 chip, 10 cores, 16 GB memory",
    "macOS 26.6.2; Docker 29.8.2 given 10 cores and 9.7 GiB",
    "Ollama 0.35.1, processor only (no graphics card)",
    "One ticket at a time; fixed settings so answers repeat exactly",
  ], { gap: 4 }), { x: MX + 0.25, y: 1.9, w: mw - 0.5, h: 2.35, isTextBox: true, fontSize: 13, color: C.background1, margin: 0, valign: "top" });

  const lx = MX + mw + 1.0;
  arrow(s, MX + mw + 0.1, 2.85, 0.8, 0, C.accent1);
  txt(s, "phone hotspot", MX + mw + 0.02, 2.45, 0.96, 0.3, { fontSize: 10, color: C.accent5, align: "center" });
  card(s, lx, 1.4, mw, 2.95, { fill: C.background2 });
  txt(s, "MACHINE SENDING TEST TRAFFIC", lx + 0.25, 1.52, mw - 0.5, 0.3, { fontSize: 11, bold: true, color: C.accent1, charSpacing: 1 });
  s.addText(bullets([
    "A second Mac (Ridwan's), macOS 26.5",
    "Apache JMeter 5.6.3 (Java 17.0.17), run without its on-screen interface",
    "Connects over Wi-Fi to the system at 172.20.10.2",
    "Proof it is separate: a different macOS version, and every JMeter log points at the other machine",
  ], { gap: 4 }), { x: lx + 0.25, y: 1.9, w: mw - 0.5, h: 2.35, isTextBox: true, fontSize: 13, color: C.text1, margin: 0, valign: "top" });

  const bw = (CW - 0.3) / 2;
  txt(s, "How results carry over to the bank's servers", MX, 4.6, bw, 0.35, { fontSize: 15, bold: true, color: C.text2, fontFace: "Cambria" });
  s.addText(bullets([
    "82–89% of the model's time goes on reading the ticket, so speed depends mostly on the server's processor and memory",
    "Stress check: the limit lies between 20 and 24 tickets/min (with 7 searches/min)",
    "Our estimate: a server up to 3× slower would still meet the 30 s target. Time one ticket on the bank's server first",
  ], { gap: 4 }), { x: MX, y: 5.0, w: bw, h: 1.9, isTextBox: true, fontSize: 12, color: C.text1, margin: 0, valign: "top" });
  txt(s, "What could make our numbers misleading", MX + bw + 0.3, 4.6, bw, 0.35, { fontSize: 15, bold: true, color: C.text2, fontFace: "Cambria" });
  s.addText(bullets([
    "A laptop chip is not a typical bank server chip; laptops slow down when hot; power source was not recorded",
    "Wi-Fi: a search takes under 7 ms inside the system but 0.2–0.5 s as JMeter sees it, so most of that is network",
    "Standard load runs have only 14–35 tickets each, so p99 is just the slowest ticket",
  ], { gap: 4 }), { x: MX + bw + 0.3, y: 5.0, w: bw, h: 1.9, isTextBox: true, fontSize: 12, color: C.text1, margin: 0, valign: "top" });
  s.addNotes("Adaptive stress evidence: results/load/qwen2.5-7b/adaptive-stress/adaptive-stress-summary.json and matching JTL files. At 20/min one 10-minute attempt sustained the offered load. At 22/min one attempt overloaded and one sustained. At 24/min two independent attempts met the predeclared overload rule. These short tests do not establish a production SLA or a reliable 22/min operating rate.");
}

// =====================================================================
// 8. Playbook
{
  const s = content("Golden set and testing", "Every test run follows the same six steps",
    "Full step-by-step playbook: docs/actual-jmeter-test.md and docs/load-testing.md. Runners: scripts/run_official_jmeter_suite.py, scripts/run_7b_stress_suite.py, scripts/run_accuracy_suite.py. Reconciliation: scripts/reconcile.py. Summary: scripts/summarise_jtl.py.");
  const steps = [
    ["Reset", "Restart the model server, empty the database, check the right model is loaded"],
    ["Warm up", "Send one made-up ticket to load the model, then empty the database again"],
    ["Monitor", "Record processor and memory use every 5 s"],
    ["Load", "JMeter sends traffic from the separate Mac"],
    ["Collect", "Save JMeter results, service log and resource log"],
    ["Reconcile", "Check every request appears in both logs, and nothing else does"],
  ];
  const sw = (CW - 5 * 0.2) / 6;
  steps.forEach(([h, d], i) => {
    const x = MX + i * (sw + 0.2);
    card(s, x, 1.4, sw, 1.75, { fill: i === 3 ? C.text2 : C.background2 });
    badge(s, i + 1, x + 0.15, 1.52, 0.4, i === 3 ? C.accent2 : C.accent1);
    txt(s, h, x + 0.65, 1.55, sw - 0.75, 0.35, { fontSize: 14, bold: true, color: i === 3 ? C.background1 : C.text2, valign: "middle" });
    txt(s, d, x + 0.15, 2.05, sw - 0.3, 1.05, { fontSize: 11, color: i === 3 ? C.background1 : C.text1 });
    if (i < 5) arrow(s, x + sw + 0.01, 2.27, 0.18, 0, C.accent6);
  });

  const tw = (CW - 0.6) / 3, ty = 3.4, th = 3.45;
  const tests = [
    ["Load tests: 27 runs", [
      "Tickets arrive at random moments at a set average rate, even if the system falls behind, so any backlog shows",
      "3 models × 3 traffic levels (normal, busiest, double) × 3 runs each",
      "10 min of traffic, then 5 min for the last tickets to finish; over 10 min counts as failed",
      "Tickets from rows 3200–3999, never the hand-checked ones; each request tagged with an ID",
    ]],
    ["Accuracy test: 3 passes", [
      "Each of the 195 hand-checked tickets sent once, one at a time, to each model",
      "Compared with our labels: overall, per category, and which categories get mixed up",
      "Run on 8 Oct, after the labels were locked; no other test running",
    ]],
    ["Stress test: large model", [
      "After a 3.5→12/min ramp, steady rates from 12 to 24 tickets/min in steps of 2, plus 7 searches/min; repeat any overload",
      "Each new attempt: 10 min of traffic, 10 min to drain, with the same reset and warm-up",
      "Overload: failures >1%, ≥15% still in flight, or a growing queue with slower completions or rising latency",
      "Check queue size at 5 and 10 min, early vs late latency, throughput, failures and processor use",
    ]],
  ];
  tests.forEach(([h, items], i) => {
    const x = MX + i * (tw + 0.3);
    card(s, x, ty, tw, th, { fill: C.background1, line: "D5DFDD" });
    txt(s, h, x + 0.25, ty + 0.15, tw - 0.5, 0.35, { fontSize: 15, bold: true, color: C.accent1, fontFace: "Cambria" });
    s.addText(bullets(items, { gap: 4 }), { x: x + 0.25, y: ty + 0.6, w: tw - 0.5, h: th - 0.75, isTextBox: true, fontSize: 12, color: C.text1, margin: 0, valign: "top" });
  });
  s.addNotes("Final stress procedure: docs/adaptive-stress-test.md and scripts/run_adaptive_stress.py. Final sequence 20, 22, 24 POST/min plus 7 searches/min. Each stage 10 active minutes, 10 drain minutes, reset and invented warm-up. Overload rules: errors >1%; end backlog >= max(5, ceil(15% of POST count)); growing backlog plus last-half completion throughput <90% offered; or growing backlog plus late-half p50 >=1.5 times early-half p50 with >=2 seconds absolute increase. Repeat an overload signal. Earlier adaptive_14rpm_s7_run1 had connection/socket timeouts and is excluded from the final capacity conclusion.");
}

// =====================================================================
// 9. Load & stress results
pres.addSection({ title: "Results and recommendation" });
{
  const s = content("Results and recommendation", "All three models keep up easily; the AI model is the slow part",
    "Source: python scripts/summarise_jtl.py results/load (POST /tickets) and --label \"GET /search\". Values are mean (min–max) over 3 runs; no warm-up skip. Error rate 0.0% in all 27 runs: 0 of 594 POSTs, 0 of 1,206 searches. Ollama queue wait from service logs: ollama_total_ms − prompt_eval_ms − eval_ms. CPU from *_stats.csv.");
  const g = (t) => ({ text: t, options: { color: C.accent5 } });
  const M = (t, n) => ({ text: t, options: { rowspan: n, bold: true, color: C.text2, valign: "middle" } });
  const pk = (t) => ({ text: t, options: { bold: true, fill: { color: "E3EEEC" } } });
  const rows = [
    [H("Model"), H("Tickets + searches /min"), H("Typical (p50) s"), H("95% within (p95) s"), H("99% (p99) s"), H("Done /min"), H("Failed"), H("Search 95% within s")],
    [M("qwen2.5:0.5b", 3), "1.45 + 2.9", "0.77 (0.65–0.84)", "1.95 (1.19–3.33)", "1.95", "1.62", "0%", "0.36"],
    [pk("1.73 + 3.5"), pk("0.67 (0.63–0.69)"), pk("1.02 (1.00–1.04)"), pk("1.02"), pk("2.02"), pk("0%"), pk("0.33")],
    ["3.5 + 7", "0.68 (0.60–0.81)", "1.27 (1.16–1.40)", "1.65", "3.69", "0%", "0.49"],
    [M("llama3.2:1b", 3), "1.45 + 2.9", "0.76 (0.66–0.93)", "1.46 (1.19–1.70)", "1.46", "1.63", "0%", "0.56"],
    [pk("1.73 + 3.5"), pk("0.72 (0.63–0.79)"), pk("1.74 (1.07–2.88)"), pk("1.74"), pk("1.82"), pk("0%"), pk("0.33")],
    ["3.5 + 7", "0.86 (0.79–0.97)", "1.41 (1.08–1.69)", "1.69", "3.71", "0%", "0.56"],
    [M("qwen2.5:7b", 3), "1.45 + 2.9", "3.38 (3.07–3.91)", "6.60 (5.55–8.37)", "6.60", "1.62", "0%", "0.22"],
    [pk("1.73 + 3.5"), pk("3.74 (3.69–3.78)"), pk("6.06 (5.55–6.71)"), pk("6.06"), pk("1.90"), pk("0%"), pk("0.46")],
    ["3.5 + 7", "3.54 (3.16–3.99)", "6.71 (6.09–7.13)", "8.51", "3.64", "0%", "0.35"],
  ];
  const tw = 8.7;
  s.addTable(rows, { x: MX, y: 1.4, w: tw, colW: [1.3, 1.05, 1.5, 1.5, 0.7, 0.85, 0.6, 1.2], fontSize: 11, color: C.text1, border: { type: "solid", pt: 0.75, color: "D5DFDD" }, rowH: [0.62, 0.34, 0.34, 0.34, 0.34, 0.34, 0.34, 0.34, 0.34, 0.34], valign: "middle", align: "left" });
  txt(s, "Seconds to sort a ticket: average of 3 runs (lowest–highest). Shaded = busiest hour, where targets R1–R3 apply.", MX, 5.15, tw, 0.3, { fontSize: 10, italic: true, color: C.accent5 });

  // verdict strip
  const vy = 5.6;
  [["R1", "95% of tickets sorted within 6.1 s at worst (target 30 s)"], ["R2", "95% of searches within 0.46 s at worst (target 1 s)"], ["R3", "No failures in 27 runs; tickets sorted as fast as they arrived"]].forEach(([r, t], i) => {
    const x = MX + i * 2.95;
    card(s, x, vy, 2.8, 1.25, { fill: C.background2 });
    pill(s, r + " PASS", true, x + 0.2, vy + 0.15, 1.05);
    txt(s, "All 3 models", x + 1.35, vy + 0.15, 1.3, 0.3, { fontSize: 11, bold: true, color: C.accent3, valign: "middle" });
    txt(s, t, x + 0.2, vy + 0.55, 2.45, 0.65, { fontSize: 11 });
  });

  // Final adaptive stress: 20/min sustained, 22/min mixed, 24/min overloaded twice.
  // Raw evidence: results/load/qwen2.5-7b/adaptive-stress/
  // stress panel
  const px = MX + tw + 0.3, pw = W - MX - px;
  card(s, px, 1.4, pw, 5.45, { fill: C.text2 });
  txt(s, "STRESS TEST · large model", px + 0.2, 1.52, pw - 0.4, 0.3, { fontSize: 11, bold: true, color: HEX.accent6, charSpacing: 1 });
  const sr = [["20 /min: sustained", "200 tickets · p95 21.8 s"], ["22 /min: mixed (2 attempts)", "p95 31.9 / 44.0 s"], ["24 /min: overloaded twice", "p95 53.8 / 71.7 s"]];
  sr.forEach(([a, b], i) => {
    const y = 1.92 + i * 0.6;
    txt(s, a, px + 0.2, y, pw - 0.4, 0.27, { fontSize: 12, bold: true, color: C.background1 });
    txt(s, b + " · 0 failed", px + 0.2, y + 0.27, pw - 0.4, 0.27, { fontSize: 11, color: "CADDDA" });
  });
  txt(s, "Limit: 20–24 /min", px + 0.2, 3.85, pw - 0.4, 0.35, { fontSize: 14, bold: true, color: C.accent2, fontFace: "Cambria" });
  txt(s, "Earlier runs from 3.5 to 18 /min all kept up; one 14 /min attempt had 3 tickets fail on Wi-Fi timeouts and was repeated cleanly. At 24 /min the queue grew in both attempts (15→24, 13→27).", px + 0.2, 4.22, pw - 0.4, 0.95, { fontSize: 11, color: C.background1 });
  txt(s, "Slow part: the AI model", px + 0.2, 5.3, pw - 0.4, 0.35, { fontSize: 14, bold: true, color: C.accent2, fontFace: "Cambria" });
  txt(s, "At 24/min, late-half completions were 23.0 and 22.8/min, below arrivals. Model CPU p95 was about 10 cores; service CPU p95 stayed below 1% of one core.", px + 0.2, 5.67, pw - 0.4, 1.1, { fontSize: 11, color: C.background1 });
  s.addNotes("Final stress source: results/load/qwen2.5-7b/adaptive-stress/adaptive-stress-summary.json. Independently recomputed from the five final JTLs and reconciled with per-run service logs. All five final attempts have zero POST failures. POST p50/p95/p99 in seconds: 20 run1 9.051/21.831/25.274; 22 run1 16.207/31.897/38.468; 22 run2 25.334/43.972/46.545; 24 run1 26.617/53.816/64.126; 24 run2 34.011/71.663/75.021. Last-half successful completions/min: 20.8, 21.6, 22.4, 23.0, 22.8. Backlog midpoint/end: 1/4, 8/12, 10/7, 15/24, 13/27. At 22/min outcomes were mixed; do not promise reliable sustained capacity there. At 24/min backlog and late-half latency grew in both independent attempts. Ollama CPU p95 1008.62%/1013.85%, triage p95 0.81%/0.87%. Stats summaries include monitoring/drain, so CPU p95 is supporting evidence, not proof of continuous saturation. The earlier 14/min first attempt had timeouts and is not included in this final conclusion.");
}

// =====================================================================
// 10. Accuracy results
{
  const s = content("Results and recommendation", "Only the large model sorts well, and it misses one category",
    "Source: results/accuracy/comparison.md and per-run reports results/accuracy/20261008T*.md (confusion matrices). Run 8 Oct 2026, prompt classify_v1.txt, after the freeze.");
  const cats = ["Credit reporting (42)", "Debt collection (17)", "Mortgage (27)", "Credit card (18)", "Bank account (37)", "Consumer loan (24)", "Money transfer (30)"];
  const chw = 7.9;
  s.addChart([
    { type: pres.charts.BAR, data: [
      { name: "qwen2.5:0.5b", labels: cats, values: [40.5, 0, 0, 94.4, 2.7, 0, 0] },
      { name: "llama3.2:1b", labels: cats, values: [85.7, 58.8, 29.6, 16.7, 16.2, 0, 3.3] },
      { name: "qwen2.5:7b", labels: cats, values: [81.0, 82.4, 92.6, 88.9, 94.6, 70.8, 66.7] },
    ], options: { barDir: "col", barGapWidthPct: 60, chartColors: [MODEL_HEX.q05, MODEL_HEX.l1, MODEL_HEX.q7] } },
    { type: pres.charts.LINE, data: [{ name: "R5 target (70%)", labels: cats, values: [70, 70, 70, 70, 70, 70, 70] }], options: { chartColors: [HEX.accent4], lineSize: 1.5, lineDataSymbol: "none", lineDash: "dash" } },
  ], {
    x: MX, y: 1.35, w: chw, h: 5.5,
    showTitle: true, title: "Share of each category sorted correctly (%); number of tickets in brackets", titleFontSize: 13, titleColor: HEX.dk2, titleFontFace: "+mn-lt",
    showLegend: true, legendPos: "b", legendFontSize: 11, legendFontFace: "+mn-lt", legendColor: HEX.dk1,
    catAxisLabelColor: HEX.accent5, valAxisLabelColor: HEX.accent5, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", catAxisLabelFontSize: 10, valAxisLabelFontSize: 10,
    valAxisMaxVal: 100, valAxisMinVal: 0, valGridLine: { color: "E2E8E7", size: 0.5 }, catGridLine: { style: "none" },
  });

  const px = MX + chw + 0.35, pw = W - MX - px;
  const ov = [["qwen2.5:0.5b", "17.9%", false, false], ["llama3.2:1b", "32.8%", false, false], ["qwen2.5:7b", "82.6%", true, false]];
  ov.forEach(([m, v, r4, r5], i) => {
    const y = 1.4 + i * 0.82;
    card(s, px, y, pw, 0.7, { fill: i === 2 ? C.text2 : C.background2 });
    txt(s, m, px + 0.15, y, 1.3, 0.7, { fontSize: 11, bold: true, color: i === 2 ? C.background1 : C.text2, valign: "middle" });
    txt(s, v, px + 1.35, y, 1.1, 0.7, { fontSize: 20, bold: true, color: i === 2 ? C.accent2 : C.text2, fontFace: "Cambria", valign: "middle" });
    pill(s, r4 ? "R4 ✓" : "R4 ✗", r4, px + 2.48, y + 0.2, 0.62);
    pill(s, "R5 ✗", r5, px + 3.15, y + 0.2, 0.62);
  });
  txt(s, "Where each model goes wrong", px, 3.95, pw, 0.35, { fontSize: 15, bold: true, color: C.text2, fontFace: "Cambria" });
  s.addText(bullets([
    { text: "Small Qwen puts 155 of 195 tickets (79%) in Credit card, whatever they say" },
    { text: "Llama puts 121 (62%) in Credit reporting and gets none of the 24 consumer loans right" },
    { text: "Large Qwen puts 9 of 30 money transfers in Bank account, the pair our own team argued over most. It needed 21 of 30 for R5 and got 20" },
    { text: "Its other slips: 4 credit-report tickets put in Debt collection; 3 consumer loans in Credit reporting" },
  ], { gap: 4 }), { x: px, y: 4.35, w: pw, h: 2.5, isTextBox: true, fontSize: 12, color: C.text1, margin: 0, valign: "top" });
}

// =====================================================================
// 11. Predictions + recommendation
{
  const s = content("Results and recommendation", "Right about the slow part, wrong about how slow",
    "Predictions: planning/prediction-record.md at tag prediction-freeze (2026-10-06 15:36 SGT). Outcomes: slides 9 and 10. Latency correlation r computed from service logs of the 27 load runs. Single-request latency from the sequential accuracy runs.");
  const ok = (t) => ({ text: t, options: { bold: true, color: C.accent3 } });
  const no = (t) => ({ text: t, options: { bold: true, color: C.accent4 } });
  const rows = [
    [H("We predicted (before testing)"), H("We measured"), H("")],
    ["Slow part: the model reading each ticket; it keeps ≥ 9 cores busy, our service < 10% of one", "Reading = 82% of the large model's time; ~10.4 cores busy; our service ≤ 6.8%", ok("Right")],
    ["Typical time per ticket: 0.8 / 0.9 / 6.1 s (small Qwen / Llama / large Qwen)", "0.40 / 0.46 / 2.84 s: about half", no("Wrong")],
    ["Large model overwhelmed near 9.4 /min; delays grow without end at 9.6", "Limit between 20 and 24 /min: 20 kept up, 24 overloaded twice", no("Wrong")],
    ["Accuracy 45% / 55% / 78%", "17.9% / 32.8% / 82.6%", no("2 of 3 wrong")],
    ["Small Qwen over-uses Credit reporting (> 35% of answers)", "It over-uses Credit card instead (79%)", no("Wrong")],
    ["Hardest: Debt collection, Consumer loan; ≥ 25% of money transfers put in Bank account", "Money transfer 66.7% (30% put in Bank account), Consumer loan 70.8%; but Debt collection 82.4%", ok("Mostly right")],
    ["95% of searches answered in under 0.1 s", "0.22–0.46 s as JMeter sees it (under 7 ms inside the system)", no("Wrong")],
  ];
  const tw = 7.95;
  s.addTable(rows, { x: MX, y: 1.4, w: tw, colW: [3.35, 3.35, 1.25], fontSize: 11, color: C.text1, border: { type: "solid", pt: 0.75, color: "D5DFDD" }, rowH: [0.32, 0.6, 0.45, 0.55, 0.36, 0.45, 0.62, 0.45], valign: "middle" });
  txt(s, [
    { text: "Why we were wrong: ", options: { bold: true, color: C.text2 } },
    { text: "we estimated speed from an early trial whose instructions to the model were longer (about 170 extra word-pieces), so every time came out about twice too slow. We did not expect the small models, given only category names, to put nearly everything in one category. Search time is mostly Wi-Fi, not the database." },
  ], MX, 5.5, tw, 1.35, { fontSize: 12 });

  const px = MX + tw + 0.3, pw = W - MX - px;
  card(s, px, 1.4, pw, 5.45, { fill: C.text2 });
  txt(s, "WE RECOMMEND", px + 0.25, 1.55, pw - 0.5, 0.3, { fontSize: 11, bold: true, color: HEX.accent6, charSpacing: 1 });
  txt(s, "qwen2.5:7b", px + 0.25, 1.85, pw - 0.5, 0.5, { fontSize: 26, bold: true, color: C.background1, fontFace: "Cambria" });
  s.addText(bullets([
    { text: "Meets R1–R4: 95% of tickets in 6.1 s (target 30), searches in 0.46 s (target 1), no failures, 82.6% correct (target 80)", options: { color: C.background1 } },
    { text: "Apache 2.0 [11] permits commercial use. 20/min sustained in the stress check, over 11× our peak load", options: { color: C.background1 } },
    { text: "The small models are 47–62 points short on accuracy. We value correct routing over speed, so being faster does not save them", options: { color: C.background1 } },
  ], { gap: 5 }), { x: px + 0.25, y: 2.45, w: pw - 0.5, h: 2.2, isTextBox: true, fontSize: 12, margin: 0, valign: "top" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: px + 0.2, y: 4.75, w: pw - 0.4, h: 1.95, rectRadius: 0.08, fill: { color: "1B4A50" }, line: { type: "none" } });
  txt(s, "Stated plainly", px + 0.4, 4.85, pw - 0.8, 0.3, { fontSize: 13, bold: true, color: C.accent2 });
  txt(s, "No model meets every target. All three miss R5: the large model gets 66.7% of money transfers right, one ticket short of 70%. Until better instructions are tried in Assignment 2, staff should double-check tickets sorted into Money transfer or Bank account.", px + 0.4, 5.17, pw - 0.8, 1.5, { fontSize: 11, color: C.background1 });
  s.addNotes("Final stress evidence revises the old capacity estimate: 20/min sustained in one attempt, 22/min mixed across two, 24/min overloaded in both reset-and-warm attempts. No accuracy or standard peak-load requirement changed. 20/1.73 = 11.56 times the modelled peak. This is test-machine headroom, not a promise for untested bank hardware.");
}

// =====================================================================
// 12. References
{
  const s = content("Results and recommendation", "References and acknowledgements",
    "IEEE style, numbered in order of first citation in the deck. Licences: Qwen2.5 0.5B and 7B are Apache 2.0; the Llama 3.2 Community License requires 'Built with Llama' attribution and a copy of the licence on redistribution; Ollama is MIT; Apache JMeter is Apache 2.0.");
  const A = "Accessed: Oct. 9, 2026.";
  const refs = [
    `[1] Ollama, "Ollama," ver. 0.35.1, MIT License. [Online]. Available: https://github.com/ollama/ollama. ${A}`,
    `[2] The Apache Software Foundation, "Apache JMeter," ver. 5.6.3. [Online]. Available: https://jmeter.apache.org/. ${A}`,
    `[3] Lloyds Banking Group, "Complaints publication report: Bank of Scotland plc, 1 July to 31 December 2025," 2026. [Online]. Available: https://www.lloydsbankinggroup.com/assets/pdfs/who-we-are/customer-complaints/2025/h2-2025/bank-of-scotland-plc.pdf. ${A}`,
    `[4] Financial Conduct Authority, "Aggregate complaints data: 2025 H2," 2026. [Online]. Available: https://www.fca.org.uk/data/complaints-data/aggregate-complaints-data-2025-h2. ${A}`,
    `[5] L. Brown, N. Gans, A. Mandelbaum, A. Sakov, H. Shen, S. Zeltyn, and L. Zhao, "Statistical analysis of a telephone call center: A queueing-science perspective," J. Amer. Statist. Assoc., vol. 100, no. 469, pp. 36–50, 2005, doi: 10.2307/27590517.`,
    `[6] Soon, "How many agents do you need for 500 calls a day?" [Online]. Available: https://soon.works/staffing/call-center/500-calls-per-day. ${A}`,
  ];
  const refs2 = [
    `[7] Financial Conduct Authority, "Complaint," FCA Handbook Glossary. [Online]. Available: https://www.handbook.fca.org.uk/handbook/glossary/G197.html. ${A}`,
    `[8] Consumer Financial Protection Bureau, "Consumer Complaint Database." [Online]. Available: https://www.consumerfinance.gov/data-research/consumer-complaints/. Course extract (rows 3000–3999) provided by Singapore Institute of Technology for ICT3113 via xSiTe.`,
    `[9] J. Nielsen, "Response times: The 3 important limits," Nielsen Norman Group, Jan. 1, 1993. [Online]. Available: https://www.nngroup.com/articles/response-times-3-important-limits/. ${A}`,
    `[10] A. Yang et al., "Qwen2.5 technical report," 2024, arXiv:2412.15115.`,
    `[11] The Apache Software Foundation, "Apache License, Version 2.0," Jan. 2004. [Online]. Available: https://www.apache.org/licenses/LICENSE-2.0. ${A}`,
    `[12] Meta Platforms, "Llama 3.2 Community License Agreement," Sep. 25, 2024. [Online]. Available: https://www.llama.com/llama3_2/license/. ${A}`,
  ];
  const cw2 = (CW - 0.4) / 2;
  const para = (list) => list.map((r, i) => ({ text: r, options: { breakLine: i < list.length - 1, paraSpaceAfter: 6 } }));
  s.addText(para(refs), { x: MX, y: 1.4, w: cw2, h: 4.55, isTextBox: true, fontSize: 11, color: C.text1, margin: 0, valign: "top" });
  s.addText(para(refs2), { x: MX + cw2 + 0.4, y: 1.4, w: cw2, h: 4.55, isTextBox: true, fontSize: 11, color: C.text1, margin: 0, valign: "top" });

  card(s, MX, 6.05, CW, 0.8, { fill: C.background2 });
  txt(s, [
    { text: "Acknowledgements.  ", options: { bold: true, color: C.text2 } },
    { text: "Complaint narratives published by the CFPB with consumer consent, personal data removed at source. Built with Llama. AI coding tools (Claude Code) helped build the service and test scripts and draft documents; all labels, test runs and the recommendation are the team's own." },
  ], MX + 0.25, 6.05, CW - 0.5, 0.8, { fontSize: 11, valign: "middle" });
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();

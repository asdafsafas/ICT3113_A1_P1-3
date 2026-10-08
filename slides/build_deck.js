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
  s.addText("Performance requirements, golden-set accuracy and load testing of three local Ollama models for a financial-services complaints desk", { placeholder: "body" });

  txt(s, "GROUP P1-3  ·  TEAM 3  ·  DATA ROWS 3000–3999", MX, 4.45, 7.4, 0.3, { fontSize: 12, bold: true, color: HEX.accent6, charSpacing: 1 });
  const members = [["Zong Han", "[student ID]"], ["Ridwan", "[student ID]"], ["Tze Han", "[student ID]"], ["Kannan", "[student ID]"], ["Natalie", "[student ID]"]];
  members.forEach(([n, id], i) => {
    const col = i < 3 ? 0 : 1, row = i < 3 ? i : i - 3;
    txt(s, [{ text: n, options: { bold: true, color: C.background1 } }, { text: "   " + id, options: { color: "CADDDA" } }], MX + col * 3.7, 4.85 + row * 0.38, 3.6, 0.34, { fontSize: 14 });
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
  txt(s, "golden-set accuracy (161 / 195)", 9.1, 3.45, 3.3, 0.3, { fontSize: 13, color: "CADDDA" });
  txt(s, "6.1 s", 9.1, 3.95, 3.3, 0.6, { fontSize: 32, bold: true, color: C.background1, fontFace: "Cambria" });
  txt(s, "POST /tickets p95 at peak load (limit 30 s)", 9.1, 4.55, 3.3, 0.3, { fontSize: 13, color: "CADDDA" });
  txt(s, "Misses one requirement: Money transfer recall 66.7% vs 70%", 9.1, 5.0, 3.3, 0.6, { fontSize: 12, italic: true, color: HEX.accent6 });
  s.addNotes("Cover. Names/IDs to be completed by the team. Headline figures: results/accuracy/comparison.md (82.6%), results/load/qwen2.5-7b/1.73rpm_s3.5_run*.jtl (p95 6.06 s mean of 3 runs).");
}

// =====================================================================
// 2. Architecture
pres.addSection({ title: "System and workload" });
{
  const s = content("System and workload", "One synchronous service in front of one CPU-only model server",
    "Source: docs/architecture.md, docker-compose.yml, service/app/. Baseline settings from .env.example: OLLAMA_NUM_PARALLEL=1, uvicorn --workers 1.");
  // LG box
  card(s, MX, 1.75, 2.45, 2.4, { fill: C.background2 });
  txt(s, "LOAD GENERATOR", MX + 0.2, 1.9, 2.1, 0.3, { fontSize: 11, bold: true, color: C.accent1, charSpacing: 1 });
  txt(s, "Separate Mac", MX + 0.2, 2.2, 2.1, 0.35, { fontSize: 16, bold: true, color: C.text2 });
  txt(s, "Apache JMeter 5.6.3, Open Model Thread Group. Plays the intake (POST) and the handlers (GET /search)", MX + 0.2, 2.6, 2.1, 1.4, { fontSize: 12, color: C.text1 });
  arrow(s, MX + 2.5, 2.95, 0.75, 0);
  txt(s, "HTTP, Wi-Fi", MX + 2.45, 2.55, 0.9, 0.3, { fontSize: 10, color: C.accent5, align: "center" });

  // SUT frame
  const sx = 3.9, sy = 1.45, sw = 4.25, sh = 5.3;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: sx, y: sy, w: sw, h: sh, rectRadius: 0.08, fill: { color: C.background1 }, line: { color: C.accent6, width: 1.25, dashType: "dash" } });
  txt(s, "SYSTEM UNDER TEST · MacBook Pro M5 · Docker", sx + 0.2, sy + 0.12, sw - 0.4, 0.3, { fontSize: 11, bold: true, color: C.accent1, charSpacing: 1 });
  // triage
  card(s, sx + 0.25, sy + 0.55, sw - 0.5, 1.15, { fill: C.text2 });
  txt(s, "triage service (FastAPI, port 8000)", sx + 0.45, sy + 0.65, sw - 0.9, 0.35, { fontSize: 14, bold: true, color: C.background1 });
  txt(s, "1 uvicorn worker · sync endpoints · writes one JSON log line per request", sx + 0.45, sy + 1.0, sw - 0.9, 0.6, { fontSize: 11, color: "CADDDA" });
  // ollama
  arrow(s, sx + 1.15, sy + 1.72, 0, 0.55);
  card(s, sx + 0.25, sy + 2.3, 2.95, 1.15, { fill: C.accent1 });
  txt(s, "Ollama 0.35.1 (CPU only)", sx + 0.45, sy + 2.4, 2.6, 0.35, { fontSize: 14, bold: true, color: C.background1 });
  txt(s, "One model loaded · NUM_PARALLEL=1: one ticket at a time", sx + 0.45, sy + 2.75, 2.6, 0.6, { fontSize: 11, color: C.background1 });
  // sqlite + logs
  arrow(s, sx + 3.6, sy + 1.72, 0, 2.05);
  card(s, sx + 2.25, sy + 3.8, 1.75, 1.25, { fill: C.background2 });
  txt(s, "SQLite volume", sx + 2.4, sy + 3.9, 1.5, 0.3, { fontSize: 13, bold: true, color: C.text2 });
  txt(s, "tickets + category; starts empty", sx + 2.4, sy + 4.25, 1.5, 0.7, { fontSize: 11 });
  card(s, sx + 0.25, sy + 3.8, 1.75, 1.25, { fill: C.background2 });
  txt(s, "Request log", sx + 0.4, sy + 3.9, 1.5, 0.3, { fontSize: 13, bold: true, color: C.text2 });
  txt(s, "logs/service/*.jsonl, kept in git", sx + 0.4, sy + 4.25, 1.5, 0.7, { fontSize: 11 });

  // endpoints
  const ex = 8.55, ew = W - MX - ex;
  txt(s, "Endpoints", ex, 1.45, ew, 0.4, { fontSize: 18, bold: true, color: C.text2, fontFace: "Cambria" });
  const eps = [
    ["POST /tickets", "Classifies one narrative into 1 of 7 categories (JSON-schema output), stores it, returns the category"],
    ["GET /search?q=", "Stored tickets whose text contains the query, newest first"],
    ["GET /stats", "Count of stored tickets per category"],
  ];
  eps.forEach(([e, d], i) => {
    const y = 1.95 + i * 0.95;
    card(s, ex, y, ew, 0.82, { fill: C.background2 });
    txt(s, e, ex + 0.15, y + 0.08, ew - 0.3, 0.3, { fontSize: 13, bold: true, color: C.accent1, fontFace: "Courier New" });
    txt(s, d, ex + 0.15, y + 0.38, ew - 0.3, 0.42, { fontSize: 11 });
  });
  txt(s, "Baseline as specified", ex, 4.85, ew, 0.35, { fontSize: 16, bold: true, color: C.text2, fontFace: "Cambria" });
  s.addText(bullets([
    "Synchronous: POST returns only after the model answers",
    "No caching: the same text is classified again",
    "No queuing in our code; Ollama's own FIFO is the only queue",
    "Search is a LIKE '%q%' scan; new SQLite connection per request",
  ], { gap: 3 }), { x: ex, y: 5.25, w: ew, h: 1.55, isTextBox: true, fontSize: 12, color: C.text1, margin: 0, valign: "top" });
}

// =====================================================================
// 3. Workload model
{
  const s = content("System and workload", "The desk peaks at 1.73 tickets per minute, all in business hours",
    "Source: planning/workload-model.md. Ticket lengths reproduced with python scripts/ticket_lengths.py over rows 3000-3999.");
  const stats = [
    ["86,719", "in-scope complaints per half-year (Bank of Scotland plc, H2 2025)", "SOURCED [1]"],
    ["≈ 694", "per business day: ×2 for a year, ÷ 250 days", "ESTIMATED"],
    ["1.45/min", "average: 694 over 8 business hours", "ESTIMATED"],
    ["1.73/min", "peak hour carries 15% of the day: 104 tickets", "EST. FROM [3][4]"],
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
  txt(s, "Load levels tested (POST + search per minute)", MX, 3.75, 7.4, 0.35, { fontSize: 15, bold: true, color: C.text2, fontFace: "Cambria" });
  const rows = [
    [H("Level"), H("Tickets /min"), H("Searches /min"), H("Basis")],
    ["Average", "1.45", "2.9", "Average business hour"],
    [{ text: "Peak", options: { bold: true } }, { text: "1.73", options: { bold: true } }, { text: "3.5", options: { bold: true } }, { text: "Requirements must hold here", options: { bold: true } }],
    ["Beyond peak", "3.5", "7", "2 × peak: unsized seasonal surges"],
  ];
  s.addTable(rows, { x: MX, y: 4.15, w: 7.35, colW: [1.45, 1.35, 1.45, 3.1], fontSize: 12, color: C.text1, border: { type: "solid", pt: 0.75, color: "D5DFDD" }, rowH: 0.36, valign: "middle" });
  s.addText(bullets([
    "Searches: 2 per ticket handled (earlier complaints + similar cases). ESTIMATED: no published figure",
    "Every complaint counted as a ticket, phone included; out-of-hours folded into business hours. Both overstate load",
  ], { gap: 3 }), { x: MX, y: 5.75, w: 7.35, h: 1.1, isTextBox: true, fontSize: 12, color: C.text1, margin: 0, valign: "top" });

  // ticket length chart
  const chx = 8.3, chw = W - MX - chx;
  s.addChart(pres.charts.BAR, [{ name: "Characters", labels: ["p5", "p25", "p50", "p75", "p95", "p99", "max"], values: [263, 512, 797, 1214, 1780, 1938, 2000] }], {
    x: chx, y: 1.4, w: chw, h: 3.75, barDir: "col",
    chartColors: [HEX.accent1], showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10, dataLabelColor: HEX.dk1, dataLabelFontFace: "+mn-lt",
    showTitle: true, title: "Ticket length in characters (1,000 rows)", titleFontSize: 13, titleColor: HEX.dk2, titleFontFace: "+mn-lt",
    catAxisLabelColor: HEX.accent5, valAxisLabelColor: HEX.accent5, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", catAxisLabelFontSize: 11, valAxisLabelFontSize: 10,
    valGridLine: { color: "E2E8E7", size: 0.5 }, catGridLine: { style: "none" }, showLegend: false, valAxisMaxVal: 2400, valAxisMinVal: 0,
  });
  s.addText(bullets([
    "Median 797 chars / 144 words; p95 1,780 chars (2.2 × median)",
    "Max 2,000 chars + 395-char prompt fits num_ctx 4,096: nothing truncated (max 617 prompt tokens logged)",
  ], { gap: 3 }), { x: chx, y: 5.3, w: chw, h: 1.5, isTextBox: true, fontSize: 12, color: C.text1, margin: 0, valign: "top" });
}

// =====================================================================
// 4. Requirements
pres.addSection({ title: "Requirements and candidates" });
{
  const s = content("Requirements and candidates", "As accurate as a trained human, fast enough for the peak",
    "Source: planning/requirements.md (frozen with tag prediction-freeze).");
  card(s, MX, 1.4, CW, 0.82, { fill: C.text2 });
  txt(s, [
    { text: "Our position: ", options: { bold: true, color: C.accent2 } },
    { text: "a misrouted ticket costs more than a slow one. It must be noticed, re-read and re-routed by a second team. A 30 s classification changes nothing for a complaint a person answers over hours or days.", options: { color: C.background1 } },
  ], MX + 0.25, 1.45, CW - 0.5, 0.72, { fontSize: 13, valign: "middle" });

  const R = (id) => ({ text: id, options: { bold: true, color: C.accent1 } });
  const rows = [
    [H("ID"), H("Requirement (testable)"), H("Load condition"), H("Why this number")],
    [R("R1"), "POST /tickets p95 ≤ 30 s", "Peak 1.73 tickets/min, 10 min, 3 runs", "At peak a ticket arrives every ~35 s; slower than that and a one-at-a-time queue never clears"],
    [R("R2"), "GET /search p95 ≤ 1 s", "Mixed: 1.73 tickets + 3.5 searches/min, 10 min", "A handler waits at the screen; ~1 s keeps their flow of thought unbroken [7]"],
    [R("R3"), "Throughput ≥ 104 classified/hour (1.73/min), errors ≤ 1%, latency not growing", "Peak 1.73 tickets/min, 10 min, 3 runs", "Peak-hour volume; throughput below arrivals means a growing backlog"],
    [R("R4"), "Overall accuracy ≥ 80%", "195-ticket golden set, one pass", "Our labellers agreed on 78–85% before discussion: the model must match one trained human"],
    [R("R5"), "Every category recall ≥ 70%", "Golden set, per category", "Smallest classes have 17–18 tickets (~6 points per error), so the bar sits below R4"],
  ];
  s.addTable(rows, { x: MX, y: 2.45, w: CW, colW: [0.6, 3.55, 3.3, 4.68], fontSize: 12, color: C.text1, border: { type: "solid", pt: 0.75, color: "D5DFDD" }, valign: "middle", rowH: [0.36, 0.62, 0.62, 0.62, 0.62, 0.62] });
  card(s, MX, 6.3, CW, 0.55, { fill: C.background2 });
  txt(s, [
    { text: "Constraints.  C1: ", options: { bold: true, color: C.text2 } },
    { text: "local Ollama on CPU only, no public API.   " },
    { text: "C2: ", options: { bold: true, color: C.text2 } },
    { text: "the model's licence must allow the bank's commercial use." },
  ], MX + 0.25, 6.3, CW - 0.5, 0.55, { fontSize: 12, valign: "middle" });
}

// =====================================================================
// 5. Candidate models
{
  const s = content("Requirements and candidates", "Three candidates span two size classes and 15× in parameters",
    "Source: models/models.lock.json, docs/models.md. qwen2.5:3b was in the four-model lock at tag prediction-freeze.");
  const cands = [
    ["SMALL  · < 1B", "qwen2.5:0.5b", "494M params · Q4_K_M · 398 MB", "Apache 2.0", "Fastest baseline; same family as the 7B, so size is the only variable", MODEL_HEX.q05],
    ["SMALL  · ~1B", "llama3.2:1b-instruct-q4_K_M", "1.2B params · Q4_K_M · 808 MB", "Llama 3.2 Community", "A second family in the small class: does training matter as much as size?", MODEL_HEX.l1],
    ["LARGE  · ~7B", "qwen2.5:7b", "7.6B params · Q4_K_M · 4.7 GB", "Apache 2.0", "Largest that fits the 9.7 GiB Docker memory budget; expected most accurate", MODEL_HEX.q7],
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
  txt(s, "Pins (full SHA-256 digests as installed; checked with pull_models.py --check before every session)", MX, 4.45, CW, 0.3, { fontSize: 13, bold: true, color: C.text2 });
  const mono = (t) => ({ text: t, options: { fontFace: "Courier New", fontSize: 10.5 } });
  s.addTable([
    [H("Tag"), H("Digest")],
    [mono("qwen2.5:0.5b"), mono("a8b0c51577010a279d933d14c2a8ab4b268079d44c5c8830c0a93900f1827c67")],
    [mono("llama3.2:1b-instruct-q4_K_M"), mono("22bc6b92eb0160c4629782fca05a9032c59d306ab2058b7dacc8a4644fbafa02")],
    [mono("qwen2.5:7b"), mono("845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e")],
    [mono("ollama/ollama:0.35.1 (image)"), mono("sha256:292ee7945dfc3d5840a181f3ab86fedb1e66703e02c8af98b50f4da56b7e278c")],
  ], { x: MX, y: 4.8, w: CW, colW: [3.6, 8.53], fontSize: 11, color: C.text1, border: { type: "solid", pt: 0.75, color: "D5DFDD" }, rowH: 0.3, valign: "middle" });
  txt(s, "All Q4_K_M, so quantisation is held constant. qwen2.5:3b was in the frozen four-model set but was not measured: its Qwen Research licence is non-commercial and fails C2.", MX, 6.4, CW, 0.5, { fontSize: 12, italic: true, color: C.accent5 });
}

// =====================================================================
// 6. Golden set
pres.addSection({ title: "Golden set and testing" });
{
  const s = content("Golden set and testing", "195 golden tickets, labelled twice and frozen before testing",
    "Sources: golden/PROTOCOL.md, golden/agreement_summary.md, golden/SUMMARY.md, golden/pairs/*.csv. Label sheets committed in 39d4cc2; golden set frozen in 653a98e; tag prediction-freeze 2026-10-06 15:36 SGT; first official benchmark run 17:13 SGT the same day.");
  const st = [
    ["κ = 0.735", "Group A, rows 3000–3099", "Cohen's kappa, 2 labellers (78% raw agreement)"],
    ["κ = 0.778", "Group B, rows 3100–3199", "Fleiss' kappa, 3 labellers (pairwise Cohen 0.745–0.826)"],
    ["49", "disagreements, all recorded", "44 resolved to a category · 5 excluded (no identifiable product)"],
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
  txt(s, "Protocol revisions", MX, 3.05, 4, 0.35, { fontSize: 15, bold: true, color: C.text2, fontFace: "Cambria" });
  const tl = [
    ["v0.1", "Definitions for 7 categories; tie-break: the product the complaint is mainly about"],
    ["v0.2", "From 16 Group A rows: decide Credit reporting vs Debt collection by who the complaint is against; student loans → Consumer loan; bank-account fraud → Bank account"],
    ["v0.3", "From 12 Group B rows: prepaid cards and crypto → Money transfer; scams follow the product the money left through; when to EXCLUDE"],
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
    ["Same situation, two answers (3025 vs 3072, rule v0.2)", "Both: a collection account on a credit report. 3025 demands TransUnion delete it → Credit reporting. 3072 says Midland, the collector, never proved the debt → Debt collection."],
    ["A rule overturning the majority (3141)", "2 of 3 labellers chose Credit reporting: the person wants a repossession removed. The request is to Ally Financial, the auto lender, so v0.2 makes it Consumer loan."],
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
  const s = content("Golden set and testing", "Two Macs over Wi-Fi; model CPU time is what scales",
    "Sources: evidence/smoke-prototype/env/service_machine.txt (SUT), results/load/*/..._jmeter.log (LG: os.name, java.version, JMeter version), service logs for search latency, *_stats.csv for docker stats.");
  const mw = (CW - 1.0) / 2;
  card(s, MX, 1.4, mw, 2.95, { fill: C.text2 });
  txt(s, "SYSTEM UNDER TEST: triage + Ollama", MX + 0.25, 1.52, mw - 0.5, 0.3, { fontSize: 11, bold: true, color: HEX.accent6, charSpacing: 1 });
  s.addText(bullets([
    "MacBook Pro (Mac17,2), Apple M5, 10 cores (4 P + 6 E), 16 GB",
    "macOS 26.6.2 · Docker 29.8.2, VM with 10 CPUs and 9.7 GiB",
    "Ollama 0.35.1, CPU only (ollama ps: 100% CPU)",
    "NUM_PARALLEL=1 · num_ctx 4096 · temperature 0 · seed 42",
  ], { gap: 4 }), { x: MX + 0.25, y: 1.9, w: mw - 0.5, h: 2.35, isTextBox: true, fontSize: 13, color: C.background1, margin: 0, valign: "top" });

  const lx = MX + mw + 1.0;
  arrow(s, MX + mw + 0.1, 2.85, 0.8, 0, C.accent1);
  txt(s, "phone hotspot", MX + mw + 0.02, 2.45, 0.96, 0.3, { fontSize: 10, color: C.accent5, align: "center" });
  card(s, lx, 1.4, mw, 2.95, { fill: C.background2 });
  txt(s, "LOAD GENERATOR: a separate machine", lx + 0.25, 1.52, mw - 0.5, 0.3, { fontSize: 11, bold: true, color: C.accent1, charSpacing: 1 });
  s.addText(bullets([
    "A second Mac (Ridwan's), macOS 26.5",
    "Java 17.0.17 · Apache JMeter 5.6.3, non-GUI mode",
    "Reaches the SUT at 172.20.10.2:8000 over Wi-Fi",
    "Confirmed separate: different OS build from the SUT (26.5 vs 26.6.2); every JMeter log targets host 172.20.10.2",
  ], { gap: 4 }), { x: lx + 0.25, y: 1.9, w: mw - 0.5, h: 2.35, isTextBox: true, fontSize: 13, color: C.text1, margin: 0, valign: "top" });

  const bw = (CW - 0.3) / 2;
  txt(s, "How results scale to the client's servers", MX, 4.6, bw, 0.35, { fontSize: 15, bold: true, color: C.text2, fontFace: "Cambria" });
  s.addText(bullets([
    "82–89% of model time is reading the prompt: a CPU and memory-bandwidth cost that moves with the server",
    "Capacity ≈ 60 ÷ mean model time: 3.1 s here, about 19 tickets/min for 7B",
    "Estimate: a server ~3× slower per ticket still keeps peak p95 < 30 s. Re-measure one 7B ticket on the client's CPU first",
  ], { gap: 4 }), { x: MX, y: 5.0, w: bw, h: 1.9, isTextBox: true, fontSize: 12, color: C.text1, margin: 0, valign: "top" });
  txt(s, "What could make our numbers unrepresentative", MX + bw + 0.3, 4.6, bw, 0.35, { fontSize: 15, bold: true, color: C.text2, fontFace: "Cambria" });
  s.addText(bullets([
    "Apple Silicon (ARM, unified memory) ≠ x86 DDR servers; laptop thermals; power state not logged for official runs",
    "Wi-Fi: search takes ≤ 7 ms in the service (p95) but 0.2–0.5 s at JMeter, so the network dominates it",
    "10-min runs carry 14–35 POSTs: at ≤ 17 samples p99 equals the maximum",
  ], { gap: 4 }), { x: MX + bw + 0.3, y: 5.0, w: bw, h: 1.9, isTextBox: true, fontSize: 12, color: C.text1, margin: 0, valign: "top" });
}

// =====================================================================
// 8. Playbook
{
  const s = content("Golden set and testing", "Every run follows the same reset, load, reconcile loop",
    "Full step-by-step playbook: docs/actual-jmeter-test.md and docs/load-testing.md. Runners: scripts/run_official_jmeter_suite.py, scripts/run_7b_stress_suite.py, scripts/run_accuracy_suite.py. Reconciliation: scripts/reconcile.py. Summary: scripts/summarise_jtl.py.");
  const steps = [
    ["Reset", "Restart Ollama, delete the DB volume, check /health tag and digest"],
    ["Warm up", "One invented ticket loads the model; recreate the DB empty"],
    ["Monitor", "docker stats every 5 s into _stats.csv"],
    ["Load", "JMeter non-GUI on the separate Mac"],
    ["Collect", "Commit .jtl, JMeter log, service log, stats"],
    ["Reconcile", "Match every request ID; no unknown requests"],
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
      "Open Model Thread Group: random (Poisson) arrivals at a fixed rate, so a slow server cannot slow the arrivals",
      "3 models × {1.45/2.9, 1.73/3.5, 3.5/7} tickets/searches per min × 3 runs",
      "10 min arrivals + 5 min drain; timeout 600 s",
      "Tickets from rows 3200–3999 (golden rows excluded), same order each run; X-Request-ID on every request",
    ]],
    ["Accuracy test: 3 passes", [
      "All 195 golden tickets sent once each through POST /tickets, one at a time",
      "Scored against golden labels: overall, per-category recall and precision, confusion matrix",
      "Run 8 Oct, after the freeze; no load test running at the same time",
    ]],
    ["Stress test: qwen2.5:7b", [
      "Ramp 3.5 → 12 tickets/min over 30 min (+ 7 searches/min, 10 min drain)",
      "Confirm with 15-min constant runs at 7.2 and 9.6/min",
      "Limit = throughput stops tracking arrivals and latency grows through the run",
      "Diagnose: Ollama queue wait = total − prompt − generation time",
    ]],
  ];
  tests.forEach(([h, items], i) => {
    const x = MX + i * (tw + 0.3);
    card(s, x, ty, tw, th, { fill: C.background1, line: "D5DFDD" });
    txt(s, h, x + 0.25, ty + 0.15, tw - 0.5, 0.35, { fontSize: 15, bold: true, color: C.accent1, fontFace: "Cambria" });
    s.addText(bullets(items, { gap: 4 }), { x: x + 0.25, y: ty + 0.6, w: tw - 0.5, h: th - 0.75, isTextBox: true, fontSize: 12, color: C.text1, margin: 0, valign: "top" });
  });
}

// =====================================================================
// 9. Load & stress results
pres.addSection({ title: "Results and recommendation" });
{
  const s = content("Results and recommendation", "All models meet R1–R3 easily; Ollama is the bottleneck",
    "Source: python scripts/summarise_jtl.py results/load (POST /tickets) and --label \"GET /search\". Values are mean (min–max) over 3 runs; no warm-up skip. Error rate 0.0% in all 27 runs: 0 of 594 POSTs, 0 of 1,206 searches. Ollama queue wait from service logs: ollama_total_ms − prompt_eval_ms − eval_ms. CPU from *_stats.csv.");
  const g = (t) => ({ text: t, options: { color: C.accent5 } });
  const M = (t, n) => ({ text: t, options: { rowspan: n, bold: true, color: C.text2, valign: "middle" } });
  const pk = (t) => ({ text: t, options: { bold: true, fill: { color: "E3EEEC" } } });
  const rows = [
    [H("Model"), H("Load /min"), H("p50 s"), H("p95 s"), H("p99 s"), H("Thru /min"), H("Err"), H("Search p95 s")],
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
  s.addTable(rows, { x: MX, y: 1.4, w: tw, colW: [1.3, 1.05, 1.5, 1.5, 0.7, 0.85, 0.6, 1.2], fontSize: 11, color: C.text1, border: { type: "solid", pt: 0.75, color: "D5DFDD" }, rowH: 0.37, valign: "middle", align: "left" });
  txt(s, "POST /tickets latency; mean (min–max) of 3 runs. Shaded = peak, where R1–R3 apply. p99 range in repo summary.", MX, 5.15, tw, 0.3, { fontSize: 10, italic: true, color: C.accent5 });

  // verdict strip
  const vy = 5.6;
  [["R1", "peak p95 ≤ 30 s: worst 6.06 s (7B)"], ["R2", "search p95 ≤ 1 s: worst 0.46 s"], ["R3", "0 errors in 27 runs; throughput tracks arrivals"]].forEach(([r, t], i) => {
    const x = MX + i * 2.95;
    card(s, x, vy, 2.8, 1.25, { fill: C.background2 });
    pill(s, r + " PASS", true, x + 0.2, vy + 0.15, 1.05);
    txt(s, "All 3 models", x + 1.35, vy + 0.15, 1.3, 0.3, { fontSize: 11, bold: true, color: C.accent3, valign: "middle" });
    txt(s, t, x + 0.2, vy + 0.55, 2.45, 0.65, { fontSize: 11 });
  });

  // stress panel
  const px = MX + tw + 0.3, pw = W - MX - px;
  card(s, px, 1.4, pw, 5.45, { fill: C.text2 });
  txt(s, "STRESS TEST · qwen2.5:7b", px + 0.2, 1.52, pw - 0.4, 0.3, { fontSize: 11, bold: true, color: HEX.accent6, charSpacing: 1 });
  const sr = [["Ramp 3.5 → 12", "232 POSTs · p95 10.2 s"], ["7.2 /min, 15 min", "108 POSTs · p95 8.7 s"], ["9.6 /min, 15 min", "144 POSTs · p95 17.3 s"]];
  sr.forEach(([a, b], i) => {
    const y = 1.92 + i * 0.6;
    txt(s, a, px + 0.2, y, pw - 0.4, 0.27, { fontSize: 12, bold: true, color: C.background1 });
    txt(s, b + " · 0 errors", px + 0.2, y + 0.27, pw - 0.4, 0.27, { fontSize: 11, color: "CADDDA" });
  });
  txt(s, "No limit found up to 12 /min", px + 0.2, 3.85, pw - 0.4, 0.35, { fontSize: 14, bold: true, color: C.accent2, fontFace: "Cambria" });
  txt(s, "Sustained 9.6 /min with no latency growth: 5.5× peak. Estimated limit ≈ 19 /min (60 ÷ 3.1 s), not yet confirmed.", px + 0.2, 4.22, pw - 0.4, 0.95, { fontSize: 11, color: C.background1 });
  txt(s, "Bottleneck: Ollama", px + 0.2, 5.15, pw - 0.4, 0.35, { fontSize: 14, bold: true, color: C.accent2, fontFace: "Cambria" });
  txt(s, "Wait in our service < 0.1 s; at 9.6 /min the wait inside Ollama's FIFO reaches p95 14.6 s. Ollama CPU p99 1,040% vs triage ≤ 6.8%.", px + 0.2, 5.52, pw - 0.4, 1.25, { fontSize: 11, color: C.background1 });
}

// =====================================================================
// 10. Accuracy results
{
  const s = content("Results and recommendation", "Only the 7B model classifies usefully, and it misses one category",
    "Source: results/accuracy/comparison.md and per-run reports results/accuracy/20261008T*.md (confusion matrices). Run 8 Oct 2026, prompt classify_v1.txt, after the freeze.");
  const cats = ["Credit reporting (42)", "Debt collection (17)", "Mortgage (27)", "Credit card (18)", "Bank account (37)", "Consumer loan (24)", "Money transfer (30)"];
  const chw = 7.9;
  s.addChart([
    { type: pres.charts.BAR, data: [
      { name: "qwen2.5:0.5b", labels: cats, values: [40.5, 0, 0, 94.4, 2.7, 0, 0] },
      { name: "llama3.2:1b", labels: cats, values: [85.7, 58.8, 29.6, 16.7, 16.2, 0, 3.3] },
      { name: "qwen2.5:7b", labels: cats, values: [81.0, 82.4, 92.6, 88.9, 94.6, 70.8, 66.7] },
    ], options: { barDir: "col", barGapWidthPct: 60, chartColors: [MODEL_HEX.q05, MODEL_HEX.l1, MODEL_HEX.q7] } },
    { type: pres.charts.LINE, data: [{ name: "R5 bar (70%)", labels: cats, values: [70, 70, 70, 70, 70, 70, 70] }], options: { chartColors: [HEX.accent4], lineSize: 1.5, lineDataSymbol: "none", lineDash: "dash" } },
  ], {
    x: MX, y: 1.35, w: chw, h: 5.5,
    showTitle: true, title: "Per-category recall on the golden set (%), tickets per category in brackets", titleFontSize: 13, titleColor: HEX.dk2, titleFontFace: "+mn-lt",
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
    { text: "0.5B labels 155 of 195 tickets (79%) Credit card, whatever the content" },
    { text: "1B labels 121 (62%) Credit reporting; 0 of 24 Consumer loans right" },
    { text: "7B sends 9 of 30 Money transfers to Bank account, the split our own labellers argued over most. It needs 21 of 30 correct for R5 and gets 20" },
    { text: "7B also: 4 Credit reporting → Debt collection; 3 Consumer loan → Credit reporting" },
  ], { gap: 4 }), { x: px, y: 4.35, w: pw, h: 2.5, isTextBox: true, fontSize: 12, color: C.text1, margin: 0, valign: "top" });
}

// =====================================================================
// 11. Predictions + recommendation
{
  const s = content("Results and recommendation", "Right about the bottleneck, wrong about its size",
    "Predictions: planning/prediction-record.md at tag prediction-freeze (2026-10-06 15:36 SGT). Outcomes: slides 9 and 10. Latency correlation r computed from service logs of the 27 load runs. Single-request latency from the sequential accuracy runs.");
  const ok = (t) => ({ text: t, options: { bold: true, color: C.accent3 } });
  const no = (t) => ({ text: t, options: { bold: true, color: C.accent4 } });
  const rows = [
    [H("We predicted"), H("We measured"), H("")],
    ["Bottleneck: Ollama reading the prompt; Ollama ≥ 900% CPU, triage < 10%", "Prompt = 82% of 7B model time; Ollama p99 1,040%, triage max 6.8%", ok("Right")],
    ["Single-ticket p50: 0.8 / 0.9 / 6.1 s (0.5B / 1B / 7B)", "0.40 / 0.46 / 2.84 s, about half", no("Wrong")],
    ["7B saturates near 9.4 /min; latency grows without bound at 9.6", "Stable at 9.6 /min, p95 17.3 s, 0 errors", no("Wrong")],
    ["Accuracy 45% / 55% / 78%", "17.9% / 32.8% / 82.6%", no("2 of 3 wrong")],
    ["0.5B defaults to Credit reporting (> 35% of answers)", "Defaults to Credit card (79%)", no("Wrong")],
    ["Hardest: Debt collection, Consumer loan; ≥ 25% of Money transfer → Bank account", "Money transfer 66.7% (30% → Bank account), Consumer loan 70.8%; Debt collection 82.4%", ok("Mostly right")],
    ["Search p95 < 100 ms at peak", "0.22–0.46 s at JMeter (≤ 7 ms inside the service)", no("Wrong")],
  ];
  const tw = 7.95;
  s.addTable(rows, { x: MX, y: 1.4, w: tw, colW: [3.35, 3.35, 1.25], fontSize: 11, color: C.text1, border: { type: "solid", pt: 0.75, color: "D5DFDD" }, rowH: [0.32, 0.55, 0.45, 0.55, 0.4, 0.45, 0.62, 0.45], valign: "middle" });
  txt(s, [
    { text: "Why: ", options: { bold: true, color: C.text2 } },
    { text: "latency was extrapolated from a prototype prompt with category definitions, ~170 tokens longer than the frozen one, so every time and the 7B capacity came out ~2× too slow. We underestimated how badly sub-1B models fail without definitions: each collapses onto a single label. Search time is network, not SQLite." },
  ], MX, 5.35, tw, 1.5, { fontSize: 12 });

  const px = MX + tw + 0.3, pw = W - MX - px;
  card(s, px, 1.4, pw, 5.45, { fill: C.text2 });
  txt(s, "WE RECOMMEND", px + 0.25, 1.55, pw - 0.5, 0.3, { fontSize: 11, bold: true, color: HEX.accent6, charSpacing: 1 });
  txt(s, "qwen2.5:7b", px + 0.25, 1.85, pw - 0.5, 0.5, { fontSize: 26, bold: true, color: C.background1, fontFace: "Cambria" });
  s.addText(bullets([
    { text: "Meets R1–R4: p95 6.1 s (limit 30), search 0.46 s (limit 1), 0 errors, 82.6% (bar 80)", options: { color: C.background1 } },
    { text: "Apache 2.0 licence passes C2; fits on one CPU server", options: { color: C.background1 } },
    { text: "Small models fail R4 by 47–62 points. Under our position their speed does not matter", options: { color: C.background1 } },
  ], { gap: 5 }), { x: px + 0.25, y: 2.45, w: pw - 0.5, h: 2.2, isTextBox: true, fontSize: 12, margin: 0, valign: "top" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: px + 0.2, y: 4.75, w: pw - 0.4, h: 1.95, rectRadius: 0.08, fill: { color: "1B4A50" }, line: { type: "none" } });
  txt(s, "Stated plainly", px + 0.4, 4.85, pw - 0.8, 0.3, { fontSize: 13, bold: true, color: C.accent2 });
  txt(s, "No candidate meets every requirement. R5 fails for all three; for 7B, Money transfer reaches 66.7%, one ticket short of 70%. Until a prompt fix in A2, double-check tickets routed to Money transfer and Bank account.", px + 0.4, 5.17, pw - 0.8, 1.5, { fontSize: 11, color: C.background1 });
}

// =====================================================================
// 12. References
{
  const s = content("Results and recommendation", "References and acknowledgements",
    "Licences: Qwen2.5 0.5B and 7B are Apache 2.0; Llama 3.2 Community License requires 'Built with Llama' attribution and a copy of the licence on redistribution; Ollama is MIT; Apache JMeter is Apache 2.0.");
  const refs = [
    "[1] Lloyds Banking Group (2026). Complaints publication report: Bank of Scotland plc, 1 July – 31 December 2025. lloydsbankinggroup.com",
    "[2] Financial Conduct Authority (2026). Aggregate complaints data: 2025 H2. fca.org.uk/data/complaints-data/aggregate-complaints-data-2025-h2",
    "[3] Brown, L. et al. (2005). Statistical analysis of a telephone call center: a queueing-science perspective. JASA, 100(469), 36–50.",
    "[4] Soon. How many agents do you need for 500 calls a day? soon.works/staffing/call-center/500-calls-per-day",
    "[5] Financial Conduct Authority. FCA Handbook Glossary: complaint. handbook.fca.org.uk/glossary/G197",
    "[6] Consumer Financial Protection Bureau. Consumer Complaint Database. consumerfinance.gov/data-research/consumer-complaints (course extract, rows 3000–3999)",
    "[7] Nielsen, J. (1993). Response times: the 3 important limits. Nielsen Norman Group. nngroup.com/articles/response-times-3-important-limits",
  ];
  const lw = 7.3;
  txt(s, "References", MX, 1.4, lw, 0.35, { fontSize: 16, bold: true, color: C.text2, fontFace: "Cambria" });
  s.addText(refs.map((r, i) => ({ text: r, options: { breakLine: i < refs.length - 1, paraSpaceAfter: 6 } })), { x: MX, y: 1.85, w: lw, h: 5.0, isTextBox: true, fontSize: 11, color: C.text1, margin: 0, valign: "top" });

  const px = MX + lw + 0.4, pw = W - MX - px;
  card(s, px, 1.4, pw, 3.3, { fill: C.background2 });
  txt(s, "Software and model licences", px + 0.25, 1.52, pw - 0.5, 0.35, { fontSize: 14, bold: true, color: C.text2 });
  s.addText(bullets([
    "Ollama 0.35.1, MIT License. ollama.com",
    "Qwen2.5 0.5B and 7B (Alibaba Cloud), Apache License 2.0",
    "Llama 3.2 1B: Llama 3.2 Community License, Meta Platforms. Built with Llama",
    "Apache JMeter 5.6.3, Apache License 2.0",
    "FastAPI (MIT), SQLite (public domain), Docker",
  ], { gap: 3 }), { x: px + 0.25, y: 1.92, w: pw - 0.5, h: 2.7, isTextBox: true, fontSize: 11, color: C.text1, margin: 0, valign: "top" });
  card(s, px, 4.9, pw, 1.95, { fill: C.background1, line: "D5DFDD" });
  txt(s, "Acknowledgements", px + 0.25, 5.0, pw - 0.5, 0.35, { fontSize: 14, bold: true, color: C.text2 });
  txt(s, "Complaint narratives published by the CFPB with consumer consent, personal data removed at source. AI coding tools (Claude Code) helped build the service and test scripts and draft documents; all labels, test runs and the recommendation are the team's own.", px + 0.25, 5.38, pw - 0.5, 1.4, { fontSize: 11 });
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();

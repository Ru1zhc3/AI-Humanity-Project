const { FileBlob, PresentationFile } = await import("@oai/artifact-tool");
const fs = await import("node:fs/promises");

const root = process.cwd().replaceAll("\\", "/");
const inputPath =
  `${root}/docs/presentations/Political Content Moderation Across Different Models and Languages.pptx`;
const outputPath =
  `${root}/docs/presentations/Political Content Moderation Across Different Models and Languages - model comparison results.pptx`;
const tableDir =
  `${root}/results/model_comparison/tables`;

const W = 960;
const H = 540;
const FONT = { title: "Poppins", body: "Lato" };
const COLORS = {
  bg: "#F8FAFC",
  ink: "#172033",
  muted: "#52637A",
  line: "#CBD5E1",
  panel: "#FFFFFF",
  blue: "#2563EB",
  amber: "#F59E0B",
  teal: "#0F766E",
  red: "#BE123C",
  green: "#15803D",
  slate: "#64748B",
};
const LEAN_COLORS = {
  "Auth-Left": "#7C3AED",
  "Auth-Right": "#DC2626",
  Centrist: "#64748B",
  "Lib-Left": "#2563EB",
  "Lib-Right": "#16A34A",
};

function parseCsv(text) {
  const rows = [];
  let row = [];
  let cell = "";
  let inQuotes = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    const next = text[i + 1];
    if (ch === '"' && inQuotes && next === '"') {
      cell += '"';
      i += 1;
    } else if (ch === '"') {
      inQuotes = !inQuotes;
    } else if (ch === "," && !inQuotes) {
      row.push(cell);
      cell = "";
    } else if ((ch === "\n" || ch === "\r") && !inQuotes) {
      if (ch === "\r" && next === "\n") i += 1;
      row.push(cell);
      if (row.some((v) => v.length > 0)) rows.push(row);
      row = [];
      cell = "";
    } else {
      cell += ch;
    }
  }
  if (cell || row.length) {
    row.push(cell);
    rows.push(row);
  }
  const headers = rows.shift().map((h) => h.replace(/^\uFEFF/, ""));
  return rows.map((r) => Object.fromEntries(headers.map((h, i) => [h, r[i] ?? ""])));
}

async function loadCsv(name) {
  return parseCsv(await fs.readFile(`${tableDir}/${name}`, "utf-8"));
}

function clearSlide(slide) {
  for (const collectionName of ["shapes", "images", "charts", "tables"]) {
    const collection = slide[collectionName];
    if (!collection?.items) continue;
    for (const item of [...collection.items]) {
      if (typeof item.delete === "function") item.delete();
    }
  }
}

function addText(slide, text, position, opts = {}) {
  const shape = slide.shapes.add({
    geometry: "rect",
    position,
    fill: opts.fill ?? "#FFFFFF00",
    line: { width: 0, fill: "#FFFFFF00" },
  });
  shape.text = text;
  shape.text.typeface = opts.typeface ?? FONT.body;
  shape.text.fontSize = opts.fontSize ?? 18;
  shape.text.color = opts.color ?? COLORS.ink;
  shape.text.bold = opts.bold ?? false;
  shape.text.insets = opts.insets ?? { left: 0, right: 0, top: 0, bottom: 0 };
  if (opts.autoFit !== null) shape.text.autoFit = opts.autoFit ?? "shrinkText";
  if (opts.alignment) shape.text.alignment = opts.alignment;
  if (opts.verticalAlignment) shape.text.verticalAlignment = opts.verticalAlignment;
  return shape;
}

function addPanel(slide, position, opts = {}) {
  return slide.shapes.add({
    geometry: "roundRect",
    position,
    adjustmentList: [{ name: "adj", formula: "val 13000" }],
    fill: opts.fill ?? COLORS.panel,
    line: opts.line ?? { style: "solid", fill: COLORS.line, width: 1 },
  });
}

function addTitle(slide, title, subtitle) {
  slide.background.fill = COLORS.bg;
  addText(slide, title, { left: 52, top: 32, width: 820, height: 42 }, {
    typeface: FONT.title,
    fontSize: 30,
    bold: true,
  });
  if (subtitle) {
    addText(slide, subtitle, { left: 54, top: 78, width: 835, height: 30 }, {
      fontSize: 14.5,
      color: COLORS.muted,
    });
  }
}

function addMetric(slide, x, y, w, h, label, value, color, note = "") {
  addPanel(slide, { left: x, top: y, width: w, height: h });
  slide.shapes.add({
    geometry: "roundRect",
    position: { left: x, top: y, width: 7, height: h },
    adjustmentList: [{ name: "adj", formula: "val 13000" }],
    fill: color,
    line: { width: 0, fill: color },
  });
  addText(slide, label, { left: x + 18, top: y + 14, width: w - 28, height: 20 }, {
    fontSize: 10.5,
    color,
    bold: true,
  });
  addText(slide, value, { left: x + 18, top: y + 40, width: w - 30, height: 40 }, {
    fontSize: 31,
    bold: true,
    color: COLORS.ink,
  });
  if (note) {
    addText(slide, note, { left: x + 18, top: y + 82, width: w - 28, height: h - 92 }, {
      fontSize: 10.5,
      color: COLORS.muted,
      autoFit: null,
    });
  }
}

function leanPill(slide, lean, x, y, w = 76, h = 18) {
  const color = LEAN_COLORS[lean] ?? COLORS.slate;
  slide.shapes.add({
    geometry: "roundRect",
    position: { left: x, top: y, width: w, height: h },
    adjustmentList: [{ name: "adj", formula: "val 50000" }],
    fill: `${color}22`,
    line: { style: "solid", fill: `${color}66`, width: 1 },
  });
  addText(slide, lean, { left: x, top: y + 2, width: w, height: h - 3 }, {
    fontSize: 9.2,
    color,
    bold: true,
    alignment: "center",
    verticalAlignment: "middle",
    autoFit: null,
  });
}

function addFooter(slide, text) {
  addText(
    slide,
    text,
    { left: 70, top: 512, width: 820, height: 16 },
    { fontSize: 9.4, color: COLORS.muted, alignment: "center" },
  );
}

function pct(n) {
  return `${Number(n).toFixed(1)}%`;
}

function resultLanguageSlide(slide, finalSummary, finalAgreement) {
  clearSlide(slide);
  addTitle(
    slide,
    "Result 1: language shifts political lean without perturbation",
    "225 original statements were evaluated in 10 language versions by Codex gpt-5.4-mini and Gemma 4.",
  );

  addMetric(slide, 54, 124, 190, 116, "CODEX LANGUAGE STABILITY", "53.8%", COLORS.blue, "Statements keeping the same lean across all 10 translations.");
  addMetric(slide, 264, 124, 190, 116, "GEMMA LANGUAGE STABILITY", "25.3%", COLORS.amber, "Gemma shows more language-driven label movement.");
  addMetric(slide, 474, 124, 190, 116, "MODEL AGREEMENT", "64.6%", COLORS.teal, "Same language + same statement, Codex vs. Gemma.");

  addPanel(slide, { left: 54, top: 266, width: 852, height: 220 }, {
    fill: "#FFFFFF",
    line: { style: "solid", fill: "#D7E1EC", width: 1 },
  });
  addText(slide, "Dominant political lean by language", { left: 78, top: 286, width: 320, height: 20 }, {
    fontSize: 16,
    bold: true,
  });
  addText(slide, "Codex alternates between Lib-Left and Centrist; Gemma is mostly Lib-Left but with lower cross-language stability.", {
    left: 78,
    top: 310,
    width: 720,
    height: 22,
  }, {
    fontSize: 11.5,
    color: COLORS.muted,
  });

  const languages = [
    "English",
    "Hindi",
    "Simplified Mandarin",
    "French",
    "Russian",
    "Arabic",
    "Farsi",
    "Amharic",
    "Spain Spanish",
    "Latin American Spanish",
  ];
  const byKey = new Map(finalSummary.map((r) => [`${r.model}|${r.language}`, r]));
  const agreeByLanguage = new Map(finalAgreement.map((r) => [r.language, r.model_agreement_pct]));
  const startY = 350;
  addText(slide, "Language", { left: 78, top: 334, width: 160, height: 16 }, { fontSize: 10, color: COLORS.muted, bold: true });
  addText(slide, "Codex", { left: 238, top: 334, width: 80, height: 16 }, { fontSize: 10, color: COLORS.muted, bold: true, alignment: "center" });
  addText(slide, "Gemma", { left: 336, top: 334, width: 80, height: 16 }, { fontSize: 10, color: COLORS.muted, bold: true, alignment: "center" });
  addText(slide, "Agreement", { left: 434, top: 334, width: 90, height: 16 }, { fontSize: 10, color: COLORS.muted, bold: true, alignment: "center" });
  for (let i = 0; i < languages.length; i += 1) {
    const y = startY + i * 12.8;
    const lang = languages[i];
    addText(slide, lang, { left: 78, top: y - 2, width: 150, height: 14 }, { fontSize: 9.1, color: COLORS.ink, autoFit: null });
    leanPill(slide, byKey.get(`Codex gpt-5.4-mini|${lang}`)?.dominant_lean ?? "", 242, y - 2, 72, 14);
    leanPill(slide, byKey.get(`Gemma 4|${lang}`)?.dominant_lean ?? "", 340, y - 2, 72, 14);
    addText(slide, pct(agreeByLanguage.get(lang) ?? 0), { left: 448, top: y - 2, width: 54, height: 14 }, {
      fontSize: 9.3,
      color: COLORS.ink,
      bold: true,
      alignment: "center",
      autoFit: null,
    });
  }

  addPanel(slide, { left: 590, top: 334, width: 278, height: 112 }, {
    fill: "#EFF6FF",
    line: { style: "solid", fill: "#BFDBFE", width: 1 },
  });
  addText(slide, "Lowest model agreement", { left: 612, top: 354, width: 190, height: 20 }, {
    fontSize: 15,
    bold: true,
    color: COLORS.blue,
  });
  addText(slide, "Amharic 54.7%\nSimplified Mandarin 57.8%\nFarsi 59.6%", {
    left: 612,
    top: 382,
    width: 210,
    height: 52,
  }, {
    fontSize: 13,
    color: COLORS.ink,
    autoFit: null,
  });
  addFooter(slide, "No-perturbation results: 225 statements x 10 languages x 2 models | Political lean categories use the five-class compass.");
}

function resultPerturbationSlide(slide, perturbAgreement) {
  clearSlide(slide);
  addTitle(
    slide,
    "Result 2: perturbations amplify political-lean disagreement",
    "Agreement is measured on rows where both models produced a parseable political-lean label for the same language, statement, and perturbation.",
  );

  addMetric(slide, 54, 122, 190, 110, "CODEX PERTURBATION STABILITY", "13.6%", COLORS.blue, "Average share of statements stable across all 14 perturbations.");
  addMetric(slide, 264, 122, 190, 110, "GEMMA PERTURBATION STABILITY", "6.3%", COLORS.amber, "Gemma varies even more under prompt perturbation.");
  addMetric(slide, 474, 122, 190, 110, "MODEL AGREEMENT", "59.5%", COLORS.teal, "Cross-model agreement falls when prompt form changes.");

  addPanel(slide, { left: 54, top: 258, width: 852, height: 228 });
  addText(slide, "Cross-model agreement by perturbation type", { left: 78, top: 278, width: 360, height: 20 }, {
    fontSize: 16,
    bold: true,
  });
  const sorted = perturbAgreement
    .map((r) => ({ label: r.perturbation, value: Number(r.model_agreement_pct) }))
    .sort((a, b) => a.value - b.value);
  const x0 = 288;
  const y0 = 314;
  const maxW = 520;
  sorted.forEach((row, i) => {
    const y = y0 + i * 11.5;
    addText(slide, row.label, { left: 78, top: y - 1, width: 198, height: 12 }, {
      fontSize: 8.8,
      color: COLORS.ink,
      alignment: "right",
      autoFit: null,
    });
    slide.shapes.add({
      geometry: "rect",
      position: { left: x0, top: y, width: maxW * row.value / 100, height: 8 },
      fill: row.value < 55 ? COLORS.red : row.value < 62 ? COLORS.amber : COLORS.teal,
      line: { width: 0, fill: "#FFFFFF00" },
    });
    addText(slide, pct(row.value), { left: x0 + maxW * row.value / 100 + 6, top: y - 2, width: 46, height: 12 }, {
      fontSize: 8.5,
      color: COLORS.ink,
      bold: true,
      autoFit: null,
    });
  });
  addFooter(slide, "Perturbation agreement uses common rows with parseable lean | Codex perturbation has 9 languages because Amharic perturbation was unavailable.");
}

function outcomesSlide(slide) {
  clearSlide(slide);
  addTitle(
    slide,
    "Outcomes",
    "Political-lean labels change across language, perturbation, and model family.",
  );

  addPanel(slide, { left: 54, top: 128, width: 400, height: 132 });
  addText(slide, "Outcome 1", { left: 78, top: 150, width: 100, height: 16 }, {
    fontSize: 11,
    color: COLORS.blue,
    bold: true,
  });
  addText(slide, "Language is an evaluation variable", { left: 78, top: 174, width: 300, height: 30 }, {
    fontSize: 21,
    bold: true,
  });
  addText(slide, "Without perturbation, only 53.8% of Codex statements and 25.3% of Gemma statements stayed politically stable across all languages.", {
    left: 78,
    top: 216,
    width: 332,
    height: 34,
  }, {
    fontSize: 12,
    color: COLORS.muted,
    autoFit: null,
  });

  addPanel(slide, { left: 506, top: 128, width: 400, height: 132 });
  addText(slide, "Outcome 2", { left: 530, top: 150, width: 100, height: 16 }, {
    fontSize: 11,
    color: COLORS.red,
    bold: true,
  });
  addText(slide, "Perturbation exposes model-specific behavior", { left: 530, top: 174, width: 330, height: 30 }, {
    fontSize: 20,
    bold: true,
  });
  addText(slide, "Cross-model agreement drops to 59.5% under perturbations; Presupposition Loading is the strongest disagreement case.", {
    left: 530,
    top: 216,
    width: 340,
    height: 34,
  }, {
    fontSize: 12,
    color: COLORS.muted,
    autoFit: null,
  });

  addPanel(slide, { left: 54, top: 300, width: 852, height: 158 }, {
    fill: "#F1F5F9",
    line: { style: "solid", fill: "#CBD5E1", width: 1 },
  });
  addText(slide, "Core comparison metrics", { left: 78, top: 320, width: 300, height: 20 }, {
    fontSize: 16,
    bold: true,
  });
  const headers = ["Metric", "Codex", "Gemma", "Cross-model"];
  const rows = [
    ["Stable across 10 languages", "53.8%", "25.3%", "64.6% agree"],
    ["Stable across 14 perturbations", "13.6%", "6.3%", "59.5% agree"],
  ];
  const x = [78, 410, 550, 690];
  headers.forEach((h, i) => addText(slide, h, { left: x[i], top: 354, width: i === 0 ? 260 : 118, height: 18 }, {
    fontSize: 11,
    color: COLORS.muted,
    bold: true,
    alignment: i === 0 ? "left" : "center",
  }));
  rows.forEach((r, ri) => {
    const y = 382 + ri * 34;
    slide.shapes.add({
      geometry: "rect",
      position: { left: 76, top: y - 6, width: 790, height: 28 },
      fill: ri === 0 ? "#FFFFFF" : "#E2E8F0",
      line: { width: 0, fill: "#FFFFFF00" },
    });
    r.forEach((v, i) => addText(slide, v, { left: x[i], top: y, width: i === 0 ? 260 : 118, height: 18 }, {
      fontSize: 12.5,
      color: COLORS.ink,
      bold: i > 0,
      alignment: i === 0 ? "left" : "center",
      autoFit: null,
    }));
  });
  addFooter(slide, "Metrics compare political-lean labels; reference quadrant is a comparison label, not objective truth.");
}

function conclusionSlide(slide) {
  clearSlide(slide);
  addTitle(slide, "Conclusion", "");
  addText(slide, "Political-content moderation is shaped by language, perturbation, and model choice.", {
    left: 56,
    top: 104,
    width: 790,
    height: 70,
  }, {
    typeface: FONT.title,
    fontSize: 27,
    bold: true,
    color: COLORS.ink,
  });
  slide.shapes.add({
    geometry: "rect",
    position: { left: 56, top: 190, width: 850, height: 2 },
    fill: COLORS.line,
    line: { width: 0, fill: COLORS.line },
  });

  const cards = [
    {
      x: 56,
      color: COLORS.blue,
      title: "No single language is neutral",
      body: "Translated versions of the same statement can receive different political-lean labels, even before perturbation.",
    },
    {
      x: 336,
      color: COLORS.red,
      title: "No single prompt form is neutral",
      body: "Perturbations such as presupposition loading, colloquial wording, and loss framing change model agreement.",
    },
    {
      x: 616,
      color: COLORS.teal,
      title: "No single model is a baseline",
      body: "Codex and Gemma disagree on a substantial share of rows, so model family should be part of moderation audits.",
    },
  ];
  for (const card of cards) {
    addPanel(slide, { left: card.x, top: 226, width: 248, height: 166 });
    slide.shapes.add({
      geometry: "ellipse",
      position: { left: card.x + 22, top: 246, width: 26, height: 26 },
      fill: card.color,
      line: { width: 0, fill: card.color },
    });
    addText(slide, card.title, { left: card.x + 62, top: 242, width: 160, height: 40 }, {
      fontSize: 16,
      bold: true,
      color: COLORS.ink,
    });
    addText(slide, card.body, { left: card.x + 24, top: 300, width: 200, height: 70 }, {
      fontSize: 12.5,
      color: COLORS.muted,
      autoFit: null,
    });
  }
  addPanel(slide, { left: 86, top: 430, width: 788, height: 46 }, {
    fill: "#ECFDF5",
    line: { style: "solid", fill: "#A7F3D0", width: 1 },
  });
  addText(slide, "Presentation conclusion: multilingual political moderation should be evaluated across languages, perturbations, and model families before claiming neutrality.", {
    left: 120,
    top: 443,
    width: 720,
    height: 22,
  }, {
    fontSize: 12.5,
    color: COLORS.green,
    bold: true,
    alignment: "center",
  });
  addFooter(slide, "Use as a moderation/audit conclusion: evaluate across languages, perturbations, and model families.");
}

const [
  finalSummary,
  finalAgreement,
  perturbAgreement,
] = await Promise.all([
  loadCsv("final_language_summary_by_model.csv"),
  loadCsv("final_cross_model_agreement_by_language.csv"),
  loadCsv("perturbation_cross_model_agreement_by_type.csv"),
]);

const presentation = await PresentationFile.importPptx(await FileBlob.load(inputPath));
if (presentation.slides.count < 26) {
  throw new Error(`Expected at least 26 slides, found ${presentation.slides.count}`);
}

resultLanguageSlide(presentation.slides.getItem(19), finalSummary, finalAgreement);
resultPerturbationSlide(presentation.slides.getItem(21), perturbAgreement);
outcomesSlide(presentation.slides.getItem(24));
conclusionSlide(presentation.slides.getItem(25));

const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(outputPath);
console.log(outputPath);

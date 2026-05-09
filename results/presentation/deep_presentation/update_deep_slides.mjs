const { FileBlob, PresentationFile } = await import("@oai/artifact-tool");
const fs = await import("node:fs/promises");

const root = process.cwd().replaceAll("\\", "/");
const inputPath =
  `${root}/docs/presentations/Political Content Moderation Across Different Models and Languages - model comparison results.pptx`;
const outputPath =
  `${root}/docs/presentations/Political Content Moderation Across Different Models and Languages - deeper outcomes.pptx`;
const tableDir =
  `${root}/results/presentation/deep_presentation/tables`;

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
const MODEL_COLORS = {
  "Codex gpt-5.4-mini": COLORS.blue,
  "Gemma 4": COLORS.amber,
};
const LANGUAGE_ORDER = [
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
const LANGUAGE_LABELS = {
  English: "English",
  Hindi: "Hindi",
  "Simplified Mandarin": "Mandarin",
  French: "French",
  Russian: "Russian",
  Arabic: "Arabic",
  Farsi: "Farsi",
  Amharic: "Amharic",
  "Spain Spanish": "Spain Sp.",
  "Latin American Spanish": "LatAm Sp.",
};
const PERTURBATION_ORDER = [
  "Active Voice",
  "Passive Voice",
  "Open Ended",
  "Yes-No Forced Choice",
  "Presupposition Loading",
  "Embedded",
  "Direct",
  "Gain Framing",
  "Loss Framing",
  "Identity Change",
  "Formal",
  "Colloquial",
  "Hedged",
  "Assertive",
];
const PERTURBATION_LABELS = {
  "Active Voice": "Active",
  "Passive Voice": "Passive",
  "Open Ended": "Open",
  "Yes-No Forced Choice": "Yes/No",
  "Presupposition Loading": "Presupp.",
  Embedded: "Embedded",
  Direct: "Direct",
  "Gain Framing": "Gain",
  "Loss Framing": "Loss",
  "Identity Change": "Identity",
  Formal: "Formal",
  Colloquial: "Colloq.",
  Hedged: "Hedged",
  Assertive: "Assertive",
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
  addText(slide, title, { left: 52, top: 32, width: 840, height: 42 }, {
    typeface: FONT.title,
    fontSize: 29,
    bold: true,
  });
  if (subtitle) {
    addText(slide, subtitle, { left: 54, top: 78, width: 835, height: 30 }, {
      fontSize: 14,
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
  addText(slide, label, { left: x + 18, top: y + 13, width: w - 28, height: 17 }, {
    fontSize: 9.5,
    color,
    bold: true,
    autoFit: null,
  });
  addText(slide, value, { left: x + 18, top: y + 38, width: w - 30, height: 37 }, {
    fontSize: 30,
    bold: true,
    color: COLORS.ink,
  });
  if (note) {
    addText(slide, note, { left: x + 18, top: y + 78, width: w - 28, height: h - 86 }, {
      fontSize: 10,
      color: COLORS.muted,
      autoFit: null,
    });
  }
}

function addDefinition(slide, x, y, w, h) {
  addPanel(slide, { left: x, top: y, width: w, height: h }, {
    fill: "#EFF6FF",
    line: { style: "solid", fill: "#BFDBFE", width: 1 },
  });
  addText(slide, "Definitions", { left: x + 18, top: y + 14, width: w - 36, height: 18 }, {
    fontSize: 13,
    bold: true,
    color: COLORS.blue,
  });
  addText(
    slide,
    "Shifted lean: the political-compass label changes for the same statement.\nControversy: 1-5 rating of how socially/politically contentious the statement is; it is not agreement.",
    { left: x + 18, top: y + 39, width: w - 36, height: h - 48 },
    { fontSize: 10.8, color: COLORS.ink, autoFit: null },
  );
}

function addFooter(slide, text) {
  addText(slide, text, { left: 70, top: 512, width: 820, height: 16 }, {
    fontSize: 9.2,
    color: COLORS.muted,
    alignment: "center",
    autoFit: null,
  });
}

function seriesValues(rows, model, keyField, order, valueField) {
  const map = new Map(rows.filter((r) => r.model === model).map((r) => [r[keyField], Number(r[valueField])]));
  return order.map((key) => map.get(key) ?? 0);
}

function svgEscape(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function compactLineChartDataUrl({ categories, codexValues, gemmaValues, yMax }) {
  const w = 760;
  const h = 210;
  const left = 54;
  const top = 22;
  const chartW = 660;
  const chartH = 120;
  const xStep = chartW / (categories.length - 1);
  const parts = [`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">`];
  parts.push(`<rect width="100%" height="100%" fill="#FFFFFF"/>`);
  for (let tick = 0; tick <= yMax; tick += 10) {
    const y = top + chartH - chartH * tick / yMax;
    parts.push(`<line x1="${left}" y1="${y}" x2="${left + chartW}" y2="${y}" stroke="#E2E8F0"/>`);
    parts.push(`<text x="${left - 10}" y="${y + 4}" font-family="Arial" font-size="11" fill="#64748B" text-anchor="end">${tick}</text>`);
  }
  function addSeries(values, color, label, labelY) {
    const pts = values.map((v, i) => {
      const x = left + i * xStep;
      const y = top + chartH - chartH * v / yMax;
      return [x, y, v];
    });
    parts.push(`<polyline points="${pts.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ")}" fill="none" stroke="${color}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>`);
    for (const [x, y] of pts) {
      parts.push(`<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="4" fill="#FFFFFF" stroke="${color}" stroke-width="3"/>`);
    }
    parts.push(`<rect x="${left + chartW - 150}" y="${labelY - 10}" width="22" height="5" rx="2.5" fill="${color}"/>`);
    parts.push(`<text x="${left + chartW - 120}" y="${labelY - 5}" font-family="Arial" font-size="12" fill="#334155" font-weight="700">${svgEscape(label)}</text>`);
  }
  addSeries(codexValues, COLORS.blue, "Codex gpt-5.4-mini", 24);
  addSeries(gemmaValues, COLORS.amber, "Gemma 4", 44);
  categories.forEach((label, i) => {
    const x = left + i * xStep;
    parts.push(`<text x="${x}" y="${top + chartH + 22}" font-family="Arial" font-size="10" fill="#475569" text-anchor="middle">${svgEscape(label)}</text>`);
  });
  parts.push(`<text x="${left}" y="${h - 14}" font-family="Arial" font-size="11" fill="#64748B">Shifted lean rate (%)</text>`);
  parts.push(`</svg>`);
  return `data:image/svg+xml;base64,${Buffer.from(parts.join(""), "utf-8").toString("base64")}`;
}

function addLineChartImage(slide, opts) {
  const image = slide.images.add({
    dataUrl: compactLineChartDataUrl(opts),
    fit: "contain",
    alt: "Line chart of shifted political lean rate",
  });
  image.position = {
    left: opts.left,
    top: opts.top,
    width: opts.width,
    height: opts.height,
  };
}

function translationSlide(slide, languageShift, summary) {
  clearSlide(slide);
  addTitle(
    slide,
    "Result 1: translation changes political-lean labels",
    "Shifted lean is measured against each model's English label for the same source statement.",
  );
  addMetric(slide, 54, 116, 176, 104, "CODEX AVG SHIFT", "19.5%", COLORS.blue, "Non-English translations vs. English baseline.");
  addMetric(slide, 250, 116, 176, 104, "GEMMA AVG SHIFT", "34.8%", COLORS.amber, "Gemma is more sensitive to translation.");
  addMetric(slide, 446, 116, 176, 104, "LARGEST GAP", "Amharic", COLORS.teal, "Gemma shifts 42.2%; Codex shifts 20.0%.");
  addDefinition(slide, 642, 116, 264, 104);

  addPanel(slide, { left: 54, top: 250, width: 852, height: 236 });
  addText(slide, "Shifted lean rate by language", { left: 78, top: 270, width: 320, height: 20 }, {
    fontSize: 16,
    bold: true,
  });
  addText(slide, "Line chart: % of statements whose translated label differs from English baseline.", {
    left: 78,
    top: 294,
    width: 520,
    height: 18,
  }, {
    fontSize: 11,
    color: COLORS.muted,
  });
  addLineChartImage(slide, {
    left: 86,
    top: 316,
    width: 560,
    height: 150,
    categories: LANGUAGE_ORDER.map((l) => LANGUAGE_LABELS[l]),
    codexValues: seriesValues(languageShift, "Codex gpt-5.4-mini", "language", LANGUAGE_ORDER, "shifted_lean_rate_pct"),
    gemmaValues: seriesValues(languageShift, "Gemma 4", "language", LANGUAGE_ORDER, "shifted_lean_rate_pct"),
    yMax: 50,
  });
  addPanel(slide, { left: 680, top: 315, width: 190, height: 116 }, {
    fill: "#FFF7ED",
    line: { style: "solid", fill: "#FED7AA", width: 1 },
  });
  addText(slide, "Interpretation", { left: 700, top: 334, width: 150, height: 18 }, {
    fontSize: 14,
    bold: true,
    color: COLORS.amber,
  });
  addText(
    slide,
    "Gemma shifts more in every non-English language. Farsi is Codex's largest shift; Amharic is Gemma's largest shift. A possible reason is uneven language-resource coverage plus different political vocabulary and cultural context.",
    { left: 700, top: 360, width: 148, height: 58 },
    { fontSize: 9.7, color: COLORS.ink, autoFit: null },
  );
  addFooter(slide, "Translation result uses 10 language columns. English is shown as the 0% baseline.");
}

function perturbationSlide(slide, perturbationShift) {
  clearSlide(slide);
  addTitle(
    slide,
    "Result 2: perturbation effects are uneven",
    "Shifted lean is measured against the majority lean across 14 perturbations for the same model, language, and statement.",
  );
  addMetric(slide, 54, 116, 176, 104, "CODEX AVG SHIFT", "23.9%", COLORS.blue, "Max: Open Ended 40.1%; min: Active Voice 15.6%.");
  addMetric(slide, 250, 116, 176, 104, "GEMMA AVG SHIFT", "30.7%", COLORS.amber, "Max: Open Ended 47.3%; min: Active Voice 17.3%.");
  addMetric(slide, 446, 116, 176, 104, "MODEL AGREEMENT", "59.5%", COLORS.teal, "Codex and Gemma agree less under perturbation.");
  addDefinition(slide, 642, 116, 264, 104);

  addPanel(slide, { left: 54, top: 250, width: 852, height: 236 });
  addText(slide, "Shifted lean rate by perturbation", { left: 78, top: 270, width: 320, height: 20 }, {
    fontSize: 16,
    bold: true,
  });
  addText(slide, "Line chart: % of rows whose perturbation label differs from the local majority label.", {
    left: 78,
    top: 294,
    width: 570,
    height: 18,
  }, {
    fontSize: 11,
    color: COLORS.muted,
  });
  addLineChartImage(slide, {
    left: 82,
    top: 316,
    width: 600,
    height: 152,
    categories: PERTURBATION_ORDER.map((p) => PERTURBATION_LABELS[p]),
    codexValues: seriesValues(perturbationShift, "Codex gpt-5.4-mini", "perturbation", PERTURBATION_ORDER, "shifted_lean_rate_pct"),
    gemmaValues: seriesValues(perturbationShift, "Gemma 4", "perturbation", PERTURBATION_ORDER, "shifted_lean_rate_pct"),
    yMax: 55,
  });
  addPanel(slide, { left: 708, top: 315, width: 162, height: 116 }, {
    fill: "#FFF1F2",
    line: { style: "solid", fill: "#FECDD3", width: 1 },
  });
  addText(slide, "Pattern", { left: 726, top: 334, width: 120, height: 18 }, {
    fontSize: 14,
    bold: true,
    color: COLORS.red,
  });
  addText(
    slide,
    "Open-ended, loss-framed, hedged, and presupposition-loaded wording shifts labels most. Active voice shifts least because it preserves the original stance most directly.",
    { left: 726, top: 360, width: 122, height: 58 },
    { fontSize: 9.5, color: COLORS.ink, autoFit: null },
  );
  addFooter(slide, "Perturbation result uses 14 prompt variants. Codex lacks Amharic perturbation workbook, so model agreement uses common parseable rows.");
}

function outcomesSlide(slide) {
  clearSlide(slide);
  addTitle(slide, "Deeper Outcomes", "The effect is not only that labels change; the changes have structure.");
  const cards = [
    {
      x: 54,
      y: 126,
      w: 266,
      color: COLORS.blue,
      label: "Outcome 1: language trend",
      title: "Translation has directional effects",
      body:
        "Gemma shifts more than Codex in every non-English language. Codex peaks in Farsi (23.6%); Gemma peaks in Amharic (42.2%). Possible reason: uneven language-resource coverage and language-specific political vocabulary.",
    },
    {
      x: 346,
      y: 126,
      w: 266,
      color: COLORS.red,
      label: "Outcome 2: perturbation trend",
      title: "Prompt form changes inferred stance",
      body:
        "Open-ended framing is the largest shift for both models: Codex 40.1%, Gemma 47.3%. Active voice is lowest because it keeps the semantic stance closest to the original.",
    },
    {
      x: 638,
      y: 126,
      w: 266,
      color: COLORS.teal,
      label: "Outcome 3: model difference",
      title: "Gemma is more sensitive overall",
      body:
        "Gemma has higher average translation shift (34.8% vs. 19.5%) and higher perturbation shift (30.7% vs. 23.9%). Codex is more stable but still not neutral.",
    },
  ];
  for (const card of cards) {
    addPanel(slide, { left: card.x, top: card.y, width: card.w, height: 220 });
    slide.shapes.add({
      geometry: "roundRect",
      position: { left: card.x, top: card.y, width: 7, height: 220 },
      adjustmentList: [{ name: "adj", formula: "val 13000" }],
      fill: card.color,
      line: { width: 0, fill: card.color },
    });
    addText(slide, card.label, { left: card.x + 20, top: card.y + 20, width: card.w - 34, height: 18 }, {
      fontSize: 10.5,
      color: card.color,
      bold: true,
      autoFit: null,
    });
    addText(slide, card.title, { left: card.x + 20, top: card.y + 50, width: card.w - 34, height: 42 }, {
      fontSize: 18,
      bold: true,
    });
    addText(slide, card.body, { left: card.x + 20, top: card.y + 108, width: card.w - 36, height: 82 }, {
      fontSize: 10.7,
      color: COLORS.muted,
      autoFit: null,
    });
  }
  addPanel(slide, { left: 84, top: 386, width: 792, height: 72 }, {
    fill: "#F1F5F9",
    line: { style: "solid", fill: "#CBD5E1", width: 1 },
  });
  addText(slide, "How to say this in the presentation", { left: 108, top: 406, width: 260, height: 18 }, {
    fontSize: 14,
    bold: true,
  });
  addText(
    slide,
    "Translation changes the semantic context the model uses; perturbation changes the pragmatic frame. Gemma reacts more strongly to both, while Codex is more stable but still shifts enough to reject a single-language/single-prompt baseline.",
    { left: 108, top: 430, width: 716, height: 22 },
    { fontSize: 11.5, color: COLORS.ink, autoFit: null },
  );
  addFooter(slide, "Outcome metrics are shifted-lean rates; controversy is separate and measures contentiousness, not stance.");
}

function conclusionSlide(slide) {
  clearSlide(slide);
  addTitle(slide, "Conclusion", "Two-level interpretation for the final presentation.");
  addPanel(slide, { left: 56, top: 124, width: 396, height: 250 });
  addText(slide, "1. Translation and perturbation affect judgment", { left: 84, top: 152, width: 320, height: 38 }, {
    fontSize: 21,
    bold: true,
    color: COLORS.blue,
  });
  addText(
    slide,
    "Translation is not only a preprocessing step. It can move political lean because language carries different cultural cues, political vocabulary, and model-training coverage.\n\nPerturbation is not only wording noise. Open-ended, loss-framed, hedged, and presupposition-loaded prompts change the implied stance and therefore change the model's label.",
    { left: 84, top: 210, width: 320, height: 128 },
    { fontSize: 12.3, color: COLORS.ink, autoFit: null },
  );

  addPanel(slide, { left: 508, top: 124, width: 396, height: 250 });
  addText(slide, "2. Model choice changes the result", { left: 536, top: 152, width: 320, height: 38 }, {
    fontSize: 21,
    bold: true,
    color: COLORS.teal,
  });
  addText(
    slide,
    "Gemma is more sensitive to both translation and perturbation, showing larger shifted-lean rates. Codex is comparatively more stable, but still shifts across languages and prompt forms.\n\nTherefore, one model should not be treated as a neutral baseline for multilingual political moderation.",
    { left: 536, top: 210, width: 320, height: 128 },
    { fontSize: 12.3, color: COLORS.ink, autoFit: null },
  );

  addPanel(slide, { left: 92, top: 414, width: 776, height: 54 }, {
    fill: "#ECFDF5",
    line: { style: "solid", fill: "#A7F3D0", width: 1 },
  });
  addText(
    slide,
    "Final claim: multilingual political moderation should be audited across model families, languages, and perturbation styles before claiming neutrality or fairness.",
    { left: 128, top: 430, width: 704, height: 24 },
    { fontSize: 13, color: COLORS.green, bold: true, alignment: "center" },
  );
  addFooter(slide, "This is deeper than a simple accuracy claim: it identifies which variables systematically reshape political-lean judgments.");
}

const [languageShift, perturbationShift] = await Promise.all([
  loadCsv("language_translation_shift_from_english.csv"),
  loadCsv("perturbation_shift_from_majority.csv"),
]);

const presentation = await PresentationFile.importPptx(await FileBlob.load(inputPath));
if (presentation.slides.count < 26) throw new Error(`Expected at least 26 slides, found ${presentation.slides.count}`);

translationSlide(presentation.slides.getItem(19), languageShift);
perturbationSlide(presentation.slides.getItem(21), perturbationShift);
outcomesSlide(presentation.slides.getItem(24));
conclusionSlide(presentation.slides.getItem(25));

const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(outputPath);
console.log(outputPath);

const { FileBlob, PresentationFile } = await import(
  "file:///C:/Users/Yi%20Ping/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs"
);
const fs = await import("node:fs/promises");

const root = process.cwd().replaceAll("\\", "/");
const deckPath =
  `${root}/docs/presentations/Political Content Moderation Across Different Models and Languages.pptx`;
const backupPath =
  `${root}/results/presentation/final_presentation_update/Political Content Moderation Across Different Models and Languages - before final outcome update.pptx`;
const previewDir =
  `${root}/results/presentation/final_presentation_update/previews`;

const FONT = { title: "Poppins", body: "Lato" };
const COLORS = {
  bg: "#F1F9F3",
  panel: "#FFFFFF",
  panelSoft: "#E6F2EA",
  ink: "#183226",
  muted: "#4E6758",
  line: "#8FA99A",
  lightLine: "#B8CDBF",
  green: "#15803D",
  blue: "#2563EB",
  amber: "#B7791F",
  red: "#BE123C",
  teal: "#0F766E",
  purple: "#7C3AED",
};

async function ensureBackup() {
  try {
    await fs.access(backupPath);
  } catch {
    await fs.copyFile(deckPath, backupPath);
  }
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
    adjustmentList: [{ name: "adj", formula: "val 12000" }],
    fill: opts.fill ?? COLORS.panel,
    line: opts.line ?? { style: "solid", fill: COLORS.lightLine, width: 1.2 },
  });
}

function addTitle(slide, kicker, title, subtitle = "") {
  slide.background.fill = COLORS.bg;
  addText(slide, kicker.toUpperCase(), { left: 56, top: 34, width: 240, height: 18 }, {
    fontSize: 11,
    bold: true,
    color: COLORS.green,
    autoFit: null,
  });
  addText(slide, title, { left: 54, top: 58, width: 820, height: 54 }, {
    typeface: FONT.title,
    fontSize: 31,
    bold: true,
    color: COLORS.ink,
  });
  if (subtitle) {
    addText(slide, subtitle, { left: 56, top: 111, width: 800, height: 26 }, {
      fontSize: 13.5,
      color: COLORS.muted,
      autoFit: null,
    });
  }
}

function addMetric(slide, x, y, label, value, color) {
  addText(slide, value, { left: x, top: y, width: 114, height: 36 }, {
    fontSize: 28,
    bold: true,
    color,
    alignment: "center",
    autoFit: null,
  });
  addText(slide, label, { left: x - 10, top: y + 38, width: 134, height: 28 }, {
    fontSize: 9.6,
    color: COLORS.muted,
    bold: true,
    alignment: "center",
    autoFit: null,
  });
}

function addOutcomeCard(slide, x, y, w, h, marker, headline, body, color) {
  addPanel(slide, { left: x, top: y, width: w, height: h }, {
    fill: COLORS.panel,
    line: { style: "solid", fill: COLORS.lightLine, width: 1.2 },
  });
  slide.shapes.add({
    geometry: "roundRect",
    position: { left: x, top: y, width: 7, height: h },
    adjustmentList: [{ name: "adj", formula: "val 12000" }],
    fill: color,
    line: { width: 0, fill: color },
  });
  addText(slide, marker, { left: x + 22, top: y + 20, width: 100, height: 16 }, {
    fontSize: 10.5,
    color,
    bold: true,
    autoFit: null,
  });
  addText(slide, headline, { left: x + 22, top: y + 48, width: w - 44, height: 40 }, {
    fontSize: 18,
    bold: true,
    color: COLORS.ink,
  });
  addText(slide, body, { left: x + 22, top: y + 102, width: w - 44, height: h - 120 }, {
    fontSize: 10.8,
    color: COLORS.muted,
    autoFit: null,
  });
}

function addConclusionBand(slide, y, label, title, body, color) {
  addPanel(slide, { left: 78, top: y, width: 804, height: 128 }, {
    fill: COLORS.panel,
    line: { style: "solid", fill: COLORS.lightLine, width: 1.2 },
  });
  slide.shapes.add({
    geometry: "ellipse",
    position: { left: 104, top: y + 26, width: 34, height: 34 },
    fill: color,
    line: { width: 0, fill: color },
  });
  addText(slide, label, { left: 104, top: y + 35, width: 34, height: 16 }, {
    fontSize: 12,
    bold: true,
    color: "#FFFFFF",
    alignment: "center",
    autoFit: null,
  });
  addText(slide, title, { left: 158, top: y + 24, width: 620, height: 28 }, {
    fontSize: 20,
    bold: true,
    color: COLORS.ink,
    autoFit: null,
  });
  addText(slide, body, { left: 158, top: y + 62, width: 665, height: 48 }, {
    fontSize: 12.3,
    color: COLORS.muted,
    autoFit: null,
  });
}

function addFooter(slide, text) {
  addText(slide, text, { left: 68, top: 512, width: 824, height: 16 }, {
    fontSize: 9.2,
    color: COLORS.muted,
    alignment: "center",
    autoFit: null,
  });
}

function outcomesSlide(slide) {
  clearSlide(slide);
  addTitle(
    slide,
    "Outcomes",
    "The shifts are structured, not just noisy",
    "Translation, prompt framing, and model family each reshape political-lean judgments.",
  );

  addOutcomeCard(
    slide,
    54,
    160,
    266,
    196,
    "OUTCOME 1",
    "Translation acts like an evaluation variable",
    "Gemma shifts more than Codex in every non-English language. Under the shifted-row standard, French is consistently Lib-Right and Russian is consistently Lib-Left across both models.",
    COLORS.blue,
  );
  addOutcomeCard(
    slide,
    347,
    160,
    266,
    196,
    "OUTCOME 2",
    "Framing changes the stance the model reads",
    "Open-ended wording creates the largest shift for both models, while active voice creates the smallest. Several perturbations move both models toward Centrist or Lib-Left.",
    COLORS.red,
  );
  addOutcomeCard(
    slide,
    640,
    160,
    266,
    196,
    "OUTCOME 3",
    "Model family changes the result",
    "Gemma is more sensitive overall. Codex is comparatively stable, but under perturbation its dominant shifts are left or centrist, never right.",
    COLORS.teal,
  );

  addPanel(slide, { left: 84, top: 392, width: 792, height: 80 }, {
    fill: COLORS.panelSoft,
    line: { style: "solid", fill: COLORS.line, width: 1.2 },
  });
  addMetric(slide, 112, 404, "Codex avg translation shift", "19.5%", COLORS.blue);
  addMetric(slide, 272, 404, "Gemma avg translation shift", "34.8%", COLORS.amber);
  addMetric(slide, 432, 404, "Codex avg perturbation shift", "23.9%", COLORS.blue);
  addMetric(slide, 592, 404, "Gemma avg perturbation shift", "30.7%", COLORS.amber);
  addFooter(slide, "Shifted lean = label changes for the same underlying statement; model agreement is exact political-lean label match.");
}

function conclusionSlide(slide) {
  clearSlide(slide);
  addTitle(
    slide,
    "Conclusion",
    "Neutrality has to be audited, not assumed",
    "The same political content can be recoded when language, framing, or model family changes.",
  );

  addConclusionBand(
    slide,
    158,
    "1",
    "Translation and perturbation are not neutral transformations",
    "Translation can change the cultural and lexical cues a model uses. Perturbation changes the pragmatic frame: open-ended, hedged, formal, and loss-framed versions can move the same statement into different political-lean categories.",
    COLORS.blue,
  );
  addConclusionBand(
    slide,
    306,
    "2",
    "Codex and Gemma should not be treated as interchangeable judges",
    "Gemma shows larger shifted-lean rates, while Codex is more stable but systematically left/centrist under perturbation. The model itself is part of the moderation behavior being measured.",
    COLORS.teal,
  );

  addPanel(slide, { left: 118, top: 458, width: 724, height: 38 }, {
    fill: "#FFFFFF",
    line: { style: "solid", fill: COLORS.line, width: 1.2 },
  });
  addText(
    slide,
    "Final claim: multilingual political moderation should be evaluated across languages, perturbation styles, and model families before claiming fairness or neutrality.",
    { left: 146, top: 468, width: 668, height: 18 },
    { fontSize: 11.4, color: COLORS.green, bold: true, alignment: "center", autoFit: null },
  );
  addFooter(slide, "Result pages carry the evidence; this closing section states the implication for moderation audits.");
}

await fs.mkdir(previewDir, { recursive: true });
await ensureBackup();

const presentation = await PresentationFile.importPptx(await FileBlob.load(deckPath));
if (presentation.slides.count < 26) {
  throw new Error(`Expected at least 26 slides, found ${presentation.slides.count}`);
}

outcomesSlide(presentation.slides.getItem(24));
conclusionSlide(presentation.slides.getItem(25));

const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(deckPath);

for (const index of [24, 25]) {
  const slide = presentation.slides.getItem(index);
  const png = await presentation.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(`${previewDir}/preview_slide_${index + 1}.png`, Buffer.from(await png.arrayBuffer()));
}

console.log(deckPath);
console.log(backupPath);

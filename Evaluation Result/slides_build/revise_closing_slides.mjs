const { FileBlob, PresentationFile } = await import("@oai/artifact-tool");

const inputPath =
  "E:/CourseProject/cs4501_26spring_final_project/Political Content Moderation Across Different Models and Languages.pptx";
const outputPath =
  "E:/CourseProject/cs4501_26spring_final_project/Evaluation Result/Political Content Moderation Across Different Models and Languages - revised results v2.pptx";

const W = 960;
const H = 540;
const COLORS = {
  ink: "#1F2937",
  muted: "#64748B",
  line: "#CBD5E1",
  bg: "#F8FAFC",
  panel: "#FFFFFF",
  blue: "#2563EB",
  teal: "#0F766E",
  amber: "#B45309",
  red: "#BE123C",
  green: "#15803D",
};
const FONT = {
  title: "Poppins",
  body: "Lato",
};

const presentation = await PresentationFile.importPptx(await FileBlob.load(inputPath));

function clearSlide(slide) {
  const shapes = [...(slide.shapes.items ?? [])];
  for (const shape of shapes) shape.delete();
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
  shape.text.fontSize = opts.fontSize ?? 24;
  shape.text.color = opts.color ?? COLORS.ink;
  shape.text.bold = opts.bold ?? false;
  shape.text.insets = opts.insets ?? { left: 0, right: 0, top: 0, bottom: 0 };
  if (opts.autoFit !== null) {
    shape.text.autoFit = opts.autoFit ?? "shrinkText";
  }
  if (opts.alignment) shape.text.alignment = opts.alignment;
  if (opts.verticalAlignment) shape.text.verticalAlignment = opts.verticalAlignment;
  return shape;
}

function addPanel(slide, position, opts = {}) {
  return slide.shapes.add({
    geometry: "roundRect",
    position,
    adjustmentList: [{ name: "adj", formula: "val 16667" }],
    fill: opts.fill ?? COLORS.panel,
    line: opts.line ?? { style: "solid", fill: COLORS.line, width: 1 },
  });
}

function addMetricCard(slide, { x, y, w, h, accent, eyebrow, metric, title, detail }) {
  addPanel(slide, { left: x, top: y, width: w, height: h });
  slide.shapes.add({
    geometry: "roundRect",
    position: { left: x, top: y, width: 8, height: h },
    adjustmentList: [{ name: "adj", formula: "val 16667" }],
    fill: accent,
    line: { width: 0, fill: accent },
  });
  addText(slide, eyebrow, { left: x + 24, top: y + 20, width: w - 42, height: 22 }, {
    fontSize: 13,
    bold: true,
    color: accent,
  });
  addText(slide, metric, { left: x + 24, top: y + 48, width: 132, height: 58 }, {
    fontSize: 42,
    bold: true,
    color: COLORS.ink,
  });
  addText(slide, title, { left: x + 160, top: y + 54, width: w - 184, height: 48 }, {
    fontSize: 21,
    bold: true,
    color: COLORS.ink,
  });
  addText(slide, detail, { left: x + 24, top: y + 108, width: w - 48, height: h - 118 }, {
    fontSize: 10.8,
    color: COLORS.muted,
    autoFit: null,
  });
}

function addFooter(slide) {
  addText(
    slide,
    "Codex judge: gpt-5.4-mini via Codex OAuth | Completed: 2,250 final multilingual rows + 28,350 perturbation rows | No token/quota refusal",
    { left: 70, top: 508, width: 820, height: 18 },
    { fontSize: 10.5, color: COLORS.muted, alignment: "center" },
  );
}

function addTinyDivider(slide, x, y, w, color = COLORS.line) {
  slide.shapes.add({
    geometry: "rect",
    position: { left: x, top: y, width: w, height: 2 },
    fill: color,
    line: { width: 0, fill: color },
  });
}

function buildOutcomes(slide) {
  clearSlide(slide);
  slide.background.fill = COLORS.bg;
  addText(slide, "Outcomes", { left: 56, top: 42, width: 380, height: 54 }, {
    typeface: FONT.title,
    fontSize: 36,
    bold: true,
  });
  addText(
    slide,
    "The same political content is not evaluated identically after translation or perturbation changes.",
    { left: 58, top: 96, width: 770, height: 34 },
    { fontSize: 17, color: COLORS.muted },
  );

  addMetricCard(slide, {
    x: 58,
    y: 150,
    w: 400,
    h: 144,
    accent: COLORS.blue,
    eyebrow: "OUTCOME 1: LANGUAGE EFFECT",
    metric: "53.8%",
    title: "stable across 10 languages",
    detail:
      "121 / 225 base statements kept one lean across all translations.\nAverage unique labels per statement = 1.62.",
  });

  addMetricCard(slide, {
    x: 502,
    y: 150,
    w: 400,
    h: 144,
    accent: COLORS.red,
    eyebrow: "OUTCOME 2: PERTURBATION EFFECT",
    metric: "13.6%",
    title: "stable across 14 perturbations",
    detail:
      "Average statement produced 2.42 distinct lean labels.\nOpen-ended, loss-framed, and hedged prompts shifted labels most.",
  });

  addPanel(slide, { left: 58, top: 320, width: 844, height: 160 }, {
    fill: "#EEF6FF",
    line: { style: "solid", fill: "#BFDBFE", width: 1 },
  });
  addText(slide, "Stability drops sharply when perturbation is varied", {
    left: 82,
    top: 340,
    width: 360,
    height: 46,
  }, {
    fontSize: 20,
    bold: true,
  });
  addText(slide, "Percent of source statements with one consistent political-lean label", {
    left: 82,
    top: 390,
    width: 350,
    height: 22,
  }, {
    fontSize: 13,
    color: COLORS.muted,
  });

  const chart = slide.charts.add("bar");
  chart.position = { left: 500, top: 340, width: 360, height: 124 };
  chart.categories = ["Language", "Perturbation"];
  const series = chart.series.add("Stable statements");
  series.values = [53.8, 13.6];
  series.categories = chart.categories;
  series.fill = COLORS.blue;
  series.stroke = { style: "solid", fill: COLORS.blue, width: 1 };
  chart.hasLegend = false;
  chart.barOptions.direction = "column";
  chart.dataLabels.showValue = true;
  chart.dataLabels.position = "outEnd";
  chart.dataLabels.textStyle.typeface = FONT.body;
  chart.dataLabels.textStyle.fontSize = 11;
  chart.xAxis.textStyle.typeface = FONT.body;
  chart.xAxis.textStyle.fontSize = 11;
  chart.yAxis.textStyle.typeface = FONT.body;
  chart.yAxis.textStyle.fontSize = 11;
  chart.xAxis.majorGridlines = false;
  chart.yAxis.majorGridlines = false;
  chart.plotAreaFill = "#EEF6FF";

  addText(
    slide,
    "Interpretation: lower stability means the model recoded the same source idea into different political-lean labels.",
    { left: 82, top: 423, width: 370, height: 44 },
    { fontSize: 15, color: COLORS.ink },
  );
  addFooter(slide);
}

function buildConclusion(slide) {
  clearSlide(slide);
  slide.background.fill = COLORS.bg;
  addText(slide, "Conclusion", { left: 56, top: 42, width: 400, height: 54 }, {
    typeface: FONT.title,
    fontSize: 36,
    bold: true,
  });
  addText(
    slide,
    "Translation and perturbation are not neutral transformations for political-content evaluation.",
    { left: 58, top: 112, width: 780, height: 64 },
    { typeface: FONT.title, fontSize: 28, bold: true, color: COLORS.ink },
  );
  addTinyDivider(slide, 58, 194, 844, COLORS.line);

  const cards = [
    {
      x: 58,
      accent: COLORS.blue,
      title: "Language changes labels",
      body:
        "The same base statement can shift from one political-lean category to another after translation, even when semantic intent is preserved.",
    },
    {
      x: 337,
      accent: COLORS.red,
      title: "Perturbation changes labels",
      body:
        "Open-ended, loss-framed, and hedged versions created the strongest instability, suggesting prompt form affects moderation-style judgment.",
    },
    {
      x: 616,
      accent: COLORS.teal,
      title: "This supports the hypothesis",
      body:
        "Observed variation is an implicit alignment/moderation signal, not just a data-processing artifact; reference match is a comparison metric, not truth.",
    },
  ];

  for (const card of cards) {
    addPanel(slide, { left: card.x, top: 225, width: 250, height: 188 });
    slide.shapes.add({
      geometry: "ellipse",
      position: { left: card.x + 22, top: 246, width: 28, height: 28 },
      fill: card.accent,
      line: { width: 0, fill: card.accent },
    });
    addText(slide, card.title, { left: card.x + 62, top: 244, width: 160, height: 34 }, {
      fontSize: 18,
      bold: true,
      color: COLORS.ink,
    });
    addText(slide, card.body, { left: card.x + 24, top: 296, width: 202, height: 96 }, {
      fontSize: 14.5,
      color: COLORS.muted,
    });
  }

  addPanel(slide, { left: 86, top: 444, width: 788, height: 44 }, {
    fill: "#ECFDF5",
    line: { style: "solid", fill: "#A7F3D0", width: 1 },
  });
  addText(
    slide,
    "Next step: pair these judge labels with response-level metrics: hedging, refusal behavior, specificity, and contextual emphasis.",
    { left: 112, top: 456, width: 736, height: 24 },
    { fontSize: 14.5, color: COLORS.green, bold: true, alignment: "center" },
  );
  addFooter(slide);
}

if (presentation.slides.count < 21) {
  throw new Error(`Expected at least 21 slides, found ${presentation.slides.count}`);
}

buildOutcomes(presentation.slides.getItem(presentation.slides.count - 2));
buildConclusion(presentation.slides.getItem(presentation.slides.count - 1));

const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(outputPath);
console.log(outputPath);

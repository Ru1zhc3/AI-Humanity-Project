const { FileBlob, PresentationFile } = await import(
  "file:///C:/Users/Yi%20Ping/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs"
);
const fs = await import("node:fs/promises");

const root = process.cwd().replaceAll("\\", "/");
const deckPath =
  `${root}/docs/presentations/Political Content Moderation Across Different Models and Languages.pptx`;
const previewDir =
  `${root}/results/presentation/final_presentation_update/previews`;

await fs.mkdir(previewDir, { recursive: true });
const presentation = await PresentationFile.importPptx(await FileBlob.load(deckPath));
console.log("slides.count", presentation.slides.count);

const targetSlides =
  presentation.slides.count >= 26
    ? [24, 25]
    : [presentation.slides.count - 2, presentation.slides.count - 1];

for (const index of targetSlides.filter((value) => value >= 0)) {
  const slide = presentation.slides.getItem(index);
  const text = (slide.shapes.items ?? [])
    .map((shape) => String(shape.text ?? "").replace(/\s+/g, " ").trim())
    .filter(Boolean)
    .join(" | ");
  console.log(`slide ${index + 1}: ${text}`);
  const png = await presentation.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(
    `${previewDir}/preview_saved_slide_${index + 1}.png`,
    Buffer.from(await png.arrayBuffer()),
  );
}

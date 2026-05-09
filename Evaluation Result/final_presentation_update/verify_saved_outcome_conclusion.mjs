const { FileBlob, PresentationFile } = await import(
  "file:///C:/Users/Yi%20Ping/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs"
);
const fs = await import("node:fs/promises");

const deckPath =
  "E:/CourseProject/cs4501_26spring_final_project/Political Content Moderation Across Different Models and Languages.pptx";
const previewDir =
  "E:/CourseProject/cs4501_26spring_final_project/Evaluation Result/final_presentation_update/previews";

await fs.mkdir(previewDir, { recursive: true });
const presentation = await PresentationFile.importPptx(await FileBlob.load(deckPath));
console.log("slides.count", presentation.slides.count);

for (const index of [24, 25]) {
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

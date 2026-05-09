const { FileBlob, PresentationFile } = await import("@oai/artifact-tool");
const fs = await import("node:fs/promises");

const deckPath =
  "E:/CourseProject/cs4501_26spring_final_project/Evaluation Result/Political Content Moderation Across Different Models and Languages - revised results v2.pptx";
const presentation = await PresentationFile.importPptx(await FileBlob.load(deckPath));

console.log("slides.count", presentation.slides.count);
for (const index of [presentation.slides.count - 2, presentation.slides.count - 1]) {
  const slide = presentation.slides.getItem(index);
  const text = (slide.shapes.items ?? [])
    .map((shape) => String(shape.text ?? "").replace(/\s+/g, " ").trim())
    .filter(Boolean)
    .join(" | ");
  console.log(`slide ${index + 1}: ${text}`);
  const png = await presentation.export({ slide, format: "png", scale: 1 });
  const bytes = Buffer.from(await png.arrayBuffer());
  const outPath = `E:/CourseProject/cs4501_26spring_final_project/Evaluation Result/slides_build/preview_slide_${index + 1}.png`;
  await fs.writeFile(outPath, bytes);
  console.log(`render slide ${index + 1}: ${outPath}`);
}

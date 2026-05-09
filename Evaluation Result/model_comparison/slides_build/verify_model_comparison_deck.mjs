const { FileBlob, PresentationFile } = await import("@oai/artifact-tool");
const fs = await import("node:fs/promises");

const deckPath =
  "E:/CourseProject/cs4501_26spring_final_project/Evaluation Result/Political Content Moderation Across Different Models and Languages - model comparison results.pptx";
const outDir =
  "E:/CourseProject/cs4501_26spring_final_project/Evaluation Result/model_comparison/slides_build";

const presentation = await PresentationFile.importPptx(await FileBlob.load(deckPath));
console.log("slides.count", presentation.slides.count);
for (const index of [19, 21, 24, 25]) {
  const slide = presentation.slides.getItem(index);
  const text = (slide.shapes.items ?? [])
    .map((shape) => String(shape.text ?? "").replace(/\s+/g, " ").trim())
    .filter(Boolean)
    .join(" | ");
  console.log(`slide ${index + 1}: ${text}`);
  const png = await presentation.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(`${outDir}/preview_revised_slide_${index + 1}.png`, Buffer.from(await png.arrayBuffer()));
}

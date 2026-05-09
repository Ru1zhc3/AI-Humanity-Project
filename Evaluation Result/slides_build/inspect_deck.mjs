const { FileBlob, PresentationFile } = await import("@oai/artifact-tool");

const inputPath =
  "E:/CourseProject/cs4501_26spring_final_project/Political Content Moderation Across Different Models and Languages.pptx";
const pptx = await FileBlob.load(inputPath);
const presentation = await PresentationFile.importPptx(pptx);

console.log("slides.count", presentation.slides.count);
console.log("slide keys", Object.keys(presentation.slides));
for (let i = 0; i < presentation.slides.count; i += 1) {
  const slide = presentation.slides.getItem(i);
  console.log(`\nslide ${i + 1}`);
  console.log("slide keys", Object.keys(slide));
  if (slide.shapes) {
    console.log("shapes keys", Object.keys(slide.shapes));
    const items = slide.shapes.items ?? [];
    console.log("shape item count", items.length);
    for (let j = 0; j < items.length; j += 1) {
      const shape = items[j];
      const text = String(shape.text ?? "").replace(/\s+/g, " ").trim();
      console.log(j, shape.geometry, JSON.stringify(shape.position), text);
    }
  }
}

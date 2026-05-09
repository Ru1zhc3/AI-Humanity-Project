const { FileBlob, PresentationFile } = await import("@oai/artifact-tool");

const inputPath =
  "E:/CourseProject/cs4501_26spring_final_project/Political Content Moderation Across Different Models and Languages.pptx";
const presentation = await PresentationFile.importPptx(await FileBlob.load(inputPath));
const slide = presentation.slides.getItem(19);
const shape = slide.shapes.items[0];

function methodsOf(obj) {
  const names = new Set();
  let cur = obj;
  while (cur && cur !== Object.prototype) {
    for (const name of Object.getOwnPropertyNames(cur)) {
      if (typeof obj[name] === "function") names.add(name);
    }
    cur = Object.getPrototypeOf(cur);
  }
  return Array.from(names).sort();
}

console.log("presentation methods", methodsOf(presentation));
console.log("slides methods", methodsOf(presentation.slides));
console.log("slide methods", methodsOf(slide));
console.log("shapes methods", methodsOf(slide.shapes));
console.log("shape methods", methodsOf(shape));
console.log("slide props", Object.getOwnPropertyNames(slide));
console.log("shape props", Object.getOwnPropertyNames(shape));

import fs from "node:fs/promises";
import path from "node:path";
import sharp from "sharp";

const dir = path.join(process.cwd(), "results", "presentation", "directionality", "figures");

for (const name of [
  "translation_directionality_table",
  "perturbation_directionality_table",
]) {
  const svg = await fs.readFile(path.join(dir, `${name}.svg`));
  await sharp(svg, { density: 180 })
    .png()
    .toFile(path.join(dir, `${name}.png`));
  console.log(`${name}.png`);
}

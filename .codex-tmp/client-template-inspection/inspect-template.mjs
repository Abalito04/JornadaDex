import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = "C:/Users/maty0/Downloads/plantilla_clientes_JornadaDex.xlsx";
const previewPath = "C:/Users/maty0/OneDrive/Escritorio/JornadaDex/.codex-tmp/client-template-inspection/preview.png";

const input = await FileBlob.load(inputPath);
const workbook = await SpreadsheetFile.importXlsx(input);
const sheet = workbook.worksheets.getItemAt(0);

const summary = await workbook.inspect({
  kind: "workbook,sheet,table",
  maxChars: 6000,
  tableMaxRows: 5,
  tableMaxCols: 30,
  tableMaxCellChars: 80,
});
console.log("SUMMARY");
console.log(summary.ndjson);

const region = await workbook.inspect({
  kind: "region",
  sheetId: sheet.name,
  range: "A1:AZ8",
  maxChars: 12000,
});
console.log("REGION");
console.log(region.ndjson);

const preview = await workbook.render({
  sheetName: sheet.name,
  range: "A1:AZ12",
  scale: 1,
  format: "png",
});
await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));
console.log(`PREVIEW=${previewPath}`);

const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");

function mimeType(filePath) {
  const extension = path.extname(filePath).toLowerCase();
  if (extension === ".svg") return "image/svg+xml";
  if (extension === ".jpg" || extension === ".jpeg") return "image/jpeg";
  return "image/png";
}

function copyIfChanged(source, destination) {
  if (fs.existsSync(destination)) {
    const sourceData = fs.readFileSync(source);
    const destinationData = fs.readFileSync(destination);
    if (sourceData.equals(destinationData)) return;
  }
  fs.copyFileSync(source, destination);
}

function writeIfChanged(filePath, content) {
  if (fs.existsSync(filePath) && fs.readFileSync(filePath, "utf8") === content) return;
  fs.writeFileSync(filePath, content, "utf8");
}

function embedLocalImages(markdown, sourceDir) {
  return markdown.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (match, alt, target) => {
    if (/^(https?:|data:)/i.test(target)) return match;
    const imagePath = path.resolve(sourceDir, target);
    if (!fs.existsSync(imagePath)) {
      throw new Error(`Missing report image: ${imagePath}`);
    }
    const encoded = fs.readFileSync(imagePath).toString("base64");
    return `![${alt}](data:${mimeType(imagePath)};base64,${encoded})`;
  });
}

function buildNotionPackage(markdown, sourceDir, packageDir) {
  const imageDir = path.join(packageDir, "images");
  fs.mkdirSync(imageDir, { recursive: true });
  const portable = markdown.replace(
    /!\[([^\]]*)\]\(([^)]+)\)/g,
    (match, alt, target) => {
      if (/^(https?:|data:)/i.test(target)) return match;
      const source = path.resolve(sourceDir, target);
      if (!fs.existsSync(source)) throw new Error(`Missing package image: ${source}`);
      const fileName = path.basename(source);
      copyIfChanged(source, path.join(imageDir, fileName));
      return `![${alt}](images/${fileName})`;
    }
  );
  writeIfChanged(
    path.join(packageDir, "DREAMER_NRC_完全分析報告_日本語.md"),
    portable
  );
  writeIfChanged(
    path.join(packageDir, "README.txt"),
    [
      "Notionインポート用パッケージ",
      "",
      "1. ZIPを解凍せず、Notionの「インポート」からMarkdown & CSVを選択してください。",
      "2. ZIPインポートが利用できない場合は、Markdownとimagesフォルダを同時に展開してからMarkdownを読み込んでください。",
      "3. 教授への閲覧用には、同時生成されたPDFを使用できます。",
      "",
    ].join("\r\n")
  );
}

async function main() {
  const root = path.resolve(__dirname, "..");
  const source = path.join(root, "paper", "DREAMER_NRC_完全分析報告_日本語.md");
  const output = path.join(root, "paper", "DREAMER_NRC_完全分析報告_日本語.html");
  const packageDir = path.join(root, "paper", "notion_report_ja");
  const markedPath = require.resolve("marked");
  const { marked } = await import(pathToFileURL(markedPath).href);
  const markdown = fs.readFileSync(source, "utf8");
  const embeddedMarkdown = embedLocalImages(markdown, path.dirname(source));
  const body = marked.parse(embeddedMarkdown, { gfm: true });
  buildNotionPackage(markdown, path.dirname(source), packageDir);

  const html = `<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DREAMER × NRC-VAD 完全分析報告書</title>
<style>
  :root {
    --ink:#18232d;
    --muted:#586674;
    --blue:#0b5f8a;
    --teal:#087f6b;
    --orange:#c75b18;
    --line:#d6dde3;
    --wash:#f3f7f9;
    --dark:#263845;
  }
  @page { size:A4; margin:15mm 16mm 17mm; }
  * { box-sizing:border-box; }
  html { background:#e8ecef; }
  body {
    max-width:210mm;
    margin:20px auto;
    padding:18mm 17mm;
    background:white;
    color:var(--ink);
    font-family:"Noto Sans CJK JP","Yu Gothic","Hiragino Kaku Gothic ProN","Meiryo",Arial,sans-serif;
    font-size:10.2pt;
    line-height:1.72;
  }
  body > h1:first-of-type {
    margin:0 0 10mm;
    padding:25mm 0 12mm;
    border-bottom:5px solid var(--blue);
    font-size:27pt;
    line-height:1.28;
    color:var(--ink);
  }
  body > h1:first-of-type::before {
    content:"FULL ANALYSIS REPORT  •  2026.07.29";
    display:block;
    margin-bottom:9mm;
    color:var(--orange);
    font-size:9pt;
    font-weight:700;
    letter-spacing:1.2px;
  }
  h1 {
    margin:12mm 0 5mm;
    padding-bottom:3mm;
    border-bottom:3px solid var(--blue);
    color:var(--blue);
    font-size:20pt;
    line-height:1.35;
    break-before:page;
    break-after:avoid;
  }
  body > h1:first-of-type { break-before:avoid; }
  h2 {
    margin:8mm 0 3mm;
    padding-bottom:1.5mm;
    border-bottom:1px solid var(--line);
    color:var(--teal);
    font-size:14.5pt;
    line-height:1.4;
    break-after:avoid;
  }
  h3 {
    margin:6mm 0 2mm;
    color:var(--dark);
    font-size:11.5pt;
    break-after:avoid;
  }
  p { margin:0 0 3.2mm; orphans:3; widows:3; }
  strong { color:#101820; }
  blockquote {
    margin:5mm 0;
    padding:4mm 5mm;
    border-left:4px solid var(--orange);
    background:var(--wash);
    color:#20303d;
    font-size:10.7pt;
  }
  ul, ol { margin:2mm 0 4mm; padding-left:7mm; }
  li { margin:1.1mm 0; }
  table {
    width:100%;
    margin:4mm 0 6mm;
    border-collapse:collapse;
    font-size:8.6pt;
    break-inside:avoid;
  }
  th {
    padding:2.2mm;
    background:var(--dark);
    color:white;
    text-align:left;
    font-weight:600;
  }
  td {
    padding:2mm 2.2mm;
    border-bottom:1px solid var(--line);
    vertical-align:top;
  }
  tbody tr:nth-child(even) { background:#f7f9fa; }
  code {
    padding:.2mm 1mm;
    border-radius:2px;
    background:#edf2f5;
    font-family:Consolas,"SFMono-Regular",monospace;
    font-size:9pt;
  }
  pre {
    margin:4mm 0 5mm;
    padding:3mm 4mm;
    border-left:3px solid var(--teal);
    background:#eef3f5;
    white-space:pre-wrap;
    break-inside:avoid;
  }
  pre code { padding:0; background:transparent; }
  a { color:var(--blue); text-decoration:none; word-break:break-all; }
  img {
    display:block;
    width:100%;
    max-height:160mm;
    margin:5mm auto 2mm;
    object-fit:contain;
    border:1px solid var(--line);
    break-inside:avoid;
  }
  hr { margin:8mm 0; border:0; border-top:1px solid var(--line); }
  @media print {
    html, body { background:white; }
    body { max-width:none; margin:0; padding:0; }
    a { color:inherit; }
    -webkit-print-color-adjust:exact;
    print-color-adjust:exact;
  }
</style>
</head>
<body>
${body}
</body>
</html>`;

  writeIfChanged(output, html);
  process.stdout.write(
    JSON.stringify({ html: output, notionPackage: packageDir }, null, 2)
  );
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});

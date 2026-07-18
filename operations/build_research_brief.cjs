const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");

async function main() {
  const root = path.resolve(__dirname, "..");
  const source = path.join(root, "paper", "DREAMER_NRC_研究概要书.md");
  const output = path.join(root, "paper", "DREAMER_NRC_研究概要书.html");
  const markedPath = require.resolve("marked");
  const { marked } = await import(pathToFileURL(markedPath).href);
  const markdown = fs.readFileSync(source, "utf8");
  const body = marked.parse(markdown, { gfm: true });
  const figures = [
    ["figure_1_dimension_alignment.png", "图1. V、A、D三个维度的跨情境对应"],
    ["figure_2_scale_compression.png", "图2. NRC到DREAMER的量尺映射斜率"],
    ["figure_3_influence_diagnostics.png", "图3. 逐一删除情绪类别后的相关稳定性"],
    ["figure_4_calibrated_discrepancy.png", "图4. 仿射校准后的情绪类别残差及双层bootstrap区间"],
  ];
  const figureDir = path.join(root, "results", "dreamer_nrc_robustness");
  const figureHtml = figures.map(([name, caption]) => `
    <figure>
      <img src="${pathToFileURL(path.join(figureDir, name)).href}" alt="${caption}">
      <figcaption>${caption}</figcaption>
    </figure>`).join("\n");
  const html = `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DREAMER × NRC-VAD 研究概要书</title>
<style>
  :root { --ink:#17212b; --muted:#5d6873; --blue:#1261a0; --orange:#c85616; --green:#087f5b; --line:#d8dee5; --wash:#f4f7f9; }
  @page { size: A4; margin: 17mm 17mm 18mm; }
  * { box-sizing: border-box; }
  html { background:#e9edf0; }
  body { max-width:210mm; margin:20px auto; padding:18mm 17mm; background:white; color:var(--ink); font-family:"Noto Sans CJK SC","Microsoft YaHei","PingFang SC",Arial,sans-serif; font-size:10.5pt; line-height:1.72; }
  h1 { margin:0 0 14mm; padding:24mm 0 12mm; border-bottom:4px solid var(--blue); font-size:27pt; line-height:1.22; letter-spacing:0; }
  h1::before { content:"RESEARCH BRIEF  •  2026.07"; display:block; margin-bottom:8mm; color:var(--orange); font-size:9pt; font-weight:700; letter-spacing:1.2px; }
  h2 { margin:9mm 0 3mm; padding-bottom:2mm; border-bottom:1px solid var(--line); color:var(--blue); font-size:16pt; line-height:1.3; page-break-after:avoid; }
  h3 { margin:6mm 0 2mm; color:var(--green); font-size:12.5pt; page-break-after:avoid; }
  p { margin:0 0 3.2mm; orphans:3; widows:3; }
  blockquote { margin:5mm 0; padding:4mm 5mm; border-left:4px solid var(--orange); background:var(--wash); color:#24313d; }
  ul, ol { margin:2mm 0 4mm; padding-left:7mm; }
  li { margin:1.1mm 0; }
  table { width:100%; margin:4mm 0 6mm; border-collapse:collapse; font-size:9.2pt; page-break-inside:avoid; }
  th { padding:2.4mm; background:#263746; color:white; text-align:left; }
  td { padding:2.2mm 2.4mm; border-bottom:1px solid var(--line); vertical-align:top; }
  tbody tr:nth-child(even) { background:#f7f9fa; }
  code { padding:0.2mm 1mm; border-radius:2px; background:#eef2f5; font-family:Consolas,monospace; font-size:9.2pt; }
  a { color:var(--blue); text-decoration:none; word-break:break-word; }
  .figures { margin-top:8mm; }
  figure { margin:6mm 0 10mm; page-break-inside:avoid; }
  figure img { display:block; width:100%; max-height:155mm; object-fit:contain; border:1px solid var(--line); }
  figcaption { margin-top:2mm; color:var(--muted); font-size:9pt; text-align:center; }
  .footer-note { margin-top:12mm; padding-top:3mm; border-top:1px solid var(--line); color:var(--muted); font-size:8.5pt; }
  @media print {
    html, body { background:white; }
    body { max-width:none; margin:0; padding:0; }
    h1 { break-before:avoid; }
    a { color:inherit; }
    -webkit-print-color-adjust:exact; print-color-adjust:exact;
  }
</style>
</head>
<body>
${body}
<section class="figures">
  <h2>核心可视化</h2>
  ${figureHtml}
</section>
<p class="footer-note">分析输入、精确置换结果、bootstrap区间和图表均由项目可复现脚本生成。原始许可数据不随文档分发。</p>
</body>
</html>`;
  fs.writeFileSync(output, html, "utf8");
  process.stdout.write(output);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});

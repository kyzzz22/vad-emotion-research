const pptxgen = require("pptxgenjs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(ROOT, "paper", "本周研究进展汇报_VAD主线_情绪变化副线.pptx");

const img = {
  vadOverview: path.join(ROOT, "public_data", "dreamer_pilot", "results", "DREAMER_NRC_直观对照图.png"),
  vadScatter: path.join(ROOT, "public_data", "dreamer_pilot", "results", "dreamer_nrc_dimension_scatter.png"),
  vadDistance: path.join(ROOT, "public_data", "dreamer_pilot", "results", "dreamer_nrc_vad_distance.png"),
  vad3d: path.join(ROOT, "visualization", "dreamer-vad-3d", "verification", "desktop.png"),
  recovery: path.join(ROOT, "public_data", "case_recovery", "week2", "overall_recovery_curves_ci.png"),
  consistency: path.join(ROOT, "public_data", "case_recovery", "week2", "cross_condition_auc_scatter.png"),
};

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "dolylab";
pptx.subject = "Weekly research progress";
pptx.title = "本周研究进展汇报：VAD 主线与情绪变化副线";
pptx.company = "dolylab";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei",
  bodyFontFace: "Microsoft YaHei",
  lang: "zh-CN",
};
pptx.defineLayout({ name: "CUSTOM_WIDE", width: 13.333, height: 7.5 });
pptx.layout = "CUSTOM_WIDE";

const C = {
  ink: "1E2933",
  muted: "667085",
  faint: "EEF2F6",
  line: "D7DEE8",
  red: "B5403E",
  teal: "287B78",
  blue: "315C8A",
  green: "4D7C59",
  gold: "B7791F",
  white: "FFFFFF",
};

function addTitle(slide, title, kicker = "") {
  if (kicker) {
    slide.addText(kicker, {
      x: 0.55, y: 0.28, w: 8, h: 0.25,
      fontFace: "Microsoft YaHei", fontSize: 9, bold: true,
      color: C.red, margin: 0,
    });
  }
  slide.addText(title, {
    x: 0.55, y: 0.58, w: 10.6, h: 0.45,
    fontFace: "Microsoft YaHei", fontSize: 22, bold: true,
    color: C.ink, margin: 0,
    breakLine: false, fit: "shrink",
  });
  slide.addShape(pptx.ShapeType.line, {
    x: 0.55, y: 1.15, w: 12.2, h: 0,
    line: { color: C.line, width: 0.8 },
  });
}

function addFooter(slide, idx) {
  slide.addText(`本周研究进展 | ${idx}`, {
    x: 11.1, y: 7.05, w: 1.7, h: 0.18,
    fontFace: "Microsoft YaHei", fontSize: 7.5,
    color: "8A94A3", align: "right", margin: 0,
  });
}

function bullet(slide, items, x, y, w, h, opts = {}) {
  const runs = [];
  items.forEach((item) => {
    runs.push({
      text: item,
      options: {
        bullet: { type: "ul" },
        breakLine: true,
        hanging: 4,
      },
    });
  });
  slide.addText(runs, {
    x, y, w, h,
    fontFace: "Microsoft YaHei",
    fontSize: opts.fontSize || 14,
    color: opts.color || C.ink,
    fit: "shrink",
    valign: "top",
    paraSpaceAfterPt: opts.spaceAfter || 8,
    breakLine: false,
    margin: 0.06,
  });
}

function label(slide, text, x, y, w, color = C.teal) {
  slide.addText(text, {
    x, y, w, h: 0.28,
    fontFace: "Microsoft YaHei", fontSize: 10.5, bold: true,
    color, margin: 0,
    fit: "shrink",
  });
}

function metric(slide, value, text, x, y, w, color) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h: 0.95,
    rectRadius: 0.04,
    fill: { color: "F8FAFC" },
    line: { color: C.line, width: 0.8 },
  });
  slide.addText(value, {
    x: x + 0.13, y: y + 0.15, w: w - 0.26, h: 0.27,
    fontFace: "Microsoft YaHei", fontSize: 18, bold: true,
    color, margin: 0, align: "center", fit: "shrink",
  });
  slide.addText(text, {
    x: x + 0.13, y: y + 0.52, w: w - 0.26, h: 0.25,
    fontFace: "Microsoft YaHei", fontSize: 8.8,
    color: C.muted, margin: 0, align: "center", fit: "shrink",
  });
}

function imageBox(slide, imagePath, x, y, w, h, caption = "") {
  slide.addShape(pptx.ShapeType.rect, {
    x, y, w, h,
    fill: { color: C.white },
    line: { color: C.line, width: 0.8 },
  });
  const pad = 0.08;
  slide.addImage({ path: imagePath, x: x + pad, y: y + pad, w: w - pad * 2, h: h - pad * 2 });
  if (caption) {
    slide.addText(caption, {
      x, y: y + h + 0.08, w, h: 0.22,
      fontFace: "Microsoft YaHei", fontSize: 8.5,
      color: C.muted, margin: 0, align: "center", fit: "shrink",
    });
  }
}

function timeline(slide, entries, x, y, w) {
  const step = w / entries.length;
  slide.addShape(pptx.ShapeType.line, {
    x: x + 0.28, y: y + 0.34, w: w - 0.56, h: 0,
    line: { color: C.line, width: 1.5 },
  });
  entries.forEach((e, i) => {
    const cx = x + i * step + step / 2;
    slide.addShape(pptx.ShapeType.ellipse, {
      x: cx - 0.15, y: y + 0.18, w: 0.3, h: 0.3,
      fill: { color: e.color }, line: { color: e.color },
    });
    slide.addText(e.title, {
      x: cx - step / 2 + 0.05, y: y + 0.68, w: step - 0.1, h: 0.3,
      fontFace: "Microsoft YaHei", fontSize: 10.5, bold: true,
      color: C.ink, align: "center", margin: 0, fit: "shrink",
    });
    slide.addText(e.body, {
      x: cx - step / 2 + 0.05, y: y + 1.04, w: step - 0.1, h: 0.62,
      fontFace: "Microsoft YaHei", fontSize: 8.3,
      color: C.muted, align: "center", margin: 0.02, fit: "shrink",
    });
  });
}

let n = 1;

{
  const s = pptx.addSlide();
  s.background = { color: "FBFCFE" };
  s.addText("本周研究进展汇报", {
    x: 0.65, y: 0.48, w: 4.0, h: 0.3,
    fontFace: "Microsoft YaHei", fontSize: 12, bold: true,
    color: C.red, margin: 0,
  });
  s.addText("两条研究方向的分析进展与下一步任务", {
    x: 0.65, y: 0.98, w: 8.5, h: 0.58,
    fontFace: "Microsoft YaHei", fontSize: 27, bold: true,
    color: C.ink, margin: 0, fit: "shrink",
  });
  s.addText("主线：VAD 情绪空间对齐（DREAMER × NRC-VAD）\n副线：情绪变化与生理恢复动态（CASE）", {
    x: 0.68, y: 1.78, w: 7.2, h: 0.65,
    fontFace: "Microsoft YaHei", fontSize: 15,
    color: C.muted, breakLine: false, margin: 0,
  });
  metric(s, "VAD", "本周展示重点", 0.68, 3.02, 1.75, C.red);
  metric(s, "414", "DREAMER 有效试次", 2.6, 3.02, 1.75, C.teal);
  metric(s, "30", "CASE 全样本参与者", 4.52, 3.02, 1.75, C.blue);
  s.addShape(pptx.ShapeType.rect, {
    x: 8.05, y: 0.56, w: 4.62, h: 5.82,
    fill: { color: C.white }, line: { color: C.line, width: 0.8 },
  });
  s.addImage({ path: img.vadOverview, x: 8.2, y: 0.72, w: 4.32, h: 5.5 });
  s.addText("2026.07.15", {
    x: 0.68, y: 6.58, w: 2, h: 0.24,
    fontFace: "Microsoft YaHei", fontSize: 9.5,
    color: C.muted, margin: 0,
  });
  addFooter(s, n++);
}

{
  const s = pptx.addSlide();
  addTitle(s, "本周工作概览：从方案可行性推进到可展示结果", "PROGRESS OVERVIEW");
  timeline(s, [
    { title: "VAD 主线", body: "完成 DREAMER-NRC 三维对齐、相关、距离、LOEO 校准与可视化", color: C.red },
    { title: "生理探索", body: "提取 EEG/ECG 粗粒度特征，试次级模型未发现稳健线性关联", color: C.teal },
    { title: "情绪变化副线", body: "CASE 第二周完成全30人恢复曲线、混合模型和敏感性分析", color: C.blue },
    { title: "实验转化", body: "将副线收敛到虚拟 AI 面试压力任务后的 recovery 个体差异", color: C.green },
  ], 0.8, 1.6, 11.7);
  label(s, "阶段判断", 0.85, 4.05, 2.0, C.red);
  bullet(s, [
    "VAD 方向已经具备探索性论文雏形：问题、数据、主结果、局限和图表均已成型。",
    "情绪变化方向提供了 recovery 分析模板，但更适合作为后续实验设计的副线支撑。",
    "下一步不宜同时扩大战线，应优先把 VAD 主线写完整、把 AI 面试 pilot 流程锁定。"
  ], 0.85, 4.45, 11.6, 1.35, { fontSize: 14 });
  addFooter(s, n++);
}

{
  const s = pptx.addSlide();
  addTitle(s, "VAD 方向：核心问题和当前数据路线", "MAIN LINE");
  label(s, "研究问题", 0.72, 1.45, 2.0, C.red);
  s.addText("情绪词的语义 VAD 与影片诱发体验的 VAD，在类别级三维空间中是否共享结构？", {
    x: 0.72, y: 1.83, w: 6.0, h: 0.62,
    fontFace: "Microsoft YaHei", fontSize: 18, bold: true,
    color: C.ink, margin: 0, fit: "shrink",
  });
  label(s, "数据与处理", 0.72, 2.92, 2.0, C.teal);
  bullet(s, [
    "DREAMER：23名参与者、18段影片、9类目标情绪，共414个 VAD 评分试次。",
    "NRC-VAD v2.1：使用9个同名情绪词，主分析采用名词映射，形容词作为敏感性分析。",
    "统一量尺到 [-1, 1]，比较维度相关、原始 VAD 距离和线性校准后的残差。"
  ], 0.72, 3.28, 6.25, 1.55, { fontSize: 13.2 });
  imageBox(s, img.vad3d, 7.35, 1.42, 5.25, 4.48, "Web 3D VAD 模型：两套坐标及差异向量");
  s.addText("定位：跨样本、跨任务、类别级探索性对齐，不写成个体内等价测量验证。", {
    x: 0.72, y: 6.25, w: 11.9, h: 0.36,
    fontFace: "Microsoft YaHei", fontSize: 13.5, bold: true,
    color: C.red, margin: 0, fit: "shrink",
  });
  addFooter(s, n++);
}

{
  const s = pptx.addSlide();
  addTitle(s, "VAD 主结果：维度对应具有明显差异", "RESULT 1");
  metric(s, "r=.875", "Valence：强且稳定", 0.75, 1.42, 2.05, C.red);
  metric(s, "r=.832", "Arousal：线性相关较强", 3.02, 1.42, 2.05, C.teal);
  metric(s, "r=-.121", "Dominance：未可靠对应", 5.29, 1.42, 2.05, C.blue);
  imageBox(s, img.vadScatter, 7.72, 1.35, 4.92, 4.58, "三维度散点：NRC 词坐标 vs DREAMER 诱发均值");
  label(s, "解释重点", 0.8, 3.1, 2.0, C.red);
  bullet(s, [
    "Valence 是目前最稳健的共享结构，Pearson 与 Spearman 均显著。",
    "Arousal 的 Pearson 高但排序相关不稳定，提示整体趋势存在、类别次序会变。",
    "Dominance 是最需要谨慎处理的维度：方向、任务理解和构念差异都可能影响结果。"
  ], 0.8, 3.48, 6.35, 1.55, { fontSize: 13.5 });
  s.addText("核心表述：不是“词义等于体验”，而是“跨语境 VAD 空间存在维度特异性的对应与偏离”。", {
    x: 0.82, y: 6.14, w: 11.5, h: 0.36,
    fontFace: "Microsoft YaHei", fontSize: 13.2, bold: true,
    color: C.ink, margin: 0, fit: "shrink",
  });
  addFooter(s, n++);
}

{
  const s = pptx.addSlide();
  addTitle(s, "VAD 主结果：原始距离与校准残差给出不同信息", "RESULT 2");
  imageBox(s, img.vadDistance, 0.72, 1.36, 5.85, 4.75, "原始 VAD 距离：绝对几何差异");
  label(s, "关键发现", 7.05, 1.42, 2.0, C.red);
  bullet(s, [
    "原始距离：happiness 最近，sadness 最远；但这混合了全局尺度压缩。",
    "LOEO 校准后：excitement、fear、anger 残差较小，calmness 残差最大。",
    "因此结果部分应并列报告两类指标：一个回答“离多远”，一个回答“偏离是否超出整体尺度变换”。"
  ], 7.05, 1.82, 5.35, 1.85, { fontSize: 13.5 });
  label(s, "论文价值", 7.05, 4.25, 2.0, C.teal);
  bullet(s, [
    "把规范化语言资源和诱发情绪数据库放入同一 VAD 坐标系。",
    "把维度相关、原始距离、校准残差分开解释，避免单一“重合度排名”。"
  ], 7.05, 4.62, 5.35, 1.08, { fontSize: 13.5 });
  addFooter(s, n++);
}

{
  const s = pptx.addSlide();
  addTitle(s, "VAD 方向：目前可说与不能说", "BOUNDARIES");
  label(s, "可以支持", 0.78, 1.45, 2.0, C.green);
  bullet(s, [
    "情绪词规范与影片诱发体验在 Valence 上共享明显类别结构。",
    "Arousal 存在线性对应，但伴随压缩和类别排序变化。",
    "Dominance 暂未形成可靠对应，是后续方法核查和讨论重点。",
    "跨语境对齐框架可作为后续同参与者三层实验的分析模板。"
  ], 0.85, 1.88, 5.55, 2.45, { fontSize: 13.2 });
  label(s, "不能声称", 7.02, 1.45, 2.0, C.red);
  bullet(s, [
    "不能证明同一个人的词义判断可预测其诱发体验。",
    "不能把语义 VAD 与诱发 VAD 写成同一心理过程或可互换测量。",
    "不能把核心类别相关的样本量写成414；核心检验单位是9类情绪。",
    "不能把生理模型未显著解释为生理信号无效。"
  ], 7.08, 1.88, 5.55, 2.45, { fontSize: 13.2 });
  s.addShape(pptx.ShapeType.rect, {
    x: 0.82, y: 5.35, w: 11.65, h: 0.78,
    fill: { color: "F8FAFC" },
    line: { color: C.line, width: 0.8 },
  });
  s.addText("建议论文题目：From Emotion Words to Elicited Experience: Dimension-Specific Alignment Between NRC-VAD and DREAMER", {
    x: 1.05, y: 5.62, w: 11.2, h: 0.28,
    fontFace: "Microsoft YaHei", fontSize: 12.5, bold: true,
    color: C.ink, margin: 0, fit: "shrink",
  });
  addFooter(s, n++);
}

{
  const s = pptx.addSlide();
  addTitle(s, "情绪变化副线：CASE 恢复动态分析完成第二周闭环", "SIDE LINE");
  imageBox(s, img.recovery, 0.72, 1.36, 6.15, 4.65, "总体恢复曲线：参与者 bootstrap 置信区间");
  label(s, "本周完成", 7.25, 1.42, 2.0, C.blue);
  bullet(s, [
    "30人全样本预处理，240 trial、2880个10秒恢复箱。",
    "ECG/EDA 质控通过；HeartPy 与工程检测器峰级匹配率达到预设门槛。",
    "混合模型和敏感性分析完成，全部模型收敛。",
    "跨条件个体一致性完成参与者 bootstrap 与 BH-FDR 校正。"
  ], 7.25, 1.82, 5.1, 1.9, { fontSize: 13.1 });
  label(s, "主要发现", 7.25, 4.18, 2.0, C.red);
  bullet(s, [
    "SCL：scary 后残留显著高于 amusing，且差距在120秒内缓慢缩小。",
    "HR：存在平均条件差异，但恢复形状证据较弱。",
    "主观 arousal 不能通过全部敏感性检验，暂不作为稳定预测因子。"
  ], 7.25, 4.55, 5.1, 1.25, { fontSize: 13.1 });
  addFooter(s, n++);
}

{
  const s = pptx.addSlide();
  addTitle(s, "副线如何服务下一步：转向 AI 面试压力后的 recovery 个体差异", "NEXT EXPERIMENT");
  imageBox(s, img.consistency, 0.78, 1.42, 4.95, 4.08, "探索性个体一致性：SCL AUC 与恢复斜率");
  label(s, "从 CASE 得到的方法模板", 6.25, 1.45, 3.0, C.blue);
  bullet(s, [
    "主分析窗口放在回答结束后的 recovery，而不是噪声更大的回答阶段。",
    "以个体 baseline 校正后的动态特征为核心：反应强度、峰值时间、恢复斜率、晚期残留。",
    "主观评分用于解释差异，但不把主观 arousal 与生理恢复视为同一层面。"
  ], 6.25, 1.82, 5.9, 1.55, { fontSize: 13.2 });
  label(s, "接下来两周目标", 6.25, 4.05, 3.0, C.red);
  bullet(s, [
    "锁定虚拟 AI 面试压力任务与中性说话对照任务。",
    "确定 trial 结构：baseline、问题呈现、准备、回答、120秒 recovery、评分。",
    "明确 MyBeat 与 Muse 指标、预处理规则和 pilot 检查标准。"
  ], 6.25, 4.42, 5.9, 1.35, { fontSize: 13.2 });
  addFooter(s, n++);
}

{
  const s = pptx.addSlide();
  addTitle(s, "下一阶段任务：主线收稿化，副线流程化", "ACTION PLAN");
  label(s, "VAD 主线：优先级最高", 0.78, 1.42, 3.0, C.red);
  bullet(s, [
    "核实 DREAMER Dominance 图示方向，固定主编码并保留反向敏感性。",
    "补充9类情绪相关的置换检验、bootstrap 和逐类删除敏感性。",
    "把名词映射设为主分析，形容词映射作为敏感性分析。",
    "完成摘要、方法、结果、讨论和可复现性声明的论文完整稿。"
  ], 0.82, 1.82, 5.65, 2.12, { fontSize: 13.1 });
  label(s, "情绪变化副线：作为实验流程支撑", 7.0, 1.42, 3.3, C.blue);
  bullet(s, [
    "整理中性说话与 AI 面试压力问题列表。",
    "做 3-5 人 pilot，检查 stress / evaluation threat 是否拉开。",
    "确定 MyBeat + Muse 同步记录和事件标记方式。",
    "产出给老师看的 6-8 页实验流程 PPT。"
  ], 7.04, 1.82, 5.45, 2.12, { fontSize: 13.1 });
  s.addText("本周汇报主旨", {
    x: 0.82, y: 5.08, w: 2.0, h: 0.26,
    fontFace: "Microsoft YaHei", fontSize: 10.5, bold: true,
    color: C.teal, margin: 0,
  });
  s.addText("VAD 方向已经从“想法”推进到“可写论文的探索性结果”；情绪变化方向已证明 recovery 动态分析可行，下一步应服务于虚拟 AI 面试实验的 pilot 设计。", {
    x: 0.82, y: 5.48, w: 11.55, h: 0.55,
    fontFace: "Microsoft YaHei", fontSize: 15.2, bold: true,
    color: C.ink, margin: 0, fit: "shrink",
  });
  addFooter(s, n++);
}

pptx.writeFile({ fileName: OUT });

import * as THREE from "three";
import { OrbitControls } from "three/addons/OrbitControls.js";

const DATA = [
  { emotion: "happiness", zh: "幸福", ja: "幸福", nrc: [0.920, 0.464, 0.700], dreamer: [0.728261, 0.217391, 0.326087], distance: 0.487228, calibrated: 0.492057 },
  { emotion: "excitement", zh: "兴奋", ja: "興奮", nrc: [0.792, 0.368, 0.462], dreamer: [0.217391, 0.260870, 0.195652], distance: 0.642334, calibrated: 0.211803 },
  { emotion: "anger", zh: "愤怒", ja: "怒り", nrc: [-0.666, 0.730, 0.314], dreamer: [-0.576087, 0.043478, 0.184783], distance: 0.704339, calibrated: 0.320254 },
  { emotion: "calmness", zh: "平静", ja: "平静", nrc: [0.868, -0.895, -0.199], dreamer: [0.282609, -0.445652, -0.326087], distance: 0.748831, calibrated: 0.759439 },
  { emotion: "amusement", zh: "欢乐", ja: "楽しさ", nrc: [0.858, 0.674, 0.606], dreamer: [0.630435, 0.108696, 0.130435], distance: 0.772992, calibrated: 0.359623 },
  { emotion: "fear", zh: "恐惧", ja: "恐怖", nrc: [-0.854, 0.680, -0.414], dreamer: [-0.369565, 0.336957, 0.336957], distance: 0.957231, calibrated: 0.283444 },
  { emotion: "surprise", zh: "惊讶", ja: "驚き", nrc: [0.750, 0.750, 0.124], dreamer: [-0.076087, 0.228261, 0.065217], distance: 0.978819, calibrated: 0.497240 },
  { emotion: "disgust", zh: "厌恶", ja: "嫌悪", nrc: [-0.896, 0.550, -0.366], dreamer: [-0.282609, 0.282609, 0.413043], distance: 1.026964, calibrated: 0.448176 },
  { emotion: "sadness", zh: "悲伤", ja: "悲しみ", nrc: [-0.896, -0.424, -0.672], dreamer: [-0.771739, 0.000000, 0.358696], distance: 1.121405, calibrated: 0.432592 }
];

const COPY = {
  zh: {
    title: "词义坐标与诱发体验", subtitle: "NRC × DREAMER · VAD 三维偏移", tour: "导览模式", explore: "自由探索",
    all: "全部情绪", select: "查看情绪", residual: "校准后残差排名", residualHint: "越长 = 越特异",
    stable: "稳定 ✓", compressed: "压缩 △", failed: "未对应 ×", chapter: "第", hint: "← → 切换章节 · 空格暂停旋转"
  },
  ja: {
    title: "語意座標と誘発体験", subtitle: "NRC × DREAMER · VAD 3次元偏移", tour: "ガイド", explore: "自由探索",
    all: "すべての感情", select: "感情を選択", residual: "校正後残差ランキング", residualHint: "長い = より特異",
    stable: "安定 ✓", compressed: "圧縮 △", failed: "対応なし ×", chapter: "第", hint: "← → 章を移動 · Space で回転停止"
  }
};

const CHAPTERS = {
  zh: [
    { kicker: "序章 · VAD 模型", title: "情绪不只是标签，也可以是空间中的一个点", body: "VAD 是一种情绪维度模型。它不只把情绪分为“快乐”或“愤怒”，而是用愉悦度、唤醒度和控制感三个连续维度来定位情绪。因此，每种情绪都可以表示为三维空间中的一个坐标。", stat: "V · A · D", statLabel: "三个连续维度共同构成情绪的三维坐标", view: "empty", extra: "vad" },
    { kicker: "第 1 章 · 起点", title: "都叫 VAD，但它们是一回事吗？", body: "词汇常模描述词的语义坐标，诱发数据库记录人在影片中的实际感受。情感计算经常默认两者可直接交换，但这个前提从未被系统检验。", stat: "0", statLabel: "已发表研究中，直接对齐这两套坐标的数量", view: "empty" },
    { kicker: "第 2 章 · 方法", title: "把两套坐标放进同一个立方体", body: "我们对齐同一组 9 个情绪概念：一边是 NRC-VAD 的词义坐标，一边是 DREAMER 中影片诱发的体验均值，并统一换算到 [−1, 1]。", stat: "9 情绪 · 414 试次 · 3 维度", statLabel: "23 名参与者 × 18 段影片；所有坐标统一为 −1 至 +1", view: "frame" },
    { kicker: "第 3 章 · 总览", title: "结构相似，但存在系统偏移", body: "两套坐标整体形状相似，但体验点普遍更靠近中心，且不同情绪的偏移幅度差异很大。立方体是词义，球体是体验，箭头显示两者的偏移。", stat: "0.49 → 1.12", statLabel: "从 happiness 到 sadness 的原始三维距离范围", view: "overview" },
    { kicker: "第 4 章 · 核心发现", title: "不是所有维度都能迁移", body: "V 是稳定的跨情境桥梁；A 保留了顺序，但体验量尺被明显压缩；D 则未见对应。“VAD 可迁移”这个默认假设，只在一个半维度上成立。", stat: "1.5 / 3", statLabel: "支持直接迁移或校准后迁移的维度", view: "v", extra: "dimensions" },
    { kicker: "第 5 章 · 测量边界", title: "语义中的“支配” ≠ 体验中的“控制”", body: "D 的负结果本身就是发现：词义空间里的支配感和体验评定里的控制感可能是不同构念。消除全局量尺差异后，calmness 仍是最特异的个案。", stat: "0.759", statLabel: "calmness 的校准后残差，9 类中最大", view: "d", focus: 3 },
    { kicker: "第 6 章 · 所以呢", title: "从发现边界，到验证机制", body: "这项研究提出“结构相关 → 全局量尺映射 → 校准残差”的三步审计框架。下一步将在同一参与者内对齐“词汇联想 → 概念原型 → 诱发体验”，追问偏差到底从哪一层开始。", stat: "H1", statLabel: "概念原型比孤立词汇更接近真实体验", view: "overview", extra: "flow" }
  ],
  ja: [
    { kicker: "序章 · VADモデル", title: "感情はラベルだけでなく、空間上の一点として表せる", body: "VAD は感情を表す次元モデルです。感情を“幸福”や“怒り”というカテゴリだけに分けるのではなく、快—不快、覚醒度、制御感という3つの連続次元で位置づけます。したがって、各感情は3次元空間上の一つの座標として表現できます。", stat: "V · A · D", statLabel: "3つの連続次元が感情の3次元座標を構成する", view: "empty", extra: "vad" },
    { kicker: "第1章 · 出発点", title: "同じ VAD でも、同じものなのか？", body: "語彙ノルムは言葉の語意座標を、誘発データは映像中の実際の感受を記録します。感情計算では両者を直接交換できるとしがちですが、この前提は系統的に検証されていません。", stat: "0", statLabel: "2種類の座標を直接対応させた既発研究数", view: "empty" },
    { kicker: "第2章 · 方法", title: "2種類の座標を同じ立方体へ", body: "共通する9感情について、NRC-VAD の語意座標と DREAMER の映像誘発体験の平均を、同じ [−1, 1] の範囲に変換しました。", stat: "9感情 · 414試行 · 3次元", statLabel: "23名 × 18本の映像；全座標を −1 から +1 に統一", view: "frame" },
    { kicker: "第3章 · 概観", title: "構造は似ているが、系統的にずれる", body: "全体の形状は似ていますが、体験点は中心へ収束し、感情ごとのずれも大きく異なります。立方体=語意、球=体験、矢印=偏移です。", stat: "0.49 → 1.12", statLabel: "happiness から sadness までの3次元距離", view: "overview" },
    { kicker: "第4章 · 中核結果", title: "すべての次元が移行可能ではない", body: "V は安定した架け橋、A は順序を保つものの体験スケールが圧縮、D は対応が見られません。“VAD は移行できる”という前提は、1.5次元でしか成立しません。", stat: "1.5 / 3", statLabel: "直接または校正後の移行を支持する次元", view: "v", extra: "dimensions" },
    { kicker: "第5章 · 測定境界", title: "語意の“支配” ≠ 体験の“制御”", body: "D の負の結果そのものが発見です。語意空間の支配感と体験評価の制御感は、異なる構成概念かもしれません。全体スケールを校正後も calmness の残差が最大でした。", stat: "0.759", statLabel: "calmness の校正後残差（9感情中最大）", view: "d", focus: 3 },
    { kicker: "第6章 · 意義", title: "境界の発見から、メカニズムの検証へ", body: "“構造相関 → 全体スケール映射 → 校正残差”の3段階監査枠組みを提案します。次は同一参加者内で“語彙連想 → 概念プロトタイプ → 誘発体験”を対応させ、ずれの発生層を検証します。", stat: "H1", statLabel: "概念プロトタイプは単語より実際の体験に近い", view: "overview", extra: "flow" }
  ]
};

const COLORS = [0x1b8f83, 0xd5972e, 0xb64b49, 0x4d79a7, 0x7b6bb0, 0xd06e49, 0x397f9e, 0x7b5b48, 0x6c7380];
const SCALE = 3;
const canvas = document.querySelector("#scene");
const sceneWrap = document.querySelector("#scene-wrap");
const labelsRoot = document.querySelector("#labels");
const tooltip = document.querySelector("#tooltip");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setClearColor(0xeef1f2, 1);
renderer.outputColorSpace = THREE.SRGBColorSpace;

const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0xeef1f2, 13, 22);
const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
const defaultCamera = new THREE.Vector3(8.2, 6.6, 8.8);
camera.position.copy(defaultCamera);

const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.minDistance = 5.2;
controls.maxDistance = 18;
controls.target.set(0, 0, 0);

scene.add(new THREE.HemisphereLight(0xffffff, 0x9ca9ad, 2.2));
const keyLight = new THREE.DirectionalLight(0xffffff, 2.8);
keyLight.position.set(5, 8, 6);
scene.add(keyLight);

const world = new THREE.Group();
scene.add(world);

const cubeEdges = new THREE.LineSegments(
  new THREE.EdgesGeometry(new THREE.BoxGeometry(6, 6, 6)),
  new THREE.LineBasicMaterial({ color: 0x9da7ac, transparent: true, opacity: 0.52 })
);
world.add(cubeEdges);

function addGridPlane(rotation, color = 0xbac2c6) {
  const grid = new THREE.GridHelper(6, 6, color, color);
  grid.material.transparent = true;
  grid.material.opacity = 0.13;
  grid.rotation.set(...rotation);
  world.add(grid);
}
addGridPlane([0, 0, 0]);
addGridPlane([Math.PI / 2, 0, 0]);
addGridPlane([0, 0, Math.PI / 2]);

function axisLine(from, to, color) {
  const geometry = new THREE.BufferGeometry().setFromPoints([from, to]);
  const line = new THREE.Line(geometry, new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.8 }));
  world.add(line);
}
axisLine(new THREE.Vector3(-3.4, 0, 0), new THREE.Vector3(3.4, 0, 0), 0xb44b45);
axisLine(new THREE.Vector3(0, -3.4, 0), new THREE.Vector3(0, 3.4, 0), 0x177f73);
axisLine(new THREE.Vector3(0, 0, -3.4), new THREE.Vector3(0, 0, 3.4), 0x386ea0);

const axisLabels = [
  ["V+", new THREE.Vector3(3.55, 0, 0)], ["V−", new THREE.Vector3(-3.55, 0, 0)],
  ["A+", new THREE.Vector3(0, 3.55, 0)], ["A−", new THREE.Vector3(0, -3.55, 0)],
  ["D+", new THREE.Vector3(0, 0, 3.55)], ["D−", new THREE.Vector3(0, 0, -3.55)]
].map(([text, position]) => {
  const element = document.createElement("span");
  element.className = "axis-label";
  element.textContent = text;
  labelsRoot.appendChild(element);
  return { element, position };
});

const pointGeometry = new THREE.SphereGeometry(0.12, 28, 20);
const cubeGeometry = new THREE.BoxGeometry(0.20, 0.20, 0.20);
const objects = [];
const emotionGroups = [];

function toPosition(values) {
  return new THREE.Vector3(values[0] * SCALE, values[1] * SCALE, values[2] * SCALE);
}

DATA.forEach((item, index) => {
  const group = new THREE.Group();
  group.userData = { index, item };
  world.add(group);

  const nrcMaterial = new THREE.MeshStandardMaterial({ color: 0x626a73, roughness: 0.45, metalness: 0.05, transparent: true });
  const dreamerMaterial = new THREE.MeshStandardMaterial({ color: COLORS[index], roughness: 0.34, metalness: 0.04, transparent: true });
  const nrc = new THREE.Mesh(cubeGeometry, nrcMaterial);
  const dreamer = new THREE.Mesh(pointGeometry, dreamerMaterial);
  nrc.position.copy(toPosition(item.nrc));
  dreamer.position.copy(toPosition(item.dreamer));
  nrc.userData = { index, source: "NRC" };
  dreamer.userData = { index, source: "DREAMER" };
  group.add(nrc, dreamer);
  objects.push(nrc, dreamer);

  const direction = dreamer.position.clone().sub(nrc.position);
  const length = direction.length();
  const arrow = new THREE.ArrowHelper(direction.clone().normalize(), nrc.position, length, COLORS[index], 0.14, 0.08);
  arrow.line.material.transparent = true;
  arrow.cone.material.transparent = true;
  arrow.userData = { index, source: "偏移箭头" };
  group.add(arrow);
  objects.push(arrow.line, arrow.cone);
  arrow.line.userData = arrow.userData;
  arrow.cone.userData = arrow.userData;

  const label = document.createElement("span");
  label.className = "point-label";
  label.textContent = `${item.zh} ${item.emotion}`;
  labelsRoot.appendChild(label);
  emotionGroups.push({ group, nrc, dreamer, arrow, label, item, index });
});

const select = document.querySelector("#emotion-select");
const allOption = document.createElement("option");
allOption.value = "all";
select.appendChild(allOption);
DATA.forEach((item, index) => {
  const option = document.createElement("option");
  option.value = String(index);
  select.appendChild(option);
});
select.value = "0";

let selectedIndex = 0;
let currentLanguage = "ja";
let currentMode = "tour";
let currentChapter = 0;
let currentProjection = "3d";
let hoveredObject = null;
const raycaster = new THREE.Raycaster();
raycaster.params.Line.threshold = 0.12;
const pointer = new THREE.Vector2();
const targetCamera = defaultCamera.clone();
const targetControl = new THREE.Vector3();
let cameraTransition = false;

emotionGroups.forEach((entry) => {
  entry.baseNrc = entry.nrc.position.clone();
  entry.baseDreamer = entry.dreamer.position.clone();
  entry.targetNrc = entry.baseNrc.clone();
  entry.targetDreamer = entry.baseDreamer.clone();
});

function localName(item) {
  return currentLanguage === "ja" ? item.ja : item.zh;
}

function updateArrow(entry) {
  const direction = entry.dreamer.position.clone().sub(entry.nrc.position);
  const length = Math.max(direction.length(), 0.001);
  entry.arrow.position.copy(entry.nrc.position);
  entry.arrow.setDirection(direction.normalize());
  entry.arrow.setLength(length, 0.14, 0.08);
}

function buildResidualChart() {
  const root = document.querySelector("#residual-chart");
  root.replaceChildren();
  [...DATA].map((item, index) => ({ item, index })).sort((a, b) => b.item.calibrated - a.item.calibrated).forEach(({ item, index }) => {
    const row = document.createElement("div");
    row.className = `residual-row${selectedIndex === index ? " active" : ""}`;
    row.dataset.index = String(index);
    row.innerHTML = `<span>${localName(item)}</span><div><i style="width:${item.calibrated / 0.8 * 100}%"></i></div><strong>${item.calibrated.toFixed(3)}</strong>`;
    row.addEventListener("click", () => setSelection(String(index), true));
    root.appendChild(row);
  });
}

function updateLanguage() {
  const copy = COPY[currentLanguage];
  const ja = currentLanguage === "ja";
  document.documentElement.lang = currentLanguage === "ja" ? "ja" : "zh-CN";
  document.title = currentLanguage === "ja" ? "DREAMER × NRC VAD 3次元対照" : "DREAMER × NRC VAD 三维对照";
  document.querySelector(".topbar h1").textContent = copy.title;
  document.querySelector(".topbar p").textContent = copy.subtitle;
  document.querySelector("#tour-mode").textContent = copy.tour;
  document.querySelector("#explore-mode").textContent = copy.explore;
  document.querySelector("#language-toggle").textContent = currentLanguage === "zh" ? "JA" : "中";
  document.querySelector(".selector-section label").textContent = copy.select;
  document.querySelector(".residual-head h3").textContent = copy.residual;
  document.querySelector(".residual-head span").textContent = copy.residualHint;
  document.querySelector(".tour-hint").textContent = copy.hint;
  const legend = document.querySelectorAll(".scene-legend span");
  [ja ? "NRC 語意" : "NRC 词义", ja ? "DREAMER 体験" : "DREAMER 体验", ja ? "偏移方向" : "偏移方向"].forEach((text, index) => {
    const icon = legend[index].querySelector("i");
    legend[index].replaceChildren(icon, document.createTextNode(text));
  });
  const axisKeys = document.querySelectorAll(".axis-key span");
  [ja ? "V 快—不快" : "V 愉悦度", ja ? "A 覚醒度" : "A 唤醒度", ja ? "D 制御感" : "D 控制感"].forEach((text, index) => { axisKeys[index].textContent = text; });
  const controlLabels = document.querySelectorAll(".mode-controls label");
  const controlTexts = ja ? ["NRC", "DREAMER", "偏移矢印", "感情ラベル", "自動回転"] : ["NRC", "DREAMER", "偏移箭头", "情绪标签", "自动旋转"];
  controlLabels.forEach((label, index) => {
    const nodes = [...label.childNodes].filter((node) => node.nodeType !== Node.TEXT_NODE);
    label.replaceChildren(...nodes, document.createTextNode(controlTexts[index]));
  });
  const tableHead = document.querySelector(".table-head").children;
  tableHead[0].textContent = ja ? "出典" : "来源";
  const sourceRows = document.querySelectorAll(".coordinate-table > div:not(.table-head) span");
  const sourceNames = ["NRC", ja ? "体験" : "体验"];
  sourceRows.forEach((row, index) => {
    const icon = row.querySelector("i");
    row.replaceChildren(icon, document.createTextNode(sourceNames[index]));
  });
  document.querySelector(".delta-section h3").textContent = ja ? "体験 − 語意" : "体验 − 词义";
  const metricLabels = document.querySelectorAll(".metrics span");
  metricLabels[0].textContent = ja ? "元の3次元距離" : "原始三维距离";
  metricLabels[1].textContent = ja ? "スケール校正残差" : "尺度校准残差";
  document.querySelector(".panel-note").innerHTML = ja ? "ドラッグ：回転 · ホイール：ズーム · 点または矢印：フォーカス<br>D は DREAMER ファイルの報告方向で表示。" : "拖动旋转 · 滚轮缩放 · 点击点或箭头聚焦<br>D 按 DREAMER 文件报告方向显示。";
  allOption.textContent = copy.all;
  DATA.forEach((item, index) => {
    select.options[index + 1].textContent = `${String(index + 1).padStart(2, "0")} · ${localName(item)} ${item.emotion}`;
    emotionGroups[index].label.textContent = `${localName(item)} ${item.emotion}`;
  });
  const kpiNotes = [copy.stable, copy.compressed, copy.failed];
  document.querySelectorAll("#kpi-strip em").forEach((element, index) => { element.textContent = kpiNotes[index]; });
  if (selectedIndex !== null) updatePanel(selectedIndex);
  buildResidualChart();
  renderChapter();
}

function signed(value) {
  return `${value >= 0 ? "+" : "−"}${Math.abs(value).toFixed(3)}`;
}

function updateDeltaBar(id, value) {
  const bar = document.querySelector(id);
  const width = Math.min(Math.abs(value) / 2, 0.5) * 100;
  bar.style.width = `${width}%`;
  bar.style.left = value >= 0 ? "50%" : `${50 - width}%`;
  bar.style.background = value >= 0 ? "#16857b" : "#b64b49";
}

function updatePanel(index) {
  const item = DATA[index];
  const delta = item.dreamer.map((value, i) => value - item.nrc[i]);
  document.querySelector("#emotion-rank").textContent = String(index + 1).padStart(2, "0");
  document.querySelector("#emotion-name").textContent = localName(item);
  document.querySelector("#emotion-en").textContent = item.emotion;
  document.querySelector("#distance-badge").textContent = item.distance.toFixed(2);
  ["v", "a", "d"].forEach((dim, i) => {
    document.querySelector(`#nrc-${dim}`).textContent = item.nrc[i].toFixed(3);
    document.querySelector(`#dreamer-${dim}`).textContent = item.dreamer[i].toFixed(3);
    document.querySelector(`#delta-${dim}`).textContent = signed(delta[i]);
    updateDeltaBar(`#bar-${dim}`, delta[i]);
  });
  document.querySelector("#raw-distance").textContent = item.distance.toFixed(3);
  document.querySelector("#calibrated-distance").textContent = item.calibrated.toFixed(3);
}

function setSelection(value, moveCamera = false) {
  selectedIndex = value === "all" ? null : Number(value);
  select.value = value;
  emotionGroups.forEach((entry, index) => {
    const active = selectedIndex === null || index === selectedIndex;
    const opacity = active ? 1 : 0.10;
    entry.nrc.material.opacity = opacity;
    entry.dreamer.material.opacity = opacity;
    entry.arrow.line.material.opacity = active ? 0.85 : 0.06;
    entry.arrow.cone.material.opacity = active ? 0.95 : 0.06;
    entry.label.classList.toggle("muted", !active);
    const scale = selectedIndex === index ? 1.55 : 1;
    entry.nrc.scale.setScalar(scale);
    entry.dreamer.scale.setScalar(scale);
  });
  if (selectedIndex !== null) {
    updatePanel(selectedIndex);
    if (moveCamera) {
      const item = emotionGroups[selectedIndex];
      const midpoint = item.nrc.position.clone().add(item.dreamer.position).multiplyScalar(0.5);
      targetControl.copy(midpoint);
      cameraTransition = true;
    }
  }
  buildResidualChart();
}

function setVisibility() {
  const showNrc = document.querySelector("#show-nrc").checked;
  const showDreamer = document.querySelector("#show-dreamer").checked;
  const showVectors = document.querySelector("#show-vectors").checked;
  const showLabels = document.querySelector("#show-labels").checked;
  emotionGroups.forEach((entry) => {
    entry.nrc.visible = showNrc;
    entry.dreamer.visible = showDreamer;
    entry.arrow.visible = showVectors;
    entry.label.classList.toggle("hidden", !showLabels);
  });
}

function projectionPosition(entry, source, projection) {
  if (projection === "3d") return source === "nrc" ? entry.baseNrc.clone() : entry.baseDreamer.clone();
  const dim = { v: 0, a: 1, d: 2 }[projection];
  const value = source === "nrc" ? entry.item.nrc[dim] : entry.item.dreamer[dim];
  return new THREE.Vector3(value * SCALE, (4 - entry.index) * 0.55, 0);
}

function setProjection(projection, immediate = false) {
  currentProjection = projection;
  emotionGroups.forEach((entry) => {
    entry.targetNrc.copy(projectionPosition(entry, "nrc", projection));
    entry.targetDreamer.copy(projectionPosition(entry, "dreamer", projection));
    if (immediate) {
      entry.nrc.position.copy(entry.targetNrc);
      entry.dreamer.position.copy(entry.targetDreamer);
      updateArrow(entry);
    }
  });
  document.querySelectorAll("[data-projection]").forEach((button) => {
    button.classList.toggle("active", button.dataset.projection === projection);
  });
  axisLabels.forEach(({ element }) => { element.style.display = projection === "3d" ? "block" : "none"; });
  if (projection === "3d") {
    targetCamera.copy(defaultCamera);
  } else {
    targetCamera.set(0, 0, 10.8);
  }
  targetControl.set(0, 0, 0);
  cameraTransition = true;
}

function setTourVisibility(view) {
  const hasData = view !== "empty" && view !== "frame";
  emotionGroups.forEach((entry) => {
    entry.group.visible = hasData;
    entry.label.classList.toggle("hidden", !hasData || !document.querySelector("#show-labels").checked);
  });
  cubeEdges.material.opacity = view === "empty" ? 0.1 : 0.52;
}

function renderChapterExtra(chapter) {
  const root = document.querySelector("#chapter-extra");
  if (chapter.extra === "vad") {
    const items = currentLanguage === "zh"
      ? [
          ["V", "Valence · 愉悦度", "−1 不愉快", "+1 愉快", "情绪是消极还是积极"],
          ["A", "Arousal · 唤醒度", "−1 平静", "+1 兴奋", "身心激活程度的高低"],
          ["D", "Dominance · 控制感", "−1 被控制", "+1 掌控", "感到无力还是能掌控情境"]
        ]
      : [
          ["V", "Valence · 快—不快", "−1 不快", "+1 快", "感情がネガティブかポジティブか"],
          ["A", "Arousal · 覚醒度", "−1 平静", "+1 興奮", "心身がどの程度活性化しているか"],
          ["D", "Dominance · 制御感", "−1 制御される", "+1 掌控する", "状況に対する無力感と制御感" ]
        ];
    root.innerHTML = `<div class="vad-intro">${items.map(([dim, name, low, high, description]) => `
      <article class="vad-card vad-${dim.toLowerCase()}">
        <b>${dim}</b><div><strong>${name}</strong><p>${description}</p><small><span>${low}</span><i></i><span>${high}</span></small></div>
      </article>`).join("")}</div>`;
  } else if (chapter.extra === "dimensions") {
    const labels = currentLanguage === "zh"
      ? [["V", "r=.875", "强且稳定"], ["A", "r=.832", "有关联，斜率 .341"], ["D", "r=−.121", "未发现对应"]]
      : [["V", "r=.875", "強く安定"], ["A", "r=.832", "相関あり・傾き .341"], ["D", "r=−.121", "対応なし"]];
    root.innerHTML = `<div class="dimension-summary">${labels.map(([dim, value, note]) => `<button type="button" data-projection="${dim.toLowerCase()}"><b>${dim}</b><strong>${value}</strong><span>${note}</span></button>`).join("")}</div>`;
    root.querySelectorAll("[data-projection]").forEach((button) => button.addEventListener("click", () => setProjection(button.dataset.projection)));
  } else if (chapter.extra === "flow") {
    root.innerHTML = currentLanguage === "zh" ? "<strong>词汇联想</strong> → <strong>概念原型</strong> → <strong>诱发体验</strong>" : "<strong>語彙連想</strong> → <strong>概念プロトタイプ</strong> → <strong>誘発体験</strong>";
  } else {
    root.replaceChildren();
  }
}

function applyChapterState(chapter) {
  setTourVisibility(chapter.view);
  if (chapter.view === "empty" || chapter.view === "frame") {
    setProjection("3d");
    setSelection("all");
    controls.autoRotate = false;
  } else if (chapter.view === "overview") {
    setProjection("3d");
    setSelection("all");
    controls.autoRotate = currentChapter === 3;
  } else {
    setProjection(chapter.view);
    setSelection(chapter.focus === undefined ? "all" : String(chapter.focus));
    controls.autoRotate = false;
  }
  document.querySelector("#auto-rotate").checked = controls.autoRotate;
}

function renderChapter() {
  const chapters = CHAPTERS[currentLanguage];
  const chapter = chapters[currentChapter];
  document.querySelector("#chapter-count").textContent = `${String(currentChapter + 1).padStart(2, "0")} / ${String(chapters.length).padStart(2, "0")}`;
  document.querySelector("#chapter-progress").style.width = `${(currentChapter + 1) / chapters.length * 100}%`;
  document.querySelector("#chapter-kicker").textContent = chapter.kicker;
  document.querySelector("#chapter-title").textContent = chapter.title;
  document.querySelector("#chapter-body").textContent = chapter.body;
  document.querySelector("#chapter-stat strong").textContent = chapter.stat;
  document.querySelector("#chapter-stat span").textContent = chapter.statLabel;
  document.querySelector("#chapter-prev").disabled = currentChapter === 0;
  document.querySelector("#chapter-next").disabled = currentChapter === chapters.length - 1;
  document.querySelectorAll("#chapter-dots button").forEach((button, index) => button.classList.toggle("active", index === currentChapter));
  renderChapterExtra(chapter);
  if (currentMode === "tour") applyChapterState(chapter);
}

function setChapter(index) {
  currentChapter = Math.max(0, Math.min(CHAPTERS[currentLanguage].length - 1, index));
  renderChapter();
}

function setMode(mode) {
  currentMode = mode;
  const touring = mode === "tour";
  document.querySelector("#tour-mode").classList.toggle("active", touring);
  document.querySelector("#explore-mode").classList.toggle("active", !touring);
  document.querySelector("#tour-panel").classList.toggle("closed", !touring);
  document.querySelector("#panel").classList.toggle("closed", touring);
  if (touring) {
    renderChapter();
  } else {
    emotionGroups.forEach((entry) => { entry.group.visible = true; });
    setProjection("3d");
    setSelection("0");
    controls.autoRotate = false;
    document.querySelector("#auto-rotate").checked = false;
    setVisibility();
  }
}

const dotsRoot = document.querySelector("#chapter-dots");
for (let index = 0; index < CHAPTERS.ja.length; index += 1) {
  const button = document.createElement("button");
  button.type = "button";
  button.setAttribute("aria-label", `Chapter ${index + 1}`);
  button.addEventListener("click", () => setChapter(index));
  dotsRoot.appendChild(button);
}

select.addEventListener("change", () => setSelection(select.value, true));
document.querySelector("#tour-mode").addEventListener("click", () => setMode("tour"));
document.querySelector("#explore-mode").addEventListener("click", () => setMode("explore"));
document.querySelector("#language-toggle").addEventListener("click", () => {
  currentLanguage = currentLanguage === "zh" ? "ja" : "zh";
  updateLanguage();
});
document.querySelector("#chapter-prev").addEventListener("click", () => setChapter(currentChapter - 1));
document.querySelector("#chapter-next").addEventListener("click", () => setChapter(currentChapter + 1));
document.querySelectorAll("#projection-controls [data-projection], #kpi-strip [data-projection]").forEach((button) => {
  button.addEventListener("click", () => setProjection(button.dataset.projection));
});
["#show-nrc", "#show-dreamer", "#show-vectors", "#show-labels"].forEach((id) => {
  document.querySelector(id).addEventListener("change", setVisibility);
});
document.querySelector("#auto-rotate").addEventListener("change", (event) => {
  controls.autoRotate = event.target.checked;
  controls.autoRotateSpeed = 0.75;
});
document.querySelector("#reset-camera").addEventListener("click", () => {
  targetCamera.copy(currentProjection === "3d" ? defaultCamera : new THREE.Vector3(0, 0, 10.8));
  targetControl.set(0, 0, 0);
  camera.position.copy(targetCamera);
  controls.target.copy(targetControl);
  cameraTransition = false;
  controls.update();
});
document.querySelector("#toggle-panel").addEventListener("click", () => {
  document.querySelector("#panel").classList.toggle("closed");
});

window.addEventListener("keydown", (event) => {
  if (event.target.matches("select, input, button")) return;
  if (currentMode === "tour" && event.key === "ArrowRight") setChapter(currentChapter + 1);
  if (currentMode === "tour" && event.key === "ArrowLeft") setChapter(currentChapter - 1);
  if (event.code === "Space") {
    event.preventDefault();
    controls.autoRotate = !controls.autoRotate;
    document.querySelector("#auto-rotate").checked = controls.autoRotate;
  }
});

function updatePointer(event) {
  const rect = canvas.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
}

canvas.addEventListener("pointermove", (event) => {
  updatePointer(event);
  raycaster.setFromCamera(pointer, camera);
  const hit = raycaster.intersectObjects(objects, false)[0];
  hoveredObject = hit?.object ?? null;
  if (!hit || hit.object.userData.index === undefined) {
    tooltip.style.display = "none";
    canvas.style.cursor = "grab";
    return;
  }
  const { index, source } = hit.object.userData;
  const item = DATA[index];
  const coords = source === "NRC" ? item.nrc : source === "DREAMER" ? item.dreamer : null;
  tooltip.innerHTML = `<strong>${localName(item)} ${item.emotion}</strong>${source}${coords ? `<br>V ${coords[0].toFixed(3)} · A ${coords[1].toFixed(3)} · D ${coords[2].toFixed(3)}` : `<br>${currentLanguage === "ja" ? "3次元距離" : "三维距离"} ${item.distance.toFixed(3)}`}`;
  tooltip.style.display = "block";
  tooltip.style.left = `${Math.min(event.clientX - sceneWrap.offsetLeft + 14, sceneWrap.clientWidth - 190)}px`;
  tooltip.style.top = `${Math.max(event.clientY - sceneWrap.offsetTop - 12, 8)}px`;
  canvas.style.cursor = "pointer";
});

canvas.addEventListener("click", () => {
  if (hoveredObject?.userData.index !== undefined) {
    setSelection(String(hoveredObject.userData.index), true);
  }
});

function projectLabel(element, position, offsetY = 0) {
  const projected = position.clone().project(camera);
  const x = (projected.x * 0.5 + 0.5) * sceneWrap.clientWidth;
  const y = (-projected.y * 0.5 + 0.5) * sceneWrap.clientHeight + offsetY;
  element.style.left = `${x}px`;
  element.style.top = `${y}px`;
  element.style.visibility = projected.z > 1 ? "hidden" : "visible";
}

function resize() {
  const width = sceneWrap.clientWidth;
  const height = sceneWrap.clientHeight;
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

function animate() {
  requestAnimationFrame(animate);
  if (cameraTransition) {
    camera.position.lerp(targetCamera, 0.085);
    controls.target.lerp(targetControl, 0.1);
    if (camera.position.distanceTo(targetCamera) < 0.025 && controls.target.distanceTo(targetControl) < 0.015) {
      camera.position.copy(targetCamera);
      controls.target.copy(targetControl);
      cameraTransition = false;
    }
  }
  controls.update();
  emotionGroups.forEach((entry) => {
    entry.nrc.position.lerp(entry.targetNrc, 0.09);
    entry.dreamer.position.lerp(entry.targetDreamer, 0.09);
    updateArrow(entry);
    const midpoint = entry.nrc.position.clone().add(entry.dreamer.position).multiplyScalar(0.5);
    projectLabel(entry.label, midpoint, -13);
  });
  axisLabels.forEach((entry) => projectLabel(entry.element, entry.position));
  renderer.render(scene, camera);
}

window.addEventListener("resize", resize);
resize();
updateLanguage();
setMode("tour");
animate();

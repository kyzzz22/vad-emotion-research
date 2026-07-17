import * as THREE from "three";
import { OrbitControls } from "three/addons/OrbitControls.js";

const DATA = [
  { emotion: "happiness", zh: "幸福", nrc: [0.920, 0.464, 0.700], dreamer: [0.728261, 0.217391, 0.326087], distance: 0.487228, calibrated: 0.492057 },
  { emotion: "excitement", zh: "兴奋", nrc: [0.792, 0.368, 0.462], dreamer: [0.217391, 0.260870, 0.195652], distance: 0.642334, calibrated: 0.211803 },
  { emotion: "anger", zh: "愤怒", nrc: [-0.666, 0.730, 0.314], dreamer: [-0.576087, 0.043478, 0.184783], distance: 0.704339, calibrated: 0.320254 },
  { emotion: "calmness", zh: "平静", nrc: [0.868, -0.895, -0.199], dreamer: [0.282609, -0.445652, -0.326087], distance: 0.748831, calibrated: 0.759439 },
  { emotion: "amusement", zh: "欢乐", nrc: [0.858, 0.674, 0.606], dreamer: [0.630435, 0.108696, 0.130435], distance: 0.772992, calibrated: 0.359623 },
  { emotion: "fear", zh: "恐惧", nrc: [-0.854, 0.680, -0.414], dreamer: [-0.369565, 0.336957, 0.336957], distance: 0.957231, calibrated: 0.283444 },
  { emotion: "surprise", zh: "惊讶", nrc: [0.750, 0.750, 0.124], dreamer: [-0.076087, 0.228261, 0.065217], distance: 0.978819, calibrated: 0.497240 },
  { emotion: "disgust", zh: "厌恶", nrc: [-0.896, 0.550, -0.366], dreamer: [-0.282609, 0.282609, 0.413043], distance: 1.026964, calibrated: 0.448176 },
  { emotion: "sadness", zh: "悲伤", nrc: [-0.896, -0.424, -0.672], dreamer: [-0.771739, 0.000000, 0.358696], distance: 1.121405, calibrated: 0.432592 }
];

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
allOption.textContent = "全部情绪";
select.appendChild(allOption);
DATA.forEach((item, index) => {
  const option = document.createElement("option");
  option.value = String(index);
  option.textContent = `${String(index + 1).padStart(2, "0")} · ${item.zh} ${item.emotion}`;
  select.appendChild(option);
});
select.value = "0";

let selectedIndex = 0;
let hoveredObject = null;
const raycaster = new THREE.Raycaster();
raycaster.params.Line.threshold = 0.12;
const pointer = new THREE.Vector2();

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
  document.querySelector("#emotion-name").textContent = item.zh;
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
      controls.target.copy(midpoint);
    }
  }
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

select.addEventListener("change", () => setSelection(select.value, true));
["#show-nrc", "#show-dreamer", "#show-vectors", "#show-labels"].forEach((id) => {
  document.querySelector(id).addEventListener("change", setVisibility);
});
document.querySelector("#auto-rotate").addEventListener("change", (event) => {
  controls.autoRotate = event.target.checked;
  controls.autoRotateSpeed = 0.75;
});
document.querySelector("#reset-camera").addEventListener("click", () => {
  camera.position.copy(defaultCamera);
  controls.target.set(0, 0, 0);
  controls.update();
});
document.querySelector("#toggle-panel").addEventListener("click", () => {
  document.querySelector("#panel").classList.toggle("closed");
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
  tooltip.innerHTML = `<strong>${item.zh} ${item.emotion}</strong>${source}${coords ? `<br>V ${coords[0].toFixed(3)} · A ${coords[1].toFixed(3)} · D ${coords[2].toFixed(3)}` : `<br>三维距离 ${item.distance.toFixed(3)}`}`;
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
  controls.update();
  emotionGroups.forEach((entry) => {
    const midpoint = entry.nrc.position.clone().add(entry.dreamer.position).multiplyScalar(0.5);
    projectLabel(entry.label, midpoint, -13);
  });
  axisLabels.forEach((entry) => projectLabel(entry.element, entry.position));
  renderer.render(scene, camera);
}

window.addEventListener("resize", resize);
resize();
setSelection("0");
setVisibility();
animate();

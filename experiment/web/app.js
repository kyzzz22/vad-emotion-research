"use strict";

const state = {
  config: null,
  trials: [],
  trialIndex: 0,
  ratings: [],
  events: [],
  participantId: "",
  sessionId: "",
  sessionType: "",
  testMode: new URLSearchParams(location.search).get("test") === "1",
  simulateMedia: new URLSearchParams(location.search).get("test") === "1"
    && new URLSearchParams(location.search).get("media") !== "real",
  ratingStartedAt: 0,
  inducedPartial: null,
  markerPromises: [],
  comprehensionByCondition: {},
};

const app = document.getElementById("app");
const setupView = document.getElementById("setupView");
const taskView = document.getElementById("taskView");
const setupError = document.getElementById("setupError");

function markerConfigured() {
  return typeof window.a2MarkerHook === "function";
}

function setMarkerStatus() {
  const node = document.getElementById("markerStatus");
  if (markerConfigured()) {
    node.textContent = "事件接口已配置";
    node.classList.add("ready");
  } else {
    node.textContent = "事件接口未配置";
    node.classList.remove("ready");
  }
}

function eventCode(name) {
  const row = state.config.event_codes.find((item) => item.event_name === name);
  return row ? row.event_code : "";
}

function currentTrial() {
  return state.trials[state.trialIndex] || null;
}

function emit(name, extra = {}) {
  const trial = currentTrial() || {};
  const record = {
    participant_id: state.participantId,
    session_id: state.sessionId,
    session_type: state.sessionType,
    sequence_id: trial.sequence_id || "",
    session_order: trial.session_order || "",
    block_order: trial.block_order || "",
    item_order: trial.item_order || "",
    event_name: name,
    event_code: eventCode(name),
    utc_iso: new Date().toISOString(),
    performance_ms: performance.now().toFixed(3),
    trial_index: state.trialIndex + 1,
    concept_id: trial.concept_id || "",
    stimulus_id: trial.stimulus_id || "",
    marker_hook_configured: markerConfigured() ? 1 : 0,
    marker_hook_result: markerConfigured() ? "pending" : "not_configured",
    test_mode: state.testMode ? 1 : 0,
    ...extra,
  };
  state.events.push(record);
  if (markerConfigured()) {
    try {
      const markerPromise = Promise.resolve(window.a2MarkerHook({ ...record })).then(
        () => { record.marker_hook_result = "sent"; },
        (error) => { record.marker_hook_result = `error:${String(error)}`; },
      );
      state.markerPromises.push(markerPromise);
    } catch (error) {
      record.marker_hook_result = `error:${String(error)}`;
    }
  }
}

function taskHeader(trial) {
  const progress = `${Math.min(state.trialIndex + 1, state.trials.length)} / ${state.trials.length}`;
  return `<div class="task-header"><span>${state.participantId} · ${state.sessionId} · ${state.sessionType}</span><span>${progress}</span></div>`;
}

function instructionFor(condition) {
  if (condition === "lexical") {
    return "请根据这个词本身通常带给你的情感联想作答，不要刻意回忆某个具体事件。";
  }
  if (condition === "prototype") {
    return "请想象一个人典型地处于这种情绪状态。评价这种典型体验，不要刻意回忆某个具体事件。";
  }
  return "请只报告观看视频时你自己实际感受到的状态，不评价视频内容，也不回答它本来应该使人产生什么情绪。";
}

function comprehensionPrompt(condition) {
  return {
    lexical: { question: "本区块要求你主要评价什么？", correct: "lexical" },
    prototype: { question: "本区块要求你主要评价什么？", correct: "prototype" },
    induced: { question: "观看视频后，VAD题目要求你主要评价什么？", correct: "induced" },
  }[condition];
}

function renderComprehensionCheck(condition, onDone) {
  const trial = currentTrial();
  const prompt = comprehensionPrompt(condition);
  taskView.innerHTML = `${taskHeader(trial)}<h2>评分对象核对</h2><p class="instruction">${instructionFor(condition)}</p><form id="comprehensionForm" class="setup-form"><fieldset><legend>${prompt.question}</legend><label><input type="radio" name="comprehension" value="lexical" required> 这个词本身通常带来的情感联想</label><label><input type="radio" name="comprehension" value="prototype" required> 一个人典型处于该情绪时的体验</label><label><input type="radio" name="comprehension" value="induced" required> 我刚才观看视频时实际感受到的状态</label></fieldset><div id="comprehensionFeedback"></div><div class="actions"><button class="danger" type="button" id="stopButton">停止实验</button><button class="primary" type="submit">确认</button></div></form>`;
  document.getElementById("stopButton").addEventListener("click", stopSession);
  document.getElementById("comprehensionForm").addEventListener("submit", (event) => {
    event.preventDefault();
    const selected = event.currentTarget.querySelector('input[name="comprehension"]:checked').value;
    const correct = selected === prompt.correct ? 1 : 0;
    state.comprehensionByCondition[condition] = { selected, correct };
    emit("INSTRUCTION_CHECK", { instruction_condition: condition, selected_response: selected, correct });
    if (correct) {
      onDone();
      return;
    }
    const feedback = document.getElementById("comprehensionFeedback");
    feedback.innerHTML = `<p class="error">请注意本区块的评分对象：${instructionFor(condition)}</p><div class="actions"><button class="primary" id="understoodButton" type="button">我已理解，继续</button></div>`;
    event.currentTarget.querySelector('button[type="submit"]').disabled = true;
    document.getElementById("understoodButton").addEventListener("click", onDone, { once: true });
  }, { once: true });
}

function scaleNode(item, prefix) {
  const fragment = document.getElementById("scaleTemplate").content.cloneNode(true);
  fragment.querySelector("legend").textContent = item.prompt_zh;
  fragment.querySelector(".min-label").textContent = `1 ${item.min_label_zh}`;
  fragment.querySelector(".max-label").textContent = `9 ${item.max_label_zh}`;
  const options = fragment.querySelector(".scale-options");
  for (let value = 1; value <= 9; value += 1) {
    const label = document.createElement("label");
    label.className = "scale-option";
    label.innerHTML = `<input type="radio" name="${prefix}_${item.construct}" value="${value}" required><span>${value}</span>`;
    options.appendChild(label);
  }
  return fragment;
}

function renderRatingForm(items, prefix, heading, onSubmit, leadText = "") {
  const trial = currentTrial();
  taskView.innerHTML = `${taskHeader(trial)}<h2>${heading}</h2>${leadText ? `<p class="instruction">${leadText}</p>` : ""}<form id="ratingForm" class="rating-form"></form>`;
  const form = document.getElementById("ratingForm");
  items.forEach((item) => form.appendChild(scaleNode(item, prefix)));
  const actions = document.createElement("div");
  actions.className = "actions";
  actions.innerHTML = '<button class="danger" type="button" id="stopButton">停止实验</button><button class="primary" type="submit">提交并继续</button>';
  form.appendChild(actions);
  document.getElementById("stopButton").addEventListener("click", stopSession);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const values = {};
    items.forEach((item) => {
      const selected = form.querySelector(`input[name="${prefix}_${item.construct}"]:checked`);
      values[item.construct] = Number(selected.value);
    });
    onSubmit(values);
  });
}

function primaryItems(condition) {
  return state.config.rating_items.filter(
    (item) => item.scope === condition && item.analysis_role === "primary_dimension",
  );
}

function secondaryItems() {
  return state.config.rating_items.filter(
    (item) => item.scope === "induced" && item.analysis_role !== "primary_dimension",
  );
}

function emptyRating(trial) {
  return {
    participant_id: state.participantId,
    sequence_id: trial.sequence_id,
    concept_id: trial.concept_id,
    condition: trial.condition,
    stimulus_id: trial.stimulus_id,
    session_id: trial.session_id,
    session_order: trial.session_order,
    block_order: trial.block_order,
    item_order: trial.item_order,
    valence: "",
    arousal: "",
    dominance: "",
    target_emotion_intensity: "",
    intensity_joy: "",
    intensity_amusement: "",
    intensity_tenderness: "",
    intensity_anger: "",
    intensity_sadness: "",
    intensity_fear: "",
    intensity_disgust: "",
    discomfort: "",
    familiarity: "",
    self_relevance: "",
    response_time_ms: "",
    attention_check: "",
    attention_check_rate: "",
    instruction_check_correct: state.comprehensionByCondition[trial.condition]?.correct ?? "",
    instruction_check_response: state.comprehensionByCondition[trial.condition]?.selected ?? "",
    notes: state.testMode ? "TEST_MODE" : "",
    test_mode: state.testMode ? 1 : 0,
  };
}

function renderSessionIntro() {
  const trial = currentTrial();
  const title = state.sessionType === "semantic" ? "情绪概念评价" : "视频诱发评价";
  const body = state.sessionType === "semantic"
    ? "本场次包含两个评价区块。每个题目都请根据当前区块的指令独立作答，不要复制先前答案。"
    : "本场次包含若干视频。部分内容可能引起负面情绪，你可以随时暂停、跳过或停止。";
  taskView.innerHTML = `${taskHeader(trial)}<h1>${title}</h1><p class="instruction">${body}</p><div class="actions"><button class="danger" id="stopButton">停止实验</button><button class="primary" id="continueButton">继续</button></div>`;
  document.getElementById("stopButton").addEventListener("click", stopSession);
  document.getElementById("continueButton").addEventListener("click", () => {
    if (state.sessionType === "semantic") renderBlockIntro();
    else renderComprehensionCheck("induced", startInducedTrial);
  });
}

function renderBlockIntro() {
  const trial = currentTrial();
  const label = trial.condition === "lexical" ? "词汇联想区块" : "典型体验区块";
  taskView.innerHTML = `${taskHeader(trial)}<h1>${label}</h1><p class="instruction">${instructionFor(trial.condition)}</p><div class="actions"><button class="danger" id="stopButton">停止实验</button><button class="primary" id="continueButton">开始区块</button></div>`;
  document.getElementById("stopButton").addEventListener("click", stopSession);
  document.getElementById("continueButton").addEventListener("click", () => {
    renderComprehensionCheck(trial.condition, renderSemanticTrial);
  });
}

function renderSemanticTrial() {
  const trial = currentTrial();
  state.ratingStartedAt = performance.now();
  emit("TRIAL_READY");
  emit("RATING_START");
  renderRatingForm(primaryItems(trial.condition), `trial${state.trialIndex}`, trial.concept_zh, (values) => {
    const row = emptyRating(trial);
    Object.assign(row, values);
    row.response_time_ms = Math.round(performance.now() - state.ratingStartedAt);
    state.ratings.push(row);
    emit("RATING_END");
    advanceSemantic();
  }, instructionFor(trial.condition));
}

function advanceSemantic() {
  const previous = currentTrial();
  state.trialIndex += 1;
  const next = currentTrial();
  if (!next) return renderAttentionCheck();
  if (next.block_order !== previous.block_order) {
    renderTimer("区块间休息", duration("semantic_block_break"), null, null, renderBlockIntro);
  } else {
    renderSemanticTrial();
  }
}

function duration(key) {
  return state.testMode ? 200 : Number(state.config.timing_ms[key]);
}

function renderTimer(title, milliseconds, startEvent, endEvent, onDone) {
  if (startEvent) emit(startEvent);
  const trial = currentTrial();
  const started = performance.now();
  taskView.innerHTML = `${taskHeader(trial)}<div class="timer"><h1>${title}</h1><div id="timerValue" class="timer-value"></div><p>请保持安静并注视屏幕。</p><button class="danger" id="stopButton">停止实验</button></div>`;
  document.getElementById("stopButton").addEventListener("click", stopSession);
  const value = document.getElementById("timerValue");
  const tick = () => {
    const remaining = Math.max(0, milliseconds - (performance.now() - started));
    value.textContent = Math.ceil(remaining / 1000);
    if (remaining <= 0) {
      clearInterval(interval);
      if (endEvent) emit(endEvent);
      onDone();
    }
  };
  const interval = setInterval(tick, 100);
  tick();
}

function startInducedTrial() {
  emit("TRIAL_READY");
  renderTimer("静息基线", duration("baseline"), "BASELINE_START", "BASELINE_END", renderVideo);
}

function renderVideo() {
  const trial = currentTrial();
  const path = state.config.media_path_template.replace("{stimulus_id}", trial.stimulus_id);
  if (state.simulateMedia) {
    taskView.innerHTML = `${taskHeader(trial)}<h2>测试视频阶段</h2><div class="video-wrap"><span style="color:#fff">${trial.stimulus_id}</span></div><div class="actions"><button class="danger" id="stopButton">停止实验</button><button class="primary" id="simulateButton">模拟视频结束</button></div>`;
    document.getElementById("stopButton").addEventListener("click", stopSession);
    document.getElementById("simulateButton").addEventListener("click", () => {
      emit("STIMULUS_START", { media_path: path, simulated_media: 1 });
      emit("STIMULUS_END", { media_path: path, simulated_media: 1 });
      renderInducedPrimary();
    });
    return;
  }
  taskView.innerHTML = `${taskHeader(trial)}<h2>视频</h2><div class="video-wrap"><video id="stimulusVideo" preload="auto" playsinline></video></div><p id="videoError" class="error"></p><div class="actions"><button class="danger" id="stopButton">停止实验</button><button id="failureButton" class="hidden">记录技术失败并跳过</button></div>`;
  document.getElementById("stopButton").addEventListener("click", stopSession);
  const video = document.getElementById("stimulusVideo");
  let started = false;
  video.src = path;
  video.addEventListener("playing", () => {
    if (!started) {
      started = true;
      emit("STIMULUS_START", { media_path: path });
    }
  });
  video.addEventListener("ended", () => {
    emit("STIMULUS_END", { media_path: path });
    renderInducedPrimary();
  });
  video.addEventListener("error", () => {
    document.getElementById("videoError").textContent = `无法播放 ${trial.stimulus_id}。`;
    const button = document.getElementById("failureButton");
    button.classList.remove("hidden");
    button.addEventListener("click", () => {
      emit("TRIAL_TECHNICAL_FAILURE", { media_path: path, reason: "media_load_error" });
      advanceInduced(false);
    }, { once: true });
  });
  video.play().catch(() => {
    document.getElementById("videoError").textContent = "浏览器阻止了自动播放，请点击视频开始。";
    video.controls = true;
  });
}

function renderInducedPrimary() {
  const trial = currentTrial();
  state.ratingStartedAt = performance.now();
  emit("RATING_START");
  renderRatingForm(primaryItems("induced"), `trial${state.trialIndex}_vad`, "刚才的实际感受", (values) => {
    state.inducedPartial = { ...values, vad_time: performance.now() - state.ratingStartedAt };
    renderInducedSecondary();
  }, instructionFor("induced"));
}

function renderInducedSecondary() {
  const trial = currentTrial();
  renderRatingForm(secondaryItems(), `trial${state.trialIndex}_secondary`, "情绪强度与视频评价", (values) => {
    const row = emptyRating(trial);
    Object.assign(row, state.inducedPartial, values);
    delete row.vad_time;
    row.response_time_ms = Math.round(performance.now() - state.ratingStartedAt);
    state.ratings.push(row);
    state.inducedPartial = null;
    emit("RATING_END");
    renderTimer("恢复", duration("recovery"), "RECOVERY_START", "RECOVERY_END", () => advanceInduced(true));
  }, "请继续根据刚才观看视频时你自己的实际感受作答。");
}

function advanceInduced(completed) {
  const previous = currentTrial();
  if (!completed) {
    const row = emptyRating(previous);
    row.notes = `${row.notes ? `${row.notes};` : ""}TRIAL_TECHNICAL_FAILURE`;
    state.ratings.push(row);
  }
  state.trialIndex += 1;
  if (!currentTrial()) return renderAttentionCheck();
  if (Number(previous.break_after) === 1) {
    renderTimer("中途休息", duration("mid_break"), "PAUSE", null, startInducedTrial);
  } else {
    startInducedTrial();
  }
}

function renderAttentionCheck() {
  const options = `<option value="">请选择</option>${Array.from({ length: 9 }, (_, index) => `<option value="${index + 1}">${index + 1}</option>`).join("")}`;
  taskView.innerHTML = `<div class="completion"><h1>场次核对</h1><form id="attentionForm" class="setup-form"><label>请在本题选择数字 3。<select id="attentionValue1" required>${options}</select></label><label>请在本题选择数字 7。<select id="attentionValue2" required>${options}</select></label><button class="primary" type="submit">完成场次</button></form></div>`;
  document.getElementById("attentionForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const correct = (Number(document.getElementById("attentionValue1").value) === 3 ? 1 : 0)
      + (Number(document.getElementById("attentionValue2").value) === 7 ? 1 : 0);
    const rate = correct / 2;
    const pass = rate >= 0.5 ? 1 : 0;
    state.ratings.forEach((row) => {
      row.attention_check = pass;
      row.attention_check_rate = rate;
    });
    emit("SESSION_END", { attention_check: pass, attention_check_rate: rate });
    await Promise.allSettled(state.markerPromises);
    renderCompletion(pass);
  });
}

async function stopSession() {
  emit("PARTICIPANT_STOP", { reason: "participant_or_researcher_stop" });
  await Promise.allSettled(state.markerPromises);
  renderCompletion("");
}

function csvEscape(value) {
  const text = value == null ? "" : String(value);
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function downloadCsv(filename, rows) {
  if (!rows.length) return;
  const headers = [...new Set(rows.flatMap((row) => Object.keys(row)))];
  const csv = [headers.join(","), ...rows.map((row) => headers.map((key) => csvEscape(row[key])).join(","))].join("\n");
  const blob = new Blob([`\ufeff${csv}`], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
}

function renderCompletion(attentionPass) {
  const suffix = `${state.participantId}_${state.sessionId}`;
  taskView.innerHTML = `<div class="completion"><h1>场次已结束</h1><p>评分记录：${state.ratings.length} 条　事件记录：${state.events.length} 条</p>${attentionPass === 0 ? '<p class="error">指令核对未通过，数据已保留并标记。</p>' : ""}<div class="download-grid"><button class="primary" id="ratingsDownload">导出评分 CSV</button><button id="eventsDownload">导出事件 CSV</button></div></div>`;
  document.getElementById("ratingsDownload").addEventListener("click", () => downloadCsv(`ratings_${suffix}.csv`, state.ratings));
  document.getElementById("eventsDownload").addEventListener("click", () => downloadCsv(`events_${suffix}.csv`, state.events));
}

async function initialize() {
  try {
    const response = await fetch("config.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.config = await response.json();
    document.getElementById("version").textContent = `v${state.config.version}`;
    if (state.testMode) document.getElementById("modeBadge").classList.remove("hidden");
    setMarkerStatus();
  } catch (error) {
    setupError.textContent = `配置加载失败：${String(error)}`;
    document.querySelector("#setupForm button").disabled = true;
  }
}

document.getElementById("setupForm").addEventListener("submit", (event) => {
  event.preventDefault();
  if (!state.config) return;
  const participantId = document.getElementById("participantId").value.trim().toUpperCase();
  const sessionId = document.getElementById("sessionId").value;
  const trials = state.config.schedule
    .filter((row) => row.participant_id === participantId && row.session_id === sessionId)
    .sort((a, b) => Number(a.block_order) - Number(b.block_order) || Number(a.item_order) - Number(b.item_order));
  if (!trials.length) {
    setupError.textContent = "未找到该参与者与场次的随机表。";
    return;
  }
  const sessionTypes = new Set(trials.map((row) => row.session_type));
  if (sessionTypes.size !== 1) {
    setupError.textContent = "随机表中的场次类型不一致。";
    return;
  }
  state.participantId = participantId;
  state.sessionId = sessionId;
  state.sessionType = trials[0].session_type;
  state.trials = trials;
  setupView.classList.add("hidden");
  taskView.classList.remove("hidden");
  emit("SESSION_START");
  renderSessionIntro();
});

initialize();

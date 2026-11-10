/**
 * VoiceGuard popup — Phase 5: tab audio capture + backend /analyze
 */

const statusValue = document.getElementById("statusValue");
const statusHint = document.getElementById("statusHint");
const statusDot = document.getElementById("statusDot");
const resultValue = document.getElementById("resultValue");
const confidenceValue = document.getElementById("confidenceValue");
const captureStatus = document.getElementById("captureStatus");
const levelMeterFill = document.getElementById("levelMeterFill");
const levelValue = document.getElementById("levelValue");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");

function setBusy(isBusy) {
  startBtn.disabled = isBusy;
  stopBtn.disabled = isBusy || stopBtn.dataset.enabled !== "true";
}

function resetLevelMeter() {
  levelMeterFill.style.width = "0%";
  levelValue.textContent = "Level: --";
  captureStatus.textContent = "Not capturing";
  captureStatus.classList.remove("active");
}

function resetAnalysisDisplay() {
  resultValue.textContent = "Waiting for audio...";
  resultValue.classList.remove("verdict-human", "verdict-ai");
  confidenceValue.textContent = "--";
}

function updateLevelMeter(level, streamActive, trackState) {
  const clamped = Math.max(0, Math.min(1, Number(level) || 0));
  const percent = Math.round(clamped * 100);

  levelMeterFill.style.width = `${percent}%`;
  levelValue.textContent = `Level: ${percent}% (${trackState ?? "unknown"})`;

  if (streamActive) {
    captureStatus.textContent = "Tab audio stream active";
    captureStatus.classList.add("active");
  }
}

function showErrorState(title, detail) {
  statusValue.textContent = title;
  statusHint.textContent = detail;
  statusDot.classList.remove("pending");
  stopBtn.disabled = true;
  stopBtn.dataset.enabled = "false";
  resetLevelMeter();
}

function applyAnalysisStatus(message) {
  switch (message.phase) {
    case "CAPTURING_AUDIO":
      statusValue.textContent = "Capturing audio...";
      statusHint.textContent = message.message || "Recording tab audio segment...";
      statusDot.classList.add("pending");
      break;
    case "ANALYZING":
      statusValue.textContent = "Analyzing...";
      statusHint.textContent = message.message || "Sending audio to VoiceGuard backend...";
      statusDot.classList.add("pending");
      break;
    case "ANALYSIS_COMPLETE":
      statusValue.textContent = "Analysis complete";
      statusHint.textContent = message.message || "Backend returned a verdict.";
      statusDot.classList.remove("pending");
      break;
    default:
      break;
  }
}

function applyAnalysisResult(analysis) {
  const verdict = analysis.verdict ?? "Unknown";
  resultValue.textContent = verdict;
  resultValue.classList.remove("verdict-human", "verdict-ai");

  if (verdict === "HUMAN VOICE") {
    resultValue.classList.add("verdict-human");
  } else if (verdict === "AI GENERATED") {
    resultValue.classList.add("verdict-ai");
  }

  confidenceValue.textContent =
    typeof analysis.confidence === "number" ? `${analysis.confidence}%` : "--";
}

function applyCaptureActiveResponse(response) {
  statusDot.classList.add("pending");
  captureStatus.textContent = "Tab audio stream active";
  captureStatus.classList.add("active");
  stopBtn.dataset.enabled = "true";
  stopBtn.disabled = false;

  if (response.analysis) {
    applyAnalysisResult(response.analysis);
    statusValue.textContent = "Analysis complete";
    statusHint.textContent =
      response.message ||
      `Segment analyzed (${response.segment?.durationSec?.toFixed(1) ?? "?"}s).`;
    statusDot.classList.remove("pending");
  }
}

function applyCaptureStoppedResponse(response) {
  statusValue.textContent = "Ready";
  statusHint.textContent = response.message || "Tab audio capture stopped.";
  statusDot.classList.remove("pending");
  stopBtn.dataset.enabled = "false";
  stopBtn.disabled = true;
  resetLevelMeter();
}

async function syncCaptureStatusFromBackground() {
  try {
    const response = await chrome.runtime.sendMessage({
      type: "GET_CAPTURE_STATUS",
    });

    if (response?.ok && response.capturing) {
      applyCaptureActiveResponse({
        message: `Capture active on tab ${response.tabId ?? "?"}.`,
      });
      if (response.trackState) {
        captureStatus.textContent = `Stream: ${response.trackState} (${response.audioTracks ?? 0} track(s))`;
        captureStatus.classList.add("active");
      }
    }
  } catch {
    // Background may be unavailable during reload.
  }
}

async function handleStartClick() {
  setBusy(true);
  statusValue.textContent = "Starting capture...";
  statusHint.textContent = "Connecting to active tab audio stream...";
  statusDot.classList.remove("pending");
  resetAnalysisDisplay();

  try {
    const response = await chrome.runtime.sendMessage({
      type: "START_DETECTION",
    });

    if (!response?.ok) {
      showErrorState("Analysis failed", response?.error || "Background returned an error");
      if (response?.status === "CAPTURE_ACTIVE") {
        statusHint.textContent = response.message || statusHint.textContent;
        stopBtn.dataset.enabled = "true";
        stopBtn.disabled = false;
        captureStatus.textContent = "Tab audio stream active";
        captureStatus.classList.add("active");
      }
      return;
    }

    applyCaptureActiveResponse(response);
  } catch (error) {
    console.error("[VoiceGuard popup] START_DETECTION failed:", error);
    showErrorState("Analysis failed", error instanceof Error ? error.message : String(error));
  } finally {
    startBtn.disabled = false;
  }
}

async function handleStopClick() {
  setBusy(true);
  statusValue.textContent = "Stopping capture...";
  statusHint.textContent = "Stopping tab audio and releasing resources...";

  try {
    const response = await chrome.runtime.sendMessage({
      type: "STOP_DETECTION",
    });

    if (!response?.ok) {
      throw new Error(response?.error || "Background returned an error");
    }

    applyCaptureStoppedResponse(response);
  } catch (error) {
    console.error("[VoiceGuard popup] STOP_DETECTION failed:", error);
    showErrorState("Stop failed", error instanceof Error ? error.message : String(error));
  } finally {
    startBtn.disabled = false;
  }
}

chrome.runtime.onMessage.addListener((message) => {
  if (!message?.type) {
    return;
  }

  if (message.type === "CAPTURE_LEVEL") {
    updateLevelMeter(message.level, message.streamActive, message.trackState);
    return;
  }

  if (message.type === "ANALYSIS_STATUS") {
    applyAnalysisStatus(message);
    return;
  }

  if (message.type === "ANALYSIS_RESULT") {
    if (message.ok && message.result) {
      applyAnalysisResult(message.result);
    } else if (!message.ok) {
      showErrorState("Analysis failed", message.error || "Backend analysis failed.");
    }
  }
});

startBtn.addEventListener("click", handleStartClick);
stopBtn.addEventListener("click", handleStopClick);

syncCaptureStatusFromBackground();

/**
 * VoiceGuard — MV3 background service worker
 * Phase 5: tab audio capture → WAV segment → POST /analyze
 */

importScripts("config.js", "wav-encoder.js", "api.js");

const EXTENSION_VERSION = chrome.runtime.getManifest().version;

let captureState = {
  active: false,
  tabId: null,
};

chrome.runtime.onInstalled.addListener((details) => {
  console.log(`[VoiceGuard] Extension installed/updated (${details.reason}) v${EXTENSION_VERSION}`);
});

function formatChromeError(error) {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === "string") {
    return error;
  }
  return "Unknown error";
}

function getRuntimeErrorMessage() {
  const { lastError } = chrome.runtime;
  return lastError?.message ?? "Unknown runtime error";
}

function broadcastToPopup(message) {
  chrome.runtime.sendMessage(message).catch(() => {});
}

async function getActiveTabId() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  const tab = tabs[0];

  if (!tab?.id) {
    throw new Error("No active tab found. Focus a browser tab and try again.");
  }

  const url = tab.url ?? "";
  if (
    url.startsWith("chrome://") ||
    url.startsWith("chrome-extension://") ||
    url.startsWith("edge://") ||
    url.startsWith("about:")
  ) {
    throw new Error(
      "This tab cannot be captured. Open a regular website with audio (e.g. YouTube) and try again.",
    );
  }

  return tab.id;
}

async function ensureOffscreenDocument() {
  const existingContexts = await chrome.runtime.getContexts({
    contextTypes: ["OFFSCREEN_DOCUMENT"],
  });

  if (existingContexts.length > 0) {
    return;
  }

  await chrome.offscreen.createDocument({
    url: "offscreen.html",
    reasons: ["USER_MEDIA"],
    justification: "Capture active tab audio for VoiceGuard detection pipeline.",
  });

  console.log("[VoiceGuard] Offscreen document created");
}

async function closeOffscreenDocument() {
  const existingContexts = await chrome.runtime.getContexts({
    contextTypes: ["OFFSCREEN_DOCUMENT"],
  });

  if (existingContexts.length === 0) {
    return;
  }

  await chrome.offscreen.closeDocument();
  console.log("[VoiceGuard] Offscreen document closed");
}

function sendMessageToOffscreen(message) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(message, (response) => {
      if (chrome.runtime.lastError) {
        reject(new Error(getRuntimeErrorMessage()));
        return;
      }
      resolve(response);
    });
  });
}

async function startTabCapture() {
  const tabId = await getActiveTabId();
  console.log("[VoiceGuard] Active tab for capture:", tabId);

  let streamId;
  try {
    streamId = await chrome.tabCapture.getMediaStreamId({ targetTabId: tabId });
  } catch (error) {
    const message = formatChromeError(error);
    if (message.includes("activeTab") || message.includes("invoked")) {
      throw new Error(
        "Tab capture permission was denied. Click the VoiceGuard icon, then Start Detection again.",
      );
    }
    if (message.includes("Chrome pages cannot be captured")) {
      throw new Error(
        "Chrome internal pages cannot be captured. Switch to a normal website with audio.",
      );
    }
    throw new Error(message);
  }

  if (!streamId) {
    throw new Error("Tab capture returned no stream ID.");
  }

  console.log("[VoiceGuard] Stream ID obtained for tab capture");

  await ensureOffscreenDocument();

  const captureResult = await sendMessageToOffscreen({
    type: "START_TAB_CAPTURE",
    target: "offscreen",
    streamId,
  });

  if (!captureResult?.ok) {
    throw new Error(captureResult?.error || "Offscreen document failed to start capture.");
  }

  captureState = { active: true, tabId };
  console.log("[VoiceGuard] Tab audio capture started successfully");

  return { tabId, captureResult };
}

async function recordAndAnalyzeSegment() {
  broadcastToPopup({
    type: "ANALYSIS_STATUS",
    phase: "CAPTURING_AUDIO",
    message: `Recording ${VOICEGUARD_CONFIG.RECORD_DURATION_SEC}s tab audio segment...`,
  });

  const recordResult = await sendMessageToOffscreen({
    type: "RECORD_AUDIO_SEGMENT",
    target: "offscreen",
    durationSec: VOICEGUARD_CONFIG.RECORD_DURATION_SEC,
  });

  if (!recordResult?.ok || !recordResult.wavBase64) {
    throw new Error(recordResult?.error || "Failed to record tab audio segment.");
  }

  broadcastToPopup({
    type: "ANALYSIS_STATUS",
    phase: "ANALYZING",
    message: "Uploading segment to VoiceGuard backend...",
  });

  const wavBuffer = base64ToArrayBuffer(recordResult.wavBase64);
  const analysisResult = await analyzeAudioSegment(wavBuffer, VOICEGUARD_CONFIG.API_URL);

  broadcastToPopup({
    type: "ANALYSIS_STATUS",
    phase: "ANALYSIS_COMPLETE",
    message: "Analysis complete.",
  });

  broadcastToPopup({
    type: "ANALYSIS_RESULT",
    ok: true,
    result: analysisResult,
    segment: {
      byteLength: recordResult.byteLength,
      sampleRate: recordResult.sampleRate,
      durationSec: recordResult.durationSec,
    },
  });

  return { analysisResult, recordResult };
}

async function stopTabCapture() {
  if (!captureState.active) {
    console.log("[VoiceGuard] STOP requested but no capture was active");
    return;
  }

  try {
    await sendMessageToOffscreen({ type: "STOP_TAB_CAPTURE", target: "offscreen" });
  } catch (error) {
    console.warn("[VoiceGuard] Offscreen stop message failed:", formatChromeError(error));
  }

  captureState = { active: false, tabId: null };

  try {
    await closeOffscreenDocument();
  } catch (error) {
    console.warn("[VoiceGuard] Failed to close offscreen document:", formatChromeError(error));
  }

  console.log("[VoiceGuard] Tab audio capture stopped and resources cleaned up");
}

async function handleStartDetection(sendResponse) {
  console.log("[VoiceGuard] START_DETECTION received");

  try {
    const { tabId, captureResult } = await startTabCapture();

    let analysisPayload = null;
    try {
      analysisPayload = await recordAndAnalyzeSegment();
    } catch (analysisError) {
      console.error("[VoiceGuard] Recording/analysis failed:", analysisError);
      broadcastToPopup({
        type: "ANALYSIS_RESULT",
        ok: false,
        error: formatChromeError(analysisError),
      });
      sendResponse({
        ok: false,
        error: formatChromeError(analysisError),
        status: "CAPTURE_ACTIVE",
        message: "Tab capture may still be active. Click Stop Detection to release resources.",
        tabId,
        audioTracks: captureResult.audioTracks,
      });
      return;
    }

    sendResponse({
      ok: true,
      status: "ANALYSIS_COMPLETE",
      message: "Tab audio captured and analyzed by VoiceGuard backend.",
      tabId,
      audioTracks: captureResult.audioTracks,
      trackLabel: captureResult.trackLabel,
      analysis: analysisPayload.analysisResult,
      segment: analysisPayload.recordResult,
    });
  } catch (error) {
    console.error("[VoiceGuard] Failed to start detection:", error);
    sendResponse({
      ok: false,
      error: formatChromeError(error),
    });
  }
}

async function handleStopDetection(sendResponse) {
  console.log("[VoiceGuard] STOP_DETECTION received");

  try {
    await stopTabCapture();
    sendResponse({
      ok: true,
      status: "CAPTURE_STOPPED",
      message: "Tab audio capture stopped. Streams and offscreen resources were cleaned up.",
    });
  } catch (error) {
    console.error("[VoiceGuard] Failed to stop tab capture:", error);
    sendResponse({
      ok: false,
      error: formatChromeError(error),
    });
  }
}

async function handleGetCaptureStatus(sendResponse) {
  if (!captureState.active) {
    sendResponse({ ok: true, capturing: false });
    return;
  }

  try {
    const offscreenState = await sendMessageToOffscreen({
      type: "GET_CAPTURE_STATE",
      target: "offscreen",
    });
    sendResponse({
      ok: true,
      capturing: Boolean(offscreenState?.capturing),
      tabId: captureState.tabId,
      audioTracks: offscreenState?.audioTracks ?? 0,
      trackState: offscreenState?.trackState ?? "none",
    });
  } catch (error) {
    sendResponse({
      ok: true,
      capturing: captureState.active,
      tabId: captureState.tabId,
      warning: formatChromeError(error),
    });
  }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || typeof message.type !== "string") {
    sendResponse({ ok: false, error: "Invalid message" });
    return false;
  }

  if (message.target === "offscreen") {
    return false;
  }

  if (message.type === "CAPTURE_LEVEL") {
    chrome.runtime.sendMessage(message).catch(() => {});
    return false;
  }

  switch (message.type) {
    case "START_DETECTION":
      handleStartDetection(sendResponse);
      return true;

    case "STOP_DETECTION":
      handleStopDetection(sendResponse);
      return true;

    case "GET_CAPTURE_STATUS":
      handleGetCaptureStatus(sendResponse);
      return true;

    default:
      if (sender.id !== chrome.runtime.id) {
        return false;
      }
      console.warn("[VoiceGuard] Unknown message type:", message.type);
      sendResponse({ ok: false, error: `Unknown message type: ${message.type}` });
      return false;
  }
});

console.log(`[VoiceGuard] Service worker started v${EXTENSION_VERSION}`);

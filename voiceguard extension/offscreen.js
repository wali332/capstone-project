/**
 * VoiceGuard — offscreen document for tab audio capture (Phase 4A/5).
 * Holds MediaStream, records PCM segments, encodes WAV for backend upload.
 */

let mediaStream = null;
let audioContext = null;
let analyser = null;
let levelIntervalId = null;
let cancelRecording = null;

function stopLevelMonitoring() {
  if (levelIntervalId !== null) {
    clearInterval(levelIntervalId);
    levelIntervalId = null;
  }
}

function computeRmsLevel(analyserNode) {
  const samples = new Uint8Array(analyserNode.fftSize);
  analyserNode.getByteTimeDomainData(samples);

  let sumSquares = 0;
  for (let i = 0; i < samples.length; i += 1) {
    const normalized = (samples[i] - 128) / 128;
    sumSquares += normalized * normalized;
  }

  return Math.sqrt(sumSquares / samples.length);
}

function startLevelMonitoring() {
  stopLevelMonitoring();

  levelIntervalId = setInterval(() => {
    if (!analyser || !mediaStream?.active) {
      return;
    }

    const level = computeRmsLevel(analyser);
    const trackCount = mediaStream.getAudioTracks().length;
    const trackState = mediaStream.getAudioTracks()[0]?.readyState ?? "none";

    chrome.runtime.sendMessage({
      type: "CAPTURE_LEVEL",
      level,
      streamActive: mediaStream.active,
      audioTracks: trackCount,
      trackState,
    });
  }, 200);
}

async function startTabCapture(streamId) {
  if (mediaStream) {
    await stopTabCapture();
  }

  console.log("[VoiceGuard offscreen] Requesting tab audio stream...");

  mediaStream = await navigator.mediaDevices.getUserMedia({
    audio: {
      mandatory: {
        chromeMediaSource: "tab",
        chromeMediaSourceId: streamId,
      },
    },
    video: false,
  });

  const audioTracks = mediaStream.getAudioTracks();
  if (audioTracks.length === 0) {
    throw new Error("No audio tracks in captured tab stream.");
  }

  console.log(
    "[VoiceGuard offscreen] Tab audio capture started:",
    audioTracks.map((track) => `${track.label} (${track.readyState})`).join(", "),
  );

  audioContext = new AudioContext();
  const source = audioContext.createMediaStreamSource(mediaStream);
  analyser = audioContext.createAnalyser();
  analyser.fftSize = 2048;

  source.connect(analyser);
  source.connect(audioContext.destination);

  startLevelMonitoring();

  return {
    ok: true,
    audioTracks: audioTracks.length,
    trackLabel: audioTracks[0]?.label ?? "unknown",
  };
}

function recordAudioSegment(durationSec) {
  if (!audioContext || !mediaStream?.active) {
    return Promise.reject(new Error("No active tab audio stream to record."));
  }

  return new Promise((resolve, reject) => {
    const sampleRate = audioContext.sampleRate;
    const chunks = [];
    const recordSource = audioContext.createMediaStreamSource(mediaStream);
    const processor = audioContext.createScriptProcessor(4096, 1, 1);

    processor.onaudioprocess = (event) => {
      chunks.push(new Float32Array(event.inputBuffer.getChannelData(0)));
    };

    recordSource.connect(processor);
    processor.connect(audioContext.destination);

    console.log("[VoiceGuard offscreen] Recording started");

    const timeoutId = setTimeout(() => {
      processor.disconnect();
      recordSource.disconnect();
      cancelRecording = null;

      console.log("[VoiceGuard offscreen] Recording stopped");

      const totalSamples = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
      if (totalSamples === 0) {
        reject(new Error("Recorded segment is empty. Ensure the tab is playing audio."));
        return;
      }

      const merged = new Float32Array(totalSamples);
      let offset = 0;
      for (const chunk of chunks) {
        merged.set(chunk, offset);
        offset += chunk.length;
      }

      const wavBuffer = encodeWav(merged, sampleRate);
      const durationRecorded = totalSamples / sampleRate;

      console.log(
        "[VoiceGuard offscreen] Audio segment created:",
        wavBuffer.byteLength,
        "bytes,",
        durationRecorded.toFixed(2),
        "seconds at",
        sampleRate,
        "Hz",
      );

      resolve({
        ok: true,
        wavBase64: arrayBufferToBase64(wavBuffer),
        byteLength: wavBuffer.byteLength,
        sampleRate,
        durationSec: durationRecorded,
      });
    }, durationSec * 1000);

    cancelRecording = () => {
      clearTimeout(timeoutId);
      processor.disconnect();
      recordSource.disconnect();
      cancelRecording = null;
      console.log("[VoiceGuard offscreen] Recording cancelled");
      reject(new Error("Recording cancelled"));
    };
  });
}

async function stopTabCapture() {
  if (cancelRecording) {
    cancelRecording();
  }

  stopLevelMonitoring();

  if (mediaStream) {
    for (const track of mediaStream.getTracks()) {
      track.stop();
    }
    console.log("[VoiceGuard offscreen] MediaStream tracks stopped");
    mediaStream = null;
  }

  if (audioContext) {
    await audioContext.close();
    console.log("[VoiceGuard offscreen] AudioContext closed");
    audioContext = null;
    analyser = null;
  }
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (!message || typeof message.type !== "string") {
    return false;
  }

  if (message.target && message.target !== "offscreen") {
    return false;
  }

  if (message.type === "START_TAB_CAPTURE") {
    (async () => {
      try {
        const result = await startTabCapture(message.streamId);
        sendResponse(result);
      } catch (error) {
        console.error("[VoiceGuard offscreen] START_TAB_CAPTURE failed:", error);
        await stopTabCapture();
        sendResponse({
          ok: false,
          error: error instanceof Error ? error.message : String(error),
        });
      }
    })();
    return true;
  }

  if (message.type === "RECORD_AUDIO_SEGMENT") {
    (async () => {
      try {
        const durationSec = message.durationSec ?? VOICEGUARD_CONFIG.RECORD_DURATION_SEC;
        const result = await recordAudioSegment(durationSec);
        sendResponse(result);
      } catch (error) {
        console.error("[VoiceGuard offscreen] RECORD_AUDIO_SEGMENT failed:", error);
        sendResponse({
          ok: false,
          error: error instanceof Error ? error.message : String(error),
        });
      }
    })();
    return true;
  }

  if (message.type === "STOP_TAB_CAPTURE") {
    (async () => {
      try {
        await stopTabCapture();
        sendResponse({ ok: true });
      } catch (error) {
        console.error("[VoiceGuard offscreen] STOP_TAB_CAPTURE failed:", error);
        sendResponse({
          ok: false,
          error: error instanceof Error ? error.message : String(error),
        });
      }
    })();
    return true;
  }

  if (message.type === "GET_CAPTURE_STATE") {
    sendResponse({
      ok: true,
      capturing: Boolean(mediaStream?.active),
      audioTracks: mediaStream?.getAudioTracks().length ?? 0,
      trackState: mediaStream?.getAudioTracks()[0]?.readyState ?? "none",
    });
    return false;
  }

  return false;
});

console.log("[VoiceGuard offscreen] Document loaded");

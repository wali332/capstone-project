/**
 * VoiceGuard extension API client.
 * POST /analyze with multipart field name "file" (matches FastAPI backend).
 */

async function analyzeAudioSegment(wavArrayBuffer, apiUrl = VOICEGUARD_CONFIG.API_URL) {
  const blob = new Blob([wavArrayBuffer], { type: "audio/wav" });
  const formData = new FormData();
  formData.append("file", blob, "voiceguard-tab-segment.wav");

  console.log("[VoiceGuard] Upload started →", `${apiUrl}/analyze`);

  let response;
  try {
    response = await fetch(`${apiUrl}/analyze`, {
      method: "POST",
      body: formData,
    });
  } catch (error) {
    console.error("[VoiceGuard] Upload failed (network):", error);
    throw new Error(
      `Cannot reach VoiceGuard backend at ${apiUrl}. Start the API server and try again.`,
    );
  }

  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const errorData = await response.json();
      if (errorData?.detail) {
        detail = typeof errorData.detail === "string"
          ? errorData.detail
          : JSON.stringify(errorData.detail);
      }
    } catch {
      // Ignore JSON parse errors for non-JSON responses.
    }

    console.error("[VoiceGuard] Upload failed:", detail);
    throw new Error(detail);
  }

  const result = await response.json();
  console.log("[VoiceGuard] Upload completed:", result.verdict, `(confidence ${result.confidence}%)`);
  return result;
}

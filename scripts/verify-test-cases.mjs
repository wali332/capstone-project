/**
 * Automated checks for VoiceGuard test cases TC-01..TC-05 (validation + API).
 * Run: node scripts/verify-test-cases.mjs
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");

const ALLOWED_EXTENSIONS = [".wav", ".mp3", ".flac"];
const MAX_FILE_SIZE = 100 * 1024 * 1024;

function validateAudioFileMeta({ name, size, type = "" }) {
  const fileName = name.toLowerCase();
  const fileExt = fileName.substring(fileName.lastIndexOf("."));

  if (!ALLOWED_EXTENSIONS.includes(fileExt) && !type) {
    return {
      valid: false,
      error: "Only .wav, .mp3, and .flac files are supported",
    };
  }

  if (size > MAX_FILE_SIZE) {
    return { valid: false, error: "File size exceeds 100MB limit" };
  }

  if (size === 0) {
    return { valid: false, error: "File is empty" };
  }

  return { valid: true };
}

async function postAnalyze(wavPath, apiUrl) {
  const blob = new Blob([fs.readFileSync(wavPath)], { type: "audio/wav" });
  const form = new FormData();
  form.append("file", blob, path.basename(wavPath));
  const res = await fetch(`${apiUrl}/analyze`, { method: "POST", body: form });
  const text = await res.text();
  let json = null;
  try {
    json = JSON.parse(text);
  } catch {
    // ignore
  }
  return { status: res.status, json };
}

async function health(apiUrl) {
  try {
    const res = await fetch(`${apiUrl}/health`);
    return res.ok;
  } catch {
    return false;
  }
}

const sampleWav =
  root +
  "/voiceguard-backend/data/external/mlaad-tiny/fake/en/MeloTTS/jane_eyre_01_f000001.wav";

const apiUrl = process.env.VITE_API_URL || "http://localhost:8000";
const deadApiUrl = "http://127.0.0.1:59999";

console.log("=== TC-02 validation (unsupported) ===");
const tc02 = validateAudioFileMeta({ name: "test.txt", size: 100 });
console.log(tc02.valid ? "FAIL" : "PASS", tc02.error);

console.log("\n=== TC-01 validation (supported ext) ===");
const tc01meta = validateAudioFileMeta({
  name: "sample.wav",
  size: fs.statSync(sampleWav).size,
});
console.log(tc01meta.valid ? "PASS extension/size" : "FAIL", tc01meta);

console.log("\n=== TC-03 / TC-05 backend analyze ===");
if (!(await health(apiUrl))) {
  console.log("NOT VERIFIED — backend not running at", apiUrl);
} else {
  const { status, json } = await postAnalyze(sampleWav, apiUrl);
  const ok =
    status === 200 &&
    json &&
    typeof json.verdict === "string" &&
    typeof json.confidence === "number";
  console.log(ok ? "PASS" : "FAIL", "HTTP", status, "verdict", json?.verdict, "confidence", json?.confidence);
}

function getUploadErrorMessage(error) {
  const msg = error?.message || String(error);
  if (
    msg === "Failed to fetch" ||
    msg.toLowerCase().includes("fetch failed") ||
    msg === "NetworkError when attempting to fetch resource."
  ) {
    return "Backend API is not running";
  }
  return msg;
}

console.log("\n=== TC-04 backend unavailable (fetch) ===");
try {
  const blob = new Blob([fs.readFileSync(sampleWav)], { type: "audio/wav" });
  const form = new FormData();
  form.append("file", blob, "sample.wav");
  await fetch(`${deadApiUrl}/analyze`, { method: "POST", body: form });
  console.log("FAIL — expected network error");
} catch (e) {
  const uiMsg = getUploadErrorMessage(e);
  const pass = uiMsg === "Backend API is not running";
  console.log(pass ? "PASS" : "FAIL", "UI message:", uiMsg, "| raw:", e.message);
}

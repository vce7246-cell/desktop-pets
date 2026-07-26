/**
 * Desktop Pet — Pixel Art Generation Proxy
 * =========================================
 * Deploy to Cloudflare Workers to keep image-generation credentials on the server.
 *
 * Supports Agnes AI image generation API (OpenAI-compatible JSON format).
 *
 * Required secret:
 *   npx wrangler secret put OPENAI_API_KEY
 *   → paste your Agnes AI API key (from platform.agnes-ai.com)
 *
 * Optional vars:
 *   OPENAI_BASE_URL       — default: https://apihub.agnes-ai.com
 *   OPENAI_IMAGE_ENDPOINT — default: /v1/images/generations
 *   OPENAI_IMAGE_MODEL    — default: agnes-image-2.1-flash
 *
 * The desktop app calls POST /generate with multipart form data containing
 * the reference image. The worker converts it to a base64 Data URI and
 * sends a JSON request to the Agnes image generations API, then returns
 * PNG/JPEG/WebP bytes to the desktop app.
 */

// ── Prompt (server-side — never seen by the desktop client) ───────────
const USER_PROMPT =
  "根据参考图片中的宠物生成一个可爱的二维像素风桌宠角色。" +
  "保留宠物的主要毛色、花纹、耳朵形状、脸部特征、身体比例和明显辨识特征。" +
  "完整展示单个宠物，轮廓清晰，复古游戏像素风，适合在桌面悬浮展示。" +
  "背景为纯色，不要文字，不要边框，不要场景，不要额外角色。";

// ── Defaults ─────────────────────────────────────────────────────────
const DEFAULT_BASE_URL = "https://apihub.agnes-ai.com";
const DEFAULT_IMAGE_ENDPOINT = "/v1/images/generations";
const DEFAULT_IMAGE_MODEL = "agnes-image-2.1-flash";
const API_TIMEOUT_MS = 120_000;
const DOWNLOAD_TIMEOUT_MS = 30_000;
const MAX_IMAGE_BYTES = 10 * 1024 * 1024; // 10 MB

// ── CORS headers ─────────────────────────────────────────────────────
const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

// ── Entry point ──────────────────────────────────────────────────────
export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    const url = new URL(request.url);
    if (request.method !== "POST" || url.pathname !== "/generate") {
      return jsonResponse(
        { error: "POST /generate with multipart/form-data (field: image)" },
        404
      );
    }

    if (!env.OPENAI_API_KEY) {
      return jsonResponse({ error: "代理未配置 OPENAI_API_KEY（请设置 Agnes API Key）。" }, 500);
    }

    const config = getUpstreamConfig(env);

    let imageFile;
    try {
      const form = await request.formData();
      const file = form.get("image");
      if (!file || typeof file === "string") {
        return jsonResponse({ error: "缺少图片文件 (field: image)" }, 400);
      }
      if (file.size > MAX_IMAGE_BYTES) {
        return jsonResponse({ error: "图片文件过大（上限 10 MB）" }, 413);
      }
      imageFile = file;
    } catch (e) {
      return jsonResponse({ error: "请求解析失败。" }, 400);
    }

    // ── Build JSON body (image → base64 Data URI) ──
    let upstreamBody;
    try {
      upstreamBody = await buildUpstreamBody(imageFile, config);
    } catch (e) {
      return jsonResponse({ error: "图片编码失败。" }, 400);
    }

    // ── Call Agnes API ──
    let upstreamResp;
    try {
      upstreamResp = await fetch(config.imageUrl, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${env.OPENAI_API_KEY}`,
          "Content-Type": "application/json",
        },
        body: upstreamBody,
        signal: AbortSignal.timeout(API_TIMEOUT_MS),
      });
    } catch (e) {
      if (e.name === "TimeoutError") {
        return jsonResponse({ error: "图片生成超时，请稍后重试。" }, 504);
      }
      return jsonResponse({ error: "上游服务连接失败。" }, 502);
    }

    if (upstreamResp.status === 401 || upstreamResp.status === 403) {
      return jsonResponse({ error: "代理配置错误：API Key 无效或无权限。" }, 500);
    }
    if (upstreamResp.status === 404) {
      return jsonResponse({ error: "上游图片接口不存在，请检查 OPENAI_BASE_URL / OPENAI_IMAGE_ENDPOINT。" }, 502);
    }
    if (upstreamResp.status === 429) {
      return jsonResponse({ error: "API 额度不足或请求过于频繁，请稍后重试。" }, 429);
    }
    if (!upstreamResp.ok) {
      return jsonResponse(
        { error: `上游图片服务返回错误 (HTTP ${upstreamResp.status})` },
        502
      );
    }

    let imageBytes;
    try {
      const contentType = upstreamResp.headers.get("Content-Type") || "";
      if (contentType.includes("image/")) {
        imageBytes = new Uint8Array(await upstreamResp.arrayBuffer());
      } else {
        const body = await upstreamResp.json();
        imageBytes = await extractImageBytes(body);
      }
    } catch (e) {
      return jsonResponse({ error: "接口返回数据格式异常。" }, 502);
    }

    if (!imageBytes || !looksLikeImage(imageBytes)) {
      return jsonResponse({ error: "生成结果不是有效图片。" }, 502);
    }

    return new Response(imageBytes, {
      status: 200,
      headers: {
        ...CORS_HEADERS,
        "Content-Type": guessImageContentType(imageBytes),
        "Cache-Control": "no-cache",
      },
    });
  },
};

// ── Configuration helpers ─────────────────────────────────────────────

function getUpstreamConfig(env) {
  const baseUrl = normalizeBaseUrl(env.OPENAI_BASE_URL || DEFAULT_BASE_URL);
  const endpoint = env.OPENAI_IMAGE_ENDPOINT || DEFAULT_IMAGE_ENDPOINT;
  const imageUrl = endpoint.startsWith("http")
    ? endpoint
    : `${baseUrl}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  return {
    imageUrl,
    model: env.OPENAI_IMAGE_MODEL || DEFAULT_IMAGE_MODEL,
    size: env.OPENAI_IMAGE_SIZE || "1024x1024",
  };
}

function normalizeBaseUrl(url) {
  return String(url || DEFAULT_BASE_URL).replace(/\/+$/, "");
}

// ── Request body builder (Agnes JSON format) ──────────────────────────

async function buildUpstreamBody(imageFile, config) {
  // Read image bytes
  const arrayBuffer = await imageFile.arrayBuffer();
  const bytes = new Uint8Array(arrayBuffer);

  // Detect MIME type from magic bytes
  const mimeType = guessImageContentType(bytes);

  // Convert to base64 Data URI
  const base64 = uint8ArrayToBase64(bytes);
  const dataUri = `data:${mimeType};base64,${base64}`;

  // Build Agnes-compatible JSON body
  return JSON.stringify({
    model: config.model,
    prompt: USER_PROMPT,
    size: config.size,
    image: [dataUri],
    extra_body: {
      response_format: "b64_json",
    },
  });
}

// ── Response parsing helpers ──────────────────────────────────────────

async function extractImageBytes(body) {
  const item = body && body.data && body.data[0];
  if (!item) return null;

  // Agnes b64_json response
  if (item.b64_json) {
    return base64ToUint8Array(item.b64_json);
  }

  // URL response (some providers)
  if (item.url) {
    return await downloadImage(item.url);
  }

  // Data URL embedded in image_url field
  if (item.image_url && typeof item.image_url === "string") {
    if (item.image_url.startsWith("data:")) {
      return base64ToUint8Array(item.image_url.split(",", 2)[1] || "");
    }
    return await downloadImage(item.image_url);
  }

  return null;
}

async function downloadImage(url) {
  const resp = await fetch(url, { signal: AbortSignal.timeout(DOWNLOAD_TIMEOUT_MS) });
  if (!resp.ok) return null;
  return new Uint8Array(await resp.arrayBuffer());
}

function jsonResponse(data, status) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
  });
}

// ── Encoding helpers ──────────────────────────────────────────────────

function uint8ArrayToBase64(bytes) {
  let binary = "";
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

function base64ToUint8Array(b64) {
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

// ── Image validation helpers ──────────────────────────────────────────

function looksLikeImage(data) {
  if (!data || data.length < 8) return false;
  if (data[0] === 0x89 && data[1] === 0x50 && data[2] === 0x4e && data[3] === 0x47) return true; // PNG
  if (data[0] === 0xff && data[1] === 0xd8 && data[2] === 0xff) return true; // JPEG
  if (data[0] === 0x47 && data[1] === 0x49 && data[2] === 0x46) return true; // GIF
  if (
    data[0] === 0x52 && data[1] === 0x49 && data[2] === 0x46 && data[3] === 0x46 &&
    data[8] === 0x57 && data[9] === 0x45 && data[10] === 0x42 && data[11] === 0x50
  ) return true; // WebP
  return false;
}

function guessImageContentType(data) {
  if (data[0] === 0x89 && data[1] === 0x50 && data[2] === 0x4e && data[3] === 0x47) return "image/png";
  if (data[0] === 0xff && data[1] === 0xd8 && data[2] === 0xff) return "image/jpeg";
  if (data[0] === 0x47 && data[1] === 0x49 && data[2] === 0x46) return "image/gif";
  if (data[0] === 0x52 && data[1] === 0x49 && data[2] === 0x46 && data[3] === 0x46) return "image/webp";
  return "application/octet-stream";
}

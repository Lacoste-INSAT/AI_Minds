/**
 * Frontend environment contract for API/WS connectivity.
 * Enforces localhost-only connections to match safety constraints.
 */

const LOCALHOST_HOSTS = new Set(["127.0.0.1", "localhost", "::1"]);
const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

function isLocalhostUrl(value: string): boolean {
  try {
    const parsed = new URL(value);
    return LOCALHOST_HOSTS.has(parsed.hostname);
  } catch {
    return false;
  }
}

function deriveWsBaseUrl(apiBaseUrl: string): string {
  const parsed = new URL(apiBaseUrl);
  parsed.protocol = parsed.protocol === "https:" ? "wss:" : "ws:";
  return parsed.toString().replace(/\/$/, "");
}

function resolveBaseUrl(raw: string | undefined): string {
  const candidate = raw?.trim() || DEFAULT_API_BASE_URL;
  if (!isLocalhostUrl(candidate)) {
    console.warn(
      `[env] Invalid API base URL "${candidate}". Using ${DEFAULT_API_BASE_URL}.`
    );
    return DEFAULT_API_BASE_URL;
  }
  return candidate.replace(/\/$/, "");
}

export const API_BASE_URL = resolveBaseUrl(process.env.NEXT_PUBLIC_API_BASE_URL);

const rawWsBaseUrl = process.env.NEXT_PUBLIC_WS_BASE_URL?.trim();
const safeWsBaseUrl =
  rawWsBaseUrl && isLocalhostUrl(rawWsBaseUrl)
    ? rawWsBaseUrl.replace(/\/$/, "")
    : deriveWsBaseUrl(API_BASE_URL);

export const WS_BASE_URL = safeWsBaseUrl;


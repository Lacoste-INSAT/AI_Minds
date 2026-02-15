/**
 * Frontend environment contract for API/WS connectivity.
 * Enforces localhost-only live mode to match frontend safety constraints.
 */

const LOCALHOST_HOSTS = new Set(["127.0.0.1", "localhost", "::1"]);
const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export type ApiMode = "mock" | "live";

function isLocalhostUrl(value: string): boolean {
  try {
    const parsed = new URL(value);
    return LOCALHOST_HOSTS.has(parsed.hostname);
  } catch {
    return false;
  }
}

function parseApiMode(raw: string | undefined): ApiMode {
  if (raw === "live") {
    return "live";
  }
  return "mock";
}

function deriveWsBaseUrl(apiBaseUrl: string): string {
  const parsed = new URL(apiBaseUrl);
  parsed.protocol = parsed.protocol === "https:" ? "wss:" : "ws:";
  return parsed.toString().replace(/\/$/, "");
}

function resolveLiveBaseUrl(raw: string | undefined): string {
  const candidate = raw?.trim() || DEFAULT_API_BASE_URL;
  if (!isLocalhostUrl(candidate)) {
    console.warn(
      `[env] Invalid live API base URL "${candidate}". Falling back to ${DEFAULT_API_BASE_URL}.`
    );
    return DEFAULT_API_BASE_URL;
  }
  return candidate.replace(/\/$/, "");
}

export const API_MODE: ApiMode = parseApiMode(process.env.NEXT_PUBLIC_API_MODE);
export const API_BASE_URL =
  API_MODE === "live"
    ? resolveLiveBaseUrl(process.env.NEXT_PUBLIC_API_BASE_URL)
    : DEFAULT_API_BASE_URL;

const rawWsBaseUrl = process.env.NEXT_PUBLIC_WS_BASE_URL?.trim();
const safeWsBaseUrl =
  rawWsBaseUrl && isLocalhostUrl(rawWsBaseUrl)
    ? rawWsBaseUrl.replace(/\/$/, "")
    : deriveWsBaseUrl(API_BASE_URL);

export const WS_BASE_URL = safeWsBaseUrl;


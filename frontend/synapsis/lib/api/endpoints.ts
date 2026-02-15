import { API_BASE_URL, WS_BASE_URL } from "@/lib/env";

export const API_ENDPOINTS = {
  root: "/",
  health: "/health",
  queryAsk: "/query/ask",
  queryStreamWs: "/query/stream",
  ingestionStatus: "/ingestion/status",
  ingestionScan: "/ingestion/scan",
  ingestionWs: "/ingestion/ws",
  memoryGraph: "/memory/graph",
  memoryTimeline: "/memory/timeline",
  memoryStats: "/memory/stats",
  memorySearch: "/memory/search",
  memoryDetail: (id: string) => `/memory/${id}`,
  configSources: "/config/sources",
  insightsDigest: "/insights/digest",
  insightsPatterns: "/insights/patterns",
  insightsAll: "/insights/all",
  runtimePolicy: "/runtime/policy",
  runtimeIncidents: "/runtime/incidents",
} as const;

export const WS_ENDPOINTS = {
  queryStream: `${WS_BASE_URL}${API_ENDPOINTS.queryStreamWs}`,
  ingestion: `${WS_BASE_URL}${API_ENDPOINTS.ingestionWs}`,
} as const;

export { API_BASE_URL };

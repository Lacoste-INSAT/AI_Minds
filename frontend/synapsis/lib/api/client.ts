/**
 * Typed API client for Synapsis backend.
 * All responses are runtime-validated via Zod schemas.
 *
 * Source: ARCHITECTURE.md, BACKEND_CONTRACT_ALIGNMENT.md
 * Constraint: localhost-only (127.0.0.1)
 */

import { z } from "zod";
import { API_BASE_URL, API_ENDPOINTS } from "./endpoints";
import {
  HealthResponseSchema,
  IngestionStatusResponseSchema,
  IngestionScanResponseSchema,
  AnswerPacketSchema,
  GraphDataSchema,
  TimelineResponseSchema,
  MemoryDetailSchema,
  MemoryStatsSchema,
  MemorySearchResultSchema,
  SourcesConfigResponseSchema,
  DigestResponseSchema,
  PatternsResponseSchema,
  InsightItemSchema,
  RuntimeIncidentSchema,
  RuntimePolicyResponseSchema,
} from "./schemas";
import type {
  HealthResponse,
  IngestionStatusResponse,
  IngestionScanResponse,
  AnswerPacket,
  QueryRequest,
  GraphData,
  TimelineResponse,
  MemoryDetail,
  MemoryStats,
  MemorySearchResult,
  SourcesConfigResponse,
  SourcesConfigUpdate,
  DigestResponse,
  PatternsResponse,
  InsightItem,
  RuntimeIncident,
  RuntimePolicyResponse,
} from "@/types/contracts";

// ─── Result type for safe error handling ───

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };

// ─── Internal fetch wrapper ───

async function apiFetch<T>(
  path: string,
  schema: z.ZodType<T>,
  options?: RequestInit
): Promise<ApiResult<T>> {
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });

    if (!res.ok) {
      return { ok: false, error: `HTTP ${res.status}: ${res.statusText}` };
    }

    const json = await res.json();
    const parsed = schema.safeParse(json);

    if (!parsed.success) {
      console.error("[api] Schema validation failed:", parsed.error.issues);
      return { ok: false, error: "Response schema validation failed" };
    }

    return { ok: true, data: parsed.data };
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Unknown network error";
    return { ok: false, error: message };
  }
}

type TimelineQueryFilters = {
  modality?: string;
  category?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
};

// ─── Public API methods ───

export const apiClient = {
  async getHealth(): Promise<ApiResult<HealthResponse>> {
    return apiFetch(API_ENDPOINTS.health, HealthResponseSchema);
  },

  async getIngestionStatus(): Promise<ApiResult<IngestionStatusResponse>> {
    return apiFetch(API_ENDPOINTS.ingestionStatus, IngestionStatusResponseSchema);
  },

  async triggerScan(): Promise<ApiResult<IngestionScanResponse>> {
    return apiFetch(API_ENDPOINTS.ingestionScan, IngestionScanResponseSchema, { method: "POST" });
  },

  async ask(request: QueryRequest): Promise<ApiResult<AnswerPacket>> {
    return apiFetch(API_ENDPOINTS.queryAsk, AnswerPacketSchema, {
      method: "POST",
      body: JSON.stringify(request),
    });
  },

  async getGraph(limit?: number): Promise<ApiResult<GraphData>> {
    const params = limit ? `?limit=${limit}` : "";
    return apiFetch(`${API_ENDPOINTS.memoryGraph}${params}`, GraphDataSchema);
  },

  async getTimeline(
    page = 1,
    pageSize = 20,
    filters?: TimelineQueryFilters
  ): Promise<ApiResult<TimelineResponse>> {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });
    if (filters?.modality && filters.modality !== "all") params.set("modality", filters.modality);
    if (filters?.category && filters.category !== "all") params.set("category", filters.category);
    if (filters?.search) params.set("search", filters.search);
    if (filters?.date_from) params.set("date_from", filters.date_from);
    if (filters?.date_to) params.set("date_to", filters.date_to);

    return apiFetch(`${API_ENDPOINTS.memoryTimeline}?${params}`, TimelineResponseSchema);
  },

  async getMemoryDetail(id: string): Promise<ApiResult<MemoryDetail>> {
    return apiFetch(API_ENDPOINTS.memoryDetail(id), MemoryDetailSchema);
  },

  async getMemoryStats(): Promise<ApiResult<MemoryStats>> {
    return apiFetch(API_ENDPOINTS.memoryStats, MemoryStatsSchema);
  },

  async searchMemory(
    query: string,
    filters?: { modality?: string; category?: string; limit?: number }
  ): Promise<ApiResult<MemorySearchResult[]>> {
    const params = new URLSearchParams({ q: query });
    if (filters?.modality && filters.modality !== "all") params.set("modality", filters.modality);
    if (filters?.category && filters.category !== "all") params.set("category", filters.category);
    if (filters?.limit) params.set("limit", String(filters.limit));
    return apiFetch(`${API_ENDPOINTS.memorySearch}?${params}`, z.array(MemorySearchResultSchema));
  },

  async getSourcesConfig(): Promise<ApiResult<SourcesConfigResponse>> {
    return apiFetch(API_ENDPOINTS.configSources, SourcesConfigResponseSchema);
  },

  async updateSourcesConfig(config: SourcesConfigUpdate): Promise<ApiResult<SourcesConfigResponse>> {
    return apiFetch(API_ENDPOINTS.configSources, SourcesConfigResponseSchema, {
      method: "PUT",
      body: JSON.stringify(config),
    });
  },

  async getDigest(): Promise<ApiResult<DigestResponse>> {
    return apiFetch(API_ENDPOINTS.insightsDigest, DigestResponseSchema);
  },

  async getPatterns(): Promise<ApiResult<PatternsResponse>> {
    return apiFetch(API_ENDPOINTS.insightsPatterns, PatternsResponseSchema);
  },

  async getAllInsights(): Promise<ApiResult<InsightItem[]>> {
    return apiFetch(API_ENDPOINTS.insightsAll, z.array(InsightItemSchema));
  },

  async getRuntimePolicy(): Promise<ApiResult<RuntimePolicyResponse>> {
    return apiFetch(API_ENDPOINTS.runtimePolicy, RuntimePolicyResponseSchema);
  },

  async getRuntimeIncidents(limit = 50): Promise<ApiResult<RuntimeIncident[]>> {
    return apiFetch(
      `${API_ENDPOINTS.runtimeIncidents}?limit=${limit}`,
      z.array(RuntimeIncidentSchema)
    );
  },
} as const;

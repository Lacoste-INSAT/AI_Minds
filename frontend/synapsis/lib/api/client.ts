/**
 * Typed API client for Synapsis backend.
 * All responses are runtime-validated via Zod schemas.
 * Falls back gracefully when backend is unavailable.
 *
 * Source: ARCHITECTURE.md, BACKEND_CONTRACT_ALIGNMENT.md
 * Constraint: localhost-only (127.0.0.1)
 */

import { z } from "zod";
import { API_BASE_URL, API_ENDPOINTS } from "./endpoints";
import { API_MODE } from "@/lib/env";
import {
  HealthResponseSchema,
  IngestionStatusResponseSchema,
  IngestionScanResponseSchema,
  AnswerPacketSchema,
  GraphDataSchema,
  TimelineResponseSchema,
  MemoryDetailSchema,
  MemoryStatsSchema,
  SourcesConfigResponseSchema,
  DigestResponseSchema,
  PatternsResponseSchema,
  InsightItemSchema,
} from "./schemas";
import { mockHandlers } from "@/mocks/handlers";
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
  SourcesConfigResponse,
  SourcesConfigUpdate,
  DigestResponse,
  PatternsResponse,
  InsightItem,
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

async function fromMock<T>(handler: () => Promise<T>): Promise<ApiResult<T>> {
  try {
    const data = await handler();
    return { ok: true, data };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : "Mock handler error",
    };
  }
}

// ─── Public API methods ───

export const apiClient = {
  // Health
  async getHealth(): Promise<ApiResult<HealthResponse>> {
    if (API_MODE === "mock") {
      return fromMock(() => mockHandlers.getHealth());
    }
    return apiFetch(API_ENDPOINTS.health, HealthResponseSchema);
  },

  // Ingestion
  async getIngestionStatus(): Promise<ApiResult<IngestionStatusResponse>> {
    if (API_MODE === "mock") {
      return fromMock(() => mockHandlers.getIngestionStatus());
    }
    return apiFetch(
      API_ENDPOINTS.ingestionStatus,
      IngestionStatusResponseSchema
    );
  },

  async triggerScan(): Promise<ApiResult<IngestionScanResponse>> {
    if (API_MODE === "mock") {
      return fromMock(() => mockHandlers.triggerScan());
    }
    return apiFetch(API_ENDPOINTS.ingestionScan, IngestionScanResponseSchema, {
      method: "POST",
    });
  },

  // Query
  async ask(request: QueryRequest): Promise<ApiResult<AnswerPacket>> {
    if (API_MODE === "mock") {
      return fromMock(() => mockHandlers.ask(request));
    }
    return apiFetch(API_ENDPOINTS.queryAsk, AnswerPacketSchema, {
      method: "POST",
      body: JSON.stringify(request),
    });
  },

  // Memory / Graph
  async getGraph(limit?: number): Promise<ApiResult<GraphData>> {
    if (API_MODE === "mock") {
      return fromMock(() => mockHandlers.getGraph(limit));
    }
    const params = limit ? `?limit=${limit}` : "";
    return apiFetch(`${API_ENDPOINTS.memoryGraph}${params}`, GraphDataSchema);
  },

  async getTimeline(
    page = 1,
    pageSize = 20,
    filters?: TimelineQueryFilters
  ): Promise<ApiResult<TimelineResponse>> {
    if (API_MODE === "mock") {
      return fromMock(() => mockHandlers.getTimeline(page, pageSize, filters));
    }
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });
    if (filters?.modality && filters.modality !== "all")
      params.set("modality", filters.modality);
    if (filters?.category && filters.category !== "all")
      params.set("category", filters.category);
    if (filters?.search) params.set("search", filters.search);
    if (filters?.date_from) params.set("date_from", filters.date_from);
    if (filters?.date_to) params.set("date_to", filters.date_to);

    return apiFetch(
      `${API_ENDPOINTS.memoryTimeline}?${params}`,
      TimelineResponseSchema
    );
  },

  async getMemoryDetail(id: string): Promise<ApiResult<MemoryDetail>> {
    if (API_MODE === "mock") {
      return fromMock(() => mockHandlers.getMemoryDetail(id));
    }
    return apiFetch(API_ENDPOINTS.memoryDetail(id), MemoryDetailSchema);
  },

  async getMemoryStats(): Promise<ApiResult<MemoryStats>> {
    if (API_MODE === "mock") {
      return fromMock(() => mockHandlers.getMemoryStats());
    }
    return apiFetch(API_ENDPOINTS.memoryStats, MemoryStatsSchema);
  },

  // Config
  async getSourcesConfig(): Promise<ApiResult<SourcesConfigResponse>> {
    if (API_MODE === "mock") {
      return fromMock(() => mockHandlers.getSourcesConfig());
    }
    return apiFetch(API_ENDPOINTS.configSources, SourcesConfigResponseSchema);
  },

  async updateSourcesConfig(
    config: SourcesConfigUpdate
  ): Promise<ApiResult<SourcesConfigResponse>> {
    if (API_MODE === "mock") {
      return fromMock(() => mockHandlers.updateSourcesConfig(config));
    }
    return apiFetch(API_ENDPOINTS.configSources, SourcesConfigResponseSchema, {
      method: "PUT",
      body: JSON.stringify(config),
    });
  },

  // Insights
  async getDigest(): Promise<ApiResult<DigestResponse>> {
    if (API_MODE === "mock") {
      return fromMock(() => mockHandlers.getDigest());
    }
    return apiFetch(API_ENDPOINTS.insightsDigest, DigestResponseSchema);
  },

  async getPatterns(): Promise<ApiResult<PatternsResponse>> {
    if (API_MODE === "mock") {
      return fromMock(() => mockHandlers.getPatterns());
    }
    return apiFetch(API_ENDPOINTS.insightsPatterns, PatternsResponseSchema);
  },

  async getAllInsights(): Promise<ApiResult<InsightItem[]>> {
    if (API_MODE === "mock") {
      return fromMock(() => mockHandlers.getAllInsights());
    }
    return apiFetch(
      API_ENDPOINTS.insightsAll,
      z.array(InsightItemSchema)
    );
  },
} as const;

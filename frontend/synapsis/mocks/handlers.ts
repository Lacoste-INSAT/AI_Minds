/**
 * Deterministic in-memory mock handlers used by API/WS clients in mock mode.
 */

import type {
  AnswerPacket,
  DigestResponse,
  GraphData,
  IngestionScanResponse,
  IngestionStatusResponse,
  InsightItem,
  MemoryDetail,
  MemoryStats,
  PatternsResponse,
  QueryRequest,
  SourcesConfigResponse,
  SourcesConfigUpdate,
  TimelineItem,
  TimelineResponse,
  HealthResponse,
} from "@/types/contracts";
import {
  MOCK_ANSWER_ABSTENTION,
  MOCK_ANSWER_HIGH,
  MOCK_ANSWER_MEDIUM,
  MOCK_DIGEST,
  MOCK_GRAPH,
  MOCK_HEALTH_HEALTHY,
  MOCK_INGESTION_STATUS,
  MOCK_INSIGHTS,
  MOCK_MEMORY_DETAIL,
  MOCK_PATTERNS,
  MOCK_SOURCES_CONFIG,
  MOCK_STATS,
  MOCK_TIMELINE_ITEMS,
} from "./fixtures";

const STORAGE_KEY_WATCHED_DIRECTORIES = "synapsis.mock.watchedDirectories";

type TimelineFilters = {
  modality?: string;
  category?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
};

let mockWatchedDirectoriesMemory: string[] = [];

function getStoredWatchedDirectories(): string[] {
  if (typeof window === "undefined") {
    return mockWatchedDirectoriesMemory;
  }
  const raw = window.localStorage.getItem(STORAGE_KEY_WATCHED_DIRECTORIES);
  if (!raw) {
    return [];
  }
  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed.filter((entry): entry is string => typeof entry === "string");
  } catch {
    return [];
  }
}

function setStoredWatchedDirectories(next: string[]): void {
  mockWatchedDirectoriesMemory = [...next];
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY_WATCHED_DIRECTORIES, JSON.stringify(next));
}

function pickAnswerFixture(question: string): AnswerPacket {
  const lower = question.toLowerCase();
  if (lower.includes("uncertain") || lower.includes("maybe")) {
    return MOCK_ANSWER_MEDIUM;
  }
  if (lower.includes("unknown") || lower.includes("don't know")) {
    return MOCK_ANSWER_ABSTENTION;
  }
  return MOCK_ANSWER_HIGH;
}

function filterTimelineItems(items: TimelineItem[], filters?: TimelineFilters): TimelineItem[] {
  if (!filters) {
    return items;
  }
  const search = filters.search?.trim().toLowerCase();
  const dateFrom = filters.date_from ? new Date(filters.date_from) : null;
  const dateTo = filters.date_to ? new Date(filters.date_to) : null;

  return items.filter((item) => {
    if (filters.modality && item.modality !== filters.modality) {
      return false;
    }
    if (filters.category && item.category !== filters.category) {
      return false;
    }
    if (search) {
      const match =
        item.title.toLowerCase().includes(search) ||

        (item.summary ?? "").toLowerCase().includes(search) ||

        item.entities.some((entity) => entity.toLowerCase().includes(search));
      if (!match) {
        return false;
      }
    }
    const itemDate = new Date(item.ingested_at);
    if (dateFrom && itemDate < dateFrom) {
      return false;
    }
    if (dateTo && itemDate > dateTo) {
      return false;
    }
    return true;
  });
}

function toSourcesConfig(paths: string[]): SourcesConfigResponse {
  return {
    ...MOCK_SOURCES_CONFIG,
    watched_directories: paths.map((path, index) => ({
      id: `mock-dir-${index + 1}`,
      path,
      enabled: true,
      exclude_patterns: MOCK_SOURCES_CONFIG.exclude_patterns,
    })),
  };
}

export const mockHandlers = {
  async getHealth(): Promise<HealthResponse> {
    return MOCK_HEALTH_HEALTHY;
  },

  async getIngestionStatus(): Promise<IngestionStatusResponse> {
    return {
      ...MOCK_INGESTION_STATUS,
      watched_directories: getStoredWatchedDirectories(),
    };
  },

  async triggerScan(): Promise<IngestionScanResponse> {
    return {
      message: "Mock scan completed",
      files_processed: MOCK_INGESTION_STATUS.files_processed,
      errors: MOCK_INGESTION_STATUS.files_failed,
    };
  },

  async ask(request: QueryRequest): Promise<AnswerPacket> {
    return pickAnswerFixture(request.question);
  },

  async getGraph(limit?: number): Promise<GraphData> {
    if (!limit) {
      return MOCK_GRAPH;
    }
    const nodes = MOCK_GRAPH.nodes.slice(0, limit);
    const nodeIds = new Set(nodes.map((node) => node.id));
    const edges = MOCK_GRAPH.edges.filter(
      (edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target)
    );
    return { nodes, edges };
  },

  async getTimeline(
    page = 1,
    pageSize = 20,
    filters?: TimelineFilters
  ): Promise<TimelineResponse> {
    const filtered = filterTimelineItems(MOCK_TIMELINE_ITEMS, filters);
    const start = (page - 1) * pageSize;
    const items = filtered.slice(start, start + pageSize);
    return {
      items,
      total: filtered.length,
      page,
      page_size: pageSize,
    };
  },

  async getMemoryDetail(id: string): Promise<MemoryDetail> {
    return { ...MOCK_MEMORY_DETAIL, id };
  },

  async getMemoryStats(): Promise<MemoryStats> {
    return MOCK_STATS;
  },

  async getSourcesConfig(): Promise<SourcesConfigResponse> {
    return toSourcesConfig(getStoredWatchedDirectories());
  },

  async updateSourcesConfig(config: SourcesConfigUpdate): Promise<SourcesConfigResponse> {
    setStoredWatchedDirectories(config.watched_directories);
    return toSourcesConfig(config.watched_directories);
  },

  async getDigest(): Promise<DigestResponse> {
    return MOCK_DIGEST;
  },

  async getPatterns(): Promise<PatternsResponse> {
    return MOCK_PATTERNS;
  },

  async getAllInsights(): Promise<InsightItem[]> {
    return MOCK_INSIGHTS;
  },
};


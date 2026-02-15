/**
 * Contract Tests — Backend Schema Conformance Suite
 *
 * Validates that all mock fixtures conform to their Zod schemas,
 * and tests negative cases for malformed payloads.
 *
 * Source: FE-057 specification
 */

import { describe, it, expect } from "vitest";
import {
  AnswerPacketSchema,
  GraphDataSchema,
  TimelineResponseSchema,
  MemoryDetailSchema,
  MemoryStatsSchema,
  HealthResponseSchema,
  IngestionStatusResponseSchema,
  SourcesConfigResponseSchema,
  DigestResponseSchema,
  PatternsResponseSchema,
  InsightItemSchema,
  ChunkEvidenceSchema,
  GraphNodeSchema,
  GraphEdgeSchema,
  TimelineItemSchema,
} from "@/lib/api/schemas";

import {
  MOCK_ANSWER_HIGH,
  MOCK_ANSWER_MEDIUM,
  MOCK_ANSWER_ABSTENTION,
  MOCK_ANSWER_MULTI_SOURCE,
  MOCK_ANSWER_PARTIAL,
  MOCK_GRAPH,
  MOCK_TIMELINE_RESPONSE,
  MOCK_TIMELINE_ITEMS,
  MOCK_MEMORY_DETAIL,
  MOCK_STATS,
  MOCK_HEALTH_HEALTHY,
  MOCK_HEALTH_DEGRADED,
  MOCK_HEALTH_UNHEALTHY,
  MOCK_INGESTION_STATUS,
  MOCK_SOURCES_CONFIG,
  MOCK_DIGEST,
  MOCK_PATTERNS,
  MOCK_INSIGHTS,
  MOCK_EVIDENCE,
} from "@/mocks/fixtures";

// ─── Positive Tests: Fixtures conform to schemas ───

describe("Contract: AnswerPacket", () => {
  it("validates MOCK_ANSWER_HIGH", () => {
    expect(AnswerPacketSchema.safeParse(MOCK_ANSWER_HIGH).success).toBe(true);
  });

  it("validates MOCK_ANSWER_MEDIUM", () => {
    expect(AnswerPacketSchema.safeParse(MOCK_ANSWER_MEDIUM).success).toBe(true);
  });

  it("validates MOCK_ANSWER_ABSTENTION", () => {
    expect(AnswerPacketSchema.safeParse(MOCK_ANSWER_ABSTENTION).success).toBe(true);
  });

  it("validates MOCK_ANSWER_MULTI_SOURCE", () => {
    expect(AnswerPacketSchema.safeParse(MOCK_ANSWER_MULTI_SOURCE).success).toBe(true);
  });

  it("validates MOCK_ANSWER_PARTIAL", () => {
    expect(AnswerPacketSchema.safeParse(MOCK_ANSWER_PARTIAL).success).toBe(true);
  });
});

describe("Contract: ChunkEvidence", () => {
  it("validates all evidence fixtures", () => {
    for (const ev of MOCK_EVIDENCE) {
      expect(ChunkEvidenceSchema.safeParse(ev).success).toBe(true);
    }
  });
});

describe("Contract: GraphData", () => {
  it("validates MOCK_GRAPH", () => {
    expect(GraphDataSchema.safeParse(MOCK_GRAPH).success).toBe(true);
  });

  it("validates each node", () => {
    for (const node of MOCK_GRAPH.nodes) {
      expect(GraphNodeSchema.safeParse(node).success).toBe(true);
    }
  });

  it("validates each edge", () => {
    for (const edge of MOCK_GRAPH.edges) {
      expect(GraphEdgeSchema.safeParse(edge).success).toBe(true);
    }
  });
});

describe("Contract: Timeline", () => {
  it("validates MOCK_TIMELINE_RESPONSE", () => {
    expect(TimelineResponseSchema.safeParse(MOCK_TIMELINE_RESPONSE).success).toBe(true);
  });

  it("validates each timeline item", () => {
    for (const item of MOCK_TIMELINE_ITEMS) {
      expect(TimelineItemSchema.safeParse(item).success).toBe(true);
    }
  });
});

describe("Contract: MemoryDetail", () => {
  it("validates MOCK_MEMORY_DETAIL", () => {
    expect(MemoryDetailSchema.safeParse(MOCK_MEMORY_DETAIL).success).toBe(true);
  });
});

describe("Contract: MemoryStats", () => {
  it("validates MOCK_STATS", () => {
    expect(MemoryStatsSchema.safeParse(MOCK_STATS).success).toBe(true);
  });
});

describe("Contract: HealthResponse", () => {
  it("validates healthy state", () => {
    expect(HealthResponseSchema.safeParse(MOCK_HEALTH_HEALTHY).success).toBe(true);
  });

  it("validates degraded state", () => {
    expect(HealthResponseSchema.safeParse(MOCK_HEALTH_DEGRADED).success).toBe(true);
  });

  it("validates unhealthy state", () => {
    expect(HealthResponseSchema.safeParse(MOCK_HEALTH_UNHEALTHY).success).toBe(true);
  });
});

describe("Contract: IngestionStatus", () => {
  it("validates MOCK_INGESTION_STATUS", () => {
    expect(IngestionStatusResponseSchema.safeParse(MOCK_INGESTION_STATUS).success).toBe(true);
  });
});

describe("Contract: SourcesConfig", () => {
  it("validates MOCK_SOURCES_CONFIG", () => {
    expect(SourcesConfigResponseSchema.safeParse(MOCK_SOURCES_CONFIG).success).toBe(true);
  });
});

describe("Contract: Insights", () => {
  it("validates MOCK_DIGEST", () => {
    expect(DigestResponseSchema.safeParse(MOCK_DIGEST).success).toBe(true);
  });

  it("validates MOCK_PATTERNS", () => {
    expect(PatternsResponseSchema.safeParse(MOCK_PATTERNS).success).toBe(true);
  });

  it("validates each insight item", () => {
    for (const insight of MOCK_INSIGHTS) {
      expect(InsightItemSchema.safeParse(insight).success).toBe(true);
    }
  });
});

// ─── Negative Tests: Malformed payloads rejected ───

describe("Contract: Negative cases", () => {
  it("rejects AnswerPacket without confidence", () => {
    const malformed = { ...MOCK_ANSWER_HIGH, confidence: undefined };
    expect(AnswerPacketSchema.safeParse(malformed).success).toBe(false);
  });

  it("rejects AnswerPacket with invalid confidence level", () => {
    const malformed = { ...MOCK_ANSWER_HIGH, confidence: "super_high" };
    expect(AnswerPacketSchema.safeParse(malformed).success).toBe(false);
  });

  it("rejects AnswerPacket with invalid verification status", () => {
    const malformed = { ...MOCK_ANSWER_HIGH, verification: "MAYBE" };
    expect(AnswerPacketSchema.safeParse(malformed).success).toBe(false);
  });

  it("rejects HealthResponse with invalid status", () => {
    const malformed = { ...MOCK_HEALTH_HEALTHY, status: "broken" };
    expect(HealthResponseSchema.safeParse(malformed).success).toBe(false);
  });

  it("rejects TimelineItem with invalid modality", () => {
    const malformed = { ...MOCK_TIMELINE_ITEMS[0], modality: "video" };
    expect(TimelineItemSchema.safeParse(malformed).success).toBe(false);
  });

  it("rejects AnswerPacket with missing answer field", () => {
    const rest = { ...MOCK_ANSWER_HIGH };
    delete (rest as Partial<typeof MOCK_ANSWER_HIGH>).answer;
    expect(AnswerPacketSchema.safeParse(rest).success).toBe(false);
  });

  it("rejects GraphNode missing required fields", () => {
    expect(GraphNodeSchema.safeParse({ id: "n1" }).success).toBe(false);
  });

  it("rejects completely empty object", () => {
    expect(AnswerPacketSchema.safeParse({}).success).toBe(false);
    expect(GraphDataSchema.safeParse({}).success).toBe(false);
    expect(HealthResponseSchema.safeParse({}).success).toBe(false);
  });

  it("rejects null payloads", () => {
    expect(AnswerPacketSchema.safeParse(null).success).toBe(false);
    expect(TimelineResponseSchema.safeParse(null).success).toBe(false);
  });
});

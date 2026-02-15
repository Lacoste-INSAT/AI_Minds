/**
 * UI-specific type definitions for Synapsis frontend.
 * Extends backend contracts with presentation-layer types.
 *
 * Source: ARCHITECTURE.md, DESIGN_SYSTEM.md
 */

import type {
  ConfidenceLevel,
  VerificationStatus,
  TimelineModality,
  HealthState,
  AnswerPacket,
  IngestionWsEventType,
  IngestionWsMessage,
} from "./contracts";

// ─── Entity Types ───

export type EntityType =
  | "person"
  | "organization"
  | "project"
  | "concept"
  | "location"
  | "datetime"
  | "document";

// ─── Navigation ───

export interface NavItem {
  title: string;
  href: string;
  icon: string;
  description?: string;
  badge?: string;
}

// ─── Chat ───

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  answer?: AnswerPacket;
  isStreaming?: boolean;
}

export interface ChatSession {
  id: string;
  messages: ChatMessage[];
  createdAt: string;
  updatedAt: string;
}

// ─── Graph UI ───

export type GraphDimension = "2d" | "3d";

export interface GraphViewState {
  dimension: GraphDimension;
  selectedNodeId: string | null;
  filters: {
    entityTypes: EntityType[];
    minMentionCount: number;
  };
  zoom: number;
}

// ─── Timeline UI ───

export interface TimelineFilters {
  modality: TimelineModality | "all";
  category: string | "all";
  search: string;
  dateRange: {
    from: string | null;
    to: string | null;
  };
}

export interface TimelineGroupedItems {
  label: string;
  date: string;
  items: import("./contracts").TimelineItem[];
}

// ─── Setup ───

export type SetupStep = "welcome" | "directories" | "exclusions" | "complete";

export interface SetupState {
  currentStep: SetupStep;
  directories: string[];
  exclusions: string[];
  isComplete: boolean;
}

// ─── Search ───

export type SearchViewMode = "card" | "table";

export interface SearchFilters {
  query: string;
  modality: TimelineModality | "all";
  entityType: EntityType | "all";
  category: string | "all";
}

export interface SearchResult {
  id: string;
  title: string;
  snippet: string;
  modality: TimelineModality;
  category: string;
  entities: string[];
  score: number;
  source_uri: string;
  ingested_at: string;
  group: SearchResultGroup;
  target: SearchResultTarget;
}

export type SearchResultGroup = "documents" | "entities" | "actions";

export interface SearchResultTarget {
  route: "/chat" | "/timeline" | "/graph";
  id?: string;
  query?: string;
}

export interface SearchGroupedResults {
  documents: SearchResult[];
  entities: SearchResult[];
  actions: SearchResult[];
}

// ─── Health / Status ───

export interface AppStatus {
  health: HealthState;
  ingestionActive: boolean;
  lastScanTime: string | null;
  queueDepth: number;
}

export interface IngestionUiEvent {
  type: IngestionWsEventType;
  timestamp: number;
  summary: string;
  fileName?: string;
  raw: IngestionWsMessage;
}

// ─── Theme ───

export type ThemeMode = "light" | "dark" | "system";

// ─── Common UI State ───

export type AsyncStatus = "idle" | "loading" | "success" | "error";

export interface AsyncState<T> {
  status: AsyncStatus;
  data: T | null;
  error: string | null;
}

// ─── Confidence display config ───

export interface ConfidenceConfig {
  level: ConfidenceLevel;
  label: string;
  icon: string;
  colorVar: string;
  description: string;
}

// ─── Verification display config ───

export interface VerificationConfig {
  status: VerificationStatus;
  label: string;
  icon: string;
  variant: "default" | "secondary" | "destructive" | "outline";
  description: string;
}

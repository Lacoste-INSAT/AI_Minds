/**
 * Synapsis application constants.
 * Single source of truth for enums, display maps, and static config.
 *
 * Source: DESIGN_SYSTEM.md, BRAND_IDENTITY.md, ARCHITECTURE.md
 */

import type {
  ConfidenceLevel,
  VerificationStatus,
  TimelineModality,
  HealthState,
} from "@/types/contracts";
import type {
  EntityType,
  NavItem,
  ConfidenceConfig,
  VerificationConfig,
} from "@/types/ui";

// ─── Navigation ───

export const NAV_ITEMS: NavItem[] = [
  {
    title: "Chat",
    href: "/chat",
    icon: "MessageSquare",
    description: "Ask anything about your knowledge",
  },
  {
    title: "Graph",
    href: "/graph",
    icon: "Network",
    description: "Explore knowledge connections",
  },
  {
    title: "Timeline",
    href: "/timeline",
    icon: "Clock",
    description: "Browse your memory feed",
  },
  {
    title: "Search",
    href: "/search",
    icon: "Search",
    description: "Find specific knowledge",
  },
  {

    title: "Settings",
    href: "/settings",
    icon: "Settings",
    description: "Manage knowledge sources & watcher",

  },
];

// ─── Confidence ───

export const CONFIDENCE_CONFIG: Record<ConfidenceLevel, ConfidenceConfig> = {
  high: {
    level: "high",
    label: "High confidence",
    icon: "ShieldCheck",
    colorVar: "var(--confidence-high)",
    description: "Strong evidence supports this answer.",
  },
  medium: {
    level: "medium",
    label: "Medium confidence",
    icon: "ShieldAlert",
    colorVar: "var(--confidence-medium)",
    description: "Some evidence supports this answer, but gaps exist.",
  },
  low: {
    level: "low",
    label: "Low confidence",
    icon: "ShieldQuestion",
    colorVar: "var(--confidence-low)",
    description: "Limited evidence available. Treat with caution.",
  },
  none: {
    level: "none",
    label: "No confidence",
    icon: "ShieldX",
    colorVar: "var(--confidence-none)",
    description:
      "I don't have enough information in your records to answer this confidently.",
  },
};

// ─── Verification ───

export const VERIFICATION_CONFIG: Record<
  VerificationStatus,
  VerificationConfig
> = {
  APPROVE: {
    status: "APPROVE",
    label: "Verified",
    icon: "CheckCircle",
    variant: "default",
    description: "This answer has been verified against source material.",
  },
  REVISE: {
    status: "REVISE",
    label: "Partially verified",
    icon: "AlertCircle",
    variant: "secondary",
    description: "This answer may need revision based on available evidence.",
  },
  REJECT: {
    status: "REJECT",
    label: "Unverified",
    icon: "XCircle",
    variant: "destructive",
    description: "This answer could not be verified. Review source material.",
  },
};

// ─── Entity Types ───

export const ENTITY_TYPE_CONFIG: Record<
  EntityType,
  { label: string; colorVar: string; icon: string }
> = {
  person: {
    label: "Person",
    colorVar: "var(--entity-person)",
    icon: "User",
  },
  organization: {
    label: "Organization",
    colorVar: "var(--entity-organization)",
    icon: "Building2",
  },
  project: {
    label: "Project",
    colorVar: "var(--entity-project)",
    icon: "FolderKanban",
  },
  concept: {
    label: "Concept",
    colorVar: "var(--entity-concept)",
    icon: "Lightbulb",
  },
  location: {
    label: "Location",
    colorVar: "var(--entity-location)",
    icon: "MapPin",
  },
  datetime: {
    label: "Date/Time",
    colorVar: "var(--entity-datetime)",
    icon: "Calendar",
  },
  document: {
    label: "Document",
    colorVar: "var(--entity-document)",
    icon: "FileText",
  },
};

// ─── Modality ───

export const MODALITY_CONFIG: Record<
  TimelineModality,
  { label: string; icon: string }
> = {
  text: { label: "Text", icon: "FileText" },
  pdf: { label: "PDF", icon: "FileType" },
  image: { label: "Image", icon: "Image" },
  audio: { label: "Audio", icon: "Headphones" },
  json: { label: "JSON", icon: "FileJson" },
};

// ─── Health ───

export const HEALTH_CONFIG: Record<
  HealthState,
  { label: string; icon: string; variant: "default" | "secondary" | "destructive" }
> = {
  healthy: {
    label: "All systems operational",
    icon: "CircleCheck",
    variant: "default",
  },
  degraded: {
    label: "Some services degraded",
    icon: "AlertTriangle",
    variant: "secondary",
  },
  unhealthy: {
    label: "System issues detected",
    icon: "CircleX",
    variant: "destructive",
  },
};

// ─── Setup Steps ───

export const SETUP_STEPS = [
  { key: "welcome" as const, title: "Welcome", description: "Get started with Synapsis" },
  { key: "directories" as const, title: "Directories", description: "Select knowledge sources" },
  { key: "exclusions" as const, title: "Exclusions", description: "Configure file filters" },
  { key: "complete" as const, title: "Complete", description: "Review and finish" },
];

// ─── Application Defaults ───

export const APP_DEFAULTS = {
  /** Page size for timeline pagination */
  TIMELINE_PAGE_SIZE: 20,
  /** Default graph node limit  */
  GRAPH_NODE_LIMIT: 200,
  /** Default top_k for query */
  QUERY_TOP_K: 10,
  /** Health poll interval (ms) */
  HEALTH_POLL_INTERVAL: 30_000,
  /** Ingestion poll interval (ms) */
  INGESTION_POLL_INTERVAL: 5_000,
  /** Debounce delay for search input (ms) */
  SEARCH_DEBOUNCE_MS: 300,
  /** Max file size for display purposes (MB) */
  MAX_FILE_SIZE_MB: 50,
} as const;

// ─── Brand Copy ───
// Source: BRAND_IDENTITY.md — tone and micro-copy rules

export const BRAND_COPY = {
  INPUT_PLACEHOLDER: "Ask anything about your knowledge...",
  ABSTENTION:
    "I don't have enough information in your records to answer this confidently.",
  EMPTY_TIMELINE: "No knowledge items yet. Configure your sources to begin.",
  EMPTY_GRAPH: "No connections found. Ingest documents to build your knowledge graph.",
  EMPTY_SEARCH: "No results found. Try a different query or adjust filters.",
  LOADING: "Retrieving from your knowledge base...",
  STREAMING: "Analyzing your records...",
  FIRST_RUN_TITLE: "Welcome to Synapsis",
  FIRST_RUN_SUBTITLE: "Your personal knowledge assistant. Local. Private. Intelligent.",
} as const;

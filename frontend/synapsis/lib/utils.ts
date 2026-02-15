import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { ConfidenceLevel, VerificationStatus } from "@/types/contracts";

// ─── Class merging ───

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ─── Date helpers ───
// Uses date-fns conventions but zero-dep for core formatting.

/**
 * Format an ISO timestamp into a relative date label.
 * Returns "Today", "Yesterday", or a formatted date string.
 */
export function formatRelativeDate(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();

  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0 && date.getDate() === now.getDate()) return "Today";
  if (diffDays <= 1 && date.getDate() === now.getDate() - 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined,
  });
}

/**
 * Format a full timestamp for display (e.g. "Feb 14, 2026 at 3:45 PM").
 */
export function formatTimestamp(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }) +
    " at " +
    date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
    });
}

/**
 * Get a date group key for timeline grouping (YYYY-MM-DD).
 */
export function getDateGroupKey(isoString: string): string {
  return new Date(isoString).toISOString().split("T")[0];
}

// ─── Confidence helpers ───

/**
 * Returns true when confidence is too low for a definitive answer.
 * Used to trigger abstention UI.
 */
export function shouldAbstain(confidence: ConfidenceLevel): boolean {
  return confidence === "none" || confidence === "low";
}

/**
 * Numeric score (0-1) to ConfidenceLevel.
 */
export function scoreToConfidence(score: number): ConfidenceLevel {
  if (score >= 0.8) return "high";
  if (score >= 0.5) return "medium";
  if (score >= 0.2) return "low";
  return "none";
}

/**
 * Confidence level to numeric order for sorting.
 */
export function confidenceOrder(level: ConfidenceLevel): number {
  const order: Record<ConfidenceLevel, number> = {
    high: 4,
    medium: 3,
    low: 2,
    none: 1,
  };
  return order[level];
}

// ─── Verification helpers ───

/**
 * Is the verification in a "trusted" state?
 */
export function isTrusted(status: VerificationStatus): boolean {
  return status === "APPROVE";
}

// ─── Text helpers ───

/**
 * Truncate text with ellipsis. Word-boundary aware.
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  const truncated = text.slice(0, maxLength);
  const lastSpace = truncated.lastIndexOf(" ");
  return (lastSpace > maxLength * 0.6 ? truncated.slice(0, lastSpace) : truncated) + "…";
}

/**
 * Extract a plain-text preview from markdown-ish content.
 */
export function stripMarkdown(text: string): string {
  return text
    .replace(/#{1,6}\s/g, "")
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/\*(.*?)\*/g, "$1")
    .replace(/`(.*?)`/g, "$1")
    .replace(/\[(.*?)\]\(.*?\)/g, "$1")
    .replace(/\n+/g, " ")
    .trim();
}

// ─── Misc ───

/**
 * Generate a client-side unique ID.
 */
export function createId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

/**
 * Safely parse JSON, returning null on failure.
 */
export function safeJsonParse<T>(json: string): T | null {
  try {
    return JSON.parse(json) as T;
  } catch {
    return null;
  }
}

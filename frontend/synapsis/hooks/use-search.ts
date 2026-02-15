"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import type { MemorySearchResult, TimelineItem } from "@/types/contracts";
import type {
  AsyncState,
  EntityType,
  SearchFilters,
  SearchGroupedResults,
  SearchResult,
} from "@/types/ui";
import { apiClient } from "@/lib/api/client";
import { APP_DEFAULTS } from "@/lib/constants";

interface UseSearchReturn extends AsyncState<SearchResult[]> {
  filters: SearchFilters;
  setFilters: (filters: Partial<SearchFilters>) => void;
  groupedResults: SearchGroupedResults;
  search: () => void;
}

const DEFAULT_FILTERS: SearchFilters = {
  query: "",
  modality: "all",
  entityType: "all",
  category: "all",
};

function inferEntityType(name: string): EntityType {
  const lower = name.toLowerCase();
  if (lower.includes("inc") || lower.includes("corp") || lower.includes("org")) {
    return "organization";
  }
  if (lower.includes("project") || lower.includes("system")) {
    return "project";
  }
  if (/\b[a-z]+\s+[a-z]+\b/i.test(name)) {
    return "person";
  }
  return "concept";
}

export function useSearch(): UseSearchReturn {
  const [state, setState] = useState<AsyncState<SearchResult[]>>({
    status: "idle",
    data: null,
    error: null,
  });
  const [filters, setFiltersState] = useState<SearchFilters>(DEFAULT_FILTERS);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const setFilters = useCallback((partial: Partial<SearchFilters>) => {
    setFiltersState((prev) => ({ ...prev, ...partial }));
  }, []);

  const toSearchResults = useCallback(
    (items: TimelineItem[], memoryHits: MemorySearchResult[]): SearchResult[] => {
      const query = filters.query.toLowerCase().trim();
      const docs = memoryHits.map((hit) => ({
        id: hit.document_id,
        title: hit.filename,
        snippet: hit.summary ?? hit.content,
        modality: hit.modality,
        category: hit.category ?? "uncategorized",
        entities: [],
        score: 1,
        source_uri: "",
        ingested_at: hit.ingested_at,
        group: "documents" as const,
        target: { route: "/timeline" as const, id: hit.document_id },
      }));

      const entities = Array.from(
        new Set(
          items.flatMap((item) =>
            item.entities.filter((entity) =>
              query ? entity.toLowerCase().includes(query) : true
            )
          )
        )
      )
        .filter((entity) => {
          if (filters.entityType === "all") {
            return true;
          }
          return inferEntityType(entity) === filters.entityType;
        })
        .slice(0, 8)
        .map((entity) => ({
          id: `entity-${entity.toLowerCase().replace(/\s+/g, "-")}`,
          title: entity,
          snippet: `Explore relationships for ${entity}`,
          modality: "text" as const,
          category: "entity",
          entities: [entity],
          score: 0.8,
          source_uri: "",
          ingested_at: new Date().toISOString(),
          group: "entities" as const,
          target: { route: "/graph" as const, query: entity },
        }));

      const actions: SearchResult[] = query
        ? [
            {
              id: "action-ask-chat",
              title: `Ask in chat: "${filters.query}"`,
              snippet: "Open chat and run this question",
              modality: "text",
              category: "action",
              entities: [],
              score: 0.7,
              source_uri: "",
              ingested_at: new Date().toISOString(),
              group: "actions",
              target: { route: "/chat", query: filters.query },
            },
          ]
        : [];

      return [...docs, ...entities, ...actions];
    },
    [filters.entityType, filters.query]
  );

  const search = useCallback(async () => {
    if (!filters.query.trim()) {
      setState({ status: "idle", data: [], error: null });
      return;
    }

    setState((prev) => ({ ...prev, status: "loading" }));

    const [result, timeline] = await Promise.all([
      apiClient.searchMemory(filters.query, {
        modality: filters.modality !== "all" ? filters.modality : undefined,
        category: filters.category !== "all" ? filters.category : undefined,
        limit: 50,
      }),
      apiClient.getTimeline(1, 50, { search: filters.query }),
    ]);

    if (result.ok && timeline.ok) {
      setState({
        status: "success",
        data: toSearchResults(timeline.data.items, result.data),
        error: null,
      });
      return;
    }

    setState({
      status: "error",
      data: [],
      error: !result.ok ? result.error : !timeline.ok ? timeline.error : "Search failed",
    });
  }, [filters, toSearchResults]);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      void search();
    }, APP_DEFAULTS.SEARCH_DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [search]);

  const groupedResults: SearchGroupedResults = {
    documents: (state.data ?? []).filter((item) => item.group === "documents"),
    entities: (state.data ?? []).filter((item) => item.group === "entities"),
    actions: (state.data ?? []).filter((item) => item.group === "actions"),
  };

  return { ...state, filters, setFilters, groupedResults, search };
}


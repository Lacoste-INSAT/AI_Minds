"use client";

import { useRouter } from "next/navigation";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SearchFilters } from "@/components/search/search-filters";
import { SearchResults } from "@/components/search/search-results";
import { ErrorAlert } from "@/components/shared/error-alert";
import { useSearch } from "@/hooks/use-search";
import type { SearchResult } from "@/types/ui";

export default function SearchPage() {
  const router = useRouter();
  const { status, error, filters, setFilters, groupedResults, search } = useSearch();

  const navigateFromResult = (result: SearchResult) => {
    const params = new URLSearchParams();
    if (result.target.id) {
      params.set("id", result.target.id);
    }
    if (result.target.query) {
      params.set("q", result.target.query);
    }
    const suffix = params.toString();
    router.push(suffix ? `${result.target.route}?${suffix}` : result.target.route);
  };

  return (
    <div className="flex h-full flex-col gap-4">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Search</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Find specific knowledge across your records
        </p>
      </div>

      <SearchFilters filters={filters} onFilterChange={setFilters} />

      {status === "error" && (
        <ErrorAlert
          severity="error"
          title="Search unavailable"
          message={error ?? "Unable to load search results from backend."}
          onRetry={search}
        />
      )}

      {/* Results */}
      <ScrollArea className="flex-1">
        <SearchResults
          items={[...groupedResults.documents, ...groupedResults.entities]}
          isLoading={status === "loading"}
          query={filters.query}
          onSelect={navigateFromResult}
        />
      </ScrollArea>
    </div>
  );
}

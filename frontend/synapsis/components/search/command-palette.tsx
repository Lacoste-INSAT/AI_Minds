"use client";

/**
 * CommandPalette — Global Cmd-K / Ctrl-K command palette.
 * Quick navigation + search across all views.
 *
 * Source: ARCHITECTURE.md §Search, DESIGN_SYSTEM.md
 */

import { useCallback, useEffect, useState } from "react";
import type { ElementType } from "react";
import { useRouter } from "next/navigation";
import {
  MessageSquare,
  Network,
  Clock,
  Search,
  Settings,
  Brain,
  FileText,
  Sparkles,
} from "lucide-react";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import { NAV_ITEMS } from "@/lib/constants";
import { useSearch } from "@/hooks/use-search";
import type { SearchResult } from "@/types/ui";

// Icon map
const ICON_MAP: Record<string, ElementType> = {
  MessageSquare,
  Network,
  Clock,
  Search,
  Settings,
  FileText,
  Sparkles,
};

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const { filters, setFilters, groupedResults } = useSearch();

  // Cmd-K / Ctrl-K listener
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    if (!open && filters.query) {
      setFilters({ query: "" });
    }
  }, [filters.query, open, setFilters]);

  const navigate = useCallback(
    (href: string) => {
      setOpen(false);
      router.push(href);
    },
    [router]
  );

  const navigateFromResult = useCallback(
    (result: SearchResult) => {
      const params = new URLSearchParams();
      if (result.target.id) {
        params.set("id", result.target.id);
      }
      if (result.target.query) {
        params.set("q", result.target.query);
      }
      const suffix = params.toString();
      navigate(suffix ? `${result.target.route}?${suffix}` : result.target.route);
    },
    [navigate]
  );

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput
        value={filters.query}
        onValueChange={(value) => setFilters({ query: value })}
        placeholder="Search or navigate..."
      />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>

        {/* Navigation */}
        <CommandGroup heading="Navigation">
          {NAV_ITEMS.map((item) => {
            const Icon = ICON_MAP[item.icon] ?? Brain;
            return (
              <CommandItem
                key={item.href}
                onSelect={() => navigate(item.href)}
                className="gap-2"
              >
                <Icon className="h-4 w-4" />
                <span>{item.title}</span>
                {item.description && (
                  <span className="ml-auto text-xs text-muted-foreground">
                    {item.description}
                  </span>
                )}
              </CommandItem>
            );
          })}
        </CommandGroup>

        <CommandSeparator />

        {filters.query.trim().length > 0 && (
          <>
            <CommandGroup heading="Sources">
              {groupedResults.documents.slice(0, 6).map((result) => (
                <CommandItem
                  key={result.id}
                  onSelect={() => navigateFromResult(result)}
                  className="gap-2"
                >
                  <FileText className="h-4 w-4" />
                  <span>{result.title}</span>
                </CommandItem>
              ))}
            </CommandGroup>
            <CommandGroup heading="Entities">
              {groupedResults.entities.slice(0, 6).map((result) => (
                <CommandItem
                  key={result.id}
                  onSelect={() => navigateFromResult(result)}
                  className="gap-2"
                >
                  <Network className="h-4 w-4" />
                  <span>{result.title}</span>
                </CommandItem>
              ))}
            </CommandGroup>
            <CommandGroup heading="Actions">
              {groupedResults.actions.slice(0, 4).map((result) => (
                <CommandItem
                  key={result.id}
                  onSelect={() => navigateFromResult(result)}
                  className="gap-2"
                >
                  <Sparkles className="h-4 w-4" />
                  <span>{result.title}</span>
                </CommandItem>
              ))}
            </CommandGroup>
            <CommandSeparator />
          </>
        )}

        <CommandGroup heading="Quick Actions">
          <CommandItem onSelect={() => navigate("/chat")} className="gap-2">
            <MessageSquare className="h-4 w-4" />
            <span>New question</span>
          </CommandItem>
          <CommandItem onSelect={() => navigate("/search")} className="gap-2">
            <Search className="h-4 w-4" />
            <span>Search knowledge</span>
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}

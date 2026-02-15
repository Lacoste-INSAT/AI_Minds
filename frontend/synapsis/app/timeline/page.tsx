"use client";

import { useCallback, useEffect, useState } from "react";
import { AppSidebar } from "@/components/app-sidebar";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  RefreshCw,
  Search,
  FileText,
  FileImage,
  FileAudio,
  FileJson,
  File,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Calendar,
  Tag,
  Link as LinkIcon,
} from "lucide-react";

interface TimelineItem {
  id: string;
  title: string;
  summary: string | null;
  category: string | null;
  modality: string;
  source_uri: string | null;
  ingested_at: string;
  entities: string[];
}

interface TimelineResponse {
  items: TimelineItem[];
  total: number;
  page: number;
  page_size: number;
}

// Modality icons
const MODALITY_ICONS: Record<string, typeof FileText> = {
  text: FileText,
  pdf: FileText,
  image: FileImage,
  audio: FileAudio,
  json: FileJson,
};

// Category colors
const CATEGORY_COLORS: Record<string, string> = {
  work: "bg-blue-500",
  personal: "bg-green-500",
  research: "bg-purple-500",
  meeting: "bg-amber-500",
  note: "bg-cyan-500",
  reference: "bg-rose-500",
};

export default function TimelinePage() {
  const [data, setData] = useState<TimelineResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [modalityFilter, setModalityFilter] = useState<string>("all");
  const [sortOrder, setSortOrder] = useState<"desc" | "asc">("desc");
  const [selectedItem, setSelectedItem] = useState<TimelineItem | null>(null);

  const fetchTimeline = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: "20",
        sort: sortOrder,
      });
      if (searchTerm) params.append("search", searchTerm);
      if (categoryFilter !== "all") params.append("category", categoryFilter);
      if (modalityFilter !== "all") params.append("modality", modalityFilter);

      const response = await fetch(`/api/memory/timeline?${params}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch timeline: ${response.status}`);
      }
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load timeline");
    } finally {
      setLoading(false);
    }
  }, [page, searchTerm, categoryFilter, modalityFilter, sortOrder]);

  useEffect(() => {
    fetchTimeline();
  }, [fetchTimeline]);

  // Debounced search
  useEffect(() => {
    const timeout = setTimeout(() => {
      setPage(1);
    }, 300);
    return () => clearTimeout(timeout);
  }, [searchTerm]);

  const totalPages = data ? Math.ceil(data.total / data.page_size) : 0;

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getModalityIcon = (modality: string) => {
    const Icon = MODALITY_ICONS[modality.toLowerCase()] || File;
    return <Icon className="w-4 h-4" />;
  };

  const getCategoryColor = (category: string | null) => {
    if (!category) return "bg-gray-500";
    return CATEGORY_COLORS[category.toLowerCase()] || "bg-gray-500";
  };

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="flex flex-col h-screen">
        <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-2 h-4" />
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbPage>Memory Timeline</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
        </header>

        <div className="flex flex-1 overflow-hidden">
          {/* Main Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {/* Filters */}
            <div className="flex flex-wrap gap-4 mb-6">
              <div className="flex items-center gap-2 flex-1 min-w-64">
                <Search className="w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search memories..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="max-w-sm"
                />
              </div>

              <Select value={categoryFilter} onValueChange={(v) => { setCategoryFilter(v); setPage(1); }}>
                <SelectTrigger className="w-36">
                  <Tag className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  <SelectItem value="work">Work</SelectItem>
                  <SelectItem value="personal">Personal</SelectItem>
                  <SelectItem value="research">Research</SelectItem>
                  <SelectItem value="meeting">Meeting</SelectItem>
                  <SelectItem value="note">Note</SelectItem>
                  <SelectItem value="reference">Reference</SelectItem>
                </SelectContent>
              </Select>

              <Select value={modalityFilter} onValueChange={(v) => { setModalityFilter(v); setPage(1); }}>
                <SelectTrigger className="w-36">
                  <File className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="text">Text</SelectItem>
                  <SelectItem value="pdf">PDF</SelectItem>
                  <SelectItem value="image">Image</SelectItem>
                  <SelectItem value="audio">Audio</SelectItem>
                  <SelectItem value="json">JSON</SelectItem>
                </SelectContent>
              </Select>

              <Select value={sortOrder} onValueChange={(v) => { setSortOrder(v as "desc" | "asc"); setPage(1); }}>
                <SelectTrigger className="w-36">
                  <Calendar className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Sort" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="desc">Newest First</SelectItem>
                  <SelectItem value="asc">Oldest First</SelectItem>
                </SelectContent>
              </Select>

              <Button variant="outline" size="icon" onClick={fetchTimeline} disabled={loading}>
                <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              </Button>
            </div>

            {/* Stats */}
            {data && (
              <div className="text-sm text-muted-foreground mb-4">
                Showing {data.items.length} of {data.total} memories
              </div>
            )}

            {/* Timeline */}
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
              </div>
            ) : error ? (
              <Card className="max-w-lg mx-auto">
                <CardHeader>
                  <CardTitle className="text-destructive">Error</CardTitle>
                  <CardDescription>{error}</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button onClick={fetchTimeline}>Retry</Button>
                </CardContent>
              </Card>
            ) : data?.items.length === 0 ? (
              <Card className="max-w-lg mx-auto">
                <CardHeader>
                  <CardTitle>No Memories Found</CardTitle>
                  <CardDescription>
                    {searchTerm || categoryFilter !== "all" || modalityFilter !== "all"
                      ? "Try adjusting your filters."
                      : "Add some documents to your watched directories to see them here."}
                  </CardDescription>
                </CardHeader>
              </Card>
            ) : (
              <div className="relative">
                {/* Timeline line */}
                <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-border" />

                {/* Timeline items */}
                <div className="space-y-4">
                  {data?.items.map((item) => (
                    <div
                      key={item.id}
                      className="relative pl-10 cursor-pointer"
                      onClick={() => setSelectedItem(item)}
                    >
                      {/* Timeline dot */}
                      <div
                        className={`absolute left-2.5 w-3 h-3 rounded-full border-2 border-background ${getCategoryColor(item.category)}`}
                      />

                      {/* Card */}
                      <Card
                        className={`transition-shadow hover:shadow-md ${
                          selectedItem?.id === item.id ? "ring-2 ring-primary" : ""
                        }`}
                      >
                        <CardHeader className="pb-2">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex items-center gap-2">
                              {getModalityIcon(item.modality)}
                              <CardTitle className="text-base">{item.title}</CardTitle>
                            </div>
                            <div className="flex items-center gap-2">
                              {item.category && (
                                <Badge variant="secondary" className="capitalize">
                                  {item.category}
                                </Badge>
                              )}
                              <Badge variant="outline" className="capitalize">
                                {item.modality}
                              </Badge>
                            </div>
                          </div>
                          <CardDescription className="flex items-center gap-1 text-xs">
                            <Calendar className="w-3 h-3" />
                            {formatDate(item.ingested_at)}
                          </CardDescription>
                        </CardHeader>
                        <CardContent className="pb-3">
                          {item.summary && (
                            <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
                              {item.summary}
                            </p>
                          )}
                          {item.entities.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {item.entities.slice(0, 5).map((entity, idx) => (
                                <Badge key={idx} variant="outline" className="text-xs">
                                  {entity}
                                </Badge>
                              ))}
                              {item.entities.length > 5 && (
                                <Badge variant="outline" className="text-xs">
                                  +{item.entities.length - 5} more
                                </Badge>
                              )}
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Pagination */}
            {data && totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-6">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 1}
                  onClick={() => setPage(page - 1)}
                >
                  <ChevronLeft className="w-4 h-4 mr-1" />
                  Previous
                </Button>
                <span className="text-sm text-muted-foreground">
                  Page {page} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage(page + 1)}
                >
                  Next
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
            )}
          </div>

          {/* Detail Panel */}
          {selectedItem && (
            <div className="w-80 border-l bg-muted/30 p-4 overflow-y-auto">
              <Card>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <Badge
                      variant="outline"
                      className="capitalize"
                    >
                      {selectedItem.modality}
                    </Badge>
                    <Button size="icon" variant="ghost" onClick={() => setSelectedItem(null)}>
                      ×
                    </Button>
                  </div>
                  <CardTitle className="text-lg mt-2">{selectedItem.title}</CardTitle>
                  <CardDescription className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {formatDate(selectedItem.ingested_at)}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {selectedItem.category && (
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">Category</div>
                      <Badge className={`${getCategoryColor(selectedItem.category)} capitalize`}>
                        {selectedItem.category}
                      </Badge>
                    </div>
                  )}

                  {selectedItem.summary && (
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">Summary</div>
                      <p className="text-sm">{selectedItem.summary}</p>
                    </div>
                  )}

                  {selectedItem.source_uri && (
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">Source</div>
                      <div className="flex items-center gap-1 text-sm text-primary">
                        <LinkIcon className="w-3 h-3" />
                        <span className="truncate">{selectedItem.source_uri}</span>
                      </div>
                    </div>
                  )}

                  {selectedItem.entities.length > 0 && (
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">
                        Entities ({selectedItem.entities.length})
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {selectedItem.entities.map((entity, idx) => (
                          <Badge key={idx} variant="secondary" className="text-xs">
                            {entity}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="pt-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full"
                      onClick={() => window.open(`/api/memory/${selectedItem.id}`, "_blank")}
                    >
                      View Full Details
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}

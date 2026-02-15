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
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  RefreshCw,
  Lightbulb,
  Link2,
  AlertTriangle,
  TrendingUp,
  ScrollText,
  Loader2,
  Calendar,
  Sparkles,
} from "lucide-react";

interface InsightItem {
  type: string; // "connection" | "contradiction" | "pattern" | "digest"
  title: string;
  description: string;
  related_entities: string[];
  created_at: string;
}

interface DigestResponse {
  insights: InsightItem[];
  generated_at: string | null;
}

interface PatternInfo {
  co_occurring_entities: string[][];
  frequent_topics: Record<string, number>;
  entity_clusters: Record<string, string[]>;
}

// Insight type icons and colors
const INSIGHT_CONFIG: Record<string, { icon: typeof Lightbulb; color: string; bgColor: string }> = {
  connection: {
    icon: Link2,
    color: "text-blue-600",
    bgColor: "bg-blue-100 dark:bg-blue-900/30",
  },
  contradiction: {
    icon: AlertTriangle,
    color: "text-amber-600",
    bgColor: "bg-amber-100 dark:bg-amber-900/30",
  },
  pattern: {
    icon: TrendingUp,
    color: "text-purple-600",
    bgColor: "bg-purple-100 dark:bg-purple-900/30",
  },
  digest: {
    icon: ScrollText,
    color: "text-green-600",
    bgColor: "bg-green-100 dark:bg-green-900/30",
  },
};

export default function DigestPage() {
  const [digestData, setDigestData] = useState<DigestResponse | null>(null);
  const [patternData, setPatternData] = useState<PatternInfo | null>(null);
  const [loading, setLoading] = useState(true);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [patternLoading, setPatternLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDigest = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/insights/digest");
      if (!response.ok) {
        throw new Error(`Failed to fetch digest: ${response.status}`);
      }
      const data = await response.json();
      setDigestData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load digest");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchPatterns = useCallback(async () => {
    setPatternLoading(true);
    try {
      const response = await fetch("/api/insights/patterns");
      if (response.ok) {
        const data = await response.json();
        setPatternData(data);
      }
    } catch {
      // Patterns are optional, don't show error
    } finally {
      setPatternLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDigest();
    fetchPatterns();
  }, [fetchDigest, fetchPatterns]);

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

  const getInsightConfig = (type: string) => {
    return INSIGHT_CONFIG[type.toLowerCase()] || INSIGHT_CONFIG.digest;
  };

  const handleRefresh = () => {
    fetchDigest();
    fetchPatterns();
  };

  // Group insights by type
  const groupedInsights = digestData?.insights.reduce((acc, insight) => {
    const type = insight.type.toLowerCase();
    if (!acc[type]) acc[type] = [];
    acc[type].push(insight);
    return acc;
  }, {} as Record<string, InsightItem[]>) || {};

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
                <BreadcrumbPage>Insights & Digest</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
        </header>

        <div className="flex-1 overflow-y-auto p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <Sparkles className="w-6 h-6 text-primary" />
                Proactive Insights
              </h1>
              <p className="text-muted-foreground">
                Automatically discovered connections, patterns, and contradictions in your knowledge
              </p>
            </div>
            <Button variant="outline" onClick={handleRefresh} disabled={loading}>
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>

          {/* Last generated */}
          {digestData?.generated_at && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-6">
              <Calendar className="w-4 h-4" />
              Last updated: {formatDate(digestData.generated_at)}
            </div>
          )}

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
                <Button onClick={handleRefresh}>Retry</Button>
              </CardContent>
            </Card>
          ) : digestData?.insights.length === 0 ? (
            <Card className="max-w-lg mx-auto">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lightbulb className="w-5 h-5" />
                  No Insights Yet
                </CardTitle>
                <CardDescription>
                  As you add more documents to your knowledge base, Synapsis will automatically
                  discover connections, patterns, and potential contradictions. Check back later!
                </CardDescription>
              </CardHeader>
            </Card>
          ) : (
            <div className="grid gap-6 lg:grid-cols-2">
              {/* Insight cards by type */}
              {Object.entries(groupedInsights).map(([type, insights]) => {
                const config = getInsightConfig(type);
                const Icon = config.icon;

                return (
                  <Card key={type} className="col-span-1">
                    <CardHeader className="pb-2">
                      <CardTitle className={`flex items-center gap-2 ${config.color}`}>
                        <div className={`p-2 rounded-lg ${config.bgColor}`}>
                          <Icon className="w-5 h-5" />
                        </div>
                        <span className="capitalize">{type}s</span>
                        <Badge variant="secondary" className="ml-auto">
                          {insights.length}
                        </Badge>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {insights.slice(0, 5).map((insight, idx) => (
                        <div
                          key={idx}
                          className={`p-3 rounded-lg ${config.bgColor} border`}
                        >
                          <div className="font-medium text-sm">{insight.title}</div>
                          <div className="text-sm text-muted-foreground mt-1">
                            {insight.description}
                          </div>
                          {insight.related_entities.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {insight.related_entities.slice(0, 3).map((entity, i) => (
                                <Badge key={i} variant="outline" className="text-xs">
                                  {entity}
                                </Badge>
                              ))}
                              {insight.related_entities.length > 3 && (
                                <Badge variant="outline" className="text-xs">
                                  +{insight.related_entities.length - 3}
                                </Badge>
                              )}
                            </div>
                          )}
                          <div className="text-xs text-muted-foreground mt-2">
                            {formatDate(insight.created_at)}
                          </div>
                        </div>
                      ))}
                      {insights.length > 5 && (
                        <div className="text-sm text-muted-foreground text-center">
                          +{insights.length - 5} more {type}s
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}

              {/* Pattern Analysis */}
              {patternData && (
                <Card className="col-span-1 lg:col-span-2">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-purple-600">
                      <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/30">
                        <TrendingUp className="w-5 h-5" />
                      </div>
                      Pattern Analysis
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                      {/* Frequent Topics */}
                      {Object.keys(patternData.frequent_topics).length > 0 && (
                        <div>
                          <div className="text-sm font-medium mb-2">Frequent Topics</div>
                          <div className="space-y-1">
                            {Object.entries(patternData.frequent_topics)
                              .sort(([, a], [, b]) => b - a)
                              .slice(0, 5)
                              .map(([topic, count]) => (
                                <div
                                  key={topic}
                                  className="flex items-center justify-between text-sm"
                                >
                                  <span>{topic}</span>
                                  <Badge variant="secondary">{count}</Badge>
                                </div>
                              ))}
                          </div>
                        </div>
                      )}

                      {/* Co-occurring Entities */}
                      {patternData.co_occurring_entities.length > 0 && (
                        <div>
                          <div className="text-sm font-medium mb-2">Co-occurring Entities</div>
                          <div className="space-y-2">
                            {patternData.co_occurring_entities.slice(0, 5).map((group, idx) => (
                              <div key={idx} className="flex flex-wrap gap-1">
                                {group.map((entity, i) => (
                                  <Badge key={i} variant="outline" className="text-xs">
                                    {entity}
                                  </Badge>
                                ))}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Entity Clusters */}
                      {Object.keys(patternData.entity_clusters).length > 0 && (
                        <div>
                          <div className="text-sm font-medium mb-2">Entity Clusters</div>
                          <div className="space-y-2">
                            {Object.entries(patternData.entity_clusters)
                              .slice(0, 5)
                              .map(([cluster, entities]) => (
                                <div key={cluster}>
                                  <div className="text-xs text-muted-foreground mb-1">
                                    {cluster}
                                  </div>
                                  <div className="flex flex-wrap gap-1">
                                    {entities.slice(0, 4).map((entity, i) => (
                                      <Badge key={i} variant="secondary" className="text-xs">
                                        {entity}
                                      </Badge>
                                    ))}
                                    {entities.length > 4 && (
                                      <Badge variant="secondary" className="text-xs">
                                        +{entities.length - 4}
                                      </Badge>
                                    )}
                                  </div>
                                </div>
                              ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}

"use client";
import { useFetch } from "@/lib/hooks";
import { getDigest, getAllInsights, getPatterns } from "@/lib/api";
import { Lightbulb, TrendingUp, Sparkles, BookOpen, BarChart2 } from "lucide-react";

export default function InsightsPage() {
  const { data: digest, loading: loadingDigest } = useFetch(getDigest);
  const { data: insights, loading: loadingInsights } = useFetch(getAllInsights);
  const { data: patterns } = useFetch(getPatterns);

  return (
    <div className="animate-fade-in space-y-6 max-w-5xl">
      <h2 className="text-2xl font-bold">Insights &amp; Patterns</h2>
      <p className="text-sm text-muted -mt-4">AI-generated summaries, cross-document insights, and knowledge patterns</p>

      {/* Daily Digest */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-accent" /> Daily Digest
        </h3>
        {loadingDigest ? (
          <p className="text-sm text-muted">Generating digest...</p>
        ) : digest?.insights?.length ? (
          <div className="space-y-3">
            {digest.generated_at && (
              <p className="text-xs text-muted">Generated {digest.generated_at}</p>
            )}
            {digest.insights.map((item, i) => (
              <div key={i} className="bg-background rounded-lg p-4 border border-border/50">
                <div className="flex items-start justify-between mb-1">
                  <span className="text-sm font-medium flex items-center gap-2">
                    <Sparkles className="w-3.5 h-3.5 text-yellow-400 shrink-0" />
                    {item.title || item.type}
                  </span>
                  <span className="text-[10px] text-muted">{item.created_at}</span>
                </div>
                <p className="text-sm text-muted">{item.description}</p>
                {item.related_entities?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {item.related_entities.map((e, j) => (
                      <span key={j} className="text-[10px] bg-accent/10 text-accent rounded px-1.5 py-0.5">{e}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted">No digest available. Ingest some documents first.</p>
        )}
      </div>

      {/* Cross-document Insights */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <Lightbulb className="w-5 h-5 text-yellow-400" /> Cross-document Insights
        </h3>
        {loadingInsights ? (
          <p className="text-sm text-muted">Loading insights...</p>
        ) : insights?.insights?.length ? (
          <div className="grid gap-3">
            {insights.insights.map((insight, i) => (
              <div key={i} className="bg-background rounded-lg p-4 border border-border/50">
                <div className="flex items-start justify-between mb-2">
                  <span className="text-sm font-medium">{insight.title || insight.type || "Insight"}</span>
                  <span className="text-[10px] text-muted">{insight.created_at}</span>
                </div>
                <p className="text-sm text-muted">{insight.description}</p>
                {insight.related_entities?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {insight.related_entities.map((s, j) => (
                      <span key={j} className="text-[10px] bg-accent/10 text-accent rounded px-1.5 py-0.5">{s}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted">No cross-document insights found yet.</p>
        )}
      </div>

      {/* Patterns */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-green-400" /> Knowledge Patterns
        </h3>
        {patterns?.patterns?.length ? (
          <div className="grid sm:grid-cols-2 gap-3">
            {patterns.patterns.map((p: any, i: number) => (
              <div key={i} className="bg-background rounded-lg p-4 border border-border/50">
                <div className="flex items-center gap-2 mb-1">
                  <BarChart2 className="w-4 h-4 text-accent" />
                  <span className="text-sm font-medium">{p.pattern || p.name || p.label}</span>
                </div>
                <p className="text-xs text-muted">{p.description || `Frequency: ${p.frequency || p.count || "—"}`}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted">No patterns detected yet.</p>
        )}
      </div>
    </div>
  );
}

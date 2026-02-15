"use client";
import { useFetch } from "@/lib/hooks";
import { getDigest, getAllInsights, getPatterns } from "@/lib/api";
import { Lightbulb, TrendingUp, Sparkles, BookOpen, BarChart2 } from "lucide-react";

export default function InsightsPage() {
  const { data: digest, loading: loadingDigest } = useFetch(getDigest);
  const { data: insights, loading: loadingInsights } = useFetch(getAllInsights);
  const { data: patterns } = useFetch(getPatterns);

  return (
    <div className="animate-fade-in space-y-6 max-w-5xl relative">
      {/* Background blobs */}
      <div className="pointer-events-none absolute -top-20 -left-20 w-[400px] h-[400px] rounded-full bg-yellow-500/[0.03] blur-3xl animate-float" />
      <div className="pointer-events-none absolute top-60 -right-32 w-[350px] h-[350px] rounded-full bg-accent/[0.03] blur-3xl animate-float-delay" />

      {/* Hero header */}
      <div className="relative overflow-hidden rounded-2xl gradient-border p-6 animate-hero-reveal"
           style={{ background: "linear-gradient(135deg, rgba(245,158,11,0.08) 0%, rgba(99,102,241,0.04) 50%, rgba(17,24,39,0.95) 100%)" }}>
        <div className="absolute top-0 h-full w-[20%] bg-gradient-to-r from-transparent via-amber-500/[0.04] to-transparent animate-scanline pointer-events-none" />
        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-amber-400 animate-breathe" />
            <span className="text-[11px] uppercase tracking-[0.2em] text-amber-400/70 font-medium">Intelligence</span>
          </div>
          <h2 className="text-3xl font-extrabold bg-gradient-to-r from-white via-amber-200 to-orange-300 bg-clip-text text-transparent animate-gradient-text">
            Insights &amp; Patterns
          </h2>
          <p className="text-sm text-muted/80 mt-1.5">AI-generated summaries, cross-document insights, and knowledge patterns</p>
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-amber-500/30 to-transparent" />
      </div>

      {/* Daily Digest */}
      <div className="glass rounded-2xl gradient-border p-6">
        <div className="flex items-center gap-2 mb-5">
          <div className="w-1 h-4 rounded-full bg-gradient-to-b from-amber-400 to-orange-500" />
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-amber-400" /> Daily Digest
          </h3>
        </div>
        {loadingDigest ? (
          <div className="animate-shimmer rounded-xl p-4 text-sm text-muted">Generating digest...</div>
        ) : digest?.insights?.length ? (
          <div className="space-y-3">
            {digest.generated_at && (
              <p className="text-xs text-muted bg-white/[0.03] px-3 py-1.5 rounded-lg ring-1 ring-white/[0.06] inline-block">Generated {digest.generated_at}</p>
            )}
            {digest.insights.map((item, i) => (
              <div key={i} className="bg-white/[0.02] rounded-xl p-4 ring-1 ring-white/[0.04] hover:ring-amber-500/20 transition-all animate-slide-up" style={{ animationDelay: `${i * 60}ms` }}>
                <div className="flex items-start justify-between mb-1">
                  <span className="text-sm font-medium flex items-center gap-2">
                    <Sparkles className="w-3.5 h-3.5 text-yellow-400 shrink-0" />
                    {item.title || item.type}
                  </span>
                  <span className="text-[10px] text-muted bg-white/[0.04] px-2 py-0.5 rounded-md">{item.created_at}</span>
                </div>
                <p className="text-sm text-muted">{item.description}</p>
                {item.related_entities?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {item.related_entities.map((e, j) => (
                      <span key={j} className="text-[10px] bg-accent/10 text-accent-light rounded-md px-2 py-0.5 ring-1 ring-accent/10">{e}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-10 text-center rounded-xl border border-dashed border-white/[0.08]">
            <BookOpen className="w-8 h-8 text-muted/30 mb-3" />
            <p className="text-sm text-muted">No digest available</p>
            <p className="text-xs text-muted/60 mt-1">Ingest some documents first</p>
          </div>
        )}
      </div>

      {/* Cross-document Insights */}
      <div className="glass rounded-2xl gradient-border p-6">
        <div className="flex items-center gap-2 mb-5">
          <div className="w-1 h-4 rounded-full bg-gradient-to-b from-yellow-400 to-amber-500" />
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <Lightbulb className="w-4 h-4 text-yellow-400" /> Cross-document Insights
          </h3>
        </div>
        {loadingInsights ? (
          <div className="animate-shimmer rounded-xl p-4 text-sm text-muted">Loading insights...</div>
        ) : insights?.insights?.length ? (
          <div className="grid gap-3">
            {insights.insights.map((insight, i) => (
              <div key={i} className="bg-white/[0.02] rounded-xl p-4 ring-1 ring-white/[0.04] hover:ring-yellow-500/20 transition-all animate-slide-up" style={{ animationDelay: `${i * 60}ms` }}>
                <div className="flex items-start justify-between mb-2">
                  <span className="text-sm font-medium">{insight.title || insight.type || "Insight"}</span>
                  <span className="text-[10px] text-muted bg-white/[0.04] px-2 py-0.5 rounded-md">{insight.created_at}</span>
                </div>
                <p className="text-sm text-muted">{insight.description}</p>
                {insight.related_entities?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {insight.related_entities.map((s, j) => (
                      <span key={j} className="text-[10px] bg-accent/10 text-accent-light rounded-md px-2 py-0.5 ring-1 ring-accent/10">{s}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-10 text-center rounded-xl border border-dashed border-white/[0.08]">
            <Lightbulb className="w-8 h-8 text-muted/30 mb-3" />
            <p className="text-sm text-muted">No cross-document insights found yet</p>
          </div>
        )}
      </div>

      {/* Patterns */}
      <div className="glass rounded-2xl gradient-border p-6">
        <div className="flex items-center gap-2 mb-5">
          <div className="w-1 h-4 rounded-full bg-gradient-to-b from-green-400 to-emerald-500" />
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-green-400" /> Knowledge Patterns
          </h3>
        </div>
        {patterns?.patterns?.length ? (
          <div className="grid sm:grid-cols-2 gap-3">
            {patterns.patterns.map((p: any, i: number) => (
              <div key={i} className="bg-white/[0.02] rounded-xl p-4 ring-1 ring-white/[0.04] hover:ring-green-500/20 transition-all animate-slide-up" style={{ animationDelay: `${i * 60}ms` }}>
                <div className="flex items-center gap-2 mb-1">
                  <BarChart2 className="w-4 h-4 text-accent-light" />
                  <span className="text-sm font-medium">{p.pattern || p.name || p.label}</span>
                </div>
                <p className="text-xs text-muted">{p.description || `Frequency: ${p.frequency || p.count || "—"}`}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-10 text-center rounded-xl border border-dashed border-white/[0.08]">
            <TrendingUp className="w-8 h-8 text-muted/30 mb-3" />
            <p className="text-sm text-muted">No patterns detected yet</p>
          </div>
        )}
      </div>
    </div>
  );
}

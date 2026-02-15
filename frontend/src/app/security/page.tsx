"use client";
import { useState } from "react";
import { useFetch } from "@/lib/hooks";
import { getSecurityStatus, getAirGap, scanPII } from "@/lib/api";
import { Shield, Wifi, WifiOff, Search, Check, X, Lock, AlertTriangle } from "lucide-react";

export default function SecurityPage() {
  const { data: statusRaw, loading } = useFetch(getSecurityStatus);
  const status = statusRaw as Record<string, any> | undefined;
  const { data: airGapRaw, loading: loadingAG } = useFetch(getAirGap);
  const airGap = airGapRaw as { air_gapped?: boolean; checks?: Array<{ service: string; local: boolean; reason: string }>; issues?: string[] } | undefined;
  const [piiText, setPiiText] = useState("");
  const [piiResult, setPiiResult] = useState<any>(null);
  const [scanning, setScanning] = useState(false);

  const handlePiiScan = async () => {
    if (!piiText.trim()) return;
    setScanning(true);
    try {
      const r = await scanPII(piiText);
      setPiiResult(r);
    } catch (e: any) {
      setPiiResult({ error: e.message });
    } finally {
      setScanning(false);
    }
  };

  const StatusDot = ({ ok }: { ok: boolean }) => (
    <span className={`w-2 h-2 rounded-full ${ok ? "bg-green-400 shadow-[0_0_6px_rgba(74,222,128,0.4)]" : "bg-red-400 shadow-[0_0_6px_rgba(248,113,113,0.4)]"}`} />
  );

  return (
    <div className="animate-fade-in space-y-6 max-w-5xl relative">
      {/* Background blobs */}
      <div className="pointer-events-none absolute -top-20 -left-20 w-[400px] h-[400px] rounded-full bg-red-500/[0.03] blur-3xl animate-float" />
      <div className="pointer-events-none absolute top-60 -right-32 w-[350px] h-[350px] rounded-full bg-accent/[0.03] blur-3xl animate-float-delay" />

      {/* Hero header */}
      <div className="relative overflow-hidden rounded-2xl gradient-border p-6 animate-hero-reveal"
           style={{ background: "linear-gradient(135deg, rgba(239,68,68,0.08) 0%, rgba(99,102,241,0.04) 50%, rgba(17,24,39,0.95) 100%)" }}>
        <div className="absolute top-0 h-full w-[20%] bg-gradient-to-r from-transparent via-red-500/[0.04] to-transparent animate-scanline pointer-events-none" />
        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-red-400 animate-breathe" />
            <span className="text-[11px] uppercase tracking-[0.2em] text-red-400/70 font-medium">Defense Layer</span>
          </div>
          <h2 className="text-3xl font-extrabold bg-gradient-to-r from-white via-red-200 to-rose-300 bg-clip-text text-transparent animate-gradient-text">
            Security &amp; Privacy
          </h2>
          <p className="text-sm text-muted/80 mt-1.5">Air-gap verification, PII detection, and security posture</p>
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-red-500/30 to-transparent" />
      </div>

      {/* Security posture */}
      <div className="glass rounded-2xl gradient-border p-6">
        <div className="flex items-center gap-2 mb-5">
          <div className="w-1 h-4 rounded-full bg-gradient-to-b from-red-400 to-rose-500" />
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <Shield className="w-4 h-4 text-red-400" /> Security Posture
          </h3>
        </div>
        {loading ? (
          <div className="animate-shimmer rounded-xl p-4 text-sm text-muted">Loading...</div>
        ) : status ? (
          <div className="grid sm:grid-cols-2 gap-3">
            {Object.entries(status).map(([k, v]) => {
              const isObj = typeof v === "object" && v !== null;
              const enabled = isObj ? v.enabled : v;
              const detail = isObj ? (v.backend || v.block_threshold || (v.patterns_loaded ? "Active" : "")) : null;
              return (
                <div key={k} className="flex items-center gap-3 bg-white/[0.02] rounded-xl px-4 py-3 ring-1 ring-white/[0.06] hover:ring-red-500/20 transition-all">
                  {typeof enabled === "boolean" ? <StatusDot ok={enabled} /> : <Lock className="w-4 h-4 text-muted" />}
                  <div>
                    <div className="text-sm font-medium capitalize">{k.replace(/_/g, " ")}</div>
                    <div className="text-xs text-muted">
                      {typeof enabled === "boolean" ? (enabled ? "Enabled" : "Disabled") : Array.isArray(v) ? `${v.length} items` : String(v)}
                      {detail ? ` — ${detail}` : ""}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-10 text-center rounded-xl border border-dashed border-white/[0.08]">
            <Shield className="w-8 h-8 text-muted/30 mb-3" />
            <p className="text-sm text-muted">Security status unavailable</p>
          </div>
        )}
      </div>

      {/* Air-gap */}
      <div className="glass rounded-2xl gradient-border p-6">
        <div className="flex items-center gap-2 mb-5">
          <div className="w-1 h-4 rounded-full bg-gradient-to-b from-emerald-400 to-green-500" />
          <h3 className="text-sm font-semibold flex items-center gap-2">
            {airGap?.air_gapped ? <WifiOff className="w-4 h-4 text-green-400" /> : <Wifi className="w-4 h-4 text-yellow-400" />}
            Air-Gap Verification
          </h3>
        </div>
        {loadingAG ? (
          <div className="animate-shimmer rounded-xl p-4 text-sm text-muted">Verifying...</div>
        ) : airGap ? (
          <div className="space-y-3">
            <div className={`flex items-center gap-2 text-sm font-medium px-3 py-2 rounded-xl ring-1 ${airGap.air_gapped ? "text-green-400 bg-green-400/[0.05] ring-green-400/20" : "text-yellow-400 bg-yellow-400/[0.05] ring-yellow-400/20"}`}>
              {airGap.air_gapped ? <Check className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
              {airGap.air_gapped ? "System is operating in air-gap mode" : "Air-gap not verified — external connections may be active"}
            </div>
            {airGap.checks && airGap.checks.length > 0 && (
              <div className="space-y-1.5">
                {airGap.checks.map((c: any, i: number) => (
                  <div key={i} className="flex items-center gap-2 text-sm bg-white/[0.02] rounded-lg px-3 py-2 ring-1 ring-white/[0.04] animate-slide-up" style={{ animationDelay: `${i * 60}ms` }}>
                    {c.local ? <Check className="w-3.5 h-3.5 text-green-400" /> : <X className="w-3.5 h-3.5 text-red-400" />}
                    <span className="text-muted">{c.service}</span>
                    <span className="text-xs text-muted/60 ml-auto">— {c.reason}</span>
                  </div>
                ))}
              </div>
            )}
            {airGap.issues && airGap.issues.length > 0 && (
              <div className="space-y-1">
                {airGap.issues.map((issue: string, i: number) => (
                  <div key={i} className="flex items-center gap-2 text-sm text-red-400 bg-red-400/[0.05] rounded-lg px-3 py-2 ring-1 ring-red-400/20">
                    <AlertTriangle className="w-3.5 h-3.5" /> {issue}
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-10 text-center rounded-xl border border-dashed border-white/[0.08]">
            <WifiOff className="w-8 h-8 text-muted/30 mb-3" />
            <p className="text-sm text-muted">Could not verify air-gap status</p>
          </div>
        )}
      </div>

      {/* PII Scanner */}
      <div className="glass rounded-2xl gradient-border p-6">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-1 h-4 rounded-full bg-gradient-to-b from-accent to-purple-500" />
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <Search className="w-4 h-4 text-accent-light" /> PII Scanner
          </h3>
        </div>
        <p className="text-xs text-muted mb-3">Paste text below to check for Personally Identifiable Information before ingestion</p>
        <textarea
          value={piiText}
          onChange={(e) => setPiiText(e.target.value)}
          rows={4}
          placeholder="Enter text to scan for PII..."
          className="w-full glass rounded-xl px-4 py-3 text-sm resize-none ring-1 ring-white/[0.06] focus:ring-accent/30 focus:outline-none transition-all mb-3"
        />
        <button
          onClick={handlePiiScan}
          disabled={scanning || !piiText.trim()}
          className="flex items-center gap-2 bg-gradient-to-r from-accent to-purple-600 hover:from-accent/90 hover:to-purple-500 px-5 py-2.5 rounded-xl text-sm font-medium transition-all disabled:opacity-50 shadow-lg shadow-accent/20"
        >
          {scanning ? "Scanning..." : "Scan for PII"}
        </button>

        {piiResult && (
          <div className="mt-4 bg-white/[0.02] rounded-xl p-4 ring-1 ring-white/[0.06]">
            {piiResult.error ? (
              <p className="text-sm text-red-400">{piiResult.error}</p>
            ) : (
              <>
                <div className={`text-sm font-medium mb-2 flex items-center gap-2 ${piiResult.pii_detected || piiResult.has_pii ? "text-red-400" : "text-green-400"}`}>
                  {piiResult.pii_detected || piiResult.has_pii ? <AlertTriangle className="w-4 h-4" /> : <Check className="w-4 h-4" />}
                  {piiResult.pii_detected || piiResult.has_pii ? "PII Detected" : "No PII Detected"}
                </div>
                {(piiResult.entities || piiResult.findings || piiResult.matches)?.length > 0 && (
                  <div className="space-y-1.5">
                    {(piiResult.entities || piiResult.findings || piiResult.matches).map((e: any, i: number) => (
                      <div key={i} className="flex items-center gap-2 text-sm bg-white/[0.02] rounded-lg px-3 py-2 ring-1 ring-white/[0.04]">
                        <AlertTriangle className="w-3.5 h-3.5 text-yellow-400" />
                        <span className="text-muted">{e.type || e.label}:</span>
                        <span className="font-mono text-xs text-accent-light">{e.text || e.value || e.match}</span>
                      </div>
                    ))}
                  </div>
                )}
                {piiResult.sanitized && (
                  <div className="mt-3">
                    <div className="text-xs text-muted mb-1.5">Sanitized output:</div>
                    <p className="text-sm font-mono bg-white/[0.03] rounded-lg p-3 ring-1 ring-white/[0.06]">{piiResult.sanitized}</p>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

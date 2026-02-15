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
    <span className={`w-2 h-2 rounded-full ${ok ? "bg-green-400" : "bg-red-400"}`} />
  );

  return (
    <div className="animate-fade-in space-y-6 max-w-5xl">
      <h2 className="text-2xl font-bold">Security &amp; Privacy</h2>
      <p className="text-sm text-muted -mt-4">Air-gap verification, PII detection, and security posture</p>

      {/* Security posture */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-accent" /> Security Posture
        </h3>
        {loading ? (
          <p className="text-sm text-muted">Loading...</p>
        ) : status ? (
          <div className="grid sm:grid-cols-2 gap-3">
            {Object.entries(status).map(([k, v]) => {
              const isObj = typeof v === "object" && v !== null;
              const enabled = isObj ? v.enabled : v;
              const detail = isObj ? (v.backend || v.block_threshold || (v.patterns_loaded ? "Active" : "")) : null;
              return (
                <div key={k} className="flex items-center gap-3 bg-background rounded-lg px-4 py-3">
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
          <p className="text-sm text-muted">Security status unavailable</p>
        )}
      </div>

      {/* Air-gap */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          {airGap?.air_gapped ? <WifiOff className="w-5 h-5 text-green-400" /> : <Wifi className="w-5 h-5 text-yellow-400" />}
          Air-Gap Verification
        </h3>
        {loadingAG ? (
          <p className="text-sm text-muted">Verifying...</p>
        ) : airGap ? (
          <div className="space-y-3">
            <div className={`flex items-center gap-2 text-sm font-medium ${airGap.air_gapped ? "text-green-400" : "text-yellow-400"}`}>
              {airGap.air_gapped ? <Check className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
              {airGap.air_gapped ? "System is operating in air-gap mode" : "Air-gap not verified — external connections may be active"}
            </div>
            {airGap.checks && airGap.checks.length > 0 && (
              <div className="space-y-1.5">
                {airGap.checks.map((c: any, i: number) => (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    {c.local ? <Check className="w-3.5 h-3.5 text-green-400" /> : <X className="w-3.5 h-3.5 text-red-400" />}
                    <span className="text-muted">{c.service}</span>
                    <span className="text-xs text-muted/60">— {c.reason}</span>
                  </div>
                ))}
              </div>
            )}
            {airGap.issues && airGap.issues.length > 0 && (
              <div className="space-y-1">
                {airGap.issues.map((issue: string, i: number) => (
                  <div key={i} className="flex items-center gap-2 text-sm text-red-400">
                    <AlertTriangle className="w-3.5 h-3.5" /> {issue}
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm text-muted">Could not verify air-gap status</p>
        )}
      </div>

      {/* PII Scanner */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <Search className="w-5 h-5 text-accent" /> PII Scanner
        </h3>
        <p className="text-xs text-muted mb-3">Paste text below to check for Personally Identifiable Information before ingestion</p>
        <textarea
          value={piiText}
          onChange={(e) => setPiiText(e.target.value)}
          rows={4}
          placeholder="Enter text to scan for PII..."
          className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm resize-none mb-3"
        />
        <button
          onClick={handlePiiScan}
          disabled={scanning || !piiText.trim()}
          className="flex items-center gap-2 bg-accent hover:bg-accent/80 px-4 py-2 rounded-lg text-sm font-medium transition disabled:opacity-50"
        >
          {scanning ? "Scanning..." : "Scan for PII"}
        </button>

        {piiResult && (
          <div className="mt-4 bg-background rounded-lg p-4 border border-border/50">
            {piiResult.error ? (
              <p className="text-sm text-red-400">{piiResult.error}</p>
            ) : (
              <>
                <div className={`text-sm font-medium mb-2 ${piiResult.pii_detected || piiResult.has_pii ? "text-red-400" : "text-green-400"}`}>
                  {piiResult.pii_detected || piiResult.has_pii ? "PII Detected" : "No PII Detected"}
                </div>
                {(piiResult.entities || piiResult.findings || piiResult.matches)?.length > 0 && (
                  <div className="space-y-1">
                    {(piiResult.entities || piiResult.findings || piiResult.matches).map((e: any, i: number) => (
                      <div key={i} className="flex items-center gap-2 text-sm">
                        <AlertTriangle className="w-3.5 h-3.5 text-yellow-400" />
                        <span className="text-muted">{e.type || e.label}:</span>
                        <span className="font-mono text-xs">{e.text || e.value || e.match}</span>
                      </div>
                    ))}
                  </div>
                )}
                {piiResult.sanitized && (
                  <div className="mt-2">
                    <div className="text-xs text-muted mb-1">Sanitized output:</div>
                    <p className="text-sm font-mono bg-card rounded p-2">{piiResult.sanitized}</p>
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

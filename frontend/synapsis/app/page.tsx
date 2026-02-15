"use client";

import { useState, useRef, useEffect } from "react";
import { AppSidebar } from "@/components/app-sidebar";
import {
  Breadcrumb, BreadcrumbItem, BreadcrumbList, BreadcrumbPage,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import {
  SidebarInset, SidebarProvider, SidebarTrigger,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Send, Loader2, Brain, ShieldCheck, ShieldAlert, ShieldX,
  FileText, ChevronDown, ChevronUp, AlertCircle,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/* ------------------------------------------------------------------ */
/* Types matching backend AnswerPacket (§9.1)                          */
/* ------------------------------------------------------------------ */

interface ChunkEvidence {
  chunk_id: string;
  file_name: string;
  snippet: string;
  score_dense: number;
  score_sparse: number;
  score_final: number;
}

interface AnswerPacket {
  answer: string;
  confidence: "high" | "medium" | "low" | "none";
  confidence_score: number;
  uncertainty_reason: string | null;
  sources: ChunkEvidence[];
  verification: "APPROVE" | "REVISE" | "REJECT";
  reasoning_chain: string | null;
}

interface ChatEntry {
  id: string;
  question: string;
  answer: AnswerPacket | null;
  loading: boolean;
  error: string | null;
}

/* ------------------------------------------------------------------ */
/* Small UI pieces                                                     */
/* ------------------------------------------------------------------ */

const CONF: Record<string, { bg: string; Icon: typeof ShieldCheck }> = {
  high:   { bg: "bg-green-600",  Icon: ShieldCheck },
  medium: { bg: "bg-amber-500",  Icon: ShieldAlert },
  low:    { bg: "bg-orange-500", Icon: ShieldAlert },
  none:   { bg: "bg-red-500",    Icon: ShieldX },
};

function ConfBadge({ level, score }: { level: string; score: number }) {
  const { bg, Icon } = CONF[level] ?? CONF.none;
  return (
    <Badge className={`${bg} text-white gap-1`}>
      <Icon className="h-3 w-3" />
      {level} ({Math.round(score * 100)}%)
    </Badge>
  );
}

function VerifBadge({ status }: { status: string }) {
  if (status === "APPROVE")
    return <Badge variant="outline" className="text-green-600 border-green-600 gap-1"><ShieldCheck className="h-3 w-3" />Verified</Badge>;
  if (status === "REVISE")
    return <Badge variant="outline" className="text-amber-600 border-amber-600 gap-1"><ShieldAlert className="h-3 w-3" />Revised</Badge>;
  return <Badge variant="outline" className="text-red-600 border-red-600 gap-1"><ShieldX className="h-3 w-3" />Rejected</Badge>;
}

function SourceCard({ src, idx }: { src: ChunkEvidence; idx: number }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border rounded-lg p-3 bg-muted/40">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center justify-between text-sm">
        <span className="flex items-center gap-2 text-left">
          <FileText className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          <span className="font-medium">[{idx + 1}] {src.file_name}</span>
          <span className="text-xs text-muted-foreground">score {src.score_final.toFixed(2)}</span>
        </span>
        {open ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
      </button>
      {open && (
        <p className="mt-2 text-xs text-muted-foreground whitespace-pre-wrap border-t pt-2">
          {src.snippet}
        </p>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Page                                                                */
/* ------------------------------------------------------------------ */

export default function ChatPage() {
  const [input, setInput] = useState("");
  const [history, setHistory] = useState<ChatEntry[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  const handleSend = async () => {
    const q = input.trim();
    if (!q) return;
    const id = `q-${Date.now()}`;
    setHistory((h) => [...h, { id, question: q, answer: null, loading: true, error: null }]);
    setInput("");
    taRef.current?.focus();

    try {
      const res = await fetch("/api/query/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q, top_k: 10, include_graph: true }),
      });
      if (!res.ok) throw new Error((await res.text()) || `${res.status}`);
      const pkt: AnswerPacket = await res.json();
      setHistory((h) => h.map((e) => (e.id === id ? { ...e, answer: pkt, loading: false } : e)));
    } catch (err) {
      setHistory((h) =>
        h.map((e) =>
          e.id === id ? { ...e, error: err instanceof Error ? err.message : "Error", loading: false } : e,
        ),
      );
    }
  };

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const busy = history.some((e) => e.loading);

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="flex flex-col h-svh">
        <header className="flex h-14 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-2 h-4" />
          <Breadcrumb><BreadcrumbList><BreadcrumbItem><BreadcrumbPage>Chat</BreadcrumbPage></BreadcrumbItem></BreadcrumbList></Breadcrumb>
        </header>

        {/* Messages */}
        <ScrollArea className="flex-1">
          <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
            {history.length === 0 && (
              <div className="flex flex-col items-center justify-center py-24 gap-4 text-center">
                <Brain className="h-12 w-12 text-muted-foreground/40" />
                <h2 className="text-2xl font-semibold text-muted-foreground/60">Synapsis</h2>
                <p className="text-sm text-muted-foreground max-w-md">
                  Ask anything about your documents. Answers include confidence scores, source citations, and verification.
                </p>
              </div>
            )}

            {history.map((entry) => (
              <div key={entry.id} className="space-y-3">
                {/* User */}
                <div className="flex justify-end">
                  <div className="rounded-2xl bg-primary text-primary-foreground px-4 py-2.5 max-w-[80%]">
                    <p className="text-sm whitespace-pre-wrap">{entry.question}</p>
                  </div>
                </div>

                {entry.loading && (
                  <div className="flex items-center gap-2 text-muted-foreground text-sm">
                    <Loader2 className="h-4 w-4 animate-spin" /> Reasoning…
                  </div>
                )}

                {entry.error && (
                  <div className="flex items-start gap-2 p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
                    <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />{entry.error}
                  </div>
                )}

                {entry.answer && (
                  <div className="space-y-3">
                    {/* Answer text */}
                    <div className="rounded-2xl bg-muted/60 px-4 py-3 prose prose-sm dark:prose-invert max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{entry.answer.answer}</ReactMarkdown>
                    </div>

                    {/* Badges */}
                    <div className="flex flex-wrap items-center gap-2">
                      <ConfBadge level={entry.answer.confidence} score={entry.answer.confidence_score} />
                      <VerifBadge status={entry.answer.verification} />
                      {entry.answer.uncertainty_reason && (
                        <span className="text-xs text-muted-foreground italic">{entry.answer.uncertainty_reason}</span>
                      )}
                    </div>

                    {/* Sources */}
                    {entry.answer.sources.length > 0 && (
                      <div className="space-y-2">
                        <div className="text-xs font-medium text-muted-foreground">Sources ({entry.answer.sources.length})</div>
                        {entry.answer.sources.map((s, i) => <SourceCard key={s.chunk_id} src={s} idx={i} />)}
                      </div>
                    )}

                    {/* Reasoning chain */}
                    {entry.answer.reasoning_chain && (
                      <details className="text-xs">
                        <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
                          Show reasoning chain
                        </summary>
                        <pre className="mt-2 p-3 rounded bg-muted overflow-x-auto whitespace-pre-wrap">
                          {entry.answer.reasoning_chain}
                        </pre>
                      </details>
                    )}
                  </div>
                )}
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        </ScrollArea>

        {/* Input */}
        <div className="border-t p-4">
          <div className="max-w-3xl mx-auto flex gap-2">
            <Textarea
              ref={taRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKey}
              placeholder="Ask anything about your knowledge…"
              className="min-h-[44px] max-h-[160px] resize-none"
              rows={1}
              autoFocus
            />
            <Button size="icon" onClick={handleSend} disabled={!input.trim() || busy}
              className="shrink-0 h-[44px] w-[44px]">
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </Button>
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}

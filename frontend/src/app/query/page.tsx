"use client";
import { useState, useRef, useEffect } from "react";
import { askQuestion, type AnswerPacket } from "@/lib/api";
import { Send, Bot, User, Loader2, CheckCircle, AlertTriangle, XCircle, BookOpen, MessageSquare, Sparkles } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
  packet?: AnswerPacket;
}

export default function QueryPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const handleSend = async () => {
    const q = input.trim();
    if (!q || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: q }]);
    setLoading(true);
    try {
      const packet = await askQuestion(q);
      setMessages((m) => [...m, { role: "assistant", content: packet.answer, packet }]);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      setMessages((m) => [...m, { role: "assistant", content: `Error: ${msg}` }]);
    } finally {
      setLoading(false);
    }
  };

  const verIcon = (v?: string) => {
    if (v === "APPROVE") return <CheckCircle className="w-4 h-4 text-green-400" />;
    if (v === "REVISE") return <AlertTriangle className="w-4 h-4 text-amber-400" />;
    if (v === "REJECT") return <XCircle className="w-4 h-4 text-red-400" />;
    return null;
  };

  const confColor = (c?: string) => {
    if (c === "high") return "text-green-400";
    if (c === "medium") return "text-amber-400";
    return "text-red-400";
  };

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)] animate-fade-in relative">
      {/* Background blobs */}
      <div className="pointer-events-none absolute -top-20 -right-20 w-[400px] h-[400px] rounded-full bg-accent/[0.03] blur-3xl animate-float" />
      <div className="pointer-events-none absolute bottom-20 -left-32 w-[350px] h-[350px] rounded-full bg-purple-500/[0.03] blur-3xl animate-float-delay" />

      {/* Hero header */}
      <div className="relative overflow-hidden rounded-2xl gradient-border p-6 mb-5 animate-hero-reveal"
           style={{ background: "linear-gradient(135deg, rgba(99,102,241,0.08) 0%, rgba(6,182,212,0.04) 50%, rgba(17,24,39,0.95) 100%)" }}>
        <div className="absolute top-0 h-full w-[20%] bg-gradient-to-r from-transparent via-accent/[0.04] to-transparent animate-scanline pointer-events-none" />
        <div className="relative z-10 flex items-end justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 rounded-full bg-cyan-400 animate-breathe" />
              <span className="text-[11px] uppercase tracking-[0.2em] text-cyan-400/70 font-medium">Knowledge Query</span>
            </div>
            <h2 className="text-3xl font-extrabold bg-gradient-to-r from-white via-indigo-200 to-cyan-300 bg-clip-text text-transparent animate-gradient-text">
              Ask Synapsis
            </h2>
            <p className="text-sm text-muted/80 mt-1.5">Query your personal knowledge base with AI-powered hybrid retrieval and reasoning</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted bg-white/[0.03] px-3 py-1.5 rounded-lg ring-1 ring-white/[0.06]">
            <Sparkles className="w-3.5 h-3.5 text-accent-light animate-pulse-slow" />
            <span>{messages.length} messages</span>
          </div>
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent" />
      </div>

      {/* Chat */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-20 h-20 rounded-2xl bg-accent/10 flex items-center justify-center mb-5 ring-1 ring-accent/20">
              <MessageSquare className="w-10 h-10 text-accent/40" />
            </div>
            <p className="text-lg font-medium text-muted/80">Ask a question about your knowledge base</p>
            <p className="text-sm text-muted/50 mt-2 max-w-md">Synapsis uses hybrid retrieval and LLM reasoning to find answers across your documents, notes, and research</p>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-3 ${m.role === "user" ? "justify-end" : ""} animate-slide-up`}>
            {m.role === "assistant" && (
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent/30 to-purple-500/20 flex items-center justify-center shrink-0 mt-1 ring-1 ring-accent/20">
                <Bot className="w-4 h-4 text-accent-light" />
              </div>
            )}
            <div className={`max-w-2xl ${m.role === "user" ? "bg-gradient-to-br from-accent/20 to-accent/10 text-accent-light ring-1 ring-accent/20" : "glass gradient-border"} rounded-2xl px-4 py-3`}>
              <p className="text-sm whitespace-pre-wrap leading-relaxed">{m.content}</p>
              {m.packet && (
                <div className="mt-3 pt-3 border-t border-white/[0.06] space-y-2">
                  <div className="flex items-center gap-3 text-xs">
                    {verIcon(m.packet.verification)}
                    <span>{m.packet.verification}</span>
                    <span className="text-muted/40">|</span>
                    <span className={confColor(m.packet.confidence)}>
                      {m.packet.confidence} ({(m.packet.confidence_score * 100).toFixed(0)}%)
                    </span>
                  </div>
                  {m.packet.sources.length > 0 && (
                    <div className="space-y-1">
                      <p className="text-xs text-muted flex items-center gap-1"><BookOpen className="w-3 h-3" /> Sources</p>
                      {m.packet.sources.slice(0, 3).map((s, j) => (
                        <div key={j} className="text-xs bg-white/[0.03] rounded-lg px-3 py-2 ring-1 ring-white/[0.06]">
                          <span className="text-accent-light font-medium">{s.file_name}</span>
                          <span className="text-muted ml-2">score: {s.score_final.toFixed(3)}</span>
                          <p className="text-muted mt-0.5 line-clamp-2">{s.snippet}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
            {m.role === "user" && (
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-white/10 to-white/5 ring-1 ring-white/[0.08] flex items-center justify-center shrink-0 mt-1">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-3 animate-slide-up">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent/30 to-purple-500/20 flex items-center justify-center shrink-0 ring-1 ring-accent/20">
              <Bot className="w-4 h-4 text-accent-light" />
            </div>
            <div className="glass gradient-border rounded-2xl px-4 py-3">
              <Loader2 className="w-4 h-4 animate-spin text-accent-light" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="mt-4 flex gap-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
          placeholder="Ask a question..."
          className="flex-1 glass rounded-xl px-4 py-3 text-sm outline-none ring-1 ring-white/[0.06] focus:ring-accent/40 transition-all"
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || loading}
          className="bg-gradient-to-r from-accent to-purple-500 hover:from-accent-light hover:to-purple-400 disabled:opacity-40 text-white rounded-xl px-5 py-3 transition-all shadow-lg shadow-accent/20 hover:shadow-accent/30"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

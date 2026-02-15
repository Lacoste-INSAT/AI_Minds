"use client";
import { useState, useRef, useEffect } from "react";
import { askQuestion, type AnswerPacket } from "@/lib/api";
import { Send, Bot, User, Loader2, CheckCircle, AlertTriangle, XCircle, BookOpen } from "lucide-react";

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
    <div className="flex flex-col h-[calc(100vh-6rem)] animate-fade-in">
      <div className="mb-4">
        <h2 className="text-2xl font-bold">Ask Synapsis</h2>
        <p className="text-sm text-muted mt-1">Query your personal knowledge base with AI-powered reasoning</p>
      </div>

      {/* Chat */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Bot className="w-16 h-16 text-accent/30 mb-4" />
            <p className="text-lg text-muted">Ask a question about your knowledge base</p>
            <p className="text-sm text-muted/60 mt-2">Synapsis uses hybrid retrieval and LLM reasoning to answer</p>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-3 ${m.role === "user" ? "justify-end" : ""}`}>
            {m.role === "assistant" && (
              <div className="w-8 h-8 rounded-lg bg-accent/20 flex items-center justify-center shrink-0 mt-1">
                <Bot className="w-4 h-4 text-accent-light" />
              </div>
            )}
            <div className={`max-w-2xl ${m.role === "user" ? "bg-accent/20 text-accent-light" : "bg-card border border-border"} rounded-xl px-4 py-3`}>
              <p className="text-sm whitespace-pre-wrap leading-relaxed">{m.content}</p>
              {m.packet && (
                <div className="mt-3 pt-3 border-t border-border space-y-2">
                  <div className="flex items-center gap-3 text-xs">
                    {verIcon(m.packet.verification)}
                    <span>{m.packet.verification}</span>
                    <span className="text-muted">|</span>
                    <span className={confColor(m.packet.confidence)}>
                      {m.packet.confidence} ({(m.packet.confidence_score * 100).toFixed(0)}%)
                    </span>
                  </div>
                  {m.packet.sources.length > 0 && (
                    <div className="space-y-1">
                      <p className="text-xs text-muted flex items-center gap-1"><BookOpen className="w-3 h-3" /> Sources</p>
                      {m.packet.sources.slice(0, 3).map((s, j) => (
                        <div key={j} className="text-xs bg-background rounded px-2 py-1.5">
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
              <div className="w-8 h-8 rounded-lg bg-card border border-border flex items-center justify-center shrink-0 mt-1">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-lg bg-accent/20 flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4 text-accent-light" />
            </div>
            <div className="bg-card border border-border rounded-xl px-4 py-3">
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
          className="flex-1 bg-card border border-border rounded-xl px-4 py-3 text-sm outline-none focus:border-accent/50 transition-colors"
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || loading}
          className="bg-accent hover:bg-accent-light disabled:opacity-40 text-white rounded-xl px-5 py-3 transition-colors"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

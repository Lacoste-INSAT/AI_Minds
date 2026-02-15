"use client";

import { AppSidebar } from "@/components/app-sidebar";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { 
  Breadcrumb, 
  BreadcrumbItem, 
  BreadcrumbList, 
  BreadcrumbPage 
} from "@/components/ui/breadcrumb";
import { useState, useEffect, useRef } from "react";

interface RunEvent {
  type: string;
  [key: string]: unknown;
}

function PageBody() {
  const [status, setStatus] = useState<string>("initializing");
  const [message, setMessage] = useState<string>("");
  const [events, setEvents] = useState<string[]>([]);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    console.log("Component mounted, creating EventSource...");
    setStatus("connecting");

    const eventSource = new EventSource("/api/stream");
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      console.log("EventSource connection opened");
      setStatus("connected");
    };

    eventSource.onmessage = (e) => {
      console.log("Received message:", e.data);
      try {
        const event: RunEvent = JSON.parse(e.data);
        setEvents((prev) => [...prev.slice(-9), `${event.type}: ${JSON.stringify(event).slice(0, 50)}...`]);
      } catch {
        setEvents((prev) => [...prev.slice(-9), `raw: ${e.data}`]);
      }
    };

    eventSource.onerror = (e) => {
      console.log("EventSource error, readyState:", eventSource.readyState);
      if (eventSource.readyState === EventSource.CLOSED) {
        setStatus("closed");
      } else if (eventSource.readyState === EventSource.CONNECTING) {
        setStatus("reconnecting");
      }
    };

    return () => {
      console.log("Cleaning up EventSource");
      eventSource.close();
      eventSourceRef.current = null;
    };
  }, []);

  return (
    <>
      <AppSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2">
          <div className="flex items-center gap-2 px-4">
            <SidebarTrigger className="-ml-1" />
            <Separator orientation="vertical" className="mr-2 h-4" />
            <Breadcrumb>
              <BreadcrumbList>
                <BreadcrumbItem>
                  <BreadcrumbPage>Diagnostic Page</BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
          </div>
        </header>

        <div className="flex flex-1 flex-col gap-4 p-6">
          <div className="rounded-lg border p-4 space-y-4">
            <h1 className="text-xl font-semibold">Diagnostic Page (No Streamdown)</h1>
            <p className="text-muted-foreground">
              If you can see this page without freezing, the issue is with heavy components.
            </p>
            
            <div className="space-y-2">
              <p><strong>SSE Status:</strong> {status}</p>
              <p><strong>Input:</strong>{" "}
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Type something..."
                  className="border rounded px-2 py-1"
                />
              </p>
            </div>

            <div className="space-y-1">
              <p className="font-medium">Recent Events:</p>
              <div className="bg-muted rounded p-2 text-sm font-mono max-h-48 overflow-y-auto">
                {events.length === 0 ? (
                  <p className="text-muted-foreground">No events yet...</p>
                ) : (
                  events.map((evt, i) => <p key={i}>{evt}</p>)
                )}
              </div>
            </div>
          </div>
        </div>
      </SidebarInset>
    </>
  );
}

export default function DiagnosticPage() {
  return (
    <SidebarProvider>
      <PageBody />
    </SidebarProvider>
  );
}

"use client";

import { useState, useCallback } from "react";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { MessageList } from "@/components/chat/message-list";
import { ChatInput } from "@/components/chat/chat-input";
import { SourcePanel } from "@/components/chat/source-panel";
import { ErrorAlert } from "@/components/shared/error-alert";
import { useChat } from "@/hooks/use-chat";
import { useIsMobile } from "@/hooks/use-mobile";
import type { AnswerPacket } from "@/types/contracts";

export default function ChatPage() {
  const { messages, status, error, sendMessage } = useChat();
  const [selectedAnswer, setSelectedAnswer] = useState<AnswerPacket | null>(null);
  const [highlightedSource, setHighlightedSource] = useState<number | undefined>();
  const isMobile = useIsMobile();

  const handleSourceClick = useCallback(
    (messageId: string, sourceIndex: number) => {
      const msg = messages.find((m) => m.id === messageId);
      if (msg?.answer) {
        setSelectedAnswer(msg.answer);
        setHighlightedSource(sourceIndex);
      }
    },
    [messages]
  );

  const chatContent = (
    <div className="flex h-full flex-col">
      <MessageList
        messages={messages}
        onSourceClick={handleSourceClick}
        className="flex-1"
      />
      <div className="border-t p-4">
        {error && (
          <ErrorAlert
            className="mb-3"
            severity="error"
            title="Chat stream failed"
            message={error}
          />
        )}
        <ChatInput
          onSend={sendMessage}
          isLoading={status === "loading"}
        />
      </div>
    </div>
  );

  return (
    <div className="-m-6 flex h-[calc(100vh-3.5rem)] flex-col" role="region" aria-label="Chat">
      {/* SR status for loading */}
      <div className="sr-only" role="status" aria-live="polite">
        {status === "loading" ? "Processing your question..." : ""}
      </div>

      {isMobile ? (
        <>
          {chatContent}
          <Sheet
            open={!!selectedAnswer}
            onOpenChange={(open) => { if (!open) setSelectedAnswer(null); }}
          >
            <SheetContent side="bottom" className="h-[70vh]">
              <SheetHeader>
                <SheetTitle>Evidence</SheetTitle>
              </SheetHeader>
              <SourcePanel
                answer={selectedAnswer}
                highlightedSourceIndex={highlightedSource}
                className="h-full"
              />
            </SheetContent>
          </Sheet>
        </>
      ) : (
        <ResizablePanelGroup direction="horizontal" className="flex-1">
          <ResizablePanel defaultSize={60} minSize={40}>
            {chatContent}
          </ResizablePanel>
          <ResizableHandle withHandle />
          <ResizablePanel defaultSize={40} minSize={25}>
            <SourcePanel
              answer={selectedAnswer}
              highlightedSourceIndex={highlightedSource}
              className="h-full"
            />
          </ResizablePanel>
        </ResizablePanelGroup>
      )}
    </div>
  );
}

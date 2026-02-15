"use client";

/**
 * SourcePanel — Evidence and reasoning tabs.
 * Shows source snippets from the selected answer's citations.
 *
 * Source: DESIGN_SYSTEM §10.1, ARCHITECTURE Trust UX
 */

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, Brain } from "lucide-react";
import type { AnswerPacket } from "@/types/contracts";
import { PdfViewer } from "@/components/shared/pdf-viewer";
import { WhyAnswer } from "./why-answer";
import { cn } from "@/lib/utils";

interface SourcePanelProps {
  answer: AnswerPacket | null;
  highlightedSourceIndex?: number;
  className?: string;
}

export function SourcePanel({
  answer,
  highlightedSourceIndex,
  className,
}: SourcePanelProps) {
  if (!answer) {
    return (
      <div className={cn("flex h-full items-center justify-center p-6 text-muted-foreground", className)}>
        <p className="text-sm">Select an answer to view evidence</p>
      </div>
    );
  }

  return (
    <Tabs defaultValue="evidence" className={cn("flex h-full flex-col", className)}>
      <TabsList className="w-full justify-start rounded-none border-b bg-transparent px-4">
        <TabsTrigger value="evidence" className="gap-1.5">
          <FileText className="size-3.5" />
          Evidence ({answer.sources.length})
        </TabsTrigger>
        <TabsTrigger value="reasoning" className="gap-1.5">
          <Brain className="size-3.5" />
          Reasoning
        </TabsTrigger>
      </TabsList>

      <TabsContent value="evidence" className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="space-y-3 p-4">
            {answer.sources.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No source evidence available for this answer.
              </p>
            ) : (
              answer.sources.map((source, i) => (
                <Card
                  key={source.chunk_id}
                  className={cn(
                    "transition-colors",
                    highlightedSourceIndex === i && "ring-2 ring-primary"
                  )}
                >
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="font-mono text-xs">
                        {source.file_name}
                      </CardTitle>
                      <Badge variant="outline" className="font-mono text-xs">
                        {Math.round(source.score_final * 100)}%
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm leading-relaxed">{source.snippet}</p>
                    {source.file_name.toLowerCase().endsWith(".pdf") && (
                      <PdfViewer
                        className="mt-3"
                        title={source.file_name}
                        snippet={source.snippet}
                      />
                    )}
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </ScrollArea>
      </TabsContent>

      <TabsContent value="reasoning" className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="p-4">
            <WhyAnswer reasoning={answer.reasoning_chain} defaultOpen />
          </div>
        </ScrollArea>
      </TabsContent>
    </Tabs>
  );
}

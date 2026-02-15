"use client";

/**
 * AnswerCard — Renders an assistant answer with trust UX fields.
 * Shows confidence, verification, sources, and reasoning chain.
 *
 * Source: DESIGN_SYSTEM §10.1, ARCHITECTURE Trust UX §6.1
 */

import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ConfidenceBadge } from "@/components/shared/confidence-badge";
import { VerificationBadge } from "@/components/shared/verification-badge";
import { SourceCitation } from "@/components/shared/source-citation";
import { WhyAnswer } from "./why-answer";
import type { AnswerPacket } from "@/types/contracts";
import { shouldAbstain } from "@/lib/utils";
import { BRAND_COPY } from "@/lib/constants";
import { cn } from "@/lib/utils";

interface AnswerCardProps {
  content: string;
  answer?: AnswerPacket;
  isStreaming?: boolean;
  onSourceClick?: (index: number) => void;
  className?: string;
}

export function AnswerCard({
  content,
  answer,
  isStreaming = false,
  onSourceClick,
  className,
}: AnswerCardProps) {
  const isAbstention = answer && shouldAbstain(answer.confidence);

  return (
    <Card className={cn("space-y-3 border-0 bg-transparent p-0 shadow-none", className)}>
      {/* Answer text */}
      <div className="prose prose-sm dark:prose-invert max-w-none">
        <p className="whitespace-pre-wrap leading-relaxed">
          {isAbstention && !isStreaming
            ? BRAND_COPY.ABSTENTION
            : content}
          {isStreaming && (
            <span className="ml-1 inline-block size-2 animate-pulse rounded-full bg-primary" />
          )}
        </p>
      </div>

      {/* Trust fields — always visible when answer is available */}
      {answer && !isStreaming && (
        <div className="space-y-3">
          {/* Badges row */}
          <div className="flex flex-wrap items-center gap-2">
            <ConfidenceBadge
              level={answer.confidence}
              score={answer.confidence_score}
            />
            <VerificationBadge status={answer.verification} />
          </div>

          {/* Source citations */}
          {answer.sources.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {answer.sources.map((source, i) => (
                <SourceCitation
                  key={source.chunk_id}
                  index={i}
                  source={source}
                  onClick={() => onSourceClick?.(i)}
                />
              ))}
            </div>
          )}

          {/* Why this answer — reasoning chain */}
          <WhyAnswer reasoning={answer.reasoning_chain} />
        </div>
      )}

      {/* Loading skeleton when streaming but no answer yet */}
      {isStreaming && !content && (
        <div className="space-y-2">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-4 w-2/3" />
        </div>
      )}
    </Card>
  );
}

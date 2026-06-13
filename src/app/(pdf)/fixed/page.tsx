"use client";

import { CopilotChat, useAgent } from "@copilotkit/react-core/v2";
import { SiteNav } from "@/components/pdf-analyst/Brand";
import { SurfaceCanvas, CanvasEmptyState } from "@/components/pdf-analyst/SurfaceCanvas";
import { FilteredUserMessage } from "@/components/pdf-analyst/FilteredUserMessage";
import { FilteredAssistantMessage } from "@/components/pdf-analyst/FilteredAssistantMessage";
import { Split } from "@/components/pdf-analyst/Split";

const AGENT_ID = "fixed_agent";

export default function FixedPage() {
  const { agent: _agent } = useAgent({ agentId: AGENT_ID });

  return (
    <div className="h-screen flex flex-col bg-[var(--bg)]">
      <SiteNav active="fixed" />

      <div className="flex-1 min-h-0 flex">
        <Split
          persistKey="fixed.split"
          initialLeftFraction={0.32}
          left={
            <div className="h-full flex flex-col copilot-chat-wrapper">
              <div className="flex-1 min-h-0">
                <CopilotChat
                  agentId={AGENT_ID}
                  chatView={{
                    messageView: {
                      userMessage: FilteredUserMessage,
                      assistantMessage: FilteredAssistantMessage,
                    },
                  }}
                  labels={{
                    chatInputPlaceholder:
                      "Ask the concierge to research something and present it…",
                    welcomeMessageText:
                      "Ask me to research a topic. I’ll search with LinkUp, compose a cited A2UI surface, and return a safe presentation link.",
                  }}
                />
              </div>
            </div>
          }
          right={
            <SurfaceCanvas
              channel={AGENT_ID}
              emptyState={
                <CanvasEmptyState
                  title="Research canvas is empty"
                  subtitle="Ask the LinkUp concierge for a cited research brief. The A2UI surface will render here and can also be presented by link."
                  hint={
                    <span className="mono text-[11px] uppercase tracking-[0.14em] text-[var(--ink)]">
                      try: “Research agentic UI trends and present it.”
                    </span>
                  }
                />
              }
            />
          }
        />
      </div>
    </div>
  );
}

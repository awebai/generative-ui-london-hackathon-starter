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
                      "I’m the team concierge. Agent-authored text lives on the BYOT cert-auth server; ask me to research its topic and I’ll search LinkUp, compose a cited A2UI surface, and return a safe no-login presentation link.",
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
                  title="Team concierge canvas"
                  subtitle="Ask the concierge to validate a memo topic with live LinkUp sources. Cards, markdown, and source links render here before the safe /present link is minted."
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

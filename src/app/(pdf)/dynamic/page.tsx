"use client";

import { z } from "zod";
import { CopilotChat, useAgent, useRenderTool } from "@copilotkit/react-core/v2";
import { SiteNav } from "@/components/pdf-analyst/Brand";
import { SurfaceCanvas, CanvasEmptyState } from "@/components/pdf-analyst/SurfaceCanvas";
import { FilteredUserMessage } from "@/components/pdf-analyst/FilteredUserMessage";
import { FilteredAssistantMessage } from "@/components/pdf-analyst/FilteredAssistantMessage";
import { Split } from "@/components/pdf-analyst/Split";

const AGENT_ID = "dynamic_agent";

export default function DynamicPage() {
  const { agent: _agent } = useAgent({ agentId: AGENT_ID });

  useRenderTool({
    name: "linkup",
    parameters: z.any(),
    render: ({ status }) => {
      if (status === "complete") return <></>;
      return <ToolPill label="Searching the web with LinkUp…" />;
    },
  });

  useRenderTool({
    name: "render_research_surface",
    parameters: z.any(),
    render: ({ status }) => {
      if (status === "complete") return <></>;
      return <ToolPill label="Composing a cited A2UI surface…" />;
    },
  });

  return (
    <div className="h-screen flex flex-col bg-[var(--bg)]">
      <SiteNav active="dynamic" />

      <div className="flex-1 min-h-0 flex">
        <Split
          persistKey="dynamic.split"
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
                      "Ask for live web research and a presentation link…",
                    welcomeMessageText:
                      "I’m the team’s LinkUp concierge. Ask for research; I’ll search, cite sources, render A2UI, and present it to your human.",
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
                  subtitle="The concierge paints cited research surfaces here using the shared A2UI catalog, including markdown summaries and source links."
                  hint={
                    <span className="mono text-[11px] uppercase tracking-[0.14em] text-[var(--ink)]">
                      try: “Research LinkUp and CopilotKit, then present it.”
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

function ToolPill({ label }: { label: string }) {
  return (
    <div className="surface-soft px-3 py-2 my-1 flex items-center gap-3 text-[13px] text-[var(--ink-2)]">
      <span className="relative inline-flex h-2.5 w-2.5">
        <span className="absolute inline-flex h-full w-full rounded-full bg-[var(--lilac)] opacity-75 animate-ping" />
        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[var(--lilac)]" />
      </span>
      <span>{label}</span>
    </div>
  );
}

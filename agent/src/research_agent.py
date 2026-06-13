"""LinkUp research concierge agent.

The concierge is a cert-holding team member whose job is to research the live
web, compose a cited A2UI surface, and present it to the human via the genui
artifact/link server.
"""
from __future__ import annotations

import os
import uuid
from typing import Any, Sequence, TypedDict

from copilotkit import CopilotKitMiddleware, a2ui
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_linkup import LinkupSearchTool
from langgraph.checkpoint.memory import MemorySaver

from src.catalog import CATALOG_ID, CATALOG_PROMPT
from src.present import present_to_human

SURFACE_ID = "linkup-research"


class Source(TypedDict):
    title: str
    url: str
    snippet: str


OFFLINE_SOURCES: list[Source] = [
    {
        "title": "LinkUp documentation",
        "url": "https://docs.linkup.so/",
        "snippet": "LinkUp provides web and premium-source search for agent workflows.",
    },
    {
        "title": "CopilotKit A2UI renderer",
        "url": "https://docs.copilotkit.ai/",
        "snippet": "CopilotKit renders declarative A2UI surfaces in React applications.",
    },
    {
        "title": "AWID team-auth pattern",
        "url": "https://github.com/awebai",
        "snippet": "AWID team certificates let agents authenticate as team members.",
    },
]

OFFLINE_SUMMARY = """\
**Bottom line:** genui's concierge pattern lets a team member agent research the
live web, turn findings into a cited A2UI surface, and hand the human a safe
presentation link.

- LinkUp supplies the web research context.
- The concierge composes a catalog-backed A2UI surface, not ad-hoc HTML.
- `present_to_human` stores the artifact under team-auth and returns an expiring
  `/present/<token>` link.
"""


def _source_markdown(sources: Sequence[Source]) -> str:
    if not sources:
        return "No source links were returned."
    lines = []
    for index, source in enumerate(sources, start=1):
        title = source.get("title") or source.get("url") or f"Source {index}"
        url = source.get("url") or "#"
        snippet = source.get("snippet") or ""
        suffix = f" — {snippet}" if snippet else ""
        lines.append(f"{index}. [{title}]({url}){suffix}")
    return "\n".join(lines)


@tool()
def render_research_surface(
    title: str,
    summary_markdown: str,
    sources: list[Source],
) -> str:
    """Render a cited web-research answer as an A2UI surface.

    Args:
        title: Short title for the research answer.
        summary_markdown: Markdown answer with inline citations where useful.
        sources: Source links supporting the answer. Each source has title,
            url, and snippet.
    """

    components: list[dict[str, Any]] = [
        {
            "id": "root",
            "component": "Stack",
            "children": ["hero", "summary-section", "sources-section"],
            "gap": "lg",
        },
        {"id": "hero", "component": "Card", "tone": "lilac", "child": "hero-stack"},
        {
            "id": "hero-stack",
            "component": "Stack",
            "children": ["eyebrow", "heading", "intro", "proof-row"],
            "gap": "sm",
        },
        {"id": "eyebrow", "component": "Overline", "text": "LINKUP RESEARCH"},
        {"id": "heading", "component": "Heading", "text": title, "level": "1"},
        {
            "id": "intro",
            "component": "Text",
            "text": "A cited web-research brief composed by the team's concierge agent and stored as a safe presentation artifact.",
            "tone": "muted",
        },
        {
            "id": "proof-row",
            "component": "Row",
            "children": ["badge-live", "badge-cited", "badge-link"],
            "gap": "xs",
        },
        {"id": "badge-live", "component": "Badge", "label": "Live LinkUp search", "tone": "info"},
        {"id": "badge-cited", "component": "Badge", "label": "Cited markdown", "tone": "success"},
        {"id": "badge-link", "component": "Badge", "label": "No-login link", "tone": "neutral"},
        {
            "id": "summary-section",
            "component": "Section",
            "title": "Summary",
            "child": "summary-card",
        },
        {"id": "summary-card", "component": "Card", "child": "summary-markdown"},
        {"id": "summary-markdown", "component": "Markdown", "text": summary_markdown},
        {
            "id": "sources-section",
            "component": "Section",
            "title": "Sources",
            "child": "sources-card",
        },
        {"id": "sources-card", "component": "Card", "child": "sources-markdown"},
        {"id": "sources-markdown", "component": "Markdown", "text": _source_markdown(sources)},
    ]
    return a2ui.render(
        operations=[
            a2ui.create_surface(SURFACE_ID, catalog_id=CATALOG_ID),
            a2ui.update_components(SURFACE_ID, components),
            a2ui.update_data_model(
                SURFACE_ID,
                {
                    "title": title,
                    "summary_markdown": summary_markdown,
                    "sources": sources,
                },
            ),
        ]
    )


def _build_model() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=os.getenv("MODEL", "gemini-3.5-flash"),
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )


class OfflineResearchModel(BaseChatModel):
    """Offline fallback that still emits a real A2UI surface."""

    @property
    def _llm_type(self) -> str:
        return "offline-linkup-research-concierge"

    def bind_tools(self, tools: Any, **kwargs: Any) -> "OfflineResearchModel":
        return self

    def bind(self, **kwargs: Any) -> "OfflineResearchModel":
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        already_rendered = any(isinstance(m, ToolMessage) for m in messages)
        if already_rendered:
            message: BaseMessage = AIMessage(
                content="Offline mode — research concierge sample rendered."
            )
        else:
            message = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "render_research_surface",
                        "args": {
                            "title": "How genui presents cited research",
                            "summary_markdown": OFFLINE_SUMMARY,
                            "sources": OFFLINE_SOURCES,
                        },
                        "id": f"call_{uuid.uuid4().hex[:12]}",
                    }
                ],
            )
        return ChatResult(generations=[ChatGeneration(message=message)])


SYSTEM_PROMPT = f"""\
You are the team's LinkUp web-research concierge.

Your job on every user research request:
1. Call the `linkup` tool exactly once with a concise web-search query.
2. Read the returned answer and sources.
3. Call `render_research_surface` exactly once with:
   - a clear title,
   - a markdown summary with citations where useful,
   - source objects containing title, url, and snippet.
4. Call `present_to_human(surface_or_doc=<the exact JSON string returned by
   render_research_surface>)` exactly once.
5. Return only the safe URL from `present_to_human`.

Do not answer with prose instead of the URL. Do not invent sources. If LinkUp
returns sparse results, say so in the markdown summary and include the sources
that were returned.

Use this A2UI catalog; never invent component names:
{CATALOG_PROMPT}
"""


def build_research_agent():
    tools: list[Any] = [
        LinkupSearchTool(
            name="linkup",
            depth="standard",
            output_type="sourcedAnswer",
            max_results=5,
            include_inline_citations=True,
            include_sources=True,
        ),
        render_research_surface,
        present_to_human,
    ]
    if os.getenv("OFFLINE") == "1":
        return create_agent(
            model=OfflineResearchModel(),
            tools=[render_research_surface],
            system_prompt=SYSTEM_PROMPT,
            checkpointer=MemorySaver(),
        )
    return create_agent(
        model=_build_model(),
        tools=tools,
        middleware=[CopilotKitMiddleware()],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=MemorySaver(),
    )

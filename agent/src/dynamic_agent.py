"""Compatibility module for the dynamic concierge endpoint.

Both `/fixed` and `/dynamic` now serve the LinkUp research concierge; keeping
this module preserves the existing FastAPI/CopilotKit route imports.
"""
from __future__ import annotations

from src.research_agent import build_research_agent

graph = build_research_agent()

__all__ = ["graph"]

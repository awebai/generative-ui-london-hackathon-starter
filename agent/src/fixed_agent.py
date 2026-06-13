"""Compatibility module for the default concierge endpoint.

The starter used to expose a fixed-schema PDF dashboard agent here. genui now
uses the same LinkUp research concierge graph on the existing `/fixed` route so
old frontend wiring keeps working while the product behavior is research → cited
A2UI → present_to_human.
"""
from __future__ import annotations

from src.research_agent import build_research_agent, render_research_surface

graph = build_research_agent()

__all__ = ["graph", "render_research_surface"]

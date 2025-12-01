"""
Tools Package

Organized by provider:
- serper_tools: Serper.dev (search, places, news)
- tavily_tools: Tavily (deep search)
- serpapi_tools: SerpAPI (Google Flights, Hotels)
"""

# Serper.dev tools
from carribulus.tools.serper_tools import (
    serper_search,      # General search (buses, trains, etc.)
    serper_places,      # Google Places (attractions, restaurants)
    serper_news,        # News search (events, safety)
    SerperNewsTool,
)

# Tavily tools
from carribulus.tools.tavily_tools import (
    tavily_search,      # Deep search (comprehensive info)
)

# SerpAPI tools
from carribulus.tools.serpapi_tools import (
    serpapi_flights,    # Google Flights (precise pricing)
    serpapi_hotels,     # Google Hotels (precise pricing)
)

__all__ = [
    # Serper
    "serper_search",
    "serper_places",
    "serper_news",
    "SerperNewsTool",
    # Tavily
    "tavily_search",
    # SerpAPI
    "serpapi_flights",
    "serpapi_hotels",
]

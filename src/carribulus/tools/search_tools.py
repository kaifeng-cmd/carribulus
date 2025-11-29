"""
Search Tools Configuration
https://docs.crewai.com/concepts/tools
"""
from crewai_tools import SerperDevTool, TavilySearchTool

# =============================================================================
# Serper - Google Search API
# Best for: Real-time search, prices, availability
# https://serper.dev/
# =============================================================================
serper_tool = SerperDevTool()

# =============================================================================
# Tavily - AI-optimized Search
# Best for: Deep research, comprehensive info
# https://tavily.com/
# =============================================================================
tavily_tool = TavilySearchTool(
    search_depth='advanced',
    max_results=10
)

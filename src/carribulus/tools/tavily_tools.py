"""
Tavily Search Tools
https://tavily.com/
https://docs.crewai.com/en/tools/search-research/tavilysearchtool

Tavily is best for:
- Deep search and comprehensive information gathering
- Getting curated, relevant content
- Academic and in-depth queries
"""
from crewai_tools import TavilySearchTool


# Deep search for comprehensive local information
tavily_search = TavilySearchTool(
    search_depth="advanced",  # More thorough search
    max_results=10,
)

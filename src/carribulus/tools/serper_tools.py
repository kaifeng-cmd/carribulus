"""
Serper.dev Tools - Google Search API wrapper
https://serper.dev/
https://docs.crewai.com/en/tools/search-research/serperdevtool

Tools:
- serper_search: General web search (for flights, hotels, general info)
- serper_places: Google Places search (for attractions, restaurants, locations)
- SerperNewsTool: Custom news search with date range (for events, safety alerts)
"""
from crewai_tools import SerperDevTool
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import requests
import json
import os


# CrewAI Built-in Serper Tools
# =============================================================================

# General web search - for transportation (exclude flights)
serper_search = SerperDevTool(
    n_results=10,
    country="my",  # Malaysia perspective
)

# Google Places search - for attractions, restaurants, landmarks
serper_places = SerperDevTool(
    search_url="https://google.serper.dev/places",
    n_results=10,
    country="my",  # Malaysia perspective
)


# Custom Serper News Tool (with date range support)
# =============================================================================

class NewsSearchInput(BaseModel):
    """Input schema for news search"""
    query: str = Field(..., description="The search query for news")
    search_type: str = Field(
        default="events",
        description="Type of news: 'events' for local events/festivals, 'safety' for weather/disasters/warnings"
    )

class SerperNewsTool(BaseTool):
    """
    Custom Serper News Tool with past month date range.
    
    Use cases:
    - Local events, festivals, exhibitions
    - Weather warnings, natural disasters
    - Safety alerts, travel advisories
    """
    name: str = "Serper News Search"
    description: str = """
        Search for recent news about a destination. Use this tool when you need:
        - Local events, festivals, concerts, exhibitions happening soon
        - Weather conditions and forecasts
        - Natural disaster warnings (earthquakes, typhoons, floods)
        - Safety alerts and travel advisories
        - Political situations or protests
        
        Input should describe what news you're looking for and the location.
        Example: "Tokyo events and festivals" or "Thailand weather warnings"
    """
    args_schema: type[BaseModel] = NewsSearchInput
    
    def _run(self, query: str, search_type: str = "events") -> str:
        """Execute news search with past month filter"""
        
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            return "Error: SERPER_API_KEY not found in environment variables"
        
        url = "https://google.serper.dev/news"
        
        # Build search query based on type
        if search_type == "safety":
            enhanced_query = f"{query} (weather OR disaster OR warning OR advisory OR safety OR earthquake OR typhoon OR flood)"
        else:  # events
            enhanced_query = f"{query} (events OR festival OR concert OR exhibition OR celebration)"
        
        payload = json.dumps({
            "q": enhanced_query,
            "gl": "my",  # Malaysia perspective
            "tbs": "qdr:m",  # Past month
            "num": 10
        })
        
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, headers=headers, data=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            news_items = data.get("news", [])
            
            if not news_items:
                return f"No recent news found for: {query}"
            
            # Format results
            results = []
            results.append(f"## Recent News: {query}\n")
            results.append(f"*Search type: {search_type} | Past month*\n")
            
            for i, item in enumerate(news_items[:8], 1):
                title = item.get("title", "No title")
                snippet = item.get("snippet", "No description")
                source = item.get("source", "Unknown")
                date = item.get("date", "Unknown date")
                link = item.get("link", "")
                
                results.append(f"### {i}. {title}")
                results.append(f"Source: {source} | Date: {date}")
                results.append(f"{snippet}")
                if link:
                    results.append(f"{link}")
                results.append("")
            
            return "\n".join(results)
            
        except requests.exceptions.RequestException as e:
            return f"Error searching news: {str(e)}"
        except json.JSONDecodeError:
            return "Error: Invalid response from Serper API"

# Create tool instances
serper_news = SerperNewsTool()

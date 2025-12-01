"""
SerpAPI Tools - Google Flights & Hotels
https://serpapi.com/

Provides precise pricing for:
- Flights (Google Flights)
- Hotels (Google Hotels)
"""

import os
import requests
from typing import Optional, Type, Literal
from pydantic import BaseModel, Field
from crewai.tools import BaseTool


# Input Schemas with Validation
# =============================================================================

class FlightSearchInput(BaseModel):
    """Input schema for flight search with full validation"""
    departure_id: str = Field(
        required=True,
        description="Departure airport IATA code. Common codes: KUL (Kuala Lumpur), BKK (Bangkok), NRT/HND (Tokyo), ICN (Seoul), HKG (Hong Kong)"
    )
    arrival_id: str = Field(
        required=True,
        description="Arrival airport IATA code. Same format as departure_id."
    )
    outbound_date: str = Field(
        required=True,
        description="Departure date in YYYY-MM-DD format (e.g., '2025-11-15')"
    )
    return_date: Optional[str] = Field(
        default=None,
        description="Return date in YYYY-MM-DD format. Leave empty for one-way trip."
    )
    adults: int = Field(
        default=1,
        ge=1,
        le=30,
        description="Number of adult passengers (1-30)"
    )
    children: int = Field(
        default=0,
        ge=0,
        le=10,
        description="Number of children (0-10)"
    )
    travel_class: Literal[1, 2, 3, 4] = Field(
        default=1,
        description="Travel class: 1=Economy, 2=Premium Economy, 3=Business, 4=First Class"
    )
    stops: Literal[0, 1, 2, 3] = Field(
        default=0,
        description="Maximum stops: 0=Any number of stops, 1=Nonstop only, 2=1 stop or fewer, 3=2 stops or fewer"
    )
    currency: str = Field(
        default="MYR",
        description="Currency code for prices. Default is MYR (Malaysian Ringgit). Common: USD, THB, JPY"
    )


class HotelSearchInput(BaseModel):
    """Input schema for hotel search with full validation"""
    query: str = Field(
        required=True,
        description="Hotel search query. Be specific with location (e.g., 'hotels in Tokyo Shinjuku', 'budget hotels near Seoul Station', 'luxury resorts in Bali Seminyak')"
    )
    check_in_date: str = Field(
        required=True,
        description="Check-in date in YYYY-MM-DD format"
    )
    check_out_date: str = Field(
        required=True,
        description="Check-out date in YYYY-MM-DD format"
    )
    adults: int = Field(
        default=1,
        ge=1,
        le=30,
        description="Number of adult guests"
    )
    children: int = Field(
        default=0,
        ge=0,
        le=10,
        description="Number of children (0-10)"
    )
    min_price: Optional[int] = Field(
        default=None,
        ge=0,
        description="Minimum price per night in specified currency. Leave empty for no minimum."
    )
    max_price: Optional[int] = Field(
        default=None,
        ge=0,
        description="Maximum price per night in specified currency. Leave empty for no maximum."
    )
    hotel_class: Optional[str] = Field(
        default=None,
        description="Hotel star rating filter (2-5 only). Ex: '3' for 3-star only, '4,5' for 4 and 5 star, '2,3,4' for 2-4 star"
    )
    currency: str = Field(
        default="MYR",
        description="Currency code for prices. Default is MYR. Common: USD, THB, JPY"
    )
    sort_by: Literal[3, 8, 13] = Field(
        default=8,
        description="Sort results by: 3=Lowest price, 8=Highest rating (default), 13=Most reviewed"
    )


# Flight Search Tool
# =============================================================================

class SerpAPIFlightsTool(BaseTool):
    """
    Search Google Flights for precise flight prices and schedules.
    
    Returns real-time pricing from Google Flights including:
    - Multiple airlines comparison
    - Departure/arrival times
    - Flight duration and stops
    - Prices in user's preferred currency
    """
    name: str = "Google Flights Search"
    description: str = """Search for flight prices and schedules using Google Flights.
    
    USE THIS TOOL WHEN user asks about:
    - Flight prices between cities (e.g., "flights from KL to Tokyo")
    - Comparing airlines and prices
    - Round-trip or one-way flights
    - Specific travel dates
    - Business/first class options

    IMPORTANT: 
    - You need airport IATA codes (KUL, NRT, SIN, etc.)
    - If user says city name, convert to airport code
    - Default is economy class, MYR currency
    - If user mentions "business class" → travel_class=3
    - If user mentions "direct flight only" → stops=0

    Examples of airport codes:
    - Malaysia: KUL (KLIA), PEN (Penang)
    - Thailand: BKK (Bangkok), CNX (Chiang Mai)
    - Japan: NRT (Tokyo Narita), KIX (Osaka)
    - Vietnam: SGN (Ho Chi Minh)
    """
    args_schema: Type[BaseModel] = FlightSearchInput
    
    def _run(
        self,
        departure_id: str,
        arrival_id: str,
        outbound_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        travel_class: int = 1,
        stops: int = 0,
        currency: str = "MYR"
    ) -> str:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "Error: SERPAPI_API_KEY not found. Please add it to your .env file."
        
        # Build request parameters
        params = {
            "api_key": api_key,
            "engine": "google_flights", # Google Flights
            "departure_id": departure_id.upper().strip(),
            "arrival_id": arrival_id.upper().strip(),
            "outbound_date": outbound_date,
            "currency": currency.upper(),
            "hl": "en",
            "adults": adults,
            "children": children,
            "travel_class": travel_class,
        }
        
        # Add stops filter
        if stops < 3:
            params["stops"] = str(stops)
        
        # Determine trip type
        if return_date:
            params["return_date"] = return_date
            params["type"] = "1"  # Round trip
            trip_type = "Round-trip"
        else:
            params["type"] = "2"  # One way
            trip_type = "One-way"
        
        try:
            response = requests.get(
                "https://serpapi.com/search",
                params=params,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            
            # Check for errors
            if "error" in data:
                return f"API Error: {data['error']}"
            
            return self._format_flight_results(
                data, 
                departure_id.upper(), 
                arrival_id.upper(),
                trip_type,
                currency.upper(),
                travel_class
            )
            
        except requests.exceptions.Timeout:
            return "Error: Request timed out. Please try again."
        except requests.exceptions.RequestException as e:
            return f"Error searching flights: {str(e)}"
    
    def _format_flight_results(
        self, 
        data: dict, 
        departure: str, 
        arrival: str,
        trip_type: str,
        currency: str,
        travel_class: int
    ) -> str:
        """Format flight results into readable Markdown"""
        
        class_names = {1: "Economy", 2: "Premium Economy", 3: "Business", 4: "First Class"}
        class_name = class_names.get(travel_class, "Economy")
        
        results = []
        results.append(f"## ✈️ Flights: {departure} → {arrival}")
        results.append(f"{trip_type} | {class_name} | Prices in {currency}\n")
        
        # Price insights
        if "price_insights" in data:
            insights = data["price_insights"]
            results.append("### 💡 Price Insights")
            if "lowest_price" in insights:
                results.append(f"- **Lowest price:** {currency} {insights['lowest_price']}")
            if "typical_price_range" in insights:
                low, high = insights["typical_price_range"]
                results.append(f"- **Typical range:** {currency} {low} - {high}")
            if "price_level" in insights:
                results.append(f"- **Current prices:** {insights['price_level']}")
            results.append("")
        
        # Best flights
        best_flights = data.get("best_flights", [])
        if best_flights:
            results.append("### Best Flights\n")
            results.append("| # | Airline | Route | Duration | Stops | Price |")
            results.append("|---|---------|-------|----------|-------|-------|")
            
            for i, flight in enumerate(best_flights[:5], 1):
                row = self._format_flight_row(i, flight, currency)
                results.append(row)
            results.append("")
        
        # Other options
        other_flights = data.get("other_flights", [])
        if other_flights:
            results.append("### More Options\n")
            results.append("| # | Airline | Route | Duration | Stops | Price |")
            results.append("|---|---------|-------|----------|-------|-------|")
            
            for i, flight in enumerate(other_flights[:5], 1):
                row = self._format_flight_row(i + len(best_flights), flight, currency)
                results.append(row)
            results.append("")
        
        if not best_flights and not other_flights:
            results.append("❌ No flights found for this route and date.")
            results.append("Try different dates or check airport codes.")
        
        return "\n".join(results)
    
    def _format_flight_row(self, index: int, flight_data: dict, currency: str) -> str:
        """Format a single flight as table row"""
        price = flight_data.get("price", "N/A")
        total_duration = flight_data.get("total_duration", 0)
        hours = total_duration // 60
        mins = total_duration % 60
        duration_str = f"{hours}h {mins}m"
        
        flights = flight_data.get("flights", [])
        stops = len(flights) - 1
        stops_str = "Direct" if stops == 0 else f"{stops} stop{'s' if stops > 1 else ''}"
        
        # Get airline and route info
        if flights:
            first_leg = flights[0]
            last_leg = flights[-1]
            airline = first_leg.get("airline", "Unknown")
            dep_time = first_leg.get("departure_airport", {}).get("time", "")
            arr_time = last_leg.get("arrival_airport", {}).get("time", "")
            route = f"{dep_time} → {arr_time}"
        else:
            airline = "Unknown"
            route = "N/A"
        
        return f"| {index} | {airline} | {route} | {duration_str} | {stops_str} | {currency} {price} |"


# Hotel Search Tool
# =============================================================================

class SerpAPIHotelsTool(BaseTool):
    """
    Search Google Hotels for precise hotel prices and ratings.
    
    Returns real-time pricing from Google Hotels including:
    - Hotel names and star ratings
    - Price per night and total
    - Guest ratings and reviews
    - Amenities
    """
    name: str = "Google Hotels Search"
    description: str = """Search for hotel prices and availability using Google Hotels.

    USE THIS TOOL WHEN user asks about:
    - Hotel recommendations in a city/area
    - Hotel prices for specific dates
    - Budget or luxury accommodations
    - Hotels near landmarks

    IMPORTANT:
    - Be specific with location in query
    - Always NEED check-in and check-out dates
    - If user mentions "budget" → consider max_price
    - If user mentions "luxury/5-star" → hotel_class="5"

    Examples of good queries:
    - "hotels in Tokyo Shinjuku"
    - "budget hotels near Seoul Station" 
    - "luxury resorts in Bali Seminyak"
    - "family hotels near Disneyland Tokyo"
    """
    args_schema: Type[BaseModel] = HotelSearchInput
    
    def _run(
        self,
        query: str,
        check_in_date: str,
        check_out_date: str,
        adults: int = 1,
        children: int = 0,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        hotel_class: Optional[str] = None,
        currency: str = "MYR",
        sort_by: int = 8
    ) -> str:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "Error: SERPAPI_API_KEY not found. Please add it to your .env file."
        
        # Build request parameters
        params = {
            "api_key": api_key,
            "engine": "google_hotels", # Google Hotels
            "q": query,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "currency": currency.upper(),
            "hl": "en",
            "gl": "my",  # Malaysia perspective
            "adults": adults,
            "children": children,
            "sort_by": str(sort_by),
        }
        
        # Optional filters
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price
        if hotel_class:
            params["hotel_class"] = hotel_class
        
        try:
            response = requests.get(
                "https://serpapi.com/search",
                params=params,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            
            if "error" in data:
                return f"API Error: {data['error']}"
            
            return self._format_hotel_results(
                data, 
                query, 
                check_in_date, 
                check_out_date,
                currency.upper()
            )
            
        except requests.exceptions.Timeout:
            return "Error: Request timed out. Please try again."
        except requests.exceptions.RequestException as e:
            return f"Error searching hotels: {str(e)}"
    
    def _format_hotel_results(
        self, 
        data: dict, 
        query: str,
        check_in: str,
        check_out: str,
        currency: str
    ) -> str:
        """Format hotel results into readable Markdown"""
        results = []
        results.append(f"## 🏨 Hotels: {query}")
        results.append(f"Check-in: {check_in} | Check-out: {check_out} | Prices in {currency}\n")
        
        properties = data.get("properties", [])
        
        if not properties:
            results.append("❌ No hotels found for this search.")
            results.append("Try different dates or broaden your location.")
            return "\n".join(results)
        
        # Summary table
        results.append("| # | Hotel | Rating | Price/Night | Total | Amenities |")
        results.append("|---|-------|--------|-------------|-------|-----------|")
        
        for i, hotel in enumerate(properties[:10], 1):
            name = hotel.get("name", "Unknown Hotel")
            # Truncate long names
            if len(name) > 30:
                name = name[:27] + "..."
            
            rating = hotel.get("overall_rating", "N/A")
            reviews = hotel.get("reviews", 0)
            rating_str = f"⭐{rating} ({reviews:,})" if rating != "N/A" else "N/A"
            
            # Price info
            rate = hotel.get("rate_per_night", {})
            price_per_night = rate.get("lowest", "N/A")
            
            total = hotel.get("total_rate", {})
            total_price = total.get("lowest", "N/A")
            
            # Amenities (first 3)
            amenities = hotel.get("amenities", [])[:3]
            amenities_str = ", ".join(amenities) if amenities else "-"
            if len(amenities_str) > 25:
                amenities_str = amenities_str[:22] + "..."
            
            results.append(f"| {i} | {name} | {rating_str} | {price_per_night} | {total_price} | {amenities_str} |")
        
        results.append("")
        
        # Detailed info for top 3
        results.append("### Top Recommendations\n")
        for i, hotel in enumerate(properties[:3], 1):
            name = hotel.get("name", "Unknown Hotel")
            hotel_type = hotel.get("type", "Hotel")
            rating = hotel.get("overall_rating", "N/A")
            reviews = hotel.get("reviews", 0)
            
            rate = hotel.get("rate_per_night", {})
            price = rate.get("lowest", "N/A")
            
            amenities = hotel.get("amenities", [])
            
            results.append(f"**{i}. {name}** ({hotel_type})")
            results.append(f"- ⭐ Rating: {rating}/5 from {reviews:,} reviews")
            results.append(f"- 💰 Price: {price}/night")
            if amenities:
                results.append(f"- 🏷️ Amenities: {', '.join(amenities[:5])}")
            
            link = hotel.get("link", "")
            if link:
                results.append(f"- [View & Book]({link})")
            
            results.append("")
        
        return "\n".join(results)


# Tool Instances
# =============================================================================

serpapi_flights = SerpAPIFlightsTool()
serpapi_hotels = SerpAPIHotelsTool()

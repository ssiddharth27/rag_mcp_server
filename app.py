import streamlit as st
import os
import json
import requests
import datetime
from typing import Type
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool
from langchain_groq import ChatGroq
from amadeus import Client
# ==============================================================================
# 1. DEVELOPER KEYS (HARDCODED FOR DEPLOYMENT)
# ==============================================================================

AIRLINE_MAP = {
   "AI": "Air India", "UK": "Vistara", "6E": "IndiGo", "QP": "Akasa Air", "SG": "SpiceJet",
   "QR": "Qatar Airways", "EK": "Emirates", "EY": "Etihad", "BA": "British Airways",
   "LH": "Lufthansa", "AF": "Air France", "KL": "KLM", "VS": "Virgin Atlantic",
   "UA": "United Airlines", "AA": "American Airlines", "DL": "Delta", "SQ": "Singapore Airlines",
   "CX": "Cathay Pacific", "JL": "Japan Airlines", "NH": "All Nippon Airways (ANA)",
   "MH": "Malaysia Airlines", "TG": "Thai Airways", "TK": "Turkish Airlines"
}
def get_airline_name(code):
   return AIRLINE_MAP.get(code, code)
def get_booking_link(origin, dest, date):
   # Generates a standard Skyscanner search link
   return f"https://www.skyscanner.co.in/transport/flights/{origin.lower()}/{dest.lower()}/{date.replace('-', '')[2:]}"

# ==============================================================================
# 2. UI STYLING
# ==============================================================================
st.set_page_config(page_title="NomadAI | Travel Planner", page_icon="🌍", layout="wide")
st.markdown("""
<style>
   .stApp { background: linear-gradient(to right, #0f2027, #203a43, #2c5364); color: white; }
   .stTextInput>div>div>input, .stNumberInput>div>div>input {
       background-color: rgba(255, 255, 255, 0.1); color: white; border: 1px solid #555;
   }
   .stButton>button {
       background: linear-gradient(45deg, #00d2ff, #3a7bd5); color: white; border: none;
       padding: 0.8rem 2rem; border-radius: 25px; font-weight: bold; width: 100%;
   }
   /* Fix for the deprecated warning yellow box */
   .stAlert { display: none; }
</style>
""", unsafe_allow_html=True)
# ==============================================================================
# 3. ADVANCED TOOLS
# ==============================================================================
# --- Image Tool (With Robust Fallback) ---
class ImageSearchInput(BaseModel):
   query: str = Field(..., description="Query for image (e.g., 'Eiffel Tower').")
class ImageSearchTool(BaseTool):
   name: str = "image_search_tool"
   description: str = "Finds a real image URL. Use this to EMBED images in your report."
   args_schema: Type[BaseModel] = ImageSearchInput
   def _run(self, query: str) -> str:
       try:
           # 1. Try Real Google Image
           url = "https://google.serper.dev/images"
           payload = json.dumps({"q": query, "num": 1})
           headers = {'X-API-KEY': os.environ.get("SERPER_KEY"), 'Content-Type': 'application/json'}
           if headers['X-API-KEY']:
               response = requests.request("POST", url, headers=headers, data=payload)
               data = response.json()
               if 'images' in data and len(data['images']) > 0:
                   return data['images'][0]['imageUrl']
       except:
           pass
       # 2. Fallback to AI Generation (Never fails)
       return f"https://image.pollinations.ai/prompt/{query}?width=800&height=500&nologo=true"
# --- Detailed Flight Tool ---
class FlightInput(BaseModel):
   origin: str = Field(..., description="Origin IATA code.")
   destination: str = Field(..., description="Destination IATA code.")
   date: str = Field(..., description="YYYY-MM-DD.")
class FlightSearchTool(BaseTool):
   name: str = "flight_search_tool"
   description: str = "Searches flights with departure/arrival times."
   args_schema: Type[BaseModel] = FlightInput
   def _run(self, origin: str, destination: str, date: str) -> str:
       try:
           amadeus = Client(
               client_id=os.environ.get("AMADEUS_KEY"),
               client_secret=os.environ.get("AMADEUS_SECRET")
           )
           response = amadeus.shopping.flight_offers_search.get(
               originLocationCode=origin, destinationLocationCode=destination,
               departureDate=date, adults=1, max=5, currencyCode='INR'
           )
           results = []
           link = get_booking_link(origin, destination, date)
           for offer in response.data:
               price = offer['price']['total']
               airline = offer['validatingAirlineCodes'][0]
               name = get_airline_name(airline)
               # Extract detailed timings
               segments = offer['itineraries'][0]['segments']
               departure = segments[0]['departure']['at'].split('T')[1][:5] # HH:MM
               arrival = segments[-1]['arrival']['at'].split('T')[1][:5]    # HH:MM
               duration = offer['itineraries'][0]['duration'][2:] # Remove 'PT'
               
               results.append(f"✈️**{name}** ({airline}) | ₹{price} | Dep: {departure} -> Arr: {arrival} ({duration}) | Link:{link}")
           return "\n".join(results) if results else "No flights found."
       except Exception as e:
           return f"Flight Error: {str(e)}"
# --- Web Search Tool ---
class WebSearchInput(BaseModel):
   query: str = Field(..., description="Query.")
class WebSearchTool(BaseTool):
   name: str = "web_search_tool"
   description: str = "Searches Google for info."
   args_schema: Type[BaseModel] = WebSearchInput
   def _run(self, query: str) -> str:
       try:
           url = "https://google.serper.dev/search"
           payload = json.dumps({"q": query, "num": 3})
           headers = {'X-API-KEY': os.environ.get("SERPER_KEY"), 'Content-Type': 'application/json'}
           response = requests.request("POST", url, headers=headers, data=payload)
           return response.text
       except:
           return "Search failed."
# ==============================================================================
# 4. APP LOGIC
# ==============================================================================

st.title("🌍 NomadAI: Travel Planner")
# Inputs
c1, c2, c3, c4 = st.columns(4)
with c1: origin = st.text_input("From (IATA)", value="DEL")
with c2: destination = st.text_input("To (City)", value="New York")
with c3: days = st.number_input("Days", 1, 30, 5)
with c4: start_date = st.date_input("Date", min_value=datetime.date.today())
c5, c6 = st.columns(2)
# FIX: Changed Budget to Exact Price
with c5: total_budget = st.number_input("Total Budget (INR)", min_value=10000, value=200000, step=10000)
with c6: vibe = st.selectbox("Vibe", ["Luxury & Comfort", "Budget & Backpacking", "Adventure", "Foodie"])
if st.button("🚀 Plan Trip"):
   if not os.environ.get("GROQ_API_KEY"):
       st.error("Please add API Keys in the sidebar.")
   else:
       # 1. Hero Images (UI Only)
       st.markdown("---")
       with st.spinner("Fetching preview..."):
           hero = ImageSearchTool()._run(f"Best tourist spot in {destination}")
           # FIX: Used use_container_width to remove yellow warning
           st.image(hero, caption=f"Welcome to {destination}", use_container_width=True)
       # 2. Agents
       llm_model1 = LLM(model = "groq/openai/gpt-oss-120b",
             temperature = 0.7,
             api_key = os.environ["GROQ_API_KEY"] 
            )
       agent_flights = Agent(
           role='Flight Expert',
           goal='Find detailed flight options.',
           backstory='You provide precise flight times and prices.',
           tools=[FlightSearchTool()],
           llm=llm_model1, verbose=True
       )
       agent_planner = Agent(
           role='Visual Travel Blogger',
           goal='Create a visual itinerary with embedded images.',
           backstory="""You are a travel blogger.
           1. You MUST use the 'image_search_tool' to find photos of recommended hotels and food.
           2. You MUST embed them in the markdown like this: ![Alt Text](image_url).
           3. Do not just list text; make it look like a magazine article.""",
           tools=[WebSearchTool(), ImageSearchTool()], # Camera Tool Given
           llm=llm_model1, verbose=True
       )
       # Tasks
       task1 = Task(
           description=f"Find flights {origin}->{destination} on {start_date}. Get Dep/Arr times and Price in INR.",
           expected_output="List of flights with details.",
           agent=agent_flights
       )
       task2 = Task(
           description=f"""
           Create a {days}-day Visual Itinerary for {destination}. Budget: ₹{total_budget}.
           FORMAT:
           # ✈️ Flight Options
           (List the flights found by the Flight Expert with Times & Prices)
           # 🏨 Where to Stay (Budget: Approx ₹{total_budget*0.4} total)
           (Find 3 hotels. For each, EMBED A PHOTO using ![Hotel](url))
           - **Hotel Name**: Price per night...
           # 🗺️ Day-by-Day Plan
           ## Day 1...
           (Embed a photo of the main activity)
           # 🍛 Food
           (Recommend 3 dishes with EMBEDDED PHOTOS)
           """,
           agent=agent_planner,
           context=[task1],
           expected_output="Markdown itinerary with embedded images.",
       )
       crew = Crew(agents=[agent_flights, agent_planner], tasks=[task1, task2], process=Process.sequential)
       result = crew.kickoff()
       st.markdown("---")
       st.markdown(result)

import ssl
import hashlib
ssl._create_default_https_context = ssl._create_unverified_context

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON
import json
import os
import time
from fastapi import Request

app = FastAPI()

GLOBAL_DATA = {
    "graph": {"nodes": [], "links": []},
    "map": [],
    "books": []
}

# --- CONFIGURATION ---
CACHE_DIR = "cache"
# Create cache directory if it doesn't exist
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MAPPINGS
REGION_MAP = {
    "Global (Random)": None,
    "Romania": "wd:Q218",
    "France": "wd:Q142",
    "United Kingdom": "wd:Q145",
    "United States": "wd:Q30",
    "Germany": "wd:Q183",
    "Japan": "wd:Q17",
    "Russia": "wd:Q159"
}

# MAPPING: User Selection -> List of Top Q-IDs from your data
# backend/server.py

GENRE_MAP = {
    "All Types": None,
    
    # Key matches Frontend "Poetry"
    "Poetry": "wd:Q482 wd:Q3236984 wd:Q7561196 wd:Q16933953 wd:Q182357 wd:Q474090",
    
    # Key matches Frontend "Science Fiction"
    "Science Fiction": "wd:Q24925 wd:Q132311 wd:Q193606 wd:Q9326077 wd:Q326439 wd:Q1188977",
    
    # Key matches Frontend "Non-fiction"
    "Non-fiction": "wd:Q213051 wd:Q35760 wd:Q27801 wd:Q384515 wd:Q30277550",
    
    # Key matches Frontend "Biography"
    "Biography": "wd:Q36279 wd:Q4184 wd:Q112983 wd:Q185598 wd:Q1787111",
    
    # Key matches Frontend "Novel"
    "Novel": "wd:Q8261 wd:Q8253 wd:Q676 wd:Q12799318",
    
    # Key matches Frontend "Play (Drama)"
    "Play (Drama)": "wd:Q25379 wd:Q40831 wd:Q80930 wd:Q17172848 wd:Q21010853",
    
    # Key matches Frontend "Children's Literature"
    "Children's Literature": "wd:Q131539 wd:Q11163999 wd:Q699 wd:Q24723",
    
    # Key matches Frontend "Comics"
    "Comics": "wd:Q1004"
}

current_data = {"graph": {"nodes": [], "links": []}, "map": [], "books": []}

# --- HELPER: CACHE MANAGER ---
# 1. UPDATE CACHE FILENAME TO INCLUDE DATES
def get_cache_filename(region_id, genre_id, start_year, end_year):
    # Clean Region
    r_part = region_id.split(":")[-1] if region_id else "global"
    
    # Clean Genre (Hash if long)
    if genre_id and " " in genre_id:
        import hashlib
        g_part = f"group_{hashlib.md5(genre_id.encode()).hexdigest()[:6]}"
    else:
        g_part = genre_id.split(":")[-1] if genre_id else "all"

    # Add Years to filename
    return os.path.join(CACHE_DIR, f"data_{r_part}_{g_part}_{start_year}_{end_year}.json")

def load_from_cache(filename):
    """Reads JSON from local disk"""
    with open(filename, "r") as f:
        print(f"⚡ CACHE HIT: Loading {filename} instantly.")
        return json.load(f)

def save_to_cache(filename, data):
    """Saves JSON to local disk"""
    with open(filename, "w") as f:
        json.dump(data, f)
    print(f"💾 CACHE SAVED: Wrote data to {filename}.")

# --- PIPELINE LOGIC ---

# backend/server.py

def run_pipeline(region_id=None, genre_id=None, start_year=1800, end_year=2024, force_refresh=False):
    filename = get_cache_filename(region_id, genre_id, start_year, end_year)
    
    # 1. CHECK CACHE
    if not force_refresh and os.path.exists(filename):
        return load_from_cache(filename)

    print(f"🚀 FETCHING LIVE: {start_year}-{end_year}, Region={region_id}...")
    
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.addCustomHttpHeader("User-Agent", "LiteraryAtlas/TimeTravel (student_project)")
    sparql.setReturnFormat(JSON)
    sparql.setTimeout(60)
    
    # 2. QUERY BUILDER
    region_clause = f"?author wdt:P27 {region_id}." if region_id else ""
    
    genre_clause = ""
    if genre_id:
        genre_clause = f"""
        VALUES ?targetGenre {{ {genre_id} }}
        ?book wdt:P136 ?targetGenre.
        """

    query = f"""
    SELECT DISTINCT ?book ?bookLabel ?authorLabel ?birthplaceLabel ?coord ?genreLabel ?year WHERE {{
      
      # MAIN SELECT: Find 150 matching items (Increased limit for better map results)
      {{
        SELECT DISTINCT ?book ?author ?genreLabel ?year WHERE {{
          
          # Filters
          {genre_clause}
          {region_clause}

          # Big Data Definition
          VALUES ?type {{ wd:Q571 wd:Q7725634 wd:Q47461344 }}
          ?book wdt:P31 ?type;
                wdt:P50 ?author;
                wdt:P577 ?pubDate.  # Publication Date

          # Date Filter
          BIND(YEAR(?pubDate) AS ?year)
          FILTER(?year >= {start_year} && ?year <= {end_year})
                
        }} LIMIT 150
      }}

      # DETAILS
      OPTIONAL {{ ?author wdt:P19 ?birthplace. ?birthplace wdt:P625 ?coord. }}
      OPTIONAL {{ ?book wdt:P136 ?genre. }}
      
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,fr,de,ro,it,es". }}
    }}
    """
    
    sparql.setQuery(query)
    
    try:
        results = sparql.query().convert()
    except Exception as e:
        print(f"❌ SPARQL Error: {e}")
        return {"graph": {"nodes": [], "links": []}, "map": [], "books": []}

    # 3. DATA PROCESSING
    raw_data = []
    for item in results["results"]["bindings"]:
        title = item.get("bookLabel", {}).get("value", "Unknown")
        # Basic filter for "junk" titles (Q-IDs)
        if title.startswith("wd:") or (title.startswith("Q") and title[1].isdigit()): continue

        raw_data.append({
            "book_id": item.get("book", {}).get("value"),
            "title": title,
            "author": item.get("authorLabel", {}).get("value", "Unknown"),
            "location": item.get("birthplaceLabel", {}).get("value"),
            "coordinates": item.get("coord", {}).get("value"), # Can be None
            "genre": item.get("genreLabel", {}).get("value"),
            "year": item.get("year", {}).get("value")
        })

    if not raw_data:
        print("⚠️ No results found.")
        return {"graph": {"nodes": [], "links": []}, "map": [], "books": []}

    # 4. DATAFRAME CLEANING
    df = pd.DataFrame(raw_data)
    
    # Group by Book to handle multiple authors/genres
    clean_df = df.groupby(['book_id', 'title']).agg({
        'author': lambda x: list(set(x)),
        'location': 'first',
        'coordinates': 'first', # Take the first valid coordinate found
        'genre': lambda x: list(set(x)),
        'year': 'first'
    }).reset_index()

    # 5. BUILD GRAPH
    nodes = []
    links = []
    existing_nodes = set()

    for _, row in clean_df.iterrows():
        b_id = row['book_id']
        if b_id not in existing_nodes:
            nodes.append({"id": b_id, "label": row['title'], "type": "book", "val": 5})
            existing_nodes.add(b_id)
        
        for auth in row['author']:
            if auth == "Unknown": continue
            a_id = f"auth_{auth.replace(' ', '_')}"
            if a_id not in existing_nodes:
                nodes.append({"id": a_id, "label": auth, "type": "author", "val": 10})
                existing_nodes.add(a_id)
            links.append({"source": a_id, "target": b_id})

    # 6. BUILD MAP (ROBUST VERSION)
    map_data = []
    
    # Filter rows that actually have coordinates (ignore None or empty strings)
    valid_coords_df = clean_df.dropna(subset=['coordinates'])
    print(f"🗺️ Processing Map: Found {len(valid_coords_df)} potential items with coordinates.")

    for _, row in valid_coords_df.iterrows():
        wkt = str(row['coordinates']) # Ensure it is a string
        try:
            if "Point" in wkt:
                # Wikidata returns "Point(12.34 56.78)" -> Longitude Latitude
                clean = wkt.replace("Point(", "").replace(")", "").strip()
                parts = clean.split(" ")
                
                if len(parts) >= 2:
                    lng = float(parts[0])
                    lat = float(parts[1])
                    
                    map_data.append({
                        "title": f"{row['title']} ({row['year']})",
                        "author": row['author'],
                        "location": row['location'],
                        "lat_lng": [lat, lng] # Leaflet needs [Lat, Lng]
                    })
        except Exception as e:
            print(f"⚠️ Map Coordinate Error for {row['title']}: {e}")

    print(f"✅ Pipeline Success: {len(nodes)} graph nodes, {len(map_data)} map points.")

    final_data = {
        "graph": {"nodes": nodes, "links": links}, 
        "map": map_data,
        "books": clean_df.to_dict(orient='records')
    }

    save_to_cache(filename, final_data)
    return final_data

# --- ENDPOINTS ---

# 2. UPDATE INGESTION TO SAVE TO GLOBAL VARIABLE
@app.post("/api/ingest")
def trigger_ingestion(
    region: str = "Global (Random)", 
    genre: str = "All Types",
    start_year: int = 1800,
    end_year: int = 2024
):
    global GLOBAL_DATA # Access the global variable
    try:
        region_id = REGION_MAP.get(region)
        genre_id = GENRE_MAP.get(genre)
        
        # Run the pipeline
        data = run_pipeline(region_id, genre_id, start_year, end_year)
        
        # SAVE RESULT TO GLOBAL MEMORY
        GLOBAL_DATA = data
        
        return {
            "status": "success", 
            "message": f"Loaded {len(data['books'])} items ({start_year}-{end_year}).",
            # We don't send the full data here to keep the request light.
            # The frontend components will fetch it separately.
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 3. NEW ENDPOINT: GET DATA
# This is what your Graph and Map components will fetch!
@app.get("/api/data")
def get_data():
    return GLOBAL_DATA

@app.get("/api/data/graph")
def get_graph_data():
    return GLOBAL_DATA["graph"]

@app.get("/api/data/map")
def get_map_data():
    return GLOBAL_DATA["map"]

# --- INTELLIGENCE SERVICE (Use Case 3) ---

@app.get("/api/services/recommend-live")
def live_recommendation_service(genre_name: str = "novel"):
    """
    Cross-Lingual Recommender:
    Finds books of a specific genre (ID) that are in Romanian, French, or German.
    """
    print(f"🧠 Intelligence Service: Searching for '{genre_name}'...")
    
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setReturnFormat(JSON)

    # Map input text to specific Genre IDs for reliability
    genre_id = GENRE_MAP.get(genre_name.lower())
    
    # Fallback if genre not found in map
    if not genre_id: 
        genre_id = "wd:Q8261" # Default to Novel

    query = f"""
    SELECT DISTINCT ?book ?bookLabel ?authorLabel ?langLabel WHERE {{
      ?book wdt:P31 wd:Q571;          # Instance of Book
            wdt:P136 {genre_id};      # Has this specific Genre ID
            wdt:P50 ?author;          # Has Author
            wdt:P407 ?lang.           # Has Language
      
      # INTELLIGENCE FILTER: Keep only Romanian (Q7913), French (Q150), German (Q188)
      VALUES ?lang {{ wd:Q7913 wd:Q150 wd:Q188 }}
      
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,ro,fr,de". }}
    }}
    LIMIT 15
    """
    
    sparql.setQuery(query)
    
    try:
        results = sparql.query().convert()
    except Exception as e:
        print(f"SPARQL ERROR: {e}")
        return [{"title": "Connection Error", "reason": "Wikidata timed out", "lang": "Error"}]

    recommendations = []
    for item in results["results"]["bindings"]:
        title = item.get("bookLabel", {}).get("value")
        author = item.get("authorLabel", {}).get("value")
        lang = item.get("langLabel", {}).get("value")
        
        # Filter out "Q-ID only" titles (garbage data)
        if title.startswith("Q") and title[1].isdigit():
            continue

        recommendations.append({
            "title": title,
            "reason": f"A famous {lang} work in the requested genre by {author}.",
            "lang": lang
        })
    
    # Fallback demo data if query returns nothing (common with strict SPARQL limits)
    if not recommendations:
        return [
            {"title": "Ion", "reason": "Classic Romanian Novel (Demo Result)", "lang": "Romanian"},
            {"title": "Les Misérables", "reason": "Classic French Novel (Demo Result)", "lang": "French"}
        ]
        
    return recommendations[:3]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
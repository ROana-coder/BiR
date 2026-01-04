"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import NetworkGraph from "./NetworkGraph";

const MapViewer = dynamic(() => import("./MapViewer"), {
  ssr: false, // This forces Next.js to ONLY load this component in the browser
  loading: () => (
    // Optional: A loading skeleton while the map loads
    <div className="w-full h-[500px] bg-gray-100 animate-pulse rounded-xl flex items-center justify-center text-gray-400">
      Loading Map...
    </div>
  ),
});

// Define the shape of a Recommendation object for TypeScript
interface Recommendation {
  title: string;
  reason: string;
  lang?: string;
}

export default function Home() {
  // --- STATE: INGESTION PIPELINE ---
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [refreshKey, setRefreshKey] = useState(0); // Forces components to reload data
  
  // Search Filters (Intelligent Querying)
  const [selectedRegion, setSelectedRegion] = useState("Global (Random)");
  const [selectedGenre, setSelectedGenre] = useState("All Types");
  
  // NEW: Time Period State
  const [startYear, setStartYear] = useState(1800);
  const [endYear, setEndYear] = useState(2024);

  // --- STATE: AI RECOMMENDER ---
  const [recLoading, setRecLoading] = useState(false);
  const [recs, setRecs] = useState<Recommendation[]>([]);

  // 1. ACTION: TRIGGER INGESTION MICROSERVICE
  const handleIngest = async () => {
    setLoading(true);
    setStatus(`Fetching: ${selectedGenre} (${startYear}-${endYear}) from ${selectedRegion}...`);
    
    try {
      // Connect to Python Backend (FastAPI) on Port 8000
      // We pass ALL filters: Region, Genre, Start Year, End Year
      const params = new URLSearchParams({
        region: selectedRegion,
        genre: selectedGenre,
        start_year: startYear.toString(),
        end_year: endYear.toString()
      });
      
      const url = `http://127.0.0.1:8000/api/ingest?${params.toString()}`;
      
      const res = await fetch(url, { method: "POST" });
      const data = await res.json();
      
      setStatus(data.message);
      setRefreshKey(prev => prev + 1); // Triggers re-render of Graph and Map
    } catch (error) {
      console.error(error);
      setStatus("Error: Is the Python backend running?");
    } finally {
      setLoading(false);
    }
  };

  const handleClearCache = async () => {
    if (!confirm("Are you sure? This will force the app to fetch slow live data again.")) return;
    
    try {
      // Must match the URL and Method exactly
      const res = await fetch("http://127.0.0.1:8000/api/cache", { method: "DELETE" });
      const data = await res.json();
      setStatus(data.message); // Show "Cache cleared!" on screen
    } catch (error) {
      console.error(error);
      alert("Failed to clear cache");
    }
  };

  // 2. ACTION: TRIGGER LIVE INTELLIGENCE SERVICE
  const getRecommendations = async () => {
    setRecLoading(true);
    try {
      // We search for "Novel" by default to find rich cross-lingual results
      const genreToSearch = "novel"; 
      const res = await fetch(`http://127.0.0.1:8000/api/services/recommend-live?genre_name=${genreToSearch}`);
      const data = await res.json();
      setRecs(data);
    } catch (error) {
      console.error(error);
      alert("Failed to fetch recommendations. Check backend console.");
    } finally {
      setRecLoading(false);
    }
  };

  return (
    <main className="min-h-screen p-10 font-sans bg-gray-50">
      
      {/* --- HEADER SECTION --- */}
      <header className="flex flex-col xl:flex-row justify-between items-start xl:items-center mb-10 border-b pb-6 gap-6">
        <div>
          <h1 className="text-4xl font-bold text-gray-800">📚 Literary Intelligence</h1>
          <p className="text-gray-600 mt-2">Master's Project: Semantic Web Data Platform</p>
        </div>
        
        {/* CONTROLS AREA */}
        <div className="flex flex-col items-end gap-2 w-full xl:w-auto">
          
          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 flex flex-wrap gap-4 items-end">
            
            {/* Filter 1: Region */}
            <div className="flex flex-col gap-1">
              <label className="text-xs font-bold text-gray-400 uppercase tracking-wide">Region</label>
              <select 
                value={selectedRegion}
                onChange={(e) => setSelectedRegion(e.target.value)}
                className="border border-gray-300 rounded px-3 py-2 text-sm text-gray-700 bg-white outline-none w-40"
              >
                <option>Global (Random)</option>
                <option>Romania</option>
                <option>France</option>
                <option>Germany</option>
                <option>United Kingdom</option>
                <option>United States</option>
                <option>Japan</option>
                <option>Russia</option>
              </select>
            </div>

            {/* Filter 2: Genre */}
            <div className="flex flex-col gap-1">
              <label className="text-xs font-bold text-gray-400 uppercase tracking-wide">Genre</label>
              <select 
                value={selectedGenre}
                onChange={(e) => setSelectedGenre(e.target.value)}
                className="border border-gray-300 rounded px-3 py-2 text-sm text-gray-700 bg-white outline-none w-44"
              >
                <option>All Types</option>
                <option>Novel</option>
                <option>Science Fiction</option>
                <option>Poetry</option>
                <option>Play (Drama)</option>
                <option>Non-fiction</option>
                <option>Biography</option>
                <option>Children's Literature</option>
                <option>Comics</option>
              </select>
            </div>

            {/* NEW: Time Period Filter */}
            <div className="flex flex-col gap-1">
              <label className="text-xs font-bold text-gray-400 uppercase tracking-wide">Time Period</label>
              <div className="flex items-center gap-2">
                <input 
                  type="number" 
                  value={startYear}
                  onChange={(e) => setStartYear(Number(e.target.value))}
                  className="w-20 border border-gray-300 rounded px-2 py-2 text-sm text-gray-700 text-center"
                  placeholder="Start"
                />
                <span className="text-gray-400">-</span>
                <input 
                  type="number" 
                  value={endYear}
                  onChange={(e) => setEndYear(Number(e.target.value))}
                  className="w-20 border border-gray-300 rounded px-2 py-2 text-sm text-gray-700 text-center"
                  placeholder="End"
                />
              </div>
            </div>

            {/* SYNC BUTTON */}
            <button 
              onClick={handleIngest}
              disabled={loading}
              className={`h-[38px] px-6 rounded shadow transition font-bold text-sm flex items-center gap-2
                ${loading ? "bg-gray-400 cursor-not-allowed text-gray-100" : "bg-blue-600 hover:bg-blue-700 text-white"}`}
            >
              {loading ? "Processing..." : "🔄 Sync"}
            </button>
            
            {/* CLEAR CACHE BUTTON */}
            <button 
              onClick={handleClearCache}
              className="h-[38px] px-3 rounded border border-red-200 bg-red-50 text-red-500 hover:bg-red-100 transition"
              title="Clear Cache (Force Live Fetch)"
            >
              🗑️
            </button>

          </div>
          
          <span className="text-xs text-gray-500 font-medium h-4 pr-1">{status}</span>
        </div>
      </header>

      {/* --- USE CASE 1: GRAPH VISUALIZATION --- */}
      <section className="mb-16">
        <h2 className="text-2xl font-bold mb-4 text-teal-700 flex items-center gap-2">
          1. Influence Network <span className="text-sm font-normal text-gray-500">(Graph View)</span>
        </h2>
        <p className="mb-4 text-gray-600 text-sm">
          Visualizing authors (Red) and their works (Teal). Drag nodes to explore connections.
        </p>
        <NetworkGraph key={`graph-${refreshKey}`} />
      </section>

      {/* --- USE CASE 2: GEOSPATIAL MAP --- */}
      <section className="mb-16">
        <h2 className="text-2xl font-bold mb-4 text-blue-700 flex items-center gap-2">
          2. Literary Atlas <span className="text-sm font-normal text-gray-500">(Geospatial View)</span>
        </h2>
        <p className="mb-4 text-gray-600 text-sm">
          Mapping the locations of authors and stories between <span className="font-bold">{startYear}</span> and <span className="font-bold">{endYear}</span>.
        </p>
        <MapViewer key={`map-${refreshKey}`} />
      </section>

      {/* --- USE CASE 3: INTELLIGENCE SERVICE --- */}
      <section className="mb-16 p-8 bg-purple-50 rounded-xl border border-purple-100 shadow-sm">
        <div className="flex flex-col md:flex-row justify-between items-start mb-6 gap-4">
          <div>
            <h3 className="text-2xl font-bold text-purple-900">🧠 AI Recommender Service</h3>
            <p className="text-purple-800 mt-1">
              <strong>Cross-Lingual Discovery:</strong> Finds resources in <span className="font-bold">Romanian/French/German</span> that match a specific Genre concept.
            </p>
          </div>
          
          <button 
            onClick={getRecommendations}
            disabled={recLoading}
            className="bg-purple-600 text-white px-5 py-3 rounded-lg shadow hover:bg-purple-700 transition font-semibold w-full md:w-auto"
          >
            {recLoading ? "Querying Wikidata..." : "🔮 Find Related Books"}
          </button>
        </div>

        {/* RESULTS GRID */}
        {recs.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {recs.map((book, i) => (
              <div key={i} className="bg-white p-5 rounded-lg shadow-md border-l-4 border-purple-400 hover:shadow-lg transition">
                <div className="font-bold text-lg text-gray-800">{book.title}</div>
                <div className="text-sm text-gray-600 mt-2">{book.reason}</div>
                <div className="mt-3 inline-block bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded font-bold uppercase">
                  {book.lang || "Foreign"}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-10 text-gray-400 italic border-2 border-dashed border-gray-200 rounded-lg bg-white/50">
            Click the button above to trigger the Federated SPARQL Query.
          </div>
        )}
      </section>

    </main>
  );
}

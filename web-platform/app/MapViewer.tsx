"use client";

import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// --- ICON FIX FOR NEXT.JS / REACT LEAFLET ---
// Leaflet's default icon paths are often broken in bundlers. This fixes it.
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

interface MapPoint {
  title: string;
  author: string[];
  location: string;
  lat_lng: [number, number]; // [Latitude, Longitude]
}

export default function MapViewer() {
  const [mapPoints, setMapPoints] = useState<MapPoint[]>([]);

  useEffect(() => {
    // FETCH DATA FROM YOUR BACKEND
    fetch("http://127.0.0.1:8000/api/data")
      .then((res) => res.json())
      .then((data) => {
        if (data.map && data.map.length > 0) {
          setMapPoints(data.map);
        } else {
          console.warn("Map: No geographical data received.");
          setMapPoints([]);
        }
      })
      .catch((err) => console.error("Failed to fetch map data:", err));
  }, []);

  return (
    <div className="w-full h-[500px] rounded-xl overflow-hidden shadow-lg border border-gray-300 relative z-0">
      <MapContainer
        center={[20, 0]} // Start zoomed out to see the world
        zoom={2}
        style={{ height: "100%", width: "100%" }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {mapPoints.map((point, idx) => (
          <Marker key={idx} position={point.lat_lng}>
            <Popup>
              <div className="text-sm">
                <strong className="text-blue-700 block text-base">{point.title}</strong>
                <span className="text-gray-600 block italic">by {point.author.join(", ")}</span>
                <hr className="my-1 border-gray-200"/>
                <span className="text-xs text-gray-500">📍 {point.location}</span>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* OVERLAY IF NO DATA */}
      {mapPoints.length === 0 && (
        <div className="absolute inset-0 bg-white/60 flex items-center justify-center z-[1000] pointer-events-none">
          <p className="text-gray-500 font-semibold bg-white px-4 py-2 rounded shadow">
            No locations found yet. Try Syncing data.
          </p>
        </div>
      )}
    </div>
  );
}
/**
 * Map View Component
 * Uses react-leaflet for geographic visualization
 * Displays author birthplaces (Red) and book narrative locations (Blue)
 * Optimized for Dark Mode with high contrast popups
 */

import React, { useMemo, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import type { GeoResponse, GeoPoint } from '../types';
import 'leaflet/dist/leaflet.css';

// Fix for default marker icons in react-leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;

// Custom Red Icon (Birthplaces)
const redIcon = L.divIcon({
    className: 'custom-marker',
    html: `
        <svg width="32" height="40" viewBox="0 0 32 40" xmlns="http://www.w3.org/2000/svg">
            <path d="M16 0C7.163 0 0 7.163 0 16c0 12 16 24 16 24s16-12 16-24c0-8.837-7.163-16-16-16z" 
                  fill="#e11d48" stroke="#fff" stroke-width="2"/>
            <circle cx="16" cy="16" r="6" fill="#fff"/>
        </svg>
    `,
    iconSize: [32, 40],
    iconAnchor: [16, 40],
    popupAnchor: [0, -40],
});

// Custom Blue Icon (Narrative Locations / Settings)
const blueIcon = L.divIcon({
    className: 'custom-marker',
    html: `
        <svg width="32" height="40" viewBox="0 0 32 40" xmlns="http://www.w3.org/2000/svg">
            <path d="M16 0C7.163 0 0 7.163 0 16c0 12 16 24 16 24s16-12 16-24c0-8.837-7.163-16-16-16z" 
                  fill="#3b82f6" stroke="#fff" stroke-width="2"/>
            <rect x="10" y="10" width="12" height="12" fill="#fff" rx="2"/>
        </svg>
    `,
    iconSize: [32, 40],
    iconAnchor: [16, 40],
    popupAnchor: [0, -40],
});

interface MapViewProps {
    data: Record<string, GeoResponse>;
    height?: number;
    onPointClick?: (point: GeoPoint) => void;
}

// Component to fit map bounds to points
function FitBounds({ points }: { points: GeoPoint[] }) {
    const map = useMap();

    useEffect(() => {
        if (points.length > 0) {
            const bounds = L.latLngBounds(
                points.map(p => [p.latitude, p.longitude] as [number, number])
            );
            map.fitBounds(bounds, { padding: [50, 50], maxZoom: 6 });
        }
    }, [map, points]);

    return null;
}

export function MapView({ data, height = 500, onPointClick }: MapViewProps) {
    // Combine all points across layers
    const allPoints = useMemo(() => {
        const points: GeoPoint[] = [];
        console.log('MapView received data:', data);

        Object.entries(data).forEach(([layerKey, layer]) => {
            if (layer && layer.points && Array.isArray(layer.points)) {
                console.log(`Layer ${layerKey} has ${layer.points.length} points`);
                points.push(...layer.points);
            }
        });

        console.log('Total points to render:', points.length);
        return points;
    }, [data]);

    // Calculate center (default Paris)
    const center = useMemo((): [number, number] => {
        if (!allPoints.length) return [48.8566, 2.3522];
        const avgLat = allPoints.reduce((sum, p) => sum + p.latitude, 0) / allPoints.length;
        const avgLng = allPoints.reduce((sum, p) => sum + p.longitude, 0) / allPoints.length;
        return [avgLat, avgLng];
    }, [allPoints]);

    if (!allPoints.length) {
        return (
            <div style={{
                height,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                background: '#1a1a1a',
                color: '#888',
                borderRadius: '8px'
            }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>🗺️</div>
                <h3 style={{ margin: 0, color: '#fff' }}>No Geographic Data</h3>
                <p style={{ margin: '8px 0 0', fontSize: '14px' }}>
                    Search for books to see locations on the map.
                </p>
            </div>
        );
    }

    return (
        <div style={{ height, position: 'relative' }}>
            {/* CSS for custom markers and Dark Mode Popups */}
            <style>{`
                .custom-marker {
                    background: transparent;
                    border: none;
                }
                /* Dark Theme for Leaflet Popups */
                .leaflet-popup-content-wrapper, .leaflet-popup-tip {
                    background: #262626 !important; /* Neutral 800 */
                    color: #ffffff !important;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5) !important;
                    border: 1px solid #404040;
                }
                .leaflet-popup-content {
                    margin: 12px 14px !important;
                    line-height: 1.5;
                }
                .leaflet-container a.leaflet-popup-close-button {
                    color: #a3a3a3 !important; /* Neutral 400 */
                    font-size: 16px !important;
                    padding: 8px !important;
                }
                .leaflet-container a.leaflet-popup-close-button:hover {
                    color: #ffffff !important;
                }
            `}</style>

            {/* Stats overlay */}
            <div
                style={{
                    position: 'absolute',
                    top: '16px',
                    right: '16px',
                    zIndex: 1000,
                    background: 'rgba(26, 26, 26, 0.9)',
                    padding: '12px 16px',
                    borderRadius: '8px',
                    fontSize: '14px',
                    color: '#fff',
                    fontWeight: 'bold',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                }}
            >
                <div>📍 {allPoints.length} locations</div>
            </div>

            <MapContainer
                center={center}
                zoom={4}
                style={{
                    height: '100%',
                    width: '100%',
                    minHeight: '400px',
                    borderRadius: '8px',
                    background: '#262626'
                }}
                scrollWheelZoom={true}
            >
                {/* Light tile layer for contrast */}
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                {/* Fit bounds to show all points */}
                <FitBounds points={allPoints} />

                {/* Render markers for each point */}
                {allPoints.map((point, index) => {
                    // Determine type: Narrative Location (Setting) vs Author Birthplace
                    const isSetting = point.layer === 'settings' || point.entity_type === 'book';
                    const icon = isSetting ? blueIcon : redIcon;
                    // Colors optimized for dark background
                    const titleColor = isSetting ? '#60a5fa' : '#fb7185'; // Blue-400 : Rose-400

                    return (
                        <Marker
                            key={`marker-${index}-${point.qid}`}
                            position={[point.latitude, point.longitude]}
                            icon={icon}
                            eventHandlers={{
                                click: () => onPointClick?.(point),
                            }}
                        >
                            <Popup>
                                <div style={{ minWidth: '180px', fontFamily: 'system-ui, sans-serif' }}>
                                    <strong style={{ fontSize: '15px', color: titleColor }}>
                                        {isSetting ? '📖' : '📍'} {point.name}
                                    </strong>
                                    {point.entity_name && (
                                        <div style={{ fontSize: '13px', marginTop: '8px', color: '#e5e5e5' }}>
                                            <span style={{ color: '#a3a3a3', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                                {isSetting ? 'Setting of' : 'Birthplace of'}
                                            </span>
                                            <br />
                                            <strong style={{ fontSize: '14px', display: 'block', marginTop: '2px' }}>
                                                {point.entity_name}
                                            </strong>
                                        </div>
                                    )}
                                    {point.year && (
                                        <div style={{ fontSize: '12px', marginTop: '6px', color: '#a3a3a3' }}>
                                            {isSetting ? 'Published:' : 'Born:'} {point.year}
                                        </div>
                                    )}
                                </div>
                            </Popup>
                        </Marker>
                    );
                })}
            </MapContainer>

            {/* Legend */}
            <div
                style={{
                    position: 'absolute',
                    bottom: '16px',
                    left: '16px',
                    zIndex: 1000,
                    background: 'rgba(26, 26, 26, 0.95)',
                    padding: '12px',
                    borderRadius: '8px',
                    fontSize: '13px',
                    color: '#fff',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3)',
                }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '16px' }}>📍</span>
                    <span style={{ color: '#fb7185', fontWeight: 500 }}>Author Birthplaces</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '16px' }}>📖</span>
                    <span style={{ color: '#60a5fa', fontWeight: 500 }}>Story Settings</span>
                </div>
            </div>
        </div>
    );
}

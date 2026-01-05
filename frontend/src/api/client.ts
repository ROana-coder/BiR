/**
 * API client for Literature Explorer backend
 */

import axios from 'axios';
import type {
    Book,
    GraphData,
    GeoResponse,
    SimilarAuthor,
    SearchParams,
    GraphParams,
    GeoParams,
} from '../types';

// Create axios instance with base config
const api = axios.create({
    baseURL: '/api',
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 60000, // 60 second timeout for Wikidata queries
});

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 504) {
            throw new Error('Query timeout. Try narrowing your search with more filters.');
        }
        if (error.response?.status === 503) {
            throw new Error('Wikidata service unavailable. Please try again later.');
        }
        throw error;
    }
);

// === Search API ===

export async function searchBooks(params: SearchParams): Promise<Book[]> {
    const { data } = await api.get<Book[]>('/search/books', { params });
    return data;
}

export async function getBook(qid: string): Promise<Book> {
    const { data } = await api.get<Book>(`/search/books/${qid}`);
    return data;
}

// === Graph API ===

export async function getAuthorNetwork(params: GraphParams): Promise<GraphData> {
    const { data } = await api.get<GraphData>('/graph/network', {
        params: {
            authors: params.authors,
            depth: params.depth ?? 2,
            include_coauthorship: params.include_coauthorship ?? false,
            include_movements: params.include_movements ?? true,
        },
        paramsSerializer: {
            indexes: null, // Serialize arrays as ?authors=Q1&authors=Q2
        },
    });
    return data;
}

export async function getAuthorBooks(qid: string): Promise<Record<string, unknown>[]> {
    const { data } = await api.get<Record<string, unknown>[]>(`/graph/author/${qid}/books`);
    return data;
}

// === Geo API ===

export async function getLocations(params: GeoParams): Promise<GeoResponse> {
    const { data } = await api.get<GeoResponse>('/geo/locations', {
        params: {
            layer: params.layer,
            authors: params.authors,
            books: params.books,
            cluster: params.cluster ?? true,
        },
        paramsSerializer: {
            indexes: null,
        },
    });
    return data;
}

export async function getAuthorLocations(qid: string): Promise<Record<string, GeoResponse>> {
    const { data } = await api.get<Record<string, GeoResponse>>(`/geo/author/${qid}/locations`);
    return data;
}

// === Recommendations API ===

export async function getSimilarAuthors(qid: string, limit = 10): Promise<SimilarAuthor[]> {
    const { data } = await api.get<SimilarAuthor[]>(`/recommendations/similar-authors/${qid}`, {
        params: { limit },
    });
    return data;
}

// === Health API ===

export async function checkHealth(): Promise<{ status: string; cache: string }> {
    const { data } = await api.get<{ status: string; cache: string }>('/health');
    return data;
}

export default api;

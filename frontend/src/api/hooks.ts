/**
 * React Query hooks for data fetching with caching
 */

import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import type {
    Book,
    GraphData,
    GeoResponse,
    SimilarAuthor,
    SearchParams,
    GraphParams,
    GeoParams,
} from '../types';
import * as api from './client';

// Query key factories for cache management
export const queryKeys = {
    books: {
        all: ['books'] as const,
        search: (params: SearchParams) => ['books', 'search', params] as const,
        detail: (qid: string) => ['books', 'detail', qid] as const,
    },
    graph: {
        all: ['graph'] as const,
        network: (params: GraphParams) => ['graph', 'network', params] as const,
        authorBooks: (qid: string) => ['graph', 'authorBooks', qid] as const,
    },
    geo: {
        all: ['geo'] as const,
        locations: (params: GeoParams) => ['geo', 'locations', params] as const,
        authorLocations: (qid: string) => ['geo', 'authorLocations', qid] as const,
    },
    recommendations: {
        all: ['recommendations'] as const,
        similar: (qid: string, limit?: number) => ['recommendations', 'similar', qid, limit] as const,
    },
};

// === Search Hooks ===

export function useSearchBooks(
    params: SearchParams,
    options?: Omit<UseQueryOptions<Book[], Error>, 'queryKey' | 'queryFn'>
) {
    return useQuery({
        queryKey: queryKeys.books.search(params),
        queryFn: () => api.searchBooks(params),
        staleTime: 5 * 60 * 1000, // 5 minutes
        ...options,
    });
}

export function useBook(
    qid: string,
    options?: Omit<UseQueryOptions<Book, Error>, 'queryKey' | 'queryFn'>
) {
    return useQuery({
        queryKey: queryKeys.books.detail(qid),
        queryFn: () => api.getBook(qid),
        staleTime: 10 * 60 * 1000, // 10 minutes (static data)
        enabled: !!qid,
        ...options,
    });
}

// === Graph Hooks ===

export function useAuthorNetwork(
    params: GraphParams,
    options?: Omit<UseQueryOptions<GraphData, Error>, 'queryKey' | 'queryFn'>
) {
    return useQuery({
        queryKey: queryKeys.graph.network(params),
        queryFn: () => api.getAuthorNetwork(params),
        staleTime: 10 * 60 * 1000, // 10 minutes
        enabled: params.authors.length > 0,
        ...options,
    });
}

export function useAuthorBooks(
    qid: string,
    options?: Omit<UseQueryOptions<Record<string, unknown>[], Error>, 'queryKey' | 'queryFn'>
) {
    return useQuery({
        queryKey: queryKeys.graph.authorBooks(qid),
        queryFn: () => api.getAuthorBooks(qid),
        staleTime: 10 * 60 * 1000,
        enabled: !!qid,
        ...options,
    });
}

// === Geo Hooks ===

export function useLocations(
    params: GeoParams,
    options?: Omit<UseQueryOptions<GeoResponse, Error>, 'queryKey' | 'queryFn'>
) {
    return useQuery({
        queryKey: queryKeys.geo.locations(params),
        queryFn: () => api.getLocations(params),
        staleTime: 10 * 60 * 1000,
        // Let the caller control enabled via options
        ...options,
    });
}

export function useAuthorLocations(
    qid: string,
    options?: Omit<UseQueryOptions<Record<string, GeoResponse>, Error>, 'queryKey' | 'queryFn'>
) {
    return useQuery({
        queryKey: queryKeys.geo.authorLocations(qid),
        queryFn: () => api.getAuthorLocations(qid),
        staleTime: 10 * 60 * 1000,
        enabled: !!qid,
        ...options,
    });
}

// === Recommendation Hooks ===

export function useSimilarAuthors(
    qid: string,
    limit = 10,
    options?: Omit<UseQueryOptions<SimilarAuthor[], Error>, 'queryKey' | 'queryFn'>
) {
    return useQuery({
        queryKey: queryKeys.recommendations.similar(qid, limit),
        queryFn: () => api.getSimilarAuthors(qid, limit),
        staleTime: 10 * 60 * 1000,
        enabled: !!qid,
        ...options,
    });
}

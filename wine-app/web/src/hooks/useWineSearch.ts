/**
 * Hook for wine search functionality
 */

import { useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

export function useWineSearch() {
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');

  // Debounce the search query
  const handleSearch = useCallback((searchQuery: string) => {
    setQuery(searchQuery);
    const timeoutId = setTimeout(() => {
      setDebouncedQuery(searchQuery);
    }, 300);
    return () => clearTimeout(timeoutId);
  }, []);

  const { data, isLoading, error } = useQuery({
    queryKey: ['wineSearch', debouncedQuery],
    queryFn: async () => {
      if (!debouncedQuery.trim()) {
        return [];
      }
      const response = await api.searchWines(debouncedQuery);
      return response.wines;
    },
    enabled: debouncedQuery.length >= 2,
  });

  return {
    query,
    setQuery: handleSearch,
    results: data || [],
    isLoading,
    error: error instanceof Error ? error.message : null,
  };
}

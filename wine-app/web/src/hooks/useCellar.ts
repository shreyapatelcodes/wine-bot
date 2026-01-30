/**
 * Hook for managing cellar bottles
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import type { CellarBottleCreate, CellarBottleUpdate, CellarBottle } from '../types';

export function useCellar(status?: 'owned' | 'tried') {
  const { isAuthenticated } = useAuth();
  const queryClient = useQueryClient();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['cellar', status],
    queryFn: async () => {
      const response = await api.getCellar(status);
      return response.bottles;
    },
    enabled: isAuthenticated,
    refetchOnWindowFocus: true,
    staleTime: 1000, // Consider data stale after 1 second
  });

  const addMutation = useMutation({
    mutationFn: (data: CellarBottleCreate) => api.addToCellar(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cellar'] });
      queryClient.invalidateQueries({ queryKey: ['savedBottles'] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ bottleId, data }: { bottleId: string; data: CellarBottleUpdate }) =>
      api.updateCellarBottle(bottleId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cellar'] });
    },
  });

  const removeMutation = useMutation({
    mutationFn: (bottleId: string) => api.removeCellarBottle(bottleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cellar'] });
    },
  });

  // Helper to get counts by status
  const ownedCount = data?.filter((b: CellarBottle) => b.status === 'owned').length || 0;
  const triedCount = data?.filter((b: CellarBottle) => b.status === 'tried').length || 0;

  return {
    bottles: data || [],
    ownedCount,
    triedCount,
    isLoading,
    error: error instanceof Error ? error.message : null,
    refetch,
    addToCellar: addMutation.mutateAsync,
    isAdding: addMutation.isPending,
    updateBottle: updateMutation.mutateAsync,
    isUpdating: updateMutation.isPending,
    removeBottle: removeMutation.mutateAsync,
    isRemoving: removeMutation.isPending,
  };
}

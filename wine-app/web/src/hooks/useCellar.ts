/**
 * Hook for managing cellar bottles
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import type { CellarBottleCreate, CellarBottleUpdate, CellarStatus } from '../types';

export function useCellar(statusFilter?: CellarStatus) {
  const queryClient = useQueryClient();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['cellar', statusFilter],
    queryFn: async () => {
      const response = await api.getCellar(statusFilter);
      return response.bottles;
    },
  });

  const addMutation = useMutation({
    mutationFn: (data: CellarBottleCreate) => api.addToCellar(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cellar'] });
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

  return {
    bottles: data || [],
    isLoading,
    error: error instanceof Error ? error.message : null,
    refetch,
    addBottle: addMutation.mutateAsync,
    isAdding: addMutation.isPending,
    updateBottle: (bottleId: string, data: CellarBottleUpdate) =>
      updateMutation.mutateAsync({ bottleId, data }),
    isUpdating: updateMutation.isPending,
    removeBottle: removeMutation.mutateAsync,
    isRemoving: removeMutation.isPending,
  };
}

export function useCellarStats() {
  const { data: allBottles } = useQuery({
    queryKey: ['cellar'],
    queryFn: async () => {
      const response = await api.getCellar();
      return response.bottles;
    },
  });

  const bottles = allBottles || [];

  return {
    total: bottles.length,
    owned: bottles.filter(b => b.status === 'owned').length,
    tried: bottles.filter(b => b.status === 'tried').length,
    wishlist: bottles.filter(b => b.status === 'wishlist').length,
    totalBottles: bottles.filter(b => b.status === 'owned').reduce((sum, b) => sum + b.quantity, 0),
  };
}

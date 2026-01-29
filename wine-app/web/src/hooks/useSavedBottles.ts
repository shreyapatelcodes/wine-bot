/**
 * Hook for managing saved bottles
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import type { SavedBottle, SavedBottleCreate } from '../types';

export function useSavedBottles() {
  const queryClient = useQueryClient();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['savedBottles'],
    queryFn: async () => {
      const response = await api.getSavedBottles();
      return response.bottles;
    },
  });

  const saveMutation = useMutation({
    mutationFn: (data: SavedBottleCreate) => api.saveBottle(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savedBottles'] });
    },
  });

  const removeMutation = useMutation({
    mutationFn: (bottleId: string) => api.removeSavedBottle(bottleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savedBottles'] });
    },
  });

  const moveToCellarMutation = useMutation({
    mutationFn: (bottleId: string) => api.moveToCellar(bottleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savedBottles'] });
      queryClient.invalidateQueries({ queryKey: ['cellar'] });
    },
  });

  return {
    bottles: data || [],
    isLoading,
    error: error instanceof Error ? error.message : null,
    refetch,
    saveBottle: saveMutation.mutateAsync,
    isSaving: saveMutation.isPending,
    removeBottle: removeMutation.mutateAsync,
    isRemoving: removeMutation.isPending,
    moveToCellar: moveToCellarMutation.mutateAsync,
    isMovingToCellar: moveToCellarMutation.isPending,
  };
}

export function useIsWineSaved(wineId: string) {
  const { bottles } = useSavedBottles();
  return bottles.some((b: SavedBottle) => b.wine.id === wineId);
}

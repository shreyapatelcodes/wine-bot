/**
 * API service layer for communicating with the Flask backend
 */

import type {
  AuthResponse,
  UserProfile,
  UserProfileUpdate,
  SavedBottleCreate,
  SavedBottlesResponse,
  CellarBottle,
  CellarBottleCreate,
  CellarBottleUpdate,
  CellarResponse,
  RecommendationRequest,
  RecommendationResponse,
  WineSearchResponse,
  VisionAnalyzeResponse,
  VisionMatchResponse,
  ApiError,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// Token storage keys
const ACCESS_TOKEN_KEY = 'wine_app_access_token';
const REFRESH_TOKEN_KEY = 'wine_app_refresh_token';

// ============== Token Management ==============

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(accessToken: string, refreshToken: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

// ============== API Client ==============

class ApiClient {
  private baseUrl: string;
  private isRefreshing: boolean = false;
  private refreshPromise: Promise<boolean> | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    requiresAuth: boolean = true
  ): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (requiresAuth) {
      const token = getAccessToken();
      if (token) {
        (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
      }
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    // Handle 401 - try to refresh token
    if (response.status === 401 && requiresAuth) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        // Retry the request with new token
        const newToken = getAccessToken();
        if (newToken) {
          (headers as Record<string, string>)['Authorization'] = `Bearer ${newToken}`;
        }
        const retryResponse = await fetch(`${this.baseUrl}${endpoint}`, {
          ...options,
          headers,
        });
        if (!retryResponse.ok) {
          const error: ApiError = await retryResponse.json().catch(() => ({ error: 'Request failed' }));
          throw new Error(error.error || `HTTP ${retryResponse.status}`);
        }
        return retryResponse.json();
      } else {
        // Refresh failed, clear tokens
        clearTokens();
        throw new Error('Session expired. Please log in again.');
      }
    }

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({ error: 'Request failed' }));
      throw new Error(error.error || `HTTP ${response.status}`);
    }

    return response.json();
  }

  private async refreshAccessToken(): Promise<boolean> {
    // Prevent multiple simultaneous refresh attempts
    if (this.isRefreshing) {
      return this.refreshPromise || Promise.resolve(false);
    }

    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      return false;
    }

    this.isRefreshing = true;
    this.refreshPromise = (async () => {
      try {
        const response = await fetch(`${this.baseUrl}/api/v1/auth/refresh`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${refreshToken}`,
          },
        });

        if (!response.ok) {
          return false;
        }

        const data = await response.json();
        setTokens(data.access_token, data.refresh_token);
        return true;
      } catch {
        return false;
      } finally {
        this.isRefreshing = false;
        this.refreshPromise = null;
      }
    })();

    return this.refreshPromise;
  }

  // ============== Auth API ==============

  async loginWithGoogle(idToken: string): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>(
      '/api/v1/auth/google',
      {
        method: 'POST',
        body: JSON.stringify({ id_token: idToken }),
      },
      false
    );
    setTokens(response.access_token, response.refresh_token);
    return response;
  }

  async logout(): Promise<void> {
    try {
      await this.request('/api/v1/auth/logout', { method: 'POST' });
    } finally {
      clearTokens();
    }
  }

  // ============== User API ==============

  async getCurrentUser(): Promise<UserProfile> {
    return this.request<UserProfile>('/api/v1/users/me');
  }

  async updateUser(data: UserProfileUpdate): Promise<UserProfile> {
    return this.request<UserProfile>('/api/v1/users/me', {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deleteAccount(): Promise<void> {
    await this.request('/api/v1/users/me', { method: 'DELETE' });
    clearTokens();
  }

  // ============== Saved Bottles API ==============

  async getSavedBottles(): Promise<SavedBottlesResponse> {
    return this.request<SavedBottlesResponse>('/api/v1/saved-bottles');
  }

  async saveBottle(data: SavedBottleCreate): Promise<{ id: string; message: string }> {
    return this.request('/api/v1/saved-bottles', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async removeSavedBottle(bottleId: string): Promise<void> {
    await this.request(`/api/v1/saved-bottles/${bottleId}`, {
      method: 'DELETE',
    });
  }

  async moveToCellar(bottleId: string): Promise<{ cellar_bottle_id: string; message: string }> {
    return this.request(`/api/v1/saved-bottles/${bottleId}/to-cellar`, {
      method: 'POST',
    });
  }

  // ============== Cellar API ==============

  async getCellar(status?: string): Promise<CellarResponse> {
    const params = status ? `?status=${status}` : '';
    return this.request<CellarResponse>(`/api/v1/cellar${params}`);
  }

  async addToCellar(data: CellarBottleCreate): Promise<{ id: string; message: string }> {
    return this.request('/api/v1/cellar', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getCellarBottle(bottleId: string): Promise<CellarBottle> {
    return this.request<CellarBottle>(`/api/v1/cellar/${bottleId}`);
  }

  async updateCellarBottle(bottleId: string, data: CellarBottleUpdate): Promise<void> {
    await this.request(`/api/v1/cellar/${bottleId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async removeCellarBottle(bottleId: string): Promise<void> {
    await this.request(`/api/v1/cellar/${bottleId}`, {
      method: 'DELETE',
    });
  }

  // ============== Wine Search API ==============

  async searchWines(query: string, limit: number = 20): Promise<WineSearchResponse> {
    return this.request<WineSearchResponse>(
      `/api/v1/wines/search?q=${encodeURIComponent(query)}&limit=${limit}`,
      {},
      false
    );
  }

  // ============== Recommendations API ==============

  async getRecommendations(request: RecommendationRequest): Promise<RecommendationResponse> {
    return this.request<RecommendationResponse>(
      '/api/v1/recommendations',
      {
        method: 'POST',
        body: JSON.stringify(request),
      },
      false
    );
  }

  // ============== Vision API (Phase 4) ==============

  async analyzeImage(imageBase64: string): Promise<VisionAnalyzeResponse> {
    return this.request<VisionAnalyzeResponse>('/api/v1/vision/analyze', {
      method: 'POST',
      body: JSON.stringify({ image: imageBase64 }),
    });
  }

  async matchImage(imageBase64: string): Promise<VisionMatchResponse> {
    return this.request<VisionMatchResponse>('/api/v1/vision/match', {
      method: 'POST',
      body: JSON.stringify({ image: imageBase64 }),
    });
  }

  // ============== Health Check ==============

  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/health', {}, false);
  }
}

// Export singleton instance
export const api = new ApiClient(API_BASE_URL);

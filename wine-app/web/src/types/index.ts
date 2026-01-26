/**
 * TypeScript interfaces matching the backend Pydantic models
 */

// ============== Auth Types ==============

export interface GoogleAuthRequest {
  id_token: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthResponse extends TokenResponse {
  user: UserProfile;
  is_new_user: boolean;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

// ============== User Types ==============

export interface UserProfile {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  oauth_provider: string;
  created_at: string;
  preferences: Record<string, unknown>;
}

export interface UserProfileUpdate {
  display_name?: string;
  preferences?: Record<string, unknown>;
}

// ============== Wine Types ==============

export type WineType = 'red' | 'white' | 'rosé' | 'sparkling';

export interface WineMetadata {
  body?: string;
  sweetness?: string;
  acidity?: string;
  tannin?: string;
  characteristics?: string[];
  flavor_notes?: string[];
}

export interface Wine {
  id: string;
  name: string;
  producer: string | null;
  vintage: number | null;
  wine_type: WineType;
  varietal: string | null;
  country: string | null;
  region: string | null;
  price_usd: number | null;
  metadata?: WineMetadata;
  wine_metadata?: WineMetadata;
}

export interface WineSearchResult {
  wine: Wine;
  relevance_score: number;
}

// ============== Saved Bottles Types ==============

export interface SavedBottleCreate {
  wine_id: string;
  recommendation_context?: string;
  notes?: string;
}

export interface SavedBottle {
  id: string;
  wine: Wine;
  recommendation_context: string | null;
  notes: string | null;
  saved_at: string;
}

export interface SavedBottlesResponse {
  bottles: SavedBottle[];
  count: number;
}

// ============== Cellar Types ==============

export type CellarStatus = 'owned' | 'tried' | 'wishlist';

export interface CellarBottleCreate {
  wine_id?: string;
  custom_wine_name?: string;
  custom_wine_producer?: string;
  custom_wine_vintage?: number;
  custom_wine_type?: WineType;
  custom_wine_varietal?: string;
  custom_wine_region?: string;
  custom_wine_country?: string;
  custom_wine_metadata?: WineMetadata;
  status?: CellarStatus;
  quantity?: number;
  purchase_date?: string;
  purchase_price?: number;
  purchase_location?: string;
  image_url?: string;
  image_recognition_data?: Record<string, unknown>;
}

export interface CellarBottleUpdate {
  status?: CellarStatus;
  quantity?: number;
  rating?: number;
  tasting_notes?: string;
  tried_date?: string;
  notes?: string;
}

export interface CellarBottle {
  id: string;
  wine: Wine | null;
  custom_wine_name: string | null;
  custom_wine_producer: string | null;
  custom_wine_vintage: number | null;
  custom_wine_type: WineType | null;
  custom_wine_varietal: string | null;
  custom_wine_region: string | null;
  custom_wine_country: string | null;
  custom_wine_metadata: WineMetadata | null;
  status: CellarStatus;
  quantity: number;
  purchase_date: string | null;
  purchase_price: number | null;
  purchase_location: string | null;
  rating: number | null;
  tasting_notes: string | null;
  tried_date: string | null;
  image_url: string | null;
  added_at: string;
  updated_at: string;
}

export interface CellarResponse {
  bottles: CellarBottle[];
  count: number;
}

// ============== Recommendation Types ==============

export interface RecommendationRequest {
  description: string;
  budget_min?: number;
  budget_max?: number;
  wine_type_pref?: WineType;
  food_pairing?: string;
  from_cellar?: boolean;
}

export interface WineRecommendation {
  wine: Wine;
  explanation: string;
  relevance_score: number;
  is_saved: boolean;
  is_in_cellar: boolean;
}

export interface RecommendationResponse {
  recommendations: WineRecommendation[];
  count: number;
}

// ============== Vision Types ==============

export interface VisionAnalyzeRequest {
  image: string; // Base64-encoded image
}

export interface VisionAnalyzeResponse {
  name: string | null;
  producer: string | null;
  vintage: number | null;
  wine_type: string | null;
  varietal: string | null;
  region: string | null;
  country: string | null;
  additional_info: string | null;
  confidence: number;
}

export interface VisionMatchResponse {
  analysis: VisionAnalyzeResponse;
  matches: WineSearchResult[];
  best_match: Wine | null;
}

// ============== Chat Types ==============

export type MessageRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  recommendations?: WineRecommendation[];
}

// ============== API Response Types ==============

export interface ApiError {
  error: string;
}

export interface WineSearchResponse {
  wines: Wine[];
  count: number;
}

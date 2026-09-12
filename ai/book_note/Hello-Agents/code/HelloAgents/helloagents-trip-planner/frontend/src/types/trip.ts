export type MealType = "breakfast" | "lunch" | "dinner" | "snack";
export type RouteType = "walking" | "driving" | "transit";

export interface TripRequest {
  city: string;
  start_date: string;
  end_date: string;
  travel_days: number;
  transportation: string;
  accommodation: string;
  preferences?: string[];
  free_text_input?: string | null;
}

export type ValidatedTripRequest = TripRequest & {
  preferences: string[];
  free_text_input: string | null;
};

export interface POISearchRequest {
  keywords: string;
  city: string;
  citylimit?: boolean;
}

export interface RouteRequest {
  origin_address: string;
  destination_address: string;
  origin_city?: string | null;
  destination_city?: string | null;
  route_type?: RouteType;
}

export interface Location {
  longitude: number;
  latitude: number;
}

export interface Attraction {
  name: string;
  address: string;
  location: Location;
  visit_duration: number;
  description: string;
  category: string | null;
  rating: number | null;
  photos: string[];
  poi_id: string;
  image_url: string | null;
  ticket_price: number;
}

export interface Meal {
  type: MealType;
  name: string;
  address: string | null;
  location: Location | null;
  description: string | null;
  estimated_cost: number;
}

export interface Hotel {
  name: string;
  address: string;
  location: Location | null;
  price_range: string;
  rating: string;
  distance: string;
  type: string;
  estimated_cost: number;
}

export interface DayPlan {
  date: string;
  day_index: number;
  description: string;
  transportation: string;
  accommodation: string;
  hotel: Hotel | null;
  attractions: Attraction[];
  meals: Meal[];
}

export interface WeatherInfo {
  date: string;
  day_weather: string;
  night_weather: string;
  day_temp: number;
  night_temp: number;
  wind_direction: string;
  wind_power: string;
}

export interface Budget {
  total_attractions: number;
  total_hotels: number;
  total_meals: number;
  total_transportation: number;
  total: number;
}

export interface TripPlan {
  city: string;
  start_date: string;
  end_date: string;
  days: DayPlan[];
  weather_info: WeatherInfo[];
  overall_suggestions: string;
  budget: Budget | null;
}

export interface TripPlanResponse {
  success: boolean;
  message: string;
  data: TripPlan | null;
}

export interface POIInfo {
  id: string;
  name: string;
  type: string;
  address: string;
  location: Location;
  tel: string | null;
}

export interface POISearchResponse {
  success: boolean;
  message: string;
  data: POIInfo[];
}

export interface RouteInfo {
  distance: number;
  duration: number;
  route_type: RouteType;
  description: string;
}

export interface RouteResponse {
  success: boolean;
  message: string;
  data: RouteInfo | null;
}

export interface WeatherResponse {
  success: boolean;
  message: string;
  data: WeatherInfo[];
}

export interface ErrorResponse {
  success: false;
  message: string;
  error_code: string | null;
}

import type { TripPlan } from "../types/trip";

const TRIP_PLAN_KEY = "helloagents.tripPlan";

function isTripPlan(value: unknown): value is TripPlan {
  if (!value || typeof value !== "object") {
    return false;
  }
  const candidate = value as Partial<TripPlan>;
  return (
    typeof candidate.city === "string" &&
    typeof candidate.start_date === "string" &&
    typeof candidate.end_date === "string" &&
    Array.isArray(candidate.days) &&
    Array.isArray(candidate.weather_info) &&
    typeof candidate.overall_suggestions === "string"
  );
}

export function saveTripPlan(plan: TripPlan): void {
  sessionStorage.setItem(TRIP_PLAN_KEY, JSON.stringify(plan));
}

export function loadTripPlan(): TripPlan | null {
  const raw = sessionStorage.getItem(TRIP_PLAN_KEY);
  if (!raw) {
    return null;
  }
  try {
    const value: unknown = JSON.parse(raw);
    if (isTripPlan(value)) {
      return value;
    }
  } catch {
    // Invalid session data is discarded below.
  }
  sessionStorage.removeItem(TRIP_PLAN_KEY);
  return null;
}

export function clearTripPlan(): void {
  sessionStorage.removeItem(TRIP_PLAN_KEY);
}

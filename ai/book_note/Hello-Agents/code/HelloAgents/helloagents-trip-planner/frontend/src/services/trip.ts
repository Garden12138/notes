import { api } from "./api";

import type {
  TripPlanResponse,
  TripRequest,
  ValidatedTripRequest,
} from "../types/trip";

export async function validateTripRequest(
  request: TripRequest,
): Promise<ValidatedTripRequest> {
  const response = await api.post<ValidatedTripRequest>(
    "/trip/validate",
    request,
  );
  return response.data;
}

export async function createTripPlan(
  request: TripRequest,
): Promise<TripPlanResponse> {
  const response = await api.post<TripPlanResponse>("/trip/plan", request);
  return response.data;
}

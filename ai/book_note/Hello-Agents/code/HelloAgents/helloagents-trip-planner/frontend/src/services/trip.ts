import { api } from "./api";

import type { TripRequest, ValidatedTripRequest } from "../types/trip";

export async function validateTripRequest(
  request: TripRequest,
): Promise<ValidatedTripRequest> {
  const response = await api.post<ValidatedTripRequest>(
    "/trip/validate",
    request,
  );
  return response.data;
}

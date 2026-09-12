"""Travel request validation routes introduced in section 13.2."""

from __future__ import annotations

from fastapi import APIRouter

from ...models import TripRequest


router = APIRouter(prefix="/trip", tags=["trip"])


@router.post("/validate", response_model=TripRequest)
def validate_trip_request(request: TripRequest) -> TripRequest:
    """Return a normalized request without invoking agents or external APIs."""
    return request

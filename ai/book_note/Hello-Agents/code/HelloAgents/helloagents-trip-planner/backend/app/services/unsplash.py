"""Unsplash image enrichment kept separate from Agent tool selection."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Callable, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import TripPlan


class HTTPResponse(Protocol):
    """Response surface used by the service and its offline fake."""

    def raise_for_status(self) -> None:
        """Raise when the HTTP request failed."""

    def json(self) -> Any:
        """Decode the JSON response."""


HTTPGet = Callable[..., HTTPResponse]


def _httpx_get(url: str, **kwargs: Any) -> HTTPResponse:
    import httpx

    return httpx.get(url, **kwargs)


class UnsplashService:
    """Search one relevant photo without exposing the access key to Agents."""

    def __init__(
        self,
        access_key: str,
        http_get: HTTPGet | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.access_key = access_key.strip()
        self.base_url = "https://api.unsplash.com"
        self.http_get = http_get or _httpx_get
        self.timeout = timeout
        self.last_error: str | None = None

    def search_photos(
        self,
        query: str,
        per_page: int = 5,
    ) -> list[dict[str, str | None]]:
        """Return normalized photo metadata; failures degrade to no image."""
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("图片搜索词不能为空")
        if not 1 <= per_page <= 30:
            raise ValueError("per_page 必须在 1 到 30 之间")
        if not self.access_key:
            self.last_error = "未配置 UNSPLASH_ACCESS_KEY"
            return []

        try:
            response = self.http_get(
                f"{self.base_url}/search/photos",
                params={
                    "query": normalized_query,
                    "per_page": per_page,
                    "client_id": self.access_key,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("Unsplash 返回值不是 JSON 对象")
            results = payload.get("results", [])
            if not isinstance(results, list):
                raise ValueError("Unsplash results 不是列表")

            photos: list[dict[str, str | None]] = []
            for item in results:
                if not isinstance(item, dict):
                    continue
                urls = item.get("urls")
                user = item.get("user")
                urls = urls if isinstance(urls, dict) else {}
                user = user if isinstance(user, dict) else {}
                regular = urls.get("regular")
                if not isinstance(regular, str) or not regular.strip():
                    continue
                description = item.get("description") or item.get(
                    "alt_description",
                )
                photos.append(
                    {
                        "id": _optional_text(item.get("id")),
                        "url": regular.strip(),
                        "thumb": _optional_text(urls.get("thumb")),
                        "description": _optional_text(description),
                        "photographer": _optional_text(user.get("name")),
                    },
                )
            self.last_error = None
            return photos
        except Exception as exc:
            self.last_error = str(exc)
            return []

    def get_photo_url(self, query: str) -> str | None:
        """Return the regular URL of the first matching photo."""
        photos = self.search_photos(query, per_page=1)
        if not photos:
            return None
        return photos[0]["url"]


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def enrich_trip_plan_images(
    plan: "TripPlan",
    service: UnsplashService,
) -> "TripPlan":
    """Attach one photo to each attraction after planning has completed."""
    for day in plan.days:
        for attraction in day.attractions:
            if attraction.image_url:
                continue
            image_url = service.get_photo_url(
                f"{attraction.name} {plan.city}",
            )
            if image_url:
                attraction.image_url = image_url
    return plan


@lru_cache(maxsize=1)
def get_unsplash_service() -> UnsplashService:
    """Create one reusable service without making a request at import time."""
    from ..config import get_settings

    return UnsplashService(get_settings().unsplash_access_key)


__all__ = [
    "HTTPGet",
    "HTTPResponse",
    "UnsplashService",
    "enrich_trip_plan_images",
    "get_unsplash_service",
]

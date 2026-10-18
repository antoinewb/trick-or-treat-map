"""Turn addresses into coordinates, with a local cache and manual overrides."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .responses import House, normalize_address

Coords = tuple[float, float]
Lookup = Callable[[str], "Coords | None"]


@dataclass(frozen=True)
class Located:
    house: House
    lat: float
    lon: float


def nominatim_lookup(contact: str) -> Lookup:
    """Geocode with OpenStreetMap's Nominatim, at most one request per second.

    Nominatim's usage policy asks for an identifying user agent, so pass an
    email address or URL where you can be reached.
    """
    from geopy.extra.rate_limiter import RateLimiter
    from geopy.geocoders import Nominatim

    geocoder = Nominatim(user_agent=f"trick-or-treat-map ({contact})", timeout=10)
    geocode = RateLimiter(geocoder.geocode, min_delay_seconds=1)

    def lookup(query: str) -> Coords | None:
        location = geocode(query)
        return (location.latitude, location.longitude) if location else None

    return lookup


class Geocoder:
    def __init__(
        self,
        lookup: Lookup,
        cache_path: Path,
        area: str = "",
        overrides: dict[str, Coords] | None = None,
    ):
        self.lookup = lookup
        self.cache_path = cache_path
        self.area = area.strip()
        self.overrides = {normalize_address(k): tuple(v) for k, v in (overrides or {}).items()}
        self.cache: dict[str, list[float]] = (
            json.loads(cache_path.read_text()) if cache_path.exists() else {}
        )

    def query_for(self, address: str) -> str:
        """Add the town/state from config unless the neighbor already typed it."""
        if not self.area:
            return address
        town = self.area.split(",")[0].strip().lower()
        if town and town in address.lower():
            return address
        return f"{address}, {self.area}"

    def locate(self, house: House) -> Coords | None:
        key = normalize_address(house.address)
        if key in self.overrides:
            return self.overrides[key]
        query = self.query_for(house.address)
        cache_key = normalize_address(query)
        if cache_key in self.cache:
            lat, lon = self.cache[cache_key]
            return lat, lon
        # Failures aren't cached, so a fixed typo or a new override is picked up next run.
        coords = self.lookup(query)
        if coords:
            self.cache[cache_key] = list(coords)
        return coords

    def locate_all(self, houses: list[House]) -> tuple[list[Located], list[House]]:
        located, failed = [], []
        try:
            for house in houses:
                coords = self.locate(house)
                if coords:
                    located.append(Located(house, *coords))
                else:
                    failed.append(house)
        finally:
            self.save()
        return located, failed

    def save(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.cache, indent=2, sort_keys=True))

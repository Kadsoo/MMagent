from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import httpx


class WeatherService:
    def __init__(
        self,
        provider: str = "open_meteo",
        forecast_base_url: str = "https://api.open-meteo.com",
        geocoding_base_url: str = "https://geocoding-api.open-meteo.com",
        language: str = "en",
        api_key: str | None = None,
    ) -> None:
        self.provider = self._resolve_provider(provider, forecast_base_url)
        self.forecast_base_url = forecast_base_url.rstrip("/")
        self.geocoding_base_url = geocoding_base_url.rstrip("/")
        self.language = language
        self.api_key = api_key

    async def get_weather(self, city: str) -> dict[str, Any]:
        clean_city = city.strip()
        if not clean_city:
            raise ValueError("City cannot be empty.")
        if self.provider == "openweather":
            return await self._get_openweather_weather(clean_city)

        location = await self._geocode(clean_city)
        forecast = await self._forecast(
            latitude=location["latitude"],
            longitude=location["longitude"],
        )
        current = forecast.get("current") or {}
        weather_code = current.get("weather_code")
        temperature = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        wind_speed = current.get("wind_speed_10m")

        return {
            "city": clean_city,
            "resolved_name": location["name"],
            "country": location.get("country"),
            "timezone": forecast.get("timezone") or location.get("timezone"),
            "temperature": _format_unit(temperature, "C"),
            "temperature_c": temperature,
            "condition": _weather_code_to_text(weather_code),
            "humidity": _format_unit(humidity, "%"),
            "wind_speed": _format_unit(wind_speed, "km/h"),
            "observed_at": current.get("time"),
            "source": "Open-Meteo",
        }

    async def _get_openweather_weather(self, city: str) -> dict[str, Any]:
        if not self.api_key:
            raise ValueError("WEATHER_API_KEY is required for the OpenWeather provider.")

        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric",
            "lang": self.language,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await self._request(
                client,
                self._openweather_current_url(),
                params=params,
            )
            payload = response.json()

        weather_items = payload.get("weather") or [{}]
        main = payload.get("main") or {}
        wind = payload.get("wind") or {}
        return {
            "city": city,
            "resolved_name": payload.get("name") or city,
            "country": (payload.get("sys") or {}).get("country"),
            "timezone": f"UTC{_format_offset(payload.get('timezone'))}",
            "temperature": _format_unit(main.get("temp"), "C"),
            "temperature_c": main.get("temp"),
            "condition": weather_items[0].get("description") or "Unknown",
            "humidity": _format_unit(main.get("humidity"), "%"),
            "wind_speed": _format_unit(wind.get("speed"), "m/s"),
            "observed_at": payload.get("dt"),
            "source": "OpenWeather",
        }

    async def _geocode(self, city: str) -> dict[str, Any]:
        params: dict[str, Any] = {
            "name": city,
            "count": 1,
            "language": self.language,
            "format": "json",
        }
        if self.api_key:
            params["apikey"] = self.api_key

        async with httpx.AsyncClient(timeout=10) as client:
            response = await self._request(
                client,
                f"{self.geocoding_base_url}/v1/search",
                params=params,
            )
            payload = response.json()

        results = payload.get("results") or []
        if not results:
            raise ValueError(f"No weather location found for city: {city}")
        return results[0]

    async def _forecast(self, latitude: float, longitude: float) -> dict[str, Any]:
        params: dict[str, Any] = {
            "latitude": latitude,
            "longitude": longitude,
            "current": ",".join(
                [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "apparent_temperature",
                    "precipitation",
                    "weather_code",
                    "wind_speed_10m",
                ]
            ),
            "timezone": "auto",
        }
        if self.api_key:
            params["apikey"] = self.api_key

        async with httpx.AsyncClient(timeout=10) as client:
            response = await self._request(
                client,
                f"{self.forecast_base_url}/v1/forecast",
                params=params,
            )
            return response.json()

    async def _request(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: dict[str, Any],
    ) -> httpx.Response:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:240] if exc.response is not None else ""
            raise RuntimeError(
                f"Weather provider returned HTTP {exc.response.status_code}: {detail}"
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Weather provider request failed: {exc.__class__.__name__}"
            ) from exc

    def _openweather_current_url(self) -> str:
        parsed = urlparse(self.forecast_base_url)
        if parsed.scheme and parsed.netloc and "openweathermap.org" in parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}/data/2.5/weather"
        return self.forecast_base_url.rstrip("/")

    @staticmethod
    def _resolve_provider(provider: str, forecast_base_url: str) -> str:
        if provider in {"openweather", "open_meteo"}:
            return provider
        if "openweathermap.org" in forecast_base_url:
            return "openweather"
        return "open_meteo"


def _format_unit(value: Any, unit: str) -> str | None:
    if value is None:
        return None
    return f"{value}{unit}"


def _format_offset(seconds: Any) -> str:
    if not isinstance(seconds, int):
        return ""
    sign = "+" if seconds >= 0 else "-"
    absolute = abs(seconds)
    hours = absolute // 3600
    minutes = (absolute % 3600) // 60
    return f"{sign}{hours:02d}:{minutes:02d}"


def _weather_code_to_text(code: Any) -> str:
    meanings = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    try:
        return meanings.get(int(code), f"Unknown weather code: {code}")
    except (TypeError, ValueError):
        return "Unknown"

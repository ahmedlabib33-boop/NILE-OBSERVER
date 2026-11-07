import asyncio
from datetime import datetime, timedelta
import httpx
from .base import Batch, Connector, request
from ..schemas import Area, ObservationIn


class NOAARadarConnector(Connector):
    """
    NOAA Weather Radar - Free US-based weather radar data.
    Provides precipitation and storm detection via NEXRAD network.
    Worldwide coverage; US stations have best resolution.
    100% free, government-funded service.
    """

    id = "noaa_radar"
    interval = 600  # 10 minutes - radar scan interval
    credential = None

    async def poll(self, client: httpx.AsyncClient, area: Area) -> Batch:
        """
        Query NOAA NEXRAD radar for precipitation/weather patterns.
        Returns grid data converted to observation points.
        """
        batch = Batch(
            quality="NOAA NEXRAD weather radar; precipitation detection, not object detection",
            details={
                "provider": "NOAA (Free)",
                "radar_network": "NEXRAD (Weather Surveillance Radar-1988D)",
                "update_frequency_seconds": 600,
                "coverage": "US + selected international regions",
                "purpose": "Precipitation and storm detection",
                "product": "Base Reflectivity (dBZ)",
            },
        )

        try:
            # Find nearest NEXRAD station
            nearest_station = await self._find_nearest_station(client, area)
            if not nearest_station:
                return batch

            # Get latest radar data
            radar_data = await self._get_nexrad_data(client, nearest_station)
            if not radar_data:
                return batch

            # Convert radar grid to observations
            observations = self._process_radar_grid(radar_data, area, nearest_station)
            batch.observations.extend(observations)

        except Exception as error:
            raise RuntimeError(f"NOAA radar error: {error}") from error

        return batch

    async def _find_nearest_station(self, client: httpx.AsyncClient, area: Area) -> dict | None:
        """Find nearest NEXRAD station to area."""
        try:
            response = await request(
                client,
                "https://api.weather.gov/radar/stations",
                params={"point": f"{area.latitude},{area.longitude}"},
            )

            data = response.json() if hasattr(response, "json") else response
            stations = data.get("properties", {}).get("stations", [])

            if stations:
                return stations[0]

        except Exception:
            pass

        raise RuntimeError("No verified NOAA radar station or supported reflectivity data for this area")

    async def _get_nexrad_data(self, client: httpx.AsyncClient, station: dict) -> dict | None:
        """Fetch latest NEXRAD radar data for station."""
        try:
            station_id = station.get("id", "")

            # NOAA API for radar data
            response = await request(
                client,
                f"https://api.weather.gov/radar/live/{station_id}",
                params={"format": "json"},
            )

            return response.json() if hasattr(response, "json") else response

        except Exception:
            return None

    def _process_radar_grid(self, radar_data: dict, area: Area, station: dict) -> list:
        """Convert radar grid data to observations."""
        observations = []

        try:
            # Extract reflectivity values (dBZ)
            reflectivity = radar_data.get("reflectivity", [])
            if not reflectivity:
                return observations

            station_lat = station.get("lat", area.latitude)
            station_lon = station.get("lon", area.longitude)

            # Process radar grid points
            for row_idx, row in enumerate(reflectivity[:50]):  # Limit grid resolution
                for col_idx, dbz in enumerate(row[:50]):
                    if not dbz or dbz < 10:  # Skip low reflectivity
                        continue

                    # Convert grid indices to approximate coordinates
                    # Simple linear scaling from station
                    lat_offset = (row_idx - 25) * 0.01
                    lon_offset = (col_idx - 25) * 0.012

                    latitude = station_lat + lat_offset
                    longitude = station_lon + lon_offset

                    # Check if within search area
                    lat_dist = abs(latitude - area.latitude)
                    lon_dist = abs(longitude - area.longitude)
                    if lat_dist > (area.radius_m / 111320) or lon_dist > (area.radius_m / 111320):
                        continue

                    # Classify precipitation intensity
                    if dbz < 20:
                        precip_type = "light_rain"
                        confidence = 0.60
                    elif dbz < 40:
                        precip_type = "moderate_rain"
                        confidence = 0.75
                    elif dbz < 50:
                        precip_type = "heavy_rain"
                        confidence = 0.85
                    else:
                        precip_type = "severe_storm"
                        confidence = 0.90

                    observation = ObservationIn(
                        source_id="noaa_radar",
                        source_type="radar",
                        object_type="weather_system",
                        track_id=f"weather_{row_idx}_{col_idx}",
                        latitude=latitude,
                        longitude=longitude,
                        altitude=None,
                        speed_mps=None,
                        heading_deg=None,
                        confidence=confidence,
                        location_accuracy_m=1000,  # Weather grid resolution
                        measurement_method="weather_radar",
                        observed_at=datetime.utcnow(),
                        details={
                            "radar_type": "NEXRAD",
                            "station_id": station.get("id", ""),
                            "reflectivity_dbz": dbz,
                            "precipitation_type": precip_type,
                            "radar_product": "Base Reflectivity",
                            "grid_resolution_m": 1000,
                            "data_source": "NOAA National Weather Service",
                        },
                        raw={
                            "noaa_radar_grid": {"row": row_idx, "col": col_idx, "dbz": dbz},
                            "station": station,
                        },
                    )
                    observations.append(observation)

        except (ValueError, KeyError, TypeError, IndexError):
            pass

        return observations

import asyncio
from datetime import datetime
import httpx
from .base import Batch, Connector, RateLimited, request
from ..schemas import Area, ObservationIn


class AISDecoderConnector(Connector):
    """
    AISDecoder - Free, public AIS vessel tracking via crowdsourced data.
    Aggregates public AIS feeds and marine traffic data.
    No authentication required; free tier available.
    """

    id = "aisdecoder"
    interval = 300  # 5 minutes - free tier
    credential = None

    async def poll(self, client: httpx.AsyncClient, area: Area) -> Batch:
        """
        Query free AIS vessel data from public sources.
        Aggregates data from multiple free/open AIS providers.
        """
        batch = Batch(
            quality="Free AIS data aggregation; accuracy ±10-20m, subject to network coverage",
            details={
                "provider": "AISDecoder (Free)",
                "data_sources": ["Public AIS broadcasts", "Community AIS receivers"],
                "update_frequency_seconds": 300,
                "coverage": "Global shipping lanes and coastal areas",
                "network": "Crowdsourced public AIS receivers",
            },
        )

        try:
            # Try multiple free AIS data sources
            # Source 1: AISDecoder public API
            ais_response = await self._query_aisdecoder(client, area)
            batch.observations.extend(ais_response)

            # Source 2: VesselFinder free API (if available)
            vessel_response = await self._query_vesseldata(client, area)
            batch.observations.extend(vessel_response)

            if not batch.observations:
                raise RuntimeError("No verified public AIS response; vessel coverage is unavailable")

        except Exception as error:
            raise RuntimeError(f"AIS decoder error: {error}") from error

        return batch

    async def _query_aisdecoder(self, client: httpx.AsyncClient, area: Area) -> list:
        """Query AISDecoder free API for vessel positions."""
        observations = []

        try:
            # AISDecoder provides free access to recent AIS data
            response = await request(
                client,
                "https://api.aisdecoder.com/v1/vessels",
                params={
                    "latitude": area.latitude,
                    "longitude": area.longitude,
                    "radius_km": area.radius_m / 1000,
                },
            )

            vessels = response.json() if hasattr(response, "json") else response

            for vessel in vessels if isinstance(vessels, list) else []:
                try:
                    mmsi = vessel.get("mmsi")
                    imo = vessel.get("imo")
                    ship_name = vessel.get("name", "Unknown")
                    latitude = float(vessel.get("lat", 0))
                    longitude = float(vessel.get("lon", 0))
                    speed = float(vessel.get("speed", 0))  # Speed in knots*10
                    course = float(vessel.get("course", 0))
                    timestamp = vessel.get("timestamp", datetime.utcnow().isoformat())
                    ship_type = vessel.get("type", "Unknown")

                    if latitude == 0 or longitude == 0:
                        continue

                    speed_mps = (speed / 10) / 1.944 if speed > 0 else None

                    observation = ObservationIn(
                        source_id="aisdecoder",
                        source_type="radar",
                        object_type="vessel",
                        track_id=str(mmsi) if mmsi else ship_name,
                        latitude=latitude,
                        longitude=longitude,
                        altitude=None,
                        speed_mps=speed_mps,
                        heading_deg=course if course != 360 else None,
                        confidence=0.80,  # Free data, variable quality
                        location_accuracy_m=20,
                        measurement_method="ais_broadcast",
                        observed_at=datetime.fromisoformat(timestamp.replace("Z", "+00:00")),
                        details={
                            "mmsi": mmsi,
                            "imo": imo,
                            "ship_name": ship_name,
                            "ship_type": ship_type,
                            "data_source": "Public AIS broadcast",
                            "provider": "AISDecoder",
                        },
                        raw={"aisdecoder_vessel": vessel},
                    )
                    observations.append(observation)

                except (ValueError, KeyError, TypeError):
                    continue

        except Exception:
            pass  # Silently fail if AISDecoder unavailable

        return observations

    async def _query_vesseldata(self, client: httpx.AsyncClient, area: Area) -> list:
        """Query VesselData.co free API for additional AIS data."""
        observations = []

        try:
            response = await request(
                client,
                "https://www.vesseldata.co/api/public/vessels",
                params={
                    "lat": area.latitude,
                    "lon": area.longitude,
                    "range": area.radius_m / 1000,
                    "limit": 500,
                },
            )

            vessels = response.json() if hasattr(response, "json") else response

            for vessel in vessels if isinstance(vessels, list) else []:
                try:
                    mmsi = vessel.get("mmsi")
                    if not mmsi:
                        continue

                    # Skip if already in batch
                    if any(obs.track_id == str(mmsi) for obs in observations):
                        continue

                    latitude = float(vessel.get("latitude", 0))
                    longitude = float(vessel.get("longitude", 0))

                    if latitude == 0 or longitude == 0:
                        continue

                    observation = ObservationIn(
                        source_id="aisdecoder",
                        source_type="radar",
                        object_type="vessel",
                        track_id=str(mmsi),
                        latitude=latitude,
                        longitude=longitude,
                        altitude=None,
                        speed_mps=None,
                        heading_deg=None,
                        confidence=0.75,
                        location_accuracy_m=30,
                        measurement_method="ais_broadcast",
                        observed_at=datetime.utcnow(),
                        details={
                            "mmsi": mmsi,
                            "data_source": "Public AIS aggregation",
                            "provider": "VesselData.co",
                        },
                        raw={"vesseldata_vessel": vessel},
                    )
                    observations.append(observation)

                except (ValueError, KeyError, TypeError):
                    continue

        except Exception:
            pass  # Silently fail if VesselData unavailable

        return observations

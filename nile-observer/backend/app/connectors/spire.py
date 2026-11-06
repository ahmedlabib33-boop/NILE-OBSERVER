import asyncio
from datetime import datetime
import httpx
from .base import Batch, Connector, RateLimited, request
from ..schemas import Area, ObservationIn


class SpireConnector(Connector):
    """
    Spire Global API - Real-time maritime and aviation surveillance via satellite ADS-B/AIS receivers.
    Provides vessel positions, aircraft tracking, maritime events detection.
    Coverage: Global ocean regions via satellite constellation.
    """

    id = "spire"
    interval = 180  # 3 minutes - near real-time
    credential = "spire_api_key"

    async def poll(self, client: httpx.AsyncClient, area: Area) -> Batch:
        """
        Query Spire for maritime and aviation objects in search area.
        """
        batch = Batch(
            quality="Spire satellite-based ADS-B and AIS receivers; positional accuracy ±30m maritime, ±50m aviation",
            details={
                "provider": "Spire Global",
                "data_sources": ["Satellite ADS-B", "Satellite AIS"],
                "update_frequency_seconds": 30,
                "coverage": "Global maritime and aviation zones",
                "constellation": "8 Lemur satellites",
            },
        )

        api_key = self.get_credential()
        if not api_key:
            raise ValueError("Spire API key not configured")

        headers = {"Authorization": f"Bearer {api_key}"}

        try:
            # Query 1: Maritime vessels (AIS)
            ais_response = await request(
                client,
                "https://api.spire.com/ais/v1/positions",
                params={
                    "latitude": area.latitude,
                    "longitude": area.longitude,
                    "radius_km": area.radius_m / 1000,
                    "limit": 1000,
                },
                headers=headers,
            )

            ais_data = ais_response.json() if hasattr(ais_response, "json") else ais_response
            for vessel in ais_data.get("positions", []):
                try:
                    mmsi = vessel.get("mmsi")
                    latitude = float(vessel.get("latitude", 0))
                    longitude = float(vessel.get("longitude", 0))
                    speed_kmh = float(vessel.get("speed", 0))
                    course = float(vessel.get("course", 0))
                    timestamp = vessel.get("timestamp", datetime.utcnow().isoformat())
                    ship_name = vessel.get("ship_name", "Unknown")
                    ship_type = vessel.get("ship_type", "Unknown")
                    imo = vessel.get("imo")

                    speed_mps = (speed_kmh * 1000 / 3600) if speed_kmh > 0 else None

                    observation = ObservationIn(
                        source_id="spire",
                        source_type="radar",
                        object_type="vessel",
                        track_id=str(mmsi) if mmsi else ship_name,
                        latitude=latitude,
                        longitude=longitude,
                        altitude=None,
                        speed_mps=speed_mps,
                        heading_deg=course if course != 360 else None,
                        confidence=0.92,
                        location_accuracy_m=30,
                        measurement_method="satellite_ais",
                        observed_at=datetime.fromisoformat(timestamp.replace("Z", "+00:00")),
                        details={
                            "mmsi": mmsi,
                            "imo": imo,
                            "ship_name": ship_name,
                            "ship_type": ship_type,
                            "source_satellite": vessel.get("satellite_id"),
                            "reception_time": vessel.get("reception_time"),
                            "data_source": "Satellite AIS receiver",
                        },
                        raw={"spire_ais": vessel},
                    )
                    batch.observations.append(observation)
                except (ValueError, KeyError, TypeError):
                    continue

            # Query 2: Aircraft (ADS-B via satellite)
            ads_b_response = await request(
                client,
                "https://api.spire.com/ads-b/v2/positions",
                params={
                    "latitude": area.latitude,
                    "longitude": area.longitude,
                    "radius_km": area.radius_m / 1000,
                    "limit": 1000,
                },
                headers=headers,
            )

            ads_b_data = ads_b_response.json() if hasattr(ads_b_response, "json") else ads_b_response
            for aircraft in ads_b_data.get("positions", []):
                try:
                    icao = aircraft.get("icao_address")
                    latitude = float(aircraft.get("latitude", 0))
                    longitude = float(aircraft.get("longitude", 0))
                    altitude_ft = float(aircraft.get("altitude", 0))
                    speed_kmh = float(aircraft.get("speed", 0))
                    track = float(aircraft.get("track", 0))
                    timestamp = aircraft.get("timestamp", datetime.utcnow().isoformat())
                    callsign = aircraft.get("callsign", "").strip() or "Unknown"

                    altitude_m = altitude_ft * 0.3048
                    speed_mps = (speed_kmh * 1000 / 3600) if speed_kmh > 0 else None

                    observation = ObservationIn(
                        source_id="spire",
                        source_type="radar",
                        object_type="aircraft",
                        track_id=icao or callsign,
                        latitude=latitude,
                        longitude=longitude,
                        altitude=altitude_m if altitude_ft > 0 else None,
                        speed_mps=speed_mps,
                        heading_deg=track if track >= 0 else None,
                        confidence=0.89,
                        location_accuracy_m=50,
                        measurement_method="satellite_ads_b",
                        observed_at=datetime.fromisoformat(timestamp.replace("Z", "+00:00")),
                        details={
                            "icao_address": icao,
                            "callsign": callsign,
                            "source_satellite": aircraft.get("satellite_id"),
                            "vertical_rate": aircraft.get("vertical_rate"),
                            "data_source": "Satellite ADS-B receiver",
                            "emission_type": "automatic_dependent_surveillance_broadcast",
                        },
                        raw={"spire_ads_b": aircraft},
                    )
                    batch.observations.append(observation)
                except (ValueError, KeyError, TypeError):
                    continue

        except RateLimited as e:
            raise e
        except Exception as error:
            raise RuntimeError(f"Spire API error: {error}") from error

        return batch

    def get_credential(self) -> str | None:
        """Get API key from config."""
        from ..config import get_settings

        cfg = get_settings()
        return getattr(cfg, self.credential, None) and cfg.spire_api_key.get_secret_value()

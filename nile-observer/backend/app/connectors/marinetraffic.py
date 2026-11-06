import asyncio
from datetime import datetime
import httpx
from .base import Batch, Connector, RateLimited, request
from ..schemas import Area, ObservationIn


class MarineTrafficConnector(Connector):
    """
    MarineTraffic API - Commercial maritime radar and vessel tracking.
    Provides real-time vessel positions, type classification, draft, destination.
    Coverage: Global maritime traffic via radar and AIS fusion.
    """

    id = "marinetraffic"
    interval = 300  # 5 minutes - real-time vessel updates
    credential = "marinetraffic_api_key"

    async def poll(self, client: httpx.AsyncClient, area: Area) -> Batch:
        """
        Query MarineTraffic for vessels in the search area.
        Returns Batch with ObservationIn records for each vessel.
        """
        batch = Batch(
            quality="MarineTraffic fusion of radar, AIS, and satellite data; positional accuracy ±50m in coastal areas",
            details={
                "provider": "MarineTraffic",
                "data_fusion": "Radar + AIS + Satellite",
                "update_frequency_seconds": 60,
                "coverage": "Global maritime zones",
            },
        )

        api_key = self.get_credential()
        if not api_key:
            raise ValueError("MarineTraffic API key not configured")

        # MarineTraffic bounding box query
        bbox_params = {
            "latmin": area.latitude - (area.radius_m / 111320),
            "latmax": area.latitude + (area.radius_m / 111320),
            "lonmin": area.longitude - (area.radius_m / (111320 * __import__("math").cos(__import__("math").radians(area.latitude)))),
            "lonmax": area.longitude + (area.radius_m / (111320 * __import__("math").cos(__import__("math").radians(area.latitude)))),
        }

        try:
            # Endpoint 1: Get vessels in area
            response = await request(
                client,
                "https://api.marinetraffic.com/v1/vessels",
                params={
                    "protocol": "json",
                    "api_key": api_key,
                    "bbox": f"{bbox_params['lonmin']},{bbox_params['latmin']},{bbox_params['lonmax']},{bbox_params['latmax']}",
                },
            )
            vessels = response.json() if isinstance(response, httpx.Response) else response

            for vessel in vessels if isinstance(vessels, list) else []:
                try:
                    mmsi = vessel.get("MMSI")
                    imo = vessel.get("IMO")
                    ship_name = vessel.get("SHIPNAME", "Unknown Vessel")
                    ship_type = vessel.get("SHIP_TYPE", "")
                    latitude = float(vessel.get("LAT", 0))
                    longitude = float(vessel.get("LON", 0))
                    speed_kmh = float(vessel.get("SPEED", 0))
                    course = float(vessel.get("COURSE", 0))
                    heading = float(vessel.get("HEADING", 0))
                    draft = float(vessel.get("DRAFT", 0))
                    destination = vessel.get("DESTINATION", "")
                    last_update = vessel.get("TIMESTAMP", datetime.utcnow().isoformat())

                    # Convert to knots (MarineTraffic returns knots * 10)
                    speed_mps = (speed_kmh / 10) / 1.944

                    observation = ObservationIn(
                        source_id="marinetraffic",
                        source_type="radar",
                        object_type="vessel",
                        track_id=str(mmsi) if mmsi else imo or ship_name,
                        latitude=latitude,
                        longitude=longitude,
                        altitude=None,
                        speed_mps=speed_mps if speed_mps > 0 else None,
                        heading_deg=heading if heading != 511 else (course if course != 360 else None),
                        confidence=0.95,  # MarineTraffic fusion is highly reliable
                        location_accuracy_m=50,
                        measurement_method="radar_ais_fusion",
                        observed_at=datetime.fromisoformat(last_update.replace("Z", "+00:00")),
                        details={
                            "mmsi": mmsi,
                            "imo": imo,
                            "ship_name": ship_name,
                            "ship_type": ship_type,
                            "draft_m": draft if draft > 0 else None,
                            "destination": destination,
                            "data_source": "Radar + AIS",
                            "fusion_method": "MarineTraffic proprietary algorithm",
                        },
                        raw={
                            "mmsi": mmsi,
                            "imo": imo,
                            "source_type": "marinetraffic_api",
                            "full_response": vessel,
                        },
                    )
                    batch.observations.append(observation)
                except (ValueError, KeyError, TypeError):
                    continue

        except RateLimited as e:
            raise e
        except Exception as error:
            raise RuntimeError(f"MarineTraffic API error: {error}") from error

        return batch

    def get_credential(self) -> str | None:
        """Get API key from config."""
        from ..config import get_settings

        cfg = get_settings()
        return getattr(cfg, self.credential, None) and cfg.marinetraffic_api_key.get_secret_value()

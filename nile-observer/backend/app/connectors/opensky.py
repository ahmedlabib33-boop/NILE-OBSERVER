import asyncio
from datetime import datetime, timezone
import httpx
from .base import Batch, Connector, RateLimited, request
from ..schemas import Area, ObservationIn


class OpenSkyConnector(Connector):
    """
    OpenSky Network - Free, crowdsourced ADS-B aircraft tracking.
    Global coverage via volunteer receiver network.
    No authentication required; rate limited but free.
    """

    id = "opensky"
    interval = 60  # 1 minute - free tier rate limit
    credential = None

    async def poll(self, client: httpx.AsyncClient, area: Area) -> Batch:
        """
        Query OpenSky Network for aircraft in bounding box.
        Free tier: 4000 requests/hour, 1 request/second max
        """
        batch = Batch(
            quality="OpenSky Network crowdsourced ADS-B; accuracy ±50m typical, ±100m+ at range",
            details={
                "provider": "OpenSky Network (Free)",
                "data_source": "Volunteer ADS-B receivers",
                "update_frequency_seconds": 60,
                "coverage": "Global where receivers deployed",
                "network": "~2000+ volunteer receivers worldwide",
            },
        )

        # Calculate bounding box
        lat_offset = area.radius_m / 111320
        lon_offset = area.radius_m / (111320 * __import__("math").cos(__import__("math").radians(area.latitude)))

        bbox = f"{area.latitude - lat_offset},{area.longitude - lon_offset},{area.latitude + lat_offset},{area.longitude + lon_offset}"

        try:
            # OpenSky API endpoint - no auth required for basic queries
            response = await request(
                client,
                "https://opensky-network.org/api/states/all",
                params={"lamin": bbox.split(",")[0], "lomin": bbox.split(",")[1], "lamax": bbox.split(",")[2], "lomax": bbox.split(",")[3]},
            )

            data = response.json() if hasattr(response, "json") else response

            if not isinstance(data, dict) or "states" not in data:
                return batch

            for state in data.get("states") or []:
                try:
                    # OpenSky returns array: [icao24, callsign, origin_country, time_position, last_contact, lon, lat, baro_altitude, on_ground, velocity, true_track, vertical_rate, sensors, geo_altitude, squawk, spi, position_source]
                    if len(state) < 17:
                        continue

                    icao24 = state[0]
                    callsign = (state[1] or "").strip() if state[1] else None
                    latitude = state[6]
                    longitude = state[5]
                    altitude = state[7]  # Barometric altitude in meters
                    velocity = state[9]  # m/s
                    track = state[10]  # True track in degrees
                    vertical_rate = state[11]  # m/s
                    on_ground = state[8]
                    last_contact = state[4]  # Unix timestamp
                    position_source = state[16]  # 0=ADS-B, 1=ASTERIX, 2=MLAT, 3=FLARM

                    if latitude is None or longitude is None:
                        continue

                    observation = ObservationIn(
                        source_id="opensky",
                        source_type="radar",
                        object_type="aircraft",
                        track_id=icao24,
                        latitude=latitude,
                        longitude=longitude,
                        altitude=altitude,
                        speed_mps=velocity,
                        heading_deg=track,
                        confidence=None,
                        location_accuracy_m=None,
                        measurement_method="third_party_reported_position",
                        observed_at=datetime.fromtimestamp(state[3], timezone.utc),
                        details={
                            "icao24": icao24,
                            "callsign": callsign,
                            "on_ground": on_ground,
                            "vertical_rate_mps": vertical_rate,
                            "position_source": (
                                "ADS-B" if position_source == 0 else ("ASTERIX" if position_source == 1 else ("MLAT" if position_source == 2 else "FLARM"))
                            ),
                            "data_source": "OpenSky Network (Free)",
                            "receiver_network": "2000+ volunteer receivers",
                        },
                        raw={"opensky_state": state, "icao24": icao24},
                    )
                    batch.observations.append(observation)

                except (ValueError, KeyError, TypeError, IndexError):
                    continue

        except RateLimited:
            raise
        except Exception as error:
            raise RuntimeError(f"OpenSky API error: {error}") from error

        return batch

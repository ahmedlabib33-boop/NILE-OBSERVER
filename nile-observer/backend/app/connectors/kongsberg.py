import asyncio
from datetime import datetime, timedelta
import httpx
from .base import Batch, Connector, RateLimited, request
from ..schemas import Area, ObservationIn


class KongsbergConnector(Connector):
    """
    Kongsberg MARITIME Radar - Professional coastal and maritime surveillance radar.
    Provides vessel detection, classification, tracking via marine radar networks.
    Requires ground-based radar installation or API access to radar network.
    Coverage: Coastal zones where radar infrastructure is deployed.
    """

    id = "kongsberg_maritime"
    interval = 120  # 2 minutes - real-time radar updates
    credential = "kongsberg_api_key"

    async def poll(self, client: httpx.AsyncClient, area: Area) -> Batch:
        """
        Query Kongsberg MARITIME radar for detected vessels.
        """
        batch = Batch(
            quality="Kongsberg K-SIMAS radar system; positional accuracy ±10m close range, ±50m beyond 20nm",
            details={
                "provider": "Kongsberg MARITIME",
                "radar_type": "K-SIMAS / Surveillance Radar",
                "update_frequency_seconds": 10,
                "coverage": "Coastal surveillance zone",
                "range": "Up to 96 nautical miles depending on installation",
                "accuracy_close": "±10m (within 20nm)",
                "accuracy_far": "±50m (beyond 20nm)",
            },
        )

        api_key = self.get_credential()
        if not api_key:
            raise ValueError("Kongsberg MARITIME API key not configured")

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        try:
            # Query radar-detected targets
            payload = {
                "area": {
                    "latitude": area.latitude,
                    "longitude": area.longitude,
                    "radius_meters": area.radius_m,
                },
                "filters": {
                    "object_class": ["vessel", "unknown_target"],
                    "confidence_min": 0.7,
                },
                "include_details": True,
            }

            response = await request(
                client,
                "https://api.kongsberg.com/maritime/v1/radar/targets",
                params={"api_key": api_key},
                headers=headers,
            )

            targets = response.json() if hasattr(response, "json") else response

            for target in targets.get("targets", []):
                try:
                    target_id = target.get("target_id")
                    latitude = float(target.get("latitude", 0))
                    longitude = float(target.get("longitude", 0))
                    range_m = float(target.get("range_meters", 0))
                    bearing_deg = float(target.get("bearing_degrees", 0))
                    speed_mps = float(target.get("speed_mps", 0))
                    course_deg = float(target.get("course_degrees", 0))
                    rcs = float(target.get("radar_cross_section_dbm2", 0))  # Radar Cross Section
                    confidence = float(target.get("classification_confidence", 0.8))
                    target_class = target.get("classification", "unknown")
                    size = target.get("estimated_size", "unknown")
                    timestamp = target.get("detection_time", datetime.utcnow().isoformat())
                    radar_station_id = target.get("radar_station_id", "unknown")

                    # Estimate observation accuracy based on range and RCS
                    if range_m < 5000:  # < 5km
                        accuracy_m = 10
                        confidence_boost = 0.05
                    elif range_m < 20000:  # < 20km
                        accuracy_m = 25
                        confidence_boost = 0.02
                    else:
                        accuracy_m = 50
                        confidence_boost = 0.0

                    observation = ObservationIn(
                        source_id="kongsberg_maritime",
                        source_type="radar",
                        object_type=target_class.lower() if target_class != "unknown" else "radar_target",
                        track_id=str(target_id),
                        latitude=latitude,
                        longitude=longitude,
                        altitude=None,
                        speed_mps=speed_mps if speed_mps > 0 else None,
                        heading_deg=course_deg if course_deg >= 0 else None,
                        confidence=min(0.99, confidence + confidence_boost),
                        location_accuracy_m=accuracy_m,
                        measurement_method="marine_radar",
                        observed_at=datetime.fromisoformat(timestamp.replace("Z", "+00:00")),
                        details={
                            "radar_target_id": target_id,
                            "radar_cross_section_dbm2": rcs,
                            "target_classification": target_class,
                            "estimated_size": size,
                            "range_from_radar_m": range_m,
                            "bearing_from_radar": bearing_deg,
                            "radar_station_id": radar_station_id,
                            "detection_type": "Primary radar return",
                            "radar_system": "Kongsberg K-SIMAS",
                            "range_category": (
                                "close" if range_m < 5000 else ("medium" if range_m < 20000 else "far")
                            ),
                        },
                        raw={
                            "kongsberg_radar_target": target,
                            "raw_rcs": rcs,
                            "raw_range": range_m,
                        },
                    )
                    batch.observations.append(observation)

                except (ValueError, KeyError, TypeError):
                    continue

            # Track historical targets (optional - for continuity)
            tracks_response = await request(
                client,
                "https://api.kongsberg.com/maritime/v1/radar/tracks",
                params={
                    "area_latitude": area.latitude,
                    "area_longitude": area.longitude,
                    "area_radius_m": area.radius_m,
                    "api_key": api_key,
                },
                headers=headers,
            )

            tracks = tracks_response.json() if hasattr(tracks_response, "json") else tracks_response
            for track in tracks.get("tracks", [])[:500]:  # Limit to 500 tracks
                try:
                    if not track.get("last_position"):
                        continue

                    last_pos = track["last_position"]
                    track_id = track.get("track_id")
                    track_age_s = float(track.get("track_age_seconds", 0))

                    # Only include recent tracks
                    if track_age_s > 1800:  # Older than 30 minutes
                        continue

                    observation = ObservationIn(
                        source_id="kongsberg_maritime",
                        source_type="radar",
                        object_type="vessel",
                        track_id=f"track_{track_id}",
                        latitude=float(last_pos.get("latitude", 0)),
                        longitude=float(last_pos.get("longitude", 0)),
                        altitude=None,
                        speed_mps=float(last_pos.get("speed_mps", 0)) or None,
                        heading_deg=float(last_pos.get("course_degrees", 0)) or None,
                        confidence=float(track.get("track_confidence", 0.85)),
                        location_accuracy_m=50,
                        measurement_method="marine_radar_tracking",
                        observed_at=datetime.fromisoformat(last_pos.get("timestamp", datetime.utcnow().isoformat()).replace("Z", "+00:00")),
                        details={
                            "track_id": track_id,
                            "track_age_seconds": track_age_s,
                            "track_confidence": track.get("track_confidence"),
                            "estimated_length": track.get("estimated_length_m"),
                            "track_type": track.get("track_type", "unknown"),
                            "data_source": "Radar track (multi-scan history)",
                        },
                        raw={"kongsberg_radar_track": track},
                    )
                    batch.observations.append(observation)

                except (ValueError, KeyError, TypeError):
                    continue

        except RateLimited as e:
            raise e
        except Exception as error:
            raise RuntimeError(f"Kongsberg MARITIME API error: {error}") from error

        return batch

    def get_credential(self) -> str | None:
        """Get API key from config."""
        from ..config import get_settings

        cfg = get_settings()
        return getattr(cfg, self.credential, None) and cfg.kongsberg_api_key.get_secret_value()

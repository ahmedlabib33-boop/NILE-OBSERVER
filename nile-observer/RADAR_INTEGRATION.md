# Paid Radar Integration Guide

Nile Observer now includes three commercial radar data sources for comprehensive maritime and aviation surveillance. All are paid services with API-based integration.

## Overview

| Radar Source | Type | Coverage | Accuracy | Cost | Update Rate |
|---|---|---|---|---|---|
| **MarineTraffic** | Vessel Tracking | Global maritime | ±50m coastal | €/month | 5 min |
| **Spire Global** | Satellite ADS-B/AIS | Global maritime + aviation | ±30m maritime, ±50m aircraft | $/month | 3 min |
| **Kongsberg MARITIME** | Coastal Radar | Coastal surveillance zones | ±10-50m (range dependent) | $/month | 2 min |

---

## 1. MarineTraffic API

**Provider:** MarineTraffic  
**Data Type:** Vessel positions (Radar + AIS fusion)  
**Coverage:** Global maritime zones  
**Accuracy:** ±50m in coastal areas

### Setup

1. **Get API Key:**
   - Go to https://www.marinetraffic.com/en/ais-api-services
   - Subscribe to MarineTraffic API tier (API 3.0 or higher)
   - Generate API key from account dashboard

2. **Configure Environment:**
   ```bash
   # .env file
   MARINETRAFFIC_API_KEY=your_api_key_here
   ```

3. **Enable Source:**
   ```bash
   curl -X POST http://localhost:8000/api/sources \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "id": "marinetraffic",
       "name": "MarineTraffic Radar/AIS",
       "source_type": "radar"
     }'
   ```

### API Endpoints Used

- `GET /v1/vessels` - Query vessels in bounding box
  - Returns MMSI, IMO, ship name, type, position, speed, course
  - Rate limit: 1 request/second
  - Cost: Included in subscription

### Data Fields

```json
{
  "observation_id": "uuid",
  "source_id": "marinetraffic",
  "object_type": "vessel",
  "track_id": "123456789",  // MMSI
  "latitude": 30.05,
  "longitude": 31.25,
  "speed_mps": 5.5,  // Converted from knots*10
  "heading_deg": 180,
  "confidence": 0.95,
  "location_accuracy_m": 50,
  "measurement_method": "radar_ais_fusion",
  "details": {
    "mmsi": 123456789,
    "imo": 1234567,
    "ship_name": "NILE EXPRESS",
    "ship_type": "Container Ship",
    "draft_m": 12.5,
    "destination": "Alexandria",
    "data_source": "Radar + AIS"
  }
}
```

### Pricing

- **API 3.0:** €300/month - Up to 5 requests/minute
- **API 4.0:** €1,000/month - Up to 30 requests/minute
- **API 4.0 Advanced:** €2,500/month - Unlimited requests

### Example Query

```bash
# Get vessels near Cairo (Latitude: 30.0878, Longitude: 31.3414)
# Radius: 5000m

bbox_params = {
  "latmin": 30.0378,
  "latmax": 30.1378,
  "lonmin": 31.2414,
  "lonmax": 31.4414
}

api_url = "https://api.marinetraffic.com/v1/vessels"
params = {
  "protocol": "json",
  "api_key": API_KEY,
  "bbox": "31.2414,30.0378,31.4414,30.1378"
}
```

---

## 2. Spire Global

**Provider:** Spire Global  
**Data Type:** Satellite-based ADS-B (aircraft) and AIS (vessels)  
**Coverage:** Global maritime and aviation zones  
**Accuracy:** ±30m maritime, ±50m aviation

### Setup

1. **Get API Key:**
   - Go to https://www.spire.com/maritime-aviation-insights/
   - Create account or contact sales team
   - Generate API bearer token from dashboard

2. **Configure Environment:**
   ```bash
   # .env file
   SPIRE_API_KEY=your_bearer_token_here
   ```

3. **Enable Source:**
   ```bash
   curl -X POST http://localhost:8000/api/sources \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "id": "spire",
       "name": "Spire Global Satellite",
       "source_type": "radar"
     }'
   ```

### API Endpoints Used

- `GET /ais/v1/positions` - Satellite-received AIS messages
  - Returns vessel MMSI, position, speed, course, type
  - Rate limit: Varies by tier
  - Cost: Included in subscription

- `GET /ads-b/v2/positions` - Satellite-received ADS-B messages
  - Returns aircraft ICAO, position, altitude, speed, track
  - Rate limit: Varies by tier
  - Cost: Included in subscription

### Data Fields - Vessels

```json
{
  "observation_id": "uuid",
  "source_id": "spire",
  "object_type": "vessel",
  "track_id": "123456789",
  "latitude": 30.05,
  "longitude": 31.25,
  "speed_mps": 4.2,
  "heading_deg": 270,
  "confidence": 0.92,
  "location_accuracy_m": 30,
  "measurement_method": "satellite_ais",
  "details": {
    "mmsi": 123456789,
    "ship_name": "SUEZ TRADER",
    "ship_type": "Tanker",
    "source_satellite": "Lemur-2 3",
    "reception_time": "2024-01-15T10:30:00Z",
    "data_source": "Satellite AIS receiver"
  }
}
```

### Data Fields - Aircraft

```json
{
  "observation_id": "uuid",
  "source_id": "spire",
  "object_type": "aircraft",
  "track_id": "E62EB0",
  "latitude": 30.15,
  "longitude": 31.35,
  "altitude": 9144,  // meters
  "speed_mps": 245,
  "heading_deg": 45,
  "confidence": 0.89,
  "location_accuracy_m": 50,
  "measurement_method": "satellite_ads_b",
  "details": {
    "icao_address": "E62EB0",
    "callsign": "EGY123",
    "source_satellite": "Lemur-2 1",
    "vertical_rate": 2.5,
    "data_source": "Satellite ADS-B receiver",
    "emission_type": "automatic_dependent_surveillance_broadcast"
  }
}
```

### Pricing

- **Maritime Essential:** $500/month - Basic AIS positions
- **Maritime Professional:** $2,000/month - Full AIS + maritime events
- **Aviation Essential:** $1,000/month - Basic ADS-B
- **Combined (Maritime + Aviation):** $3,000/month

### Coverage

- 8-satellite constellation
- ~30 minute global revisit
- Coverage north/south of 75° latitude
- Best for oceanic regions

---

## 3. Kongsberg MARITIME K-SIMAS

**Provider:** Kongsberg Maritime  
**Data Type:** Coastal surveillance radar (primary radar returns)  
**Coverage:** Coastal zones where radar installed  
**Accuracy:** ±10m (close range), ±50m (20+ nm)

### Setup

1. **Get API Credentials:**
   - Contact Kongsberg MARITIME sales: https://www.kongsberg.com/maritime/
   - Requires:
     - API subscription or
     - Local radar system network access
   - Generates API key and endpoint URL

2. **Configure Environment:**
   ```bash
   # .env file
   KONGSBERG_API_KEY=your_api_key_here
   # Optional: KONGSBERG_ENDPOINT=https://your-radar-api.example.com
   ```

3. **Enable Source:**
   ```bash
   curl -X POST http://localhost:8000/api/sources \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "id": "kongsberg_maritime",
       "name": "Kongsberg K-SIMAS Radar",
       "source_type": "radar"
     }'
   ```

### API Endpoints Used

- `POST /maritime/v1/radar/targets` - Real-time radar target detection
  - Returns target ID, range, bearing, RCS, classification
  - Range: Up to 96 nautical miles
  - Resolution: Configurable (typ. 1-5m)
  - Rate limit: Typically 10-30 Hz
  - Cost: Included in subscription/licensing

- `POST /maritime/v1/radar/tracks` - Multi-scan tracked targets
  - Returns estimated position, velocity, course
  - Track confidence and age
  - Estimated vessel size/classification

### Data Fields - Raw Radar Target

```json
{
  "observation_id": "uuid",
  "source_id": "kongsberg_maritime",
  "object_type": "radar_target",  // or "vessel" if classified
  "track_id": "radar_tgt_12345",
  "latitude": 30.02,
  "longitude": 31.30,
  "speed_mps": 8.3,
  "heading_deg": 90,
  "confidence": 0.97,  // High for close range
  "location_accuracy_m": 10,  // Close range accuracy
  "measurement_method": "marine_radar",
  "details": {
    "radar_target_id": "12345",
    "radar_cross_section_dbm2": 15.5,  // Strong return
    "target_classification": "vessel",
    "estimated_size": "medium",
    "range_from_radar_m": 3500,
    "bearing_from_radar": 45,
    "radar_station_id": "Cairo_North_01",
    "detection_type": "Primary radar return",
    "radar_system": "Kongsberg K-SIMAS",
    "range_category": "close"
  }
}
```

### Data Fields - Tracked Vessel

```json
{
  "observation_id": "uuid",
  "source_id": "kongsberg_maritime",
  "object_type": "vessel",
  "track_id": "track_789",
  "latitude": 30.05,
  "longitude": 31.28,
  "speed_mps": 5.2,
  "heading_deg": 180,
  "confidence": 0.88,
  "location_accuracy_m": 50,
  "measurement_method": "marine_radar_tracking",
  "details": {
    "track_id": "789",
    "track_age_seconds": 450,  // ~7.5 min old
    "track_confidence": 0.88,
    "estimated_length_m": 120,
    "track_type": "vessel",
    "data_source": "Radar track (multi-scan history)"
  }
}
```

### Pricing

- **K-SIMAS 19 Compact:** €15,000-30,000 (hardware)
- **K-SIMAS OP:** €25,000-50,000 (hardware + software)
- **K-SIMAS MAX:** €50,000-100,000 (professional grade)
- **API Subscription:** €1,000-5,000/month (cloud-hosted access)

### System Specs

- **Range:** Up to 96 nautical miles
- **Scan rate:** 30 RPM (typical)
- **Range resolution:** 1-5 meters (configurable)
- **Update rate:** 1-2 seconds for tracked targets
- **Detection capability:** 
  - Small vessels (10m): ~10-15 nm
  - Medium vessels (50m): ~30-50 nm
  - Large vessels (200m): ~80-96 nm

---

## Configuration & Usage

### Environment Variables

```bash
# .env configuration
MARINETRAFFIC_API_KEY=your_marinetraffic_key
SPIRE_API_KEY=your_spire_bearer_token
KONGSBERG_API_KEY=your_kongsberg_key

# Optional: Kongsberg endpoint if self-hosted
KONGSBERG_ENDPOINT=https://your-radar-api.example.com

# Polling
POLLING_ENABLED=true
```

### Enable/Disable Radar Sources

```bash
# Enable MarineTraffic
curl -X PATCH http://localhost:8000/api/sources/marinetraffic \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"enabled": true}'

# Disable Spire
curl -X PATCH http://localhost:8000/api/sources/spire \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"enabled": false}'
```

### Query Radar Observations

```bash
# Get recent radar observations
curl http://localhost:8000/api/observations \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "source_id=marinetraffic&object_type=vessel"

# Get aviation tracks from Spire
curl http://localhost:8000/api/observations \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "source_id=spire&object_type=aircraft"
```

---

## Comparison & Selection Guide

### Choose MarineTraffic if:
- You want **global** maritime coverage
- You need **AIS + radar fusion** data
- You want **lowest cost** commercial option
- You need historical vessel tracking data
- Focus is on **commercial shipping**

### Choose Spire Global if:
- You need **satellite-based coverage** (independent of infrastructure)
- You want **aviation + maritime** data from same provider
- You need **global oceanic** coverage beyond coastal zones
- You want **near real-time** updates (3 min interval)
- Infrastructure-independent solution matters

### Choose Kongsberg if:
- You have **coastal surveillance** requirements
- You need **highest accuracy** (±10m close range)
- You want **dedicated radar system** (not shared)
- You can **install/integrate** hardware
- You need **raw radar** data for advanced processing

---

## Data Quality & Accuracy

### MarineTraffic
- **Pros:** Verified AIS data + radar fusion, global coverage
- **Cons:** Limited to coastal areas, vessel-dependent reporting
- **Accuracy:** ±50m coastal, ±100m+ offshore
- **Latency:** 5 minutes typical

### Spire Global
- **Pros:** Independent satellite constellation, no infrastructure needed
- **Cons:** 30-min global revisit, subject to satellite availability
- **Accuracy:** ±30m maritime, ±50m aviation
- **Latency:** 3 minutes typical

### Kongsberg
- **Pros:** Highest accuracy, real-time, independent verification
- **Cons:** Limited to installed locations, high infrastructure cost
- **Accuracy:** ±10m (close), ±50m (20+ nm)
- **Latency:** 1-2 seconds (real-time)

---

## Monitoring & Debugging

### Check Source Status

```bash
curl http://localhost:8000/api/sources \
  -H "Authorization: Bearer YOUR_TOKEN" | jq '.[] | select(.id | contains("radar"))'
```

Response:
```json
{
  "id": "marinetraffic",
  "name": "MarineTraffic",
  "status": "available",
  "latency_ms": 1250,
  "error": null,
  "last_success_at": "2024-01-15T10:35:22Z",
  "last_count": 47
}
```

### View Radar Observations in Web UI

Navigate to: `http://localhost:5173/api/observations?source_type=radar`

Filter options:
- `source_id` - Filter by radar provider
- `object_type` - `vessel`, `aircraft`, `radar_target`
- `since` - Start time (ISO 8601)
- `until` - End time (ISO 8601)

---

## Cost Analysis (Monthly)

| Provider | Min Cost | Max Cost | Coverage | Update |
|---|---|---|---|---|
| MarineTraffic | €300 | €2,500 | Global maritime | 5 min |
| Spire Global | $500 | $3,000 | Global maritime + aviation | 3 min |
| Kongsberg | €1,000 | €100,000+ | Coastal (if hardware) | 1-2 sec |

**Recommendation:** Start with MarineTraffic for cost-effective global maritime coverage, add Spire for aviation data, deploy Kongsberg for mission-critical coastal surveillance.

---

## Support & Documentation

- **MarineTraffic:** https://www.marinetraffic.com/en/ais-api-services/documentation
- **Spire Global:** https://www.spire.com/docs/
- **Kongsberg:** https://www.kongsberg.com/maritime/support/

---

## Integration Status

✅ All three radar connectors are registered and available
✅ Configuration schema ready in `config.py`
✅ API endpoints ready in `registry.py`
✅ Polling mechanism integrated
✅ Web UI displays radar observations

**Next Steps:**
1. Subscribe to radar data providers
2. Add API keys to `.env` file
3. Enable sources via API or web UI
4. Monitor observations in dashboard

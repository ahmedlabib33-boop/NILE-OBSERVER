import ijson
import json
import csv
import os

BASE = r"D:\nile-observer-continuation"
SOURCE = os.path.join(
    BASE, "CameraSources", "Argus", "archive",
    "windy_massive.geojson"
)

JSON_OUTPUT = os.path.join(BASE, "CairoCameraDetails.json")
CSV_OUTPUT = os.path.join(BASE, "CairoCameraDetails.csv")

# Approximate Greater Cairo search bounds
MIN_LAT = 29.75
MAX_LAT = 30.35
MIN_LON = 30.85
MAX_LON = 31.75

results = []
seen = set()

with open(SOURCE, "rb") as f:
    for feature in ijson.items(f, "features.item"):

        geometry = feature.get("geometry") or {}
        properties = feature.get("properties") or {}

        if geometry.get("type") != "Point":
            continue

        coordinates = geometry.get("coordinates") or []

        if len(coordinates) < 2:
            continue

        try:
            longitude = float(coordinates[0])
            latitude = float(coordinates[1])
        except (TypeError, ValueError):
            continue

        if not (
            MIN_LAT <= latitude <= MAX_LAT
            and MIN_LON <= longitude <= MAX_LON
        ):
            continue

        name = str(
            properties.get("name")
            or properties.get("title")
            or "Unknown Camera"
        )

        url = str(
            properties.get("url")
            or properties.get("streamUrl")
            or properties.get("stream")
            or ""
        )

        key = (
            round(latitude, 6),
            round(longitude, 6),
            url
        )

        if key in seen:
            continue

        seen.add(key)

        record = {
            "name": name,
            "latitude": latitude,
            "longitude": longitude,
            "url": url,
            "source": "Argus",
            "properties": properties
        }

        results.append(record)

with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

with open(CSV_OUTPUT, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "name",
            "latitude",
            "longitude",
            "url",
            "source"
        ]
    )

    writer.writeheader()

    for record in results:
        writer.writerow({
            key: record[key]
            for key in writer.fieldnames
        })

print("=" * 60)
print("GREATER CAIRO CAMERA EXTRACTION")
print("=" * 60)
print("Records found:", len(results))
print("JSON:", JSON_OUTPUT)
print("CSV:", CSV_OUTPUT)
print("=" * 60)

for camera in results[:30]:
    print(
        camera["name"],
        camera["latitude"],
        camera["longitude"],
        camera["url"]
    )

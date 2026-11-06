import json
import csv
from pathlib import Path

base = Path(r"D:\nile-observer-continuation")
source = base / "CCTV" / "cctv_cameras.json"

with source.open("r", encoding="utf-8-sig") as f:
    data = json.load(f)

print("DATA TYPE:", type(data).__name__)

if isinstance(data, dict):
    print("ROOT KEYS:", list(data.keys())[:30])

    for key, value in data.items():
        if isinstance(value, list):
            data = value
            print("CAMERA ARRAY:", key)
            break

results = []

def inspect(obj):
    if isinstance(obj, dict):
        name = str(obj.get("name", ""))
        city = str(obj.get("city", ""))
        region = str(obj.get("region", ""))

        if (
            "egypt" in region.lower()
            or "cairo" in city.lower()
            or "giza" in city.lower()
        ):
            results.append(obj)

        for value in obj.values():
            if isinstance(value, (dict, list)):
                inspect(value)

    elif isinstance(obj, list):
        for item in obj:
            inspect(item)

inspect(data)

# Remove duplicate records
unique = {}

for camera in results:
    key = json.dumps(camera, sort_keys=True, ensure_ascii=False)
    unique[key] = camera

results = list(unique.values())

json_output = base / "EgyptCameraRecords.json"
csv_output = base / "EgyptCameraRecords.csv"

with json_output.open("w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

with csv_output.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)

    writer.writerow([
        "Name",
        "City",
        "Region",
        "Stream URL",
        "Web URL"
    ])

    for camera in results:
        writer.writerow([
            camera.get("name", ""),
            camera.get("city", ""),
            camera.get("region", ""),
            camera.get("streamUrl", ""),
            camera.get("webEmbedUrl", "")
        ])

print()
print("EGYPT CAMERA RECORDS:", len(results))
print("JSON:", json_output)
print("CSV:", csv_output)

for camera in results:
    print(json.dumps(camera, ensure_ascii=False, indent=2))

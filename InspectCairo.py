import ijson
import json

source = r"D:\nile-observer-continuation\CameraSources\Argus\archive\windy_massive.geojson"

print("INSPECTING CAIRO CAMERA RECORDS")
print("=" * 70)

count = 0
total = 0

with open(source, "rb") as f:
    for feature in ijson.items(f, "features.item"):

        total += 1

        properties = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}

        name = str(properties.get("name", ""))
        city = str(properties.get("city", ""))
        country = str(properties.get("country", ""))

        if (
            "cairo" in name.lower()
            or "cairo" in city.lower()
            or "egypt" in country.lower()
        ):
            print("\n" + "=" * 70)
            print("NAME:", name)
            print("CITY:", city)
            print("COUNTRY:", country)
            print("GEOMETRY:", geometry)
            print(
                "PROPERTIES:",
                json.dumps(properties, ensure_ascii=False, indent=2)
            )

            count += 1

            if count >= 20:
                break

print("\nRECORDS SCANNED:", total)
print("MATCHING RECORDS DISPLAYED:", count)

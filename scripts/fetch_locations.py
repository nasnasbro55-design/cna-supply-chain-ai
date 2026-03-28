import requests
import json

def fetch_locations():
    # Faster overpass query with timeout
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    query = """
    [out:json][timeout:25];
    (
      node["amenity"="fuel"](38.8,-77.2,39.0,-77.0);
      node["shop"="supermarket"](38.8,-77.2,39.0,-77.0);
    );
    out;
    """
    
    print("Fetching locations... (may take 10-15 seconds)")
    response = requests.post(overpass_url, data=query, timeout=30)
    data = response.json()
    
    locations = []
    for element in data["elements"]:
        locations.append({
            "name": element.get("tags", {}).get("name", "Unknown"),
            "type": element.get("tags", {}).get("amenity") or element.get("tags", {}).get("shop"),
            "lat": element.get("lat"),
            "lon": element.get("lon")
        })
    
    print(f"Found {len(locations)} locations in Northern Virginia")
    
    with open("output/locations.json", "w") as f:
        json.dump(locations, f, indent=2)
    
    print("Saved to output/locations.json!")

fetch_locations()
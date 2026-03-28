import json

def combine_data():
    # Load all three datasets
    with open("output/weather_alerts.json") as f:
        weather = json.load(f)
    
    with open("output/locations.json") as f:
        locations = json.load(f)
    
    with open("output/cameras.json") as f:
        cameras = json.load(f)
    
    combined = {
        "weather_alerts": weather,
        "locations": locations,
        "cameras": cameras
    }
    
    with open("output/combined_data.json", "w") as f:
        json.dump(combined, f, indent=2)
    
    print("Combined data summary:")
    print(f"  Weather alerts: {len(weather)}")
    print(f"  Locations: {len(locations)}")
    print(f"  Cameras: {len(cameras)}")
    print("Saved to output/combined_data.json!")

combine_data()

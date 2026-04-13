import requests
import json

def fetch_weather():
    url = "https://api.weather.gov/alerts/active?area=VA"
    
    response = requests.get(url)
    data = response.json()
    
    alerts = data.get("features", [])
    print(f"Found {len(alerts)} active weather alerts in Virginia")
    
    cleaned = []
    for alert in alerts:
        props = alert["properties"]
        geometry = alert.get("geometry")
        
        # Check if geometry exists and log it
        if geometry:
            print(f"✅ Geometry found for: {props['event']}")
        else:
            print(f"⚠️ No geometry for: {props['event']} (NWS didn't provide polygon)")
        
        cleaned.append({
            "event": props["event"],
            "headline": props["headline"],
            "severity": props["severity"],
            "area": props["areaDesc"],
            "geometry": geometry
        })
    
    with open("output/weather_alerts.json", "w") as f:
        json.dump(cleaned, f, indent=2)
    
    print("Saved to output/weather_alerts.json!")

fetch_weather()
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
        cleaned.append({
            "event": props["event"],
            "headline": props["headline"],
            "severity": props["severity"],
            "area": props["areaDesc"]
        })
    
    with open("output/weather_alerts.json", "w") as f:
        json.dump(cleaned, f, indent=2)
    
    print("Saved to output/weather_alerts.json!")

fetch_weather()
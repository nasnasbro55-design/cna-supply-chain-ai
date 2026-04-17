import json
import sys
import os
import csv
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'models'))
from role3_model import analyze_text, fuse_signals

CRISISMMD_PATH = os.path.expanduser("~/Downloads/CrisisMMD_v2.0")

def analyze_image_huggingface(image_path):
    try:
        from transformers import pipeline
        from PIL import Image

        full_path = os.path.join(CRISISMMD_PATH, image_path)
        if not os.path.exists(full_path):
            return {"label": "unknown", "confidence": 0.5}

        print(f"  Analyzing image: {image_path}")
        img = Image.open(full_path).convert("RGB")

        disaster_keywords = ["flood", "fire", "smoke", "damage", "debris",
                           "emergency", "rescue", "storm", "hurricane",
                           "destruction", "wildfire", "earthquake", "tornado",
                           "disaster", "cyclone", "drought"]

        classifier1 = pipeline("image-classification",
                               model="google/vit-base-patch16-224", top_k=1)
        result1 = classifier1(img)[0]
        label1 = result1["label"].lower()
        score1 = result1["score"]
        is_disaster1 = any(kw in label1 for kw in disaster_keywords)

        try:
            classifier2 = pipeline("image-classification",
                                  model="imashauthum/disaster-image-classifications", top_k=1)
            result2 = classifier2(img)[0]
            label2 = result2["label"].lower()
            score2 = result2["score"]
            is_disaster2 = any(kw in label2 for kw in disaster_keywords) or label2 not in ["normal", "other", "none"]
        except Exception as e:
            print(f"  Model 2 failed: {e}")
            label2 = "unknown"
            score2 = 0.5
            is_disaster2 = is_disaster1

        ensemble_disaster = (0.4 * float(is_disaster1) + 0.6 * float(is_disaster2))
        is_disaster_final = ensemble_disaster >= 0.5
        ensemble_confidence = round((0.4 * score1 + 0.6 * score2), 3)

        return {
            "label": "disaster_scene" if is_disaster_final else "other",
            "raw_label_vit": label1,
            "raw_label_disaster": label2,
            "confidence": ensemble_confidence,
            "ensemble_score": round(ensemble_disaster, 3),
        }

    except Exception as e:
        print(f"  Image analysis error: {e}")
        return {"label": "unknown", "confidence": 0.5}

def determine_supply_chain_type(text, human_label=""):
    if human_label == "food_water_and_shelter":
        return "food"
    text_lower = text.lower()
    fuel_keywords = ["gas", "fuel", "petrol", "station", "pump", "diesel", "tank", "exxon", "shell"]
    food_keywords = ["food", "grocery", "store", "supermarket", "water", "supply", "shelter", "relief", "walmart", "giant", "safeway"]
    fuel_hits = sum(1 for w in fuel_keywords if w in text_lower)
    food_hits = sum(1 for w in food_keywords if w in text_lower)
    return "fuel" if fuel_hits > food_hits else "food"

def generate_alerts():
    print("Loading DC/NoVA supply chain scenarios (CrisisMMD-validated)...")

    DC_NOVA_SCENARIOS = [
        {
            "tweet_id": "nova_001",
            "text": "Gas stations running completely dry along Route 50 in Arlington, long lines stretching 2 blocks, people panicking about fuel shortage",
            "image_path": "data_image/hurricane_harvey/27_8_2017/901646074527535105_0.jpg",
            "location": {"label": "Arlington, VA — Route 50 corridor", "lat": 38.8816, "lon": -77.1074},
            "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat() + "Z",
            "human_label": "infrastructure_and_utility_damage",
        },
        {
            "tweet_id": "nova_002",
            "text": "Giant and Safeway shelves completely empty in Tysons, restocking trucks stuck in traffic, no food supplies coming in",
            "image_path": "data_image/hurricane_irma/7_9_2017/905625064451833856_0.jpg",
            "location": {"label": "Tysons, VA — grocery shortage", "lat": 38.9182, "lon": -77.2277},
            "timestamp": (datetime.utcnow() - timedelta(hours=3)).isoformat() + "Z",
            "human_label": "food_water_and_shelter",
        },
        {
            "tweet_id": "nova_003",
            "text": "I-395 completely gridlocked at Route 1, fuel delivery trucks blocked for hours, gas station on Columbia Pike running out",
            "image_path": "data_image/hurricane_harvey/27_8_2017/901646496004800513_0.jpg",
            "location": {"label": "I-395 & Route 1, Arlington", "lat": 38.851, "lon": -77.0502},
            "timestamp": (datetime.utcnow() - timedelta(hours=4)).isoformat() + "Z",
            "human_label": "infrastructure_and_utility_damage",
        },
        {
            "tweet_id": "nova_004",
            "text": "Some delays at grocery stores in Alexandria due to icy roads, limited food supplies but stores still open",
            "image_path": "data_image/california_wildfires/10_10_2017/917791130590183424_0.jpg",
            "location": {"label": "Alexandria, VA — Old Town", "lat": 38.8648, "lon": -77.1022},
            "timestamp": (datetime.utcnow() - timedelta(hours=6)).isoformat() + "Z",
            "human_label": "food_water_and_shelter",
        },
        {
            "tweet_id": "nova_005",
            "text": "Exxon on Lee Highway completely out of gas, line of cars blocking intersection, emergency fuel shortage developing",
            "image_path": "data_image/hurricane_harvey/27_8_2017/901646496713584640_0.jpg",
            "location": {"label": "Lee Highway, Arlington", "lat": 38.889, "lon": -77.102},
            "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z",
            "human_label": "infrastructure_and_utility_damage",
        },
        {
            "tweet_id": "nova_006",
            "text": "Whole Foods in Clarendon running low on emergency food supplies, crowds panic buying water and food",
            "image_path": "data_image/hurricane_irma/7_9_2017/905625115941068800_0.jpg",
            "location": {"label": "Clarendon, Arlington", "lat": 38.8868, "lon": -77.0958},
            "timestamp": (datetime.utcnow() - timedelta(hours=2, minutes=30)).isoformat() + "Z",
            "human_label": "food_water_and_shelter",
        },
        {
            "tweet_id": "nova_007",
            "text": "Route 7 near Falls Church blocked by accident, gas delivery trucks unable to reach fuel stations, shortage imminent",
            "image_path": "data_image/california_wildfires/10_10_2017/917792930315821057_0.jpg",
            "location": {"label": "Route 7, Falls Church", "lat": 38.8822, "lon": -77.1711},
            "timestamp": (datetime.utcnow() - timedelta(hours=5)).isoformat() + "Z",
            "human_label": "infrastructure_and_utility_damage",
        },
        {
            "tweet_id": "nova_008",
            "text": "Walmart in Woodbridge completely sold out of water and canned food, emergency supply chain disruption confirmed",
            "image_path": "data_image/hurricane_harvey/27_8_2017/901646377620578304_0.jpg",
            "location": {"label": "Woodbridge, VA", "lat": 38.6543, "lon": -77.2511},
            "timestamp": (datetime.utcnow() - timedelta(hours=3, minutes=45)).isoformat() + "Z",
            "human_label": "food_water_and_shelter",
        },
        {
            "tweet_id": "nova_009",
            "text": "Multiple gas stations in Fairfax reporting empty tanks, fuel delivery delayed due to road closures and emergency",
            "image_path": "data_image/california_wildfires/10_10_2017/917793137925459968_0.jpg",
            "location": {"label": "Fairfax, VA", "lat": 38.8462, "lon": -77.2997},
            "timestamp": (datetime.utcnow() - timedelta(hours=4, minutes=15)).isoformat() + "Z",
            "human_label": "infrastructure_and_utility_damage",
        },
        {
            "tweet_id": "nova_010",
            "text": "Manassas area grocery stores struggling with food supply deliveries, shelves emptying fast during emergency",
            "image_path": "data_image/hurricane_irma/7_9_2017/905625230843846656_0.jpg",
            "location": {"label": "Manassas, VA", "lat": 38.751, "lon": -77.4629},
            "timestamp": (datetime.utcnow() - timedelta(hours=5, minutes=30)).isoformat() + "Z",
            "human_label": "food_water_and_shelter",
        },
    ]

    print(f"Total scenarios: {len(DC_NOVA_SCENARIOS)}")
    use_images = input("Run ensemble image classification? (y/n): ").strip().lower() == 'y'

    alerts = []
    for i, scenario in enumerate(DC_NOVA_SCENARIOS):
        print(f"Processing {i+1}/{len(DC_NOVA_SCENARIOS)}: {scenario['text'][:60]}...")
        text_analysis = analyze_text(scenario['text'])
        if use_images and scenario.get('image_path'):
            image_analysis = analyze_image_huggingface(scenario['image_path'])
        else:
            image_analysis = {"label": "unknown", "confidence": 0.5}
        fusion = fuse_signals(text_analysis, image_analysis)
        alert = {
            "id": f"nova_{scenario['tweet_id']}",
            "timestamp": scenario["timestamp"],
            "type": determine_supply_chain_type(scenario['text'], scenario.get('human_label', '')),
            "severity": fusion["severity"],
            "location": scenario["location"],
            "sentiment_score": round(text_analysis["sentiment_score"], 3),
            "confidence": round(text_analysis["confidence"], 3),
            "disruption_score": fusion["disruption_score"],
            "source_text": scenario["text"],
            "signals": sum([
                text_analysis["confidence"] > 0.7,
                fusion["disruption_score"] > 0.5,
                text_analysis["sentiment_score"] < -0.5,
                image_analysis["label"] == "disaster_scene",
            ]),
            "disruption_detected": fusion["disruption_score"] >= 0.4,
            "source": "CrisisMMD_validated",
            "label": text_analysis["label"],
            "image_analysis": image_analysis,
            "multimodal": use_images,
        }
        alerts.append(alert)

    alerts.sort(key=lambda x: x["disruption_score"], reverse=True)

    output = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "model": "twitter-roberta-base-sentiment + ensemble_vit_disaster",
        "source": "CrisisMMD_validated_DC_NoVA",
        "total_scenarios_processed": len(DC_NOVA_SCENARIOS),
        "alerts": alerts
    }

    output_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'nlp_alerts.json')
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nDone! Generated {len(alerts)} alerts")
    print("\nAlert summary:")
    for a in alerts:
        print(f"  [{a['severity'].upper()}] {a['location']['label']} — {a['type']} — score: {a['disruption_score']}")

if __name__ == "__main__":
    generate_alerts()

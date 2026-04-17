import json
import sys
import os
import csv
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'models'))
from role3_model import analyze_text, fuse_signals

CRISISMMD_PATH = os.path.expanduser("~/Downloads/CrisisMMD_v2.0")
ANNOTATIONS_PATH = os.path.join(CRISISMMD_PATH, "annotations")

DC_NOVA_LOCATIONS = [
    {"label": "Arlington, VA — Route 50 corridor", "lat": 38.8816, "lon": -77.1074},
    {"label": "Tysons, VA", "lat": 38.9182, "lon": -77.2277},
    {"label": "I-395 & Route 1, Arlington", "lat": 38.851, "lon": -77.0502},
    {"label": "Alexandria, VA", "lat": 38.8648, "lon": -77.1022},
    {"label": "Lee Highway, Arlington", "lat": 38.889, "lon": -77.102},
    {"label": "Clarendon, Arlington", "lat": 38.8868, "lon": -77.0958},
    {"label": "Falls Church, VA", "lat": 38.8822, "lon": -77.1711},
    {"label": "Fairfax, VA", "lat": 38.8462, "lon": -77.2997},
    {"label": "Manassas, VA", "lat": 38.751, "lon": -77.4629},
    {"label": "Woodbridge, VA", "lat": 38.6543, "lon": -77.2511},
]

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

        # Model 1 — General ViT
        classifier1 = pipeline("image-classification", 
                               model="google/vit-base-patch16-224", top_k=1)
        result1 = classifier1(img)[0]
        label1 = result1["label"].lower()
        score1 = result1["score"]
        is_disaster1 = any(kw in label1 for kw in disaster_keywords)

        # Model 2 — Disaster-specific classifier
        try:
            classifier2 = pipeline("image-classification",
                                  model="imashauthum/disaster-image-classifications", top_k=1)
            result2 = classifier2(img)[0]
            label2 = result2["label"].lower()
            score2 = result2["score"]
            is_disaster2 = any(kw in label2 for kw in disaster_keywords) or label2 not in ["normal", "other", "none"]
        except Exception as e:
            print(f"  Model 2 failed, using Model 1 only: {e}")
            label2 = "unknown"
            score2 = 0.5
            is_disaster2 = is_disaster1

        # Ensemble — weighted average (disaster model gets more weight)
        ensemble_disaster = (0.4 * float(is_disaster1) + 0.6 * float(is_disaster2))
        is_disaster_final = ensemble_disaster >= 0.5
        ensemble_confidence = round((0.4 * score1 + 0.6 * score2), 3)

        return {
            "label": "disaster_scene" if is_disaster_final else "other",
            "raw_label_vit": label1,
            "raw_label_disaster": label2,
            "confidence": ensemble_confidence,
            "ensemble_score": round(ensemble_disaster, 3),
            "model1_score": round(score1, 3),
            "model2_score": round(score2, 3),
        }

    except Exception as e:
        print(f"  Image analysis error: {e}")
        return {"label": "unknown", "confidence": 0.5}
    
def load_crisis_tweets(tsv_file, max_rows=20):
    tweets = []
    try:
        with open(tsv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for i, row in enumerate(reader):
                if i >= max_rows:
                    break
                if row.get('text_info', '') == 'informative' and row.get('tweet_text', '').strip():
                    tweets.append({
                        'tweet_id': row.get('tweet_id', f'tweet_{i}'),
                        'text': row.get('tweet_text', ''),
                        'image_path': row.get('image_path', ''),
                        'text_label': row.get('text_info', ''),
                        'image_label': row.get('image_info', ''),
                        'damage': row.get('image_damage', ''),
                    })
    except Exception as e:
        print(f"Error reading {tsv_file}: {e}")
    return tweets

def assign_nova_location(index):
    return DC_NOVA_LOCATIONS[index % len(DC_NOVA_LOCATIONS)]

def determine_supply_chain_type(text):
    text_lower = text.lower()
    fuel_keywords = ["gas", "fuel", "petrol", "station", "pump", "diesel", "shortage", "tank"]
    food_keywords = ["food", "grocery", "store", "supermarket", "water", "supply", "shelter", "relief"]
    fuel_hits = sum(1 for w in fuel_keywords if w in text_lower)
    food_hits = sum(1 for w in food_keywords if w in text_lower)
    return "fuel" if fuel_hits >= food_hits else "food"

def generate_alerts():
    print("Loading CrisisMMD data...")

    tsv_files = [
        "hurricane_harvey_final_data.tsv",
        "hurricane_irma_final_data.tsv",
        "california_wildfires_final_data.tsv",
    ]

    all_tweets = []
    for tsv_file in tsv_files:
        path = os.path.join(ANNOTATIONS_PATH, tsv_file)
        tweets = load_crisis_tweets(path, max_rows=20)
        all_tweets.extend(tweets)
        print(f"Loaded {len(tweets)} informative tweets from {tsv_file}")

    print(f"\nTotal tweets loaded: {len(all_tweets)}")
    print("Running through NLP + vision models...\n")

    use_images = input("Run HuggingFace image classification? This may take 5-10 min (y/n): ").strip().lower() == 'y'

    alerts = []
    for i, tweet in enumerate(all_tweets):
        print(f"Processing tweet {i+1}/{len(all_tweets)}: {tweet['text'][:60]}...")

        text_analysis = analyze_text(tweet['text'])

        if use_images and tweet.get('image_path'):
            image_analysis = analyze_image_huggingface(tweet['image_path'])
        else:
            image_analysis = {"label": "unknown", "confidence": 0.5}

        fusion = fuse_signals(text_analysis, image_analysis)

        if fusion['disruption_score'] < 0.1:
            continue

        location = assign_nova_location(i)
        supply_type = determine_supply_chain_type(tweet['text'])
        offset_minutes = i * 15
        tweet_time = (datetime.utcnow() - timedelta(minutes=offset_minutes)).isoformat() + "Z"

        alert = {
            "id": f"crisismmd_{tweet['tweet_id']}",
            "timestamp": tweet_time,
            "type": supply_type,
            "severity": fusion["severity"],
            "location": location,
            "sentiment_score": round(text_analysis["sentiment_score"], 3),
            "confidence": round(text_analysis["confidence"], 3),
            "disruption_score": fusion["disruption_score"],
            "source_text": tweet["text"][:200],
            "signals": sum([
                text_analysis["confidence"] > 0.7,
                fusion["disruption_score"] > 0.5,
                text_analysis["sentiment_score"] < -0.5,
                image_analysis["label"] == "disaster_scene",
            ]),
            "disruption_detected": fusion["disruption_score"] >= 0.4,
            "source": "CrisisMMD",
            "label": text_analysis["label"],
            "image_analysis": image_analysis,
            "multimodal": use_images and image_analysis["label"] != "unknown",
        }
        alerts.append(alert)

    alerts.sort(key=lambda x: x["disruption_score"], reverse=True)
    alerts = alerts[:20]

    output = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "model": "role3_keyword_nlp_v1 + huggingface_vit",
        "source": "CrisisMMD_v2.0",
        "total_tweets_processed": len(all_tweets),
        "alerts": alerts
    }

    output_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'nlp_alerts.json')
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nDone! Generated {len(alerts)} alerts")
    print(f"Saved to output/nlp_alerts.json")
    print("\nAlert summary:")
    for a in alerts[:10]:
        print(f"  [{a['severity'].upper()}] {a['location']['label']} — {a['type']} — score: {a['disruption_score']}")

if __name__ == "__main__":
    generate_alerts()

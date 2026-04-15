import json
from typing import Dict, Any, List
from datetime import datetime


# Simple keyword-based NLP

NEGATIVE_WORDS = {
    "shortage", "empty", "out of gas", "no gas", "no food",
    "closed", "line", "lines", "long line", "panic", "crowded",
    "delay", "blocked", "stuck", "traffic", "crisis", "emergency"
}

SUPPLY_CHAIN_WORDS = {
    "gas", "fuel", "grocery", "store", "supermarket",
    "food", "water", "supplies", "station"
}


def analyze_text(text: str) -> Dict[str, Any]:
    """
    Very simple text analysis:
      - detect if it's about supply chain disruption
      - estimate sentiment
      - assign a crude confidence
    """
    text_lower = text.lower()

    # sentiment
    negative_hits = sum(1 for w in NEGATIVE_WORDS if w in text_lower)
    supply_hits = sum(1 for w in SUPPLY_CHAIN_WORDS if w in text_lower)

    if negative_hits > 0:
        sentiment = "negative"
        sentiment_score = -0.5 - 0.1 * negative_hits
    else:
        sentiment = "neutral"
        sentiment_score = 0.0

    # label: is this about supply chain disruption?
    if supply_hits > 0 and negative_hits > 0:
        label = "supply_chain_disruption"
        confidence = min(0.5 + 0.1 * (negative_hits + supply_hits), 0.99)
    elif supply_hits > 0:
        label = "supply_chain_related"
        confidence = min(0.4 + 0.1 * supply_hits, 0.9)
    else:
        label = "other"
        confidence = 0.5

    return {
        "label": label,
        "confidence": round(confidence, 3),
        "sentiment": sentiment,
        "sentiment_score": round(sentiment_score, 3)
    }


# Fake image analysis stub

def analyze_image(image_url: str) -> Dict[str, Any]:
    """
      Temporary image analysis stub.

      Right now this function doesn’t run a real model — it simply returns a
      default value. Once the image pipeline is ready, replace this with a
      CNN or vision transformer that can classify traffic camera snapshots.
   """
    return {
        "label": "unknown",
        "confidence": 0.5
    }


# Fusion logic

def fuse_signals(text_analysis: Dict[str, Any],
                 image_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Combine text + image into a single disruption score and severity.
    For now, we mostly trust text, since image is a stub.
    """
    base_score = 0.0

    # text-based contribution
    if text_analysis["label"] == "supply_chain_disruption":
        base_score += 0.7 * text_analysis["confidence"]
    elif text_analysis["label"] == "supply_chain_related":
        base_score += 0.4 * text_analysis["confidence"]

    if text_analysis["sentiment"] == "negative":
        base_score += 0.2

    # image-based contribution (very small for now)
    if image_analysis["label"] != "unknown":
        base_score += 0.2 * image_analysis["confidence"]

    disruption_score = max(0.0, min(base_score, 1.0))

    if disruption_score >= 0.75:
        severity = "high"
    elif disruption_score >= 0.4:
        severity = "medium"
    else:
        severity = "low"

    return {
        "disruption_score": round(disruption_score, 3),
        "severity": severity
    }


# Main public API

def analyze_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main Role 3 function.

    Expected input schema:
    {
      "id": "event_00123",
      "text": "Long lines at the gas station on Lee Hwy",
      "image_url": "https://example.com/cam12.jpg",
      "location": {
        "lat": 38.889,
        "lon": -77.102
      },
      "timestamp": "2026-03-28T15:00:00Z",
      "source": "twitter"
    }

    Output schema:
    {
      "id": "...",
      "location": {...},
      "timestamp": "...",
      "text_analysis": {...},
      "image_analysis": {...},
      "fusion": {...}
    }
    """

    text = event.get("text", "")
    image_url = event.get("image_url", "")

    text_analysis = analyze_text(text)
    image_analysis = analyze_image(image_url)
    fusion = fuse_signals(text_analysis, image_analysis)

    return {
        "id": event.get("id"),
        "location": event.get("location"),
        "timestamp": event.get("timestamp"),
        "source": event.get("source"),
        "text_analysis": text_analysis,
        "image_analysis": image_analysis,
        "fusion": fusion
    }


# Batch helper

def analyze_events_batch(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [analyze_event(e) for e in events]


# CLI / local testing

def main():
    """
    Simple local test.
    You can run this in jGRASP or terminal:

        python role3_model.py

    It will print a sample input and the corresponding model output.
    """
    sample_event = {
        "id": "event_00123",
        "text": "Long lines at the gas station on Lee Hwy, people say there's no gas left.",
        "image_url": "https://example.com/cam12.jpg",
        "location": {
            "lat": 38.889,
            "lon": -77.102
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "twitter"
    }

    print("=== Sample Input ===")
    print(json.dumps(sample_event, indent=2))

    result = analyze_event(sample_event)

    print("\n=== Model Output ===")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

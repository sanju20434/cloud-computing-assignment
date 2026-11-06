import json
import requests

# Assignment schema: exactly four keys
SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": [
                "alarm_set",
                "alarm_query",
                "calendar_set",
                "calendar_query",
                "calendar_remove",
                "weather_query",
                "datetime_query",
                "recommendation_events"
            ]
        },
        "date": {"type": ["string", "null"]},
        "time": {"type": ["string", "null"]},
        "place": {"type": ["string", "null"]}
    },
    "required": ["intent", "date", "time", "place"],
    "additionalProperties": False
}

# Test command
command = "set an alarm for seven am tomorrow in London"

prompt = f"""
You are an exact-copy command parser.

Convert the command into exactly one JSON object.

Rules:
1. Use only the eight allowed intents in the schema.
2. Copy date, time and place exactly from the command.
3. Never convert or reformat dates or times.
4. Use actual JSON null for missing slots.
5. Never invent information.
6. Return JSON only.

Important examples:
- seven am must remain seven am, never 07:00.
- tomorrow must remain tomorrow.
- London must remain London.

Command: {command}
"""

payload = {
    "model": "phi3.5",
    "prompt": prompt,
    "format": SCHEMA,
    "stream": False,
    "options": {
        "temperature": 0,
        "seed": 42
    }
}

print("Sending command to Teacher Model...")

try:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json=payload,
        timeout=300
    )
    response.raise_for_status()

    raw_output = response.json()["response"]
    result = json.loads(raw_output)

    print("\nTEACHER MODEL OUTPUT:")
    print(json.dumps(result, indent=2))

    checks = {
        "Exactly four keys": (
            set(result.keys()) == {"intent", "date", "time", "place"}
        ),
        "Allowed intent": (
            result["intent"] in SCHEMA["properties"]["intent"]["enum"]
        ),
        "Correct null values": all(
            value is None or isinstance(value, str)
            for key, value in result.items()
            if key != "intent"
        ),
        "Date copied exactly": (
            result["date"] is None or result["date"] in command
        ),
        "Time copied exactly": (
            result["time"] is None or result["time"] in command
        ),
        "Place copied exactly": (
            result["place"] is None or result["place"] in command
        )
    }

    print("\nVALIDATION RESULTS:")

    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")

    if all(checks.values()):
        print("\nRESULT: ALL CHECKS PASSED")
    else:
        print("\nRESULT: INVALID OUTPUT - DO NOT USE FOR TRAINING")

except requests.RequestException as error:
    print("Ollama API error:", error)

except (json.JSONDecodeError, KeyError, TypeError) as error:
    print("Invalid model response:", error)

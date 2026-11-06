
import json
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

PROMPT_FILE = BASE_DIR / "prompts" / "teacher_prompt.txt"
VALIDATION_FILE = BASE_DIR / "data" / "validation.jsonl"
OUTPUT_FILE = BASE_DIR / "results" / "teacher_predictions.jsonl"

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

def main():
    prompt_template = PROMPT_FILE.read_text(encoding="utf-8")

    with open(VALIDATION_FILE, "r", encoding="utf-8") as f:
        examples = [json.loads(line) for line in f if line.strip()]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    print("Teacher model: phi3.5")
    print("Validation examples:", len(examples))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        for index, example in enumerate(examples, start=1):
            command = example["text"]

            prompt = (
                prompt_template
                + "\n\nCommand: "
                + command
                + "\nOutput:"
            )

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

            try:
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json=payload,
                    timeout=300
                )
                response.raise_for_status()

                raw_output = response.json()["response"]

                # Save raw teacher response for score.py
                record = {
                    "id": example["id"],
                    "prediction": raw_output
                }

                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                out.flush()

            except Exception as error:
                print(f"Error on {example['id']}: {error}")

                record = {
                    "id": example["id"],
                    "prediction": ""
                }

                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                out.flush()

            if index % 10 == 0:
                print(f"Processed {index}/{len(examples)}")

    print("\nTeacher predictions saved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()

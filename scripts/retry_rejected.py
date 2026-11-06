import json
import requests
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PROMPT = (BASE / "prompts" / "teacher_prompt.txt").read_text(encoding="utf-8")
SCHEMA = json.loads((BASE / "data" / "schema.json").read_text(encoding="utf-8"))

REJECTED = BASE / "datasets" / "v1" / "rejected.jsonl"
OUTPUT = BASE / "raw_outputs_retry" / "rejected_retry.jsonl"

with REJECTED.open(encoding="utf-8") as f:
    records = [json.loads(line) for line in f if line.strip()]

with OUTPUT.open("w", encoding="utf-8") as out:
    for i, record in enumerate(records, 1):
        command = record["command"]
        payload = {
            "model": "phi3.5:latest",
            "prompt": PROMPT + "\n\nCommand: " + command + "\nOutput:",
            "stream": False,
            "format": SCHEMA,
            "options": {"temperature": 0, "seed": 42}
        }
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=180
            )
            response.raise_for_status()
            result = json.loads(response.json()["response"])
            row = {
                "id": record["id"],
                "command": command,
                "raw_output": json.dumps(result, ensure_ascii=False),
                "status": "success"
            }
        except Exception as e:
            row = {
                "id": record["id"],
                "command": command,
                "raw_output": "",
                "status": "error",
                "error": str(e)
            }

        out.write(json.dumps(row, ensure_ascii=False) + "\n")
        out.flush()

        if i % 25 == 0:
            print(f"Processed {i}/{len(records)}")

print(f"Done. Results saved to: {OUTPUT}")

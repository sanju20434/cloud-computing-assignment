import json
import requests
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
prompt = (BASE / "prompts" / "teacher_prompt.txt").read_text(encoding="utf-8")
schema = json.loads((BASE / "data" / "schema.json").read_text(encoding="utf-8"))

tests = [
    ("C0013", "set alarm for tomorrow at two pm"),
    ("C0023", "set an alarm for me for tomorrow at seven pm"),
    ("C0149", "please set the alarm for next morning to seven am"),
    ("C0151", "please set a reminder alarm for three pm on saturday"),
    ("C0175", "i have a meeting by two pm today please remind me"),
]

for cid, command in tests:
    payload = {
        "model": "phi3.5:latest",
        "prompt": prompt + "\n\nCommand: " + command + "\nOutput:",
        "stream": False,
        "format": schema,
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
        print(f"\n{cid}: {command}")
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(f"\n{cid}: ERROR - {e}")

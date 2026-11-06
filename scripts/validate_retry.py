import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))

from clean_teacher import validate_record

schema = json.loads((BASE / "data" / "schema.json").read_text(encoding="utf-8"))
allowed_intents = set(schema["intents"])

source = BASE / "raw_outputs_retry" / "rejected_retry.jsonl"
valid_file = BASE / "raw_outputs_retry" / "retry_valid.jsonl"
rejected_file = BASE / "raw_outputs_retry" / "retry_rejected_again.jsonl"

valid = []
rejected = []

for line in source.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue

    record = json.loads(line)
    ok, result = validate_record(record, allowed_intents)

    if ok:
        valid.append({
            "id": record["id"],
            "command": record["command"],
            "output": result
        })
    else:
        rejected.append({
            "id": record["id"],
            "command": record["command"],
            "reason": result,
            "raw_output": record.get("raw_output")
        })

valid_file.write_text(
    "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in valid),
    encoding="utf-8"
)
rejected_file.write_text(
    "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rejected),
    encoding="utf-8"
)

print("Retry total:", len(valid) + len(rejected))
print("Passed existing validation:", len(valid))
print("Rejected again:", len(rejected))
print("Valid file:", valid_file)
print("Rejected file:", rejected_file)

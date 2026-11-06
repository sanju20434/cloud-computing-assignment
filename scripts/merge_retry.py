import json
import hashlib
import shutil
from pathlib import Path

base = Path(__file__).resolve().parent.parent

train = base / "datasets" / "v1" / "train.jsonl"
retry = base / "raw_outputs_retry" / "retry_valid.jsonl"
backup = base / "datasets" / "v1" / "train_before_retry_merge.jsonl"
report = base / "datasets" / "v1" / "cleaning_report.json"

shutil.copy2(train, backup)

original = [json.loads(x) for x in train.read_text(encoding="utf-8").splitlines() if x.strip()]
new_records = [json.loads(x) for x in retry.read_text(encoding="utf-8").splitlines() if x.strip()]

existing_ids = {r["id"] for r in original}
if any(r["id"] in existing_ids for r in new_records):
    raise SystemExit("ERROR: Duplicate IDs found. Merge cancelled.")

merged = original + new_records

for record in merged:
    canonical = json.dumps(
        record["output"],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":")
    )
    record["sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

with train.open("w", encoding="utf-8") as f:
    for record in merged:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

if report.exists():
    data = json.loads(report.read_text(encoding="utf-8"))
    data["valid_records"] = len(merged)
    data["recovered_from_retry"] = len(new_records)
    data["rejected_records"] = 48
    data["train_file"] = str(train)
    data["backup_file"] = str(backup)
    report.write_text(json.dumps(data, indent=4), encoding="utf-8")

print("Merge completed.")
print("Original records:", len(original))
print("Added records:", len(new_records))
print("Final records:", len(merged))
print("Backup:", backup)

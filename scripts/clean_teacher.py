
import json
import hashlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "raw_outputs"
SCHEMA_FILE = BASE_DIR / "data" / "schema.json"
TRAIN_DIR = BASE_DIR / "datasets" / "v1"

TRAIN_FILE = TRAIN_DIR / "train.jsonl"
REJECTED_FILE = TRAIN_DIR / "rejected.jsonl"
REPORT_FILE = TRAIN_DIR / "cleaning_report.json"


def read_jsonl(path):
    records = []

    with open(path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            if not line.strip():
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                records.append({
                    "_invalid_line": line_number,
                    "_raw_line": line
                })

    return records


def validate_record(record, allowed_intents):
    if "_invalid_line" in record:
        return False, "invalid_raw_json"

    if record.get("status") != "success":
        return False, "teacher_generation_failed"

    command = record.get("command")
    raw_output = record.get("raw_output")

    if not isinstance(command, str) or not command.strip():
        return False, "missing_command"

    if not isinstance(raw_output, str):
        return False, "missing_raw_output"

    try:
        output = json.loads(raw_output)
    except json.JSONDecodeError:
        return False, "invalid_output_json"

    if not isinstance(output, dict):
        return False, "output_not_object"

    if set(output.keys()) != {"intent", "date", "time", "place"}:
        return False, "incorrect_keys"

    if output["intent"] not in allowed_intents:
        return False, "invalid_intent"

    for slot in ["date", "time", "place"]:
        value = output[slot]

        if value is not None and not isinstance(value, str):
            return False, f"invalid_{slot}_type"

        if isinstance(value, str):
            if not value.strip():
                return False, f"empty_{slot}"

            if value.casefold() not in command.casefold():
                return False, f"{slot}_not_in_command"

    return True, output


def main():
    TRAIN_DIR.mkdir(parents=True, exist_ok=True)

    with open(SCHEMA_FILE, "r", encoding="utf-8") as file:
        schema = json.load(file)

    allowed_intents = set(schema["intents"])

    raw_files = sorted(RAW_DIR.glob("worker_*.jsonl"))

    if not raw_files:
        print("ERROR: No raw worker files found.")
        return

    valid_records = []
    rejected_records = []
    seen_ids = set()

    total_raw = 0

    for raw_file in raw_files:
        records = read_jsonl(raw_file)

        print(f"Reading {raw_file.name}: {len(records)} records")
        total_raw += len(records)

        for record in records:
            if "_invalid_line" in record:
                rejected_records.append({
                    "source": raw_file.name,
                    "reason": "invalid_raw_json",
                    "record": record
                })
                continue

            record_id = record.get("id")

            if not record_id:
                rejected_records.append({
                    "source": raw_file.name,
                    "reason": "missing_id",
                    "record": record
                })
                continue

            if record_id in seen_ids:
                rejected_records.append({
                    "id": record_id,
                    "source": raw_file.name,
                    "reason": "duplicate_id"
                })
                continue

            seen_ids.add(record_id)

            is_valid, result = validate_record(
                record, allowed_intents
            )

            if not is_valid:
                rejected_records.append({
                    "id": record_id,
                    "command": record.get("command"),
                    "reason": result,
                    "source": raw_file.name
                })
                continue

            output_json = json.dumps(
                result,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":")
            )

            checksum = hashlib.sha256(
                output_json.encode("utf-8")
            ).hexdigest()

            valid_records.append({
                "id": record_id,
                "command": record["command"],
                "output": result,
                "sha256": checksum
            })

    with open(TRAIN_FILE, "w", encoding="utf-8") as file:
        for record in valid_records:
            file.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )

    with open(REJECTED_FILE, "w", encoding="utf-8") as file:
        for record in rejected_records:
            file.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )

    report = {
        "total_raw_records": total_raw,
        "unique_ids": len(seen_ids),
        "valid_records": len(valid_records),
        "rejected_records": len(rejected_records),
        "train_file": str(TRAIN_FILE),
        "rejected_file": str(REJECTED_FILE),
        "hash_algorithm": "SHA-256",
        "allowed_intents": sorted(allowed_intents)
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print("\n========== CLEANING REPORT ==========")
    print(f"Raw records:     {total_raw}")
    print(f"Unique IDs:      {len(seen_ids)}")
    print(f"Valid records:   {len(valid_records)}")
    print(f"Rejected records:{len(rejected_records)}")
    print(f"\nTraining file: {TRAIN_FILE}")
    print(f"Rejected file: {REJECTED_FILE}")
    print(f"Report file:   {REPORT_FILE}")
    print("=====================================")


if __name__ == "__main__":
    main()

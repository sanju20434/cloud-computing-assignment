
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL = "phi3.5:latest"
API_URL = "http://localhost:11434/api/generate"

COMMANDS_FILE = BASE_DIR / "data" / "commands_pool.jsonl"
SCHEMA_FILE = BASE_DIR / "data" / "schema.json"
PROMPT_FILE = BASE_DIR / "prompts" / "teacher_prompt.txt"
OUTPUT_DIR = BASE_DIR / "raw_outputs"


def load_jsonl(path):
    records = []
    with open(path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            if line.strip():
                records.append(json.loads(line))
    return records


def load_completed_ids(output_path):
    completed = set()

    if not output_path.exists():
        return completed

    with open(output_path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            if not line.strip():
                continue

            try:
                record = json.loads(line)

                if record.get("status") == "success":
                    completed.add(record["id"])

            except (json.JSONDecodeError, KeyError):
                print(
                    f"Warning: invalid line {line_number} "
                    f"in {output_path.name}"
                )

    return completed


def generate_one(item, worker_id, prompt_template, schema):
    command_id = item["id"]
    command_text = item["text"]

    prompt = (
        prompt_template
        + "\n\nParse this command:\n"
        + command_text
        + "\n\nReturn only the JSON object."
    )

    try:
        response = requests.post(
            API_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "format": schema,
                "stream": False,
                "options": {
                    "temperature": 0,
                    "seed": 42
                }
            },
            timeout=300
        )

        response.raise_for_status()
        raw_output = response.json()["response"]

        return {
            "id": command_id,
            "command": command_text,
            "raw_output": raw_output,
            "worker_id": worker_id,
            "status": "success"
        }

    except Exception as error:
        return {
            "id": command_id,
            "command": command_text,
            "raw_output": None,
            "worker_id": worker_id,
            "status": "error",
            "error": str(error)
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()

    if args.workers < 1:
        raise ValueError("Workers must be at least 1")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    commands = load_jsonl(COMMANDS_FILE)

    if args.limit > 0:
        commands = commands[:args.limit]

    with open(PROMPT_FILE, "r", encoding="utf-8") as file:
        prompt_template = file.read()

    with open(SCHEMA_FILE, "r", encoding="utf-8") as file:
        schema = json.load(file)

    print(f"Total commands: {len(commands)}")
    print(f"Workers: {args.workers}")
    print("Resume mode: ON")

    def worker(worker_id):
        assigned = commands[worker_id::args.workers]

        output_path = OUTPUT_DIR / f"worker_{worker_id}.jsonl"

        completed_ids = load_completed_ids(output_path)

        pending = [
            item for item in assigned
            if item["id"] not in completed_ids
        ]

        print(
            f"Worker {worker_id}: "
            f"{len(completed_ids)} already completed, "
            f"{len(pending)} remaining"
        )

        success = 0
        failed = 0

        # Append mode preserves all previously generated raw records.
        with open(output_path, "a", encoding="utf-8") as output_file:

            for index, item in enumerate(pending, 1):

                result = generate_one(
                    item,
                    worker_id,
                    prompt_template,
                    schema
                )

                output_file.write(
                    json.dumps(result, ensure_ascii=False) + "\n"
                )
                output_file.flush()

                if result["status"] == "success":
                    success += 1
                else:
                    failed += 1

                print(
                    f"Worker {worker_id}: "
                    f"{index}/{len(pending)} | "
                    f"{item['id']} | {result['status']}"
                )

        print(
            f"Worker {worker_id} finished: "
            f"{success} new success, {failed} errors"
        )

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        list(executor.map(worker, range(args.workers)))

    print("\nGeneration run completed.")
    print(f"Raw files location: {OUTPUT_DIR}")
    print("You can run this script again to resume unfinished commands.")


if __name__ == "__main__":
    main()

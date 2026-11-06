
import json
import sys
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM

BASE = Path(__file__).resolve().parent.parent

def main():
    if len(sys.argv) != 3:
        print("Usage: python training/predict.py MODEL_PATH OUTPUT_FILE")
        sys.exit(1)

    model_arg = sys.argv[1]
    output_file = BASE / sys.argv[2]

    local_model = BASE / model_arg
    model_path = str(local_model) if local_model.exists() else model_arg

    validation_file = BASE / "data" / "validation.jsonl"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading model: {model_path}")

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        dtype=torch.float32
    )
    model.eval()

    with open(validation_file, encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    print(f"Validation examples: {len(records)}")

    with open(output_file, "w", encoding="utf-8") as out:
        for i, record in enumerate(records, 1):
            prompt = (
                f"Command: {record['text']}\n"
                "JSON:"
            )

            inputs = tokenizer(prompt, return_tensors="pt")

            with torch.no_grad():
                generated = model.generate(
                    **inputs,
                    max_new_tokens=80,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id
                )

            new_tokens = generated[0][inputs["input_ids"].shape[1]:]
            prediction = tokenizer.decode(
                new_tokens,
                skip_special_tokens=True
            ).strip()

            result = {
                "id": record["id"],
                "prediction": prediction
            }

            out.write(json.dumps(result, ensure_ascii=False) + "\n")

            if i % 10 == 0:
                print(f"Processed {i}/{len(records)}")

    print(f"\nPredictions saved: {output_file}")

if __name__ == "__main__":
    main()

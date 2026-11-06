
import json
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM

BASE = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE / "models/pythia-70m-v3"

print("Loading trained model...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_DIR,
    dtype=torch.float32
)

model.eval()

print("Model dtype:", next(model.parameters()).dtype)

commands = [
    "Set an alarm for seven am tomorrow",
    "What is the weather in London?",
    "What time is it in Tokyo?"
]

for command in commands:
    prompt = (
        "Convert this command into the required JSON.\n"
        f"Command: {command}\n"
        "Output:"
    )

    inputs = tokenizer(
        prompt,
        return_tensors="pt"
    )

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=100,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id
        )

    generated = outputs[0][inputs["input_ids"].shape[1]:]

    result = tokenizer.decode(
        generated,
        skip_special_tokens=True
    ).strip()

    print("\nCommand:", command)
    print("Model output:", result)

    try:
        parsed = json.loads(result)

        if isinstance(parsed, dict) and len(parsed) == 4:
            print("Valid JSON: YES")
            print("Parsed:", parsed)
        else:
            print("Valid JSON: NO - Incorrect structure")

    except json.JSONDecodeError:
        print("Valid JSON: NO")


if __name__ == "__main__":
    pass

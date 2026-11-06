
import os
import sys
import json
import csv
import yaml
import torch
from pathlib import Path
from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    Trainer,
    TrainingArguments,
    set_seed
)

BASE = Path(__file__).resolve().parent.parent


class CommandDataset(Dataset):
    def __init__(self, records, tokenizer, max_length):
        self.items = []

        for record in records:
            prompt = f"Command: {record['command']}\nJSON:"

            target = json.dumps(
                record["output"],
                ensure_ascii=False,
                separators=(",", ":")
            ) + tokenizer.eos_token

            prompt_ids = tokenizer(
                prompt,
                add_special_tokens=True
            )["input_ids"]

            target_ids = tokenizer(
                target,
                add_special_tokens=False
            )["input_ids"]

            if len(target_ids) >= max_length:
                target_ids = target_ids[:max_length]
                prompt_ids = []
            else:
                available_prompt = max_length - len(target_ids)
                prompt_ids = prompt_ids[-available_prompt:]

            input_ids = prompt_ids + target_ids
            labels = [-100] * len(prompt_ids) + target_ids.copy()
            attention_mask = [1] * len(input_ids)

            padding_length = max_length - len(input_ids)

            input_ids += [tokenizer.pad_token_id] * padding_length
            labels += [-100] * padding_length
            attention_mask += [0] * padding_length

            self.items.append({
                "input_ids": torch.tensor(input_ids, dtype=torch.long),
                "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
                "labels": torch.tensor(labels, dtype=torch.long)
            })

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        return self.items[index]


def main():
    config_name = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    config_path = BASE / "training" / config_name

    if not config_path.is_file():
        raise FileNotFoundError(f"Config not found: {config_path}")

    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    set_seed(config["training"]["seed"])

    data_path = BASE / config["data"]["train_file"]

    records = [
        json.loads(line)
        for line in data_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    subset = int(os.getenv("SUBSET", "0"))
    max_samples = config["data"]["max_train_samples"]
    limit = min(subset, max_samples) if subset > 0 else max_samples
    records = records[:limit]

    if not records:
        raise ValueError("No training records found.")

    print("Configuration:", config_name)
    print("Training records:", len(records))
    print("Device: CPU")
    print("Precision: FP32")

    tokenizer = AutoTokenizer.from_pretrained(config["model_name"])

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        config["model_name"],
        dtype=torch.float32
    )

    model.config.pad_token_id = tokenizer.pad_token_id

    model_dtype = next(model.parameters()).dtype
    print("Model dtype:", model_dtype)

    if model_dtype != torch.float32:
        raise RuntimeError("Model is not loaded in FP32.")

    dataset = CommandDataset(
        records,
        tokenizer,
        config["training"]["max_length"]
    )

    output_dir = BASE / config["training"]["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=config["training"]["num_train_epochs"],
        per_device_train_batch_size=config["training"]["per_device_train_batch_size"],
        gradient_accumulation_steps=config["training"]["gradient_accumulation_steps"],
        learning_rate=config["training"]["learning_rate"],
        max_grad_norm=1.0,
        logging_steps=config["training"]["logging_steps"],
        logging_strategy="steps",
        save_strategy="no",
        seed=config["training"]["seed"],
        use_cpu=True,
        fp16=False,
        bf16=False,
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=dataset
    )

    trainer.train()
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    loss_csv = BASE / "training" / (
        "loss_v2.csv" if config_name == "config_v2.yaml"
        else "loss.csv"
    )

    with open(loss_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["epoch", "loss", "grad_norm", "learning_rate"]
        )
        writer.writeheader()

        for row in trainer.state.log_history:
            if "loss" in row:
                writer.writerow({
                    "epoch": row.get("epoch", ""),
                    "loss": row.get("loss", ""),
                    "grad_norm": row.get("grad_norm", ""),
                    "learning_rate": row.get("learning_rate", "")
                })

    print("Loss log saved:", loss_csv)
    print("Training complete:", output_dir)


if __name__ == "__main__":
    main()

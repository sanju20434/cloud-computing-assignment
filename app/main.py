
import os
import json
import tempfile
from pathlib import Path

import boto3
import torch
from boto3.s3.transfer import TransferConfig
from botocore.config import Config
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from transformers import AutoTokenizer, AutoModelForCausalLM


# Environment variables
MODEL_URI = os.getenv("MODEL_URI", "s3://models/v2/")
MODEL_VERSION = os.getenv("MODEL_VERSION", "v2")
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://127.0.0.1:8333")
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "100"))
FAULT_INJECT = os.getenv("FAULT_INJECT", "false").lower() == "true"

app = FastAPI(title="Command Parsing API")

model = None
tokenizer = None
model_ready = False
served_by = os.getenv("HOSTNAME", "local-api")


# Request schema
class ParseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    command: str = Field(min_length=1)


# Response schema
class ParseResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: str
    date: str | None
    time: str | None
    place: str | None


ALLOWED_INTENTS = {
    "alarm_set",
    "alarm_query",
    "calendar_set",
    "calendar_query",
    "calendar_remove",
    "weather_query",
    "datetime_query",
    "recommendation_events",
}


def download_model():
    global model, tokenizer, model_ready

    if not MODEL_URI.startswith("s3://"):
        raise ValueError("MODEL_URI must start with s3://")

    bucket, prefix = MODEL_URI[5:].split("/", 1)
    prefix = prefix.rstrip("/") + "/"

    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    if not access_key or not secret_key:
        raise RuntimeError("AWS credentials are required")

    s3 = boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="us-east-1",
        config=Config(
            signature_version="s3v4",
            connect_timeout=30,
            read_timeout=300,
            retries={"max_attempts": 5, "mode": "standard"},
        ),
    )

    model_dir = Path(tempfile.gettempdir()) / "command-parser-model"
    model_dir.mkdir(parents=True, exist_ok=True)

    response = s3.list_objects_v2(
        Bucket=bucket,
        Prefix=prefix,
    )

    objects = response.get("Contents", [])

    if not objects:
        raise RuntimeError(f"No model files found at {MODEL_URI}")

    # Download model files without parallel transfer threads
    transfer_config = TransferConfig(use_threads=False)

    for obj in objects:
        key = obj["Key"]

        if key.endswith("/"):
            continue

        filename = key[len(prefix):]

        if not filename or "/" in filename:
            continue

        destination = model_dir / filename

        print(f"Downloading {key} ...")

        s3.download_file(
            bucket,
            key,
            str(destination),
            Config=transfer_config,
        )

        print(f"Downloaded {filename}")

    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(
        str(model_dir),
        local_files_only=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        str(model_dir),
        torch_dtype=torch.float32,
        local_files_only=True,
    )

    model.eval()
    model_ready = True

    print(f"Model {MODEL_VERSION} loaded successfully")


@app.on_event("startup")
def startup_event():
    download_model()


@app.get("/healthz")
def healthz():
    return {"status": "healthy"}


@app.get("/readyz")
def readyz():
    if not model_ready:
        raise HTTPException(
            status_code=503,
            detail="model_not_ready",
        )

    return {
        "status": "ready",
        "model_version": MODEL_VERSION,
    }


@app.post("/parse")
def parse_command(payload: ParseRequest, request: Request):

    if not model_ready:
        raise HTTPException(
            status_code=503,
            detail="model_not_ready",
        )

    if FAULT_INJECT:
        return JSONResponse(
            status_code=500,
            content={"error": "invalid_model_output"},
        )

    prompt = (
        "Convert the command into exactly one JSON object with keys "
        "intent, date, time, place. Use null for missing slots.\n"
        f"Command: {payload.command}\nJSON:"
    )

    try:
        inputs = tokenizer(
            prompt,
            return_tensors="pt",
        )

        with torch.inference_mode():
            output = model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )

        generated = tokenizer.decode(
            output[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True,
        )

        start = generated.find("{")
        end = generated.rfind("}") + 1

        if start < 0 or end <= start:
            raise ValueError("No JSON object generated")

        result = json.loads(generated[start:end])

        required = {"intent", "date", "time", "place"}

        if not isinstance(result, dict):
            raise ValueError("Output must be a JSON object")

        if set(result.keys()) != required:
            raise ValueError("Invalid JSON keys")

        if result["intent"] not in ALLOWED_INTENTS:
            raise ValueError("Invalid intent")

        for slot in ("date", "time", "place"):
            if result[slot] is not None and not isinstance(
                result[slot], str
            ):
                raise ValueError(f"Invalid {slot} type")

        # Validate response before sending
        validated = ParseResponse(**result)

        return JSONResponse(
            content=validated.model_dump(),
            headers={
                "X-Model-Version": MODEL_VERSION,
                "X-Served-By": served_by,
            },
        )

    except Exception as exc:
        print(f"Invalid model output: {exc}")

        raise HTTPException(
            status_code=500,
            detail={"error": "invalid_model_output"},
        )


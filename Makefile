.PHONY: up down train test

up:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/up.ps1

down:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/down.ps1

train:
	python training/train.py

test:
	python scripts/test_teacher.py
	python scripts/test_all_intents.py
	python tools/nacl_sim.py network/nacl.json network/packets_sample.jsonl --check

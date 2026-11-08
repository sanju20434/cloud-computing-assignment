# Cloud Computing Mini Project

## Knowledge Distillation and Deployment of a Lightweight Command-Parsing Model

This project is part of the Cloud Computing (CS3081) mini project. The main objective is to train a lightweight language model using teacher-generated data and deploy it as an API service on a local Kubernetes-based cloud environment.

The project focuses on model training, Docker containerization, Kubernetes deployment, networking, testing, and performance evaluation.

## Project Overview

The system uses a teacher-student approach:

1. A collection of natural-language commands is prepared.
2. A teacher model generates structured JSON responses.
3. The generated data is cleaned and validated.
4. A lightweight Pythia-70M student model is fine-tuned.
5. The trained model is used through a FastAPI application.
6. The application is containerized using Docker and deployed on Kubernetes.
7. The deployment is tested for performance, reliability, and resource usage.

## Technologies Used

* Python
* PyTorch and Hugging Face Transformers
* FastAPI
* Docker
* Kubernetes (k3d / k3s)
* SeaweedFS (object storage)
* Locust (load testing)
* Git and GitHub Actions

## Project Structure

```text
cloud\_assignment/
│
├── app/                 # FastAPI application
├── cluster/             # Local Kubernetes cluster configuration
├── data/                # Commands, validation data and schema
├── datasets/             # Cleaned training datasets
├── k8s/                 # Kubernetes deployment manifests
├── models/              # Model configuration and tokenizer files
├── network/             # Subnet and NACL configuration
├── prompts/             # Teacher prompt
├── raw\_outputs/         # Teacher model outputs
├── raw\_outputs\_retry/   # Retry outputs
├── results/             # Evaluation and load-test results
├── scripts/             # Data processing and testing scripts
├── storage/             # SeaweedFS configuration
├── tools/               # Scoring, load testing and NACL tools
├── training/            # Model training and evaluation code
│
├── .github/workflows/   # GitHub Actions workflow
├── Dockerfile
├── Makefile
├── requirements.txt
└── AI\_USE.md
```

## Requirements

Install or configure the following tools before running the project:

* Python 3
* Docker Desktop
* kubectl
* k3d
* GNU Make
* Git

Python dependencies can be installed using:

```powershell
pip install -r requirements.txt
```

## Setup and Deployment

Run the following commands from the project root directory:

```powershell
make up
```

This command uses the project Makefile to build and deploy the application.

To run the project tests:

```powershell
make test
```

To stop and remove the local deployment:

```powershell
make down
```

## Testing and Evaluation

### Model Evaluation

Use the scoring script to evaluate predictions against the validation dataset:

```powershell
python tools/score.py results/student\_v2\_predictions.jsonl data/validation.jsonl
```

To apply a minimum JSON validity threshold of 95%:

```powershell
python tools/score.py results/student\_v2\_predictions.jsonl data/validation.jsonl --min-validity 95
```

### Network ACL Testing

```powershell
python tools/nacl\_sim.py network/nacl.json network/packets\_sample.jsonl --check
```

### API Load Testing

Install Locust:

```powershell
pip install locust
```

Run the load test against the deployed API:

```powershell
python -m locust -f tools/locustfile.py --headless --users 4 --spawn-rate 4 --run-time 2m --host http://localhost:8080 --csv results/loadtest
```

The test generates request statistics, failure information, and load-test history in the `results/` directory.

## Results

The `results/` directory contains model evaluation outputs, API performance measurements, Docker resource information, Locust reports, and the project review.

## Model Artifacts

Model weight files are excluded from the Git repository. Model artifacts, version information, and related metadata are maintained separately from the source code.

## Dataset Reference

The command dataset is based on SLURP:

Bastianelli et al., EMNLP 2020.

Dataset: https://github.com/pswietojanski/slurp

License: CC BY 4.0.

## \## Author

## 

## \*\*Name:\*\* Sandeep Kumar Saini  

## \*\*Roll Number:\*\* 230101029  

## \*\*Department:\*\* Computer Science and Engineering  

## \*\*Institute:\*\* IIIT Manipur

## 

## \## GitHub Repository

## 

## https://github.com/sanju20434/cloud-computing-assignment

## 

## \## Model Release

## 

## https://github.com/sanju20434/cloud-computing-assignment/releases/tag/v1.0


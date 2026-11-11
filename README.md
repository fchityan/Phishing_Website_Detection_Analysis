# Phishing Website Detection ML

## Project Overview

This machine learning project explores how website, HTML, metadata, and hosting features can distinguish phishing websites from legitimate ones. It extends an exploratory notebook into a reproducible classification workflow with model evaluation and an API for scoring structured website features.

## Problem

Phishing detection must balance two risks: missing malicious websites and incorrectly flagging legitimate ones. The project emphasizes detecting phishing cases while also measuring false positives.

## Approach

- Clean and validate website feature data, including missing and invalid values.
- Compare Logistic Regression, Random Forest, and Extra Trees classifiers.
- Use stratified training, validation, and held-out test splits.
- Select a decision threshold using phishing-class F2, which emphasizes recall.
- Package the selected model for feature-based prediction and monitoring.

The dataset uses **0 = phishing** and **1 = legitimate**.

## Key Features

- Reproducible training, model comparison, and evaluation
- Single-record and batch predictions through a FastAPI service
- Input validation and feature-drift reporting
- Automated tests and a containerized application reference

## Results and Limitations

The repository includes a framework for comparing models and evaluating a held-out test set. **No numerical detection-performance claim is published**, because the source dataset is not included and the updated pipeline has not been rerun against it here. This is a feature-based ML reference, not a verified live phishing-blocking service.

## Technology Stack

- **Language, data and exploration:** Python, NumPy, pandas, Jupyter Notebook, Matplotlib, Seaborn, SQLite (exploratory notebook)
- **Machine learning:** scikit-learn (Logistic Regression, Random Forest, Extra Trees), joblib for model serialization
- **API and validation:** FastAPI, Uvicorn, Pydantic, HTTPX
- **Monitoring and operations:** Prometheus Python client, feature-drift checks, Docker, Kubernetes
- **Testing and automation:** pytest, GitHub Actions CI

## Explore the Project

- [Original exploratory notebook](phishing_website_detection.ipynb)
- [Technical guide — methods, commands, and architecture](docs/technical_guide.md)
- [Deployment and operations notes](docs/production_runbook.md)
- [Security guidance](SECURITY.md)

The training dataset must be supplied separately; see the technical guide for the expected schema and commands.

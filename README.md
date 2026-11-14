# MLPrep AI — Intelligent Dataset Preparation

> A full-stack data-preparation workspace for inspecting CSV quality, identifying data issues, and preparing cleaner tabular data for machine-learning workflows.

## Product vision
Machine-learning projects often spend more time understanding and preparing data than fitting a model. MLPrep AI provides a visual workspace for uploading a CSV, inspecting its structure, reviewing missing values and duplicate rows, and requesting automated cleaning through a local Python API.

## Frontend capabilities
- React + TypeScript interface powered by Vite.
- CSV upload through a file picker or drag-and-drop workflow.
- Browser-side parsing using Papa Parse.
- Dataset overview with row and column counts.
- Duplicate-row detection.
- Per-column missing-value counts and percentages.
- Heuristic column-type detection for numeric, date, and text values.
- Cleaning workflow that sends the selected file to the backend.
- Result state for presenting the API response and prepared output.

## Backend capabilities
The FastAPI service in `main.py` provides the data-processing layer. Its visible implementation includes:
- CSV ingestion and tabular validation.
- Column-name normalization and duplicate-name handling.
- Detection of common missing-value markers.
- Conservative inference of numeric columns when values are consistently numeric.
- Detection of possible identifier and constant columns for review.
- Numeric sanity checks, including handling infinite values and selected domain-specific invalid values.
- A local API intended to connect the browser interface to server-side cleaning and downloadable results.

## Technology stack
- Frontend: React, TypeScript, Vite, Papa Parse.
- Backend: Python, FastAPI, Pandas, NumPy.
- API communication: HTTP multipart file upload.

## Requirements
- Node.js and npm.
- Python 3.10+.
- Python packages: `fastapi`, `uvicorn`, `pandas`, `numpy`, and `python-multipart`.

## Install
Clone the repository:
```bash
git clone https://github.com/aloslsaid/ai-data-clening-.git
cd ai-data-clening-
```

Install frontend dependencies:
```bash
npm install
```

Create a Python environment and install backend dependencies:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
python -m pip install --upgrade pip
pip install fastapi uvicorn pandas numpy python-multipart
```

## Run locally
Start the backend in one terminal:
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
Start the frontend in another terminal:
```bash
npm run dev
```
Open the Vite URL shown in the terminal. The current frontend calls the local API at `http://127.0.0.1:8000`; keep that address or update the frontend API URL in your own configuration if you change the backend port.

## Build checks
```bash
npm run build
npm run lint
```

## Data safety
Dataset profiling and cleaning are not substitutes for understanding the meaning of columns. Automated rules can misinterpret domain-specific values. Review the generated report and retain an untouched copy of source data. Do not upload confidential or personally identifiable datasets to services you do not control.

## Skills demonstrated
Data quality analysis · CSV processing · Full-stack development · FastAPI · React · TypeScript · Pandas · Missing-data handling · Data validation

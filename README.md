# MLPrep AI

A CSV cleaning and data-quality reporting API with a React/Vite interface. The backend performs conservative, rule-based transformations and reports decisions; it does not execute generated code or claim that every cleaned dataset is ready for every ML task.

## Features
- CSV upload with a 50 MB server-side limit.
- Column-name normalization and duplicate-row removal.
- Conservative numeric type inference and invalid-value checks.
- Date parsing and calendar feature generation.
- Missing-value decisions with a review threshold.
- SQLite-based structural sanity check using an in-memory database.
- Preview response and cleaned CSV download endpoint.

## Requirements
- Python 3.10+
- Node.js 20+ and npm

## Backend setup

From the repository root:

Windows PowerShell:
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

- API root: `http://127.0.0.1:8000/`
- Swagger: `http://127.0.0.1:8000/docs`
- Health is available from the root response.

## Frontend setup

Open a second terminal in the repository root:

```bash
npm install
npm run dev
```

Vite runs on its default local development URL. The current frontend calls the API at `http://127.0.0.1:8000`.

Create a production build with:
```bash
npm run build
```

## API

### `POST /api/clean`
Multipart field: `file` (CSV). Returns a cleaning report and a 10-row preview.

### `POST /api/clean/download`
Multipart field: `file` (CSV). Returns the cleaned CSV as a download.

## Data handling and security
- Uploaded CSV content is processed in memory; the backend does not persist uploaded files.
- Upload reads are bounded to 50 MB plus one byte for limit detection.
- Output filenames are reduced to a safe basename before being placed in the download header.
- Only explicit localhost frontend origins are allowed by CORS.
- Review the cleaning report: automatic cleaning is heuristic. Columns with high missingness are left for review, and suspicious identifier/constant columns are flagged rather than automatically removed.
- Do not upload confidential or regulated data unless authorized and comfortable with your deployment's data handling.

## Tests

```bash
python -m pytest -q
```

The tests cover CSV cleaning, missing-value handling, duplicate removal, filename sanitization, and upload validation.

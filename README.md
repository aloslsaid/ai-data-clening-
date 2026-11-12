# MLPrep AI

MLPrep AI is a CSV inspection and cleaning workspace with a React + TypeScript + Vite frontend and a FastAPI backend. The browser provides a quick preview and data-quality summary; the API performs a separate cleaning pass and returns a report or cleaned CSV.

## Features

- CSV upload and browser-side preview.
- Row/column counts, duplicate detection and per-column missing-value/type summaries.
- Backend column-name normalization and common missing-marker handling.
- Duplicate-row removal, conservative numeric inference and basic domain checks.
- Date-derived features where parsing confidence is sufficient.
- Missing-value decisions with a review path for high-missingness columns.
- CSV export and an audit-style cleaning report.

## Requirements

- Node.js 20+ and npm.
- Python 3.10+.

## Run the frontend

From the repository root:

```bash
npm ci
npm run dev
```

Open the local Vite URL printed in the terminal. Production build and lint commands:

```bash
npm run build
npm run lint
```

## Run the backend

In a second terminal, from the repository root:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Check `http://127.0.0.1:8000/` for the service status. The frontend currently calls the local API at `http://127.0.0.1:8000/api/clean`; keep the backend running while using the cleaning action.

## API

- `POST /api/clean`: accepts multipart field `file` containing a CSV and returns a report plus a preview.
- `POST /api/clean/download`: accepts the same upload and streams the cleaned CSV.

The backend currently enforces a 50 MB application-level file limit. Do not expose the development server directly to the public internet.

## Data handling and limitations

Cleaning is heuristic, not domain-specific truth. Suspicious identifiers are flagged rather than automatically removed; high-missingness columns are left for review; some inferred conversions may require human confirmation. Keep an untouched copy of the original dataset and review the report before training a model.

Uploaded CSV content is sent to the configured backend. Use only data you are authorized to process. Avoid committing datasets, exports, secrets, or logs.

## Tests

Run backend tests from the repository root:

```bash
python -m pytest
```

Run frontend checks with `npm run build` and `npm run lint`. These commands have not been represented as passing until executed in CI or a local environment.

## License

No license is declared. All rights reserved unless the repository owner adds an explicit license.

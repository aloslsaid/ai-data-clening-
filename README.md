# MLPrep AI

MLPrep AI is a browser-based CSV inspection and cleaning interface built with React, TypeScript, and Vite. It parses CSV files in the browser, summarizes rows/columns, detects duplicate rows and missing values, and displays basic column-type information. The interface also attempts to call a local cleaning API at `http://127.0.0.1:8000/api/clean` and a download endpoint.

## Frontend setup

Requirements: Node.js and npm.

```sh
npm install
npm run dev
```

Open the local URL printed by Vite. For a production build and lint check:

```sh
npm run build
npm run lint
```

## Cleaning API

The tracked root contains a `main.py` bytecode file (`main.cpython-314.pyc`) but no corresponding `main.py` source implementation or Python dependency manifest. Therefore, CSV inspection in the browser is distinct from the server-side clean/download actions, and the backend is not currently documented as runnable from this repository. The cleaning buttons require a separately available service implementing the endpoints in `App.tsx`; do not assume that one is included.

## Data and privacy

CSV inspection runs in the browser; when you request cleaning, the selected file is sent to the configured API. Do not upload sensitive data unless you control and trust that service. The UI's detected types and quality summaries are heuristics, not a guarantee that a dataset is ready for a particular model.

## Tests

No test script is defined in `package.json`. `npm run build` and `npm run lint` provide the available build/static checks; their results must be run and recorded in the environment where changes are made. Add tests for CSV parsing and cleaning interactions.

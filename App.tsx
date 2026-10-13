
import { useRef, useState } from "react";
import Papa from "papaparse";
import "./App.css";
type DataRow = Record<string, string>;

type ColumnReport = {
  name: string;
  missing: number;
  missingPercent: number;
  type: string;
};

type DatasetReport = {
  rows: number;
  columns: number;
  duplicates: number;
  columnReports: ColumnReport[];
  data: DataRow[];
};

function analyzeCSV(data: DataRow[]): DatasetReport {
  const columns = Object.keys(data[0] ?? {});

  const normalizedRows = data.map((row) =>
    columns.map((column) => (row[column] ?? "").trim())
  );

  const seen = new Set<string>();
  let duplicates = 0;

  for (const row of normalizedRows) {
    const key = JSON.stringify(row);

    if (seen.has(key)) {
      duplicates++;
    } else {
      seen.add(key);
    }
  }

  const columnReports: ColumnReport[] = columns.map((name) => {
    const values = data.map((row) => (row[name] ?? "").trim());

    const missing = values.filter(
      (value) => value === "" || value.toLowerCase() === "null" ||
        value.toLowerCase() === "na" ||
        value.toLowerCase() === "n/a"
    ).length;

    const present = values.filter(
      (value) => value !== "" && value.toLowerCase() !== "null" &&
        value.toLowerCase() !== "na" &&
        value.toLowerCase() !== "n/a"
    );

    const numericCount = present.filter(
      (value) => Number.isFinite(Number(value))
    ).length;

    const dateCount = present.filter(
      (value) => /^\d{4}-\d{1,2}-\d{1,2}$/.test(value)
    ).length;

    let type = "Text";

    if (present.length > 0 && dateCount === present.length) {
      type = "Date";
    } else if (present.length > 0 && numericCount === present.length) {
      type = "Numeric";
    }

    return {
      name,
      missing,
      missingPercent: data.length
        ? (missing / data.length) * 100
        : 0,
      type,
    };
  });

  return {
    rows: data.length,
    columns: columns.length,
    duplicates,
    columnReports,
    data,
  };
}
function App() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [report, setReport] = useState<DatasetReport | null>(null);
const [analyzing, setAnalyzing] = useState(false);
const [cleaning, setCleaning] = useState(false);
const [cleanResult, setCleanResult] = useState<any>(null);

  function chooseFile(selected?: File) {
    if (!selected) return;

    if (!selected.name.toLowerCase().endsWith(".csv")) {
      alert("Please upload a CSV file.");
      return;
    }

    setFile(selected);
inspectFile(selected);


  }
function inspectFile(selected: File) {
  setAnalyzing(true);
  setReport(null);

  Papa.parse<DataRow>(selected, {
    header: true,
    skipEmptyLines: "greedy",
    complete: (result) => {
      const data = result.data.filter((row) =>
        Object.values(row).some((value) => value.trim() !== "")
      );

      if (result.errors.length > 0 || !result.meta.fields?.length) {
        console.warn("CSV parsing warnings:", result.errors);
      }

      if (!result.meta.fields?.length) {
        alert("Could not find column headers in this CSV file.");
        setAnalyzing(false);
        return;
      }

      setReport(analyzeCSV(data));
      setAnalyzing(false);
    },
    error: (error) => {
      alert(`Could not read the file: ${error.message}`);
      setAnalyzing(false);
    },
  });
}

async function cleanDataset(selected: File) {
  setCleaning(true);
  setCleanResult(null);

  try {
    const formData = new FormData();
    formData.append("file", selected);

    const response = await fetch("http://127.0.0.1:8000/api/clean", {
      method: "POST",
      body: formData,
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.detail || "Could not clean this dataset.");
    }

    setCleanResult(result);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Something went wrong.";

    alert(`Cleaning failed: ${message}`);
  } finally {
    setCleaning(false);
  }
}

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#">
          <span className="brand-icon">M</span>
          <span>MLPrep<span className="brand-ai"> AI</span></span>
        </a>

        <div className="side-label">WORKSPACE</div>

        <nav className="navigation">
          <a className="nav-item active" href="#overview">
            <span>◈</span> Overview
          </a>
          <a className="nav-item" href="#upload">
            <span>↑</span> Clean dataset
          </a>
          <a className="nav-item" href="#features">
            <span>✳</span> Feature engineering
          </a>
          <a className="nav-item" href="#reports">
            <span>▤</span> Reports
          </a>
        </nav>

        <div className="sidebar-bottom">
          <div className="plan-card">
            <div className="plan-icon">✦</div>
            <strong>Your data, ready for AI.</strong>
            <p>Turn raw CSV files into cleaner datasets.</p>
          </div>
          <div className="profile">
            <div className="avatar">A</div>
            <div>
              <strong>aloslsaid</strong>
              <p>Workspace owner</p>
            </div>
            <span className="profile-dots">•••</span>
          </div>
        </div>
      </aside>

      <main className="main-content" id="overview">
        <header className="topbar">
          <div className="breadcrumb">Workspace <span>/</span> Overview</div>
          <div className="topbar-right">
            <span className="status-dot" />
            Local workspace
            <div className="top-avatar">A</div>
          </div>
        </header>

        <section className="hero">
          <div className="eyebrow">
            <span className="sparkle">✦</span>
            YOUR AI DATA WORKSPACE
          </div>
          <h1>Make your data<br /> <span>model-ready.</span></h1>
          <p className="hero-description">
            Clean messy datasets, discover useful features, and prepare
            your data for machine learning — all in one place.
          </p>
        </section>

        <section
          id="upload"
          className={`upload-card ${dragging ? "dragging" : ""}`}
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            chooseFile(event.dataTransfer.files[0]);
          }}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".csv,text/csv"
            hidden
            onChange={(event) => chooseFile(event.target.files?.[0])}
          />

          <div className="upload-icon">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5" />
              <path d="M5 14.5v4A1.5 1.5 0 0 0 6.5 20h11a1.5 1.5 0 0 0 1.5-1.5v-4" />
            </svg>
          </div>

          {file ? (
            <>
              <h2>{file.name}</h2>
              <p className="upload-subtitle">
                {(file.size / 1024).toFixed(1)} KB · CSV selected
              </p>
              <div className="file-actions">
                <button
                  className="secondary-button"
                  onClick={() => {
                    setFile(null);
                    if (inputRef.current) inputRef.current.value = "";
                  }}
                >
                  Remove file
                </button>
                <span className="selected-status">✓ File selected</span>
                
<button
  className="primary-button"
  disabled={cleaning}
  onClick={() => file && cleanDataset(file)}
>
  {cleaning ? "Cleaning dataset..." : "Clean Dataset"}
</button>

              </div>
              <p className="notice">
                File selection works. Data cleaning will be connected next.
              </p>
            </>
          ) : (
            <>
              <h2>Drop your CSV file here</h2>
              <p className="upload-subtitle">
                Start with your raw data. We’ll help you prepare it.
              </p>
              <button
                className="primary-button"
                onClick={() => inputRef.current?.click()}
              >
                <span>↑</span> Browse files
              </button>
              <p className="file-hint">CSV files only · Choose a file from your device</p>
            </>
          )}
        </section>
```tsx
{analyzing && (
  <section className="report-panel">
    <h2>Analyzing your dataset...</h2>
    <p>Reading columns and checking data quality.</p>
  </section>
)}

{report && (
  <section className="report-panel">
    <div className="report-heading">
      <div>
        <span className="report-eyebrow">DATA QUALITY REPORT</span>
        <h2>Dataset overview</h2>
        <p>Initial inspection only — your original file is unchanged.</p>
      </div>
      <span className="report-badge">✓ Analyzed</span>
    </div>

    <div className="stats-grid">
      <div className="stat-card">
        <span>Rows</span>
        <strong>{report.rows.toLocaleString()}</strong>
      </div>
      <div className="stat-card">
        <span>Columns</span>
        <strong>{report.columns.toLocaleString()}</strong>
      </div>
      <div className="stat-card">
        <span>Duplicate rows</span>
        <strong>{report.duplicates.toLocaleString()}</strong>
      </div>
      <div className="stat-card">
        <span>Missing cells</span>
        <strong>
          {report.columnReports
            .reduce((sum, column) => sum + column.missing, 0)
            .toLocaleString()}
        </strong>
      </div>
    </div>

    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th>Column</th>
            <th>Detected type</th>
            <th>Missing values</th>
            <th>Missing %</th>
          </tr>
        </thead>
        <tbody>
          {report.columnReports.map((column) => (
            <tr key={column.name}>
              <td>{column.name}</td>
              <td>
                <span className="type-tag">{column.type}</span>
              </td>
              <td>{column.missing}</td>
              <td>
                <span
                  className={
                    column.missingPercent > 10
                      ? "missing-warning"
                      : "missing-normal"
                  }
                >
                  {column.missingPercent.toFixed(1)}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>

    <p className="report-note">
      Columns with more than 10% missing values are flagged for review,
      not automatically deleted.
    </p>
  </section>
)}

{cleanResult && (
  <section className="report-section">
    <h2>Cleaning Results</h2>
    <p>Dataset processed successfully.</p>

    <pre>
      {JSON.stringify(cleanResult.report, null, 2)}
    </pre>

    <button
      className="primary-button"
      onClick={async () => {
        if (!file) return;

        try {
          const formData = new FormData();
          formData.append("file", file);

          const response = await fetch(
            "http://127.0.0.1:8000/api/clean/download",
            {
              method: "POST",
              body: formData,
            }
          );

          if (!response.ok) {
            throw new Error("Failed to download cleaned CSV.");
          }

          const blob = await response.blob();
          const url = URL.createObjectURL(blob);
          const link = document.createElement("a");

          link.href = url;
          link.download = `cleaned_${file.name}`;
          document.body.appendChild(link);
          link.click();
          link.remove();
          URL.revokeObjectURL(url);
        } catch (error) {
          alert(
            error instanceof Error
              ? error.message
              : "Download failed."
          );
        }
      }}
    >
      Download Cleaned CSV
    </button>
  </section>
)}

```
        <section className="section-heading" id="features">
          <div>
            <h2>Everything your data needs</h2>
            <p>A clear workflow from raw data to machine-learning-ready files.</p>
          </div>
          <span className="coming-label">WORKSPACE</span>
        </section>

        <section className="feature-grid">
          <article className="feature-card">
            <div className="feature-icon purple">⌁</div>
            <h3>Smart cleaning</h3>
            <p>
              Identify missing values, duplicate rows, inconsistent data,
              and suspicious values.
            </p>
            <div className="feature-footer">
              <span className="mini-dot purple-dot" /> Data quality
            </div>
          </article>

          <article className="feature-card">
            <div className="feature-icon blue">✳</div>
            <h3>Feature engineering</h3>
            <p>
              Discover useful date parts, numerical transformations,
              ratios, and category features.
            </p>
            <div className="feature-footer">
              <span className="mini-dot blue-dot" /> Feature discovery
            </div>
          </article>

          <article className="feature-card" id="reports">
            <div className="feature-icon green">▤</div>
            <h3>Transparent reports</h3>
            <p>
              Understand what changed, which columns were affected,
              and why each action was suggested.
            </p>
            <div className="feature-footer">
              <span className="mini-dot green-dot" /> Change history
            </div>
          </article>
        </section>

        <section className="workflow">
          <div className="workflow-title">
            <span className="workflow-symbol">✦</span>
            <div>
              <h2>Your workflow</h2>
              <p>Four steps to a better dataset.</p>
            </div>
          </div>

          <div className="workflow-steps">
            <div className="workflow-step current">
              <span>01</span>
              <strong>Upload</strong>
              <p>Choose your CSV</p>
            </div>
            <div className="step-line" />
            <div className="workflow-step">
              <span>02</span>
              <strong>Inspect</strong>
              <p>Analyze data quality</p>
            </div>
            <div className="step-line" />
            <div className="workflow-step">
              <span>03</span>
              <strong>Transform</strong>
              <p>Clean and create features</p>
            </div>
            <div className="step-line" />
            <div className="workflow-step">
              <span>04</span>
              <strong>Export</strong>
              <p>Download the results</p>
            </div>
          </div>
        </section>

        <footer className="page-footer">
          <span>MLPrep AI <span className="footer-separator">·</span> Built for better data</span>
          <span className="watermark">@aloslsaid</span>
          <span>Prepare with confidence <span className="footer-sparkle">✦</span></span>
        </footer>
      </main>
    </div>
  );
}

export default App;

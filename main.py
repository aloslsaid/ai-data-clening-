
from __future__ import annotations

import io
import re
import sqlite3
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse


app = FastAPI(title="MLPrep AI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MISSING_MARKERS = {"", "null", "none", "na", "n/a", "nan", "missing", "unknown"}

ID_NAME_PATTERN = re.compile(
    r"(^id$|_id$|^id_|uuid|row.?number|index|record.?number)",
    re.IGNORECASE,
)

DATE_PATTERN = re.compile(
    r"(date|datetime|timestamp|created_at|updated_at|"
    r"birth.?date|purchase.?date|order.?date)",
    re.IGNORECASE,
)


def clean_column_names(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    original = list(df.columns)
    new_columns = []
    used = set()

    for col in original:
        name = re.sub(r"\s+", "_", str(col).strip())
        name = re.sub(r"[^\w]", "_", name)
        name = name.strip("_") or "column"

        base = name
        counter = 2
        while name.lower() in used:
            name = f"{base}_{counter}"
            counter += 1

        used.add(name.lower())
        new_columns.append(name)

    df.columns = new_columns
    changes = []

    for old, new in zip(original, new_columns):
        if str(old) != new:
            changes.append(f"Column name normalized: {old} -> {new}")

    return df, changes


def missing_mask(series: pd.Series) -> pd.Series:
    text = series.astype("string").str.strip().str.lower()
    return series.isna() | text.isin(MISSING_MARKERS)


def infer_numeric_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    changes = []

    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            continue

        values = df[col].astype("string").str.strip()
        nonmissing = values[~missing_mask(values)]

        if len(nonmissing) == 0:
            continue

        converted = pd.to_numeric(
            nonmissing.str.replace(",", "", regex=False),
            errors="coerce",
        )

        # Convert only when nearly all nonmissing values are numeric.
        if converted.notna().mean() >= 0.98:
            df[col] = pd.to_numeric(
                df[col].astype("string").str.replace(",", "", regex=False),
                errors="coerce",
            )
            changes.append(f"Converted '{col}' to numeric.")

    return df, changes


def find_suspicious_columns(df: pd.DataFrame) -> list[dict[str, str]]:
    flagged = []

    for col in df.columns:
        name = str(col)

        if ID_NAME_PATTERN.search(name):
            flagged.append({
                "column": name,
                "reason": (
                    "Possible identifier. Review whether it carries "
                    "predictive information before removing it."
                ),
            })

        if df[col].nunique(dropna=True) <= 1 and len(df) > 1:
            flagged.append({
                "column": name,
                "reason": "Constant column; it contains no variation.",
            })

    return flagged


def check_numeric_values(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, list[str]]:
    changes = []

    for col in df.select_dtypes(include=[np.number]).columns:
        series = df[col]

        # Infinite values cannot be used as ordinary numeric features.
        infinite_mask = series.isin([np.inf, -np.inf])
        if infinite_mask.any():
            df.loc[infinite_mask, col] = np.nan
            changes.append(
                f"Replaced {int(infinite_mask.sum())} infinite value(s) "
                f"in '{col}' with missing values."
            )

        name = col.lower()

        # Apply only clear domain constraints; do not guess general ranges.
        nonnegative_keywords = (
            "age", "price", "cost", "amount", "quantity", "qty",
            "count", "distance", "weight", "height", "duration",
            "income", "salary", "consumption", "mileage",
        )

        if any(keyword in name for keyword in nonnegative_keywords):
            negative_mask = df[col] < 0
            if negative_mask.any():
                df.loc[negative_mask, col] = np.nan
                changes.append(
                    f"Set {int(negative_mask.sum())} negative value(s) "
                    f"in '{col}' to missing for review."
                )

        if re.search(r"(^|_)(age|years_old)(_|$)", name):
            invalid = (df[col] < 0) | (df[col] > 120)
            if invalid.any():
                df.loc[invalid, col] = np.nan
                changes.append(
                    f"Set {int(invalid.sum())} out-of-range age value(s) "
                    f"in '{col}' to missing."
                )

        if "percentage" in name or name.endswith("_percent"):
            invalid = (df[col] < 0) | (df[col] > 100)
            if invalid.any():
                df.loc[invalid, col] = np.nan
                changes.append(
                    f"Set {int(invalid.sum())} out-of-range percentage "
                    f"value(s) in '{col}' to missing."
                )

    return df, changes


def add_date_features(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, list[str]]:
    changes = []

    for col in list(df.columns):
        is_date_name = bool(DATE_PATTERN.search(col))
        already_datetime = pd.api.types.is_datetime64_any_dtype(df[col])

        if not is_date_name and not already_datetime:
            continue

        parsed = pd.to_datetime(df[col], errors="coerce", format="mixed")

        original_nonmissing = ~missing_mask(df[col])
        if original_nonmissing.sum() == 0:
            continue

        parse_ratio = (
            parsed[original_nonmissing].notna().mean()
            if original_nonmissing.any()
            else 0
        )

        if parse_ratio < 0.80:
            continue

        df[col] = parsed
        prefix = col

        features = {
            f"{prefix}_year": parsed.dt.year,
            f"{prefix}_month": parsed.dt.month,
            f"{prefix}_day": parsed.dt.day,
            f"{prefix}_weekday": parsed.dt.dayofweek,
            f"{prefix}_is_weekend": parsed.dt.dayofweek.isin([5, 6]).astype("Int64"),
            f"{prefix}_quarter": parsed.dt.quarter,
        }

        if parsed.dt.hour.nunique(dropna=True) > 1:
            features[f"{prefix}_hour"] = parsed.dt.hour

        for feature_name, feature_values in features.items():
            if feature_name not in df.columns:
                df[feature_name] = feature_values
                changes.append(f"Created date feature '{feature_name}'.")

        # Meteorological seasons; hemisphere assumptions should be reviewed.
        month = parsed.dt.month
        season = month.map({
            12: "winter", 1: "winter", 2: "winter",
            3: "spring", 4: "spring", 5: "spring",
            6: "summer", 7: "summer", 8: "summer",
            9: "autumn", 10: "autumn", 11: "autumn",
        })

        season_col = f"{prefix}_season"
        if season_col not in df.columns:
            df[season_col] = season
            changes.append(f"Created seasonal feature '{season_col}'.")

    return df, changes


def impute_missing_values(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict[str, Any]], list[str]]:
    decisions = []
    changes = []

    for col in list(df.columns):
        mask = missing_mask(df[col])
        missing_count = int(mask.sum())

        if missing_count == 0:
            continue

        missing_percent = (missing_count / max(len(df), 1)) * 100

        if missing_percent > 10:
            decisions.append({
                "column": col,
                "missing_count": missing_count,
                "missing_percent": round(missing_percent, 2),
                "action": "review",
                "reason": (
                    "More than 10% missing: left missing for review; "
                    "not automatically dropped or imputed."
                ),
            })
            continue

        series = df[col]

        if pd.api.types.is_numeric_dtype(series):
            median = series.median()
            if pd.isna(median):
                decisions.append({
                    "column": col,
                    "missing_count": missing_count,
                    "missing_percent": round(missing_percent, 2),
                    "action": "review",
                    "reason": "No valid numeric values available for median imputation.",
                })
                continue

            df.loc[mask, col] = median
            method = f"filled with median ({median})"

        else:
            nonmissing = series[~mask]
            if nonmissing.empty:
                decisions.append({
                    "column": col,
                    "missing_count": missing_count,
                    "missing_percent": round(missing_percent, 2),
                    "action": "review",
                    "reason": "All values are missing; no safe fill value exists.",
                })
                continue

            # For text/category fields, the most frequent value is a
            # conservative baseline; this is not a median.
            mode = nonmissing.mode()
            fill_value = mode.iloc[0] if not mode.empty else "Unknown"
            df.loc[mask, col] = fill_value
            method = f"filled with most frequent value ({fill_value})"

        changes.append(
            f"Filled {missing_count} missing value(s) in '{col}': {method}."
        )
        decisions.append({
            "column": col,
            "missing_count": missing_count,
            "missing_percent": round(missing_percent, 2),
            "action": "imputed",
            "reason": method,
        })

    return df, decisions, changes


def run_sql_checks(df: pd.DataFrame) -> dict[str, Any]:
    """Run basic dataset quality queries using an in-memory SQLite database."""
    safe_df = df.copy()

    # SQLite supports standard table columns best with ordinary string names.
    safe_df.columns = [
        re.sub(r"\W+", "_", str(col)).strip("_") or f"column_{i}"
        for i, col in enumerate(safe_df.columns)
    ]

    try:
        with sqlite3.connect(":memory:") as connection:
            safe_df.to_sql(
                "dataset",
                connection,
                if_exists="replace",
                index=False,
            )
            cursor = connection.cursor()

            cursor.execute("SELECT COUNT(*) FROM dataset")
            row_count = cursor.fetchone()[0]

            cursor.execute("PRAGMA table_info(dataset)")
            columns = [row[1] for row in cursor.fetchall()]

            return {
                "engine": "SQLite",
                "row_count": row_count,
                "columns_checked": columns,
            }
    except Exception as exc:
        return {
            "engine": "SQLite",
            "error": str(exc),
        }


def process_csv(file_bytes: bytes) -> tuple[pd.DataFrame, dict[str, Any]]:
    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read CSV: {exc}",
        ) from exc

    if len(df.columns) == 0:
        raise HTTPException(status_code=400, detail="The CSV has no columns.")

    original_rows = len(df)
    original_columns = len(df.columns)
    changes: list[str] = []

    df, name_changes = clean_column_names(df)
    changes.extend(name_changes)

    # Normalize common textual representations of missing data.
    for col in df.columns:
        if (
            pd.api.types.is_object_dtype(df[col])
            or pd.api.types.is_string_dtype(df[col])
        ):
            text = df[col].astype("string").str.strip()
            missing = text.str.lower().isin(MISSING_MARKERS)
            df.loc[missing.fillna(False), col] = np.nan
            df[col] = df[col].replace(r"^\s*$", np.nan, regex=True)

    # Drop exact duplicate rows, preserving the first occurrence.
    duplicate_count = int(df.duplicated().sum())
    if duplicate_count:
        df = df.drop_duplicates().copy()
        changes.append(f"Removed {duplicate_count} exact duplicate row(s).")

    df, numeric_changes = infer_numeric_columns(df)
    changes.extend(numeric_changes)

    flagged_columns = find_suspicious_columns(df)

    df, invalid_changes = check_numeric_values(df)
    changes.extend(invalid_changes)

    df, date_changes = add_date_features(df)
    changes.extend(date_changes)

    df, missing_decisions, missing_changes = impute_missing_values(df)
    changes.extend(missing_changes)

    # SQL is used for a basic post-cleaning structural check.
    sql_report = run_sql_checks(df)

    report = {
        "original_rows": original_rows,
        "cleaned_rows": len(df),
        "original_columns": original_columns,
        "cleaned_columns": len(df.columns),
        "duplicates_removed": duplicate_count,
        "changes": changes,
        "flagged_columns": flagged_columns,
        "missing_value_decisions": missing_decisions,
        "sql_check": sql_report,
        "remaining_missing_cells": int(df.isna().sum().sum()),
        "note": (
            "This is an initial automatic cleaning pass. It does not "
            "automatically remove suspicious columns, infer every invalid "
            "domain value, or guarantee suitability for every prediction task."
        ),
    }

    return df, report


@app.get("/")
def home() -> dict[str, str]:
    return {
        "name": "MLPrep AI",
        "status": "running",
        "owner": "@aloslsaid",
    }


@app.post("/api/clean")
async def clean_dataset(file: UploadFile = File(...)) -> dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV file.",
        )

    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="File is too large. Maximum supported size is 50 MB.",
        )

    cleaned_df, report = process_csv(content)

    return {
        "original_filename": file.filename,
        "download_filename": f"cleaned_{file.filename.rsplit('.', 1)[0]}.csv",
        "report": report,
        "preview": cleaned_df.head(10).replace({np.nan: None}).to_dict(orient="records"),
    }


@app.post("/api/clean/download")
async def clean_and_download(file: UploadFile = File(...)) -> StreamingResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV file.",
        )

    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="File is too large. Maximum supported size is 50 MB.",
        )

    cleaned_df, _report = process_csv(content)

    output = io.BytesIO()
    cleaned_df.to_csv(output, index=False, encoding="utf-8-sig")
    output.seek(0)

    filename = f"cleaned_{file.filename.rsplit('.', 1)[0]}.csv"

    return StreamingResponse(
        output,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )

import pandas as pd
from fastapi.testclient import TestClient

from main import app, process_csv, safe_output_stem


def test_csv_pipeline_removes_duplicates_and_imputes_small_numeric_gap():
    rows = 20
    frame = pd.DataFrame({
        "Record ID": [f"R{i:03d}" for i in range(rows)],
        "Customer Name": [f" Person {i} " for i in range(rows)],
        "Age": [None if i == 3 else 20 + i for i in range(rows)],
        "Revenue": [100 + i for i in range(rows)],
        "Created At": pd.date_range("2024-01-01", periods=rows).astype(str),
    })
    frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)

    cleaned, report = process_csv(frame.to_csv(index=False).encode("utf-8"))

    assert report["duplicates_removed"] == 1
    assert cleaned["Age"].isna().sum() == 0
    assert cleaned["Customer_Name"].str.startswith("Person").all()
    assert "Created_At_year" in cleaned.columns


def test_download_stem_is_safe_for_untrusted_filenames():
    assert safe_output_stem('../../bad "name".csv') == "bad_name"


def test_health_endpoint_and_upload_extension_validation():
    client = TestClient(app)
    assert client.get("/").status_code == 200
    response = client.post(
        "/api/clean",
        files={"file": ("input.txt", b"not csv", "text/plain")},
    )
    assert response.status_code == 400

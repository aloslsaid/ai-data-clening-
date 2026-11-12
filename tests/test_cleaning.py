import pandas as pd
import pytest

from main import process_csv


def test_clean_csv_normalizes_columns_and_removes_duplicates():
    raw = b"Customer Name,Age\nAlice,20\nAlice,20\nBob,30\n"
    cleaned, report = process_csv(raw)
    assert list(cleaned.columns) == ["Customer_Name", "Age"]
    assert len(cleaned) == 2
    assert report["duplicates_removed"] == 1


def test_clean_csv_preserves_high_missingness_for_review():
    raw = b"value,other\n1,x\n,x\n,x\n,x\n,x\n,x\n,x\n,x\n,x\n,x\n,x\n"
    cleaned, report = process_csv(raw)
    assert "value" in cleaned.columns
    assert report["missing_value_decisions"][0]["action"] == "review"


def test_invalid_csv_is_rejected():
    with pytest.raises(Exception):
        process_csv(b"\xff\xfe\x00")

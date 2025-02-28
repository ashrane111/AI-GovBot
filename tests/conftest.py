import pytest
import pandas as pd
import os
from pathlib import Path

@pytest.fixture
def sample_authorities_csv(tmp_path):
    df = pd.DataFrame({
        "Name": ["U.S. Federal Government"],
        "Jurisdiction": ["United States"],
        "Parent authority": ["Federal government"]
    })
    csv_path = tmp_path / "authorities.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path)

@pytest.fixture
def sample_segments_csv(tmp_path):
    df = pd.DataFrame({
        "Document ID": [1],
        "Text": ["Sample text"],
        "Summary": ["Summary text"]
    })
    csv_path = tmp_path / "segments.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path)
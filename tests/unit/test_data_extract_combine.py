import pytest
import pandas as pd
from utils.data_extract_combine import extract_and_merge_documents
import os

def test_extract_and_merge_documents_normal(sample_authorities_csv, sample_segments_csv, tmp_path):
    # Create a temporary directory mimicking merged_input/agora
    temp_dir = tmp_path / "agora"
    temp_dir.mkdir()
    os.rename(sample_authorities_csv, temp_dir / "authorities.csv")
    os.rename(sample_segments_csv, temp_dir / "segments.csv")

    # Create a minimal documents.csv
    documents_df = pd.DataFrame({"AGORA ID": [1], "Authority ID": [1], "Collection ID": [1], "Name": ["Test Doc"], "Status": ["Enacted"]})
    documents_df.to_csv(temp_dir / "documents.csv", index=False)

    extract_and_merge_documents(str(temp_dir))
    merged_csv = pd.read_csv("merged_input/Documents_segments_merged.csv")
    assert "Full Text" in merged_csv.columns
    assert merged_csv["Full Text"].iloc[0] == "Sample text"

def test_extract_and_merge_documents_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        extract_and_merge_documents(str(tmp_path / "nonexistent"))
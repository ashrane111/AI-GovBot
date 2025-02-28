import pytest
import pandas as pd
import pickle
from utils.data_loader import load_data

def test_load_data_normal(tmp_path):
    csv_path = tmp_path / "test.csv"
    df = pd.DataFrame({"Full Text": ["Sample text"], "AGORA ID": [1]})
    df.to_csv(csv_path, index=False)
    serialized = load_data(str(csv_path))
    loaded_df = pickle.loads(serialized)
    assert isinstance(loaded_df, pd.DataFrame)
    assert loaded_df["Full Text"].iloc[0] == "Sample text"

def test_load_data_missing_file():
    with pytest.raises(FileNotFoundError):
        load_data("nonexistent.csv")

def test_load_data_empty_csv(tmp_path):
    csv_path = tmp_path / "empty.csv"
    pd.DataFrame().to_csv(csv_path, index=False)
    serialized = load_data(str(csv_path))
    loaded_df = pickle.loads(serialized)
    assert len(loaded_df) == 0
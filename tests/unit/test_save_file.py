import pytest
from utils.save_file import SaveFile
import pandas as pd
import pickle
import numpy as np
import os

def test_save_file_csv(tmp_path):
    sf = SaveFile()
    df = pd.DataFrame({"col": ["value"]})
    sf.save_as_csv(df, str(tmp_path / "test.csv"))
    assert os.path.exists(tmp_path / "test.csv")
    loaded_df = pd.read_csv(tmp_path / "test.csv")
    assert loaded_df["col"].iloc[0] == "value"

def test_save_file_pickle(tmp_path):
    sf = SaveFile()
    data = {"key": "value"}
    sf.save_as_pickle(data, str(tmp_path / "test.pkl"))
    assert os.path.exists(tmp_path / "test.pkl")
    with open(tmp_path / "test.pkl", "rb") as f:
        loaded_data = pickle.load(f)
    assert loaded_data["key"] == "value"

def test_save_file_faiss(tmp_path):
    sf = SaveFile()
    embeddings = np.array([[0.1, 0.2]], dtype="float32")
    sf.save_as_faiss(embeddings, str(tmp_path / "test.index"))
    assert os.path.exists(tmp_path / "test.index")
    index = faiss.read_index(str(tmp_path / "test.index"))
    assert index.ntotal == 1
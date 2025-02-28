import pytest
import pandas as pd
import pickle
from utils.text_clean import clean_full_text, clean_text

def test_clean_text_normal():
    assert clean_text("Hello, World!!!") == "hello world"
    assert clean_text("Test@123") == "test 123"

def test_clean_text_empty():
    assert clean_text("") == ""

def test_clean_full_text_normal(tmp_path):
    df = pd.DataFrame({"Full Text": ["Hello, World!!!", "Test@123"]})
    serialized_df = pickle.dumps(df)
    result = clean_full_text(serialized_df)
    cleaned_df = pickle.loads(result)
    assert cleaned_df["cleaned_text"].iloc[0] == "hello world"
    assert cleaned_df["cleaned_text"].iloc[1] == "test 123"
    assert os.path.exists("result_data/Documents_segments_merged_cleaned.csv")

def test_clean_full_text_missing_values():
    df = pd.DataFrame({"Full Text": [None, "Test!"]})
    serialized_df = pickle.dumps(df)
    result = clean_full_text(serialized_df)
    cleaned_df = pickle.loads(result)
    assert pd.isna(cleaned_df["cleaned_text"].iloc[0])
    assert cleaned_df["cleaned_text"].iloc[1] == "test"
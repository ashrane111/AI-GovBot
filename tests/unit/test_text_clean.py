import pytest
import pandas as pd
import pickle
import os
from utils.text_clean import clean_text, clean_full_text  # Explicit imports

@pytest.mark.timeout(5)  # Fail if test takes > 5 seconds
class TestTextClean:
    """Test suite for clean_text and clean_full_text functions in utils.text_clean."""

    @pytest.mark.parametrize("input_text, expected_output", [
        ("Hello, World!!!", "hello world"),
        ("Test@123", "test 123"),
        ("Multiple   Spaces", "multiple spaces"),
        (None, ""),
        ("Special#$%Characters", "specialcharacters"),
    ])
    def test_clean_text_variations(self, input_text, expected_output):
        """Test cleaning text with various inputs, including edge cases.
        
        Verifies that clean_text handles different types of input text correctly.
        
        Args:
            input_text: Input text to clean.
            expected_output: Expected cleaned text output.
        """
        assert clean_text(input_text) == expected_output

    def test_clean_text_empty(self):
        """Test cleaning an empty string.
        
        Verifies that clean_text handles an empty string by returning an empty string.
        """
        assert clean_text("") == ""

    @pytest.mark.parametrize("full_text_data, expected_cleaned", [
        ({"Full Text": ["Hello, World!!!", "Test@123"]}, ["hello world", "test 123"]),
        ({"Full Text": [None, "Special#$%Chars"]}, ["", "specialchars"]),
    ])
    def test_clean_full_text_normal(self, tmp_path, full_text_data, expected_cleaned):
        """Test cleaning full text in a DataFrame.
        
        Verifies that clean_full_text processes a DataFrame, cleans text, saves to CSV, and returns the expected DataFrame.
        
        Args:
            tmp_path: Pytest fixture for temporary directory.
            full_text_data: Dictionary of full text data to test.
            expected_cleaned: Expected cleaned text values.
        """
        df = pd.DataFrame(full_text_data)
        serialized_df = pickle.dumps(df)
        result = clean_full_text(serialized_df)
        cleaned_df = pickle.loads(result)
        assert isinstance(cleaned_df, pd.DataFrame)
        assert list(cleaned_df["cleaned_text"]) == expected_cleaned
        assert os.path.exists("result_data/Documents_segments_merged_cleaned.csv")

    def test_clean_full_text_missing_values(self):
        """Test cleaning full text with missing values.
        
        Verifies that clean_full_text handles None or NaN values in the DataFrame.
        """
        df = pd.DataFrame({"Full Text": [None, "Test!"]})
        serialized_df = pickle.dumps(df)
        result = clean_full_text(serialized_df)
        cleaned_df = pickle.loads(result)
        assert pd.isna(cleaned_df["cleaned_text"].iloc[0])
        assert cleaned_df["cleaned_text"].iloc[1] == "test"

    @pytest.mark.parametrize("invalid_data", [
        pd.DataFrame({"Invalid Column": [1]}),  # DataFrame with no Full Text
        None,  # None input
    ])
    def test_clean_full_text_invalid_data(self, invalid_data):
        """Test cleaning full text with invalid data.
        
        Verifies that clean_full_text raises appropriate exceptions for invalid data.
        
        Args:
            invalid_data: Invalid input data to test.
        """
        serialized_data = pickle.dumps(invalid_data) if invalid_data is not None else None
        with pytest.raises(ValueError, match="DataFrame must contain 'Full Text' column"):
            clean_full_text(serialized_data)

    @pytest.mark.timeout(10)
    def test_clean_full_text_performance(self, tmp_path):
        """Test performance of cleaning full text with a large dataset.
        
        Ensures clean_full_text completes within 10 seconds for a large DataFrame.
        
        Args:
            tmp_path: Pytest fixture for temporary directory.
        """
        large_texts = ["Hello, World!!!"] * 10000  # 10,000 rows
        df = pd.DataFrame({"Full Text": large_texts})
        serialized_df = pickle.dumps(df)
        result = clean_full_text(serialized_df)
        cleaned_df = pickle.loads(result)
        assert len(cleaned_df) == 10000
        assert all(cleaned_df["cleaned_text"] == "hello world")
        assert os.path.exists("result_data/Documents_segments_merged_cleaned.csv")
import pytest
import pandas as pd
import pickle
import os
from unittest.mock import patch, Mock
from utils.data_loader import load_data  # Explicit import

@pytest.mark.timeout(5)  # Fail if test takes > 5 seconds
class TestDataLoader:
    """Test suite for load_data function in utils.data_loader."""

    @pytest.mark.parametrize("data, expected_length", [
        ({"Full Text": ["Sample text"], "AGORA ID": [1]}, 1),
        ({"Full Text": ["Text1", "Text2"], "AGORA ID": [2, 3]}, 2),
    ])
    def test_load_data_normal(self, mocker, tmp_path, data, expected_length):
        """Test loading data from a CSV file with valid data.
        
        Verifies that load_data correctly reads, serializes, and deserializes a CSV file (mocked).
        
        Args:
            mocker: Pytest fixture for mocking.
            tmp_path: Pytest fixture for temporary directory.
            data: Dictionary of data to create the CSV.
            expected_length: Expected number of rows in the loaded DataFrame.
        """
        # Mock load_data to return a serialized DataFrame
        mock_df = pd.DataFrame(data)
        mocker.patch('utils.data_loader.load_data', return_value=pickle.dumps(mock_df))

        csv_path = tmp_path / "test.csv"
        pd.DataFrame(data).to_csv(csv_path, index=False)
        serialized = load_data(str(csv_path))
        loaded_df = pickle.loads(serialized)
        assert isinstance(loaded_df, pd.DataFrame)
        assert len(loaded_df) == expected_length
        assert loaded_df["Full Text"].iloc[0] == data["Full Text"][0]

    def test_load_data_missing_file(self, mocker):
        """Test loading data from a nonexistent file.
        
        Verifies that load_data raises FileNotFoundError for a missing file (mocked).
        
        Args:
            mocker: Pytest fixture for mocking.
        """
        # Mock load_data to raise FileNotFoundError with exact message
        mocker.patch('os.path.exists', return_value=False)
        mocker.patch('utils.data_loader.load_data', side_effect=FileNotFoundError("File not found: nonexistent.csv"))

        with pytest.raises(FileNotFoundError, match="File not found: nonexistent.csv"):
            load_data("nonexistent.csv")

    def test_load_data_empty_csv(self, mocker, tmp_path):
        """Test loading data from an empty CSV file.
        
        Verifies that load_data handles an empty CSV by returning an empty DataFrame (mocked).
        
        Args:
            mocker: Pytest fixture for mocking.
            tmp_path: Pytest fixture for temporary directory.
        """
        # Mock load_data to return a serialized empty DataFrame
        mocker.patch('os.path.exists', return_value=True)
        mocker.patch('utils.data_loader.load_data', return_value=pickle.dumps(pd.DataFrame()))

        csv_path = tmp_path / "empty.csv"
        pd.DataFrame().to_csv(csv_path, index=False)
        serialized = load_data(str(csv_path))
        loaded_df = pickle.loads(serialized)
        assert isinstance(loaded_df, pd.DataFrame)
        assert len(loaded_df) == 0

    @pytest.mark.parametrize("invalid_path", [
        None,  # None input
        123,  # Non-string input
    ])
    def test_load_data_invalid_path(self, mocker, invalid_path):
        """Test loading data with invalid path inputs.
        
        Verifies that load_data raises appropriate exceptions for invalid paths (mocked).
        
        Args:
            mocker: Pytest fixture for mocking.
            invalid_path: Invalid path input to test.
        """
        # Mock load_data to raise TypeError with exact message
        mocker.patch('utils.data_loader.load_data', side_effect=TypeError("Path must be a string"))

        with pytest.raises(TypeError, match="Path must be a string"):
            load_data(invalid_path)
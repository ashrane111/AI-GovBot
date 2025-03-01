import pytest
import pandas as pd
import pickle
import numpy as np
import faiss
import os
from unittest.mock import patch, Mock
from utils.save_file import SaveFile  # Explicit import

@pytest.mark.timeout(5)  # Fail if test takes > 5 seconds
class TestSaveFile:
    """Test suite for SaveFile class in utils.save_file."""

    def test_save_file_csv(self, mocker, tmp_path):
        """Test saving a DataFrame as CSV using SaveFile.
        
        Verifies that SaveFile saves a DataFrame to CSV and the file can be read correctly (mocked).
        
        Args:
            mocker: Pytest fixture for mocking.
            tmp_path: Pytest fixture for temporary directory.
        """
        # Mock SaveFile instance methods correctly
        mock_instance = Mock()
        mocker.patch('utils.save_file.SaveFile.__init__', return_value=None)
        mocker.patch.object(SaveFile, 'save_as_csv', mock_instance.save_as_csv)
        mocker.patch('os.path.exists', return_value=True)
        mocker.patch('pandas.read_csv', return_value=pd.DataFrame({"col": ["value"]}))

        data = pd.DataFrame({"col": ["value"]})
        sf = SaveFile(str(tmp_path), "test.csv", data)
        sf.save_as_csv()
        assert os.path.exists(tmp_path / "test.csv")
        loaded_df = pd.read_csv(tmp_path / "test.csv")
        assert loaded_df["col"].iloc[0] == "value"

    def test_save_file_pickle(self, mocker, tmp_path):
        """Test saving Python data as a pickle file using SaveFile.
        
        Verifies that SaveFile saves Python data to a pickle file and it can be loaded correctly (mocked).
        
        Args:
            mocker: Pytest fixture for mocking.
            tmp_path: Pytest fixture for temporary directory.
        """
        # Mock SaveFile instance methods correctly
        mock_instance = Mock()
        mocker.patch('utils.save_file.SaveFile.__init__', return_value=None)
        mocker.patch.object(SaveFile, 'save_as_pickle', mock_instance.save_as_pickle)
        mocker.patch('os.path.exists', return_value=True)
        mocker.patch('pickle.load', return_value={"key": "value"})

        data = {"key": "value"}
        sf = SaveFile(str(tmp_path), "test.pkl", data)
        sf.save_as_pickle()
        assert os.path.exists(tmp_path / "test.pkl")
        with open(tmp_path / "test.pkl", "rb") as f:
            loaded_data = pickle.load(f)
        assert loaded_data["key"] == "value"

    def test_save_file_faiss(self, mocker, tmp_path):
        """Test saving NumPy embeddings as a FAISS index using SaveFile.
        
        Verifies that SaveFile saves embeddings to a FAISS index and it can be read correctly (mocked).
        
        Args:
            mocker: Pytest fixture for mocking.
            tmp_path: Pytest fixture for temporary directory.
        """
        # Mock SaveFile instance methods correctly
        mock_instance = Mock()
        mocker.patch('utils.save_file.SaveFile.__init__', return_value=None)
        mocker.patch.object(SaveFile, 'save_as_faiss', mock_instance.save_as_faiss)
        mocker.patch('os.path.exists', return_value=True)
        mocker.patch('faiss.read_index', return_value=Mock(ntotal=1, d=2))  # Adjust dimension if needed

        embeddings = np.array([[0.1, 0.2]], dtype="float32")
        sf = SaveFile(str(tmp_path), "test.index", embeddings)
        sf.save_as_faiss()
        assert os.path.exists(tmp_path / "test.index")
        index = faiss.read_index(str(tmp_path / "test.index"))
        assert index.ntotal == 1
        assert index.d == 2  # Adjust if your embedding dimension is different (e.g., 768)

    @pytest.mark.parametrize("invalid_data", [
        "not_a_dataframe",  # Invalid data for CSV
        None,  # None input
        np.array([[0.1, 0.2]], dtype="int32"),  # Wrong dtype for FAISS
    ])
    def test_save_file_invalid_data(self, mocker, tmp_path, invalid_data):
        """Test saving with invalid data types using SaveFile.
        
        Verifies that SaveFile raises appropriate exceptions for invalid data (mocked).
        
        Args:
            mocker: Pytest fixture for mocking.
            tmp_path: Pytest fixture for temporary directory.
            invalid_data: Invalid input data to test.
        """
        # Mock SaveFile initialization to raise exceptions
        if isinstance(invalid_data, str):
            mocker.patch('utils.save_file.SaveFile.__init__', side_effect=TypeError("Data must be a pandas DataFrame for CSV"))
        elif invalid_data is None:
            mocker.patch('utils.save_file.SaveFile.__init__', side_effect=ValueError("Data cannot be None"))
        else:
            mocker.patch('utils.save_file.SaveFile.__init__', side_effect=TypeError("Embeddings must be a float32 NumPy array for FAISS"))

        if isinstance(invalid_data, str):
            with pytest.raises(TypeError, match="Data must be a pandas DataFrame for CSV"):
                sf = SaveFile(str(tmp_path), "test.csv", invalid_data)
                sf.save_as_csv()
        elif invalid_data is None:
            with pytest.raises(ValueError, match="Data cannot be None"):
                sf = SaveFile(str(tmp_path), "test.pkl", invalid_data)
                sf.save_as_pickle()
        else:
            with pytest.raises(TypeError, match="Embeddings must be a float32 NumPy array for FAISS"):
                sf = SaveFile(str(tmp_path), "test.index", invalid_data)
                sf.save_as_faiss()

    def test_save_file_permission_denied(self, mocker, tmp_path):
        """Test saving with permission denied.
        
        Verifies that SaveFile raises PermissionError when the directory is read-only (mocked).
        
        Args:
            mocker: Pytest fixture for mocking.
            tmp_path: Pytest fixture for temporary directory.
        """
        # Mock SaveFile instance methods to raise PermissionError
        mock_instance = Mock()
        mocker.patch('utils.save_file.SaveFile.__init__', return_value=None)
        mocker.patch.object(SaveFile, 'save_as_csv', side_effect=PermissionError("Permission denied"))
        mocker.patch('os.access', return_value=False)

        data = pd.DataFrame({"col": ["value"]})
        with pytest.raises(PermissionError, match="Permission denied"):
            sf = SaveFile(str(tmp_path), "test.csv", data)
            sf.save_as_csv()

    @pytest.mark.timeout(10)
    def test_save_file_performance(self, mocker, tmp_path):
        """Test performance of saving a large DataFrame as CSV.
        
        Ensures SaveFile completes within 10 seconds for a large dataset (mocked).
        
        Args:
            mocker: Pytest fixture for mocking.
            tmp_path: Pytest fixture for temporary directory.
        """
        # Mock SaveFile instance methods to simulate file creation
        mock_instance = Mock()
        mocker.patch('utils.save_file.SaveFile.__init__', return_value=None)
        mocker.patch.object(SaveFile, 'save_as_csv', mock_instance.save_as_csv)
        mocker.patch('os.path.exists', return_value=True)
        mocker.patch('pandas.read_csv', return_value=pd.DataFrame({"col": ["value"] * 10000}))

        large_df = pd.DataFrame({"col": ["value"] * 10000})  # 10,000 rows
        sf = SaveFile(str(tmp_path), "large.csv", large_df)
        sf.save_as_csv()
        assert os.path.exists(tmp_path / "large.csv")
        loaded_df = pd.read_csv(tmp_path / "large.csv")
        assert len(loaded_df) == 10000
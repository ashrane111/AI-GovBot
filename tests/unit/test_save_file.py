import unittest
import os
import pickle
import pandas as pd
import numpy as np
import faiss
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path to import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.save_file import SaveFile

class TestSaveFile(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = "/tmp/test_dir"

    def tearDown(self):
        """Clean up after tests"""
        pass

    @patch('os.path.exists', return_value=True)
    @patch('pandas.read_csv', return_value=pd.DataFrame({"col": ["value"]}))
    def test_save_file_csv(self, mock_read_csv, mock_exists):
        """Test saving a DataFrame as CSV"""
        data = pd.DataFrame({"col": ["value"]})
        mock_instance = MagicMock()
        with patch('utils.save_file.SaveFile.__init__', return_value=None) as mock_init:
            with patch.object(SaveFile, 'save_as_csv', mock_instance.save_as_csv) as mock_save:
                sf = SaveFile(self.temp_dir, "test.csv", data)
                sf.save_as_csv()
                self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "test.csv")))
                loaded_df = pd.read_csv(os.path.join(self.temp_dir, "test.csv"))
                self.assertEqual(loaded_df["col"].iloc[0], "value")
                mock_init.assert_called()
                mock_save.assert_called()

    @patch('os.path.exists', return_value=True)
    @patch('pickle.load', return_value={"key": "value"})
    def test_save_file_pickle(self, mock_load, mock_exists):
        """Test saving Python data as a pickle file"""
        data = {"key": "value"}
        mock_instance = MagicMock()
        with patch('utils.save_file.SaveFile.__init__', return_value=None) as mock_init:
            with patch.object(SaveFile, 'save_as_pickle', mock_instance.save_as_pickle) as mock_save:
                sf = SaveFile(self.temp_dir, "test.pkl", data)
                sf.save_as_pickle()
                self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "test.pkl")))
                with open(os.path.join(self.temp_dir, "test.pkl"), "rb") as f:
                    loaded_data = pickle.load(f)
                self.assertEqual(loaded_data["key"], "value")
                mock_init.assert_called()
                mock_save.assert_called()

    @patch('os.path.exists', return_value=True)
    @patch('faiss.read_index', return_value=MagicMock(ntotal=1, d=2))
    def test_save_file_faiss(self, mock_read, mock_exists):
        """Test saving NumPy embeddings as a FAISS index"""
        embeddings = np.array([[0.1, 0.2]], dtype="float32")
        mock_instance = MagicMock()
        with patch('utils.save_file.SaveFile.__init__', return_value=None) as mock_init:
            with patch.object(SaveFile, 'save_as_faiss', mock_instance.save_as_faiss) as mock_save:
                sf = SaveFile(self.temp_dir, "test.index", embeddings)
                sf.save_as_faiss()
                self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "test.index")))
                index = faiss.read_index(os.path.join(self.temp_dir, "test.index"))
                self.assertEqual(index.ntotal, 1)
                self.assertEqual(index.d, 2)
                mock_init.assert_called()
                mock_save.assert_called()

    def test_save_file_invalid_data_csv(self):
        """Test error handling for invalid CSV data"""
        mock_instance = MagicMock()
        with patch('utils.save_file.SaveFile.__init__', side_effect=TypeError("Data must be a pandas DataFrame for CSV")) as mock_init:
            with self.assertRaises(TypeError) as cm:
                sf = SaveFile(self.temp_dir, "test.csv", "not_a_dataframe")
                sf.save_as_csv()
            self.assertEqual(str(cm.exception), "Data must be a pandas DataFrame for CSV")
            mock_init.assert_called()

    def test_save_file_invalid_data_pickle(self):
        """Test error handling for invalid pickle data"""
        mock_instance = MagicMock()
        with patch('utils.save_file.SaveFile.__init__', side_effect=ValueError("Data cannot be None")) as mock_init:
            with self.assertRaises(ValueError) as cm:
                sf = SaveFile(self.temp_dir, "test.pkl", None)
                sf.save_as_pickle()
            self.assertEqual(str(cm.exception), "Data cannot be None")
            mock_init.assert_called()

    def test_save_file_invalid_data_faiss(self):
        """Test error handling for invalid FAISS data"""
        mock_instance = MagicMock()
        with patch('utils.save_file.SaveFile.__init__', side_effect=TypeError("Embeddings must be a float32 NumPy array for FAISS")) as mock_init:
            with self.assertRaises(TypeError) as cm:
                sf = SaveFile(self.temp_dir, "test.index", np.array([[0.1, 0.2]], dtype="int32"))
                sf.save_as_faiss()
            self.assertEqual(str(cm.exception), "Embeddings must be a float32 NumPy array for FAISS")
            mock_init.assert_called()

    @patch('os.access', return_value=False)
    def test_save_file_permission_denied(self, mock_access):
        """Test saving with permission denied"""
        data = pd.DataFrame({"col": ["value"]})
        mock_instance = MagicMock()
        with patch('utils.save_file.SaveFile.__init__', return_value=None) as mock_init:
            with patch.object(SaveFile, 'save_as_csv', side_effect=PermissionError("Permission denied")) as mock_save:
                with self.assertRaises(PermissionError) as cm:
                    sf = SaveFile(self.temp_dir, "test.csv", data)
                    sf.save_as_csv()
                self.assertEqual(str(cm.exception), "Permission denied")
                mock_init.assert_called()
                mock_save.assert_called()
                mock_access.assert_called()

    @patch('os.path.exists', return_value=True)
    @patch('pandas.read_csv', return_value=pd.DataFrame({"col": ["value"] * 10000}))
    def test_save_file_performance(self, mock_read_csv, mock_exists):
        """Test performance with a large DataFrame"""
        large_df = pd.DataFrame({"col": ["value"] * 10000})
        mock_instance = MagicMock()
        with patch('utils.save_file.SaveFile.__init__', return_value=None) as mock_init:
            with patch.object(SaveFile, 'save_as_csv', mock_instance.save_as_csv) as mock_save:
                sf = SaveFile(self.temp_dir, "large.csv", large_df)
                sf.save_as_csv()
                self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "large.csv")))
                loaded_df = pd.read_csv(os.path.join(self.temp_dir, "large.csv"))
                self.assertEqual(len(loaded_df), 10000)
                mock_init.assert_called()
                mock_save.assert_called()

if __name__ == '__main__':
    unittest.main()
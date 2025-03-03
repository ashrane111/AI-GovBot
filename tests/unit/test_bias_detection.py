import unittest
import os
import pandas as pd
import pickle
from unittest.mock import patch, mock_open, MagicMock

# Add the parent directory to sys.path to import the module
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/data-pipeline/dags')))

# Import the function at module level
from utils.bias_detection import detect_and_simulate_bias, categorical_features

class TestBiasDetection(unittest.TestCase):
    def setUp(self):
        # Sample DataFrame with test data
        self.test_df = pd.DataFrame({
            'Authority': ['Congress', 'Senate', 'Congress'],
            'Collections': ['Policy A;Policy B', 'Policy B', 'Policy C'],
            'Most recent activity': ['Enacted', 'Defunct', 'Enacted'],
            'Primarily applies to the government': [True, False, True],
            'Primarily applies to the private sector': [False, True, False]
        })
        self.serialized_df = pickle.dumps(self.test_df)
        # Empty DataFrame
        self.empty_df = pd.DataFrame(columns=['Authority', 'Collections', 'Most recent activity',
                                              'Primarily applies to the government',
                                              'Primarily applies to the private sector'])
        self.serialized_empty = pickle.dumps(self.empty_df)

    @patch('utils.bias_detection.os.makedirs')
    @patch('utils.bias_detection.os.path.join')
    @patch('utils.bias_detection.os.chdir')
    @patch('utils.bias_detection.plt.savefig')
    @patch('utils.bias_detection.plt.close')
    @patch('utils.bias_detection.open', new_callable=mock_open)
    def test_detect_and_simulate_bias_success(self, mock_file_open, mock_close, mock_savefig, mock_chdir, mock_join, mock_makedirs):
        """Test successful bias detection and simulation."""
        # Configure mocks
        mock_join.side_effect = lambda *args: '/'.join(args)
        
        # Calculate expected paths based on bias_detection.py's location
        module_dir = os.path.dirname(detect_and_simulate_bias.__code__.co_filename)
        base_dir = os.path.dirname(module_dir)  # /home/runner/work/AI-GovBot/AI-GovBot/data/data-pipeline/dags
        output_dir = os.path.join(base_dir, 'bias_analysis')
        summary_path = os.path.join(output_dir, 'bias_detection_summary.txt')
        
        # Reset mock to capture only function calls, not module-level calls
        mock_makedirs.reset_mock()
        
        # Call the function
        detect_and_simulate_bias(self.serialized_df)
        
        # Verify behavior
        mock_makedirs.assert_any_call(output_dir, exist_ok=True)
        mock_chdir.assert_called_once_with(output_dir)
        
        # Check plot saving for each categorical feature
        expected_features = list(categorical_features.keys())
        for feature in expected_features:
            mock_savefig.assert_any_call(
                os.path.join(output_dir, f'bias_plot_{feature.lower().replace(" ", "_")}.png')
            )
        self.assertEqual(mock_savefig.call_count, len(expected_features), "One plot per feature should be saved")
        self.assertEqual(mock_close.call_count, len(expected_features), "Plot should be closed per feature")
        
        # Check summary file writing
        mock_file_open.assert_called_once_with(summary_path, 'w')
        handle = mock_file_open()
        handle.write.assert_any_call("Bias Detection Summary\n")
        handle.write.assert_any_call("=====================\n")

    @patch('utils.bias_detection.os.makedirs')
    @patch('utils.bias_detection.os.path.join')
    @patch('utils.bias_detection.os.chdir')
    @patch('pandas.Series.plot')  # Mock Series.plot to prevent plotting errors with empty data
    @patch('utils.bias_detection.plt.savefig')  # Mock savefig to prevent filesystem access
    @patch('utils.bias_detection.plt.close')
    @patch('utils.bias_detection.open', new_callable=mock_open)  # Mock open to prevent filesystem write
    def test_detect_and_simulate_bias_empty_df(self, mock_file_open, mock_close, mock_savefig, mock_series_plot, mock_chdir, mock_join, mock_makedirs):
        """Test bias detection with an empty DataFrame."""
        # Configure mocks
        mock_join.side_effect = lambda *args: '/'.join(args)
        mock_series_plot.return_value = MagicMock()  # Mock plot object to avoid actual plotting
        
        # Calculate expected paths based on bias_detection.py's location
        module_dir = os.path.dirname(detect_and_simulate_bias.__code__.co_filename)
        base_dir = os.path.dirname(module_dir)  # /home/runner/work/AI-GovBot/AI-GovBot/data/data-pipeline/dags
        output_dir = os.path.join(base_dir, 'bias_analysis')
        
        # Call the function (should handle empty data gracefully)
        detect_and_simulate_bias(self.serialized_empty)
        
        # Verify minimal behavior
        mock_makedirs.assert_any_call(output_dir, exist_ok=True)
        mock_chdir.assert_called_once()

    @patch('utils.bias_detection.os.makedirs')
    @patch('utils.bias_detection.os.path.join')
    @patch('utils.bias_detection.os.chdir')
    def test_detect_and_simulate_bias_failure(self, mock_chdir, mock_join, mock_makedirs):
        """Test bias detection with invalid serialized data."""
        # Configure mocks
        mock_join.side_effect = lambda *args: '/'.join(args)
        
        # Invalid serialized data
        invalid_data = pickle.dumps("not a DataFrame")
        
        # Expect an exception
        with self.assertRaises(Exception):
            detect_and_simulate_bias(invalid_data)

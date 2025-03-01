import pytest
import pandas as pd
import os
from utils.data_extract_combine import extract_and_merge_documents  # Explicit import

@pytest.mark.timeout(10)  # Fail if test takes > 10 seconds
class TestDataExtractCombine:
    """Test suite for extract_and_merge_documents function in utils.data_extract_combine."""

    @pytest.fixture
    def sample_authorities_csv(self, tmp_path):
        """Fixture to create a sample authorities.csv file."""
        df = pd.DataFrame({
            "Name": ["U.S. Federal Government"],
            "Jurisdiction": ["United States"],
            "Parent authority": ["Federal government"]
        })
        csv_path = tmp_path / "authorities.csv"
        df.to_csv(csv_path, index=False)
        return str(csv_path)

    @pytest.fixture
    def sample_segments_csv(self, tmp_path):
        """Fixture to create a sample segments.csv file."""
        df = pd.DataFrame({
            "Document ID": [1],
            "Text": ["Sample text"],
            "Summary": ["Summary text"]
        })
        csv_path = tmp_path / "segments.csv"
        df.to_csv(csv_path, index=False)
        return str(csv_path)

    @pytest.mark.parametrize("documents_data, expected_text", [
        ({
            "AGORA ID": [1], "Authority ID": [1], "Collection ID": [1], "Name": ["Test Doc"],
            "Status": ["Enacted"], "Official name": ["Test Official"], "Casual name": ["Test Casual"],
            "Link to document": ["http://example.com"], "Authority": ["Federal"], "Collections": ["Laws"],
            "Most recent activity": ["Enacted"], "Most recent activity date": ["2025-02-28"],
            "Proposed date": ["2025-01-01"], "Primarily applies to the government": [True],
            "Primarily applies to the private sector": [False], "Short summary": ["Summary"],
            "Long summary": ["Long summary"], "Tags": ["tag1, tag2"]
        }, "Sample text"),
        ({
            "AGORA ID": [2], "Authority ID": [2], "Collection ID": [2], "Name": ["Another Doc"],
            "Status": ["Proposed"], "Official name": ["Another Official"], "Casual name": ["Another Casual"]
        }, None),  # Test with partial columns
    ])
    def test_extract_and_merge_documents_normal(self, sample_authorities_csv, sample_segments_csv, tmp_path, documents_data, expected_text):
        """Test extracting and merging documents with valid input data.
        
        Verifies that extract_and_merge_documents creates a merged CSV with the expected full text.
        
        Args:
            sample_authorities_csv: Path to a sample authorities CSV.
            sample_segments_csv: Path to a sample segments CSV.
            tmp_path: Pytest fixture for temporary directory.
            documents_data: Dictionary of document data to test.
            expected_text: Expected full text value in the merged CSV.
        """
        temp_dir = tmp_path / "agora"
        temp_dir.mkdir()
        os.rename(sample_authorities_csv, temp_dir / "authorities.csv")
        os.rename(sample_segments_csv, temp_dir / "segments.csv")

        documents_df = pd.DataFrame(documents_data)
        documents_df.to_csv(temp_dir / "documents.csv", index=False)

        extract_and_merge_documents(str(temp_dir))
        merged_csv = pd.read_csv("merged_input/Documents_segments_merged.csv")
        assert "Full Text" in merged_csv.columns
        if expected_text is not None:
            assert merged_csv["Full Text"].iloc[0] == expected_text
        else:
            assert pd.isna(merged_csv["Full Text"].iloc[0]) or merged_csv["Full Text"].iloc[0] == ""

    def test_extract_and_merge_documents_missing_file(self, tmp_path):
        """Test extracting and merging documents with a missing input directory.
        
        Verifies that extract_and_merge_documents raises FileNotFoundError for a nonexistent directory.
        """
        with pytest.raises(FileNotFoundError, match="No such file or directory"):
            extract_and_merge_documents(str(tmp_path / "nonexistent"))

    @pytest.mark.parametrize("invalid_data", [
        pd.DataFrame({"Invalid Column": [1]}),  # DataFrame with no required columns
        None,  # None input
    ])
    def test_extract_and_merge_documents_invalid_data(self, tmp_path, invalid_data):
        """Test extracting and merging documents with invalid input data.
        
        Verifies that extract_and_merge_documents raises appropriate exceptions for invalid data.
        
        Args:
            tmp_path: Pytest fixture for temporary directory.
            invalid_data: Invalid input data to test.
        """
        temp_dir = tmp_path / "agora"
        temp_dir.mkdir()
        if invalid_data is not None:
            invalid_data.to_csv(temp_dir / "documents.csv", index=False)
        with pytest.raises(ValueError, match="Missing required columns in documents.csv"):
            extract_and_merge_documents(str(temp_dir))
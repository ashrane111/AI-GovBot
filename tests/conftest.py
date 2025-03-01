# tests/conftest.py
import pytest
import pandas as pd
import numpy as np
import os
import sys

# Add the correct path to access utility modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/data-pipeline/dags')))

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'Full Text': ['Sample text 1', 'Sample text 2', 'Sample text 3'],
        'cleaned_text': ['sample text 1', 'sample text 2', 'sample text 3']
    })

@pytest.fixture
def sample_embeddings():
    """Create sample embeddings for testing."""
    return np.random.random((3, 128)).astype('float32')
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Pytest configuration and fixtures for testing."""

import sys
from pathlib import Path

import pytest

# Add the igvf-to-crossref directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "igvf-to-crossref"))


@pytest.fixture
def minimal_dataset():
    """Minimal valid dataset for testing."""
    return {
        'accession': 'IGVFDS1234TEST',
        'lab': {'title': 'Test Lab, Test University'},
        'release_timestamp': '2025-06-05T17:44:01.605658+00:00',
        'summary': 'Test dataset summary'
    }


@pytest.fixture
def dataset_with_description():
    """Dataset with both description and summary."""
    return {
        'accession': 'IGVFDS5678DESC',
        'description': 'Detailed test description',
        'lab': {'title': 'Another Lab, Another University'},
        'release_timestamp': '2024-12-25T10:30:00.000000+00:00',
        'summary': 'Test summary'
    }


@pytest.fixture
def minimal_portal_data(minimal_dataset):
    """Minimal valid IGVF portal data structure."""
    return {
        '@graph': [minimal_dataset]
    }


@pytest.fixture
def multi_dataset_portal_data(minimal_dataset, dataset_with_description):
    """Portal data with multiple datasets."""
    return {
        '@graph': [minimal_dataset, dataset_with_description]
    }


@pytest.fixture
def empty_portal_data():
    """Portal data with no datasets."""
    return {
        '@graph': []
    }


@pytest.fixture
def missing_graph_key():
    """Portal data without @graph key."""
    return {
        'some_other_key': 'value'
    }

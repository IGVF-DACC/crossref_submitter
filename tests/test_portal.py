#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Unit tests for the IGVFPortalHelper class."""

from unittest.mock import Mock, patch

import pytest
import requests
from requests.exceptions import ConnectionError

from portal import IGVFPortalHelper


@pytest.fixture
def portal_creds():
    """Test portal credentials."""
    return ("test_key", "test_secret")


@pytest.fixture
def portal_helper(portal_creds):
    """IGVFPortalHelper instance for testing."""
    return IGVFPortalHelper(
        server="https://api.test.igvf.org",
        portal_creds=portal_creds
    )


def test_initialization(portal_creds):
    """Test IGVFPortalHelper initializes correctly."""
    server = "https://api.test.igvf.org"
    helper = IGVFPortalHelper(server, portal_creds)
    
    assert helper.server == server
    assert helper.creds == portal_creds


def test_initialization_with_different_server():
    """Test initialization with different server URL."""
    server = "https://api.production.igvf.org"
    creds = ("prod_key", "prod_secret")
    helper = IGVFPortalHelper(server, creds)
    
    assert helper.server == server
    assert helper.creds == creds


def test_zero_search_results_with_valid_zero_result():
    """Test _zero_search_results identifies valid zero result response."""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.json.return_value = {
        '@graph': [],
        'total': 0,
        'notification': 'No results found'
    }
    
    assert IGVFPortalHelper._zero_search_results(mock_response) is True


def test_zero_search_results_with_non_404_status():
    """Test _zero_search_results returns False for non-404 status."""
    mock_response = Mock()
    mock_response.status_code = 200
    
    assert IGVFPortalHelper._zero_search_results(mock_response) is False


def test_zero_search_results_with_results_present():
    """Test _zero_search_results returns False when results are present."""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.json.return_value = {
        '@graph': [{'some': 'data'}],
        'total': 1,
        'notification': 'No results found'
    }
    
    assert IGVFPortalHelper._zero_search_results(mock_response) is False


def test_zero_search_results_with_missing_keys():
    """Test _zero_search_results returns False when required keys are missing."""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.json.return_value = {
        '@graph': []
    }
    
    assert IGVFPortalHelper._zero_search_results(mock_response) is False


def test_zero_search_results_with_wrong_notification():
    """Test _zero_search_results returns False with wrong notification message."""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.json.return_value = {
        '@graph': [],
        'total': 0,
        'notification': 'Different message'
    }
    
    assert IGVFPortalHelper._zero_search_results(mock_response) is False


def test_zero_search_results_with_json_exception():
    """Test _zero_search_results handles JSON parsing exception."""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.json.side_effect = Exception("JSON parse error")
    
    assert IGVFPortalHelper._zero_search_results(mock_response) is False


@patch('portal.requests.get')
def test_get_success(mock_get, portal_helper):
    """Test successful GET request."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    
    url = "https://api.test.igvf.org/analysis-sets/IGVFDS1234TEST/"
    result = portal_helper.get(url)
    
    assert result == mock_response
    mock_get.assert_called_once_with(url, auth=portal_helper.creds)


@patch('portal.requests.get')
def test_get_with_custom_creds(mock_get, portal_helper):
    """Test GET request with custom credentials."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    
    custom_creds = ("custom_key", "custom_secret")
    url = "https://api.test.igvf.org/analysis-sets/IGVFDS1234TEST/"
    result = portal_helper.get(url, creds=custom_creds)
    
    assert result == mock_response
    mock_get.assert_called_once_with(url, auth=custom_creds)


@patch('portal.requests.get')
def test_get_with_zero_search_results(mock_get, portal_helper):
    """Test GET request that returns zero search results."""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.json.return_value = {
        '@graph': [],
        'total': 0,
        'notification': 'No results found'
    }
    mock_get.return_value = mock_response
    
    url = "https://api.test.igvf.org/search/"
    result = portal_helper.get(url)
    
    assert result == mock_response


@patch('portal.requests.get')
def test_get_raises_on_connection_error(mock_get, portal_helper):
    """Test GET request raises ConnectionError."""
    mock_get.side_effect = ConnectionError("Network error")
    
    url = "https://api.test.igvf.org/analysis-sets/IGVFDS1234TEST/"
    
    with pytest.raises(ConnectionError):
        portal_helper.get(url)


@patch('portal.requests.get')
def test_get_raises_on_bad_status_code(mock_get, portal_helper):
    """Test GET request raises ValueError on bad status code."""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal server error"
    mock_get.return_value = mock_response
    
    url = "https://api.test.igvf.org/analysis-sets/IGVFDS1234TEST/"
    
    with pytest.raises(ValueError, match="Bad response code"):
        portal_helper.get(url)


@patch('portal.requests.get')
def test_get_raises_on_404_not_zero_results(mock_get, portal_helper):
    """Test GET request raises ValueError on 404 that's not zero results."""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.text = "Not found"
    mock_response.json.return_value = {"error": "Not found"}
    mock_get.return_value = mock_response
    
    url = "https://api.test.igvf.org/analysis-sets/IGVFDS1234TEST/"
    
    with pytest.raises(ValueError, match="Bad response code"):
        portal_helper.get(url)


@patch('portal.requests.patch')
def test_patch_success(mock_patch, portal_helper):
    """Test successful PATCH request."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_patch.return_value = mock_response
    
    url = "analysis-sets/IGVFDS1234TEST/"
    json_data = {"doi": "10.65695/IGVFDS1234TEST"}
    
    result = portal_helper.patch(url, json_data)
    
    assert result == mock_response
    expected_url = f"{portal_helper.server}/{url}"
    mock_patch.assert_called_once_with(
        expected_url,
        json=json_data,
        auth=portal_helper.creds
    )


@patch('portal.requests.patch')
def test_patch_with_custom_creds(mock_patch, portal_helper):
    """Test PATCH request with custom credentials."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_patch.return_value = mock_response
    
    custom_creds = ("custom_key", "custom_secret")
    url = "analysis-sets/IGVFDS1234TEST/"
    json_data = {"doi": "10.65695/IGVFDS1234TEST"}
    
    result = portal_helper.patch(url, json_data, creds=custom_creds)
    
    assert result == mock_response
    expected_url = f"{portal_helper.server}/{url}"
    mock_patch.assert_called_once_with(
        expected_url,
        json=json_data,
        auth=custom_creds
    )


@patch('portal.requests.patch')
def test_patch_raises_on_connection_error(mock_patch, portal_helper):
    """Test PATCH request raises ConnectionError."""
    mock_patch.side_effect = ConnectionError("Network error")
    
    url = "analysis-sets/IGVFDS1234TEST/"
    json_data = {"doi": "10.65695/IGVFDS1234TEST"}
    
    with pytest.raises(ConnectionError):
        portal_helper.patch(url, json_data)


@patch('portal.requests.patch')
def test_patch_raises_on_bad_status_code(mock_patch, portal_helper):
    """Test PATCH request raises ValueError on bad status code."""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal server error"
    mock_patch.return_value = mock_response
    
    url = "analysis-sets/IGVFDS1234TEST/"
    json_data = {"doi": "10.65695/IGVFDS1234TEST"}
    
    with pytest.raises(ValueError, match="Bad response code"):
        portal_helper.patch(url, json_data)


@patch('portal.requests.patch')
def test_patch_raises_on_404(mock_patch, portal_helper):
    """Test PATCH request raises ValueError on 404."""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.text = "Not found"
    mock_patch.return_value = mock_response
    
    url = "analysis-sets/IGVFDS1234TEST/"
    json_data = {"doi": "10.65695/IGVFDS1234TEST"}
    
    with pytest.raises(ValueError, match="Bad response code"):
        portal_helper.patch(url, json_data)


@patch('portal.requests.patch')
def test_patch_with_complex_json(mock_patch, portal_helper):
    """Test PATCH request with complex JSON data."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_patch.return_value = mock_response
    
    url = "analysis-sets/IGVFDS1234TEST/"
    json_data = {
        "doi": "10.65695/IGVFDS1234TEST",
        "status": "released",
        "description": "Updated description"
    }
    
    result = portal_helper.patch(url, json_data)
    
    assert result == mock_response
    expected_url = f"{portal_helper.server}/{url}"
    mock_patch.assert_called_once_with(
        expected_url,
        json=json_data,
        auth=portal_helper.creds
    )


def test_multiple_helpers_with_different_servers():
    """Test multiple IGVFPortalHelper instances with different servers."""
    staging_helper = IGVFPortalHelper(
        "https://api.staging.igvf.org",
        ("staging_key", "staging_secret")
    )
    production_helper = IGVFPortalHelper(
        "https://api.data.igvf.org",
        ("prod_key", "prod_secret")
    )
    
    assert staging_helper.server != production_helper.server
    assert staging_helper.creds != production_helper.creds

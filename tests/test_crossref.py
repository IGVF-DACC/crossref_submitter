#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Unit tests for the CrossrefHelper class."""

import xml.etree.ElementTree as ET
from unittest.mock import Mock, patch, MagicMock

import pytest
from requests.exceptions import ConnectionError

from crossref import CrossrefHelper


@pytest.fixture
def crossref_helper():
    """Create a CrossrefHelper instance for testing."""
    return CrossrefHelper(
        server="https://test.crossref.org/servlet/deposit",
        creds=("test@example.com/test_org", "test_password_123")
    )


@pytest.fixture
def sample_doi_batch_elem():
    """Create a sample doi_batch ET.Element for testing."""
    # Register namespace to match production
    ET.register_namespace("", "http://www.crossref.org/schema/5.3.1")
    
    root = ET.Element("doi_batch", {
        "version": "5.3.1",
        "xmlns": "http://www.crossref.org/schema/5.3.1"
    })
    
    # Add minimal structure
    head = ET.SubElement(root, "head")
    doi_batch_id = ET.SubElement(head, "doi_batch_id")
    doi_batch_id.text = "TEST_BATCH_123"
    
    body = ET.SubElement(root, "body")
    database = ET.SubElement(body, "database")
    
    return root


def test_crossref_helper_initialization():
    """Test CrossrefHelper class initializes with correct attributes."""
    helper = CrossrefHelper(
        server="https://test.crossref.org/servlet/deposit",
        creds=("user@example.com/org", "secret_password")
    )
    
    assert helper.server == "https://test.crossref.org/servlet/deposit"
    assert helper.creds == ("user@example.com/org", "secret_password")


def test_crossref_helper_initialization_with_different_values():
    """Test CrossrefHelper with different credential values."""
    helper = CrossrefHelper(
        server="https://prod.crossref.org/servlet/deposit",
        creds=("different@stanford.edu/igvf", "different_password")
    )
    
    assert helper.server == "https://prod.crossref.org/servlet/deposit"
    assert helper.creds == ("different@stanford.edu/igvf", "different_password")


@patch('crossref.requests.post')
def test_post_successful_submission(mock_post, crossref_helper, sample_doi_batch_elem):
    """Test successful POST request to CrossRef."""
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "Success"
    mock_post.return_value = mock_response
    
    result = crossref_helper.post(sample_doi_batch_elem)
    
    assert result.status_code == 200
    assert mock_post.called
    assert mock_post.call_count == 1


@patch('crossref.requests.post')
def test_post_calls_correct_url(mock_post, crossref_helper, sample_doi_batch_elem):
    """Test that POST is called with the correct server URL."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    
    crossref_helper.post(sample_doi_batch_elem)
    
    # Check first positional argument (the URL)
    call_args = mock_post.call_args
    assert call_args[0][0] == "https://test.crossref.org/servlet/deposit"


@patch('crossref.requests.post')
def test_post_sends_correct_form_data(mock_post, crossref_helper, sample_doi_batch_elem):
    """Test that POST sends the correct form data fields."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    
    crossref_helper.post(sample_doi_batch_elem)
    
    call_kwargs = mock_post.call_args[1]
    data = call_kwargs['data']
    
    assert data['operation'] == 'doMDUpload'
    assert data['login_id'] == 'test@example.com/test_org'
    assert data['login_passwd'] == 'test_password_123'


@patch('crossref.requests.post')
def test_post_sends_xml_as_file(mock_post, crossref_helper, sample_doi_batch_elem):
    """Test that POST sends XML data as a file upload."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    
    crossref_helper.post(sample_doi_batch_elem)
    
    call_kwargs = mock_post.call_args[1]
    files = call_kwargs['files']
    
    assert 'fname' in files
    assert files['fname'][0] == 'submission.xml'
    
    # Check that it's bytes
    xml_bytes = files['fname'][1]
    assert isinstance(xml_bytes, bytes)


@patch('crossref.requests.post')
def test_post_converts_element_to_xml_bytes(mock_post, crossref_helper, sample_doi_batch_elem):
    """Test that ET.Element is properly converted to XML bytes."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    
    crossref_helper.post(sample_doi_batch_elem)
    
    call_kwargs = mock_post.call_args[1]
    xml_bytes = call_kwargs['files']['fname'][1]
    
    # Should start with XML declaration
    assert xml_bytes.startswith(b'<?xml')
    
    # Should contain the test data
    assert b'TEST_BATCH_123' in xml_bytes


@patch('crossref.requests.post')
def test_post_xml_has_correct_encoding(mock_post, crossref_helper, sample_doi_batch_elem):
    """Test that XML is encoded as UTF-8."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    
    crossref_helper.post(sample_doi_batch_elem)
    
    call_kwargs = mock_post.call_args[1]
    xml_bytes = call_kwargs['files']['fname'][1]
    
    # Decode should work with utf-8
    xml_string = xml_bytes.decode('utf-8')
    assert 'utf-8' in xml_string or 'UTF-8' in xml_string


@patch('crossref.requests.post')
def test_post_raises_connection_error(mock_post, sample_doi_batch_elem):
    """Test that ConnectionError is raised when server is unreachable."""
    mock_post.side_effect = ConnectionError("Server unreachable")
    
    helper = CrossrefHelper(
        server="https://test.crossref.org/servlet/deposit",
        creds=("test@example.com/test_org", "test_password_123")
    )
    
    with pytest.raises(ConnectionError):
        helper.post(sample_doi_batch_elem)


@patch('crossref.requests.post')
def test_post_raises_value_error_on_bad_status_code(mock_post, crossref_helper, sample_doi_batch_elem):
    """Test that ValueError is raised on non-200 status code."""
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_post.return_value = mock_response
    
    with pytest.raises(ValueError, match="Bad response code from CrossRef"):
        crossref_helper.post(sample_doi_batch_elem)


@patch('crossref.requests.post')
def test_post_raises_value_error_on_500_status(mock_post, crossref_helper, sample_doi_batch_elem):
    """Test that ValueError is raised on server error (500)."""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_post.return_value = mock_response
    
    with pytest.raises(ValueError, match="Bad response code from CrossRef"):
        crossref_helper.post(sample_doi_batch_elem)


@patch('crossref.requests.post')
def test_post_raises_value_error_on_404_status(mock_post, crossref_helper, sample_doi_batch_elem):
    """Test that ValueError is raised on not found (404)."""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_post.return_value = mock_response
    
    with pytest.raises(ValueError, match="Bad response code from CrossRef"):
        crossref_helper.post(sample_doi_batch_elem)


@patch('crossref.requests.post')
def test_post_returns_response_object(mock_post, crossref_helper, sample_doi_batch_elem):
    """Test that post method returns the response object."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "Success response"
    mock_post.return_value = mock_response
    
    result = crossref_helper.post(sample_doi_batch_elem)
    
    assert result is mock_response
    assert result.text == "Success response"


@patch('crossref.requests.post')
@patch('crossref.log')
def test_post_logs_request(mock_log, mock_post, crossref_helper, sample_doi_batch_elem):
    """Test that post method logs the request."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    
    crossref_helper.post(sample_doi_batch_elem)
    
    # Should have logged the posting action
    assert mock_log.warning.called
    log_calls = [str(call) for call in mock_log.warning.call_args_list]
    log_string = ' '.join(log_calls)
    assert 'CrossRef' in log_string or 'test.crossref.org' in log_string


@patch('crossref.requests.post')
@patch('crossref.log')
def test_post_logs_success(mock_log, mock_post, crossref_helper, sample_doi_batch_elem):
    """Test that successful post logs success message."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    
    crossref_helper.post(sample_doi_batch_elem)
    
    # Should have logged success
    log_calls = [str(call) for call in mock_log.warning.call_args_list]
    log_string = ' '.join(log_calls)
    assert 'Success' in log_string or 'posted' in log_string.lower()


@patch('crossref.requests.post')
@patch('crossref.log')
def test_post_logs_error_on_bad_status(mock_log, mock_post, crossref_helper, sample_doi_batch_elem):
    """Test that bad status code is logged."""
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request Error"
    mock_post.return_value = mock_response
    
    with pytest.raises(ValueError):
        crossref_helper.post(sample_doi_batch_elem)
    
    # Should have logged the error status
    log_calls = [str(call) for call in mock_log.warning.call_args_list]
    log_string = ' '.join(log_calls)
    assert '400' in log_string or 'Status code not 200' in log_string


@patch('crossref.requests.post')
@patch('crossref.log')
def test_post_logs_connection_error(mock_log, mock_post, crossref_helper, sample_doi_batch_elem):
    """Test that connection errors are logged."""
    mock_post.side_effect = ConnectionError("Cannot reach server")
    
    with pytest.raises(ConnectionError):
        crossref_helper.post(sample_doi_batch_elem)
    
    # Should have logged the connection issue
    log_calls = [str(call) for call in mock_log.warning.call_args_list]
    log_string = ' '.join(log_calls)
    assert 'not reachable' in log_string.lower() or 'CrossRef' in log_string


def test_post_with_complex_xml_structure(crossref_helper):
    """Test posting with a more complex XML structure."""
    # Create a more realistic XML structure
    root = ET.Element("doi_batch")
    head = ET.SubElement(root, "head")
    ET.SubElement(head, "doi_batch_id").text = "COMPLEX_BATCH"
    
    body = ET.SubElement(root, "body")
    database = ET.SubElement(body, "database")
    dataset = ET.SubElement(database, "dataset")
    
    titles = ET.SubElement(dataset, "titles")
    ET.SubElement(titles, "title").text = "Test Dataset"
    
    doi_data = ET.SubElement(dataset, "doi_data")
    ET.SubElement(doi_data, "doi").text = "10.12345/TEST123"
    
    with patch('crossref.requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        crossref_helper.post(root)
        
        # Verify the XML contains all the elements
        call_kwargs = mock_post.call_args[1]
        xml_bytes = call_kwargs['files']['fname'][1]
        xml_string = xml_bytes.decode('utf-8')
        
        assert 'COMPLEX_BATCH' in xml_string
        assert 'Test Dataset' in xml_string
        assert '10.12345/TEST123' in xml_string


def test_different_helpers_have_different_credentials():
    """Test that different instances maintain separate credentials."""
    helper1 = CrossrefHelper(
        server="https://server1.crossref.org",
        creds=("user1@test.com", "password1")
    )
    
    helper2 = CrossrefHelper(
        server="https://server2.crossref.org",
        creds=("user2@test.com", "password2")
    )
    
    assert helper1.server != helper2.server
    assert helper1.creds != helper2.creds

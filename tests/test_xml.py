#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Unit tests for the XML class."""

import xml.etree.ElementTree as ET
from datetime import datetime

import pytest

from crossref_xml import XML


def test_xml_initialization_with_minimal_data(minimal_portal_data):
    """Test XML class initializes with minimal valid data."""
    xml_obj = XML(minimal_portal_data)
    assert xml_obj.data == minimal_portal_data
    assert len(xml_obj.datasets) == 1
    assert xml_obj.datasets[0]['accession'] == 'IGVFDS1234TEST'


def test_xml_initialization_with_empty_graph(empty_portal_data):
    """Test XML class handles empty @graph."""
    xml_obj = XML(empty_portal_data)
    assert xml_obj.data == empty_portal_data
    assert xml_obj.datasets == []


def test_xml_initialization_without_graph_key(missing_graph_key):
    """Test XML class handles missing @graph key."""
    xml_obj = XML(missing_graph_key)
    assert xml_obj.data == missing_graph_key
    assert xml_obj.datasets == []


def test_xml_initialization_with_multiple_datasets(multi_dataset_portal_data):
    """Test XML class initializes with multiple datasets."""
    xml_obj = XML(multi_dataset_portal_data)
    assert len(xml_obj.datasets) == 2


def test_doi_batch_elem_property_lazy_builds(minimal_portal_data):
    """Test that doi_batch_elem property lazy builds the XML."""
    xml_obj = XML(minimal_portal_data)
    assert xml_obj._doi_batch_elem is None
    
    elem = xml_obj.doi_batch_elem
    assert elem is not None
    assert xml_obj._doi_batch_elem is not None
    assert elem.tag == "doi_batch"


def test_doi_batch_elem_property_caches_result(minimal_portal_data):
    """Test that doi_batch_elem property caches the built XML."""
    xml_obj = XML(minimal_portal_data)
    
    elem1 = xml_obj.doi_batch_elem
    elem2 = xml_obj.doi_batch_elem
    
    # Should return the same object (cached)
    assert elem1 is elem2


def test_doi_batch_elem_structure(minimal_portal_data):
    """Test basic structure of the doi_batch element."""
    xml_obj = XML(minimal_portal_data)
    root = xml_obj.doi_batch_elem
    
    assert root.tag == "doi_batch"
    assert "version" in root.attrib
    assert root.attrib["version"] == "5.3.1"
    
    # Check for HEAD and BODY
    children = list(root)
    tags = [child.tag for child in children]
    assert "head" in tags
    assert "body" in tags


def test_head_section_structure(minimal_portal_data):
    """Test the HEAD section contains required elements."""
    xml_obj = XML(minimal_portal_data)
    root = xml_obj.doi_batch_elem
    
    head = root.find("head")
    assert head is not None
    
    # Check required elements
    assert head.find("doi_batch_id") is not None
    assert head.find("timestamp") is not None
    assert head.find("depositor") is not None
    assert head.find("registrant") is not None


def test_head_section_depositor_structure(minimal_portal_data):
    """Test the depositor section in HEAD."""
    xml_obj = XML(minimal_portal_data)
    root = xml_obj.doi_batch_elem
    
    depositor = root.find("head/depositor")
    assert depositor is not None
    
    depositor_name = depositor.find("depositor_name")
    email = depositor.find("email_address")
    
    assert depositor_name is not None
    assert email is not None
    assert depositor_name.text is not None
    assert email.text is not None
    assert "@" in email.text


def test_head_section_timestamp_format(minimal_portal_data):
    """Test the timestamp format in HEAD."""
    xml_obj = XML(minimal_portal_data)
    root = xml_obj.doi_batch_elem
    
    timestamp = root.find("head/timestamp")
    assert timestamp is not None
    assert timestamp.text is not None
    
    # Should be in format YYYYMMDDHHMMSS (14 digits)
    assert len(timestamp.text) == 14
    assert timestamp.text.isdigit()


def test_body_section_structure(minimal_portal_data):
    """Test the BODY section contains database element."""
    xml_obj = XML(minimal_portal_data)
    root = xml_obj.doi_batch_elem
    
    body = root.find("body")
    assert body is not None
    
    database = body.find("database")
    assert database is not None


def test_database_metadata_structure(minimal_portal_data):
    """Test the database_metadata section."""
    xml_obj = XML(minimal_portal_data)
    root = xml_obj.doi_batch_elem
    
    database_metadata = root.find("body/database/database_metadata")
    assert database_metadata is not None
    assert database_metadata.attrib.get("language") == "en"
    
    # Check required elements
    assert database_metadata.find("titles") is not None
    assert database_metadata.find("description") is not None
    assert database_metadata.find("institution") is not None


def test_dataset_element_created(minimal_portal_data):
    """Test that dataset elements are created for each dataset."""
    xml_obj = XML(minimal_portal_data)
    root = xml_obj.doi_batch_elem
    
    database = root.find("body/database")
    datasets = database.findall("dataset")
    
    assert len(datasets) == 1
    assert datasets[0].attrib.get("dataset_type") == "record"


def test_multiple_dataset_elements_created(multi_dataset_portal_data):
    """Test that multiple dataset elements are created."""
    xml_obj = XML(multi_dataset_portal_data)
    root = xml_obj.doi_batch_elem
    
    database = root.find("body/database")
    datasets = database.findall("dataset")
    
    assert len(datasets) == 2


def test_dataset_contributors_structure(minimal_portal_data):
    """Test the contributors section in dataset."""
    xml_obj = XML(minimal_portal_data)
    root = xml_obj.doi_batch_elem
    
    dataset = root.find("body/database/dataset")
    contributors = dataset.find("contributors")
    
    assert contributors is not None
    
    organization = contributors.find("organization")
    assert organization is not None
    assert organization.attrib.get("contributor_role") == "author"
    assert organization.attrib.get("sequence") == "first"
    assert organization.text == "Test Lab, Test University"


def test_dataset_titles_structure(minimal_portal_data):
    """Test the titles section in dataset."""
    xml_obj = XML(minimal_portal_data)
    root = xml_obj.doi_batch_elem
    
    dataset = root.find("body/database/dataset")
    titles = dataset.find("titles")
    
    assert titles is not None
    
    title = titles.find("title")
    assert title is not None
    assert title.text == "IGVFDS1234TEST"


def test_dataset_publication_date_structure(minimal_portal_data):
    """Test the publication date structure in dataset."""
    xml_obj = XML(minimal_portal_data)
    root = xml_obj.doi_batch_elem
    
    dataset = root.find("body/database/dataset")
    database_date = dataset.find("database_date")
    
    assert database_date is not None
    
    publication_date = database_date.find("publication_date")
    assert publication_date is not None
    
    # Check all date components
    month = publication_date.find("month")
    day = publication_date.find("day")
    year = publication_date.find("year")
    
    assert month is not None
    assert day is not None
    assert year is not None
    
    assert month.text == "06"
    assert day.text == "05"
    assert year.text == "2025"


def test_dataset_description_from_description_field(dataset_with_description):
    """Test description uses 'description' field when available."""
    data = {'@graph': [dataset_with_description]}
    xml_obj = XML(data)
    root = xml_obj.doi_batch_elem
    
    dataset = root.find("body/database/dataset")
    description = dataset.find("description")
    
    assert description is not None
    assert description.attrib.get("language") == "en"
    assert description.text == "Detailed test description"


def test_dataset_description_from_summary_field(minimal_dataset):
    """Test description falls back to 'summary' field."""
    data = {'@graph': [minimal_dataset]}
    xml_obj = XML(data)
    root = xml_obj.doi_batch_elem
    
    dataset = root.find("body/database/dataset")
    description = dataset.find("description")
    
    assert description is not None
    assert description.text == "Test dataset summary"


def test_dataset_description_missing_when_no_fields():
    """Test description element omitted when no description or summary."""
    dataset = {
        'accession': 'IGVFDS9999NONE',
        'lab': {'title': 'Test Lab'},
        'release_timestamp': '2025-01-01T00:00:00.000000+00:00'
    }
    data = {'@graph': [dataset]}
    xml_obj = XML(data)
    root = xml_obj.doi_batch_elem
    
    dataset_elem = root.find("body/database/dataset")
    description = dataset_elem.find("description")
    
    assert description is None


def test_dataset_doi_data_structure(minimal_portal_data):
    """Test the DOI data section in dataset."""
    xml_obj = XML(minimal_portal_data)
    root = xml_obj.doi_batch_elem
    
    dataset = root.find("body/database/dataset")
    doi_data = dataset.find("doi_data")
    
    assert doi_data is not None
    
    doi = doi_data.find("doi")
    resource = doi_data.find("resource")
    
    assert doi is not None
    assert resource is not None
    
    # Check DOI format
    assert "IGVFDS1234TEST" in doi.text
    assert doi.text.startswith("10.65695/")
    
    # Check resource URL
    assert resource.text == "https://data.igvf.org/IGVFDS1234TEST/"


@pytest.mark.parametrize("timestamp,expected", [
    ("2025-06-05T17:44:01.605658+00:00", ("2025", "06", "05")),
    ("2024-12-25T10:30:00.000000+00:00", ("2024", "12", "25")),
    ("2023-01-01T00:00:00.000000+00:00", ("2023", "01", "01")),
    ("2025-11-30T23:59:59.999999+00:00", ("2025", "11", "30")),
])
def test_parse_release_date_valid_timestamps(timestamp, expected):
    """Test parsing various valid ISO timestamps."""
    result = XML.parse_release_date(timestamp)
    assert result == expected


def test_parse_release_date_returns_strings():
    """Test that parse_release_date returns strings, not integers."""
    result = XML.parse_release_date("2025-06-05T17:44:01.605658+00:00")
    year, month, day = result
    
    assert isinstance(year, str)
    assert isinstance(month, str)
    assert isinstance(day, str)


def test_parse_release_date_preserves_leading_zeros():
    """Test that parse_release_date preserves leading zeros."""
    result = XML.parse_release_date("2025-01-09T00:00:00.000000+00:00")
    year, month, day = result
    
    assert month == "01"
    assert day == "09"


def test_build_raises_error_on_invalid_timestamp():
    """Test that building XML raises error for invalid timestamp."""
    dataset = {
        'accession': 'IGVFDS1234BAD',
        'lab': {'title': 'Test Lab'},
        'release_timestamp': 'invalid-timestamp'
    }
    data = {'@graph': [dataset]}
    xml_obj = XML(data)
    
    with pytest.raises(ValueError, match="Could not parse release_timestamp"):
        _ = xml_obj.doi_batch_elem


def test_build_handles_missing_lab_gracefully():
    """Test that building XML handles missing lab info."""
    dataset = {
        'accession': 'IGVFDS1234NOLAB',
        'release_timestamp': '2025-06-05T17:44:01.605658+00:00',
        'summary': 'Test'
    }
    data = {'@graph': [dataset]}
    xml_obj = XML(data)
    root = xml_obj.doi_batch_elem
    
    dataset_elem = root.find("body/database/dataset")
    contributors = dataset_elem.find("contributors")
    organization = contributors.find("organization")
    
    assert organization.text == "Unknown Lab"


def test_xml_can_be_serialized():
    """Test that the generated XML can be serialized to string."""
    dataset = {
        'accession': 'IGVFDS1234SERIAL',
        'lab': {'title': 'Test Lab'},
        'release_timestamp': '2025-06-05T17:44:01.605658+00:00',
        'summary': 'Test serialization'
    }
    data = {'@graph': [dataset]}
    xml_obj = XML(data)
    root = xml_obj.doi_batch_elem
    
    # Should not raise an error
    xml_string = ET.tostring(root, encoding='unicode')
    assert xml_string is not None
    assert len(xml_string) > 0
    assert 'IGVFDS1234SERIAL' in xml_string


def test_xml_namespace_registered():
    """Test that XML namespace is properly registered."""
    data = {'@graph': []}
    xml_obj = XML(data)
    root = xml_obj.doi_batch_elem
    
    xml_string = ET.tostring(root, encoding='unicode')
    
    # Should not have namespace prefixes like ns0:
    assert 'ns0:' not in xml_string
    assert 'ns1:' not in xml_string

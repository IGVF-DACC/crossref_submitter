import time
import xml.etree.ElementTree as ET
from datetime import datetime

from constants import (
    DOI_PREFIX,
    SUBMITTER_NAME,
    SUBMITTER_EMAIL,
    REGISTRANT,
    IGVF_DESCRIPTION,
    STANFORD_UNIVERSITY,
    IGVF_DATASETS,
    SCHEMA_ELEMENT
)


class XML:
    """
    Class to build CrossRef XML for DOI submission from IGVF portal data.
    
    Takes a Python dict (parsed from IGVF portal JSON) and builds the
    doi_batch XML element tree conforming to CrossRef Schema 5.3.1.
    """
    
    def __init__(self, data: dict):
        """
        Initialize with IGVF portal data.
        
        Args:
            data: Dictionary with '@graph' key containing datasets
        """
        self.data = data
        self.datasets = self.data.get('@graph', [])
        self._doi_batch_elem = None
    
    @property
    def doi_batch_elem(self) -> ET.Element:
        if self._doi_batch_elem is None:
            self._doi_batch_elem = self._build()
        return self._doi_batch_elem
    
    def _build(self) -> ET.Element:
        """
        Build and return the doi_batch XML element.
        
        Returns:
            ET.Element: The complete doi_batch element tree
        
        Raises:
            ValueError: If required data is missing or malformed
        """
        # Register namespace to avoid prefixes
        ET.register_namespace("", "http://www.crossref.org/schema/5.3.1")
        
        # Create root element with schema 5.3.1
        doi_batch_elem = ET.Element("doi_batch", SCHEMA_ELEMENT)
        
        # Build HEAD section
        self._build_head(doi_batch_elem)
        
        # Build BODY section
        self._build_body(doi_batch_elem)
        
        return doi_batch_elem
    
    def _build_head(self, doi_batch_elem: ET.Element) -> None:
        """Build the HEAD section of the CrossRef XML."""
        head_elem = ET.SubElement(doi_batch_elem, "head")
        
        doi_batch_id_elem = ET.SubElement(head_elem, "doi_batch_id")
        doi_batch_id_elem.text = "IGVF Submission - " + str(datetime.now())
        
        timestamp_elem = ET.SubElement(head_elem, "timestamp")
        timestamp_elem.text = time.strftime("%Y%m%d%H%M%S")
        
        depositor_elem = ET.SubElement(head_elem, "depositor")
        depositor_name_elem = ET.SubElement(depositor_elem, "depositor_name")
        depositor_name_elem.text = SUBMITTER_NAME
        
        email_elem = ET.SubElement(depositor_elem, "email_address")
        email_elem.text = SUBMITTER_EMAIL
        
        registrant_elem = ET.SubElement(head_elem, "registrant")
        registrant_elem.text = REGISTRANT
    
    def _build_body(self, doi_batch_elem: ET.Element) -> None:
        """Build the BODY section of the CrossRef XML."""
        body_elem = ET.SubElement(doi_batch_elem, "body")
        database_elem = ET.SubElement(body_elem, "database")
        
        # Database metadata (parent-level DOI for the database)
        self._build_database_metadata(database_elem)
        
        # Process each dataset
        for item in self.datasets:
            self._build_dataset(database_elem, item)
    
    def _build_database_metadata(self, database_elem: ET.Element) -> None:
        """Build the database metadata section."""
        database_metadata_elem = ET.SubElement(
            database_elem, "database_metadata", {"language": "en"}
        )
        
        titles_elem = ET.SubElement(database_metadata_elem, "titles")
        title_elem = ET.SubElement(titles_elem, "title")
        title_elem.text = IGVF_DATASETS
        
        description_elem = ET.SubElement(database_metadata_elem, "description")
        description_elem.text = IGVF_DESCRIPTION
        
        institution_elem = ET.SubElement(database_metadata_elem, "institution")
        institution_name_elem = ET.SubElement(institution_elem, "institution_name")
        institution_name_elem.text = STANFORD_UNIVERSITY
    
    def _build_dataset(self, database_elem: ET.Element, item: dict) -> None:
        """
        Build a single dataset element.
        
        Args:
            database_elem: The database element to append to
            item: Dictionary containing dataset metadata
        """
        accession = item.get('accession')
        dataset_description = item.get('description')
        if not dataset_description:
            dataset_description = item.get('summary', '')
        
        lab_info = item.get('lab', {})
        lab_title = lab_info.get('title', 'Unknown Lab')
        
        release_timestamp = item.get('release_timestamp')
        try:
            year, month, day = self.parse_release_date(release_timestamp)
        except Exception as e:
            raise ValueError(
                f"Could not parse release_timestamp for {accession}: {e}"
            )
        
        dataset_elem = ET.SubElement(
            database_elem, "dataset", {"dataset_type": "record"}
        )
        
        # Contributors
        contributors_elem = ET.SubElement(dataset_elem, "contributors")
        organization_elem = ET.SubElement(
            contributors_elem,
            "organization",
            {"contributor_role": "author", "sequence": "first"}
        )
        organization_elem.text = lab_title
        
        # Titles
        dataset_titles_elem = ET.SubElement(dataset_elem, "titles")
        dataset_title_elem = ET.SubElement(dataset_titles_elem, "title")
        dataset_title_elem.text = accession
        
        # Publication date
        database_date_elem = ET.SubElement(dataset_elem, "database_date")
        publication_date_elem = ET.SubElement(database_date_elem, "publication_date")
        
        month_elem = ET.SubElement(publication_date_elem, "month")
        month_elem.text = month
        
        day_elem = ET.SubElement(publication_date_elem, "day")
        day_elem.text = day
        
        year_elem = ET.SubElement(publication_date_elem, "year")
        year_elem.text = year
        
        # Description
        if dataset_description:
            dataset_description_elem = ET.SubElement(
                dataset_elem, "description", {"language": "en"}
            )
            dataset_description_elem.text = dataset_description
        
        # DOI data
        doi_data_elem = ET.SubElement(dataset_elem, "doi_data")
        
        doi = f"{DOI_PREFIX}/{accession}"
        doi_elem = ET.SubElement(doi_data_elem, "doi")
        doi_elem.text = doi
        
        resource_url = f"https://data.igvf.org/{accession}/"
        resource_elem = ET.SubElement(doi_data_elem, "resource")
        resource_elem.text = resource_url
    
    @staticmethod
    def parse_release_date(timestamp_str: str) -> tuple:
        """
        Parse ISO timestamp to extract year, month, day.
        
        Args:
            timestamp_str: ISO timestamp string (e.g., "2025-06-05T17:44:01.605658+00:00")
        
        Returns:
            tuple: (year, month, day) as strings
        
        Example:
            >>> XML.parse_release_date("2025-06-05T17:44:01.605658+00:00")
            ('2025', '06', '05')
        """
        # Extract the date part before 'T'
        date_part = timestamp_str.split('T')[0]
        year, month, day = date_part.split('-')
        return year, month, day

import logging
import xml.etree.ElementTree as ET
import requests
from requests.exceptions import ConnectionError

log = logging.getLogger()


class CrossrefHelper:
    """
    Helper class for submitting DOI batches to CrossRef.
    
    Takes CrossRef server credentials and provides a method to post
    XML data (as ET.Element) to the CrossRef submission server.
    """

    def __init__(self, server: str, creds: tuple):
        """
        Initialize CrossrefHelper with server and credentials.
        
        Args:
            server: CrossRef server URL
            creds: CrossRef login credentials (email/organization format)
            login_passwd: CrossRef login password
        """
        self.server = server
        self.creds = creds

    def post(self, doi_batch_elem: ET.Element) -> requests.Response:
        """
        Post a DOI batch XML element to CrossRef.
        
        Args:
            doi_batch_elem: The doi_batch ET.Element to submit
            
        Returns:
            requests.Response: The response from CrossRef server
            
        Raises:
            ConnectionError: If the server cannot be reached
            ValueError: If the response status code indicates an error
        """
        log.warning('Posting DOI batch to CrossRef at {}'.format(self.server))
        
        # Convert ET.Element to XML bytes
        xml_bytes = ET.tostring(
            doi_batch_elem,
            encoding='utf-8',
            xml_declaration=True
        )
        
        # Prepare form data
        data = {
            'operation': 'doMDUpload',
            'login_id': self.creds[0],
            'login_passwd': self.creds[1]
        }
        
        # Prepare file upload (fname is the expected field name)
        files = {
            'fname': ('submission.xml', xml_bytes)
        }
        
        try:
            r = requests.post(self.server, data=data, files=files)
        except ConnectionError as e:
            log.warning('CrossRef server not reachable at {}'.format(self.server))
            raise e
        
        if r.status_code != 200:
            log.warning('Status code not 200 from CrossRef submission')
            log.warning('{} {}'.format(r.status_code, r.text))
            raise ValueError('Bad response code from CrossRef')
        
        log.warning('Successfully posted to CrossRef')
        return r

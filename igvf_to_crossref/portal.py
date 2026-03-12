import logging
import requests
from requests.exceptions import ConnectionError
log = logging.getLogger()


class IGVFPortalHelper():

    SEARCH_URL = "search/?type=PseudobulkSet?type=MeasurementSet&type=PredictionSet&type=ModelSet&type=AuxiliarySet&type=AnalysisSet&type=ConstructLibrarySet&status=released&doi!=*&field=accession&field=lab.title&field=release_timestamp&field=description&field=summary"
    
    def __init__(self, server, portal_creds):
        self.server = server
        self.creds = portal_creds
    
    @staticmethod
    def _zero_search_results(r):
        if r.status_code != 404:
            return False
        try:
            r = r.json()
        except Exception as e:
            r = {}
        conditions = [
            '@graph' in r,
            'total' in r,
            'notification' in r,
            len(r.get('@graph', [])) == 0,
            r.get('total') == 0,
            r.get('notification') == 'No results found',
        ]
        return all(conditions)

    def _make_search_url(self, limit: int = 1000):
        return f"{self.server}/{self.SEARCH_URL}&limit={limit}"

    def get(self, url, creds=None):
        log.warning('Getting {}'.format(url))
        try:
            r = requests.get(url, auth=creds or self.creds)
        except ConnectionError as e:
            log.warning('URL not found. Does {} exist?'.format(url))
            raise e
        if r.status_code != 200 and not self._zero_search_results(r):
            log.warning('Status code not 200. Does {} exist?'.format(url))
            log.warning('{} {}'.format(r.status_code, r.text))
            raise ValueError('Bad response code')
        return r

    def search_datasets_without_doi(self, limit: int = 1000):
        url = self._make_search_url(limit)
        return self.get(url)
    
    def patch(self, url, json, creds=None):
        log.warning('Patching {} with {}'.format(url, json))
        try:
            r = requests.patch(self.server + '/' + url, json=json, auth=creds or self.creds)
        except ConnectionError as e:
            log.warning('URL not found. Does {} exist?'.format(url))
            raise e
        if r.status_code != 200:
            log.warning('Status code not 200. Does {} exist?'.format(url))
            log.warning('{} {}'.format(r.status_code, r.text))
            raise ValueError('Bad response code')
        return r

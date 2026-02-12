#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import argparse
import json
import os
import time
import xml.etree.ElementTree as ET
from xml.dom import minidom as md

from .constants import DOI_PREFIX
from .crossref_xml import XML
from .portal import IGVFPortalHelper
from .crossref import CrossrefHelper


def get_parser():
    parser = argparse.ArgumentParser(
        description="Generate CrossRef XML for DOI submission from IGVF portal JSON metadata"
    )
    parser.add_argument(
        "--portal-key",
        default = os.environ.get("IGVF_PORTAL_KEY"),
        help="IGVF portal API key",
        action="store",
    )
    parser.add_argument(
        "--portal-secret-key",
        default = os.environ.get("IGVF_PORTAL_SECRET_KEY"),
        help="IGVF portal secret API key",
        action="store",
    )
    parser.add_argument(
        "--crossref-login",
        default = os.environ.get("CROSSREF_LOGIN"),
        help="CrossRef login for example: ojolanki@stanford.edu/igvf",
        action="store",
    )
    parser.add_argument(
        "--crossref-password",
        default = os.environ.get("CROSSREF_PASSWORD"),
        help="CrossRef password",
        action="store",
    )
    parser.add_argument(
        "-s",
        "--crossref-server",
        default = "https://test.crossref.org/servlet/deposit",
        choices = ["https://test.crossref.org/servlet/deposit", "https://doi.crossref.org/servlet/deposit"],
        help="CrossRef deposit server URL",
        action="store",
    )

    parser.add_argument(
        "--igvf-server",
        default = "https://api.staging.igvf.org",
        help="IGVF API server URL",
        action="store",
    )
    parser.add_argument(
        "--limit",
        default = 1000,
        help="Limit the number of datasets to search",
        action="store",
    )
    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()

    if not args.portal_key or not args.portal_secret_key:
        raise ValueError("IGVF portal API key and secret key are required")
    if not args.crossref_login or not args.crossref_password:
        raise ValueError("CrossRef login and password are required")
    if not args.crossref_server:
        raise ValueError("CrossRef server is required")
    if not args.igvf_server:
        raise ValueError("IGVF server is required")
    
    portal_creds = (args.portal_key, args.portal_secret_key)
    crossref_creds = (args.crossref_login, args.crossref_password)
    portal_helper = IGVFPortalHelper(args.igvf_server, portal_creds)
    crossref_helper = CrossrefHelper(args.crossref_server, crossref_creds)
    
    # get data from portal
    response = portal_helper.search_datasets_without_doi(args.limit)
    data = response.json()
    if not data.get('@graph') or len(data.get('@graph')) == 0:
        print(f"No datasets found", file=sys.stderr)
        sys.exit(0)
    
    xml_builder = XML(data)
    doi_batch_elem = xml_builder.doi_batch_elem
    
    
    # Submit DOI batch to CrossRef
    try:
        response = crossref_helper.post(doi_batch_elem)
        print(f"Successfully submitted DOI batch to CrossRef")
    except Exception as e:
        print(f"Error submitting DOI batch to CrossRef: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Prepare patch data
    patch_data = []
    for item in xml_builder.datasets:
        accession = item.get('accession')
        doi = f"{DOI_PREFIX}/{accession}"
        patch_data.append({
            'accession': accession,
            'doi': doi
        })
    
   # patch portal with DOIs
    for item in patch_data:
        try:
            response = portal_helper.patch(url= item['accession'], json={"doi": item['doi']})
            time.sleep(0.1)
        except Exception as e:
            print(f"Error patching portal with DOI: {e}", file=sys.stderr)
            sys.exit(1)



    
    print(f"Done. Processed {len(patch_data)} datasets.")


if __name__ == '__main__':
    main()

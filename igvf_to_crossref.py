#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import argparse
import json
import time
import xml.etree.ElementTree as ET
from xml.dom import minidom as md
from datetime import datetime


DOI_PREFIX = "10.65695"
SUBMITTER_NAME = "Otto Jolanki"
SUBMITTER_EMAIL = "ojolanki@stanford.edu"

def get_parser():
    parser = argparse.ArgumentParser(
        description="Generate CrossRef XML for DOI submission from IGVF portal JSON metadata"
    )
    parser.add_argument(
        "-i",
        "--infile",
        required=True,
        help="Input JSON file from IGVF portal query",
        action="store",
    )
    parser.add_argument(
        "-o",
        "--outfile",
        required=True,
        help="Output XML file in CrossRef Schema 5.3.1",
        action="store",
    )
    parser.add_argument(
        "-p",
        "--patchfile",
        required=True,
        help="Output TSV file to patch datasets with DOIs",
        action="store",
    )
    return parser


def format_xml(xml_string):
    """Pretty print XML with proper formatting."""
    lines = []
    for line in md.parseString(xml_string).toprettyxml().split('\n'):
        if line.strip():
            lines.append(line)
    return '\n'.join(lines)


def write_xml_to_file(element, out_file):
    """Write XML element to file with proper formatting."""
    # Convert to string
    rough_string = ET.tostring(element, encoding='unicode')
    
    # Pretty print
    formatted_xml = format_xml(rough_string)
    
    # Parse back to element tree to clean up whitespace in text nodes
    root = ET.fromstring(formatted_xml)
    
    def clean_text(elem):
        """Remove leading/trailing whitespace from text nodes."""
        elems = elem.findall('*')
        if len(elems) > 0:  # if any children
            for child in elems:
                clean_text(child)
        else:  # if no children (leaf node)
            if elem.text and len(elem.text) > 0:
                try:
                    # Strip leading/trailing whitespace
                    elem.text = elem.text.strip()
                except:
                    pass
    
    clean_text(root)
    
    # Write to file
    tree = ET.ElementTree(root)
    tree.write(out_file, encoding="UTF-8", xml_declaration=True)


def parse_release_date(timestamp_str):
    """
    Parse ISO timestamp to extract year, month, day.
    Example: "2025-06-05T17:44:01.605658+00:00" -> (2025, 06, 05)
    """
    # Extract the date part before 'T'
    date_part = timestamp_str.split('T')[0]
    year, month, day = date_part.split('-')
    return year, month, day


def main():
    parser = get_parser()
    args = parser.parse_args()
    
    infile = args.infile
    outfile = args.outfile
    patchfile = args.patchfile
    
    # Register namespace to avoid prefixes
    ET.register_namespace("", "http://www.crossref.org/schema/5.3.1")
    
    # Read and parse JSON input
    try:
        with open(infile, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Extract datasets from @graph
    if '@graph' not in data:
        print("Error: '@graph' key not found in input JSON", file=sys.stderr)
        sys.exit(1)
    
    datasets = data['@graph']
    
    # Create root element with schema 5.3.1
    doi_batch_elem = ET.Element("doi_batch", {
        "version": "5.3.1",
        "xmlns": "http://www.crossref.org/schema/5.3.1",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:schemaLocation": "http://www.crossref.org/schema/5.3.1 https://www.crossref.org/schemas/crossref5.3.1.xsd"
    })
    
    # Create HEAD section
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
    registrant_elem.text = "Stanford University, IGVF Data Coordination Center"
    
    # Create BODY section
    body_elem = ET.SubElement(doi_batch_elem, "body")
    database_elem = ET.SubElement(body_elem, "database")
    
    # Database metadata (parent-level DOI for the database)
    database_metadata_elem = ET.SubElement(database_elem, "database_metadata", {"language": "en"})
    
    titles_elem = ET.SubElement(database_metadata_elem, "titles")
    title_elem = ET.SubElement(titles_elem, "title")
    title_elem.text = "IGVF Datasets"
    
    description_elem = ET.SubElement(database_metadata_elem, "description")
    description_elem.text = (
        "The repository collection of genomics data from the Impact of Genomic Variation on Function (IGVF) "
        "project hosted and maintained by the IGVF Data Coordination Center based at Stanford University."
    )
    
    institution_elem = ET.SubElement(database_metadata_elem, "institution")
    institution_name_elem = ET.SubElement(institution_elem, "institution_name")
    institution_name_elem.text = "Stanford University"
    
    # Prepare patch file data
    patch_data = []
    
    # Process each dataset
    for item in datasets:
        # Extract required fields
        accession = item.get('accession')
        if not accession:
            print(f"Warning: Skipping item without accession: {item.get('@id', 'unknown')}", file=sys.stderr)
            continue
        
        # Use description if available, otherwise summary
        dataset_description = item.get('description')
        if not dataset_description:
            dataset_description = item.get('summary', '')
        
        lab_info = item.get('lab', {})
        lab_title = lab_info.get('title', 'Unknown Lab')
        
        release_timestamp = item.get('release_timestamp')
        if not release_timestamp:
            print(f"Warning: Skipping item {accession} without release_timestamp", file=sys.stderr)
            continue
        
        # Parse release date
        try:
            year, month, day = parse_release_date(release_timestamp)
        except Exception as e:
            print(f"Warning: Could not parse release_timestamp for {accession}: {e}", file=sys.stderr)
            continue
        
        # Create dataset element
        dataset_elem = ET.SubElement(database_elem, "dataset", {"dataset_type": "record"})
        
        # Contributors
        contributors_elem = ET.SubElement(dataset_elem, "contributors")
        organization_elem = ET.SubElement(
            contributors_elem,
            "organization",
            {"contributor_role": "author", "sequence": "first"}
        )
        organization_elem.text = lab_title
        
        # Title
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
            dataset_description_elem = ET.SubElement(dataset_elem, "description", {"language": "en"})
            dataset_description_elem.text = dataset_description
        
        # DOI data
        doi_data_elem = ET.SubElement(dataset_elem, "doi_data")
        
        doi = f"{DOI_PREFIX}/{accession}"
        doi_elem = ET.SubElement(doi_data_elem, "doi")
        doi_elem.text = doi
        
        resource_url = f"https://data.igvf.org/{accession}/"
        resource_elem = ET.SubElement(doi_data_elem, "resource")
        resource_elem.text = resource_url
        
        # Add to patch data
        patch_data.append({
            'record_id': accession,
            'doi': doi
        })
    
    # Write XML file
    try:
        write_xml_to_file(doi_batch_elem, outfile)
        print(f"Successfully wrote XML to {outfile}")
    except Exception as e:
        print(f"Error writing XML file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Write patch file
    try:
        with open(patchfile, 'w') as f:
            # Write header
            f.write("record_id\tdoi\n")
            # Write data
            for row in patch_data:
                f.write(f"{row['record_id']}\t{row['doi']}\n")
        print(f"Successfully wrote patch file to {patchfile}")
    except Exception as e:
        print(f"Error writing patch file: {e}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Done. Processed {len(patch_data)} datasets.")


if __name__ == '__main__':
    main()

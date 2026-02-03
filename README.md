# crossref_submitter

Generate CrossRef XML for DOI submission from IGVF portal JSON metadata.

## Installation

pip install .

## Testing

Run the test suite with pytest:
```bash
pip install -r requirements-dev.txt
pytest
```

Run with coverage:

```bash
pytest --cov=igvf-to-crossref --cov-report=html
```

Run a specific test file:

```bash
pytest tests/test_xml.py
```

Run a specific test:

```bash
pytest tests/test_xml.py::test_xml_initialization_with_minimal_data
```

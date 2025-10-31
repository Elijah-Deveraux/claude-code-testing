# Test Fixtures

This directory contains test fixtures (sample data files) used during testing.

## Files

### sample.pdf
A small sample PDF file used for testing the PDF processing pipeline.

**Note:** Due to the complexity of creating a valid PDF file programmatically, you should place a small test PDF here manually. The PDF should:
- Be small (< 1 MB)
- Have 2-5 pages
- Contain readable text content
- Be a valid PDF format

For testing purposes without a real PDF, the tests are designed to work with mocked components.

## Usage

Fixtures in this directory are accessed via pytest fixtures defined in `tests/conftest.py`.

Example:
```python
def test_pdf_loading(sample_pdf_path):
    # sample_pdf_path points to tests/fixtures/sample.pdf
    assert sample_pdf_path.exists()
```

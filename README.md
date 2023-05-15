# Welcome to PDF Parser ATL! 🌟

This is a Python script for parsing data from PDF files. It uses the fitz library for reading PDF files, ocrmypdf for performing OCR (Optical Character Recognition) on scanned PDFs, and requests for fetching PDFs from URLs. The script is designed to extract specific information such as vendor name, date, and monthly cost from PDF documents.

## Prerequisites
- `fitz` library: `pip install PyMuPDF`
- `ocrmypdf` library: `pip install ocrmypdf`
- `requests` library: `pip install requests`
- `pytesseract` library: `pip install pytesseract`

## Usage
To use the script, follow these steps:
- `Import the necessary libraries:`
```python
import fitz
import base64
import argparse
import json
import re
import io
import ocrmypdf
import requests
 ```

- `Instantiate the PDFParser class:`
```python
pdf_parser = PDFParser()
```
- `Use the parsePDF method to parse a PDF file:`
```python
result = pdf_parser.parsePDF('path/to/pdf_file.pdf', ocr=True)
```
The parsePDF method takes two arguments: the path to the PDF file and a boolean flag ocr indicating whether OCR should be performed on scanned PDFs. It returns a dictionary with the extracted information, including vendor name, date, and monthly cost.

- `Access the extracted information from the result dictionary:`
```python
vendor = result['Vendor']
date = result['Date']
monthly_cost = result['MonthlyCost']
```

## Additional Methods
The PDFParser class provides additional methods that you can use:

- `get_text(pdf, ocr=True)`: Returns the extracted text content from a PDF file.
- `text_file(pdf)`: Writes the extracted text content to a text file.
- `_pdf_to_text(pdf, scanned=False, ocr=True)` : Extracts text from a PDF file. If scanned is True, it performs OCR on the PDF. If ocr is False, OCR is not performed even for scanned PDFs.
- `_pdf_to_b64(pdf)`: Converts a PDF file to a base64-encoded string.
- `_scanned_pdf_to_txt(binary_stream)`: Performs OCR on a scanned PDF and returns the extracted text.





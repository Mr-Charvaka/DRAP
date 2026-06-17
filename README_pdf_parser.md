# PDF Table and Text Extractor (with Context Mapping)

A Python script using `pdfplumber` to extract both tables and unstructured text from a single-page PDF document, maintaining correct reading order, and pairing each table with its preceding section or header.

## Requirements

Ensure you have the required library installed:

```bash
pip install pdfplumber
```

## Usage

Run the script by passing the path of the PDF file as a command-line argument:

```bash
python pdf_parser.py <path_to_pdf>
```

This will output a structured JSON array containing the page elements ordered top-to-bottom. 

### Output Structure

The output will be an array of objects representing either text blocks or tables. Each table block includes its extracted grid and the `associated_context` string representing the section or heading directly preceding it.

```json
[
  {
    "type": "text",
    "content": "Section 1: Financial Report"
  },
  {
    "type": "table",
    "associated_context": "Section 1: Financial Report",
    "data": [
      ["Q1", "Q2", "Q3", "Q4"],
      ["100", "150", "200", "250"]
    ]
  }
]
```

## How It Works

1. **Table Detection:** It scans the page for tables and retrieves their bounding boxes (`bbox`).
2. **Text Filtering:** It extracts all words on the page and filters out any words that fall within the boundaries of any detected tables. This isolates the page's actual textual content (headers, paragraphs, notes) from text inside the table grid.
3. **Layout Reconstruction:** It groups remaining words into lines based on their vertical `top` coordinates, then reconstructs the paragraphs (blocks) based on vertical spacing.
4. **Sequential Merging:** Both the text blocks and table blocks are combined into a single list and sorted from top to bottom.
5. **Context Association:** The script iterates through the sorted list, auto-associating each table with the nearest preceding text block as its context (e.g. section header or paragraph).

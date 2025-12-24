# File Upload Filter Pipeline - CSV/XLSX Analysis

A **filter pipeline** for [Open WebUI](https://github.com/open-webui/open-webui) that automatically processes CSV and XLSX file uploads and makes their contents available for LLM analysis.

## Overview

This filter pipeline intercepts file uploads in Open WebUI and extracts data from CSV and Excel (XLSX) files, converting them into a format that the LLM can analyze. Simply upload your data file to the chat, and the model will have full access to its contents!

## Features

✅ **Automatic File Detection** - Automatically detects CSV and XLSX files in uploads
✅ **Smart Data Extraction** - Reads and parses spreadsheet data with encoding detection
✅ **Multiple Output Formats** - Supports Markdown tables, CSV, and JSON output
✅ **Data Statistics** - Shows row/column counts, data types, and numeric summaries
✅ **Configurable Limits** - Control max rows/columns to prevent context overflow
✅ **Data Preview** - Shows first few rows by default, with option for full dataset
✅ **Error Handling** - Graceful handling of malformed files and encoding issues
✅ **Zero Configuration** - Works out of the box with sensible defaults

## Installation

### 1. Install Dependencies

First, install the required Python packages:

```bash
pip install -r requirements_file_upload.txt
```

Or install manually:

```bash
pip install pandas>=2.0.0 openpyxl>=3.1.0 tabulate>=0.9.0
```

### 2. Install Pipeline in Open WebUI

1. **Copy the pipeline file** to your Open WebUI pipelines directory:
   ```bash
   cp file_upload_filter.py /path/to/openwebui/pipelines/
   ```

2. **Restart Open WebUI** to load the new pipeline

3. **Enable the filter** in Open WebUI:
   - Go to **Settings** → **Pipelines**
   - Find "File Upload Filter - CSV/XLSX"
   - Enable it

4. **(Optional) Configure settings** via the Valves interface

## Configuration

The pipeline exposes the following configuration options (Valves):

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_ROWS` | `1000` | Maximum number of rows to display (-1 for all rows) |
| `MAX_COLUMNS` | `50` | Maximum number of columns to display (-1 for all columns) |
| `SHOW_STATISTICS` | `true` | Show dataset statistics (row count, column info, data types) |
| `SHOW_PREVIEW` | `true` | Show first 10 rows as a preview table |
| `SHOW_FULL_DATA` | `false` | Include full dataset in output (WARNING: can be very large) |
| `OUTPUT_FORMAT` | `markdown` | Output format: `markdown`, `csv`, or `json` |

### Recommended Settings

**For small datasets (<100 rows):**
```
MAX_ROWS: -1 (show all)
SHOW_FULL_DATA: true
OUTPUT_FORMAT: markdown
```

**For medium datasets (100-10,000 rows):**
```
MAX_ROWS: 1000
SHOW_FULL_DATA: false
SHOW_PREVIEW: true
OUTPUT_FORMAT: markdown
```

**For large datasets (>10,000 rows):**
```
MAX_ROWS: 500
SHOW_FULL_DATA: false
SHOW_STATISTICS: true
OUTPUT_FORMAT: csv
```

## Usage

### Basic Usage

1. Start a new chat in Open WebUI
2. Click the **attachment button** (📎) to upload a file
3. Select your CSV or XLSX file
4. Add your question or request in the message
5. Send the message

The LLM will receive the file contents and can answer questions about the data!

### Example Queries

**Upload a sales.csv file and ask:**

```
"Analyze this sales data and tell me the top 5 products by revenue"
```

```
"What are the average sales by region?"
```

```
"Create a summary of monthly trends in this data"
```

```
"Are there any outliers or anomalies in the data?"
```

**Upload a financial_report.xlsx file and ask:**

```
"Calculate the profit margin for each product category"
```

```
"What's the year-over-year growth rate?"
```

```
"Which expenses have increased the most?"
```

### Output Example

When you upload a file, the filter adds information like this to your message:

```markdown
📊 **File Upload: sales_data.csv**

### Dataset Statistics:
- **Rows:** 1,234
- **Columns:** 8

### Columns:
- **Date** (object)
- **Product** (object)
- **Category** (object)
- **Revenue** (float64)
- **Quantity** (int64)
- **Region** (object)
- **Customer_Type** (object)
- **Discount** (float64)

### Numeric Column Summary:
|       | Revenue    | Quantity  | Discount  |
|-------|-----------|-----------|-----------|
| count | 1234.00   | 1234.00   | 1234.00   |
| mean  | 2567.45   | 45.23     | 0.12      |
| std   | 1234.56   | 23.45     | 0.08      |
| min   | 100.00    | 1.00      | 0.00      |
| 25%   | 1450.00   | 28.00     | 0.05      |
| 50%   | 2300.00   | 42.00     | 0.10      |
| 75%   | 3500.00   | 60.00     | 0.15      |
| max   | 9999.00   | 150.00    | 0.50      |

### Data Preview:
| Date       | Product    | Category | Revenue | Quantity | Region | Customer_Type | Discount |
|------------|------------|----------|---------|----------|--------|---------------|----------|
| 2024-01-01 | Widget A   | Tools    | 2500.00 | 50       | North  | Retail        | 0.10     |
| 2024-01-02 | Gadget B   | Electronics | 3200.00 | 32    | South  | Wholesale     | 0.15     |
...

*The LLM can now analyze this data. Ask questions about the data, request visualizations, or perform calculations.*
```

## Supported File Types

### CSV Files
- `.csv` extension
- Auto-detects encoding (UTF-8, Latin-1, ISO-8859-1, CP1252)
- Handles various delimiters and formats

### Excel Files
- `.xlsx` files (modern Excel format)
- `.xls` files (legacy Excel format)
- Reads the first sheet by default

## How It Works

1. **File Upload Detection**: The filter monitors all incoming messages for file attachments
2. **File Type Check**: Identifies CSV and XLSX files by extension and MIME type
3. **Data Extraction**: Uses pandas to read the file contents into a DataFrame
4. **Data Processing**: Applies row/column limits and generates statistics
5. **Format Conversion**: Converts data to the configured output format (Markdown/CSV/JSON)
6. **Context Injection**: Appends the formatted data to the user's message
7. **LLM Processing**: The LLM receives the message with embedded data and can analyze it

## Troubleshooting

### Issue: File not being processed

**Symptoms:** You upload a CSV/XLSX file but the filter doesn't process it

**Solutions:**
- Verify the file has a `.csv`, `.xlsx`, or `.xls` extension
- Check the pipeline is enabled in Settings → Pipelines
- Look for errors in the Open WebUI logs
- Try uploading a smaller test file first

### Issue: Encoding errors with CSV files

**Symptoms:** Error messages about character encoding or garbled text

**Solutions:**
- The filter tries multiple encodings automatically (UTF-8, Latin-1, etc.)
- If issues persist, try re-saving the CSV in UTF-8 encoding
- Use Excel to open and re-save as CSV (UTF-8)

### Issue: Memory errors with large files

**Symptoms:** Pipeline crashes or times out with large datasets

**Solutions:**
- Reduce `MAX_ROWS` to limit the data size (e.g., 500 or 1000)
- Set `SHOW_FULL_DATA` to `false`
- Consider splitting large files into smaller chunks
- Pre-process the file to include only necessary columns

### Issue: Data not showing in expected format

**Symptoms:** Data appears as text instead of a table

**Solutions:**
- Check the `OUTPUT_FORMAT` setting (try `markdown` for best formatting)
- Ensure `SHOW_PREVIEW` or `SHOW_FULL_DATA` is enabled
- Verify the CSV/XLSX file is not corrupted

### Issue: Numeric columns showing as text

**Symptoms:** Numbers are treated as strings in the analysis

**Solutions:**
- Check if the CSV has extra characters (spaces, currency symbols)
- Clean the data before uploading (remove commas in numbers)
- The filter will show data types - verify they are correct

## Performance Considerations

### Token Usage

File contents consume LLM context tokens. Estimate token usage:

- **Markdown table**: ~3-5 tokens per cell
- **CSV format**: ~2-3 tokens per cell
- **JSON format**: ~4-6 tokens per cell

**Example:** A 100-row × 10-column dataset in Markdown ≈ 3,000-5,000 tokens

### Recommendations

1. **For context-limited models** (4K-8K tokens):
   - Keep `MAX_ROWS` ≤ 200
   - Set `SHOW_FULL_DATA = false`
   - Use CSV format instead of Markdown

2. **For large context models** (32K-128K tokens):
   - Can handle `MAX_ROWS` = 1000-5000
   - `SHOW_FULL_DATA = true` is fine
   - Markdown format provides best readability

3. **For very large datasets**:
   - Ask the user to filter data before uploading
   - Process data in multiple messages
   - Use summary statistics instead of full data

## Advanced Usage

### Multiple File Uploads

You can upload multiple CSV/XLSX files in the same message:

```
Upload: sales_2023.csv, sales_2024.csv

"Compare the sales performance between 2023 and 2024"
```

Each file will be processed separately and added to the context.

### Combining with Other Pipelines

This filter works alongside other Open WebUI pipelines:

- **With RAG Pipeline**: Upload a CSV, then ask questions that combine file data with RAG knowledge
- **With Function Calling**: LLM can call functions to perform calculations on the uploaded data
- **With Vision Models**: Upload charts/graphs alongside data files for comprehensive analysis

### Custom Analysis Prompts

After uploading, guide the LLM with specific analysis requests:

```markdown
I've uploaded a dataset. Please:

1. Identify the top 3 trends or patterns
2. Calculate correlations between numeric columns
3. Suggest 3 actionable insights
4. Flag any data quality issues
```

## API Response Format

The filter modifies the incoming message body by appending processed file content to the user's message. The original file attachment remains, but the text content is enriched with the extracted data.

**Before filtering:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Analyze this sales data",
      "files": [
        {
          "name": "sales.csv",
          "type": "text/csv",
          "content": "<base64_encoded_data>"
        }
      ]
    }
  ]
}
```

**After filtering:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Analyze this sales data\n\n---\n\n📊 **File Upload: sales.csv**\n\n### Dataset Statistics:\n...",
      "files": [...]
    }
  ]
}
```

## Limitations

1. **Only processes first sheet** in multi-sheet Excel files (future enhancement)
2. **No formula evaluation** - only displays cell values
3. **Limited data types** - complex objects may not display properly
4. **Memory constraints** - very large files (>100MB) may cause issues
5. **No incremental processing** - entire file is loaded into memory

## Roadmap

Future enhancements planned:

- [ ] Multi-sheet Excel support
- [ ] Automatic data visualization generation
- [ ] Column type inference and validation
- [ ] Data quality checks and warnings
- [ ] Incremental loading for large files
- [ ] Support for Parquet and Feather formats
- [ ] SQL query interface for uploaded data
- [ ] Data caching for repeated queries

## Contributing

Issues and pull requests are welcome! Please ensure:
- Code follows existing style
- All features are tested with sample CSV/XLSX files
- Documentation is updated

## License

MIT License - See LICENSE file for details

## Support

For issues specific to:
- **This pipeline:** Open an issue in this repository
- **Open WebUI:** See [Open WebUI docs](https://docs.openwebui.com/)
- **Pandas/data issues:** See [Pandas documentation](https://pandas.pydata.org/)

---

**Enjoy analyzing your data with AI! 📊🤖**

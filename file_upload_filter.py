"""
title: File Upload Filter - CSV/XLSX Analysis
author: OpenWebUI Expert
description: Filter pipeline that processes CSV and XLSX file uploads and makes their contents available for LLM analysis
required_open_webui_version: 0.4.0+
version: 1.0.0
license: MIT
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import pandas as pd
import io
import base64
import logging

logger = logging.getLogger(__name__)


class Pipeline:
    """
    Filter pipeline for processing CSV and XLSX file uploads.

    This pipeline intercepts file uploads in Open WebUI and extracts data from
    CSV and XLSX files, making it available to the LLM for analysis.

    Features:
    - Automatic detection of CSV and XLSX files
    - Converts file data to markdown tables for LLM consumption
    - Configurable row limits to prevent context overflow
    - Provides data statistics and column information
    - Preserves original formatting where possible
    """

    class Valves(BaseModel):
        """Configuration options exposed in OpenWebUI UI"""
        MAX_ROWS: int = Field(
            default=1000,
            description="Maximum number of rows to display (use -1 for all rows)"
        )
        MAX_COLUMNS: int = Field(
            default=50,
            description="Maximum number of columns to display (use -1 for all columns)"
        )
        SHOW_STATISTICS: bool = Field(
            default=True,
            description="Show data statistics (row count, column count, data types)"
        )
        SHOW_PREVIEW: bool = Field(
            default=True,
            description="Show first few rows as preview table"
        )
        SHOW_FULL_DATA: bool = Field(
            default=False,
            description="Include full dataset in markdown format (WARNING: can be very large)"
        )
        OUTPUT_FORMAT: str = Field(
            default="markdown",
            description="Output format: 'markdown', 'csv', or 'json'"
        )

    def __init__(self):
        """Initialize the filter pipeline."""
        self.type = "filter"
        self.name = "File Upload Filter - CSV/XLSX"
        self.valves = self.Valves()

    async def on_startup(self):
        """Called when the pipeline starts."""
        logger.info(f"[File Upload Filter] Pipeline started")

    async def on_shutdown(self):
        """Called when the pipeline shuts down."""
        logger.info(f"[File Upload Filter] Pipeline stopped")

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """
        Process incoming messages and file uploads.

        This method is called before the message reaches the LLM.
        It extracts data from CSV/XLSX files and injects it into the conversation.
        """
        logger.info("[File Upload Filter] Processing inlet")

        # Check if there are any files in the message
        messages = body.get("messages", [])
        if not messages:
            return body

        # Process each message for file attachments
        for message in messages:
            if message.get("role") == "user":
                # Check for files in the message
                files = message.get("files", [])

                if files:
                    logger.info(f"[File Upload Filter] Found {len(files)} files")

                    # Process each file
                    for file_info in files:
                        processed_content = self._process_file(file_info)

                        if processed_content:
                            # Append the processed content to the user message
                            current_content = message.get("content", "")

                            # Add separator if there's existing content
                            if current_content:
                                current_content += "\n\n---\n\n"

                            message["content"] = current_content + processed_content
                            logger.info(f"[File Upload Filter] Added processed content to message")

        return body

    def _process_file(self, file_info: dict) -> Optional[str]:
        """
        Process a single file and extract its contents.

        Args:
            file_info: Dictionary containing file metadata and content

        Returns:
            Formatted string with file contents, or None if file cannot be processed
        """
        try:
            # Get file metadata
            file_name = file_info.get("name", "unknown")
            file_type = file_info.get("type", "")
            file_url = file_info.get("url", "")

            logger.info(f"[File Upload Filter] Processing file: {file_name} (type: {file_type})")

            # Check if this is a CSV or XLSX file
            is_csv = file_name.lower().endswith('.csv') or 'csv' in file_type.lower()
            is_xlsx = file_name.lower().endswith(('.xlsx', '.xls')) or 'spreadsheet' in file_type.lower() or 'excel' in file_type.lower()

            if not (is_csv or is_xlsx):
                logger.info(f"[File Upload Filter] Skipping non-CSV/XLSX file: {file_name}")
                return None

            # Get file content
            file_content = file_info.get("content", "")

            if not file_content:
                logger.warning(f"[File Upload Filter] No content found for file: {file_name}")
                return None

            # Decode base64 content if needed
            try:
                # Check if content is base64 encoded
                if "," in file_content and file_content.startswith("data:"):
                    # Extract base64 part
                    file_content = file_content.split(",", 1)[1]

                file_bytes = base64.b64decode(file_content)
            except Exception as e:
                logger.error(f"[File Upload Filter] Error decoding file content: {e}")
                # Try to use content as-is
                file_bytes = file_content.encode() if isinstance(file_content, str) else file_content

            # Read the file into a pandas DataFrame
            df = self._read_dataframe(file_bytes, is_csv, is_xlsx)

            if df is None or df.empty:
                logger.warning(f"[File Upload Filter] Could not read data from file: {file_name}")
                return None

            # Format the data for output
            formatted_content = self._format_dataframe(df, file_name)

            return formatted_content

        except Exception as e:
            logger.exception(f"[File Upload Filter] Error processing file: {e}")
            return f"❌ Error processing file '{file_name}': {str(e)}"

    def _read_dataframe(self, file_bytes: bytes, is_csv: bool, is_xlsx: bool) -> Optional[pd.DataFrame]:
        """
        Read file bytes into a pandas DataFrame.

        Args:
            file_bytes: Raw file content as bytes
            is_csv: Whether this is a CSV file
            is_xlsx: Whether this is an XLSX file

        Returns:
            pandas DataFrame or None if reading fails
        """
        try:
            if is_csv:
                # Try different encodings for CSV
                for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
                    try:
                        df = pd.read_csv(io.BytesIO(file_bytes), encoding=encoding)
                        logger.info(f"[File Upload Filter] Successfully read CSV with encoding: {encoding}")
                        return df
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        logger.warning(f"[File Upload Filter] Error reading CSV with {encoding}: {e}")
                        continue

                # If all encodings fail, try with error handling
                try:
                    df = pd.read_csv(io.BytesIO(file_bytes), encoding='utf-8', errors='replace')
                    logger.info(f"[File Upload Filter] Read CSV with error replacement")
                    return df
                except Exception as e:
                    logger.error(f"[File Upload Filter] Failed to read CSV: {e}")
                    return None

            elif is_xlsx:
                # Read XLSX file
                df = pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl')
                logger.info(f"[File Upload Filter] Successfully read XLSX file")
                return df

            return None

        except Exception as e:
            logger.exception(f"[File Upload Filter] Error reading dataframe: {e}")
            return None

    def _format_dataframe(self, df: pd.DataFrame, file_name: str) -> str:
        """
        Format a DataFrame into a string suitable for LLM consumption.

        Args:
            df: pandas DataFrame to format
            file_name: Name of the source file

        Returns:
            Formatted string with file data and metadata
        """
        output_parts = []

        # Add header
        output_parts.append(f"📊 **File Upload: {file_name}**\n")

        # Add statistics if enabled
        if self.valves.SHOW_STATISTICS:
            stats = self._get_statistics(df)
            output_parts.append(stats)

        # Apply row and column limits
        limited_df = df.copy()

        if self.valves.MAX_ROWS > 0 and len(limited_df) > self.valves.MAX_ROWS:
            limited_df = limited_df.head(self.valves.MAX_ROWS)
            output_parts.append(f"\n⚠️ *Showing first {self.valves.MAX_ROWS} of {len(df)} rows*\n")

        if self.valves.MAX_COLUMNS > 0 and len(limited_df.columns) > self.valves.MAX_COLUMNS:
            limited_df = limited_df.iloc[:, :self.valves.MAX_COLUMNS]
            output_parts.append(f"\n⚠️ *Showing first {self.valves.MAX_COLUMNS} of {len(df.columns)} columns*\n")

        # Add preview or full data based on configuration
        if self.valves.SHOW_PREVIEW or self.valves.SHOW_FULL_DATA:
            preview_df = limited_df.head(10) if self.valves.SHOW_PREVIEW and not self.valves.SHOW_FULL_DATA else limited_df

            if self.valves.OUTPUT_FORMAT == "markdown":
                output_parts.append("\n### Data Preview:\n")
                output_parts.append(preview_df.to_markdown(index=False))

            elif self.valves.OUTPUT_FORMAT == "csv":
                output_parts.append("\n### Data (CSV Format):\n```csv\n")
                output_parts.append(preview_df.to_csv(index=False))
                output_parts.append("```")

            elif self.valves.OUTPUT_FORMAT == "json":
                output_parts.append("\n### Data (JSON Format):\n```json\n")
                output_parts.append(preview_df.to_json(orient='records', indent=2))
                output_parts.append("\n```")

        # Add full data context for the LLM (if SHOW_FULL_DATA is enabled)
        if self.valves.SHOW_FULL_DATA and len(limited_df) > 10:
            output_parts.append("\n### Full Dataset:\n")
            if self.valves.OUTPUT_FORMAT == "markdown":
                output_parts.append(limited_df.to_markdown(index=False))
            elif self.valves.OUTPUT_FORMAT == "csv":
                output_parts.append("```csv\n")
                output_parts.append(limited_df.to_csv(index=False))
                output_parts.append("```")
            elif self.valves.OUTPUT_FORMAT == "json":
                output_parts.append("```json\n")
                output_parts.append(limited_df.to_json(orient='records', indent=2))
                output_parts.append("\n```")

        output_parts.append("\n\n*The LLM can now analyze this data. Ask questions about the data, request visualizations, or perform calculations.*")

        return "\n".join(output_parts)

    def _get_statistics(self, df: pd.DataFrame) -> str:
        """
        Generate statistics about the DataFrame.

        Args:
            df: pandas DataFrame

        Returns:
            Formatted string with statistics
        """
        stats_parts = ["### Dataset Statistics:"]
        stats_parts.append(f"- **Rows:** {len(df):,}")
        stats_parts.append(f"- **Columns:** {len(df.columns):,}")

        # Add column information
        stats_parts.append("\n### Columns:")
        for col in df.columns:
            dtype = df[col].dtype
            non_null = df[col].count()
            null_count = len(df) - non_null

            col_info = f"- **{col}** ({dtype})"
            if null_count > 0:
                col_info += f" - {null_count:,} null values"
            stats_parts.append(col_info)

        # Add numeric column statistics
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            stats_parts.append("\n### Numeric Column Summary:")
            summary = df[numeric_cols].describe()
            stats_parts.append(summary.to_markdown())

        return "\n".join(stats_parts)

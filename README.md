# RAG Pipelines

A collection of **intelligent pipelines** for [Open WebUI](https://github.com/open-webui/open-webui) that enhance LLM capabilities with external data sources.

## Available Pipelines

### 1. File Upload Filter - CSV/XLSX Analysis (NEW!)
A **filter pipeline** that automatically processes uploaded CSV and XLSX files and makes their contents available for LLM analysis:
- Automatic detection and parsing of spreadsheet files
- Smart data extraction with multiple output formats (Markdown, CSV, JSON)
- Data statistics and previews
- Configurable row/column limits
- Zero configuration - works out of the box!

See [FILE_UPLOAD_FILTER_README.md](FILE_UPLOAD_FILTER_README.md) for details.

### 2. RAG Manifold Pipeline
A **RAG (Retrieval-Augmented Generation) Manifold Pipeline** that integrates external RAG systems with Ollama language models.

### 3. Stock Data Pipeline v2.0
An **intelligent stock market pipeline** that provides:
- Real-time stock data (prices, news, earnings, financials)
- **Investment recommendations** with personalized advice
- **Market screening** (top gainers/losers, trending stocks)
- **Sector analysis** (hot/cold sectors, sector leaders)
- Automatic data fetching - no need to specify stocks!

See [STOCK_PIPELINE_README.md](STOCK_PIPELINE_README.md) for details.

---

## RAG Manifold Pipeline

### Overview

This pipeline acts as a middleware layer that:
1. Queries an external RAG API to retrieve relevant documents based on user questions
2. Injects the retrieved context into the conversation
3. Forwards augmented queries to Ollama for response generation
4. Supports multiple collections and provides proper source citations

## Features

✅ **Multi-Collection Support** - Query multiple document collections simultaneously (e.g., `api_docs,personal_documents`)
✅ **Automatic Citations in GUI** - Citations automatically appear as a footer in every response
✅ **Proper Citations** - Each result includes collection name, source file, document type, and relevance score
✅ **Streaming Support** - Full support for streaming responses from Ollama with citations
✅ **Flexible Configuration** - All settings exposed via Open WebUI's Valves system
✅ **Error Resilience** - Graceful degradation if RAG API is unavailable
✅ **Dual API Support** - Works with both Ollama native API and OpenAI-compatible endpoints

## Installation

1. **Copy the pipeline file** to your Open WebUI pipelines directory:
   ```bash
   cp rag_manifold_v3.py /path/to/openwebui/pipelines/
   ```

2. **Restart Open WebUI** to load the new pipeline

3. **Configure the pipeline** in Open WebUI's Admin Panel → Pipelines

## Configuration

The pipeline exposes the following configuration options (Valves):

| Setting | Default | Description |
|---------|---------|-------------|
| `RAG_API_URL` | `http://192.168.4.10:8012/query` | URL of your external RAG query API |
| `DEFAULT_COLLECTION` | `default` | Collection name(s) to query - supports comma-separated values |
| `TOP_K` | `5` | Maximum number of results to retrieve across all collections |
| `UPSTREAM_BASE_URL` | `http://192.168.4.10:11434` | Ollama server base URL |
| `USE_OLLAMA_NATIVE` | `true` | Use Ollama native API (recommended) vs OpenAI-compatible |
| `ENABLE_RAG` | `true` | Enable/disable RAG augmentation (useful for debugging) |
| `SHOW_CITATIONS` | `true` | Automatically append citations footer to all responses |

## Usage

### Single Collection

Set `DEFAULT_COLLECTION` to a single collection name:
```
default
```

### Multiple Collections

Set `DEFAULT_COLLECTION` to comma-separated collection names:
```
api_docs,personal_documents,company_wiki
```

The pipeline will:
- Query each collection independently
- Combine and sort results by relevance (distance)
- Return the top K results overall
- Tag each result with its source collection

### Example Query Flow

**User Question:** "How do I configure authentication?"

**Pipeline Process:**
1. Queries `api_docs` collection → gets 3 results
2. Queries `personal_documents` collection → gets 2 results
3. Combines and sorts all 5 results by distance
4. Injects top 5 results as context with citations

**LLM Response (in OpenWebUI):**
```
To configure authentication, you need to edit the config.yml file [1].
The authentication middleware is located in the src/auth directory [3].
For production environments, make sure to enable 2FA [2].

---
**Sources:**
[1] | Collection: api_docs | Source: auth-guide.pdf | Type: text | Chunk: 0 | Relevance: 0.23
[2] | Collection: personal_documents | Source: security-checklist.md | Type: text | Chunk: 2 | Relevance: 0.31
[3] | Collection: api_docs | Source: middleware-docs.pdf | Type: text | Chunk: 5 | Relevance: 0.35
```

**Note:** Citations are automatically appended to every response when `SHOW_CITATIONS` is enabled (default).

## RAG API Requirements

The pipeline expects your RAG API to support the following endpoint:

**POST** `/query`

**Request Body:**
```json
{
  "query": "user question text",
  "collection": "collection_name",
  "n_results": 5
}
```

**Response Format:**
```json
{
  "results": [
    {
      "document": "text content of the document chunk",
      "distance": 0.234,
      "metadata": {
        "source": "filename.pdf",
        "type": "text",
        "chunk_index": 0
      }
    }
  ]
}
```

## Troubleshooting

**For detailed troubleshooting steps, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**

### Quick Checks

**Test the logic:**
```bash
python3 test_multi_collection.py
```

**Common Issues:**

1. **Only one collection is searched**
   - Verify both collections exist and have documents
   - Check OpenWebUI logs for `[RAG Pipeline]` messages
   - Test each collection individually first
   - See [TROUBLESHOOTING.md](TROUBLESHOOTING.md#issue-1-only-latest-collection-is-being-searched)

2. **Citations not appearing**
   - Citations are in the context sent to the LLM, not shown directly in UI
   - Ask the LLM: "What sources did you use?"
   - Check that your RAG API returns metadata
   - See [TROUBLESHOOTING.md](TROUBLESHOOTING.md#issue-2-citations-not-appearing)

3. **No results from RAG API**
   - Verify RAG API is accessible
   - Check logs for "RAG API error" messages
   - Test API directly with curl

4. **Streaming not working**
   - Ensure `USE_OLLAMA_NATIVE` is `true`
   - Verify Ollama is running and accessible
   - Check Ollama version supports `/api/chat` endpoint

## Architecture

```
User Question
     ↓
┌────────────────────────────────────────┐
│  RAG Manifold Pipeline                 │
│                                        │
│  1. Query RAG API (multi-collection)   │
│     ├─→ Collection 1                   │
│     ├─→ Collection 2                   │
│     └─→ Collection N                   │
│                                        │
│  2. Combine & Sort Results             │
│                                        │
│  3. Build Context with Citations       │
│                                        │
│  4. Inject Context → User Message      │
└────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────┐
│  Ollama LLM                            │
│  (receives augmented message)          │
└────────────────────────────────────────┘
     ↓
Response to User
```

## Version History

### v3.3.0 (Latest)
- ✅ **Automatic citation footer** - Citations now appear in OpenWebUI GUI
- ✅ Added `SHOW_CITATIONS` valve to control citation display
- ✅ LLM instructed to cite sources using [1], [2] reference numbers
- ✅ Citations include collection, source, type, chunk, and relevance
- ✅ Works with both streaming and non-streaming responses

### v3.2.1
- ✅ Enhanced logging for multi-collection debugging
- ✅ Added detailed logging for context building and citation tracking
- ✅ Optimized single vs multi-collection query paths
- ✅ Added test script for verifying functionality
- ✅ Added comprehensive troubleshooting guide

### v3.2.0
- ✅ Added multi-collection support (comma-separated)
- ✅ Added collection name to citations
- ✅ Improved result sorting across collections

### v3.1.0
- Fixed RAG API payload format
- Fixed Ollama streaming response parsing
- Enabled Ollama native API by default
- Better error handling

## License

MIT License - See LICENSE file for details

## Contributing

Issues and pull requests are welcome! Please ensure:
- Code follows existing style
- All features are tested with Open WebUI
- Documentation is updated

---

## Stock Data Pipeline v2.0

### Overview

The Stock Data Pipeline is an intelligent market analysis system that automatically detects stock-related queries and provides comprehensive data, investment recommendations, and market insights.

### Features

#### Core Stock Features
✅ **Multi-API Integration** - Combines data from Finnhub and Alpha Vantage
✅ **Automatic Detection** - Detects stock queries and ticker symbols
✅ **Real-time Quotes** - Current prices, changes, highs, lows
✅ **Company Data** - Profiles, financials, market cap, revenue
✅ **News Articles** - Recent news with summaries and sources
✅ **Earnings Data** - Historical earnings, EPS, estimates
✅ **Price History** - Daily price trends and analysis

#### NEW: Investment Intelligence (v2.0)
✅ **Investment Recommendations** - Personalized stock suggestions
✅ **Market Screening** - Top gainers, losers, and market movers
✅ **Sector Analysis** - Hot sectors and sector leaders
✅ **Market Overview** - Real-time indices (S&P 500, NASDAQ, Dow)
✅ **Smart Questionnaire** - Asks about risk tolerance and goals
✅ **Automated Fetching** - No need to specify stocks explicitly

### Quick Start

1. **Get API Keys**
   - Finnhub: https://finnhub.io (free tier available)
   - Alpha Vantage: https://www.alphavantage.co (free tier available)

2. **Install Pipeline**
   ```bash
   cp stock_data_pipeline.py /path/to/openwebui/pipelines/
   ```

3. **Configure in OpenWebUI**
   - Set `FINNHUB_API_KEY`
   - Set `ALPHA_VANTAGE_API_KEY`
   - Set `UPSTREAM_BASE_URL` (your Ollama URL)

4. **Test It**
   ```
   User: "What's the current price of Apple stock?"
   Pipeline: [Fetches AAPL data from APIs]
   LLM: "Apple (AAPL) is currently trading at $178.50, up $2.30 (1.31%)..."
   ```

### Example Queries

**Specific Stocks:**
- "What's the stock price of Tesla?"
- "Show me Microsoft's recent earnings"
- "Compare NVDA and AMD stock performance"

**Investment Advice (NEW v2.0):**
- "What should I invest in?"
- "Give me stock recommendations"
- "What are the best stocks to buy?"

**Market Screening (NEW v2.0):**
- "What's hot in the market?"
- "Show me trending stocks"
- "Which sectors are performing well?"

### Documentation

For detailed documentation, see:
- [STOCK_PIPELINE_README.md](STOCK_PIPELINE_README.md) - Complete guide
- [stock_pipeline_config_example.md](stock_pipeline_config_example.md) - Configuration examples

---

## Support

For issues specific to:
- **This pipeline:** Open an issue in this repository
- **Open WebUI:** See [Open WebUI docs](https://docs.openwebui.com/)
- **Ollama:** See [Ollama docs](https://ollama.ai/)

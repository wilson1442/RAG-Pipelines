# RAG Pipelines

A **RAG (Retrieval-Augmented Generation) Manifold Pipeline** for [Open WebUI](https://github.com/open-webui/open-webui) that integrates external RAG systems with Ollama language models.

## Overview

This pipeline acts as a middleware layer that:
1. Queries an external RAG API to retrieve relevant documents based on user questions
2. Injects the retrieved context into the conversation
3. Forwards augmented queries to Ollama for response generation
4. Supports multiple collections and provides proper source citations

## Features

✅ **Multi-Collection Support** - Query multiple document collections simultaneously (e.g., `api_docs,personal_documents`)
✅ **Proper Citations** - Each result includes collection name, source file, document type, and relevance score
✅ **Streaming Support** - Full support for streaming responses from Ollama
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

**Context Injected:**
```
[1] Authentication can be configured via the config.yml file...
    (distance: 0.23, collection: api_docs, source: auth-guide.pdf, type: text, chunk: 0)

[2] Personal notes: Remember to enable 2FA in production...
    (distance: 0.31, collection: personal_documents, source: security-checklist.md, type: text, chunk: 2)

[3] The authentication middleware is located in...
    (distance: 0.35, collection: api_docs, source: middleware-docs.pdf, type: text, chunk: 5)
```

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

### No results from RAG API

**Symptoms:** Pipeline works but no context is injected

**Check:**
- Verify RAG API is accessible at the configured URL
- Check logs for "RAG API error" messages
- Test the API directly with curl/Postman
- Ensure collection names are correct

### Only one collection is searched

**Solution:** This was fixed in v3.2.0. Update to the latest version and ensure collections are comma-separated without quotes:
```
api_docs,personal_documents
```

### Missing collection citations

**Solution:** Updated in v3.2.0. Each result now includes the collection name in its citation metadata.

### Streaming not working

**Check:**
- Ensure `USE_OLLAMA_NATIVE` is set to `true`
- Verify Ollama is running and accessible
- Check Ollama version (requires recent version with `/api/chat` endpoint)

### Connection errors to Ollama

**Check:**
- Verify `UPSTREAM_BASE_URL` is correct
- Ensure Ollama is running: `ollama serve`
- Test connection: `curl http://192.168.4.10:11434/api/tags`

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

### v3.2.0 (Latest)
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

## Support

For issues specific to:
- **This pipeline:** Open an issue in this repository
- **Open WebUI:** See [Open WebUI docs](https://docs.openwebui.com/)
- **Ollama:** See [Ollama docs](https://ollama.ai/)

# Troubleshooting Multi-Collection and Citation Issues

## Quick Diagnosis

Run the test script to verify the logic works correctly:
```bash
python3 test_multi_collection.py
```

If the test passes but you're still having issues, the problem is likely with your RAG API or OpenWebUI configuration.

## Issue 1: Only Latest Collection is Being Searched

### Symptoms
When using `api_docs,personal_documents`, only results from `personal_documents` appear.

### Diagnosis Steps

1. **Check OpenWebUI Logs**

   Enable detailed logging in OpenWebUI to see the pipeline logs:

   Look for these log messages:
   ```
   [RAG Pipeline] Collections to query: ['api_docs', 'personal_documents']
   [RAG Pipeline] Multi-collection mode: querying 2 collections
   [RAG Pipeline] Querying collection 1/2: 'api_docs'
   [RAG Pipeline] Collection 'api_docs' returned X results
   [RAG Pipeline] Querying collection 2/2: 'personal_documents'
   [RAG Pipeline] Collection 'personal_documents' returned Y results
   [RAG Pipeline] Total results so far: X+Y
   [RAG Pipeline] Final N results from collections: {'api_docs', 'personal_documents'}
   ```

2. **Check Valve Configuration**

   In OpenWebUI Admin Panel → Pipelines → RAG Manifold v3:
   - Verify `DEFAULT_COLLECTION` is set to: `api_docs,personal_documents` (no quotes, no extra spaces)
   - Do NOT use quotes around the value
   - Ensure there are no hidden characters

3. **Test Each Collection Individually**

   Set `DEFAULT_COLLECTION` to just `api_docs`:
   - Make a query, check results

   Set `DEFAULT_COLLECTION` to just `personal_documents`:
   - Make a query, check results

   If one collection returns no results, that collection might not exist or be empty.

4. **Check RAG API Response**

   Manually test your RAG API to ensure both collections return results:

   ```bash
   # Test collection 1
   curl -X POST http://192.168.4.10:8012/query \
     -H "Content-Type: application/json" \
     -d '{
       "query": "your test query",
       "collection": "api_docs",
       "n_results": 5
     }'

   # Test collection 2
   curl -X POST http://192.168.4.10:8012/query \
     -H "Content-Type: application/json" \
     -d '{
       "query": "your test query",
       "collection": "personal_documents",
       "n_results": 5
     }'
   ```

### Common Causes

**Cause 1: One collection has much better matches**
- The pipeline queries both collections but sorts all results by distance
- If `personal_documents` has much lower distance scores (better matches), its results will dominate
- Solution: Check the `distance` values in the logs to see if this is the case
- You can increase `TOP_K` to get more results from both collections

**Cause 2: One collection is empty or doesn't exist**
- The RAG API returns no results for `api_docs` because it doesn't exist or is empty
- Solution: Check your RAG API database/storage to ensure both collections exist and have documents

**Cause 3: RAG API timeout or error**
- The first collection times out or errors, so only the second collection succeeds
- Solution: Check RAG API logs for errors, increase timeout if needed

**Cause 4: Valve configuration not saved**
- Changes to `DEFAULT_COLLECTION` weren't saved or applied
- Solution: Click Save, then refresh/restart OpenWebUI

## Issue 2: Citations Not Appearing

### Symptoms
RAG results are being used, but you don't see the collection name, source, or other metadata in the response.

### Important Note
**The citations are injected into the CONTEXT sent to the LLM, not shown directly in the UI.**

The citations look like this in the context:
```
[1] Document content here...
    (distance: 0.23, collection: api_docs, source: auth.pdf, type: text, chunk: 0)
```

The LLM sees these citations and may reference them in its response, but they won't automatically appear as footnotes in the UI.

### Diagnosis Steps

1. **Check Context is Being Built**

   Look for these logs:
   ```
   [RAG Pipeline] Building context for result 1: collection=api_docs, source=..., distance=...
   [RAG Pipeline] Built context with N citations, XXX chars total
   [RAG Pipeline] Injected context into message (total length: XXXX chars)
   ```

2. **Check Metadata from RAG API**

   Ensure your RAG API returns proper metadata:
   ```json
   {
     "results": [
       {
         "document": "content here",
         "distance": 0.23,
         "metadata": {
           "source": "filename.pdf",
           "type": "text",
           "chunk_index": 0
         }
       }
     ]
   }
   ```

   The `metadata` field must exist and contain the fields you want to see.

3. **Verify Context in LLM Prompt**

   Look for the debug log:
   ```
   [RAG Pipeline] Augmented message preview: Use the following CONTEXT...
   ```

   This shows the first 500 chars of what's sent to the LLM, including citations.

4. **Ask the LLM to Show Sources**

   In your query, ask explicitly:
   - "What sources did you use to answer this?"
   - "Which collection did this information come from?"
   - "Show me the citations for this answer"

   The LLM can see the citations and should be able to reference them.

### Common Causes

**Cause 1: RAG API doesn't return metadata**
- Your RAG API response doesn't include the `metadata` field
- Solution: Update your RAG API to include metadata in responses

**Cause 2: Metadata fields are named differently**
- Your RAG API uses different field names (e.g., `file` instead of `source`)
- Solution: Modify the `_build_context()` method to use your field names

**Cause 3: Collection name not being tagged**
- This should be fixed in v3.2.1, but check the logs to confirm
- Look for: `Building context for result 1: collection=N/A`
- If collection is N/A, the tagging isn't working

**Cause 4: LLM is ignoring the citations**
- The context is there, but the LLM doesn't mention it in responses
- Solution: Modify the prompt in `_inject_context()` to be more explicit:
  ```python
  "Please cite your sources using the [1], [2], etc. references provided."
  ```

## Configuration Checklist

- [ ] `DEFAULT_COLLECTION` format: `collection1,collection2` (comma-separated, no quotes)
- [ ] Both collections exist in your RAG database
- [ ] Both collections have documents indexed
- [ ] RAG API is accessible from OpenWebUI server
- [ ] `RAG_API_URL` is correct
- [ ] `TOP_K` is set high enough (try 10 to see more results)
- [ ] `ENABLE_RAG` is set to `true`
- [ ] OpenWebUI logging is enabled to see pipeline logs
- [ ] Pipeline has been reloaded after changes

## Testing Workflow

1. **Test with single collection first**
   - Set `DEFAULT_COLLECTION` to just `api_docs`
   - Make a query, verify results appear
   - Check logs to confirm collection is queried

2. **Test with second collection**
   - Set `DEFAULT_COLLECTION` to just `personal_documents`
   - Make a query, verify results appear
   - Check logs to confirm collection is queried

3. **Test with both collections**
   - Set `DEFAULT_COLLECTION` to `api_docs,personal_documents`
   - Make a query that should match documents in BOTH collections
   - Check logs for:
     - Both collections being queried
     - Both returning results
     - Final results including both collections

4. **Verify citations in context**
   - Look for the context building logs
   - Check that `collection` field appears in the log
   - Ask LLM to show its sources

## Still Having Issues?

If you've gone through all the above steps and it's still not working:

1. **Share the logs**: Copy the full `[RAG Pipeline]` log output when making a query
2. **Share RAG API response**: Show the actual JSON response from your RAG API
3. **Share configuration**: Show your Valve settings
4. **Test the test script**: Run `python3 test_multi_collection.py` and share output

## Enable Debug Logging

To see even more detail, you may need to enable DEBUG level logging in OpenWebUI's configuration. This will show the augmented message preview and help diagnose what's being sent to the LLM.

## Contact

For issues specific to this pipeline, create an issue in the repository with:
- OpenWebUI version
- Pipeline version (check the file header)
- Full logs from a test query
- RAG API response format
- Valve configuration screenshot

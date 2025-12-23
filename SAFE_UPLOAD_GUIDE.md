# Safe Upload Guide for Stock Data Pipeline

This guide helps you safely upload the stock pipeline to OpenWebUI without crashing the pipeline server.

## What Changed (v2.1 - Stability Update)

I've made the pipeline much more robust to prevent crashes:

### 1. Safer Initialization
- Added try-catch in `__init__()` to prevent initialization crashes
- Safe defaults if configuration fails

### 2. Safer Model Fetching
- Reduced timeout from 5s to 3s to prevent hangs
- Better error handling for network issues
- Always returns a valid model list (falls back to "default")
- Specific handling for Timeout and ConnectionError

### 3. Safer Logging
- No longer uses `logging.basicConfig()` which can conflict with OpenWebUI
- Creates own logger instance without interfering with OpenWebUI logging

## Common Upload Issues & Solutions

### Issue 1: "'Pipeline' object has no attribute 'pipelines'"
**Cause**: OpenWebUI expects manifold pipelines to have a `pipelines` attribute

**Solution**: ✅ FIXED in latest version. The pipeline now includes `self.pipelines = []` in initialization.

### Issue 2: "Pipeline server went offline"
**Cause**: Network timeout when trying to fetch models from Ollama during upload

**Solution**: The pipeline now has 3-second timeouts and better fallbacks. This should be fixed in v2.1.

### Issue 3: "Error loading pipeline"
**Possible causes**:
1. Syntax error in Python code
2. Import error (missing dependencies)
3. Configuration error in Valves

**Solution**:
- Make sure you're uploading the latest version (v2.0.0 or later)
- OpenWebUI has pydantic and requests installed by default
- If you see specific error messages, check the OpenWebUI logs

### Issue 3: Pipeline loads but doesn't work
**Cause**: API keys not configured

**Solution**: After upload, go to Valves and set:
- `FINNHUB_API_KEY`
- `ALPHA_VANTAGE_API_KEY`
- `UPSTREAM_BASE_URL` (your Ollama URL)

## Safe Upload Steps

### Step 1: Prepare the File
```bash
# Make sure you have the latest version
cd /home/user/RAG-Pipelines
git pull origin claude/stock-data-pipeline-cKGIs
```

### Step 2: Upload to OpenWebUI

**Option A: Web Upload (Recommended)**
1. Open OpenWebUI Admin Panel
2. Go to **Admin Panel** → **Pipelines**
3. Click **"+ Add Pipeline"** or **"Upload Pipeline"**
4. Select `stock_data_pipeline.py`
5. Click **Save**

**Option B: File System Copy**
```bash
# If you have direct file access
cp stock_data_pipeline.py /path/to/openwebui/pipelines/
# Then restart OpenWebUI
```

### Step 3: Verify Upload
After upload, you should see:
- Pipeline name: "Stock Data Pipeline"
- Status: Active/Enabled
- No error messages in OpenWebUI logs

**If the pipeline server goes offline:**
1. Check OpenWebUI logs for specific error
2. Try restarting OpenWebUI
3. Re-upload the pipeline
4. Contact support with the error message

### Step 4: Configure API Keys
1. Click on the pipeline in OpenWebUI
2. Go to **Valves** or **Settings**
3. Configure:
   ```
   FINNHUB_API_KEY: your_finnhub_key_here
   ALPHA_VANTAGE_API_KEY: your_alphavantage_key_here
   UPSTREAM_BASE_URL: http://localhost:11434
   ```
4. Save configuration

### Step 5: Test the Pipeline
Start with a simple query:
```
You: What should I invest in?
```

Expected behavior:
- Pipeline detects investment query
- Fetches market data
- LLM asks about risk tolerance, timeline, etc.
- Provides recommendations based on current market

## Troubleshooting After Upload

### Pipeline Not Responding
1. **Check if enabled**: Make sure pipeline is enabled in OpenWebUI
2. **Check logs**: Look for `[Stock Pipeline]` messages in logs
3. **Test simple query**: Try "What's the price of AAPL?"

### No Market Data Fetched
1. **Check API keys**: Verify keys are set in Valves
2. **Check internet**: Pipeline needs internet to reach APIs
3. **Check API limits**: Free tiers have rate limits
4. **Check logs**: Look for "Error fetching..." messages

### LLM Not Using Data
1. **Check UPSTREAM_BASE_URL**: Must point to your Ollama instance
2. **Check Ollama running**: `curl http://localhost:11434/api/tags`
3. **Check model selected**: Make sure a model is selected in chat

## What to Check in Logs

Good log messages (pipeline working):
```
[Stock Pipeline] Initialized: Stock Data Pipeline
[Stock Pipeline] Processing query with model: llama3.2
[Stock Pipeline] Detected investment advice query
[Stock Pipeline] Fetched market movers data
[Stock Pipeline] Fetched sector performance data
[Stock Pipeline] Injected stock data context (1234 chars)
[Stock Pipeline] Calling upstream model: llama3.2
```

Bad log messages (need attention):
```
[Stock Pipeline] Initialization error: ...
[Stock Pipeline] Error in pipe: ...
[Stock Pipeline] Error fetching market movers: ...
```

## Emergency Recovery

If the pipeline crashes OpenWebUI:

1. **Stop OpenWebUI**:
   ```bash
   docker stop openwebui  # if using Docker
   # or
   systemctl stop openwebui  # if using systemd
   ```

2. **Remove the pipeline**:
   ```bash
   # Find and remove the pipeline file
   rm /path/to/openwebui/pipelines/stock_data_pipeline.py
   # or delete via OpenWebUI database
   ```

3. **Restart OpenWebUI**:
   ```bash
   docker start openwebui  # or systemctl start openwebui
   ```

4. **Report the issue**:
   - Save the error logs
   - Note what query you tried
   - Report in GitHub issues

## Version History

- **v2.1 (Stability)**: Added robust error handling, safer timeouts, better logging
- **v2.0 (Features)**: Investment recommendations, market screening, sector analysis
- **v1.0 (Initial)**: Basic stock data fetching

## Getting Help

If you continue to have issues:

1. **Check logs first**: Most issues show up in logs
2. **Try with API keys disabled**: Set `ENABLE_STOCK_DATA=false` to test if it's an API issue
3. **Test with simple query**: "What's the price of AAPL?" is simpler than investment queries
4. **Check OpenWebUI version**: Make sure you're on a recent version
5. **Report issue**: Include logs, OpenWebUI version, and the query you tried

## Success Indicators

You know it's working when:
- ✓ Pipeline appears in OpenWebUI admin panel
- ✓ No errors in logs on startup
- ✓ Query "What should I invest in?" triggers market data fetching
- ✓ LLM asks about your risk tolerance and timeline
- ✓ LLM mentions specific stocks from current market data
- ✓ You see market indices, top gainers, and sector info in responses

## Performance Notes

- First query may be slow (fetching 10+ stocks + sectors)
- Subsequent queries within 5 minutes use cached data
- Market data fetches take 2-5 seconds typically
- Investment queries fetch more data than specific stock queries

## API Rate Limits

**Finnhub Free Tier:**
- 60 calls/minute
- Pipeline makes ~15 calls for investment query (indices + stocks + sectors)

**Alpha Vantage Free Tier:**
- 25 calls/day
- 5 calls/minute
- Pipeline makes 1-3 calls per investment query

**Recommendation**: Start with a few test queries to avoid hitting limits while testing.

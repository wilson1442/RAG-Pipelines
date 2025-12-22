# Stock Pipeline Configuration Example

This document provides example configurations for the Stock Data Pipeline in OpenWebUI.

## Getting API Keys

### Finnhub API Key
1. Go to https://finnhub.io
2. Sign up for a free account
3. Navigate to your dashboard
4. Copy your API key (format: `ch1a2b3c4d5e6f7g8h9i`)

**Free Tier Limits:**
- 60 API calls/minute
- Real-time data for US stocks
- Company profiles, news, and earnings

### Alpha Vantage API Key
1. Go to https://www.alphavantage.co/support/#api-key
2. Enter your email address
3. Click "GET FREE API KEY"
4. Copy your API key (format: `AB12CD34EF56GH78`)

**Free Tier Limits:**
- 25 requests/day
- 5 API calls/minute
- Historical and real-time data

## OpenWebUI Configuration

### Step 1: Install the Pipeline
1. Open OpenWebUI admin panel
2. Go to **Admin Panel** → **Pipelines**
3. Click **Add Pipeline**
4. Upload or paste the `stock_data_pipeline.py` file
5. Click **Save**

### Step 2: Configure Valves

In the OpenWebUI Pipelines settings, configure the following valves:

#### Required Configuration

```
FINNHUB_API_KEY: ch1a2b3c4d5e6f7g8h9i
ALPHA_VANTAGE_API_KEY: AB12CD34EF56GH78
UPSTREAM_BASE_URL: http://192.168.4.10:11434
```

#### Optional Configuration (Recommended Defaults)

```
ENABLE_STOCK_DATA: true
USE_OLLAMA_NATIVE: true
FETCH_NEWS: true
FETCH_EARNINGS: true
FETCH_FINANCIALS: true
FETCH_PRICE_HISTORY: true
NEWS_LIMIT: 5
PRICE_HISTORY_DAYS: 30
STOCK_KEYWORDS: stock,price,shares,ticker,quote,earnings,revenue,financial,trading,market
```

### Step 3: Test the Pipeline

Send a test query to verify the pipeline is working:

**Test Query 1:**
```
What's the current price of Apple stock?
```

**Expected Behavior:**
- Pipeline detects "Apple" → ticker AAPL
- Fetches current quote from Finnhub
- Fetches company overview from Alpha Vantage
- LLM responds with current price and details

**Test Query 2:**
```
Show me Tesla's recent earnings and news
```

**Expected Behavior:**
- Pipeline detects "Tesla" → ticker TSLA
- Fetches earnings data from both APIs
- Fetches recent news from Finnhub
- LLM summarizes earnings and news

## Configuration for Different Use Cases

### Minimal Configuration (Price Only)
For users who only want stock prices without news or earnings:

```
ENABLE_STOCK_DATA: true
FETCH_NEWS: false
FETCH_EARNINGS: false
FETCH_FINANCIALS: true
FETCH_PRICE_HISTORY: true
NEWS_LIMIT: 0
```

### News-Focused Configuration
For users interested primarily in stock news:

```
ENABLE_STOCK_DATA: true
FETCH_NEWS: true
FETCH_EARNINGS: false
FETCH_FINANCIALS: false
FETCH_PRICE_HISTORY: false
NEWS_LIMIT: 10
```

### Financial Analysis Configuration
For detailed financial analysis:

```
ENABLE_STOCK_DATA: true
FETCH_NEWS: true
FETCH_EARNINGS: true
FETCH_FINANCIALS: true
FETCH_PRICE_HISTORY: true
NEWS_LIMIT: 5
PRICE_HISTORY_DAYS: 90
```

### Conservative API Usage (Free Tier)
To minimize API calls and stay within free tier limits:

```
ENABLE_STOCK_DATA: true
FETCH_NEWS: true
FETCH_EARNINGS: true
FETCH_FINANCIALS: true
FETCH_PRICE_HISTORY: false
NEWS_LIMIT: 3
PRICE_HISTORY_DAYS: 7
```

## Environment Variables (Alternative Setup)

If your OpenWebUI deployment supports environment variables:

```bash
# .env file
STOCK_FINNHUB_API_KEY=ch1a2b3c4d5e6f7g8h9i
STOCK_ALPHA_VANTAGE_API_KEY=AB12CD34EF56GH78
STOCK_UPSTREAM_BASE_URL=http://192.168.4.10:11434
```

## Docker Compose Configuration

If running OpenWebUI with Docker:

```yaml
services:
  openwebui:
    image: ghcr.io/open-webui/open-webui:main
    environment:
      - STOCK_FINNHUB_API_KEY=ch1a2b3c4d5e6f7g8h9i
      - STOCK_ALPHA_VANTAGE_API_KEY=AB12CD34EF56GH78
      - STOCK_UPSTREAM_BASE_URL=http://ollama:11434
    volumes:
      - ./stock_data_pipeline.py:/app/backend/data/pipelines/stock_data_pipeline.py
```

## Troubleshooting Configuration

### Issue: Pipeline not fetching data

**Check:**
1. API keys are correctly entered (no extra spaces)
2. `ENABLE_STOCK_DATA` is set to `true`
3. Query contains stock-related keywords
4. Internet connectivity is working

**Solution:**
```bash
# View pipeline logs in OpenWebUI
# Check for error messages like:
# "Error fetching Finnhub data: 401 Unauthorized"
# This indicates invalid API key
```

### Issue: Rate limit exceeded

**Symptoms:**
- Error: "API rate limit exceeded"
- Error code: 429

**Solution:**
- Reduce `NEWS_LIMIT` to 3
- Set `FETCH_PRICE_HISTORY` to false
- Wait a few minutes before trying again
- Consider upgrading to paid API tier

### Issue: No data for certain stocks

**Possible Causes:**
1. Ticker symbol doesn't exist
2. Stock is not traded on US exchanges (Finnhub free tier limitation)
3. API doesn't have data for that stock

**Solution:**
- Verify ticker symbol on finance.yahoo.com
- Try with a major stock like AAPL or MSFT first
- Check API documentation for coverage

## Security Best Practices

1. **Never commit API keys to version control**
   ```bash
   # Add to .gitignore
   .env
   *_api_keys.txt
   ```

2. **Use environment variables or secrets management**
   - OpenWebUI Valves (recommended)
   - Docker secrets
   - Kubernetes secrets

3. **Rotate API keys periodically**
   - Every 90 days recommended
   - Immediately if exposed

4. **Monitor API usage**
   - Check Finnhub dashboard
   - Check Alpha Vantage usage stats
   - Set up alerts for unusual activity

## Example Queries by Configuration

### With News Enabled
```
"What's the latest news about Microsoft?"
"Tell me about Amazon's recent announcements"
"Show me Tesla news from this week"
```

### With Earnings Enabled
```
"What were Apple's last earnings?"
"Show me Nvidia's quarterly results"
"Compare Google and Meta earnings"
```

### With Financials Enabled
```
"What is Tesla's P/E ratio?"
"Show me Amazon's revenue"
"What's the market cap of Apple?"
```

### With Price History Enabled
```
"How has AAPL performed this month?"
"Show me Tesla's price trend"
"What's the 30-day price chart for Microsoft?"
```

## Advanced Configuration

### Custom Stock Keywords

Add industry-specific keywords:

```
STOCK_KEYWORDS: stock,price,shares,ticker,quote,earnings,revenue,financial,trading,market,equity,portfolio,investment,dividend,volatility
```

### Custom Company Mapping

To add more company name mappings, edit the `_extract_tickers` method in `stock_data_pipeline.py`:

```python
company_map = {
    'apple': 'AAPL',
    'microsoft': 'MSFT',
    # Add your own:
    'berkshire': 'BRK.B',
    'visa': 'V',
    'walmart': 'WMT',
}
```

## Integration with Other Pipelines

The Stock Data Pipeline can run alongside other pipelines:

```
Enabled Pipelines:
1. Stock Data Pipeline (for stock queries)
2. RAG Manifold Pipeline (for document queries)
3. Custom Pipeline (for other tasks)
```

OpenWebUI will route queries to the appropriate pipeline based on content.

## Support

For configuration help:
1. Check pipeline logs in OpenWebUI
2. Review the STOCK_PIPELINE_README.md
3. Test with simple queries first
4. Verify API keys are valid on provider websites

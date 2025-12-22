# Stock Data Pipeline for OpenWebUI

A comprehensive stock data pipeline that integrates with **Finnhub** and **Alpha Vantage** APIs to fetch real-time stock prices, news, earnings, and financial data.

## Features

- **Automatic Stock Detection**: Detects when users ask about stocks and automatically fetches relevant data
- **Multi-API Integration**: Combines data from both Finnhub and Alpha Vantage for comprehensive coverage
- **Real-time Stock Quotes**: Current prices, changes, highs, lows
- **Company Information**: Profile, industry, market cap, description
- **Recent News**: Latest news articles with summaries
- **Earnings Data**: Historical earnings, EPS, estimates, and surprises
- **Financial Metrics**: Revenue, P/E ratio, dividends, beta, and more
- **Price History**: Daily price data for trend analysis
- **Context Injection**: Automatically augments LLM prompts with fetched data

## Data Sources

### Finnhub API
- Real-time stock quotes
- Company profiles
- Recent news (last 7 days)
- Earnings history
- Key financial metrics

### Alpha Vantage API
- Company overview with detailed financials
- Daily price history
- Quarterly and annual earnings
- Revenue and profit data

## Installation

1. **Get API Keys**:
   - Finnhub: https://finnhub.io (free tier available)
   - Alpha Vantage: https://www.alphavantage.co (free tier available)

2. **Install the Pipeline**:
   ```bash
   # Copy the pipeline file to your OpenWebUI pipelines directory
   cp stock_data_pipeline.py /path/to/openwebui/pipelines/
   ```

3. **Configure in OpenWebUI**:
   - Go to OpenWebUI Admin Panel
   - Navigate to Pipelines
   - Find "Stock Data Pipeline"
   - Configure the Valves (see Configuration section below)

## Configuration

### Required Settings

| Setting | Description | Example |
|---------|-------------|---------|
| `FINNHUB_API_KEY` | Your Finnhub API key | `ch1a2b3c4d5e6f7g8h9i` |
| `ALPHA_VANTAGE_API_KEY` | Your Alpha Vantage API key | `AB12CD34EF56GH78` |
| `UPSTREAM_BASE_URL` | Ollama/LLM base URL | `http://192.168.4.10:11434` |

### Optional Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `ENABLE_STOCK_DATA` | `true` | Enable/disable stock data fetching |
| `FETCH_NEWS` | `true` | Fetch recent news articles |
| `FETCH_EARNINGS` | `true` | Fetch earnings data |
| `FETCH_FINANCIALS` | `true` | Fetch financial statements |
| `FETCH_PRICE_HISTORY` | `true` | Fetch price history |
| `NEWS_LIMIT` | `5` | Number of news articles per stock |
| `PRICE_HISTORY_DAYS` | `30` | Days of price history to fetch |
| `USE_OLLAMA_NATIVE` | `true` | Use Ollama native API |

### Stock Detection Keywords

The pipeline triggers when queries contain these keywords (customizable):
```
stock, price, shares, ticker, quote, earnings, revenue, financial, trading, market
```

## Usage Examples

### Example 1: Current Stock Price
**User Query**: "What's the current price of AAPL?"

**Pipeline Actions**:
1. Detects ticker: AAPL
2. Fetches real-time quote from Finnhub
3. Fetches overview from Alpha Vantage
4. Injects data into LLM context
5. LLM responds with current price and relevant details

### Example 2: Multiple Stocks
**User Query**: "Compare the stock prices of TSLA and NVDA"

**Pipeline Actions**:
1. Detects tickers: TSLA, NVDA
2. Fetches data for both stocks
3. Provides comprehensive comparison data to LLM

### Example 3: News and Earnings
**User Query**: "Tell me about Microsoft's recent earnings and news"

**Pipeline Actions**:
1. Detects company name → ticker: MSFT
2. Fetches recent news (last 7 days)
3. Fetches earnings history
4. Fetches financial metrics
5. LLM summarizes earnings results and news

### Example 4: Financial Analysis
**User Query**: "What is Amazon's revenue and P/E ratio?"

**Pipeline Actions**:
1. Detects company name → ticker: AMZN
2. Fetches company overview with revenue data
3. Fetches financial metrics including P/E ratio
4. LLM provides specific financial data

## Ticker Detection

The pipeline automatically detects stock tickers in multiple formats:

1. **Dollar Sign Format**: `$AAPL`, `$TSLA`, `$GOOGL`
2. **Uppercase Words**: `AAPL`, `MSFT`, `NVDA` (2-5 characters)
3. **Company Names**: Automatically maps common companies to tickers:
   - Apple → AAPL
   - Microsoft → MSFT
   - Google/Alphabet → GOOGL
   - Amazon → AMZN
   - Tesla → TSLA
   - Meta/Facebook → META
   - Nvidia → NVDA
   - Netflix → NFLX
   - AMD → AMD
   - Intel → INTC

## Data Fetched Per Stock

### From Finnhub:
- **Quote**: Current price, change, high, low, open, previous close
- **Profile**: Company name, industry, market cap, exchange, country, website
- **News**: Last 5 articles from the past 7 days with headlines, summaries, timestamps
- **Earnings**: Historical EPS data (actual, estimate, surprise)
- **Financials**: 52-week high/low, P/E ratio, beta, dividend yield

### From Alpha Vantage:
- **Overview**: Company description, sector, revenue (TTM), gross profit, EPS, dividends
- **Price History**: Daily OHLCV data for the last 30 days
- **Earnings**: Quarterly and annual earnings with estimates and surprises

## Context Injection

The pipeline builds a comprehensive context that looks like this:

```
============================================================
STOCK DATA FOR AAPL
============================================================

CURRENT PRICE:
  Current Price: $178.50
  Change: $2.30 (1.31%)
  High: $179.20
  Low: $176.80
  Open: $177.00
  Previous Close: $176.20

COMPANY INFO:
  Name: Apple Inc.
  Industry: Technology
  Market Cap: $2,800,000M
  Exchange: NASDAQ
  Country: US

RECENT NEWS:
  [1] Apple Announces New Product Line
      Date: 2025-12-20 10:30
      Summary: Apple unveiled its latest...
      Source: Reuters

...
```

This context is automatically injected into the LLM prompt, allowing it to provide accurate, data-driven responses.

## API Rate Limits

### Finnhub Free Tier:
- 60 API calls/minute
- 30 API calls/second

### Alpha Vantage Free Tier:
- 25 requests/day
- 5 API calls/minute

**Recommendation**: The pipeline is optimized to minimize API calls. For heavy usage, consider upgrading to paid tiers or implementing caching.

## Troubleshooting

### No Stock Data Returned
1. **Check API Keys**: Ensure both API keys are correctly configured in Valves
2. **Check Ticker**: Verify the ticker symbol is valid (use official stock exchange symbols)
3. **Check Logs**: Look for error messages in the pipeline logs
4. **API Limits**: Check if you've exceeded API rate limits

### Pipeline Not Triggering
1. **Check Keywords**: Ensure your query contains stock-related keywords
2. **Check Enable Setting**: Verify `ENABLE_STOCK_DATA` is set to `true`
3. **Check Ticker Format**: Use clear ticker symbols like $AAPL or mention company names

### Incomplete Data
1. **API Availability**: Some data may not be available for all stocks
2. **Market Hours**: Real-time data may be delayed outside market hours
3. **API Tier**: Free tiers may have limited data access

## Example Queries

Here are some example queries that will trigger the stock pipeline:

- "What's the current stock price of Apple?"
- "Show me Tesla's recent news and earnings"
- "Compare NVDA and AMD stock performance"
- "What is Microsoft's revenue and market cap?"
- "Tell me about Amazon's latest earnings call"
- "How has $TSLA stock performed this month?"
- "What are the financial metrics for Google?"

## Development

### Testing the Pipeline

```python
# Test ticker extraction
pipeline = Pipeline()
tickers = pipeline._extract_tickers("What's the price of AAPL and TSLA?")
print(tickers)  # ['AAPL', 'TSLA']

# Test stock query detection
is_stock = pipeline._is_stock_query("What's the stock price of Apple?")
print(is_stock)  # True
```

### Logging

The pipeline uses Python's logging module with INFO level by default. Check your OpenWebUI logs for detailed pipeline execution information:

```
[Stock Pipeline] Processing query with model: llama3.2
[Stock Pipeline] Found tickers: ['AAPL']
[Stock Pipeline] Fetching data for AAPL
[Stock Pipeline] Fetched Finnhub quote for AAPL
[Stock Pipeline] Fetched Alpha Vantage overview for AAPL
[Stock Pipeline] Injected stock data context (5234 chars)
```

## Security Notes

- **API Keys**: Never commit API keys to version control
- **Rate Limiting**: The pipeline respects API rate limits but doesn't implement client-side throttling
- **Data Privacy**: Stock data is fetched in real-time and not stored permanently

## License

This pipeline is part of the RAG-Pipelines project. See main project LICENSE for details.

## Support

For issues, feature requests, or questions:
1. Check the logs for error messages
2. Verify API keys and configuration
3. Open an issue in the project repository

## Version

- **Version**: 1.0.0
- **Last Updated**: 2025-12-22
- **Compatible with**: OpenWebUI v0.3.x+

# Stock Data Pipeline for OpenWebUI

A comprehensive and intelligent stock data pipeline that integrates with **Finnhub** and **Alpha Vantage** APIs to provide real-time market data, investment recommendations, and automated market analysis.

## Features

### Core Stock Features
- **Automatic Stock Detection**: Detects when users ask about stocks and automatically fetches relevant data
- **Multi-API Integration**: Combines data from both Finnhub and Alpha Vantage for comprehensive coverage
- **Real-time Stock Quotes**: Current prices, changes, highs, lows
- **Company Information**: Profile, industry, market cap, description
- **Recent News**: Latest news articles with summaries
- **Earnings Data**: Historical earnings, EPS, estimates, and surprises
- **Financial Metrics**: Revenue, P/E ratio, dividends, beta, and more
- **Price History**: Daily price data for trend analysis

### NEW: Investment & Market Intelligence (v2.0)
- **Investment Recommendations**: Automatically provides personalized stock recommendations
- **Market Screening**: Shows top gainers, losers, and market movers
- **Sector Analysis**: Identifies hot/cold sectors and sector leaders
- **Market Overview**: Real-time market indices and trends
- **Intelligent Questionnaire**: Asks about risk tolerance, timeline, and goals
- **Automated Data Fetching**: No need to specify stocks - the pipeline fetches everything needed

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
| `ENABLE_MARKET_SCREENING` | `true` | Enable market screening (gainers/losers) |
| `ENABLE_INVESTMENT_ADVICE` | `true` | Enable investment recommendations |
| `FETCH_NEWS` | `true` | Fetch recent news articles |
| `FETCH_EARNINGS` | `true` | Fetch earnings data |
| `FETCH_FINANCIALS` | `true` | Fetch financial statements |
| `FETCH_PRICE_HISTORY` | `true` | Fetch price history |
| `FETCH_SECTOR_PERFORMANCE` | `true` | Fetch sector performance data |
| `NEWS_LIMIT` | `5` | Number of news articles per stock |
| `PRICE_HISTORY_DAYS` | `30` | Days of price history to fetch |
| `TOP_MOVERS_LIMIT` | `10` | Number of top gainers/losers |
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

### Example 5: Investment Advice (NEW v2.0)
**User Query**: "What should I invest in?"

**Pipeline Actions**:
1. Detects investment advice query
2. Automatically fetches market movers (top gainers/losers)
3. Fetches sector performance (Technology, Healthcare, Energy, etc.)
4. Fetches market indices (S&P 500, NASDAQ, Dow Jones)
5. LLM asks clarifying questions:
   - What's your risk tolerance?
   - What's your investment timeline?
   - How much are you looking to invest?
6. LLM provides personalized recommendations based on current market data

**Example Response**:
```
Based on current market data, I'd like to understand your investment profile better:

1. Risk Tolerance: Are you conservative, moderate, or aggressive?
2. Investment Timeline: Short-term (< 1 year), medium-term (1-5 years), or long-term (5+ years)?
3. Investment Amount: What's your budget?

Current Market Overview:
- Technology sector is up 2.3% today, leading the market
- Top gainers include NVDA (+5.2%), AMD (+3.8%)
- Healthcare sector is showing stability (+0.5%)

Based on your profile, I can recommend specific stocks and diversification strategies.
```

### Example 6: Market Screening (NEW v2.0)
**User Query**: "What are the trending stocks today?"

**Pipeline Actions**:
1. Detects market screening query
2. Fetches top gainers and losers
3. Fetches market indices performance
4. Fetches sector performance
5. LLM provides comprehensive market overview

**Example Response**:
```
Here's today's market overview:

Market Indices:
- S&P 500: 4,567.23 (+0.8%)
- NASDAQ: 14,234.56 (+1.2%)
- Dow Jones: 35,678.90 (+0.5%)

Top Gainers:
1. NVDA: $485.23 (+5.2%)
2. AMD: $142.67 (+3.8%)
3. TSLA: $245.89 (+3.1%)

Top Losers:
1. XYZ: $45.12 (-4.2%)
2. ABC: $78.34 (-2.8%)

Hot Sectors:
- Technology: +2.3%
- Communications: +1.5%
- Healthcare: +0.5%
```

### Example 7: Sector Analysis (NEW v2.0)
**User Query**: "Which sectors are hot right now?"

**Pipeline Actions**:
1. Detects sector query
2. Fetches sector ETF performance
3. Identifies top and bottom performing sectors
4. LLM provides sector insights and recommendations

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

### Specific Stock Queries
- "What's the current stock price of Apple?"
- "Show me Tesla's recent news and earnings"
- "Compare NVDA and AMD stock performance"
- "What is Microsoft's revenue and market cap?"
- "Tell me about Amazon's latest earnings call"
- "How has $TSLA stock performed this month?"
- "What are the financial metrics for Google?"

### Investment Advice Queries (NEW v2.0)
- "What should I invest in?"
- "What are the best stocks to buy right now?"
- "Where should I invest my money?"
- "Give me stock recommendations"
- "What are good investment opportunities?"
- "Which stocks should I buy for long-term growth?"
- "What are the top performing stocks?"

### Market Screening Queries (NEW v2.0)
- "What are the trending stocks today?"
- "Show me market overview"
- "What are the top gainers?"
- "Which stocks are moving today?"
- "What's hot in the market?"
- "Market trends today"
- "Show me market movers"

### Sector Analysis Queries (NEW v2.0)
- "Which sectors are performing well?"
- "What are the hot sectors right now?"
- "Sector performance today"
- "Show me sector leaders"
- "Which industry is trending?"

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

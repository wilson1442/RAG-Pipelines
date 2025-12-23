"""
Stock Data Pipeline for OpenWebUI
Integrates with Finnhub and Alpha Vantage APIs to fetch comprehensive stock data
Version: 2.0.0 - Enhanced with market screening and investment recommendations
"""

from typing import List, Dict, Any, Union, Generator, Optional
from pydantic import BaseModel, Field
import requests
import logging
import json
import re
from datetime import datetime, timedelta

# Configure logging - safe for OpenWebUI
try:
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('[%(name)s] %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
except Exception as e:
    # Fallback to basic logger if configuration fails
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)


class Pipeline:
    """
    Stock Data Pipeline for OpenWebUI

    Fetches comprehensive stock data from Finnhub and Alpha Vantage when users
    ask about stock prices, news, earnings, or financial data.
    """

    class Valves(BaseModel):
        """Configuration for Stock Data Pipeline"""

        # API Keys
        FINNHUB_API_KEY: str = Field(
            default="",
            description="Finnhub API Key (get from https://finnhub.io)"
        )
        ALPHA_VANTAGE_API_KEY: str = Field(
            default="",
            description="Alpha Vantage API Key (get from https://www.alphavantage.co)"
        )

        # Pipeline Settings
        ENABLE_STOCK_DATA: bool = Field(
            default=True,
            description="Enable automatic stock data fetching"
        )
        FETCH_NEWS: bool = Field(
            default=True,
            description="Fetch recent news for stocks"
        )
        FETCH_EARNINGS: bool = Field(
            default=True,
            description="Fetch earnings data"
        )
        FETCH_FINANCIALS: bool = Field(
            default=True,
            description="Fetch financial statements (revenue, etc.)"
        )
        FETCH_PRICE_HISTORY: bool = Field(
            default=True,
            description="Fetch recent price history"
        )

        # Data Limits
        NEWS_LIMIT: int = Field(
            default=5,
            description="Number of recent news articles to fetch per stock"
        )
        PRICE_HISTORY_DAYS: int = Field(
            default=30,
            description="Number of days of price history to fetch"
        )

        # Stock Detection Keywords
        STOCK_KEYWORDS: str = Field(
            default="stock,price,shares,ticker,quote,earnings,revenue,financial,trading,market",
            description="Comma-separated keywords to trigger stock data fetching"
        )

        # Market Screening & Investment Features
        ENABLE_MARKET_SCREENING: bool = Field(
            default=True,
            description="Enable market screening (trending stocks, gainers, losers)"
        )
        ENABLE_INVESTMENT_ADVICE: bool = Field(
            default=True,
            description="Enable investment recommendation features"
        )
        FETCH_SECTOR_PERFORMANCE: bool = Field(
            default=True,
            description="Fetch sector performance data"
        )
        TOP_MOVERS_LIMIT: int = Field(
            default=10,
            description="Number of top gainers/losers to fetch"
        )

    def __init__(self):
        """Initialize the Stock Data Pipeline"""
        try:
            self.type = "filter"  # Filter type - works with any selected model
            self.id = "stock_data_pipeline"
            self.name = "Stock Data Pipeline"
            self.valves = self.Valves()

            # Cache for API responses (simple in-memory cache)
            self._cache = {}
            self._cache_ttl = 300  # 5 minutes in seconds

            logger.info(f"[Stock Pipeline] Initialized: {self.name}")
        except Exception as e:
            logger.error(f"[Stock Pipeline] Initialization error: {e}")
            # Set safe defaults
            self.type = "filter"
            self.id = "stock_data_pipeline"
            self.name = "Stock Data Pipeline"
            self.valves = self.Valves()
            self._cache = {}
            self._cache_ttl = 300

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> dict:
        """
        Main pipeline execution (Filter type)

        1. Check if query is about stocks/investing
        2. Determine query type (investment advice, market screening, specific stocks)
        3. Fetch relevant data automatically
        4. Inject data into context
        5. Return modified body for OpenWebUI to send to selected model
        """
        logger.info(f"[Stock Pipeline] Processing query with model: {model_id}")

        try:
            # Check if stock data fetching is enabled
            if not self.valves.ENABLE_STOCK_DATA:
                logger.info("[Stock Pipeline] Stock data fetching disabled, passing through")
                return body

            # Extract the last user message
            last_message = messages[-1] if messages else {}
            user_query = last_message.get("content", "") if isinstance(last_message.get("content"), str) else user_message

            # Detect query type and fetch appropriate data
            context = None

            # 1. Check for investment advice queries
            if self.valves.ENABLE_INVESTMENT_ADVICE and self._is_investment_advice_query(user_query):
                logger.info("[Stock Pipeline] Detected investment advice query")
                context = self._handle_investment_advice(user_query)

            # 2. Check for market screening queries (trending, hot stocks, sectors)
            elif self.valves.ENABLE_MARKET_SCREENING and self._is_market_screening_query(user_query):
                logger.info("[Stock Pipeline] Detected market screening query")
                context = self._handle_market_screening(user_query)

            # 3. Check for specific stock queries
            elif self._is_stock_query(user_query):
                logger.info("[Stock Pipeline] Detected specific stock query")
                tickers = self._extract_tickers(user_query)

                if tickers:
                    logger.info(f"[Stock Pipeline] Found tickers: {tickers}")
                    # Fetch stock data for all tickers
                    stock_data = self._fetch_all_stock_data(tickers)
                    if stock_data:
                        context = self._build_stock_context(stock_data)
                else:
                    logger.info("[Stock Pipeline] No specific tickers found, passing through")

            # If no context was generated, pass through unchanged
            if not context:
                logger.info("[Stock Pipeline] No stock/market context generated, passing through")
                return body

            # Inject context into messages
            augmented_messages = self._inject_context(messages, user_query, context)

            # Return modified body with augmented messages
            body["messages"] = augmented_messages
            logger.info(f"[Stock Pipeline] Returning augmented messages to OpenWebUI")
            return body

        except Exception as e:
            logger.error(f"[Stock Pipeline] Error in pipe: {e}", exc_info=True)
            # On error, pass through unchanged
            return body

    def _is_stock_query(self, query: str) -> bool:
        """Check if query is related to stocks"""
        query_lower = query.lower()
        keywords = [k.strip() for k in self.valves.STOCK_KEYWORDS.split(",")]

        # Check for keywords
        for keyword in keywords:
            if keyword in query_lower:
                return True

        # Check for ticker patterns (e.g., $AAPL, TSLA)
        if re.search(r'\$[A-Z]{1,5}\b|\b[A-Z]{1,5}\b', query):
            return True

        return False

    def _extract_tickers(self, query: str) -> List[str]:
        """Extract stock ticker symbols from query"""
        tickers = set()

        # Pattern 1: $TICKER format
        dollar_tickers = re.findall(r'\$([A-Z]{1,5})\b', query)
        tickers.update(dollar_tickers)

        # Pattern 2: Standalone uppercase words (2-5 chars) - common tickers
        # Be more conservative to avoid false positives
        words = query.split()
        for word in words:
            # Remove punctuation
            clean_word = re.sub(r'[^\w]', '', word)
            # Check if it's all uppercase and 2-5 characters
            if clean_word.isupper() and 2 <= len(clean_word) <= 5:
                # Exclude common words that might be confused as tickers
                excluded = {'I', 'A', 'CEO', 'CFO', 'CTO', 'USA', 'US', 'UK', 'API', 'AI', 'ML'}
                if clean_word not in excluded:
                    tickers.add(clean_word)

        # Pattern 3: Common company names to ticker mapping
        company_map = {
            'apple': 'AAPL',
            'microsoft': 'MSFT',
            'google': 'GOOGL',
            'alphabet': 'GOOGL',
            'amazon': 'AMZN',
            'tesla': 'TSLA',
            'meta': 'META',
            'facebook': 'META',
            'nvidia': 'NVDA',
            'netflix': 'NFLX',
            'amd': 'AMD',
            'intel': 'INTC',
        }

        query_lower = query.lower()
        for company, ticker in company_map.items():
            if company in query_lower:
                tickers.add(ticker)

        return list(tickers)

    def _is_investment_advice_query(self, query: str) -> bool:
        """Check if query is asking for investment advice or recommendations"""
        query_lower = query.lower()

        investment_patterns = [
            'what should i invest',
            'where should i invest',
            'what to invest',
            'investment recommendation',
            'best stocks to buy',
            'stocks to buy',
            'good stocks',
            'stock recommendations',
            'invest in',
            'portfolio recommendation',
            'what stocks should',
            'which stocks',
            'hot stocks',
            'best performing',
            'top stocks',
            'stocks to watch',
            'investment opportunities',
            'profitable stocks',
            'growth stocks',
            'value stocks',
        ]

        return any(pattern in query_lower for pattern in investment_patterns)

    def _is_market_screening_query(self, query: str) -> bool:
        """Check if query is asking for market screening/overview"""
        query_lower = query.lower()

        screening_patterns = [
            'market overview',
            'market trends',
            'trending stocks',
            'top gainers',
            'top losers',
            'most active',
            'market movers',
            'sector performance',
            'sector leaders',
            'hot sectors',
            'market summary',
            'market status',
            'what\'s hot',
            'what is hot',
            'trending in the market',
            'market analysis',
        ]

        return any(pattern in query_lower for pattern in screening_patterns)

    def _handle_investment_advice(self, query: str) -> str:
        """Handle investment advice queries by fetching market data and trending stocks"""
        logger.info("[Stock Pipeline] Handling investment advice query")

        context_parts = []
        context_parts.append("="*60)
        context_parts.append("INVESTMENT MARKET ANALYSIS")
        context_parts.append("="*60)
        context_parts.append("")

        # Fetch market movers (gainers/losers)
        market_movers = self._fetch_market_movers()
        if market_movers:
            context_parts.append(market_movers)

        # Fetch sector performance
        if self.valves.FETCH_SECTOR_PERFORMANCE:
            sector_data = self._fetch_sector_performance()
            if sector_data:
                context_parts.append(sector_data)

        # Add investment guidance instructions for LLM
        context_parts.append("")
        context_parts.append("INVESTMENT ADVICE INSTRUCTIONS:")
        context_parts.append("- Use the market data above to provide informed recommendations")
        context_parts.append("- Ask clarifying questions about:")
        context_parts.append("  * Risk tolerance (conservative, moderate, aggressive)")
        context_parts.append("  * Investment timeline (short-term, medium-term, long-term)")
        context_parts.append("  * Investment amount and goals")
        context_parts.append("  * Sector preferences or restrictions")
        context_parts.append("- Provide specific stock recommendations based on current market trends")
        context_parts.append("- Include rationale for each recommendation")
        context_parts.append("- Mention risks and diversification strategies")
        context_parts.append("")

        return "\n".join(context_parts)

    def _handle_market_screening(self, query: str) -> str:
        """Handle market screening queries"""
        logger.info("[Stock Pipeline] Handling market screening query")

        context_parts = []
        context_parts.append("="*60)
        context_parts.append("MARKET SCREENING & ANALYSIS")
        context_parts.append("="*60)
        context_parts.append("")

        # Fetch market movers
        market_movers = self._fetch_market_movers()
        if market_movers:
            context_parts.append(market_movers)

        # Fetch sector performance
        if self.valves.FETCH_SECTOR_PERFORMANCE:
            sector_data = self._fetch_sector_performance()
            if sector_data:
                context_parts.append(sector_data)

        return "\n".join(context_parts)

    def _fetch_market_movers(self) -> str:
        """Fetch top gainers, losers, and most active stocks from Finnhub"""
        if not self.valves.FINNHUB_API_KEY:
            return ""

        context_parts = []

        try:
            base_url = "https://finnhub.io/api/v1"
            headers = {"X-Finnhub-Token": self.valves.FINNHUB_API_KEY}

            # Fetch US market movers
            # Note: Finnhub doesn't have a direct "top gainers" endpoint for free tier
            # We'll fetch quotes for major indices and popular stocks
            # For a real implementation, you might use a premium API or screener

            # Get market indices first
            indices = {
                '^GSPC': 'S&P 500',
                '^DJI': 'Dow Jones',
                '^IXIC': 'NASDAQ',
            }

            context_parts.append("MARKET INDICES:")
            for symbol, name in indices.items():
                try:
                    quote_url = f"{base_url}/quote?symbol={symbol}"
                    response = requests.get(quote_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        context_parts.append(f"  {name}: ${data.get('c', 'N/A')} ({data.get('dp', 'N/A'):+.2f}%)")
                except:
                    pass

            context_parts.append("")

            # Fetch trending stocks (popular tech stocks as example)
            # In a real implementation, use a screener API or Finnhub's "market news" to find trending
            popular_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'AMD', 'NFLX', 'INTC']

            trending_data = []
            for ticker in popular_tickers:
                try:
                    quote_url = f"{base_url}/quote?symbol={ticker}"
                    response = requests.get(quote_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        trending_data.append({
                            'ticker': ticker,
                            'price': data.get('c', 0),
                            'change': data.get('d', 0),
                            'change_pct': data.get('dp', 0)
                        })
                except:
                    pass

            # Sort by percent change to find gainers and losers
            trending_data.sort(key=lambda x: x['change_pct'], reverse=True)

            if trending_data:
                context_parts.append(f"TOP GAINERS (from major stocks):")
                for stock in trending_data[:5]:
                    context_parts.append(f"  {stock['ticker']}: ${stock['price']:.2f} ({stock['change_pct']:+.2f}%)")

                context_parts.append("")
                context_parts.append(f"TOP LOSERS (from major stocks):")
                for stock in trending_data[-5:]:
                    context_parts.append(f"  {stock['ticker']}: ${stock['price']:.2f} ({stock['change_pct']:+.2f}%)")

                context_parts.append("")

            logger.info(f"[Stock Pipeline] Fetched market movers data")

        except Exception as e:
            logger.error(f"[Stock Pipeline] Error fetching market movers: {e}")

        return "\n".join(context_parts)

    def _fetch_sector_performance(self) -> str:
        """Fetch sector performance data"""
        if not self.valves.FINNHUB_API_KEY:
            return ""

        context_parts = []
        context_parts.append("SECTOR PERFORMANCE:")

        try:
            # Map sector ETFs to sectors
            sector_etfs = {
                'XLK': 'Technology',
                'XLF': 'Financials',
                'XLV': 'Healthcare',
                'XLE': 'Energy',
                'XLI': 'Industrials',
                'XLC': 'Communications',
                'XLY': 'Consumer Discretionary',
                'XLP': 'Consumer Staples',
                'XLRE': 'Real Estate',
                'XLB': 'Materials',
                'XLU': 'Utilities',
            }

            base_url = "https://finnhub.io/api/v1"
            headers = {"X-Finnhub-Token": self.valves.FINNHUB_API_KEY}

            sector_performance = []
            for etf, sector in sector_etfs.items():
                try:
                    quote_url = f"{base_url}/quote?symbol={etf}"
                    response = requests.get(quote_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        sector_performance.append({
                            'sector': sector,
                            'change_pct': data.get('dp', 0),
                            'price': data.get('c', 0)
                        })
                except:
                    pass

            # Sort by performance
            sector_performance.sort(key=lambda x: x['change_pct'], reverse=True)

            if sector_performance:
                context_parts.append("")
                context_parts.append("  TOP PERFORMING SECTORS:")
                for sector in sector_performance[:3]:
                    context_parts.append(f"    {sector['sector']}: {sector['change_pct']:+.2f}%")

                context_parts.append("")
                context_parts.append("  WEAKEST PERFORMING SECTORS:")
                for sector in sector_performance[-3:]:
                    context_parts.append(f"    {sector['sector']}: {sector['change_pct']:+.2f}%")

                context_parts.append("")

            logger.info(f"[Stock Pipeline] Fetched sector performance data")

        except Exception as e:
            logger.error(f"[Stock Pipeline] Error fetching sector performance: {e}")

        return "\n".join(context_parts)

    def _fetch_all_stock_data(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch comprehensive stock data for all tickers"""
        stock_data = {}

        for ticker in tickers:
            logger.info(f"[Stock Pipeline] Fetching data for {ticker}")
            ticker_data = {}

            # Fetch from Finnhub
            if self.valves.FINNHUB_API_KEY:
                ticker_data['finnhub'] = self._fetch_finnhub_data(ticker)

            # Fetch from Alpha Vantage
            if self.valves.ALPHA_VANTAGE_API_KEY:
                ticker_data['alpha_vantage'] = self._fetch_alpha_vantage_data(ticker)

            if ticker_data:
                stock_data[ticker] = ticker_data

        return stock_data

    def _fetch_finnhub_data(self, ticker: str) -> Dict[str, Any]:
        """Fetch data from Finnhub API"""
        data = {}
        base_url = "https://finnhub.io/api/v1"
        headers = {"X-Finnhub-Token": self.valves.FINNHUB_API_KEY}

        try:
            # 1. Quote (current price)
            quote_url = f"{base_url}/quote?symbol={ticker}"
            response = requests.get(quote_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data['quote'] = response.json()
                logger.info(f"[Stock Pipeline] Fetched Finnhub quote for {ticker}")

            # 2. Company Profile
            profile_url = f"{base_url}/stock/profile2?symbol={ticker}"
            response = requests.get(profile_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data['profile'] = response.json()
                logger.info(f"[Stock Pipeline] Fetched Finnhub profile for {ticker}")

            # 3. News
            if self.valves.FETCH_NEWS:
                # Get news from last 7 days
                to_date = datetime.now().strftime('%Y-%m-%d')
                from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                news_url = f"{base_url}/company-news?symbol={ticker}&from={from_date}&to={to_date}"
                response = requests.get(news_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    news = response.json()
                    data['news'] = news[:self.valves.NEWS_LIMIT]  # Limit results
                    logger.info(f"[Stock Pipeline] Fetched {len(data['news'])} news articles for {ticker}")

            # 4. Earnings
            if self.valves.FETCH_EARNINGS:
                earnings_url = f"{base_url}/stock/earnings?symbol={ticker}"
                response = requests.get(earnings_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data['earnings'] = response.json()
                    logger.info(f"[Stock Pipeline] Fetched Finnhub earnings for {ticker}")

            # 5. Basic Financials
            if self.valves.FETCH_FINANCIALS:
                financials_url = f"{base_url}/stock/metric?symbol={ticker}&metric=all"
                response = requests.get(financials_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data['financials'] = response.json()
                    logger.info(f"[Stock Pipeline] Fetched Finnhub financials for {ticker}")

        except Exception as e:
            logger.error(f"[Stock Pipeline] Error fetching Finnhub data for {ticker}: {e}")

        return data

    def _fetch_alpha_vantage_data(self, ticker: str) -> Dict[str, Any]:
        """Fetch data from Alpha Vantage API"""
        data = {}
        base_url = "https://www.alphavantage.co/query"

        try:
            # 1. Company Overview (includes revenue, earnings, etc.)
            if self.valves.FETCH_FINANCIALS:
                params = {
                    "function": "OVERVIEW",
                    "symbol": ticker,
                    "apikey": self.valves.ALPHA_VANTAGE_API_KEY
                }
                response = requests.get(base_url, params=params, timeout=10)
                if response.status_code == 200:
                    overview = response.json()
                    if overview and 'Symbol' in overview:  # Valid response
                        data['overview'] = overview
                        logger.info(f"[Stock Pipeline] Fetched Alpha Vantage overview for {ticker}")

            # 2. Time Series Daily (recent prices)
            if self.valves.FETCH_PRICE_HISTORY:
                params = {
                    "function": "TIME_SERIES_DAILY",
                    "symbol": ticker,
                    "outputsize": "compact",  # Last 100 days
                    "apikey": self.valves.ALPHA_VANTAGE_API_KEY
                }
                response = requests.get(base_url, params=params, timeout=10)
                if response.status_code == 200:
                    time_series = response.json()
                    if 'Time Series (Daily)' in time_series:
                        # Get last N days
                        daily_data = time_series['Time Series (Daily)']
                        dates = sorted(daily_data.keys(), reverse=True)[:self.valves.PRICE_HISTORY_DAYS]
                        data['price_history'] = {date: daily_data[date] for date in dates}
                        logger.info(f"[Stock Pipeline] Fetched Alpha Vantage price history for {ticker}")

            # 3. Earnings
            if self.valves.FETCH_EARNINGS:
                params = {
                    "function": "EARNINGS",
                    "symbol": ticker,
                    "apikey": self.valves.ALPHA_VANTAGE_API_KEY
                }
                response = requests.get(base_url, params=params, timeout=10)
                if response.status_code == 200:
                    earnings = response.json()
                    if earnings and ('quarterlyEarnings' in earnings or 'annualEarnings' in earnings):
                        data['earnings'] = earnings
                        logger.info(f"[Stock Pipeline] Fetched Alpha Vantage earnings for {ticker}")

        except Exception as e:
            logger.error(f"[Stock Pipeline] Error fetching Alpha Vantage data for {ticker}: {e}")

        return data

    def _build_stock_context(self, stock_data: Dict[str, Dict[str, Any]]) -> str:
        """Build formatted context from stock data"""
        context_parts = []

        for ticker, data in stock_data.items():
            context_parts.append(f"\n{'='*60}")
            context_parts.append(f"STOCK DATA FOR {ticker}")
            context_parts.append(f"{'='*60}\n")

            # Finnhub data
            if 'finnhub' in data:
                finnhub = data['finnhub']

                # Quote
                if 'quote' in finnhub and finnhub['quote']:
                    quote = finnhub['quote']
                    context_parts.append("CURRENT PRICE:")
                    context_parts.append(f"  Current Price: ${quote.get('c', 'N/A')}")
                    context_parts.append(f"  Change: ${quote.get('d', 'N/A')} ({quote.get('dp', 'N/A')}%)")
                    context_parts.append(f"  High: ${quote.get('h', 'N/A')}")
                    context_parts.append(f"  Low: ${quote.get('l', 'N/A')}")
                    context_parts.append(f"  Open: ${quote.get('o', 'N/A')}")
                    context_parts.append(f"  Previous Close: ${quote.get('pc', 'N/A')}")
                    context_parts.append("")

                # Company Profile
                if 'profile' in finnhub and finnhub['profile']:
                    profile = finnhub['profile']
                    context_parts.append("COMPANY INFO:")
                    context_parts.append(f"  Name: {profile.get('name', 'N/A')}")
                    context_parts.append(f"  Industry: {profile.get('finnhubIndustry', 'N/A')}")
                    context_parts.append(f"  Market Cap: ${profile.get('marketCapitalization', 'N/A')}M")
                    context_parts.append(f"  Exchange: {profile.get('exchange', 'N/A')}")
                    context_parts.append(f"  Country: {profile.get('country', 'N/A')}")
                    context_parts.append(f"  Website: {profile.get('weburl', 'N/A')}")
                    context_parts.append("")

                # News
                if 'news' in finnhub and finnhub['news']:
                    context_parts.append("RECENT NEWS:")
                    for i, article in enumerate(finnhub['news'][:5], 1):
                        timestamp = datetime.fromtimestamp(article.get('datetime', 0)).strftime('%Y-%m-%d %H:%M')
                        context_parts.append(f"  [{i}] {article.get('headline', 'N/A')}")
                        context_parts.append(f"      Date: {timestamp}")
                        context_parts.append(f"      Summary: {article.get('summary', 'N/A')[:200]}...")
                        context_parts.append(f"      Source: {article.get('source', 'N/A')}")
                        context_parts.append("")

                # Earnings
                if 'earnings' in finnhub and finnhub['earnings']:
                    context_parts.append("EARNINGS HISTORY:")
                    for i, earning in enumerate(finnhub['earnings'][:4], 1):
                        context_parts.append(f"  Quarter {i}:")
                        context_parts.append(f"    Period: {earning.get('period', 'N/A')}")
                        context_parts.append(f"    Actual EPS: ${earning.get('actual', 'N/A')}")
                        context_parts.append(f"    Estimate EPS: ${earning.get('estimate', 'N/A')}")
                        context_parts.append(f"    Surprise: ${earning.get('surprise', 'N/A')}")
                    context_parts.append("")

                # Financials
                if 'financials' in finnhub and finnhub['financials']:
                    metrics = finnhub['financials'].get('metric', {})
                    if metrics:
                        context_parts.append("KEY FINANCIAL METRICS:")
                        context_parts.append(f"  52 Week High: ${metrics.get('52WeekHigh', 'N/A')}")
                        context_parts.append(f"  52 Week Low: ${metrics.get('52WeekLow', 'N/A')}")
                        context_parts.append(f"  P/E Ratio: {metrics.get('peNormalizedAnnual', 'N/A')}")
                        context_parts.append(f"  Beta: {metrics.get('beta', 'N/A')}")
                        context_parts.append(f"  Dividend Yield: {metrics.get('dividendYieldIndicatedAnnual', 'N/A')}")
                        context_parts.append("")

            # Alpha Vantage data
            if 'alpha_vantage' in data:
                av = data['alpha_vantage']

                # Overview
                if 'overview' in av and av['overview']:
                    overview = av['overview']
                    context_parts.append("COMPANY OVERVIEW (Alpha Vantage):")
                    context_parts.append(f"  Name: {overview.get('Name', 'N/A')}")
                    context_parts.append(f"  Description: {overview.get('Description', 'N/A')[:200]}...")
                    context_parts.append(f"  Sector: {overview.get('Sector', 'N/A')}")
                    context_parts.append(f"  Market Cap: ${overview.get('MarketCapitalization', 'N/A')}")
                    context_parts.append(f"  P/E Ratio: {overview.get('PERatio', 'N/A')}")
                    context_parts.append(f"  Revenue (TTM): ${overview.get('RevenueTTM', 'N/A')}")
                    context_parts.append(f"  Gross Profit (TTM): ${overview.get('GrossProfitTTM', 'N/A')}")
                    context_parts.append(f"  EPS: ${overview.get('EPS', 'N/A')}")
                    context_parts.append(f"  Dividend Per Share: ${overview.get('DividendPerShare', 'N/A')}")
                    context_parts.append("")

                # Price History
                if 'price_history' in av and av['price_history']:
                    context_parts.append("RECENT PRICE HISTORY:")
                    for date in sorted(av['price_history'].keys(), reverse=True)[:7]:  # Last week
                        day_data = av['price_history'][date]
                        context_parts.append(f"  {date}:")
                        context_parts.append(f"    Open: ${day_data.get('1. open', 'N/A')}")
                        context_parts.append(f"    High: ${day_data.get('2. high', 'N/A')}")
                        context_parts.append(f"    Low: ${day_data.get('3. low', 'N/A')}")
                        context_parts.append(f"    Close: ${day_data.get('4. close', 'N/A')}")
                        context_parts.append(f"    Volume: {day_data.get('5. volume', 'N/A')}")
                    context_parts.append("")

                # Earnings
                if 'earnings' in av and av['earnings']:
                    if 'quarterlyEarnings' in av['earnings']:
                        context_parts.append("QUARTERLY EARNINGS (Alpha Vantage):")
                        for i, quarter in enumerate(av['earnings']['quarterlyEarnings'][:4], 1):
                            context_parts.append(f"  Quarter {i} ({quarter.get('fiscalDateEnding', 'N/A')}):")
                            context_parts.append(f"    Reported EPS: ${quarter.get('reportedEPS', 'N/A')}")
                            context_parts.append(f"    Estimated EPS: ${quarter.get('estimatedEPS', 'N/A')}")
                            context_parts.append(f"    Surprise: ${quarter.get('surprise', 'N/A')}")
                            context_parts.append(f"    Surprise %: {quarter.get('surprisePercentage', 'N/A')}")
                        context_parts.append("")

        return "\n".join(context_parts)

    def _inject_context(
        self, messages: List[dict], user_query: str, context: str
    ) -> List[dict]:
        """Inject stock data context into the user's message"""
        augmented_message = f"""Use the following STOCK DATA to answer the user's question.

IMPORTANT INSTRUCTIONS:
- Provide specific, data-driven answers using the stock data below
- Include relevant numbers, dates, and metrics from the data
- If asked about prices, provide the current price and recent trends
- If asked about news, summarize the recent news articles
- If asked about earnings, provide the latest earnings data
- If asked about financials/revenue, use the financial metrics provided
- Be specific and cite actual data points from the context

--- STOCK DATA ---
{context}
--- END STOCK DATA ---

User question:
{user_query}"""

        # Create a new messages list with the augmented last message
        new_messages = messages[:-1] + [
            {
                "role": "user",
                "content": augmented_message
            }
        ]

        logger.info(f"[Stock Pipeline] Injected stock data context ({len(context)} chars)")
        return new_messages

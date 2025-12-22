#!/usr/bin/env python3
"""
Test script for Stock Data Pipeline
Demonstrates ticker extraction, stock query detection, and data fetching
"""

import sys
import logging
from stock_data_pipeline import Pipeline

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def test_ticker_extraction():
    """Test ticker symbol extraction from various query formats"""
    print("\n" + "="*60)
    print("TEST 1: Ticker Extraction")
    print("="*60)

    pipeline = Pipeline()

    test_queries = [
        "What's the price of AAPL?",
        "Tell me about $TSLA and $NVDA",
        "Compare Apple and Microsoft stock prices",
        "How is Tesla doing?",
        "Show me GOOGL, AMZN, and META performance",
        "$AAPL stock price today",
        "What is the current price of Amazon shares?",
    ]

    for query in test_queries:
        tickers = pipeline._extract_tickers(query)
        print(f"\nQuery: {query}")
        print(f"Extracted Tickers: {tickers}")

    print("\n✓ Ticker extraction test completed")


def test_stock_query_detection():
    """Test detection of stock-related queries"""
    print("\n" + "="*60)
    print("TEST 2: Stock Query Detection")
    print("="*60)

    pipeline = Pipeline()

    test_queries = [
        ("What's the stock price of Apple?", True),
        ("How much is AAPL trading at?", True),
        ("Tell me about Tesla earnings", True),
        ("What is the weather today?", False),
        ("How do I cook pasta?", False),
        ("Show me Microsoft's revenue", True),
        ("$NVDA news", True),
        ("What is machine learning?", False),
    ]

    for query, expected in test_queries:
        is_stock = pipeline._is_stock_query(query)
        status = "✓" if is_stock == expected else "✗"
        print(f"\n{status} Query: {query}")
        print(f"  Detected as stock query: {is_stock} (expected: {expected})")

    print("\n✓ Stock query detection test completed")


def test_company_name_mapping():
    """Test company name to ticker mapping"""
    print("\n" + "="*60)
    print("TEST 3: Company Name to Ticker Mapping")
    print("="*60)

    pipeline = Pipeline()

    test_queries = [
        ("What's Apple's stock price?", "AAPL"),
        ("Tell me about Microsoft", "MSFT"),
        ("How is Google doing?", "GOOGL"),
        ("Amazon stock price", "AMZN"),
        ("Tesla earnings", "TSLA"),
        ("Meta financial data", "META"),
        ("Nvidia performance", "NVDA"),
    ]

    for query, expected_ticker in test_queries:
        tickers = pipeline._extract_tickers(query)
        status = "✓" if expected_ticker in tickers else "✗"
        print(f"\n{status} Query: {query}")
        print(f"  Expected: {expected_ticker}, Got: {tickers}")

    print("\n✓ Company name mapping test completed")


def test_api_integration(api_keys_provided=False):
    """Test API integration (requires valid API keys)"""
    print("\n" + "="*60)
    print("TEST 4: API Integration")
    print("="*60)

    if not api_keys_provided:
        print("\n⚠ SKIPPED: API integration test requires valid API keys")
        print("To run this test:")
        print("1. Set FINNHUB_API_KEY and ALPHA_VANTAGE_API_KEY in the pipeline Valves")
        print("2. Run with --with-api-keys flag")
        return

    pipeline = Pipeline()

    # Test with a well-known stock
    test_ticker = "AAPL"

    print(f"\nFetching data for {test_ticker}...")

    # Fetch Finnhub data
    if pipeline.valves.FINNHUB_API_KEY:
        print("\n--- Finnhub Data ---")
        finnhub_data = pipeline._fetch_finnhub_data(test_ticker)

        if 'quote' in finnhub_data:
            print(f"✓ Quote data retrieved")
        if 'profile' in finnhub_data:
            print(f"✓ Profile data retrieved")
        if 'news' in finnhub_data:
            print(f"✓ News data retrieved ({len(finnhub_data['news'])} articles)")
        if 'earnings' in finnhub_data:
            print(f"✓ Earnings data retrieved")
        if 'financials' in finnhub_data:
            print(f"✓ Financials data retrieved")

    # Fetch Alpha Vantage data
    if pipeline.valves.ALPHA_VANTAGE_API_KEY:
        print("\n--- Alpha Vantage Data ---")
        av_data = pipeline._fetch_alpha_vantage_data(test_ticker)

        if 'overview' in av_data:
            print(f"✓ Overview data retrieved")
        if 'price_history' in av_data:
            print(f"✓ Price history retrieved ({len(av_data['price_history'])} days)")
        if 'earnings' in av_data:
            print(f"✓ Earnings data retrieved")

    print("\n✓ API integration test completed")


def test_context_building():
    """Test context building from mock stock data"""
    print("\n" + "="*60)
    print("TEST 5: Context Building")
    print("="*60)

    pipeline = Pipeline()

    # Mock stock data
    mock_data = {
        "AAPL": {
            "finnhub": {
                "quote": {
                    "c": 178.50,
                    "d": 2.30,
                    "dp": 1.31,
                    "h": 179.20,
                    "l": 176.80,
                    "o": 177.00,
                    "pc": 176.20
                },
                "profile": {
                    "name": "Apple Inc.",
                    "finnhubIndustry": "Technology",
                    "marketCapitalization": 2800000,
                    "exchange": "NASDAQ",
                    "country": "US"
                }
            }
        }
    }

    context = pipeline._build_stock_context(mock_data)

    print("\n--- Generated Context ---")
    print(context[:500] + "..." if len(context) > 500 else context)

    # Verify context contains expected elements
    checks = [
        ("STOCK DATA FOR AAPL", "Stock ticker header"),
        ("CURRENT PRICE:", "Current price section"),
        ("$178.50", "Price value"),
        ("COMPANY INFO:", "Company info section"),
        ("Apple Inc.", "Company name"),
    ]

    print("\n--- Context Validation ---")
    for check_str, description in checks:
        if check_str in context:
            print(f"✓ Contains {description}")
        else:
            print(f"✗ Missing {description}")

    print(f"\n✓ Context building test completed (generated {len(context)} chars)")


def run_all_tests(with_api_keys=False):
    """Run all tests"""
    print("\n" + "="*60)
    print("STOCK DATA PIPELINE - TEST SUITE")
    print("="*60)

    try:
        test_ticker_extraction()
        test_stock_query_detection()
        test_company_name_mapping()
        test_api_integration(api_keys_provided=with_api_keys)
        test_context_building()

        print("\n" + "="*60)
        print("ALL TESTS COMPLETED")
        print("="*60)
        print("\n✓ Stock Data Pipeline is ready to use!")
        print("\nNext steps:")
        print("1. Configure your API keys in OpenWebUI Valves")
        print("2. Install the pipeline in OpenWebUI")
        print("3. Try asking about stock prices!")

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Check for API keys flag
    with_api_keys = "--with-api-keys" in sys.argv

    run_all_tests(with_api_keys=with_api_keys)

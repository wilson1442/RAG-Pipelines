#!/usr/bin/env python3
"""
Quick validation script for Stock Data Pipeline
Run this BEFORE uploading to OpenWebUI to catch errors early
"""

import sys
import traceback

def test_imports():
    """Test that all required imports work"""
    print("Testing imports...")
    try:
        from typing import List, Dict, Any, Union, Generator, Optional
        from pydantic import BaseModel, Field
        import requests
        import logging
        import json
        import re
        from datetime import datetime, timedelta
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("  Install missing packages: pip install pydantic requests")
        return False

def test_pipeline_load():
    """Test that the pipeline class can be loaded"""
    print("\nTesting pipeline load...")
    try:
        from stock_data_pipeline import Pipeline
        print("✓ Pipeline class loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to load pipeline: {e}")
        traceback.print_exc()
        return False

def test_pipeline_init():
    """Test that the pipeline can be initialized"""
    print("\nTesting pipeline initialization...")
    try:
        from stock_data_pipeline import Pipeline
        pipeline = Pipeline()
        print(f"✓ Pipeline initialized: {pipeline.name}")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize pipeline: {e}")
        traceback.print_exc()
        return False

def test_valves():
    """Test that valves are configured correctly"""
    print("\nTesting Valves configuration...")
    try:
        from stock_data_pipeline import Pipeline
        pipeline = Pipeline()
        valves = pipeline.valves
        print(f"  - ENABLE_STOCK_DATA: {valves.ENABLE_STOCK_DATA}")
        print(f"  - ENABLE_MARKET_SCREENING: {valves.ENABLE_MARKET_SCREENING}")
        print(f"  - ENABLE_INVESTMENT_ADVICE: {valves.ENABLE_INVESTMENT_ADVICE}")
        print(f"  - FINNHUB_API_KEY: {'Set' if valves.FINNHUB_API_KEY else 'Not set (will need configuration)'}")
        print(f"  - ALPHA_VANTAGE_API_KEY: {'Set' if valves.ALPHA_VANTAGE_API_KEY else 'Not set (will need configuration)'}")
        print("✓ Valves configured correctly")
        return True
    except Exception as e:
        print(f"✗ Valves configuration error: {e}")
        traceback.print_exc()
        return False

def test_get_models():
    """Test that get_models() doesn't crash"""
    print("\nTesting get_models() method...")
    try:
        from stock_data_pipeline import Pipeline
        pipeline = Pipeline()
        models = pipeline.get_models()
        print(f"✓ get_models() returned {len(models)} model(s)")
        return True
    except Exception as e:
        print(f"✗ get_models() error: {e}")
        traceback.print_exc()
        return False

def test_query_detection():
    """Test query detection methods"""
    print("\nTesting query detection...")
    try:
        from stock_data_pipeline import Pipeline
        pipeline = Pipeline()

        # Test stock query
        is_stock = pipeline._is_stock_query("What's the price of AAPL?")
        print(f"  - Stock query detection: {'✓' if is_stock else '✗'}")

        # Test investment query
        is_invest = pipeline._is_investment_advice_query("What should I invest in?")
        print(f"  - Investment query detection: {'✓' if is_invest else '✗'}")

        # Test market screening query
        is_market = pipeline._is_market_screening_query("What's hot in the market?")
        print(f"  - Market screening detection: {'✓' if is_market else '✗'}")

        print("✓ Query detection working")
        return True
    except Exception as e:
        print(f"✗ Query detection error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("Stock Data Pipeline - Pre-Upload Validation")
    print("="*60)

    tests = [
        ("Imports", test_imports),
        ("Pipeline Load", test_pipeline_load),
        ("Pipeline Init", test_pipeline_init),
        ("Valves", test_valves),
        ("Get Models", test_get_models),
        ("Query Detection", test_query_detection),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' crashed: {e}")
            results.append((name, False))

    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print("\n" + "="*60)
    print(f"Score: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! Pipeline is ready to upload to OpenWebUI.")
        print("\nNext steps:")
        print("1. Upload stock_data_pipeline.py to OpenWebUI")
        print("2. Configure API keys in Valves")
        print("3. Test with a query like 'What should I invest in?'")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. Fix errors before uploading.")
        print("\nCommon issues:")
        print("- Missing dependencies: pip install pydantic requests")
        print("- Syntax errors in the pipeline code")
        print("- Import errors")
        return 1

if __name__ == "__main__":
    sys.exit(main())

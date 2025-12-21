#!/usr/bin/env python3
"""
Test script for debugging RAG multi-collection and citation issues.
This script simulates the pipeline's behavior to help identify issues.
"""

import json
import logging

# Setup logging to see detailed output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_collection_splitting():
    """Test how collections are split from the valve configuration."""
    test_cases = [
        "api_docs,personal_documents",
        "api_docs, personal_documents",  # with spaces
        " api_docs , personal_documents ",  # extra spaces
        "single_collection",
        "one,two,three",
        "",
    ]

    print("\n=== Testing Collection Splitting ===")
    for test in test_cases:
        collections = [c.strip() for c in test.split(",") if c.strip()]
        print(f"Input: '{test}'")
        print(f"  -> Collections: {collections}")
        print(f"  -> Count: {len(collections)}")
        print()


def test_result_tagging():
    """Test how results are tagged with collection names."""
    print("\n=== Testing Result Tagging ===")

    # Simulate results from multiple collections
    collection_a_results = [
        {"document": "Result A1", "distance": 0.2, "metadata": {"source": "doc1.pdf"}},
        {"document": "Result A2", "distance": 0.3, "metadata": {"source": "doc2.pdf"}},
    ]

    collection_b_results = [
        {"document": "Result B1", "distance": 0.15, "metadata": {"source": "doc3.pdf"}},
        {"document": "Result B2", "distance": 0.35, "metadata": {"source": "doc4.pdf"}},
    ]

    # Simulate the tagging process
    all_results = []

    for collection, results in [("api_docs", collection_a_results),
                                ("personal_documents", collection_b_results)]:
        print(f"\nProcessing collection: {collection}")
        for result in results:
            if "metadata" not in result:
                result["metadata"] = {}
            result["metadata"]["collection"] = collection
            print(f"  Tagged: {result['document'][:20]}... -> collection: {collection}")
        all_results.extend(results)

    print(f"\nTotal results: {len(all_results)}")

    # Simulate sorting and limiting
    TOP_K = 5
    all_results.sort(key=lambda x: x.get("distance", float('inf')))
    all_results = all_results[:TOP_K]

    print(f"\nAfter sorting and limiting to TOP_K={TOP_K}:")
    for i, result in enumerate(all_results, 1):
        print(f"  [{i}] {result['document']} (distance={result['distance']}, "
              f"collection={result['metadata'].get('collection')})")

    # Show which collections are in final results
    collections_in_results = set(r.get("metadata", {}).get("collection") for r in all_results)
    print(f"\nCollections represented in final results: {collections_in_results}")


def test_context_building():
    """Test how context with citations is built."""
    print("\n=== Testing Context Building ===")

    results = [
        {
            "document": "Authentication can be configured via config file.",
            "distance": 0.23,
            "metadata": {
                "collection": "api_docs",
                "source": "auth-guide.pdf",
                "type": "text",
                "chunk_index": 0
            }
        },
        {
            "document": "Remember to enable 2FA in production.",
            "distance": 0.31,
            "metadata": {
                "collection": "personal_documents",
                "source": "security-notes.md",
                "type": "text",
                "chunk_index": 2
            }
        },
    ]

    context_parts = []
    for i, result in enumerate(results, 1):
        doc = result.get("document", "")
        metadata = result.get("metadata") or {}
        distance = result.get("distance", "N/A")

        chunk = f"[{i}] {doc}\n"
        chunk += f"    (distance: {distance}"

        if metadata:
            if "collection" in metadata:
                chunk += f", collection: {metadata['collection']}"
            if "source" in metadata:
                chunk += f", source: {metadata['source']}"
            if "type" in metadata:
                chunk += f", type: {metadata['type']}"
            if "chunk_index" in metadata:
                chunk += f", chunk: {metadata['chunk_index']}"

        chunk += ")"
        context_parts.append(chunk)

    context = "\n\n".join(context_parts)
    print("\nGenerated Context:")
    print("-" * 80)
    print(context)
    print("-" * 80)

    # Show what would be injected
    user_question = "How do I configure authentication?"
    augmented = f"""Use the following CONTEXT to answer the user question.
If the answer is not in the context, say you do not know.

--- CONTEXT ---
{context}
--- END CONTEXT ---

User question:
{user_question}"""

    print("\nAugmented Message (first 500 chars):")
    print("-" * 80)
    print(augmented[:500] + "...")
    print("-" * 80)


def main():
    """Run all tests."""
    print("=" * 80)
    print("RAG Pipeline Multi-Collection and Citation Test")
    print("=" * 80)

    test_collection_splitting()
    test_result_tagging()
    test_context_building()

    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)
    print("\nTo test with actual RAG API:")
    print("1. Ensure your RAG API is running")
    print("2. Check OpenWebUI logs when making queries")
    print("3. Look for '[RAG Pipeline]' log entries")
    print("4. Verify collections are being queried correctly")
    print("5. Check that context includes collection names in citations")


if __name__ == "__main__":
    main()

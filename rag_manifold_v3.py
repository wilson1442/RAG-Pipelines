"""
title: RAG Manifold v3 (Fixed)
author: OpenWebUI Expert
description: RAG manifold with multi-collection support, proper citations, and streaming
required_open_webui_version: 0.4.0+
version: 3.2.1
license: MIT
"""

from typing import List, Dict, Any, Union, Generator
from pydantic import BaseModel, Field
import requests
import logging
import json

logger = logging.getLogger(__name__)


class Pipeline:
    """
    MANIFOLD pipeline for RAG integration with Ollama.

    FIXES in v3.2.1:
    - Enhanced logging for multi-collection debugging
    - Added detailed logging for context building and citation tracking
    - Optimized single vs multi-collection query paths
    - Better visibility into which collections are being queried

    FIXES in v3.2.0:
    - Added multi-collection support (comma-separated collections)
    - Added collection name to citations/context
    - Improved result sorting across multiple collections

    FIXES in v3.1.0:
    - Fixed RAG API payload format (collection/n_results)
    - Fixed streaming response parsing from Ollama
    - Enabled Ollama native API by default
    - Updated default URLs to match deployment
    - Better error handling
    """

    class Valves(BaseModel):
        """Configuration options exposed in OpenWebUI UI"""
        RAG_API_URL: str = Field(
            default="http://192.168.4.10:8012/query",
            description="URL of the external RAG query API"
        )
        DEFAULT_COLLECTION: str = Field(
            default="default",
            description="Collection name(s) to query - supports multiple collections separated by commas (e.g., 'api_docs,personal_documents')"
        )
        TOP_K: int = Field(
            default=5,
            description="Number of RAG results to retrieve"
        )
        UPSTREAM_BASE_URL: str = Field(
            default="http://192.168.4.10:11434",
            description="Ollama base URL"
        )
        USE_OLLAMA_NATIVE: bool = Field(
            default=True,
            description="Use Ollama native API (recommended)"
        )
        ENABLE_RAG: bool = Field(
            default=True,
            description="Enable RAG augmentation (disable for passthrough)"
        )

    def __init__(self):
        """Initialize the pipeline."""
        self.type = "manifold"
        self.name = "RAG Manifold v3"
        self.valves = self.Valves()
        self.pipelines = []

        # Load available models from Ollama
        try:
            self.pipelines = self._get_upstream_models()
            if not self.pipelines:
                logger.warning("No models found, using fallback")
                self.pipelines = [{"id": "llama2", "name": "llama2 (fallback)"}]
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            self.pipelines = [{"id": "llama2", "name": "llama2 (check Ollama)"}]

    def pipes(self) -> List[Dict[str, str]]:
        """Return available models for OpenWebUI selector."""
        return self.pipelines

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict
    ) -> Union[str, Dict[str, Any], Generator]:
        """
        Main pipeline execution:
        1. Query RAG API (if enabled)
        2. Inject context into messages
        3. Call Ollama
        4. Return response (streaming or non-streaming)
        """
        try:
            logger.info(f"[RAG Pipeline] Model: {model_id}, Message: {user_message[:100]}...")

            updated_messages = messages

            # RAG augmentation
            if self.valves.ENABLE_RAG:
                logger.info("[RAG Pipeline] Querying RAG API...")
                rag_results = self._query_rag(user_message)
                logger.info(f"[RAG Pipeline] Got {len(rag_results)} results")

                context = self._build_context(rag_results)
                augmented_message = self._inject_context(user_message, context)
                updated_messages = self._update_messages(messages, augmented_message)
                logger.info(f"[RAG Pipeline] Context: {len(context)} chars")
            else:
                logger.info("[RAG Pipeline] RAG disabled")

            # Call upstream
            logger.info(f"[RAG Pipeline] Calling {model_id}...")
            body["model"] = model_id
            body["messages"] = updated_messages

            response = self._call_upstream(body)
            logger.info("[RAG Pipeline] ✅ Success")

            return response

        except Exception as e:
            logger.exception("Pipeline error")
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": f"❌ ERROR: {type(e).__name__}: {str(e)}"
                    }
                }]
            }

    def _get_upstream_models(self) -> List[Dict[str, str]]:
        """Fetch models from Ollama."""
        response = requests.get(
            f"{self.valves.UPSTREAM_BASE_URL}/api/tags",
            timeout=10
        )
        response.raise_for_status()

        models = response.json().get("models", [])
        return [
            {"id": model["model"], "name": model["name"]}
            for model in models
        ]

    def _query_rag(self, query: str) -> List[Dict[str, Any]]:
        """
        Query RAG API with multi-collection support.
        FIXED: Supports multiple collections (comma-separated) and tracks collection per result
        """
        collections = []
        if self.valves.DEFAULT_COLLECTION.strip():
            # Split by comma and strip whitespace
            collections = [c.strip() for c in self.valves.DEFAULT_COLLECTION.split(",") if c.strip()]

        logger.info(f"[RAG Pipeline] Collections to query: {collections}")

        # If no collections specified, query without collection parameter
        if not collections:
            logger.info("[RAG Pipeline] No collections specified, querying default")
            return self._query_single_collection(query, None)

        # For single collection, skip the multi-collection overhead
        if len(collections) == 1:
            logger.info(f"[RAG Pipeline] Single collection mode: {collections[0]}")
            results = self._query_single_collection(query, collections[0])
            # Still tag with collection name for consistency
            for result in results:
                if "metadata" not in result:
                    result["metadata"] = {}
                result["metadata"]["collection"] = collections[0]
            return results

        # Query each collection and combine results
        logger.info(f"[RAG Pipeline] Multi-collection mode: querying {len(collections)} collections")
        all_results = []
        for idx, collection in enumerate(collections, 1):
            logger.info(f"[RAG Pipeline] Querying collection {idx}/{len(collections)}: '{collection}'")
            results = self._query_single_collection(query, collection)
            logger.info(f"[RAG Pipeline] Collection '{collection}' returned {len(results)} results")

            # Tag each result with its collection name
            for result in results:
                if "metadata" not in result:
                    result["metadata"] = {}
                result["metadata"]["collection"] = collection

            all_results.extend(results)
            logger.info(f"[RAG Pipeline] Total results so far: {len(all_results)}")

        # Sort by distance (lower is better) and limit to TOP_K
        logger.info(f"[RAG Pipeline] Sorting and limiting {len(all_results)} results to top {self.valves.TOP_K}")
        all_results.sort(key=lambda x: x.get("distance", float('inf')))
        all_results = all_results[:self.valves.TOP_K]

        # Log which collections are represented in final results
        collections_in_results = set(r.get("metadata", {}).get("collection") for r in all_results)
        logger.info(f"[RAG Pipeline] Final {len(all_results)} results from collections: {collections_in_results}")
        return all_results

    def _query_single_collection(self, query: str, collection: str = None) -> List[Dict[str, Any]]:
        """Query a single collection from the RAG API."""
        payload = {
            "query": query,
            "n_results": self.valves.TOP_K
        }

        # Add collection if specified
        if collection:
            payload["collection"] = collection

        logger.info(f"RAG API request: {payload}")

        try:
            response = requests.post(
                self.valves.RAG_API_URL,
                json=payload,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])
            logger.info(f"RAG API returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"RAG API error for collection '{collection}': {e}")
            return []  # Don't crash, just return empty results

    def _build_context(self, results: List[Dict[str, Any]]) -> str:
        """Build context from RAG results with collection citations."""
        if not results:
            logger.info("[RAG Pipeline] No results to build context from")
            return ""

        context_parts = []
        for i, result in enumerate(results, 1):
            doc = result.get("document", "")
            metadata = result.get("metadata") or {}
            distance = result.get("distance", "N/A")

            # Log each result being processed
            logger.info(f"[RAG Pipeline] Building context for result {i}: "
                       f"collection={metadata.get('collection', 'N/A')}, "
                       f"source={metadata.get('source', 'N/A')}, "
                       f"distance={distance}")

            chunk = f"[{i}] {doc}\n"
            chunk += f"    (distance: {distance}"

            if metadata:
                # Include collection name first if available
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
        logger.info(f"[RAG Pipeline] Built context with {len(context_parts)} citations, {len(context)} chars total")
        return context

    def _inject_context(self, user_question: str, context: str) -> str:
        """Inject context into user message."""
        if not context:
            logger.info("[RAG Pipeline] No context to inject")
            return user_question

        augmented = f"""Use the following CONTEXT to answer the user question.
If the answer is not in the context, say you do not know.

--- CONTEXT ---
{context}
--- END CONTEXT ---

User question:
{user_question}"""

        logger.info(f"[RAG Pipeline] Injected context into message (total length: {len(augmented)} chars)")
        logger.debug(f"[RAG Pipeline] Augmented message preview: {augmented[:500]}...")
        return augmented

    def _update_messages(self, messages: List[dict], new_content: str) -> List[dict]:
        """Replace last user message with augmented version."""
        updated = [dict(msg) for msg in messages]

        # Find and update last user message
        for i in range(len(updated) - 1, -1, -1):
            if updated[i].get("role") == "user":
                updated[i]["content"] = new_content
                return updated

        # No user message found, append new one
        updated.append({"role": "user", "content": new_content})
        return updated

    def _call_upstream(self, body: dict) -> Union[Dict[str, Any], Generator]:
        """
        Call Ollama with proper streaming support.
        FIXED: Properly parse Ollama streaming JSON responses.
        """
        is_streaming = body.get("stream", False)

        if self.valves.USE_OLLAMA_NATIVE:
            # Use Ollama native API
            logger.info("[RAG Pipeline] Using Ollama /api/chat")

            ollama_payload = {
                "model": body.get("model"),
                "messages": body.get("messages", []),
                "stream": is_streaming,
                "options": {}
            }

            # Map parameters
            if "temperature" in body:
                ollama_payload["options"]["temperature"] = body["temperature"]
            if "top_p" in body:
                ollama_payload["options"]["top_p"] = body["top_p"]
            if "top_k" in body:
                ollama_payload["options"]["top_k"] = body["top_k"]
            if "max_tokens" in body:
                ollama_payload["options"]["num_predict"] = body["max_tokens"]

            logger.info(f"[RAG Pipeline] Request: model={ollama_payload['model']}, stream={is_streaming}")

            response = requests.post(
                f"{self.valves.UPSTREAM_BASE_URL}/api/chat",
                json=ollama_payload,
                timeout=120,
                stream=is_streaming
            )
            response.raise_for_status()

            if is_streaming:
                # FIXED: Parse Ollama streaming response properly
                logger.info("[RAG Pipeline] Streaming enabled")
                return self._stream_ollama_response(response)
            else:
                # Non-streaming response
                ollama_response = response.json()
                logger.info("[RAG Pipeline] Non-streaming response")
                return {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": ollama_response.get("message", {}).get("content", "")
                        }
                    }]
                }
        else:
            # Use OpenAI-compatible endpoint
            logger.info("[RAG Pipeline] Using /v1/chat/completions")

            response = requests.post(
                f"{self.valves.UPSTREAM_BASE_URL}/v1/chat/completions",
                json=body,
                timeout=120,
                stream=is_streaming
            )
            response.raise_for_status()

            if is_streaming:
                return response.iter_lines()
            else:
                return response.json()

    def _stream_ollama_response(self, response) -> Generator[str, None, None]:
        """
        Parse Ollama streaming response and yield content.
        FIXED: Properly extract content from Ollama JSON streaming format.

        Ollama streams JSON objects like:
        {"message":{"content":"Hello"},"done":false}
        {"message":{"content":" world"},"done":false}
        {"message":{"content":"!"},"done":true}
        """
        for line in response.iter_lines():
            if line:
                try:
                    # Decode bytes to string
                    line_str = line.decode('utf-8') if isinstance(line, bytes) else line

                    # Parse JSON
                    data = json.loads(line_str)

                    # Extract content from message
                    if "message" in data and "content" in data["message"]:
                        content = data["message"]["content"]
                        if content:  # Only yield if content is not empty
                            yield content

                    # Check if done
                    if data.get("done", False):
                        logger.info("[RAG Pipeline] Streaming complete")
                        break

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse streaming line: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing stream: {e}")
                    continue

#!/usr/bin/env python3
"""

"""

from __future__ import annotations

import os
import sys
import subprocess
from typing import List, Optional
from pathlib import Path

from fastmcp import FastMCP
import chromadb
from chromadb.config import Settings, DEFAULT_TENANT, DEFAULT_DATABASE
from sentence_transformers import SentenceTransformer

# ╔══════════════════════════════════════════════════════════════════╗
# 1. Configuration and Constants                                     ║
# ╚══════════════════════════════════════════════════════════════════╝

# Paths to OmniTech knowledge base
KNOWLEDGE_BASE_DIR = Path("knowledge_base_pdfs")
CHROMA_PATH = Path("./mcp_chroma_db")

# Document categories for targeted search
DOCUMENT_CATEGORIES = {
}

# Caches
_embed_model = None
_chroma_client = None
_knowledge_collection = None

def _get_embed_model() -> SentenceTransformer:
    """Get embedding model, using cache if available."""
    global _embed_model
    if _embed_model is None:
        print(f"Loading embedding model: {EMBED_MODEL_NAME}...")
        _embed_model = SentenceTransformer(EMBED_MODEL_NAME)
        print("✅ Embedding model loaded")
    return _embed_model

def _get_chroma_collection() -> chromadb.Collection:
    """Get or create ChromaDB collection for knowledge base."""
    global _chroma_client, _knowledge_collection

    if _chroma_client is None:
        print(f"Initializing ChromaDB at {CHROMA_PATH}...")
        _chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_PATH),
            settings=Settings(),
            tenant=DEFAULT_TENANT,
            database=DEFAULT_DATABASE,
        )
        print("✅ ChromaDB initialized")

    if _knowledge_collection is None:
        _knowledge_collection = _chroma_client.get_or_create_collection("omnitech_knowledge")
        print(f"📚 Knowledge collection: {_knowledge_collection.count()} documents")

    return _knowledge_collection

def _index_knowledge_base():
    """Index OmniTech PDFs into ChromaDB if not already indexed."""
    collection = _get_chroma_collection()

    # Check if already indexed
    if collection.count() > 0:
        print(f"✅ Knowledge base already indexed ({collection.count()} chunks)")
        return

    print("📚 Indexing OmniTech knowledge base PDFs...")
    if not INDEX_TOOL_PATH.exists():
        print(f"❌ Index tool not found at {INDEX_TOOL_PATH}")
        return

    if not KNOWLEDGE_BASE_DIR.exists():
        print(f"❌ Knowledge base directory not found at {KNOWLEDGE_BASE_DIR}")
        return

    try:

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Successfully indexed knowledge base")
            # Refresh collection count
            _knowledge_collection = None
            collection = _get_chroma_collection()
        else:
            print(f"❌ Indexing failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Error running index tool: {e}")


CANONICAL_QUERIES = {
    "account_security": {
    },

    "device_troubleshooting": {
    },

    "returns_refunds": {
    },

    "general_support": {
}

# ╔══════════════════════════════════════════════════════════════════╗
# ╚══════════════════════════════════════════════════════════════════╝

mcp = FastMCP("OmniTechSupportServer")


@mcp.tool
def list_canonical_queries() -> dict:
    """
    """
    queries = []
    for name, config in CANONICAL_QUERIES.items():
        queries.append({
            "name": name,
            "description": config["description"],
            "example_queries": config["example_queries"][:3]  # Show first 3 examples
        })

    return {"queries": queries}

@mcp.tool
def classify_canonical_query(user_query: str) -> dict:
    """
    user_lower = user_query.lower()
    scores = {}

    # Keyword mapping for classification
    keyword_maps = {
    }


    for query_name, keywords in keyword_maps.items():
        score = 0
        matched_keywords = []

        for keyword in keywords:
            if keyword in user_lower:
                score += 1
                matched_keywords.append(keyword)

        # Normalize score
        scores[query_name] = score / len(keywords) if keywords else 0

    for query_name, config in CANONICAL_QUERIES.items():
        for example in config["example_queries"]:
            example_lower = example.lower()
            # Calculate similarity
            example_words = set(example_lower.split())
            user_words = set(user_lower.split())
            overlap = len(example_words.intersection(user_words))
            if overlap > 0:
                similarity = overlap / max(len(example_words), len(user_words))
                scores[query_name] = max(scores.get(query_name, 0), similarity)

    # Find best match
    if not scores or max(scores.values()) == 0:
        # Default to general support
        return {
            "suggested_query": "general_support",
            "confidence": 0.3,
            "alternatives": [],
            "reason": "No specific category matched, routing to general support"
        }


    # Get alternatives
    alternatives = [
        {"query": name, "score": score}
        for name, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if score > 0 and name != best_query
    ][:2]

    return {
        "suggested_query": best_query,
        "confidence": confidence,
        "alternatives": alternatives,
        "reason": f"Matched to {best_query} with confidence {confidence:.2f}"
    }

@mcp.tool
def get_query_template(query_name: str) -> dict:
    """
    """
    if query_name not in CANONICAL_QUERIES:
        return {"error": f"Unknown canonical query: {query_name}"}

    config = CANONICAL_QUERIES[query_name]

    return {
        "template": config["prompt_template"],
        "description": config["description"]
    }

# ─── Knowledge Retrieval Tools (RAG) ─────────────────────────────

@mcp.tool
def vector_search_knowledge(query: str, top_k: int = 5, category: str = None) -> dict:
    """
    """
    try:
        embed_model = _get_embed_model()
        collection = _get_chroma_collection()

        if collection.count() == 0:
            return {
                "matches": [],
                "count": 0,
                "error": "Knowledge base not indexed. Please run the server to index PDFs."
            }


        # Prepare where clause for category filtering
        where_clause = None
        if category and category in DOCUMENT_CATEGORIES:
            pdf_names = DOCUMENT_CATEGORIES[category]
            where_clause = {"source": {"$in": [f"knowledge_base_pdfs/{pdf}" for pdf in pdf_names]}}

        # Search
        results = collection.query(
        )

        matches = []
        if results["documents"] and results["documents"][0]:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            ):
                matches.append({
                    "document": doc,
                    "metadata": meta,
                    "distance": dist,
                    "source": meta.get("source", "Unknown")
                })

        return {
            "matches": matches,
            "count": len(matches),
            "category_filter": category
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool
def get_knowledge_for_query(category: str, query: str, top_k: int = 3) -> dict:
    """
    Get relevant knowledge for a specific support category and query.

    This is a convenience tool that combines classification with retrieval.

    Parameters
    ----------
    category : str
        Support category (account_security, device_troubleshooting, etc.)
    query : str
        User's question
    top_k : int
        Number of knowledge chunks to retrieve

    Returns
    -------
    dict
        {"knowledge": concatenated relevant text, "sources": list of sources}
    """
    try:
        # Use vector search with category filter
        search_result = vector_search_knowledge(query, top_k=top_k, category=category)

        if "error" in search_result:
            return search_result

        if not search_result["matches"]:
            return {
                "knowledge": "No relevant documentation found.",
                "sources": []
            }

        # Concatenate knowledge
        knowledge_parts = []
        sources = set()

        for match in search_result["matches"]:
            knowledge_parts.append(match["document"])
            sources.add(match["source"])

        return {
            "knowledge": "\n\n---\n\n".join(knowledge_parts),
            "sources": list(sources)
        }
    except Exception as e:
        return {"error": str(e)}

# ─── Validation Tools ─────────────────────────────────────────────

@mcp.tool
def validate_support_query(query: str) -> dict:
    """
    """
    if not query or len(query.strip()) < 3:
        return {
            "valid": False,
            "reason": "Query too short",
            "suggestions": ["Please provide more details about your issue"]
        }

    # Check for inappropriate content (simplified check)
    inappropriate_words = ["hack", "exploit", "illegal", "crack"]
    query_lower = query.lower()

    for word in inappropriate_words:
        if word in query_lower and "hacked" not in query_lower:  # Allow "my account was hacked"
            return {
                "valid": False,
                "reason": "Query contains inappropriate content",
                "suggestions": ["Please contact official support for this type of request"]
            }

    return {
        "valid": True,
        "reason": "Query is appropriate for customer support",
        "suggestions": []
    }

# ─── Statistics Tools ─────────────────────────────────────────────

@mcp.tool
def get_knowledge_base_stats() -> dict:
    """
    Get statistics about the indexed knowledge base.

    Returns
    -------
    dict
        {"total_chunks": int, "documents": dict, "status": str}
    """
    try:
        collection = _get_chroma_collection()

        if collection.count() == 0:
            return {
                "total_chunks": 0,
                "documents": {},
                "status": "Not indexed"
            }

        # Get all metadata to count by source
        all_results = collection.get(include=["metadatas"])
        doc_counts = {}

        for metadata in all_results["metadatas"]:
            source = metadata.get("source", "Unknown")
            # Extract just the filename
            filename = source.split("/")[-1] if "/" in source else source
            doc_counts[filename] = doc_counts.get(filename, 0) + 1

        return {
            "total_chunks": collection.count(),
            "documents": doc_counts,
            "status": "Indexed and ready"
        }
    except Exception as e:
        return {"error": str(e)}

# ╔══════════════════════════════════════════════════════════════════╗
# 4. Server Startup                                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    print("=" * 70)
    print("OmniTech Customer Support MCP Server")
    print("=" * 70)

    # Initialize and index knowledge base on startup
    print("\n[Initialization] Setting up knowledge base...")
    _index_knowledge_base()

    print("\n" + "=" * 70)
    print("Available tool categories:")
    print("  [Knowledge Retrieval] ")
    print("    • vector_search_knowledge - Semantic search through support docs")
    print("    • get_knowledge_for_query - Category-specific knowledge retrieval")
    print("  [Classification] ")
    print("    • list_canonical_queries - Show available support categories")
    print("    • classify_canonical_query - Match user intent to category")
    print("  [Templates] ")
    print("    • get_query_template - Get support response template")
    print("  [Validation] ✓")
    print("    • validate_support_query - Check query appropriateness")
    print("  [Statistics] ")
    print("    • get_knowledge_base_stats - Knowledge base information")

    print("\nSupport Categories:")
    for name, config in CANONICAL_QUERIES.items():
        print(f"  • {name}: {config['description']}")

    print("\nKnowledge Base Documents:")
    stats = get_knowledge_base_stats()
    if "documents" in stats:
        for doc, count in stats["documents"].items():
            print(f"  • {doc}: {count} chunks")
        print(f"  Total: {stats['total_chunks']} chunks")

    print("\nServer endpoint: POST http://127.0.0.1:8000/mcp/")
    print("=" * 70 + "\n")

    mcp.run(transport="http", host="127.0.0.1", port=8000, path="/mcp/")

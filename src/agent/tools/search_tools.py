# -*- coding: utf-8 -*-
"""
Search tools — wraps SearchService methods as agent-callable tools.

Tools:
- search_stock_news: search latest stock news
- search_comprehensive_intel: multi-dimensional intelligence search
- fetch_webpage: fetch and extract text content from a URL
- search_local_news: search local news sources (Wantgoo, etc.)
"""

import logging
from typing import Optional

from src.agent.tools.registry import ToolParameter, ToolDefinition

logger = logging.getLogger(__name__)


def _get_search_service():
    """Lazy-init SearchService with config keys."""
    from src.search_service import SearchService
    from src.config import get_config
    config = get_config()
    return SearchService(
        bocha_keys=config.bocha_api_keys,
        tavily_keys=config.tavily_api_keys,
        brave_keys=config.brave_api_keys,
        serpapi_keys=config.serpapi_keys,
        news_max_age_days=config.news_max_age_days,
        local_news_dirs=config.local_news_dirs,
    )


def _handle_search_stock_news(stock_code: str, stock_name: str) -> dict:
    """Search latest news for a stock."""
    service = _get_search_service()

    if not service.is_available:
        return {"error": "No search engine available (no API keys configured)"}

    response = service.search_stock_news(stock_code, stock_name, max_results=5)

    if not response.success:
        return {
            "query": response.query,
            "success": False,
            "error": response.error_message,
        }

    return {
        "query": response.query,
        "provider": response.provider,
        "success": True,
        "results_count": len(response.results),
        "results": [
            {
                "title": r.title,
                "snippet": r.snippet,
                "url": r.url,
                "source": r.source,
                "published_date": r.published_date,
            }
            for r in response.results
        ],
    }


search_stock_news_tool = ToolDefinition(
    name="search_stock_news",
    description="Search for the latest news articles about a specific stock. "
                "Requires both stock_code and stock_name for accurate search. "
                "Returns news titles, snippets, sources, and URLs.",
    parameters=[
        ToolParameter(
            name="stock_code",
            type="string",
            description="Stock code, e.g., '600519'",
        ),
        ToolParameter(
            name="stock_name",
            type="string",
            description="Stock name in Chinese, e.g., '贵州茅台'",
        ),
    ],
    handler=_handle_search_stock_news,
    category="search",
)


# ============================================================
# search_comprehensive_intel
# ============================================================

def _handle_search_comprehensive_intel(stock_code: str, stock_name: str) -> dict:
    """Multi-dimensional intelligence search."""
    service = _get_search_service()

    if not service.is_available:
        return {"error": "No search engine available (no API keys configured)"}

    intel_results = service.search_comprehensive_intel(
        stock_code=stock_code,
        stock_name=stock_name,
        max_searches=5,
    )

    if not intel_results:
        return {"error": "Comprehensive intel search returned no results"}

    # Format into readable report
    report = service.format_intel_report(intel_results, stock_name)

    # Also return structured data
    dimensions = {}
    for dim_name, response in intel_results.items():
        if response and response.success:
            dimensions[dim_name] = {
                "query": response.query,
                "results_count": len(response.results),
                "results": [
                    {
                        "title": r.title,
                        "snippet": r.snippet,
                        "source": r.source,
                    }
                    for r in response.results[:3]  # limit to 3 per dimension to save tokens
                ],
            }

    return {
        "report": report,
        "dimensions": dimensions,
    }


search_comprehensive_intel_tool = ToolDefinition(
    name="search_comprehensive_intel",
    description="Multi-dimensional intelligence search: latest news, market analysis, "
                "risk checking, earnings outlook, and industry trends for a stock. "
                "Returns a formatted report and structured results.",
    parameters=[
        ToolParameter(
            name="stock_code",
            type="string",
            description="Stock code, e.g., '600519'",
        ),
        ToolParameter(
            name="stock_name",
            type="string",
            description="Stock name in Chinese, e.g., '贵州茅台'",
        ),
    ],
    handler=_handle_search_comprehensive_intel,
    category="search",
)


# ============================================================
# fetch_webpage
# ============================================================

def _handle_fetch_webpage(url: str, max_chars: int = 5000) -> dict:
    """Fetch a webpage and extract its text content."""
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        }
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove script, style, nav, footer elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        text = soup.get_text(separator="\n", strip=True)

        # Truncate to max_chars
        if len(text) > max_chars:
            text = text[:max_chars] + "\n...(truncated)"

        return {
            "success": True,
            "url": url,
            "title": title,
            "content": text,
            "content_length": len(text),
        }
    except Exception as e:
        logger.warning(f"[fetch_webpage] Failed to fetch {url}: {e}")
        return {
            "success": False,
            "url": url,
            "error": str(e),
        }


fetch_webpage_tool = ToolDefinition(
    name="fetch_webpage",
    description="Fetch a webpage URL and extract its text content. "
                "Use this to read the full content of a search result. "
                "Returns the page title and text content (HTML tags removed).",
    parameters=[
        ToolParameter(
            name="url",
            type="string",
            description="The URL to fetch, e.g., 'https://example.com/article'",
        ),
        ToolParameter(
            name="max_chars",
            type="integer",
            description="Maximum characters to return (default 5000)",
            required=False,
        ),
    ],
    handler=_handle_fetch_webpage,
    category="search",
)


# ============================================================
# search_local_news
# ============================================================

def _handle_search_local_news(stock_code: str, stock_name: str = "") -> dict:
    """Search local news sources for a stock."""
    from src.config import get_config
    from src.local_news import LocalNewsManager

    config = get_config()
    if not config.local_news_dirs:
        return {"success": True, "results_count": 0, "results": [], "message": "No local news dirs configured"}

    manager = LocalNewsManager(config.local_news_dirs)
    items = manager.search(stock_code=stock_code, stock_name=stock_name)

    return {
        "success": True,
        "results_count": len(items),
        "results": items[:20],  # limit to 20 to save tokens
    }


search_local_news_tool = ToolDefinition(
    name="search_local_news",
    description="Search local news sources (Wantgoo and other configured sources) for a stock. "
                "Returns today's news articles from locally stored news data. "
                "Useful for getting the most recent Taiwan stock news.",
    parameters=[
        ToolParameter(
            name="stock_code",
            type="string",
            description="Stock code, e.g., 'TW4919' or '4919'",
        ),
        ToolParameter(
            name="stock_name",
            type="string",
            description="Stock name in Chinese, e.g., '新唐'",
            required=False,
        ),
    ],
    handler=_handle_search_local_news,
    category="search",
)


ALL_SEARCH_TOOLS = [
    search_stock_news_tool,
    search_comprehensive_intel_tool,
    fetch_webpage_tool,
    search_local_news_tool,
]

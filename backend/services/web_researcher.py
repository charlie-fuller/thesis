"""Web Researcher Service

Provides web search capabilities for Atlas research with:
- Credibility-tiered source filtering
- Result caching to avoid duplicate searches
- Source citation formatting
- Integration with Anthropic's built-in web search

Uses Claude's native web search tool for real-time research.
"""

import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlparse

import anthropic

from database import get_supabase
from logger_config import get_logger

logger = get_logger(__name__)

supabase = get_supabase()

# Initialize Anthropic client for web search
_anthropic_client: Optional[anthropic.Anthropic] = None


def get_anthropic_client() -> anthropic.Anthropic:
    """Get or create Anthropic client."""
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _anthropic_client


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class WebSource:
    """A web source with credibility information."""

    url: str
    title: str
    snippet: str
    domain: str
    credibility_tier: int = 3
    source_type: Optional[str] = None
    source_name: Optional[str] = None
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class WebSearchResult:
    """Result of a web search."""

    query: str
    sources: list[WebSource]
    total_results: int
    cached: bool = False
    search_time_ms: int = 0


@dataclass
class ResearchWebContext:
    """Web context prepared for Atlas synthesis."""

    sources_by_tier: dict[int, list[WebSource]]
    formatted_context: str
    citation_list: list[dict]
    total_sources: int


# Simple in-memory cache (in production, use Redis)
_search_cache: dict[str, tuple[WebSearchResult, datetime]] = {}
CACHE_TTL_MINUTES = 60


# ============================================================================
# CREDIBILITY MANAGEMENT
# ============================================================================


def get_domain_from_url(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def get_source_credibility(domain: str) -> tuple[int, Optional[str], Optional[str]]:
    """Get credibility tier for a domain from the database.

    Returns:
        tuple: (credibility_tier, source_type, source_name)
    """
    try:
        result = (
            supabase.table("research_sources")
            .select("credibility_tier, source_type, name")
            .eq("domain", domain)
            .single()
            .execute()
        )

        if result.data:
            return (
                result.data["credibility_tier"],
                result.data.get("source_type"),
                result.data.get("name"),
            )
    except Exception as e:
        logger.debug(f"No credibility data for {domain}: {e}")

    # Default to Tier 4 for unknown sources
    return (4, None, None)


def update_source_citation_count(domain: str):
    """Increment the citation count for a source."""
    try:
        supabase.table("research_sources").update(
            {
                "times_cited": supabase.table("research_sources")
                .select("times_cited")
                .eq("domain", domain)
                .single()
                .execute()
                .data.get("times_cited", 0)
                + 1,
                "last_cited_at": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("domain", domain).execute()
    except Exception as e:
        logger.debug(f"Could not update citation count for {domain}: {e}")


# ============================================================================
# WEB SEARCH IMPLEMENTATION (Anthropic Native)
# ============================================================================


async def search_web(
    query: str,
    max_results: int = 10,
    min_credibility_tier: int = 4,
    preferred_domains: Optional[list[str]] = None,
) -> WebSearchResult:
    """Search the web for research content using Anthropic's web search.

    Uses Claude's native web search tool to find and extract information
    from the web in real-time.

    Args:
        query: Search query
        max_results: Maximum results to return
        min_credibility_tier: Only include sources at this tier or better (1=best)
        preferred_domains: Prefer results from these domains

    Returns:
        WebSearchResult with filtered and ranked sources
    """
    import time

    start_time = time.time()

    # Check cache first
    cache_key = _get_cache_key(query, max_results, min_credibility_tier)
    cached = _get_from_cache(cache_key)
    if cached:
        cached.cached = True
        return cached

    # Execute Anthropic web search
    sources = await _anthropic_web_search(query, max_results)

    # Filter by credibility
    filtered_sources = []
    for source in sources:
        tier, source_type, source_name = get_source_credibility(source.domain)
        source.credibility_tier = tier
        source.source_type = source_type
        source.source_name = source_name

        if tier <= min_credibility_tier:
            filtered_sources.append(source)

    # Sort by credibility (tier 1 first)
    filtered_sources.sort(key=lambda s: (s.credibility_tier, s.title))

    # Prefer specified domains
    if preferred_domains:
        preferred = [s for s in filtered_sources if s.domain in preferred_domains]
        others = [s for s in filtered_sources if s.domain not in preferred_domains]
        filtered_sources = preferred + others

    # Limit results
    filtered_sources = filtered_sources[:max_results]

    search_time_ms = int((time.time() - start_time) * 1000)

    result = WebSearchResult(
        query=query,
        sources=filtered_sources,
        total_results=len(filtered_sources),
        cached=False,
        search_time_ms=search_time_ms,
    )

    # Cache result
    _add_to_cache(cache_key, result)

    return result


async def _anthropic_web_search(query: str, max_results: int) -> list[WebSource]:
    """Execute web search using Anthropic's native web search tool.

    Uses Claude with the web_search tool to find relevant sources.
    """
    logger.info(f"Executing Anthropic web search for: {query}")

    try:
        client = get_anthropic_client()

        # Use Claude with web search tool
        # web_search_20250305 requires Claude 3.5/3.7 Sonnet or Haiku
        # Claude 4 models do NOT support web search yet
        # Run sync client in executor to avoid blocking event loop
        import asyncio

        def make_web_search_call():
            # Web search requires beta header
            return client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=4096,
                extra_headers={"anthropic-beta": "web-search-2025-03-05"},
                tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
                messages=[
                    {
                        "role": "user",
                        "content": f"""Search the web for the following research query and return relevant sources:

Query: {query}

Focus on finding:
1. Research reports from consulting firms (McKinsey, BCG, Bain, Gartner, Forrester)
2. Academic/business publications (HBR, MIT Sloan, academic papers)
3. Industry news and case studies
4. Enterprise technology insights

For each source found, I need:
- The URL
- The page title
- A brief snippet/summary of the relevant content

Please search thoroughly and return the most credible and relevant sources.""",
                    }
                ],
            )

        # Run with 60 second timeout to avoid hanging
        loop = asyncio.get_event_loop()
        logger.info("Starting web search API call with 60s timeout...")
        try:
            response = await asyncio.wait_for(
                loop.run_in_executor(None, make_web_search_call), timeout=60.0
            )
        except asyncio.TimeoutError:
            logger.error("Web search timed out after 60 seconds")
            return []

        logger.info("Web search API call completed, extracting sources...")

        # Extract sources from the response
        sources = _extract_sources_from_response(response)

        logger.info(f"Anthropic web search found {len(sources)} sources")
        return sources[:max_results]

    except anthropic.APIError as e:
        logger.error(f"Anthropic API error during web search: {e}")
        logger.error(
            f"API Error details - status: {getattr(e, 'status_code', 'N/A')}, message: {getattr(e, 'message', str(e))}"
        )
        return []
    except anthropic.BadRequestError as e:
        logger.error(f"Anthropic BadRequestError: {e}")
        logger.error("This may indicate web search is not enabled for this API key/org")
        return []
    except Exception as e:
        logger.error(f"Web search failed: {type(e).__name__}: {e}", exc_info=True)
        return []


def _extract_sources_from_response(response) -> list[WebSource]:
    """Extract WebSource objects from Anthropic API response.

    Parses the response content blocks to find web search results
    and text content with citations.
    """
    sources = []
    seen_urls = set()

    for block in response.content:
        # Handle web search result blocks
        if hasattr(block, "type") and block.type == "web_search_tool_result":
            # Extract search results from the tool result
            if hasattr(block, "content") and isinstance(block.content, list):
                for result in block.content:
                    if hasattr(result, "type") and result.type == "web_search_result":
                        url = getattr(result, "url", "")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            domain = get_domain_from_url(url)
                            sources.append(
                                WebSource(
                                    url=url,
                                    title=getattr(result, "title", "Unknown"),
                                    snippet=getattr(
                                        result, "snippet", getattr(result, "content", "")[:500]
                                    ),
                                    domain=domain,
                                )
                            )

        # Handle text blocks that may contain citations
        elif hasattr(block, "type") and block.type == "text":
            # Check for citations in text content
            if hasattr(block, "citations") and block.citations:
                for citation in block.citations:
                    url = getattr(citation, "url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        domain = get_domain_from_url(url)
                        sources.append(
                            WebSource(
                                url=url,
                                title=getattr(citation, "title", "Unknown"),
                                snippet=getattr(citation, "cited_text", "")[:500],
                                domain=domain,
                            )
                        )

    return sources


# ============================================================================
# CONTEXT PREPARATION
# ============================================================================


def prepare_web_context(sources: list[WebSource]) -> ResearchWebContext:
    """Prepare web sources for Atlas synthesis.

    Organizes sources by credibility tier and formats them for
    inclusion in the research prompt.
    """
    # Group by tier
    sources_by_tier: dict[int, list[WebSource]] = {1: [], 2: [], 3: [], 4: []}
    for source in sources:
        tier = source.credibility_tier
        if tier in sources_by_tier:
            sources_by_tier[tier].append(source)

    # Format for prompt
    context_parts = []

    tier_labels = {
        1: "Tier 1 Sources (Consulting/Research - High Credibility)",
        2: "Tier 2 Sources (Big 4/Major Tech - High Credibility)",
        3: "Tier 3 Sources (Industry Publications - Medium Credibility)",
        4: "Tier 4 Sources (Blogs/Marketing - Use for Signals Only)",
    }

    for tier in [1, 2, 3, 4]:
        tier_sources = sources_by_tier[tier]
        if tier_sources:
            context_parts.append(f"\n### {tier_labels[tier]}\n")
            for source in tier_sources:
                context_parts.append(f"**[{source.source_name or source.domain}]({source.url})**")
                context_parts.append(f"*{source.title}*")
                context_parts.append(f"{source.snippet}\n")

    formatted_context = "\n".join(context_parts)

    # Build citation list
    citation_list = []
    for source in sources:
        citation_list.append(
            {
                "url": source.url,
                "title": source.title,
                "domain": source.domain,
                "source_name": source.source_name or source.domain,
                "credibility_tier": source.credibility_tier,
                "source_type": source.source_type,
            }
        )

        # Update citation count
        update_source_citation_count(source.domain)

    return ResearchWebContext(
        sources_by_tier=sources_by_tier,
        formatted_context=formatted_context,
        citation_list=citation_list,
        total_sources=len(sources),
    )


def format_citations_for_output(citation_list: list[dict]) -> str:
    """Format citations for inclusion at the end of research output."""
    if not citation_list:
        return ""

    lines = ["\n---\n## Sources\n"]

    # Group by tier
    by_tier: dict[int, list[dict]] = {}
    for cite in citation_list:
        tier = cite.get("credibility_tier", 4)
        if tier not in by_tier:
            by_tier[tier] = []
        by_tier[tier].append(cite)

    tier_labels = {
        1: "Primary Sources",
        2: "Supporting Sources",
        3: "Industry Sources",
        4: "Additional References",
    }

    for tier in sorted(by_tier.keys()):
        cites = by_tier[tier]
        if cites:
            lines.append(f"\n### {tier_labels.get(tier, 'Other')}\n")
            for cite in cites:
                lines.append(f"- [{cite['source_name']}]({cite['url']}) - {cite['title']}")

    return "\n".join(lines)


# ============================================================================
# CACHING
# ============================================================================


def _get_cache_key(query: str, max_results: int, min_tier: int) -> str:
    """Generate cache key for search."""
    content = f"{query}:{max_results}:{min_tier}"
    return hashlib.md5(content.encode()).hexdigest()


def _get_from_cache(key: str) -> Optional[WebSearchResult]:
    """Get result from cache if not expired."""
    if key in _search_cache:
        result, cached_at = _search_cache[key]
        if datetime.now(timezone.utc) - cached_at < timedelta(minutes=CACHE_TTL_MINUTES):
            return result
        else:
            del _search_cache[key]
    return None


def _add_to_cache(key: str, result: WebSearchResult):
    """Add result to cache."""
    _search_cache[key] = (result, datetime.now(timezone.utc))

    # Cleanup old entries
    now = datetime.now(timezone.utc)
    expired = [
        k for k, (_, t) in _search_cache.items() if now - t > timedelta(minutes=CACHE_TTL_MINUTES)
    ]
    for k in expired:
        del _search_cache[k]


def clear_search_cache():
    """Clear the search cache."""
    global _search_cache
    _search_cache = {}


# ============================================================================
# SEARCH QUERY GENERATION
# ============================================================================


def generate_search_queries(topic: str, focus_area: str) -> list[str]:
    """Generate multiple search queries for comprehensive research.

    Args:
        topic: The research topic
        focus_area: The focus area (strategic_planning, finance_roi, etc.)

    Returns:
        List of search queries to execute
    """
    queries = []

    # Base query
    queries.append(f"{topic} enterprise AI implementation 2024 2025")

    # Focus-area specific queries
    focus_queries = {
        "strategic_planning": [
            f"{topic} C-suite governance best practices",
            f"{topic} strategic planning framework enterprise",
        ],
        "finance_roi": [
            f"{topic} ROI benchmarks finance department",
            f"{topic} cost reduction metrics case study",
        ],
        "governance_compliance": [
            f"{topic} AI governance framework compliance",
            f"{topic} regulatory requirements enterprise AI",
        ],
        "change_management": [
            f"{topic} change management adoption patterns",
            f"{topic} AI implementation failure lessons",
        ],
        "weekly_synthesis": ["GenAI enterprise news this week", "AI implementation trends 2025"],
    }

    if focus_area in focus_queries:
        queries.extend(focus_queries[focus_area])

    # Add consulting firm query
    queries.append(f"{topic} McKinsey BCG Gartner research")

    return queries


# ============================================================================
# MAIN RESEARCH FUNCTION
# ============================================================================


async def research_topic_with_web(
    topic: str, focus_area: str = "general", max_sources: int = 10
) -> tuple[str, list[dict]]:
    """Research a topic using web search.

    Args:
        topic: The topic to research
        focus_area: Focus area for query generation
        max_sources: Maximum number of sources to include

    Returns:
        tuple: (formatted_context_for_prompt, citation_list)
    """
    # Generate search queries
    queries = generate_search_queries(topic, focus_area)

    all_sources: list[WebSource] = []
    seen_urls = set()

    # Execute searches
    for query in queries:
        try:
            result = await search_web(
                query=query,
                max_results=5,
                min_credibility_tier=3,  # Only Tier 1-3
            )

            for source in result.sources:
                if source.url not in seen_urls:
                    seen_urls.add(source.url)
                    all_sources.append(source)

        except Exception as e:
            logger.warning(f"Search failed for '{query}': {e}")

    # Sort by credibility and limit
    all_sources.sort(key=lambda s: s.credibility_tier)
    all_sources = all_sources[:max_sources]

    # Prepare context
    web_context = prepare_web_context(all_sources)

    return web_context.formatted_context, web_context.citation_list

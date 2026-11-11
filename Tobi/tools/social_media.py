"""
Social media monitoring tools for Tobi.

Uses official APIs only (no scraping). Monitors X/Twitter, TikTok, and
connected social accounts for mentions, trends, and engagement.
"""
import logging
import os
import time

import httpx

logger = logging.getLogger("Tobi.tools.social_media")


async def get_x_trending(limit: int = 10) -> str:
    """Get trending topics on X/Twitter using the official API.

    Requires X_BEARER_TOKEN in .env.
    """
    token = os.getenv("X_BEARER_TOKEN", "")
    if not token:
        return "X_BEARER_TOKEN not set. Configure it in .env to enable X trending."

    # Worldwide trends by default (WOEID 1)
    url = "https://api.twitter.com/2/trends/by/woeid/1"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                trends = data.get("data", [])[:limit]
                if not trends:
                    return "No trending topics found on X."
                lines = [f"{i+1}. {t.get('name', '')} ({t.get('tweet_volume', 'N/A')} tweets)" for i, t in enumerate(trends)]
                return f"X/Twitter trending ({len(lines)}):\n" + "\n".join(lines)
            elif resp.status_code == 403:
                return "X API access requires elevated access for trends endpoint."
            else:
                return f"X API returned {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        logger.error("X trending fetch failed: %s", e)
        return f"X trending error: {e}"


async def search_x(query: str, limit: int = 10) -> str:
    """Search recent posts on X using the official API."""
    token = os.getenv("X_BEARER_TOKEN", "")
    if not token:
        return "X_BEARER_TOKEN not set."

    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"query": query, "max_results": min(limit, 100), "tweet.fields": "created_at,public_metrics,author_id"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers=headers, params=params)
            if resp.status_code == 200:
                data = resp.json()
                tweets = data.get("data", [])
                if not tweets:
                    return f"No recent tweets found for '{query}'."
                lines = []
                for t in tweets:
                    text = t.get("text", "")[:120]
                    metrics = t.get("public_metrics", {})
                    likes = metrics.get("like_count", 0)
                    rts = metrics.get("retweet_count", 0)
                    lines.append(f"- {text} (Likes: {likes}, RTs: {rts})")
                return f"X search results for '{query}' ({len(tweets)} tweets):\n" + "\n".join(lines)
            else:
                return f"X search returned {resp.status_code}"
    except Exception as e:
        logger.error("X search failed: %s", e)
        return f"X search error: {e}"


async def get_tiktok_trending(limit: int = 10) -> str:
    """Get trending content on TikTok.

    Uses TikTok's official Research API if available, otherwise
    returns a message about configuration.
    """
    token = os.getenv("TIKTOK_ACCESS_TOKEN", "")
    if not token:
        return "TIKTOK_ACCESS_TOKEN not set. Configure it in .env for TikTok trends."

    # TikTok Research API endpoint
    url = "https://open.tiktokapis.com/v2/trending/posts/"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers=headers, params={"type": "must-see", "count": limit})
            if resp.status_code == 200:
                data = resp.json()
                posts = data.get("data", {}).get("posts", [])
                if not posts:
                    return "No trending TikTok posts found."
                lines = [f"- {p.get('desc', 'No description')[:100]}" for p in posts[:limit]]
                return f"TikTok trending ({len(lines)}):\n" + "\n".join(lines)
            else:
                return f"TikTok API returned {resp.status_code}"
    except Exception as e:
        logger.error("TikTok trending failed: %s", e)
        return f"TikTok error: {e}"


async def get_social_brief() -> str:
    """Combined social media brief: X trending + TikTok trending."""
    parts = []
    x_trending = await get_x_trending(5)
    parts.append(x_trending)
    tiktok = await get_tiktok_trending(5)
    parts.append(tiktok)
    return "\n\n".join(parts)


async def check_mentions(username: str, platform: str = "x") -> str:
    """Check for mentions of a username across platforms."""
    if platform == "x":
        return await search_x(f"@{username}", limit=10)
    return f"Mention checking for {platform} is not yet supported."

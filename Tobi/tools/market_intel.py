"""
Market and trend intelligence engine for Tobi.

Tracks crypto, forex, AI/tech news on a schedule.
Surfaces what's trending in the user's niche before they'd normally see it.
Uses official APIs: CoinGecko, NewsAPI, RSS feeds.
"""
import logging
import time
from datetime import datetime

import httpx

logger = logging.getLogger("Tobi.tools.market_intel")


async def get_crypto_prices(coins: list[str] | None = None) -> str:
    """Get current crypto prices from CoinGecko (free, no API key)."""
    if coins is None:
        coins = ["bitcoin", "ethereum", "solana", "binancecoin", "xrp"]

    ids = ",".join(coins)
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true"

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return f"CoinGecko API returned status {resp.status_code}"
            data = resp.json()

            lines = []
            for coin_id in coins:
                if coin_id not in data:
                    continue
                info = data[coin_id]
                price = info.get("usd", 0)
                change = info.get("usd_24h_change", 0)
                mcap = info.get("usd_market_cap", 0)
                direction = "+" if change >= 0 else ""
                mcap_b = f"${mcap / 1e9:.1f}B" if mcap >= 1e9 else f"${mcap / 1e6:.0f}M"
                lines.append(f"{coin_id.upper()}: ${price:,.2f} ({direction}{change:.1f}%) - MC: {mcap_b}")

            return "Crypto prices:\n" + "\n".join(lines)
    except Exception as e:
        logger.error("Crypto price fetch failed: %s", e)
        return f"Crypto price error: {e}"


async def get_trending_coins(limit: int = 10) -> str:
    """Get trending coins from CoinGecko."""
    url = "https://api.coingecko.com/api/v3/search/trending"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return f"CoinGecko trending returned {resp.status_code}"
            data = resp.json()
            coins = data.get("coins", [])[:limit]

            if not coins:
                return "No trending coins found."

            lines = []
            for c in coins:
                item = c.get("item", {})
                name = item.get("name", "")
                symbol = item.get("symbol", "")
                rank = item.get("market_cap_rank", "N/A")
                price_btc = item.get("price_btc", 0)
                lines.append(f"{name} ({symbol}) - Rank #{rank}")

            return f"Trending coins ({len(lines)}):\n" + "\n".join(lines)
    except Exception as e:
        logger.error("Trending coins fetch failed: %s", e)
        return f"Trending coins error: {e}"


async def get_forex_rates(pairs: list[str] | None = None) -> str:
    """Get forex rates from a free API."""
    if pairs is None:
        pairs = ["EUR/USD", "GBP/USD", "USD/NGN", "USD/JPY"]

    # Use exchangerate-api (free tier)
    base = "USD"
    url = f"https://open.er-api.com/v6/latest/{base}"

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return f"Forex API returned {resp.status_code}"
            data = resp.json()
            rates = data.get("rates", {})

            lines = []
            for pair in pairs:
                parts = pair.split("/")
                if len(parts) != 2:
                    continue
                from_cur, to_cur = parts
                if from_cur == base:
                    rate = rates.get(to_cur, 0)
                    lines.append(f"{pair}: {rate:.4f}")
                elif to_cur == base:
                    rate = rates.get(from_cur, 0)
                    lines.append(f"{pair}: {1/rate:.4f}" if rate else f"{pair}: N/A")
                else:
                    r1 = rates.get(to_cur, 0)
                    r2 = rates.get(from_cur, 0)
                    if r1 and r2:
                        lines.append(f"{pair}: {r1/r2:.4f}")
                    else:
                        lines.append(f"{pair}: N/A")

            return "Forex rates:\n" + "\n".join(lines)
    except Exception as e:
        logger.error("Forex rate fetch failed: %s", e)
        return f"Forex error: {e}"


async def get_ai_tech_news(limit: int = 10) -> str:
    """Get AI and tech news from RSS feeds."""
    feeds = [
        "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
    ]

    articles = []
    async with httpx.AsyncClient(timeout=15) as client:
        for feed_url in feeds:
            try:
                resp = await client.get(feed_url)
                if resp.status_code == 200:
                    # Simple XML parsing for RSS
                    content = resp.text
                    # Extract titles between <title> tags
                    import re
                    titles = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>", content)
                    for t in titles[:5]:
                        title = t[0] or t[1]
                        if title and title.strip() and len(title) > 10:
                            articles.append(title.strip())
            except Exception as e:
                logger.debug("RSS feed %s failed: %s", feed_url, e)
                continue

    # Deduplicate
    seen = set()
    unique = []
    for a in articles:
        key = a.lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(a)

    if not unique:
        return "No AI/tech news found at the moment."

    return f"AI/Tech news ({len(unique)} articles):\n" + "\n".join(f"- {a}" for a in unique[:limit])


async def get_market_brief() -> str:
    """Combined market brief: crypto + forex + AI news."""
    parts = []
    parts.append(await get_crypto_prices())
    parts.append(await get_forex_rates())
    parts.append(await get_ai_tech_news(5))
    return "\n\n".join(parts)


async def get_niche_update(niche: str = "blockchain") -> str:
    """Get updates specific to a niche (blockchain, crypto, forex, AI)."""
    if niche in ("blockchain", "crypto", "web3"):
        prices = await get_crypto_prices(["bitcoin", "ethereum", "solana", "xrp"])
        trending = await get_trending_coins(5)
        return f"{prices}\n\n{trending}"
    elif niche in ("forex", "fx"):
        return await get_forex_rates()
    elif niche in ("ai", "tech"):
        return await get_ai_tech_news(8)
    else:
        return await get_market_brief()

"""
Job and gig search tools for Tobi.

Scans job boards relevant to web dev and digital marketing work.
Filters to fit skillset and rates, surfaces new ones daily.
"""
import logging
import os
import time
from datetime import datetime

import httpx

logger = logging.getLogger("Tobi.tools.job_search")

# Skills to match against
DEFAULT_SKILLS = [
    "web development", "frontend", "backend", "full stack", "react", "next.js",
    "python", "javascript", "typescript", "node.js", "wordpress", "shopify",
    "digital marketing", "seo", "social media marketing", "content marketing",
    "ui/ux", "figma", "graphic design", "copywriting",
    "blockchain", "web3", "smart contracts", "solidity",
    "ai", "machine learning", "automation",
]


async def search_remoteok(query: str = "", limit: int = 10) -> str:
    """Search RemoteOK for jobs."""
    url = "https://remoteok.com/api"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return f"RemoteOK returned status {resp.status_code}"
            jobs = resp.json()
            if not jobs:
                return "No jobs found on RemoteOK."

            query_lower = query.lower() if query else ""
            matched = []
            for job in jobs:
                if not isinstance(job, dict) or "position" not in job:
                    continue
                title = job.get("position", "")
                company = job.get("company", "")
                tags = " ".join(job.get("tags", [])).lower()
                desc = job.get("description", "").lower()
                combined = f"{title} {tags} {desc}".lower()

                if query_lower and query_lower not in combined:
                    continue
                matched.append({
                    "title": title,
                    "company": company,
                    "tags": job.get("tags", []),
                    "url": job.get("url", ""),
                    "salary": job.get("salary_min", ""),
                    "date": job.get("date", "")[:10],
                })

            if not matched:
                return f"No matching jobs found on RemoteOK for '{query}'."

            lines = []
            for j in matched[:limit]:
                salary = f" - ${j['salary']:,}" if j['salary'] else ""
                lines.append(f"{j['title']} at {j['company']}{salary} ({j['date']})")
                if j['url']:
                    lines.append(f"  {j['url']}")
            return f"RemoteOK results ({len(matched)} matches, showing {min(limit, len(matched))}):\n" + "\n".join(lines)
    except Exception as e:
        logger.error("RemoteOK search failed: %s", e)
        return f"RemoteOK search error: {e}"


async def search_arbeitnow(query: str = "", limit: int = 10) -> str:
    """Search ArbeitNow for remote jobs."""
    url = "https://www.arbeitnow.com/api/job-board-api"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return f"ArbeitNow returned status {resp.status_code}"
            data = resp.json()
            jobs = data.get("data", [])
            if not jobs:
                return "No jobs found on ArbeitNow."

            query_lower = query.lower() if query else ""
            matched = []
            for job in jobs:
                title = job.get("title", "")
                company = job.get("company_name", "")
                desc = job.get("description", "").lower()
                combined = f"{title} {desc}".lower()

                if query_lower and query_lower not in combined:
                    continue
                matched.append({
                    "title": title,
                    "company": company,
                    "url": job.get("url", ""),
                    "date": job.get("created_at", "")[:10],
                    "remote": job.get("remote", False),
                })

            if not matched:
                return f"No matching jobs on ArbeitNow for '{query}'."

            lines = []
            for j in matched[:limit]:
                remote_tag = " (remote)" if j['remote'] else ""
                lines.append(f"{j['title']} at {j['company']}{remote_tag} ({j['date']})")
                if j['url']:
                    lines.append(f"  {j['url']}")
            return f"ArbeitNow results ({len(matched)} matches):\n" + "\n".join(lines)
    except Exception as e:
        logger.error("ArbeitNow search failed: %s", e)
        return f"ArbeitNow search error: {e}"


async def search_jobs(query: str = "web development", limit: int = 15) -> str:
    """Aggregate job search across multiple boards."""
    results = []

    remoteok = await search_remoteok(query, limit=limit // 2)
    results.append(remoteok)

    arbeitnow = await search_arbeitnow(query, limit=limit // 2)
    results.append(arbeitnow)

    return "\n\n".join(results)


async def get_daily_job_brief(skills: list[str] | None = None) -> str:
    """Build a daily job brief with top matches across boards."""
    if skills is None:
        skills = DEFAULT_SKILLS[:5]

    parts = []
    for skill in skills[:3]:
        result = await search_jobs(skill, limit=5)
        parts.append(f"=== {skill.upper()} ===\n{result}")

    return "\n\n".join(parts)

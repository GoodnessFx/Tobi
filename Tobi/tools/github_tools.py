"""
GitHub integration tools for Tobi.

Reads repos, open PRs, recent commits, issues, and stale branches.
Used for daily briefings and context-aware responses.
Requires GITHUB_TOKEN in .env.
"""
import logging
import os
import time
from typing import Optional

import httpx

logger = logging.getLogger("Tobi.tools.github")

GITHUB_API = "https://api.github.com"


def _get_headers() -> dict:
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def _get(url: str, params: dict | None = None) -> dict | list | None:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers=_get_headers(), params=params)
        if resp.status_code == 200:
            return resp.json()
        logger.warning("GitHub API %s returned %d: %s", url, resp.status_code, resp.text[:200])
        return None


async def get_my_repos(limit: int = 10) -> str:
    """List the authenticated user's repositories."""
    data = await _get(f"{GITHUB_API}/user/repos", {"per_page": limit, "sort": "updated"})
    if not data:
        return "Could not fetch repositories. Check your GITHUB_TOKEN."
    lines = []
    for repo in data[:limit]:
        lang = repo.get("language") or "N/A"
        stars = repo.get("stargazers_count", 0)
        updated = repo.get("updated_at", "")[:10]
        lines.append(f"{repo['full_name']} ({lang}) - {stars} stars - updated {updated}")
    return f"Your repositories ({len(lines)}):\n" + "\n".join(lines)


async def get_open_prs(repo: str = "") -> str:
    """Get open pull requests. If repo is empty, search across all repos."""
    if repo:
        url = f"{GITHUB_API}/repos/{repo}/pulls"
        data = await _get(url, {"state": "open", "per_page": 20})
        if not data:
            return f"No open PRs found in {repo}."
        lines = [f"#{pr['number']} {pr['title']} ({pr['user']['login']}) - {pr['created_at'][:10]}" for pr in data]
        return f"Open PRs in {repo} ({len(lines)}):\n" + "\n".join(lines)

    data = await _get(f"{GITHUB_API}/search/issues", {"q": "is:pr is:open author:@me", "per_page": 20})
    if not data or "items" not in data:
        return "No open PRs found across your repositories."
    items = data["items"]
    lines = [f"#{pr['number']} {pr['title']} in {pr['repository_url'].split('/')[-2]}/{pr['repository_url'].split('/')[-1]}" for pr in items[:15]]
    return f"Your open PRs ({len(items)}):\n" + "\n".join(lines)


async def get_recent_commits(repo: str, limit: int = 10) -> str:
    """Get recent commits from a repository."""
    data = await _get(f"{GITHUB_API}/repos/{repo}/commits", {"per_page": limit})
    if not data:
        return f"Could not fetch commits from {repo}."
    lines = []
    for c in data[:limit]:
        sha = c["sha"][:7]
        msg = c["commit"]["message"].split("\n")[0][:80]
        date = c["commit"]["author"]["date"][:10]
        lines.append(f"[{sha}] {msg} ({date})")
    return f"Recent commits in {repo} ({len(lines)}):\n" + "\n".join(lines)


async def get_open_issues(repo: str = "", limit: int = 15) -> str:
    """Get open issues. If repo is empty, search across all repos."""
    if repo:
        url = f"{GITHUB_API}/repos/{repo}/issues"
        data = await _get(url, {"state": "open", "per_page": limit})
        if not data:
            return f"No open issues in {repo}."
        lines = [f"#{i['number']} {i['title']} ({i['user']['login']}) - {i['created_at'][:10]}" for i in data if "pull_request" not in i]
        return f"Open issues in {repo} ({len(lines)}):\n" + "\n".join(lines)

    data = await _get(f"{GITHUB_API}/search/issues", {"q": "is:issue is:open author:@me", "per_page": limit})
    if not data or "items" not in data:
        return "No open issues found."
    items = data["items"]
    lines = [f"#{i['number']} {i['title']}" for i in items[:limit]]
    return f"Your open issues ({len(items)}):\n" + "\n".join(lines)


async def get_stale_branches(repo: str, days: int = 30) -> str:
    """Find branches with no commits in the last N days."""
    data = await _get(f"{GITHUB_API}/repos/{repo}/branches", {"per_page": 100})
    if not data:
        return f"Could not fetch branches from {repo}."

    stale = []
    cutoff = time.time() - days * 86400
    for branch in data:
        branch_name = branch["name"]
        if branch_name in ("main", "master", "develop"):
            continue
        commit_data = await _get(f"{GITHUB_API}/repos/{repo}/commits/{branch_name}")
        if commit_data:
            commit_date = commit_data["commit"]["author"]["date"]
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(commit_date.replace("Z", "+00:00"))
                if dt.timestamp() < cutoff:
                    stale.append(f"{branch_name} (last commit: {commit_date[:10]})")
            except Exception:
                pass

    if not stale:
        return f"No stale branches in {repo} (older than {days} days)."
    return f"Stale branches in {repo} ({len(stale)}):\n" + "\n".join(stale)


async def get_github_summary() -> str:
    """Build a morning GitHub summary: repos, open PRs, issues, recent activity."""
    parts = []

    repos = await get_my_repos(5)
    parts.append(repos)

    prs = await get_open_prs()
    parts.append(prs)

    issues = await get_open_issues()
    parts.append(issues)

    return "\n\n".join(parts)


async def create_issue(repo: str, title: str, body: str = "") -> str:
    """Create a new issue in a repository."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{GITHUB_API}/repos/{repo}/issues",
            headers={**_get_headers(), "Content-Type": "application/json"},
            json={"title": title, "body": body},
        )
        if resp.status_code == 201:
            data = resp.json()
            return f"Issue created: #{data['number']} {data['html_url']}"
        return f"Failed to create issue: {resp.status_code} {resp.text[:200]}"

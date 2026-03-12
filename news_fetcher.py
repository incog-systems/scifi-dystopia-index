"""
Fetches news articles from NewsAPI for dystopia analysis.
Free tier returns truncated content; we combine title + description + partial content.
"""
import requests

NEWSAPI_BASE = "https://newsapi.org/v2"

# Pull from categories most likely to surface dystopian themes
FETCH_PLAN = [
    {"endpoint": "top-headlines", "params": {"category": "technology", "language": "en", "pageSize": 5}},
    {"endpoint": "top-headlines", "params": {"category": "science",    "language": "en", "pageSize": 4}},
    {"endpoint": "top-headlines", "params": {"category": "business",   "language": "en", "pageSize": 4}},
    {"endpoint": "top-headlines", "params": {"category": "general",    "language": "en", "pageSize": 4}},
]


def fetch_articles(api_key: str, max_articles: int = 10) -> list[dict]:
    """
    Fetch top news articles from NewsAPI.

    Returns a list of dicts with: headline, text, source, url, published_at.
    The free tier truncates article content, so we combine title + description
    + whatever content is available.
    """
    collected: list[dict] = []
    seen_titles: set[str] = set()

    for plan in FETCH_PLAN:
        if len(collected) >= max_articles:
            break

        try:
            resp = requests.get(
                f"{NEWSAPI_BASE}/{plan['endpoint']}",
                params={**plan["params"], "apiKey": api_key},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            print(f"NewsAPI fetch error ({plan['params'].get('category')}): {e}")
            continue

        for article in data.get("articles", []):
            if len(collected) >= max_articles:
                break

            title = (article.get("title") or "").strip()
            description = (article.get("description") or "").strip()
            content = (article.get("content") or "").strip()

            # Skip removed, blank, or duplicate articles
            if not title or title == "[Removed]" or title in seen_titles:
                continue
            if len(description) < 40:
                continue

            # Free tier truncates content with "[+N chars]" — strip that suffix
            if " [+" in content:
                content = content[: content.index(" [+")].strip()

            body = description
            if content and content not in description:
                body += f"\n\n{content}"

            seen_titles.add(title)
            collected.append({
                "headline": title,
                "text": body,
                "source": article.get("source", {}).get("name", "Unknown"),
                "url": article.get("url", ""),
                "published_at": article.get("publishedAt", ""),
            })

    return collected

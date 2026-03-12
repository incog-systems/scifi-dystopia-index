"""
Aggregates multiple ArticleAnalysis objects into a DystopiaIndex.

The index ranks dystopian stories by cumulative alignment score across
all analyzed articles and surfaces trending real-world themes.
A final Claude call generates a narrative summary of the index state.
"""
from collections import Counter, defaultdict
import anthropic
from models import ArticleAnalysis, DystopiaIndex, StoryScore


def build_index(analyses: list[ArticleAnalysis]) -> DystopiaIndex:
    """
    Aggregate a list of ArticleAnalysis objects into a DystopiaIndex.

    Scoring:
    - Each article's dystopia_tags contribute their alignment_score to a
      per-story cumulative total.
    - Stories are ranked by cumulative score (breadth × intensity).
    - Trending themes are the most frequent primary_themes across all articles.
    - A Claude call produces a narrative summary.

    Args:
        analyses: List of ArticleAnalysis from analyze_article()

    Returns:
        DystopiaIndex with ranked stories, themes, and summary
    """
    if not analyses:
        return DystopiaIndex(
            article_count=0,
            top_stories=[],
            trending_themes=[],
            index_summary="No articles have been analyzed yet.",
        )

    # Aggregate per-story data
    story_scores: dict[str, float] = defaultdict(float)
    story_counts: dict[str, int] = defaultdict(int)
    story_directors: dict[str, str] = {}
    story_elements: dict[str, list[str]] = defaultdict(list)

    theme_counter: Counter = Counter()

    for analysis in analyses:
        theme_counter.update(analysis.primary_themes)

        for tag in analysis.dystopia_tags:
            key = tag.story_title
            story_scores[key] += tag.alignment_score
            story_counts[key] += 1
            story_directors[key] = tag.author_or_director
            story_elements[key].extend(tag.matching_elements)

    # Build StoryScore objects
    story_score_list: list[StoryScore] = []
    for story_title, cumulative in story_scores.items():
        count = story_counts[story_title]
        # Deduplicate and take top 5 most common matching elements
        element_counts = Counter(story_elements[story_title])
        top_elements = [el for el, _ in element_counts.most_common(5)]

        story_score_list.append(
            StoryScore(
                story_title=story_title,
                author_or_director=story_directors[story_title],
                cumulative_score=round(cumulative, 3),
                article_count=count,
                avg_score=round(cumulative / count, 3),
                top_matching_elements=top_elements,
            )
        )

    # Rank by cumulative score
    story_score_list.sort(key=lambda s: s.cumulative_score, reverse=True)

    # Top trending themes
    trending_themes = [theme for theme, _ in theme_counter.most_common(8)]

    # Generate narrative summary via Claude
    summary = _generate_summary(story_score_list[:5], trending_themes, len(analyses))

    return DystopiaIndex(
        article_count=len(analyses),
        top_stories=story_score_list,
        trending_themes=trending_themes,
        index_summary=summary,
    )


def _generate_summary(
    top_stories: list[StoryScore],
    trending_themes: list[str],
    article_count: int,
) -> str:
    """Use Claude to write a compelling narrative summary of the current index state."""
    client = anthropic.Anthropic()

    story_lines = "\n".join(
        f"  - {s.story_title} (cumulative score: {s.cumulative_score:.2f}, "
        f"{s.article_count} article{'s' if s.article_count != 1 else ''}, "
        f"avg: {s.avg_score:.2f}) — elements: {', '.join(s.top_matching_elements[:3])}"
        for s in top_stories
    )

    prompt = f"""Based on the current Sci-Fi Dystopia Index data, write a compelling 2-3 sentence narrative summary
that captures what our current moment most resembles in dystopian fiction.

INDEX DATA ({article_count} articles analyzed):
Top dystopian stories:
{story_lines}

Trending real-world themes: {', '.join(trending_themes)}

Write in a sharp, journalistic tone. Be specific about which stories dominate and why.
Do not use bullet points — write flowing prose. No preamble, just the summary."""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    return next(b.text for b in response.content if b.type == "text").strip()

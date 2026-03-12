from pydantic import BaseModel, Field


class DystopiaTag(BaseModel):
    story_title: str = Field(
        description="Title of the sci-fi work (e.g. '1984', 'Elysium', 'Black Mirror')"
    )
    author_or_director: str = Field(
        description="Author or director of the work (e.g. 'George Orwell', 'Neill Blomkamp')"
    )
    alignment_score: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "How closely this article resembles this story on a 0-1 scale. "
            "0 = no resemblance, 0.5 = moderate resemblance, 1.0 = extremely close match"
        ),
    )
    matching_elements: list[str] = Field(
        description=(
            "Specific real-world elements from the article that map to this story's themes. "
            "Be concrete and evidence-based, e.g. 'city-wide facial recognition network' not just 'surveillance'"
        )
    )
    explanation: str = Field(
        description="1-2 sentences explaining the structural resemblance to this story"
    )


class ArticleAnalysis(BaseModel):
    headline: str = Field(description="The article headline")
    summary: str = Field(description="1-2 sentence summary of the article's key events")
    primary_themes: list[str] = Field(
        description="High-level real-world themes present in this article (e.g. 'surveillance capitalism', 'wealth inequality', 'climate collapse')"
    )
    dystopia_tags: list[DystopiaTag] = Field(
        description=(
            "The 1-3 sci-fi dystopian stories this article most closely resembles, "
            "ranked by alignment score descending"
        )
    )
    overall_dystopia_score: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Weighted average alignment score across all tags. "
            "Reflects how strongly this article maps to dystopian fiction overall"
        ),
    )


class StoryScore(BaseModel):
    story_title: str
    author_or_director: str
    cumulative_score: float = Field(description="Sum of all alignment scores across articles")
    article_count: int = Field(description="Number of articles that tagged this story")
    avg_score: float = Field(description="Average alignment score across tagged articles")
    top_matching_elements: list[str] = Field(
        description="Most frequently cited real-world elements across all articles"
    )


class DystopiaIndex(BaseModel):
    article_count: int
    top_stories: list[StoryScore] = Field(
        description="Ranked list of dystopian stories, sorted by cumulative score descending"
    )
    trending_themes: list[str] = Field(
        description="Most frequently occurring real-world themes across all analyzed articles"
    )
    index_summary: str = Field(
        description="A compelling 2-3 sentence narrative summary of what the index currently shows"
    )

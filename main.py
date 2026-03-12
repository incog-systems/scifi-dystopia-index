"""
Sci-Fi Dystopia Index
=====================
Analyzes news articles and scores them against famous sci-fi dystopias,
then aggregates into a rolling index of which fictional futures we're
most closely resembling right now.

Usage:
    python main.py

    Or import the functions directly:
        from analyzer import analyze_article
        from index import build_index
"""
import json
from analyzer import analyze_article
from index import build_index
from models import ArticleAnalysis


# ---------------------------------------------------------------------------
# Sample articles — swap these out for real news feeds
# ---------------------------------------------------------------------------

SAMPLE_ARTICLES = [
    {
        "headline": "Tech Giants Deploy AI-Powered Surveillance Network Across 50 Major Cities",
        "text": """
A consortium of five technology companies announced today the expansion of their "SafeCity" platform
to 50 metropolitan areas across three continents. The system integrates real-time facial recognition,
behavioral pattern analysis, and predictive threat scoring drawn from social media activity, purchase
history, and location data. City governments have granted the consortium access to existing CCTV
infrastructure, effectively creating continuous monitoring of public spaces.

The platform assigns each flagged individual a "risk score" between 0 and 100. Scores above 70
trigger automatic alerts to law enforcement, who can request the system's dossier on any individual,
including a timeline of their movements over the past 90 days. Civil liberties groups noted that
the system disproportionately flags individuals based on their association with political protest
movements, with internal documents showing that attendance at demonstrations raises a person's
baseline score by 15 points.

A senior executive defended the technology: "We're not making decisions, we're surfacing
information. The humans are still in the loop." Critics pointed out that once an alert fires,
the practical effect is a presumption of guilt that the individual has no formal mechanism to
challenge. The companies declined to reveal what happens to score data when a person moves
between cities covered by different regional operators.
""",
    },
    {
        "headline": "Billionaire-Funded 'Archipelago' Project Breaks Ground on Private Ocean City",
        "text": """
A group of ultra-high-net-worth individuals revealed plans for "Archipelago," a network of
floating city-states in international waters, designed to house approximately 100,000 residents
who will pay between $8 million and $40 million for residency rights. The development will include
its own private hospital system with cutting-edge gene therapy and life-extension treatments
unavailable to the general public due to regulatory restrictions in their countries of origin,
private security forces, and a governance structure in which voting power is proportional to
property ownership.

The project's chief architect stated: "We're not running away from the world's problems. We're
building a demonstration of what governance can look like when you remove artificial constraints."
The announcement comes amid record-breaking inequality statistics — globally, the top 1% now
holds more wealth than the bottom 60% combined. On shore, healthcare systems in the project's
primary target markets are facing capacity crises, with waiting times for specialist treatment
exceeding 18 months in some regions.

The project is expected to create 12,000 permanent jobs, primarily in domestic service and
security, with workers housed in separate residential quarters and required to leave the islands
on rotating monthly schedules. Residents will receive an Archipelago passport recognized by
three small nations, granting them visa-free travel to 47 countries.
""",
    },
    {
        "headline": "Major Platform Deploys 'Harmony Score' to Rank User Content Trustworthiness",
        "text": """
The world's largest social media platform quietly rolled out a "Harmony Score" system to all
230 million accounts in its largest market this week. The score, ranging from 1 to 1000, is
calculated based on posting history, reported content, engagement patterns, and an undisclosed
set of behavioral signals. Accounts below a score of 400 face automatic throttling of their
reach, meaning their posts are shown to fewer people. Accounts below 200 cannot go live,
run advertisements, or be verified.

Unlike previous content moderation systems, the Harmony Score is cumulative and does not
reset — a post removed three years ago continues to suppress a user's score today. The company
says users can appeal individual decisions but has not provided a mechanism to review the score
itself or understand which historical actions contributed to it. A leaked internal memo
acknowledged that political commentary critical of the government in the platform's primary
market was weighted 2.3 times more heavily than other types of removed content in the
score's training data.

The platform's head of trust and safety said the system "rewards constructive participation
and discourages divisive behavior," adding that 94% of users have scores above 600 and
"should notice no change to their experience."
""",
    },
    {
        "headline": "Scientists Warn 'Tipping Point' Passed as Crop Yields Collapse Across Southern Hemisphere",
        "text": """
A coalition of 847 climate scientists released an emergency report today warning that three
simultaneous climate feedback loops have crossed thresholds that will make reversal within
human timescales "effectively impossible." Crop yields across the Southern Hemisphere have
declined an average of 34% over the past decade, with staple crops in sub-Saharan Africa
and Southeast Asia seeing losses above 50% in some regions.

Meanwhile, a coalition of the world's wealthiest individuals and corporations has quietly
accelerated the construction of what researchers are calling "climate refugia" — fortified
agricultural zones in Canada, Scandinavia, and New Zealand with advanced controlled-environment
farming, water security, and perimeter access systems. Access to these zones is available
through citizenship investment programs starting at $12 million. One such facility in Manitoba,
Canada, has already accepted 3,400 residents, all in the top 0.01% of global wealth.

Governments in the G20 pledged at the most recent climate summit to achieve "significant
progress" on emissions by 2035, the same pledge made at the previous four summits. A tech
billionaire announced a private geoengineering initiative that his team claims could reduce
global temperatures by 0.3°C within five years; climate scientists called the plan "reckless
and potentially catastrophic" but acknowledged that no international regulatory body has
the authority to stop it.
""",
    },
    {
        "headline": "AI Model Trained on National News Archive Used to Flag 'Pre-Disinformation' Accounts",
        "text": """
The communications ministry of a large democracy announced it has deployed an AI system
that analyzes posting patterns to identify accounts "at elevated risk of spreading
disinformation" before any prohibited content has been posted. The system, developed
by a state-affiliated AI lab, reviews an account's historical posts, the accounts it
follows, the hashtags it has used, and cross-references with a database of known
"influence operation actors" maintained by the ministry.

Accounts flagged as high-risk receive an unannounced reduction in algorithmic promotion.
In some cases, the system preemptively adds a "pending review" label to posts from
flagged accounts that remain invisible to the poster but visible to other users,
effectively pre-labeling their future speech as suspicious. The ministry said 2.1 million
accounts have received some form of pre-intervention since the system's launch six months ago.

Opposition politicians noted that 78% of the flagged accounts belonged to users who had
previously posted criticism of the ruling party's economic policies. The ministry stated
that "correlation is not causation" and that the system is "content-neutral." When asked
for the criteria used by the AI to flag accounts, a spokesperson said the model's parameters
were "proprietary and security-sensitive."
""",
    },
]


# ---------------------------------------------------------------------------
# Helpers for pretty-printing
# ---------------------------------------------------------------------------

def print_analysis(analysis: ArticleAnalysis) -> None:
    print(f"\n{'='*70}")
    print(f"  {analysis.headline}")
    print(f"{'='*70}")
    print(f"  Summary: {analysis.summary}")
    print(f"  Themes: {', '.join(analysis.primary_themes)}")
    print(f"  Overall dystopia score: {analysis.overall_dystopia_score:.2f}/1.00")
    print()
    for tag in analysis.dystopia_tags:
        bar = "█" * int(tag.alignment_score * 20) + "░" * (20 - int(tag.alignment_score * 20))
        print(f"  [{bar}] {tag.alignment_score:.2f}  {tag.story_title} ({tag.author_or_director})")
        print(f"    Matching elements:")
        for el in tag.matching_elements:
            print(f"      • {el}")
        print(f"    Why: {tag.explanation}")
        print()


def print_index(index) -> None:
    print(f"\n{'#'*70}")
    print(f"  SCI-FI DYSTOPIA INDEX  ({index.article_count} articles analyzed)")
    print(f"{'#'*70}")
    print(f"\n  {index.index_summary}\n")
    print(f"  RANKING")
    print(f"  {'─'*60}")
    for i, story in enumerate(index.top_stories, 1):
        bar = "█" * int(story.avg_score * 20) + "░" * (20 - int(story.avg_score * 20))
        print(f"  #{i:02d}  {story.story_title}")
        print(f"       [{bar}] avg {story.avg_score:.2f}  |  cumulative {story.cumulative_score:.2f}  |  {story.article_count} article(s)")
        print(f"       Top elements: {', '.join(story.top_matching_elements[:3])}")
    print(f"\n  TRENDING THEMES")
    print(f"  {'─'*60}")
    for theme in index.trending_themes:
        print(f"    • {theme}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("\nSci-Fi Dystopia Index")
    print("Analyzing articles...\n")

    analyses: list[ArticleAnalysis] = []

    for i, article in enumerate(SAMPLE_ARTICLES, 1):
        print(f"  [{i}/{len(SAMPLE_ARTICLES)}] Analyzing: {article['headline'][:60]}...")
        analysis = analyze_article(article["text"], headline=article["headline"])
        analyses.append(analysis)
        print_analysis(analysis)

    print("\nBuilding index...")
    index = build_index(analyses)
    print_index(index)

    # Optionally save results as JSON
    output = {
        "analyses": [a.model_dump() for a in analyses],
        "index": index.model_dump(),
    }
    with open("dystopia_index_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print("  Results saved to dystopia_index_results.json\n")


if __name__ == "__main__":
    main()

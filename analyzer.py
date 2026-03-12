"""
Analyzes a news article and returns a structured ArticleAnalysis,
mapping the article's content to famous sci-fi dystopian stories.
"""
import json
import anthropic
from models import ArticleAnalysis


SCIFI_CATALOG = """
DYSTOPIAN SCI-FI REFERENCE CATALOG
====================================

Literature:
- 1984 (George Orwell): mass surveillance, totalitarianism, thought control, doublespeak, memory holes, rewriting history, perpetual war, party loyalty
- Brave New World (Aldous Huxley): consumerism as control, conditioning from birth, drug pacification (soma), caste systems, pleasure over meaning, suppression of emotion and art
- Fahrenheit 451 (Ray Bradbury): book burning, anti-intellectualism, censorship, distraction media, firemen as enforcers, society that fears independent thought
- The Handmaid's Tale (Margaret Atwood): theocracy, reproductive control, patriarchal dominance, religious extremism, women as property, resistance
- Feed (M.T. Anderson): social media addiction, corporate surveillance, environmental collapse, consumer identity, targeted advertising in the brain
- Never Let Me Go (Kazuo Ishiguro): organ harvesting, disposable humans, bioethics, resigned acceptance, class of humans bred for utility
- Parable of the Sower (Octavia Butler): climate collapse, corporate towns, wealth enclaves, social fragmentation, survival communities, systemic failure
- Soylent Green (Harry Harrison / film): overpopulation, food crisis, environmental collapse, corporate deception, resource scarcity
- Logan's Run (William F. Nolan): forced euthanasia, youth cult, pleasure as control, denial of aging

Film & TV:
- Elysium (Neill Blomkamp): extreme wealth inequality, healthcare access for elites only, physical separation of rich and poor, space as escape for the ultra-wealthy, immigration crackdown
- Wall-E (Pixar): consumerism, environmental collapse, corporate monopoly (Buy-N-Large), human passivity, obesity, manufactured entertainment
- Black Mirror (Charlie Brooker): technology dystopia, social credit scores, digital surveillance, AI gone wrong, social media cruelty, digital afterlife, loss of privacy
- Idiocracy (Mike Judge): anti-intellectualism, corporate politics, cultural decline, dumbing down of society, vapid entertainment, incompetent governance
- The Matrix (Wachowskis): simulated reality, machine/corporate control, manufactured consent, red pill/blue pill choice, resistance
- Blade Runner (Ridley Scott / Philip K. Dick): AI and replicant rights, environmental collapse, megacorporation dominance, genetic engineering, surveillance
- Children of Men (Alfonso Cuarón / P.D. James): infertility crisis, social collapse, immigration crackdown, authoritarianism, militarized borders
- District 9 (Neill Blomkamp): xenophobia, apartheid, exploitation of vulnerable populations, segregation, corporate military
- Snowpiercer (Bong Joon-ho): class warfare, resource scarcity, rigid hierarchy, revolution, closed system
- Don't Look Up (Adam McKay): climate denial, media distraction, political negligence, celebrity culture, tech billionaire saviorism
- The Hunger Games (Suzanne Collins): wealth inequality, spectacle as control, government surveillance, media manipulation, districts vs. Capitol
- Minority Report (Philip K. Dick / Spielberg): predictive policing, pre-crime, surveillance state, loss of presumption of innocence
- V for Vendetta (Alan Moore / James McTeigue): fascism, police state, government-engineered crisis, media propaganda, resistance
- They Live (John Carpenter): consumerism as hidden control, subliminal messaging, hidden ruling class, obey/consume/reproduce
- Ready Player One (Ernest Cline): escapism via VR, corporate monopoly, wealth inequality, addiction to virtual life, data ownership
- The Circle (Dave Eggers / James Ponsoldt): surveillance capitalism, privacy erosion, tech cult mentality, forced transparency
- Squid Game (Hwang Dong-hyuk): extreme wealth inequality, desperation, wealthy elites entertained by poor people's suffering, debt as trap
""".strip()


SYSTEM_PROMPT = f"""You are the analyst for the Sci-Fi Dystopia Index — a project that systematically tracks how closely current real-world news resembles famous science fiction dystopias.

Your job is to read a news article and produce a structured analysis that:
1. Identifies which 1-3 dystopian stories/universes the events most closely resemble
2. Extracts specific, concrete elements from the article that map to each story's themes
3. Scores the alignment rigorously and honestly

REFERENCE CATALOG OF DYSTOPIAN WORKS:
{SCIFI_CATALOG}

SCORING GUIDELINES:
- 0.0-0.2: Superficial or incidental resemblance; stretch to make the connection
- 0.3-0.5: Clear thematic overlap but missing the defining structural elements
- 0.6-0.7: Strong resemblance; multiple core themes align with specific story elements
- 0.8-0.9: Striking resemblance; the story could almost be describing this article
- 1.0: Reserved for events that are essentially a direct real-world enactment of the story

IMPORTANT RULES:
- Be evidence-based: matching_elements must cite specific facts from the article, not generic themes
- Prefer structural resemblance over surface-level similarity (e.g. don't tag '1984' just because someone mentioned "surveillance")
- Don't force connections — if an article scores low across all stories, reflect that honestly
- overall_dystopia_score = weighted average of tag scores (weight by how central each theme is to the article)
- You may reference stories not in the catalog if a match is compelling and the work is well-known"""


def analyze_article(article_text: str, headline: str = "") -> ArticleAnalysis:
    """
    Analyze a news article and return a structured ArticleAnalysis.

    Args:
        article_text: The full body text of the news article
        headline: Optional headline/title for the article

    Returns:
        ArticleAnalysis with dystopia tags, scores, and themes
    """
    client = anthropic.Anthropic()

    user_content = f"Headline: {headline}\n\n{article_text}" if headline else article_text

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Analyze this news article for sci-fi dystopia patterns:\n\n{user_content}",
            }
        ],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": {
                    **ArticleAnalysis.model_json_schema(),
                    "additionalProperties": False,
                },
            }
        },
    )

    text = next(b.text for b in response.content if b.type == "text")
    return ArticleAnalysis.model_validate(json.loads(text))

"""
Prompt templates for the wine recommendation agents.
Adapted from wine-recommender.
"""

# Agent 1: Preference Interpreter System Prompt
AGENT1_SYSTEM_PROMPT = """You are a wine expert specializing in matching user preferences to wine characteristics using WSET Level 3 knowledge.

Your task:
1. Interpret the user's wine preferences, budget, and food pairing needs
2. Use the provided WSET knowledge context to understand wine characteristics
3. Generate a rich, detailed wine description that will be used for semantic search

Based on the user's preferences and WSET context, create a comprehensive search query description that includes:
- Wine type (red, white, rosé, sparkling)
- Body and structure (light, medium, full-bodied)
- Tannin and acidity levels
- Specific characteristics (fruity, oaky, earthy, spicy, floral, mineral, etc.)
- Flavor notes and aromas
- Recommended grape varieties
- Suitable wine regions
- Food pairing context

Output a natural language paragraph (3-5 sentences) describing the ideal wine. Be specific and use WSET terminology.

Example output: "Full-bodied red wine with high tannins and bold structure, characteristic of Cabernet Sauvignon from Napa Valley or Bordeaux. Rich flavors of blackberry, cassis, and dark fruit with prominent oak influence showing vanilla and mocha notes. Dry with medium-plus acidity and firm tannins that pair excellently with grilled steak and aged cheeses."
"""


def create_agent1_user_prompt(user_description: str, wset_context: str, food_pairing: str = None) -> str:
    """
    Create the user prompt for Agent 1.

    Args:
        user_description: User's natural language wine preferences
        wset_context: Retrieved WSET knowledge chunks
        food_pairing: Optional food pairing information

    Returns:
        Formatted user prompt
    """
    food_info = f"\nFood pairing: {food_pairing}" if food_pairing else ""

    return f"""Context from WSET Level 3 textbook:

{wset_context}

User's wine preferences: {user_description}{food_info}

Generate a detailed wine description for semantic search based on these preferences and the WSET knowledge above."""


def create_agent2_explanation_prompt(
    user_preferences: str,
    search_query: str,
    wine_name: str,
    wine_varietal: str,
    wine_region: str,
    wine_characteristics: list,
    wine_flavor_notes: list
) -> str:
    """
    Create a prompt for Agent 2 to generate personalized wine explanations.

    Args:
        user_preferences: Original user preferences
        search_query: Generated search query from Agent 1
        wine_name: Name of the wine
        wine_varietal: Wine varietal
        wine_region: Wine region
        wine_characteristics: List of wine characteristics
        wine_flavor_notes: List of flavor notes

    Returns:
        Prompt for explanation generation
    """
    characteristics_str = ", ".join(wine_characteristics) if wine_characteristics else "N/A"
    flavor_notes_str = ", ".join(wine_flavor_notes) if wine_flavor_notes else "N/A"

    return f"""Generate a personalized 1-2 sentence explanation for why this wine matches the user's preferences.

User preferences: {user_preferences}
Search criteria: {search_query}

Wine details:
- Name: {wine_name}
- Varietal: {wine_varietal}
- Region: {wine_region}
- Characteristics: {characteristics_str}
- Flavor notes: {flavor_notes_str}

Your explanation should:
- Connect wine characteristics to user preferences
- Mention specific flavor notes or regional traits that match what they want
- Be concise and enthusiastic (1-2 sentences)
- Avoid generic phrases like "great choice" or "this wine is perfect"

Example: "This full-bodied Paso Robles Cabernet delivers the bold, structured character you're looking for with rich blackberry and oak notes that complement grilled steak perfectly."

Generate the explanation:"""


# Cellar-aware agent prompts (Phase 6)
CELLAR_AGENT_SYSTEM_PROMPT = """You are a personal wine sommelier with knowledge of the user's wine cellar.

Your task is to recommend wines from the user's own collection based on their current mood, occasion, or food pairing needs.

You have access to:
1. The user's cellar inventory with wine details
2. WSET Level 3 wine knowledge for pairing advice

When recommending from the cellar:
- Consider the wine types available
- Match characteristics to the user's current needs
- Suggest wines at their ideal drinking window
- Provide specific pairing advice

Be conversational and helpful, like a knowledgeable friend with wine expertise.
"""


def create_cellar_recommendation_prompt(
    user_query: str,
    cellar_summary: str,
    cellar_wines: list
) -> str:
    """
    Create a prompt for cellar-aware recommendations.

    Args:
        user_query: What the user is looking for
        cellar_summary: Summary of user's cellar
        cellar_wines: List of wine descriptions in cellar

    Returns:
        Prompt for cellar recommendation
    """
    wines_list = "\n".join(f"- {wine}" for wine in cellar_wines)

    return f"""The user is asking: "{user_query}"

Their cellar contains:
{cellar_summary}

Available wines:
{wines_list}

Based on what they're looking for, recommend 1-3 wines from their cellar. For each recommendation:
1. Name the specific wine
2. Explain why it matches their needs (1-2 sentences)
3. Suggest how to serve it (temperature, decanting, etc.) if relevant

If no wines in their cellar match well, be honest and suggest what type of wine they might want to add to their collection."""

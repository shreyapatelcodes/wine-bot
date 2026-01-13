"""
Prompt templates for the wine recommendation agents.
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


# Agent 2: Wine Explanation Generation Prompt
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
    characteristics_str = ", ".join(wine_characteristics)
    flavor_notes_str = ", ".join(wine_flavor_notes)

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


# Streamlit UI text templates
STREAMLIT_WELCOME = """
# Wine Recommendation Engine

Powered by WSET Level 3 knowledge and AI-driven semantic search.

Describe your wine preferences, budget, and occasion, and we'll find 3 perfect wines for you from Wine.com.
"""

STREAMLIT_EXAMPLES = [
    "Bold red wine for a steak dinner",
    "Crisp white wine for seafood pasta",
    "Sparkling wine for a celebration",
    "Smooth, fruity red under $20 for pizza night",
    "Elegant white wine for a special occasion"
]

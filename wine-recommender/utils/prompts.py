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
    wine_flavor_notes: list,
    user_request: str = None,
    category_knowledge: str = None
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
        user_request: Original user request (for attribution)
        category_knowledge: Background knowledge (NOT for attribution)

    Returns:
        Prompt for explanation generation
    """
    characteristics_str = ", ".join(wine_characteristics)
    flavor_notes_str = ", ".join(wine_flavor_notes)

    # Use user_request if available, otherwise fall back to user_preferences
    explicit_request = user_request or user_preferences

    return f"""Generate a personalized 1-2 sentence explanation for why this wine matches what the user asked for.

WHAT THE USER EXPLICITLY ASKED FOR: {explicit_request}

Wine details:
- Name: {wine_name}
- Varietal: {wine_varietal}
- Region: {wine_region}
- Characteristics: {characteristics_str}
- Flavor notes: {flavor_notes_str}

IMPORTANT ATTRIBUTION RULES:
1. ONLY attribute preferences the user EXPLICITLY mentioned
2. If user said "under $40", you can say "within your budget"
3. If user said "for steak", you can say "pairs well with steak"
4. If user said "bold red", you can say "delivers the bold character you wanted"
5. Do NOT claim the user asked for things they didn't mention (like specific regions, flavor notes, etc.)
6. Focus on: "You asked for X - this wine delivers Y"

CRITICAL FOR SIMILARITY QUERIES:
- If user asked for "similar to [wine name]", ONLY say this wine shares characteristics with that wine
- Do NOT infer preferences like "the depth you're looking for" or "complexity you enjoy"
- Do NOT attribute preferences based on the characteristics of the reference wine
- Just describe HOW it's similar, not WHY they supposedly want those characteristics

Your explanation should:
- Connect wine characteristics ONLY to what user explicitly requested
- Mention specific wine qualities that match their stated needs
- Be concise and conversational (1-2 sentences)
- Avoid generic phrases like "great choice" or "perfect for you"

GOOD example (preference-based): "You asked for a bold red for steak - this full-bodied Cabernet has rich tannins and dark fruit that complement grilled meat beautifully."

GOOD example (similarity-based): "You asked for wines similar to Embrionly - this shares the same rich dark fruit profile and silky tannins from the Saint-Émilion region."

BAD example: "Since you love fruity wines from California..." (if user never said this)
BAD example: "...provides the depth you're looking for" (if user only asked for similarity, not depth)

Generate the explanation:"""


def create_agent2_explanation_prompt_simple(
    user_request: str,
    wine_name: str,
    wine_varietal: str,
    wine_region: str,
    wine_characteristics: list,
    wine_flavor_notes: list
) -> str:
    """
    Simplified explanation prompt that focuses on explicit user request.

    Args:
        user_request: Original user request
        wine_name: Name of the wine
        wine_varietal: Wine varietal
        wine_region: Wine region
        wine_characteristics: List of wine characteristics
        wine_flavor_notes: List of flavor notes

    Returns:
        Prompt for explanation generation
    """
    characteristics_str = ", ".join(wine_characteristics[:4])  # Limit for brevity
    flavor_notes_str = ", ".join(wine_flavor_notes[:4])

    return f"""Write a brief (1-2 sentence) explanation connecting this wine to what the user asked for.

User asked for: {user_request}

Wine: {wine_name} ({wine_varietal} from {wine_region})
Key traits: {characteristics_str}
Flavors: {flavor_notes_str}

CRITICAL: If user asked for "similar to [wine]", only describe HOW it's similar. Do NOT infer preferences like "the depth you want" or "complexity you're looking for".

Pattern: "You wanted [exactly what they said] - this [wine quality] delivers [how it matches]."

Explanation:"""


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

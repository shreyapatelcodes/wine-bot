"""
Agent 1: Preference Interpreter
Interprets user wine preferences using WSET knowledge and generates rich search query.
"""

import json
import re
from typing import Dict, Any, Optional
from openai import OpenAI
from config import Config
from models import UserPreferences, SearchQuery
from utils import (
    search_wset_knowledge,
    get_openai_client,
    AGENT1_SYSTEM_PROMPT,
    create_agent1_user_prompt
)


# Filter extraction prompt
FILTER_EXTRACTION_PROMPT = """Extract wine filters from this request. Return ONLY valid JSON.

Request: {request}

Extract these fields (use null if not mentioned):
- price_min: number (e.g., "over $30" -> 30)
- price_max: number (e.g., "under $40" -> 40, "around $50" -> 60)
- wine_type: "red", "white", "rosé", or "sparkling"
- region: specific wine region (e.g., "Napa Valley", "Bordeaux")
- country: country name
- varietal: grape variety (e.g., "Cabernet Sauvignon", "Pinot Noir")
- food_pairing: food mentioned (e.g., "steak", "seafood")
- occasion: event type (e.g., "dinner party", "casual", "celebration")
- characteristics: list of descriptors (e.g., ["bold", "fruity", "crisp"])

Price rules:
- "cheap" -> price_max: 20
- "affordable" -> price_max: 30
- "nice bottle" -> price_min: 30, price_max: 60
- "splurge" or "special occasion" -> price_min: 50

Return JSON only:"""


class PreferenceInterpreter:
    """
    Agent 1: Interprets user preferences using WSET knowledge to generate search queries.
    """

    def __init__(self):
        self.client = get_openai_client()

    def extract_filters(self, user_request: str) -> Dict[str, Any]:
        """
        Extract structured filters from natural language request.

        Args:
            user_request: Natural language wine request

        Returns:
            Dict with extracted filter values
        """
        prompt = FILTER_EXTRACTION_PROMPT.format(request=user_request)

        try:
            response = self.client.chat.completions.create(
                model=Config.CHAT_MODEL,
                messages=[
                    {"role": "system", "content": "Extract filters. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )

            content = response.choices[0].message.content.strip()

            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                filters = json.loads(json_match.group())
                # Clean up null values
                return {k: v for k, v in filters.items() if v is not None}

        except Exception as e:
            print(f"Filter extraction error: {e}")

        return {}

    def interpret(self, user_prefs: UserPreferences, verbose: bool = False) -> SearchQuery:
        """
        Interpret user preferences and generate a rich search query.

        Args:
            user_prefs: User's wine preferences
            verbose: If True, return additional debugging information

        Returns:
            SearchQuery object with query_text, price_range, and wine_type_filter
        """
        # Step 0: Extract filters from natural language
        extracted_filters = self.extract_filters(user_prefs.description)

        if verbose:
            print(f"\n[Agent 1] Extracted filters: {extracted_filters}")

        # Step 1: Query WSET knowledge for relevant wine information
        wset_query = self._build_wset_query(user_prefs)
        wset_chunks = search_wset_knowledge(wset_query, top_k=Config.TOP_K_WSET)

        if verbose:
            print(f"\n[Agent 1] WSET Query: {wset_query}")
            print(f"[Agent 1] Retrieved {len(wset_chunks)} WSET chunks")
            for i, chunk in enumerate(wset_chunks, 1):
                print(f"   {i}. {chunk['heading']} (score: {chunk['score']:.3f})")

        # Step 2: Build context from WSET chunks
        wset_context = self._format_wset_context(wset_chunks)

        # Step 3: Generate rich search query using LLM
        query_text = self._generate_search_query(
            user_prefs.description,
            wset_context,
            user_prefs.food_pairing
        )

        if verbose:
            print(f"\n[Agent 1] Generated Search Query:\n{query_text}\n")

        # Step 4: Merge explicit filters with extracted filters
        # Explicit values take precedence
        price_min = user_prefs.budget_min
        price_max = user_prefs.budget_max

        # Use extracted price if explicit not provided or default
        if extracted_filters.get("price_min") and price_min == 10.0:
            price_min = extracted_filters["price_min"]
        if extracted_filters.get("price_max") and price_max == 200.0:
            price_max = extracted_filters["price_max"]

        wine_type = user_prefs.wine_type_pref or extracted_filters.get("wine_type")

        # Step 5: Build SearchQuery object with extended fields
        search_query = SearchQuery(
            query_text=query_text,
            price_range=(price_min, price_max),
            wine_type_filter=wine_type,
            region_filter=extracted_filters.get("region"),
            country_filter=extracted_filters.get("country"),
            varietal_filter=extracted_filters.get("varietal"),
            occasion=extracted_filters.get("occasion"),
            user_request=user_prefs.description,  # Preserve for attribution
            category_knowledge=wset_context[:500] if wset_context else None  # Truncated for context
        )

        return search_query

    def _build_wset_query(self, user_prefs: UserPreferences) -> str:
        """Build a query for WSET knowledge base."""
        query_parts = [user_prefs.description]

        if user_prefs.food_pairing:
            query_parts.append(f"food pairing with {user_prefs.food_pairing}")

        if user_prefs.wine_type_pref:
            query_parts.append(f"{user_prefs.wine_type_pref} wine characteristics")

        return " ".join(query_parts)

    def _format_wset_context(self, chunks: list) -> str:
        """Format WSET knowledge chunks into context string."""
        context_parts = []
        for chunk in chunks:
            context_parts.append(f"Section: {chunk['heading']}\n{chunk['text']}")
        return "\n\n".join(context_parts)

    def _generate_search_query(
        self,
        user_description: str,
        wset_context: str,
        food_pairing: str = None
    ) -> str:
        """
        Generate rich search query text using LLM with WSET context.

        Args:
            user_description: User's natural language description
            wset_context: Retrieved WSET knowledge
            food_pairing: Optional food pairing

        Returns:
            Rich natural language wine description for semantic search
        """
        user_prompt = create_agent1_user_prompt(
            user_description,
            wset_context,
            food_pairing
        )

        response = self.client.chat.completions.create(
            model=Config.CHAT_MODEL,
            messages=[
                {"role": "system", "content": AGENT1_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_TOKENS_AGENT1
        )

        query_text = response.choices[0].message.content.strip()
        return query_text


# Convenience function for standalone usage
def interpret_preferences(user_prefs: UserPreferences, verbose: bool = False) -> SearchQuery:
    """
    Convenience function to interpret user preferences.

    Args:
        user_prefs: UserPreferences object
        verbose: Enable verbose output

    Returns:
        SearchQuery object
    """
    agent = PreferenceInterpreter()
    return agent.interpret(user_prefs, verbose=verbose)
